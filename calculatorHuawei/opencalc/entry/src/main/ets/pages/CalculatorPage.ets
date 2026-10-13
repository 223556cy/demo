// OpenCalc — 主计算器页面（横竖屏自适应 + Android 配色）
// 移植自：MainActivity.kt（1447行）
import { promptAction } from '@kit.ArkUI'
import { router } from '@kit.ArkUI'
import { pasteboard } from '@kit.BasicServicesKit'
import { common } from '@kit.AbilityKit'
import { Expression } from '../calculator/Expression'
import { CalcEngine } from '../calculator/Calculator'
import { NumberFormatter } from '../calculator/NumberFormatter'
import { DisplayMode, NumberingSystem, HistoryItem } from '../model/Models'
import { ErrorFlags } from '../model/ErrorFlags'
import { KeyboardMode, cycleMode as modeCycle, applySwiperIndex, resolveStartupMode } from '../model/ModeController'
import { PreferencesStore } from '../preferences/PreferencesStore'
import { NaturalLanguageParser, ParseResult } from '../common/NaturalLanguageParser'
import { UnitConverter } from '../common/UnitConverter'
import { FractionUtil } from '../common/FractionUtil'
import { QrCodeBuilder } from '../qrcode/QrCodeBuilder'
import { groupHistoryByDate, HistorySection, HistoryGroupKey } from '../history/HistoryGroup'
import { filterHistoryByQuery } from '../history/HistorySearch'
import { LongPressMenu, MENU_WIDTH_RATIO, MENU_MAX_WIDTH, MENU_ITEM_HEIGHT, MENU_FONT_SIZE, MENU_BORDER_RADIUS, MENU_MASK_COLOR, MENU_MASK_OPACITY, MENU_PADDING } from './LongPressMenu'
// aid-workflow 20260617 Issue #28: 记忆槽 (M1-M6 + MR)
import { MemorySlots, MemorySlotsState, MemorySlot } from '../calculator/MemorySlots'

@Entry
@Component
export struct CalculatorPage {
  // ==================== 显示状态 ====================
  // aid-workflow 20260612: @Watch 修饰 @State 字段，expression 变化时触发 onExpressionChange
  @State @Watch('onExpressionChange') expression: string = ''
  @State preview: string = ''   // aid-workflow 20260612: 实时预览值
  @State result: string = ''
  @State errorMsg: string = ''
  @State nlConversionResult: string = ''  // aid-workflow 20260615: NL 单位换算结果(空=未识别 NL,降级到原计算)
  @State scientific: boolean = false
  // aid-workflow 20260618 Issue #29: 三态键盘模式 (BASIC=0 / SCIENTIFIC=1 / PROGRAMMER=2)
  @State currentMode: KeyboardMode = KeyboardMode.BASIC
  @State history: HistoryItem[] = []
  // aid-workflow 20260617 Issue #24: 历史搜索关键字 (空=不过滤)
  @State searchQuery: string = ''
  @State showHistory: boolean = false
  @State showSettings: boolean = false
  @State showAbout: boolean = false
  @State isLandscape: boolean = false
  // aid-workflow 20260615: Issue #13 一键分享二维码
  @State showShare: boolean = false
  // aid-workflow 20260617 Issue #17: 粘贴去重 hash
  @State lastPastedHash: number = 0

  // ==================== 偏好设置状态 ====================
  @State vibrateOn: boolean = true
  @State preventSleep: boolean = false
  @State radianMode: boolean = false
  @State themeIdx: number = 0

  // aid-workflow 20260616: 长按候选菜单状态 (FMEA C2: 状态独立, 任何关闭路径置 false)
  @State showLongPressMenu: boolean = false
  @State longPressSource: string = ''

  // aid-workflow 20260617: Issue #27 分数/小数显示模式
  @State displayMode: DisplayMode = DisplayMode.DECIMAL

  // aid-workflow 20260617: Issue #27 缓存最近一次原始计算结果(用于分数模式重格式化)
  @State lastRawResult: number = 0

  // aid-workflow 20260617 Issue #28: 记忆槽 (M1-M6 + MR) 状态
  @State memorySlots: MemorySlotsState = MemorySlots.empty()
  @State showMemoryPicker: boolean = false

  // ==================== 内部状态 ====================
  private nextId: number = 0
  private engine: CalcEngine = new CalcEngine()
  private expr: Expression = new Expression()
  private prefs: PreferencesStore | null = null
  // aid-workflow 20260618 Issue #29: Swiper 控制器, 模式按钮通过 changeIndex 触发滑动
  private swpController: SwiperController = new SwiperController()

  aboutToAppear(): void {
    const ctx: common.UIAbilityContext = getContext(this) as common.UIAbilityContext
    this.prefs = new PreferencesStore(ctx)
    this.prefs.init().then((): void => { this.loadPrefs(); this.loadHistory() })
  }

  async loadPrefs(): Promise<void> {
    if (!this.prefs) return
    this.vibrateOn = await this.prefs.getVibrationEnabled()
    this.preventSleep = await this.prefs.getPreventSleep()
    this.radianMode = await this.prefs.getRadiansDefault()
    this.themeIdx = await this.prefs.getTheme()
    // aid-workflow 20260618 Issue #29: 启动优先级 SCIENTIFIC > PROGRAMMER > BASIC
    const sci: number = await this.prefs.getScientificModeDefault()
    const prog: number = await this.prefs.getProgrammerModeDefault()
    this.currentMode = resolveStartupMode(sci, prog)
    this.scientific = (this.currentMode === KeyboardMode.SCIENTIFIC)
    // aid-workflow 20260617: Issue #27 加载结果显示模式
    this.displayMode = await this.prefs.getResultDisplayMode()
  }

  async loadHistory(): Promise<void> {
    if (!this.prefs) return
    this.history = await this.prefs.getHistory()
    if (this.history.length > 0) this.nextId = this.history[0].id + 1
  }

  async savePref(key: string, value: boolean | number | string): Promise<void> {
    if (!this.prefs) return
    if (key === 'vibrateOn') await this.prefs.setVibrationEnabled(value as boolean)
    else if (key === 'preventSleep') await this.prefs.setPreventSleep(value as boolean)
    else if (key === 'radianMode') await this.prefs.setRadiansDefault(value as boolean)
    else if (key === 'themeIdx') await this.prefs.setTheme(value as number)
    else if (key === 'scientific') await this.prefs.setScientificModeDefault(value as number)
    // aid-workflow 20260617: Issue #27 持久化显示模式
    else if (key === 'resultDisplayMode') await this.prefs.setResultDisplayMode(value as DisplayMode)
    // aid-workflow 20260618 Issue #29: 程序员模式持久化
    else if (key === 'programmer') await this.prefs.setProgrammerModeDefault(value as number)
  }

  // ==================== Issue #29 模式状态机 ====================
  // aid-workflow 20260618: 模式按钮点击 → cycleMode → swpController.changeIndex → onChange 兜底更新
  // 单向数据流: 任何入口都走 onSwiperChange 完成 currentMode / scientific / 持久化同步
  cycleMode(): void {
    const next: KeyboardMode = modeCycle(this.currentMode)
    this.swpController.changeIndex(next, false)
  }

  // aid-workflow 20260618: Swiper onChange 回调, 单一可信源
  // 非法 index (负数/越界) → console.warn, 兜底 BASIC, 不动 currentMode
  onSwiperChange(idx: number): void {
    const next: KeyboardMode | null = applySwiperIndex(idx)
    if (next === null) {
      console.warn('CalculatorPage.onSwiperChange invalid index=' + idx)
      return
    }
    this.currentMode = next
    this.scientific = (next === KeyboardMode.SCIENTIFIC)
    // 持久化: 互斥写, 一次只写一个为 1
    void this.savePref('scientific', next === KeyboardMode.SCIENTIFIC ? 1 : 0)
    void this.savePref('programmer', next === KeyboardMode.PROGRAMMER ? 1 : 0)
  }

