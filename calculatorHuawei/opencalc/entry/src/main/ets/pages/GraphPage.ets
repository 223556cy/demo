// OpenCalc — 函数图像绘制页面
// aid-workflow 20260617: Issue #26 函数图像
// 设计参考: specs/changes/20260617-requirement-add-plot-graph/delta-design.md §3.5

import { router } from '@kit.ArkUI'
import { GraphViewModel } from '../viewmodels/GraphViewModel'
import { PlotUtils, PlotPoint, PlotBounds, PlotSeries } from '../common/PlotUtils'
import { PreferencesStore } from '../preferences/PreferencesStore'
import { common } from '@kit.AbilityKit'

/** 主题色(themeIdx 0/1/2 → 颜色字符串) */
const THEME_COLORS: string[] = ['#4684E3', '#4FC3F7', '#7E57C2']

/** 文本输入最大长度(防路由参数溢出) */
const MAX_INPUT_LENGTH: number = 256

/** Canvas 内边距(像素,vp 单位) */
const PAD_L: number = 40
const PAD_R: number = 20
const PAD_T: number = 20
const PAD_B: number = 30

@Entry
@Component
struct GraphPage {
  @State vm: GraphViewModel = new GraphViewModel()
  @State curveColor: string = THEME_COLORS[0]
  // aid-workflow 20260626: 默认显示 sin(x) 完整周期 (-2π ~ 2π),而非 -2~2
  // 之前 -2~2 太窄,sin 在这个范围近似一条直线,容易被误判为"画错"
  @State expressionInput: string = 'sin(x)'
  @State xMinInput: string = '-6.28'
  @State xMaxInput: string = '6.28'
  @State samplesInput: string = '200'
  @State isLandscape: boolean = false
  @State canvasReady: boolean = false
  @State canvasWidth: number = 0
  @State canvasHeight: number = 0
  // aid-workflow 20260626: 自动重绘 debounce 句柄
  private autoDrawTimer: number = -1
  // aid-workflow 20260626: 用于键盘可见性,固定"绘制"按钮位置
  @State @Watch('onKeyboardStateChange') keyboardVisible: boolean = false

  private canvasCtx: CanvasRenderingContext2D = new CanvasRenderingContext2D(new RenderingContextSettings(true))
  private prefs: PreferencesStore | null = null

  aboutToAppear(): void {
    // 读取路由参数(可选)
    const params = router.getParams() as Record<string, Object> | undefined
    if (params !== undefined && params !== null) {
      const expr = params['expression'] as string | undefined
      if (expr !== undefined && expr.length > 0 && expr.length <= MAX_INPUT_LENGTH) {
        this.vm.expression = expr
        this.expressionInput = expr
      }
    }
    // aid-workflow 20260708: Issue #37 修复 isDegree 时序竞态
    // 原因: 原代码 prefs.init().then(loadPrefs) 是微任务,setTimeout(compute, 0) 是宏任务。
    //       ArkTS 事件循环规则: 微任务先于宏任务 → loadPrefs 先跑 (setRadianMode(true)) →
    //       但 setTimeout(compute) 反而先跑(因为 prefs.init() 是 5ms 异步) → vm.compute()
    //       使用未污染的 isDegree=false,但 hilog 仍可能看到 deg=true 取决于 timing。
    //       修复: 将 vm.compute() 移入 loadPrefs().then() 闭包,确保 isDegree 已稳定后再计算。
    //       降级: prefs.init() 失败时直接 compute (使用 VM 默认 isDegree=false)。
    const ctx: common.UIAbilityContext = getContext(this) as common.UIAbilityContext
    this.prefs = new PreferencesStore(ctx)
    this.prefs.init()
      .then((): void => {
        this.loadPrefs()
        this.vm.compute()
      })
      .catch((): void => {
        this.vm.compute()
      })
  }

  aboutToDisappear(): void {
    // aid-workflow 20260626: 清理 debounce 定时器,避免页面销毁后回调
    if (this.autoDrawTimer !== -1) {
      clearTimeout(this.autoDrawTimer)
      this.autoDrawTimer = -1
    }
  }