  // aid-workflow 20260618: 当前模式显示标签 (基础/科学/程序员)
  getCurrentModeLabel(): string {
    if (this.currentMode === KeyboardMode.SCIENTIFIC) return '科学'
    if (this.currentMode === KeyboardMode.PROGRAMMER) return '程序员'
    return '基础'
  }

  // ==================== 按钮事件 ====================
  // aid-workflow 20260612: 实时预览触发器，expression 变化时同步计算 preview
  // aid-workflow 20260615: NL 单位换算触发器,在 preview 之前执行
  // 注：ArkTS 中 @Watch 装饰器必须紧跟 @State（见字段声明），此处仅为回调方法
  onExpressionChange(): void {
    // 1. NL 解析【aid-workflow 20260615】
    const nlResult: ParseResult | null = NaturalLanguageParser.parse(this.expression)
    if (nlResult !== null) {
      const converted: number | null = UnitConverter.convert(
        nlResult.value, nlResult.from, nlResult.to, nlResult.category
      )
      if (converted !== null) {
        this.nlConversionResult = NumberFormatter.format(
          converted.toString(), '.', ',', NumberingSystem.INTERNATIONAL
        )
      } else {
        this.nlConversionResult = ''
      }
    } else {
      this.nlConversionResult = ''
    }
    // 2. 原有 preview 计算【aid-workflow 20260612】
    this.preview = this.computePreview(this.expression, this.radianMode)
  }

  /**
   * aid-workflow 20260612: 计算表达式实时预览（纯函数，副作用隔离）
   * 对应 design.md §3.3 与 RealtimePreview.port.mjs::PreviewCalculator.computePreview
   * @param exprStr 用户当前输入的表达式字符串
   * @param radianMode true=弧度模式，false=角度模式
   * @returns 格式化后的预览字符串，错误/不完整时返回空字符串
   */
  private computePreview(exprStr: string, radianMode: boolean): string {
    // 1. 空表达式 → ""
    if (exprStr.length === 0) return ''

    // 2. 末字符白名单过滤
    const lastChar: string = exprStr.charAt(exprStr.length - 1)
    if (!this.isLastCharComputable(lastChar)) return ''

    // 3. 括号平衡过滤（未闭合左括号 → 空）
    let openP: number = 0
    let closeP: number = 0
    for (let pi: number = 0; pi < exprStr.length; pi++) {
      const ch: string = exprStr.charAt(pi)
      if (ch === '(') openP++
      else if (ch === ')') closeP++
    }
    if (openP > closeP) return ''

    // 3.5 连续运算符检测（aid-workflow 20260612 修复 1++2 BUG）
    // 不允许两个二元运算符相邻（如 ++, +-, --, *+, /+, *-, 等）
    // 允许一元负号: "(-5)" 中 - 紧跟 ( 是合法的一元负号
    // 实现: 扫描每个运算符位置，如果前一个非 ( 也非数字开头的小数点，则为不合法的连续运算符
    if (this.hasConsecutiveBinaryOperators(exprStr)) return ''

    // 4. ErrorFlags 快照（避免污染主流程）
    const snap: boolean[] = ErrorFlags.snapshot()

    try {
      // 5. 预处理
      const clean: string = this.expr.getCleanExpression(exprStr, '.', ',')
      if (ErrorFlags.syntax_error) {
        ErrorFlags.restore(snap)
        return ''
      }

      // 6. 求值
      const raw: number = this.engine.evaluate(clean, !radianMode)
      if (ErrorFlags.division_by_0 || ErrorFlags.domain_error ||
          ErrorFlags.syntax_error || ErrorFlags.is_infinity ||
          ErrorFlags.require_real_number) {
        ErrorFlags.restore(snap)
        return ''
      }

      // 7. 格式化
      const formatted: string = NumberFormatter.format(raw.toString(), '.', ',', NumberingSystem.INTERNATIONAL)
      ErrorFlags.restore(snap)
      return formatted
    } catch (_e) {
      ErrorFlags.restore(snap)
      return ''
    }
  }

  /**
   * aid-workflow 20260612: 末字符是否可参与求值
   * 可计算末字符：数字 / '.' / ')' / '%' / '!' / 'π' / 'e'
   */
  private isLastCharComputable(lastChar: string): boolean {
    if ((lastChar >= '0' && lastChar <= '9') || lastChar === '.') return true
    if (lastChar === ')') return true
    if (lastChar === '%') return true
    if (lastChar === '!') return true
    if (lastChar === 'π' || lastChar === 'e') return true
    return false
  }

  /**
   * aid-workflow 20260612 (BUG 修复): 检测连续二元运算符
   * 修复 1++2 / 2×-2 预览误显示的问题。
   * 规则：不允许两个二元运算符相邻
   * 支持的运算符：+ - * / × ÷ % ^ #（含 Unicode × ÷，用户键入的乘除号）
   * 允许的合法场景：一元负号 (-5)、一元正号 (+5) 在表达式开头或 ( 后
   * @param exprStr 表达式字符串
   * @returns true=存在不合法的连续运算符，false=合法
   */
  private hasConsecutiveBinaryOperators(exprStr: string): boolean {
    const binaryOps: string = '+-*/×÷%^#'  // 同时支持 ASCII (* /) 和 Unicode (× ÷)
    for (let i: number = 1; i < exprStr.length; i++) {
      const prev: string = exprStr.charAt(i - 1)
      const curr: string = exprStr.charAt(i)
      // 当前是二元运算符
      if (binaryOps.indexOf(curr) === -1) continue
      // 前一个是 ( → 当前是一元运算符，合法（如 (-5）、(×2)）
      if (prev === '(') continue
      // 前一个是数字/小数点/右括号/百分号/阶乘/常量 → 当前是二元运算符，合法
      if ((prev >= '0' && prev <= '9') || prev === '.' || prev === ')' ||
          prev === '%' || prev === '!' || prev === 'π' || prev === 'e') continue
      // 其他情况：两个二元运算符相邻
      if (binaryOps.indexOf(prev) !== -1) return true
    }
    return false
  }

  onDigit(d: string): void {
    this.expression = this.expression + d
    this.errorMsg = ''
  }
  onOp(op: string): void {
    // aid-workflow 20260612: 错误状态恢复（SR-09）
    // 用户决策：清空 expression 和 errorMsg
    if (ErrorFlags.syntax_error || ErrorFlags.division_by_0 || ErrorFlags.domain_error ||
        ErrorFlags.is_infinity || ErrorFlags.require_real_number) {
      ErrorFlags.reset()
      this.expression = ''
      this.errorMsg = ''
      this.result = ''
    }
    this.expression = this.expression + op
    this.errorMsg = ''
  }
  onFunc(f: string): void { this.expression = this.expression + f + '('; this.errorMsg = '' }
  onConst(c: string): void { this.expression = this.expression + c; this.errorMsg = '' }
  onBS(): void { if (this.expression.length > 0) this.expression = this.expression.substring(0, this.expression.length - 1) }
  onAC(): void {
    this.expression = ''
    this.result = ''
    this.preview = ''
    this.nlConversionResult = ''
    this.errorMsg = ''
    // aid-workflow 20260617: Issue #27 清空最近原始结果
    this.lastRawResult = 0
    ErrorFlags.reset()
  }

  onEquals(): void {
    if (this.expression.length === 0) return

    // aid-workflow 20260615: NL 换算结果优先(若已识别)
    if (this.nlConversionResult.length > 0) {
      this.result = this.nlConversionResult
      this.errorMsg = ''
      const item: HistoryItem = { id: this.nextId, expression: this.expression, result: this.nlConversionResult, timestamp: Date.now() }
      this.nextId = this.nextId + 1
      const nh: HistoryItem[] = [item]
      for (let i: number = 0; i < this.history.length; i++) nh.push(this.history[i])
      this.history = nh
      if (this.prefs) this.prefs.setHistory(this.history)
      return
    }

    ErrorFlags.reset()
    try {
      const clean: string = this.expr.getCleanExpression(this.expression, '.', ',')
      const raw: number = this.engine.evaluate(clean, !this.radianMode)
      if (ErrorFlags.division_by_0) { this.errorMsg = '除数不能为零'; this.result = '' }
      else if (ErrorFlags.domain_error) { this.errorMsg = '定义域错误'; this.result = '' }
      else if (ErrorFlags.syntax_error) { this.errorMsg = '表达式错误'; this.result = '' }
      else if (ErrorFlags.is_infinity) { this.errorMsg = '结果无穷大'; this.result = '' }
      else if (ErrorFlags.require_real_number) { this.errorMsg = '需要实数'; this.result = '' }
      else {
        const fmt: string = NumberFormatter.format(raw.toString(), '.', ',', NumberingSystem.INTERNATIONAL)
        this.result = fmt
        // aid-workflow 20260617: Issue #27 缓存 raw 数值, 用于分数模式重格式化
        this.lastRawResult = raw
        this.errorMsg = ''
        const item: HistoryItem = { id: this.nextId, expression: this.expression, result: fmt, timestamp: Date.now() }
        this.nextId = this.nextId + 1
        const nh: HistoryItem[] = [item]
        for (let i: number = 0; i < this.history.length; i++) nh.push(this.history[i])
        this.history = nh
        if (this.prefs) this.prefs.setHistory(this.history)
      }
    } catch (_e) { this.errorMsg = '计算错误' }
  }

  // ==================== Issue #27 分数/小数显示切换 ====================
  // aid-workflow 20260617: 切换显示模式(小数 ↔ 分数) 并持久化
  onToggleDisplayMode(): void {
    if (this.errorMsg.length > 0) return  // 错误态禁用
    if (this.result.length === 0) return  // 无结果时禁用
    if (this.displayMode === DisplayMode.DECIMAL) {
      this.displayMode = DisplayMode.FRACTION
    } else {
      this.displayMode = DisplayMode.DECIMAL
    }
    this.savePref('resultDisplayMode', this.displayMode)
  }

  // aid-workflow 20260617: Issue #27 根据 displayMode 重新格式化结果显示
  // 不修改 this.result 本身(那是历史记录用的小数), 只在 UI 渲染时按模式格式化
  // 历史记录保持小数显示, 与 resultDisplayMode 解耦
  private formatResultForDisplay(): string {
    if (this.displayMode === DisplayMode.FRACTION) {
      const frac = FractionUtil.toFraction(this.lastRawResult)
      if (frac !== null) {
        return FractionUtil.format(frac.numerator, frac.denominator)
      }
    }
    // 小数模式或分数化简失败时回退
    return NumberFormatter.format(
      this.lastRawResult.toString(), '.', ',', NumberingSystem.INTERNATIONAL
    )
  }

  onCopy(): void {
    if (this.result.length === 0) return
    pasteboard.getSystemPasteboard().setData(pasteboard.createData(pasteboard.MIMETYPE_TEXT_PLAIN, this.result))
    promptAction.showToast({ message: '已复制' })
  }

  // ==================== Issue #13 一键分享二维码 ====================
  // aid-workflow 20260615: 分享按钮是否可用（用方法而非 getter，规避 ArkTS getter 兼容性问题）
  // 启用条件：expression 非空 + errorMsg 为空 + result 非空
  checkShareEnabled(): boolean {
    return this.expression.length > 0 && this.errorMsg.length === 0 && this.result.length > 0
  }

  // aid-workflow 20260615: 点击分享按钮（直接弹出 QR 模态，QR 码由 ArkUI 内置组件渲染）
  onShareClick(): void {
    if (!this.checkShareEnabled()) return
    this.showShare = true
  }

  // aid-workflow 20260615: 关闭分享模态层
  onShareClose(): void {
    this.showShare = false
  }

  // aid-workflow 20260720: 构造 QR payload（纯函数委托给 QrCodeBuilder）
  // 修复: 原 get sharePayload() 在 ArkUI 上返回值 undefined，导致 QRCode 渲染为字符串 "undefined"
  // 改用方法 (与 checkShareEnabled 同模式), 同步修 isPayloadTruncated
  // @returns URL 编码后的 payload 字符串
  getSharePayload(): string {
    return QrCodeBuilder.buildSharePayload(this.expression, this.result)
  }

  // aid-workflow 20260720: 当前 payload 是否被截断（用于显示提示）
  isPayloadTruncated(): boolean {
    return this.getSharePayload().indexOf(QrCodeBuilder.TRUNCATED_FLAG) !== -1
  }

  // ==================== Issue #16 长按菜单 ====================
  // aid-workflow 20260616: 长按按钮 → 弹出候选菜单 (FR-1)
  // 无候选时不弹 (FMEA C4: ln/log 首版不映射)
  onLongPress(label: string): void {
    if (!LongPressMenu.hasCandidates(label)) return
    this.longPressSource = label
    this.showLongPressMenu = true
  }

  // aid-workflow 20260616: 点击候选 → 复用 onFunc 插入 + 关闭菜单 (FR-3)
  // FMEA C3: 必须复用 onFunc, 禁止另写插入逻辑
  onLongPressCandidate(item: string): void {
    this.showLongPressMenu = false
    this.onFunc(item)
  }

  // ==================== Issue #17 粘贴即计算 ====================
  // aid-workflow 20260617 Issue #17: 页面挂载/恢复时尝试自动粘贴
  // ArkTS @Entry 组件生命周期：onPageShow 等价于 Android onResume
  onPageShow(): void {
    this.onPaste()  // 异步 fire-and-forget; onPaste 内部 await
  }

  // aid-workflow 20260617 Issue #26: 跳转到函数图像绘制页
  // 传当前 expression (若含 x 变量,GraphPage 复用;否则用默认 sin(x))
  onGraphClick(): void {
    router.pushUrl({
      url: 'pages/GraphPage',
      params: { expression: this.expression }
    }).catch((err: Error): void => {
      // 路由失败不弹窗,仅 log
      console.error('[GraphPage] pushUrl failed: ' + err.message)
    })
  }

  // aid-workflow 20260617 Issue #17: 从剪贴板粘贴并自动计算
  // - 复用 onEquals()（push history）
  // - 复用 computePreview()（校验）
  // - lastPastedHash 去重（FMEA-4）
  // - 失败仅 Toast，不弹窗不震动
  // - FMEA-5: 系统异常静默；FMEA-6: 空白静默；FMEA-2: 超长截断
  // 注意: pasteboard.getData() 在 HarmonyOS 4.0+ 是 async, 必须 await
  private async onPaste(): Promise<void> {
    let text: string = ''
    try {
      // getData 返回 Promise<PasteData>，需要 await
      const data: pasteboard.PasteData = await pasteboard.getSystemPasteboard().getData()
      if (data === null || data === undefined) return
      const primary: string = data.getPrimaryText()
      if (primary === null || primary === undefined) return
      text = primary.trim()
    } catch (_e) {
      return  // FMEA-5: 系统异常静默
    }

    if (text.length === 0) return  // FMEA-6: 空白静默

    if (text.length > 200) text = text.substring(0, 200).trim()  // FMEA-2: 超长截断
    if (text.length === 0) return

    const hash: number = this.computeHash(text)
    if (hash === this.lastPastedHash) return  // FMEA-4: 静默去重

    if (this.computePreview(text, this.radianMode).length === 0) {
      promptAction.showToast({ message: '非数学表达式', duration: 1500 })
      return
    }

    this.lastPastedHash = hash
    this.expression = text       // @Watch 自动重算 preview
    this.onEquals()              // 复用：计算 + push history
  }