  // aid-workflow 20260626: f(x) 变化后 debounce 300ms 自动重绘
  // 不再需要用户手动按"绘制"按钮,大幅提升体验
  private scheduleAutoDraw(): void {
    if (this.autoDrawTimer !== -1) {
      clearTimeout(this.autoDrawTimer)
    }
    this.autoDrawTimer = setTimeout((): void => {
      this.vm.compute()
      this.drawCanvas()
      this.autoDrawTimer = -1
    }, 300)
  }

  onKeyboardStateChange(): void {
    // 预留:键盘状态变化时(如弹出"绘制"按钮在屏幕外),未来可加自动滚动
  }

  onPageShow(): void {
    // 页面显示时强制重绘(防止 Canvas 状态丢失)
    if (this.canvasReady) {
      this.drawCanvas()
    }
  }

  async loadPrefs(): Promise<void> {
    if (!this.prefs) return
    // aid-workflow 20260708: Issue #37 扩展修复 (Task 5.3)
    // 历史代码 setRadianMode(!radianMode) 跟随用户偏好,但用户默认 radiansDefault=false
    // (角度制)→ isDegree=true → sin(x) 在 x∈[-6.28, 6.28] 范围被当成角度计算 →
    // 小角近似 sin(x°)≈x*π/180 → 渲染成直线。
    // 修复: GraphPage 强制使用弧度制 (数学绘图惯例,不受用户一般偏好影响)。
    // 如果未来要支持"绘图用角度"功能,应单独加 graphUseDegrees 偏好,不要复用
    // radiansDefault。
    this.vm.setRadianMode(false)
    const themeIdx = await this.prefs.getTheme()
    if (themeIdx >= 0 && themeIdx < THEME_COLORS.length) {
      this.curveColor = THEME_COLORS[themeIdx]
    }
  }

  onBackPress(): boolean {
    router.back()
    return true
  }