  // aid-workflow 20260617 Issue #17: 简单字符串 hash（仅用于去重，不强加密）
  // 字符 code 累加 + 长度系数，避免碰撞概率
  private computeHash(text: string): number {
    let h: number = 0
    for (let i: number = 0; i < text.length; i++) {
      h = (h * 31 + text.charCodeAt(i)) | 0
    }
    return (h ^ text.length) | 0
  }

  onHistoryTap(item: HistoryItem): void { this.expression = item.expression; this.showHistory = false; this.searchQuery = '' }
  onHistoryDelete(item: HistoryItem): void {
    const keep: HistoryItem[] = []
    for (let i: number = 0; i < this.history.length; i++) { if (this.history[i].id !== item.id) keep.push(this.history[i]) }
    this.history = keep
    if (this.prefs) this.prefs.setHistory(this.history)
  }

  // aid-workflow 20260616: 按日期分组 (今天/昨天/更早)
  // aid-workflow 20260617 Issue #24: 过滤后分组,空 query 透传 (FR-24-08)
  // 每次 build 时即时计算, 无缓存, 无副作用
  getHistorySections(): HistorySection[] {
    const filtered: HistoryItem[] = filterHistoryByQuery(this.history, this.searchQuery)
    return groupHistoryByDate(filtered, Date.now())
  }

  // ==================== 主题颜色（对齐 Android 原版） ====================
  // themeIdx: 0=默认浅色  1=AMOLED纯黑  2=暗色
  // 默认：Android values/colors.xml 浅色主题
  // 暗色：Android values-night/colors.xml 暗色主题

  /** 背景色（默认白 #FFFFFF） */
  getBg(): string {
    if (this.themeIdx === 1) return '#000000'   // AMOLED
    if (this.themeIdx === 2) return '#121212'   // 暗色
    return '#FFFFFF'                              // 默认浅色
  }

  /** 按钮背景色 */
  getBtnBg(): string {
    if (this.themeIdx === 1) return '#1a1a1a'   // AMOLED: 微亮于纯黑背景
    if (this.themeIdx === 2) return '#333333'
    return '#EFEFEF'
  }

  /** 面板背景色 */
  getPanelBg(): string {
    if (this.themeIdx === 1) return '#0a0a0a'   // AMOLED: 稍亮于纯黑
    if (this.themeIdx === 2) return '#323232'
    return '#FFFFFF'
  }

  /** 功能/常量按钮背景（比普通按钮稍暗以区分层级） */
  getFuncBg(): string {
    if (this.themeIdx === 1) return '#111111'
    if (this.themeIdx === 2) return '#333333'
    return '#E8E8E8'
  }

  /** 运算符按钮色（默认浅蓝 #B4D2E4） */
  getOp(): string {
    if (this.themeIdx === 2) return '#0070BC'
    return '#B4D2E4'
  }

  /** 等号按钮色（默认浅粉 #DCB5C5） */
  getEq(): string {
    if (this.themeIdx === 2) return '#B3004D'
    return '#DCB5C5'
  }

  /** 清除按钮色（默认浅绿 #B7DABD） */
  getClr(): string {
    if (this.themeIdx === 2) return '#00BA20'
    return '#B7DABD'
  }

  /** 错误文字色 */
  getErr(): string { return '#F44B3F' }

  /** 主文字色（默认黑 #000000） */
  getT1(): string {
    if (this.themeIdx >= 1) return '#EFEFEF'
    return '#000000'
  }

  /** 次要文字色（默认深灰 #595959） */
  getT2(): string {
    if (this.themeIdx >= 1) return '#BDBDBD'
    return '#595959'
  }

  /** 运算符文字色（白字在有色按钮上） */
  getBtnText(): string {
    if (this.themeIdx >= 1) return '#EFEFEF'
    return '#000000'
  }

  // ==================== 主布局 ====================
  // aid-workflow 20260616: 长按候选菜单面板 (FR-2/FR-3/FR-4)
  // 半透明遮罩 + 居中菜单列表, Stack 层级隔离 (FMEA C5)
  @Builder LongPressMenuPanel() {
    Stack() {
      // 1. 遮罩层 (FR-4: 点击外部关闭)
      Column().width('100%').height('100%')
        .backgroundColor(MENU_MASK_COLOR).opacity(MENU_MASK_OPACITY)
        .onClick((): void => { this.showLongPressMenu = false })

      // 2. 菜单容器 (FR-2: 居中垂直列表)
      Column() {
        ForEach(LongPressMenu.getCandidates(this.longPressSource), (item: string) => {
          Text(item)
            .fontSize(MENU_FONT_SIZE).fontColor(this.getT1())
            .width('100%').height(MENU_ITEM_HEIGHT)
            .textAlign(TextAlign.Center)
            .backgroundColor(this.getPanelBg())
            .onClick((): void => { this.onLongPressCandidate(item) })
        })
      }
      .width(MENU_WIDTH_RATIO).constraintSize({ maxWidth: MENU_MAX_WIDTH })
      .backgroundColor(this.getPanelBg()).borderRadius(MENU_BORDER_RADIUS)
      .padding(MENU_PADDING)
    }
    .width('100%').height('100%')
  }

  build() {
    Stack() {
      if (this.isLandscape) {
        // 横屏：左边按钮 + 可选右侧历史（有折叠按钮）
        Row() {
          Column() {
            this.DisplayPanel()
            this.ButtonGrid()
          }
          .layoutWeight(this.showHistory ? 3 : 1).height('100%')
          if (this.showHistory) this.HistoryPanel()
        }
        .width('100%').height('100%').backgroundColor(this.getBg())
      } else {
        // 竖屏：Swiper 包裹三页键盘 (Issue #29) — 始终渲染,不再因 this.mode 分支跳过
        Column() {
          this.DisplayPanel()
          this.ToggleRow()
          this.ButtonGrid()
          if (this.showHistory) this.HistoryPanel()
        }
        .width('100%').height('100%').backgroundColor(this.getBg())
      }
      if (this.showSettings) this.SettingsPanel()
      if (this.showAbout) this.AboutPanel()
      // aid-workflow 20260615: Issue #13 分享二维码模态层
      if (this.showShare) this.SharePanel()
      // aid-workflow 20260616: Issue #16 长按候选菜单 (FR-1/FR-2, 顶层遮罩盖全屏)
      if (this.showLongPressMenu) this.LongPressMenuPanel()
      // aid-workflow 20260617 Issue #28: 记忆槽选择面板 (顶层遮罩盖全屏)
      if (this.showMemoryPicker) this.MemoryPickerPanel()
    }
    .width('100%').height('100%')
    .onAreaChange((_old: Area, newVal: Area): void => {
      const w: number = newVal.width as number
      const h: number = newVal.height as number
      this.isLandscape = w > h
      // 横屏时自动开启科学模式（但不强制显示历史）
      if (this.isLandscape) this.scientific = true
    })
  }