  build() {
    Stack() {
      Column() {
        // 工具栏
        this.Toolbar()
        // Canvas 画布
        Canvas(this.canvasCtx)
          .width('100%')
          .layoutWeight(1)
          .backgroundColor('#FFFFFF')
          .onReady((): void => {
            this.canvasReady = true
            // 读取实际画布尺寸
            this.canvasWidth = this.canvasCtx.width
            this.canvasHeight = this.canvasCtx.height
            this.drawCanvas()
          })
          .onAreaChange((_old: Area, newVal: Area): void => {
            const w = newVal.width as number
            const h = newVal.height as number
            this.canvasWidth = w
            this.canvasHeight = h
            this.isLandscape = w > h
            if (this.canvasReady) {
              this.drawCanvas()
            }
          })
        // 错误条 (aid-workflow 20260626: 加重错误提示,加示例按钮一键填入)
        if (this.vm.errorMessage.length > 0) {
          Column() {
            Text(this.vm.errorMessage)
              .fontSize(13)
              .fontColor('#FF3B30')
              .fontWeight(FontWeight.Medium)
              .width('100%')
              .textAlign(TextAlign.Center)
            Text('示例: sin(x) / cos(x) / x*x / x^3 / sqrt(x) / log(x)')
              .fontSize(11)
              .fontColor('#888888')
              .width('100%')
              .textAlign(TextAlign.Center)
              .margin({ top: 4 })
          }
          .width('100%')
          .padding(10)
          .backgroundColor('#FFEEEE')
          .border({ width: { top: 1 }, color: '#FFCCCC' })
        }
        // 输入栏
        this.InputPanel()
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#FAFAFA')
    }
    .width('100%')
    .height('100%')
  }

  // ==================== 工具栏 ====================
  @Builder Toolbar() {
    Row() {
      Text('←')
        .fontSize(20)
        .fontColor('#333333')
        .padding({ left: 12, right: 12, top: 8, bottom: 8 })
        .onClick((): void => { router.back() })
      Text('函数图像')
        .fontSize(18)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .layoutWeight(1)
        .padding({ left: 8 })
      Blank()
      Text('📈')
        .fontSize(20)
        .padding({ right: 16 })
    }
    .width('100%')
    .height(48)
    .backgroundColor('#FFFFFF')
    .border({ width: { bottom: 1 }, color: '#EEEEEE' })
  }

  // ==================== 输入栏 ====================
  @Builder InputPanel() {
    Column() {
      Row() {
        Text('f(x)=')
          .fontSize(14)
          .fontColor('#333333')
          .width(50)
          .height(36)
        TextInput({ text: this.expressionInput, placeholder: 'sin(x)' })
          .layoutWeight(1)
          .height(36)
          .fontSize(14)
          // aid-workflow 20260626: 改完 300ms 自动重绘,无需按"绘制"按钮
          .onChange((value: string): void => {
            this.expressionInput = value
            this.vm.expression = value
            this.scheduleAutoDraw()
          })
        Button('绘制')
          .fontSize(13)
          .height(36)
          .margin({ left: 8 })
          .backgroundColor(this.curveColor)
          .onClick((): void => {
            // aid-workflow 20260626: 主动取消 debounce,立即重绘
            if (this.autoDrawTimer !== -1) {
              clearTimeout(this.autoDrawTimer)
              this.autoDrawTimer = -1
            }
            this.vm.compute()
            this.drawCanvas()
          })
      }
      .width('100%')
      .padding(8)

      Row() {
        Column() {
          Text('xMin').fontSize(10).fontColor('#888888').width('100%')
          TextInput({ text: this.xMinInput })
            .width('100%')
            .height(32)
            .fontSize(13)
            .onChange((value: string): void => {
              this.xMinInput = value
              const v = PlotUtils.parseRange(value)
              if (v !== null) this.vm.xMin = v
              this.scheduleAutoDraw()
            })
        }
        .layoutWeight(1)
        .padding({ right: 4 })

        Column() {
          Text('xMax').fontSize(10).fontColor('#888888').width('100%')
          TextInput({ text: this.xMaxInput })
            .width('100%')
            .height(32)
            .fontSize(13)
            .onChange((value: string): void => {
              this.xMaxInput = value
              const v = PlotUtils.parseRange(value)
              if (v !== null) this.vm.xMax = v
              this.scheduleAutoDraw()
            })
        }
        .layoutWeight(1)
        .padding({ left: 4, right: 4 })

        Column() {
          Text('samples').fontSize(10).fontColor('#888888').width('100%')
          TextInput({ text: this.samplesInput })
            .width('100%')
            .height(32)
            .fontSize(13)
            .onChange((value: string): void => {
              this.samplesInput = value
              const v = parseInt(value)
              if (!isNaN(v)) this.vm.samples = v
              this.scheduleAutoDraw()
            })
        }
        .layoutWeight(1)
        .padding({ left: 4 })
      }
      .width('100%')
      .padding({ left: 8, right: 8, bottom: 8 })
    }
    .width('100%')
    .height(116)
    .backgroundColor('#FFFFFF')
    .border({ width: { top: 1 }, color: '#EEEEEE' })
  }

  // ==================== 绘制 ====================
  private drawCanvas(): void {
    const ctx = this.canvasCtx
    if (this.canvasWidth <= 0 || this.canvasHeight <= 0) return
    // 清空
    ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
    ctx.fillStyle = '#FFFFFF'
    ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight)

    const bounds: PlotBounds = {
      width: this.canvasWidth,
      height: this.canvasHeight,
      paddingLeft: PAD_L,
      paddingRight: PAD_R,
      paddingTop: PAD_T,
      paddingBottom: PAD_B
    }

    const series = this.vm.series
    if (series === null) {
      this.drawPlaceholder(bounds, this.vm.errorMessage.length > 0 ? this.vm.errorMessage : '点击"绘制"按钮开始')
      return
    }

    // 网格
    this.drawGrid(bounds, series)
    // 坐标轴
    this.drawAxes(bounds, series)
    // 曲线
    this.drawCurve(bounds, series)
  }