  // ==================== 显示屏 ====================
  @Builder DisplayPanel() {
    Column() {
    // aid-workflow 20260615: 分享按钮行已移至 ToggleRow（避开 DisplayPanel 的 LongPressGesture）

    // 横屏时在显示屏右侧加历史切换按钮
    if (this.isLandscape) {
      Row() {
        Text(this.expression.length > 0 ? this.expression : ' ')
          .fontSize(14).fontColor(this.getT2()).textAlign(TextAlign.End).maxLines(3).layoutWeight(1)
        Text(this.showHistory ? '◀' : '▶')
          .fontSize(14).fontColor(this.getOp()).padding({ left: 8 })
          .onClick((): void => { this.showHistory = !this.showHistory })
      }
      .width('100%').padding({ right: 8, left: 8 })
    } else {
      Text(this.expression.length > 0 ? this.expression : ' ')
        .fontSize(18).fontColor(this.getT2()).width('100%').textAlign(TextAlign.End)
        .padding({ right: 12, left: 12 }).maxLines(3)
    }
    // aid-workflow 20260612: 实时预览行（expression 下方、result/errorMsg 上方）
    Text(this.preview.length > 0 ? this.preview : ' ')
      .fontSize(this.isLandscape ? 12 : 14)
      .fontColor(this.getT2())
      .width('100%').textAlign(TextAlign.End)
      .padding({ right: 12, left: 12, top: 2, bottom: 2 })
      .maxLines(1)
      if (this.errorMsg.length > 0) {
        Text(this.errorMsg).fontSize(this.isLandscape ? 22 : 28).fontColor(this.getErr())
          .width('100%').textAlign(TextAlign.End).padding({ right: 12, left: 12 })
      } else {
        // aid-workflow 20260617: Issue #27 用 Stack 包裹结果 Text + 模式切换按钮
        // 横屏隐藏按钮(节省空间, 仿 ToggleRow 策略)
        Stack({ alignContent: Alignment.TopEnd }) {
          Text(this.result.length > 0 ? this.formatResultForDisplay() : '0')
            .fontSize(this.isLandscape ? 28 : 36).fontWeight(FontWeight.Bold).fontColor(this.getT1())
            .width('100%').textAlign(TextAlign.End).padding({ right: 12, left: 12 })
          if (!this.isLandscape && this.result.length > 0) {
            Text(this.displayMode === DisplayMode.FRACTION ? '0.5' : '1/2')
              .fontSize(11).fontColor(this.displayMode === DisplayMode.FRACTION ? this.getOp() : this.getT2())
              .padding({ left: 6, right: 6, top: 2, bottom: 2 })
              .border({ width: 1, color: this.displayMode === DisplayMode.FRACTION ? this.getOp() : this.getT2(), radius: 4 })
              .margin({ right: 12, top: 6 })
              .onClick((): void => { this.onToggleDisplayMode() })
          }
        }.width('100%')
      }
    }
    .width('100%').padding(this.isLandscape ? { top: 8, bottom: 2 } : { top: 16, bottom: 8 })
    .gesture(LongPressGesture().onAction((): void => { this.onCopy() }))
  }

  // ==================== 分享二维码模态层（Issue #13） ====================
  @Builder SharePanel() {
    Column() {
      // 标题栏
      Row() {
        Text('二维码分享').fontSize(18).fontWeight(FontWeight.Bold).fontColor(this.getT1())
        Blank()
        Text('✕').fontSize(20).fontColor(this.getT2())
          .onClick((): void => { this.onShareClose() })
      }.width('100%').padding(16)

      // QR 码区域（ArkUI 内置 QRCode 组件 + 强制白底，不受主题影响）
      QRCode(this.getSharePayload())
        .width(240).height(240)
        .color(Color.Black)
        .backgroundColor(Color.White)

      // 文本副本（人工可读）
      Text(this.expression + ' = ' + this.result)
        .fontSize(14).fontColor(this.getT1())
        .padding({ top: 12 })
        .maxLines(2)

      // 截断提示（payload 超长时）
      if (this.isPayloadTruncated()) {
        Text('⚠ 算式过长已截断').fontSize(11).fontColor(this.getT2()).padding({ top: 4 })
      }

      // 操作提示
      Text('用手机扫码即可在手机上查看算式与结果')
        .fontSize(11).fontColor(this.getT2()).padding({ top: 8 })
    }
    .width('85%').padding(24).backgroundColor(this.getPanelBg()).borderRadius(16)
  }

  // aid-workflow 20260617 Issue #28: 数字键长按手势构造器（仅 1-6 触发存槽；0/7/8/9 noop）
  // 返回类型推断为 LongPressGesture；显式标 GestureConfig 在 ArkTS 严格模式下未导出
  private buildDigitLongPressGesture(l: string) {
    if (l < '1' || l > '6') {
      return LongPressGesture().onAction((): void => {})
    }
    return LongPressGesture().onAction((): void => { this.onLongPressDigit(l) })
  }

  // aid-workflow 20260617 Issue #28: 派生记忆激活指示文案
  private getMemoryActiveLabel(): string {
    return MemorySlots.lastUsedLabel(this.memorySlots)
  }

  // aid-workflow 20260617 Issue #28: 派生 MR 按钮是否可用
  private getMRButtonEnabled(): boolean {
    return MemorySlots.anyHasValue(this.memorySlots)
  }

  // aid-workflow 20260617 Issue #28: 数字键 1-6 长按 → 存槽 + toast
  private onLongPressDigit(d: string): void {
    // 解析 display（剥千分位逗号），非有限值拒绝
    const raw: string = this.result.replace(/,/g, '')
    const value: number = Number.parseFloat(raw)
    if (!Number.isFinite(value)) {
      promptAction.showToast({ message: '无法存入', duration: 1500 })
      return
    }
    const idx: number = Number(d)
    this.memorySlots = MemorySlots.save(this.memorySlots, idx, value)
    promptAction.showToast({ message: `已存入 M${idx}`, duration: 1500 })
  }

  // aid-workflow 20260617 Issue #28: MR 按钮点击 → 打开/关闭面板
  private onMRClick(): void {
    if (!MemorySlots.anyHasValue(this.memorySlots)) return  // FMEA-FM-04 兜底
    this.showMemoryPicker = !this.showMemoryPicker
    // FMEA-FM-06: 互斥关闭 LongPressMenu
    if (this.showLongPressMenu) this.showLongPressMenu = false
  }

  // aid-workflow 20260617 Issue #28: 选槽调出 → 写入输入流
  private onPickSlot(idx: 1 | 2 | 3 | 4 | 5 | 6): void {
    const value: number | null = MemorySlots.recall(this.memorySlots, idx)
    if (value === null) return  // FMEA 兜底：空槽不应被点中
    this.expression = this.expression + String(value)
    this.errorMsg = ''
    this.showMemoryPicker = false
  }

  // aid-workflow 20260617 Issue #28: 面板遮罩点击 → 关闭
  private onMemoryMaskClick(): void {
    this.showMemoryPicker = false
  }

  // aid-workflow 20260617 Issue #28: 6 槽选择面板 (与 LongPressMenuPanel 风格一致)
  @Builder MemoryPickerPanel() {
    Stack() {
      // 遮罩
      Column().width('100%').height('100%')
        .backgroundColor(MENU_MASK_COLOR).opacity(MENU_MASK_OPACITY)
        .onClick((): void => { this.onMemoryMaskClick() })

      // 居中浮层
      Column() {
        ForEach(this.memorySlots.slots, (slot: MemorySlot) => {
          Row() {
            Text(`M${slot.slotIndex}`)
              .fontSize(MENU_FONT_SIZE)
              .fontColor(slot.isEmpty() ? this.getT2() : this.getT1())
              .width(50)
            Text(slot.isEmpty() ? '—' : String(slot.value))
              .fontSize(MENU_FONT_SIZE)
              .fontColor(slot.isEmpty() ? this.getT2() : this.getT1())
              .layoutWeight(1)
          }
          .width('100%').height(MENU_ITEM_HEIGHT)
          .opacity(slot.isEmpty() ? 0.4 : 1.0)
          .enabled(!slot.isEmpty())
          .onClick((): void => { this.onPickSlot(slot.slotIndex) })
        }, (slot: MemorySlot): string => String(slot.slotIndex))
      }
      .width('60%').constraintSize({ maxWidth: MENU_MAX_WIDTH })
      .backgroundColor(this.getPanelBg()).borderRadius(MENU_BORDER_RADIUS)
      .padding(MENU_PADDING)
    }
    .width('100%').height('100%')
  }

  // ==================== 模式切换栏（仅竖屏显示） ====================
  // aid-workflow 20260618 Issue #29: 模式按钮三态循环 (基础 → 科学 → 程序员 → 基础)
  @Builder ToggleRow() {
    Row() {
      Text(this.getCurrentModeLabel()).fontSize(12).fontColor(this.getOp())
        .padding({ left: 12, right: 12, top: 4, bottom: 4 })
        .border({ width: 1, color: this.getOp(), radius: 8 })
        .onClick((): void => { this.cycleMode() })
      Blank()
      // aid-workflow 20260617 Issue #26: 绘图入口按钮
      Text('📈').fontSize(14).fontColor(this.getT2()).padding(8)
        .onClick((): void => { this.onGraphClick() })
      // aid-workflow 20260617 Issue #17: 粘贴按钮（手动触发粘贴）
      Text('📋').fontSize(14).fontColor(this.getT2()).padding(8)
        .onClick((): void => { this.onPaste() })
      Text(this.showHistory ? '▲ 历史' : '▼ 历史').fontSize(12).fontColor(this.getT2()).padding(8)
        .onClick((): void => { this.showHistory = !this.showHistory })
      // aid-workflow 20260615: Issue #13 一键分享按钮
      Button('分享', { type: ButtonType.Normal })
        .fontSize(11).fontColor(this.checkShareEnabled() ? this.getOp() : this.getT2())
        .backgroundColor(Color.Transparent)
        .height(22).padding({ left: 6, right: 6 })
        .margin({ right: 4 })
        .onClick((): void => { this.onShareClick() })
      Text('⚙').fontSize(16).fontColor(this.getT2()).padding(8)
        .onClick((): void => { this.showSettings = true })
    }
    .width('100%').padding({ left: 16, right: 16, bottom: 4 })
  }

  // ==================== 按钮网格 ====================
  // aid-workflow 20260618 Issue #29: 竖屏 Swiper 包裹三页键盘, 横屏沿用原单页科学模式
  @Builder ButtonGrid() {
    Column() {
      // aid-workflow 20260617 Issue #28: 记忆行（MR + 激活指示）
      Row() {
        Text('M').fontSize(12).fontColor(this.getT2())
          .width('17%').height(24).textAlign(TextAlign.Center)
        Text(this.getMemoryActiveLabel()).fontSize(12).fontColor(this.getT2())
          .layoutWeight(1).height(24).textAlign(TextAlign.Start)
        Text('MR').fontSize(14).fontColor(this.getMRButtonEnabled() ? this.getT1() : this.getT2())
          .width('17%').height(28).textAlign(TextAlign.Center)
          .backgroundColor(this.getBtnBg()).borderRadius(50)
          .margin({ left: 4, right: 4 })
          .enabled(this.getMRButtonEnabled())
          .opacity(this.getMRButtonEnabled() ? 1.0 : 0.4)
          .onClick((): void => { this.onMRClick() })
      }.width('100%').margin({ bottom: 4 })

      if (this.isLandscape) {
        // 横屏: 沿用原单页布局, 强制 scientific=true
        this.LandscapeGrid()
      } else {
        // 竖屏: Swiper 包裹三页
        Swiper(this.swpController) {
          this.BasicGrid()
          this.ScientificGrid()
          this.ProgrammerGrid()
        }
        .index(this.currentMode)
        .loop(false)
        .indicator(new DotIndicator())
        .onChange((idx: number): void => { this.onSwiperChange(idx) })
        .width('100%').layoutWeight(1)
      }
    }
    .width('100%').padding({ left: 8, right: 8 }).layoutWeight(this.isLandscape ? 0 : 1)
  }

  // aid-workflow 20260618 Issue #29: 基础键盘页
  @Builder BasicGrid() {
    Column() {
      Row() { this.BtnActPct('AC'); this.BtnOpPct('%'); this.BtnOpPct('('); this.BtnOpPct(')'); this.BtnOpPct('÷') }
      Row() { this.BtnDig('7'); this.BtnDig('8'); this.BtnDig('9'); this.BtnOp('×') }
      Row() { this.BtnDig('4'); this.BtnDig('5'); this.BtnDig('6'); this.BtnOp('-') }
      Row() { this.BtnDig('1'); this.BtnDig('2'); this.BtnDig('3'); this.BtnOp('+') }
      Row() { this.BtnDig('0'); this.BtnOp('.'); this.BtnAct('⌫'); this.BtnEq() }
    }.width('100%').layoutWeight(1).justifyContent(FlexAlign.SpaceBetween)
  }

  // aid-workflow 20260618 Issue #29: 科学键盘页
  @Builder ScientificGrid() {
    Column() {
      Row() { this.BtnFunc('sin'); this.BtnFunc('cos'); this.BtnFunc('tan'); this.BtnFunc('ln'); this.BtnFunc('log') }
      Row() { this.BtnFunc('arcsi'); this.BtnFunc('arcco'); this.BtnFunc('arcta'); this.BtnConst('π'); this.BtnConst('e') }
      Row() { this.BtnActPct('AC'); this.BtnOpPct('%'); this.BtnOpPct('('); this.BtnOpPct(')'); this.BtnOpPct('÷') }
      Row() { this.BtnDig('7'); this.BtnDig('8'); this.BtnDig('9'); this.BtnOp('×') }
      Row() { this.BtnDig('4'); this.BtnDig('5'); this.BtnDig('6'); this.BtnOp('-') }
      Row() { this.BtnDig('1'); this.BtnDig('2'); this.BtnDig('3'); this.BtnOp('+') }
      Row() { this.BtnDig('0'); this.BtnOp('.'); this.BtnAct('⌫'); this.BtnEq() }
    }.width('100%').layoutWeight(1).justifyContent(FlexAlign.SpaceBetween)
  }

  // aid-workflow 20260618 Issue #29: 程序员键盘页 (HEX/DEC/OCT/BIN + 位运算)
  // 本期 UI-only, 数字/位运算按键复用 onDigit / onOp 通道, 后续 issue 接入 CalcEngine
  @Builder ProgrammerGrid() {
    Column() {
      Row() { this.BtnBase('HEX'); this.BtnBase('DEC'); this.BtnBase('OCT'); this.BtnBase('BIN') }
      Row() { this.BtnFunc('AND'); this.BtnFunc('OR'); this.BtnFunc('NOT'); this.BtnFunc('XOR') }
      Row() { this.BtnOp('<<'); this.BtnOp('>>'); this.BtnAct('⌫'); this.BtnAct('AC') }
      Row() { this.BtnDig('7'); this.BtnDig('8'); this.BtnDig('9'); this.BtnOp('-') }
      Row() { this.BtnDig('4'); this.BtnDig('5'); this.BtnDig('6'); this.BtnOp('+') }
      Row() { this.BtnDig('1'); this.BtnDig('2'); this.BtnDig('3'); this.BtnOp('×') }
      Row() { this.BtnDig('0'); this.BtnOp('.'); this.BtnFunc('MOD'); this.BtnEq() }
    }.width('100%').layoutWeight(1).justifyContent(FlexAlign.SpaceBetween)
  }

  // aid-workflow 20260618 Issue #29: 横屏单页布局 (保留 scientific 切换, 不渲染 Swiper)
  @Builder LandscapeGrid() {
    Column() {
      if (this.scientific) {
        Row() { this.BtnFunc('sin'); this.BtnFunc('cos'); this.BtnFunc('tan'); this.BtnFunc('ln'); this.BtnFunc('log') }
        // Issue #21: 阶乘按钮 — 6 列布局,所有按钮 width 18%→16%
        Row() { this.BtnFunc16('arcsi'); this.BtnFunc16('arcco'); this.BtnFunc16('arcta'); this.BtnConst16('π'); this.BtnConst16('e'); this.BtnOpPct16('!') }
      }
      Row() { this.BtnActPct('AC'); this.BtnOpPct('%'); this.BtnOpPct('('); this.BtnOpPct(')'); this.BtnOpPct('÷') }
      Row() { this.BtnDig('7'); this.BtnDig('8'); this.BtnDig('9'); this.BtnOp('×') }
      Row() { this.BtnDig('4'); this.BtnDig('5'); this.BtnDig('6'); this.BtnOp('-') }
      Row() { this.BtnDig('1'); this.BtnDig('2'); this.BtnDig('3'); this.BtnOp('+') }
      Row() { this.BtnDig('0'); this.BtnOp('.'); this.BtnAct('⌫'); this.BtnEq() }
    }.width('100%')
  }