  private drawGrid(bounds: PlotBounds, series: PlotSeries): void {
    const ctx = this.canvasCtx
    ctx.strokeStyle = '#22000000'
    ctx.lineWidth = 1
    const step = 1
    const startX = Math.floor(series.xMin / step)
    const endX = Math.ceil(series.xMax / step)
    // 垂直网格线
    for (let i = startX; i <= endX; i++) {
      const p = PlotUtils.mapToCanvas({ x: i, y: 0 } as PlotPoint, bounds, series.xMin, series.xMax, series.yMin, series.yMax)
      if (p === null) continue
      ctx.beginPath()
      ctx.moveTo(p.px, bounds.paddingTop)
      ctx.lineTo(p.px, bounds.height - bounds.paddingBottom)
      ctx.stroke()
    }
    // 水平网格线
    const startY = Math.floor(series.yMin / step)
    const endY = Math.ceil(series.yMax / step)
    for (let i = startY; i <= endY; i++) {
      const p = PlotUtils.mapToCanvas({ x: 0, y: i } as PlotPoint, bounds, series.xMin, series.xMax, series.yMin, series.yMax)
      if (p === null) continue
      ctx.beginPath()
      ctx.moveTo(bounds.paddingLeft, p.py)
      ctx.lineTo(bounds.width - bounds.paddingRight, p.py)
      ctx.stroke()
    }
  }

  private drawAxes(bounds: PlotBounds, series: PlotSeries): void {
    const ctx = this.canvasCtx
    ctx.strokeStyle = '#FF000000'
    ctx.lineWidth = 2
    ctx.fillStyle = '#FF333333'
    ctx.font = '10px sans-serif'
    // x 轴 (y=0)
    const xAxisP = PlotUtils.mapToCanvas({ x: 0, y: 0 } as PlotPoint, bounds, series.xMin, series.xMax, series.yMin, series.yMax)
    if (xAxisP !== null && xAxisP.py >= bounds.paddingTop && xAxisP.py <= bounds.height - bounds.paddingBottom) {
      ctx.beginPath()
      ctx.moveTo(bounds.paddingLeft, xAxisP.py)
      ctx.lineTo(bounds.width - bounds.paddingRight, xAxisP.py)
      ctx.stroke()
    }
    // y 轴 (x=0)
    const yAxisP = PlotUtils.mapToCanvas({ x: 0, y: 0 } as PlotPoint, bounds, series.xMin, series.xMax, series.yMin, series.yMax)
    if (yAxisP !== null && yAxisP.px >= bounds.paddingLeft && yAxisP.px <= bounds.width - bounds.paddingRight) {
      ctx.beginPath()
      ctx.moveTo(yAxisP.px, bounds.paddingTop)
      ctx.lineTo(yAxisP.px, bounds.height - bounds.paddingBottom)
      ctx.stroke()
    }
    // 刻度标签
    const labelStep = 1
    const startX = Math.floor(series.xMin / labelStep)
    const endX = Math.ceil(series.xMax / labelStep)
    for (let i = startX; i <= endX; i++) {
      if (i === 0) continue
      const p = PlotUtils.mapToCanvas({ x: i, y: 0 } as PlotPoint, bounds, series.xMin, series.xMax, series.yMin, series.yMax)
      if (p === null) continue
      ctx.fillText(String(i), p.px - 5, (xAxisP !== null ? xAxisP.py : bounds.height / 2) + 12)
    }
  }

  private drawCurve(bounds: PlotBounds, series: PlotSeries): void {
    const ctx = this.canvasCtx
    ctx.strokeStyle = this.curveColor
    ctx.lineWidth = 2
    ctx.beginPath()
    let started = false
    for (let i = 0; i < series.points.length; i++) {
      const p = series.points[i]
      const cp = PlotUtils.mapToCanvas(p, bounds, series.xMin, series.xMax, series.yMin, series.yMax)
      if (cp === null) {
        started = false
        continue
      }
      if (!started) {
        ctx.moveTo(cp.px, cp.py)
        started = true
      } else {
        ctx.lineTo(cp.px, cp.py)
      }
    }
    ctx.stroke()
  }

  private drawPlaceholder(bounds: PlotBounds, text: string): void {
    const ctx = this.canvasCtx
    ctx.fillStyle = '#FF999999'
    ctx.font = '14px sans-serif'
    const w = ctx.measureText(text).width
    ctx.fillText(text, (bounds.width - w) / 2, bounds.height / 2)
  }
}