  // aid-workflow 20260618 Issue #29: 基数按钮 (HEX/DEC/OCT/BIN)
  // 本期点击仅提示用户, 后续 issue 接入 CalcEngine 切换数字基数
  @Builder BtnBase(l: string) {
    Text(l).fontSize(13).fontColor(this.getT1()).width('23%').height(40)
      .textAlign(TextAlign.Center).backgroundColor(this.getFuncBg()).borderRadius(50).margin(2)
      .onClick((): void => { promptAction.showToast({ message: l + ' (本期仅 UI 展示)' }) })
  }

  /** 数字按钮 */
  @Builder BtnDig(l: string) {
    Text(l).fontSize(this.isLandscape ? 16 : 22).fontColor(this.getT1()).width('17%').height(this.isLandscape ? 36 : 56).textAlign(TextAlign.Center).backgroundColor(this.getBtnBg()).borderRadius(50).margin(this.isLandscape ? 1 : 4).onClick((): void => { this.onDigit(l) })
      // aid-workflow 20260617 Issue #28: 仅 1-6 数字键挂长按手势（0/7/8/9 不存槽）
      .gesture(this.buildDigitLongPressGesture(l))
  }

  // ==================== Issue #22 程序员模式 (Issue #22) 已删 ====================
  // 历史原因: Issue #22 实现了 CalculatorMode 双状态机 + 显示 4 进制 + A-F 键盘,
  // 后续 Issue #29 用 KeyboardMode + Swiper 重构, 但 build() 残留 this.mode 分支
  // 导致 prefs prog=1 时永远走老分支, Swiper 不可见, % 按钮消失。
  // 删除: ProgrammerSection / ProgrammerKeyboard / BtnProg / parseExpressionAsNumber
  // 保留: Swiper 内 ProgrammerGrid (HEX/DEC/OCT/BIN 按钮 + 位运算按钮, 接 CalcEngine)

  /** 运算符按钮（含 %） */
  @Builder BtnOp(l: string) { Text(l).fontSize(this.isLandscape ? 14 : 20).fontColor(this.getBtnText()).width('17%').height(this.isLandscape ? 36 : 56).textAlign(TextAlign.Center).backgroundColor(this.getOp()).borderRadius(50).margin(this.isLandscape ? 1 : 4).onClick((): void => { this.onOp(l) }) }

  /** 科学函数按钮 */
  @Builder BtnFunc(l: string) {
    Text(l).fontSize(this.isLandscape ? 11 : 14).fontColor(this.getT1()).width('18%').height(this.isLandscape ? 30 : 46).textAlign(TextAlign.Center).backgroundColor(this.getFuncBg()).borderRadius(50).margin(this.isLandscape ? 1 : 3).onClick((): void => { this.onFunc(l) })
      // aid-workflow 20260616: 长按弹出候选菜单 (FR-1)
      // 系统保证短按触发 onClick, 长按触发 onAction, 互不冲突 (FMEA C5)
      .gesture(LongPressGesture().onAction((): void => { this.onLongPress(l) }))
  }

  /** 常量按钮 */
  @Builder BtnConst(l: string) { Text(l).fontSize(this.isLandscape ? 13 : 18).fontColor(this.getOp() === '#B4D2E4' ? '#4684E3' : this.getOp()).width('18%').height(this.isLandscape ? 30 : 46).textAlign(TextAlign.Center).backgroundColor(this.getFuncBg()).borderRadius(50).margin(this.isLandscape ? 1 : 3).onClick((): void => { this.onConst(l) }) }

  /** 动作按钮（AC/退格） */
  @Builder BtnAct(l: string) { Text(l).fontSize(this.isLandscape ? 14 : 20).fontColor(this.getBtnText()).width('17%').height(this.isLandscape ? 36 : 56).textAlign(TextAlign.Center).backgroundColor(l === 'AC' ? this.getClr() : this.getBtnBg()).borderRadius(50).margin(this.isLandscape ? 1 : 4).onClick((): void => { if (l === 'AC') this.onAC(); else this.onBS() }) }

  /** 等号按钮 */
  @Builder BtnEq() { Text('=').fontSize(this.isLandscape ? 18 : 24).fontWeight(FontWeight.Bold).fontColor(this.getBtnText()).width('22%').height(this.isLandscape ? 36 : 56).textAlign(TextAlign.Center).backgroundColor(this.getEq()).borderRadius(50).margin(this.isLandscape ? 1 : 4).onClick((): void => { this.onEquals() }) }

  /** 运算符按钮 - 5列布局版 */
  @Builder BtnOpPct(l: string) { Text(l).fontSize(this.isLandscape ? 14 : 20).fontColor(this.getBtnText()).width('17%').height(this.isLandscape ? 36 : 56).textAlign(TextAlign.Center).backgroundColor(this.getOp()).borderRadius(50).margin(this.isLandscape ? 1 : 4).onClick((): void => { this.onOp(l) }) }

  /** Issue #21: 阶乘按钮 (6 列布局版) */
  @Builder BtnOpPct16(l: string) { Text(l).fontSize(this.isLandscape ? 14 : 20).fontColor(this.getBtnText()).width('16%').height(this.isLandscape ? 36 : 56).textAlign(TextAlign.Center).backgroundColor(this.getOp()).borderRadius(50).margin(this.isLandscape ? 1 : 4).onClick((): void => { this.onOp(l) }) }

  /** Issue #21: 6 列布局版科学函数按钮 (width 18%→16%) */
  @Builder BtnFunc16(l: string) { Text(l).fontSize(this.isLandscape ? 11 : 14).fontColor(this.getT1()).width('16%').height(this.isLandscape ? 30 : 46).textAlign(TextAlign.Center).backgroundColor(this.getFuncBg()).borderRadius(50).margin(this.isLandscape ? 1 : 3).onClick((): void => { this.onFunc(l) }) }

  /** Issue #21: 6 列布局版常量按钮 (width 18%→16%) */
  @Builder BtnConst16(l: string) { Text(l).fontSize(this.isLandscape ? 13 : 18).fontColor(this.getOp() === '#B4D2E4' ? '#4684E3' : this.getOp()).width('16%').height(this.isLandscape ? 30 : 46).textAlign(TextAlign.Center).backgroundColor(this.getFuncBg()).borderRadius(50).margin(this.isLandscape ? 1 : 3).onClick((): void => { this.onConst(l) }) }

  /** 动作按钮 - 5列布局版 */
  @Builder BtnActPct(l: string) { Text(l).fontSize(this.isLandscape ? 14 : 20).fontColor(this.getBtnText()).width('17%').height(this.isLandscape ? 36 : 56).textAlign(TextAlign.Center).backgroundColor(l === 'AC' ? this.getClr() : this.getBtnBg()).borderRadius(50).margin(this.isLandscape ? 1 : 4).onClick((): void => { if (l === 'AC') this.onAC(); else this.onBS() }) }

  // ==================== 历史面板（仿 Android SlidingUpPanelLayout） ====================

  @Builder HistoryPanel() {
    Column() {
      // 拖拽手柄 / 折叠按钮（始终可见，仿 Android sliding_layout_button）
      Row() {
        // 手柄横条
        Text('').width(40).height(4).backgroundColor(this.getT2()).borderRadius(2)
      }
      .width('100%').height(24).justifyContent(FlexAlign.Center)
      .onClick((): void => { this.showHistory = false; this.searchQuery = '' })

      // aid-workflow 20260617 Issue #24: 搜索框 (FR-24-01)
      this.SearchBox()

      if (this.history.length === 0) {
        Text('暂无计算记录').fontSize(13).fontColor(this.getT2()).width('100%').textAlign(TextAlign.Center).padding(20)
      } else if (this.searchQuery.length > 0 && this.getHistorySections().every((s: HistorySection): boolean => s.items.length === 0)) {
        // aid-workflow 20260617 Issue #24: 无匹配占位 (FR-24-07)
        Text('无匹配记录').fontSize(13).fontColor(this.getT2()).width('100%').textAlign(TextAlign.Center).padding(20)
      } else {
        List() {
          // aid-workflow 20260616: 按日期分组 (今天/昨天/更早), 每段组内 newest-first
          ForEach(this.getHistorySections(), (section: HistorySection) => {
            if (section.items.length > 0) {
              ListItem() { this.SectionHeader(section.title) }
              ForEach(section.items, (item: HistoryItem) => {
                ListItem() {
                  Column() {
                    Text(item.expression).fontSize(12).fontColor(this.getT2()).maxLines(1)
                    Text(item.result).fontSize(15).fontWeight(FontWeight.Bold).fontColor(this.getOp())
                  }
                  .alignItems(HorizontalAlign.Start).width('100%').padding(this.isLandscape ? 8 : 12)
                  .onClick((): void => { this.onHistoryTap(item) })
                }
                .swipeAction({ end: { builder: (): void => { this.DelBtn(item) } } })
              }, (item: HistoryItem): string => item.id.toString())
            }
          }, (section: HistorySection): string => section.key.toString())
        }
        .layoutWeight(1)
      }
    }
    .layoutWeight(this.isLandscape ? 1 : 0)
    .width('100%').height(this.isLandscape ? '100%' : 'auto')
    .backgroundColor(this.getPanelBg())
    .borderRadius(this.isLandscape ? 0 : { topLeft: 16, topRight: 16 })
  }

  // aid-workflow 20260616: 段标题 (今天 / 昨天 / 更早)
  @Builder SectionHeader(title: string) {
    Row() {
      Text(title)
        .fontSize(11)
        .fontColor(this.getT2())
        .padding({ left: 12, top: 8, bottom: 4 })
    }
    .width('100%')
    .backgroundColor(this.getPanelBg())
  }

  @Builder DelBtn(item: HistoryItem) {
    Text('删除').fontSize(14).fontColor(this.getT1()).padding(16).backgroundColor(this.getErr()).height('100%')
      .onClick((): void => { this.onHistoryDelete(item) })
  }

  // aid-workflow 20260617 Issue #24: 搜索框 (FR-24-01 / FR-24-02)
  // TextInput + ✕ 清除按钮; 背景随主题 getPanelBg
  @Builder SearchBox() {
    Row() {
      TextInput({ placeholder: '搜索算式或结果', text: this.searchQuery })
        .layoutWeight(1)
        .fontSize(14)
        .fontColor(this.getT1())
        .backgroundColor('transparent')
        .placeholderColor(this.getT2())
        .onChange((value: string): void => { this.searchQuery = value })
      if (this.searchQuery.length > 0) {
        Text('✕').fontSize(16).fontColor(this.getT2())
          .padding(8)
          .onClick((): void => { this.searchQuery = '' })
      }
    }
    .width('100%').height(this.isLandscape ? 36 : 40)
    .padding({ left: 12, right: 12 })
    .backgroundColor(this.getPanelBg())
  }

  // ==================== 设置面板 ====================
  @Builder SettingsPanel() {
    Column() {
      Row() {
        Text('设置').fontSize(18).fontWeight(FontWeight.Bold).fontColor(this.getT1())
        Blank()
        Text('✕').fontSize(20).fontColor(this.getT2()).onClick((): void => { this.showSettings = false })
      }.width('100%').padding(16)
      List() {
        ListItem() { this.ToggleItem('振动反馈', this.vibrateOn, (v: boolean): void => { this.vibrateOn = v; this.savePref('vibrateOn', v) }) }
        ListItem() { this.ToggleItem('防休眠', this.preventSleep, (v: boolean): void => { this.preventSleep = v; this.savePref('preventSleep', v) }) }
        ListItem() { this.ToggleItem('弧度模式', this.radianMode, (v: boolean): void => { this.radianMode = v; this.savePref('radianMode', v) }) }
        ListItem() { this.ThemeItem() }
        ListItem() {
          Row() { Text('关于 OpenCalc').fontSize(15).fontColor(this.getT2()); Blank(); Text('>').fontColor(this.getT2()) }
          .width('100%').padding(12).onClick((): void => { this.showSettings = false; this.showAbout = true })
        }
      }
    }
    .width('85%').backgroundColor(this.getPanelBg()).borderRadius(16)
  }

  @Builder ToggleItem(title: string, val: boolean, cb: (v: boolean) => void) {
    Row() {
      Text(title).fontSize(15).fontColor(this.getT1()).layoutWeight(1)
      Toggle({ type: ToggleType.Switch, isOn: val }).onChange((on: boolean): void => { cb(on) })
    }.width('100%').padding(12)
  }

  @Builder ThemeItem() {
    Row() {
      Text('主题').fontSize(15).fontColor(this.getT1()).layoutWeight(1)
      Row() {
        Text('浅色').fontSize(11).fontColor(this.themeIdx === 0 ? '#000' : this.getT2())
          .backgroundColor(this.themeIdx === 0 ? this.getOp() : (this.themeIdx >= 1 ? '#555' : '#DDD'))
          .padding({ left: 8, right: 8, top: 4, bottom: 4 }).borderRadius(8).margin({ left: 2 })
          .onClick((): void => { this.themeIdx = 0; this.savePref('themeIdx', 0) })
        Text('暗色').fontSize(11).fontColor(this.themeIdx === 2 ? '#EFEFEF' : this.getT2())
          .backgroundColor(this.themeIdx === 2 ? '#0070BC' : (this.themeIdx >= 1 ? '#555' : '#DDD'))
          .padding({ left: 8, right: 8, top: 4, bottom: 4 }).borderRadius(8).margin({ left: 2 })
          .onClick((): void => { this.themeIdx = 2; this.savePref('themeIdx', 2) })
        Text('AMOLED').fontSize(11).fontColor(this.themeIdx === 1 ? '#EFEFEF' : this.getT2())
          .backgroundColor(this.themeIdx === 1 ? '#B3004D' : (this.themeIdx >= 1 ? '#555' : '#DDD'))
          .padding({ left: 8, right: 8, top: 4, bottom: 4 }).borderRadius(8).margin({ left: 2 })
          .onClick((): void => { this.themeIdx = 1; this.savePref('themeIdx', 1) })
      }
    }.width('100%').padding(12)
  }

  // ==================== 关于面板 ====================
  @Builder AboutPanel() {
    Column() {
      Text('关于 OpenCalc').fontSize(18).fontWeight(FontWeight.Bold).fontColor(this.getT1()).padding({ bottom: 12 })
      Text('OpenCalc HarmonyOS').fontSize(14).fontColor(this.getT2())
      Text('版本 1.0.0').fontSize(14).fontColor(this.getT2()).padding({ top: 4 })
      Text('原项目: github.com/clementwzk/OpenCalc').fontSize(11).fontColor(this.getT2()).padding({ top: 8 })
      Text('Android 3.2.1 → HarmonyOS').fontSize(11).fontColor(this.getT2()).padding({ top: 2 })
      Text('迁移: github.com/JungleTestLabs/opencalc-harmonyos').fontSize(11).fontColor(this.getOp()).padding({ top: 4 })
      Button('关闭').margin({ top: 16 }).onClick((): void => { this.showAbout = false })
    }
    .width('80%').padding(24).backgroundColor(this.getPanelBg()).borderRadius(16)
  }
}
