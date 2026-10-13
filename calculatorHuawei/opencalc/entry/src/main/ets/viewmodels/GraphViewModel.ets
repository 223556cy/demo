// OpenCalc — 函数图像 ViewModel
// aid-workflow 20260617: Issue #26 函数图像
// 状态管理: 表达式 + 范围 + 采样 + 序列 + 错误

import { CalcEngine } from '../calculator/Calculator'
import { Expression } from '../calculator/Expression'
import { ErrorFlags } from '../model/ErrorFlags'
import { PlotUtils, PlotSeries, Evaluator } from '../common/PlotUtils'

/** 最小采样数 */
const MIN_SAMPLES: number = 50
/** 最大采样数 */
const MAX_SAMPLES: number = 1000
/** 默认采样数 */
const DEFAULT_SAMPLES: number = 200
/** aid-workflow 20260626: 默认 xMin ( -2π ≈ -6.28 ),让 sin/cos 完整周期可见 */
const DEFAULT_X_MIN: number = -2 * Math.PI
/** aid-workflow 20260626: 默认 xMax ( 2π ≈ 6.28 ) */
const DEFAULT_X_MAX: number = 2 * Math.PI

@Observed
export class GraphViewModel {
  /** 函数表达式,默认 sin(x) */
  expression: string = 'sin(x)'
  /** x 区间左端点 */
  xMin: number = DEFAULT_X_MIN
  /** x 区间右端点 */
  xMax: number = DEFAULT_X_MAX
  /** 采样数 */
  samples: number = DEFAULT_SAMPLES
  /** 计算结果曲线;null 表示未计算或计算失败 */
  series: PlotSeries | null = null
  /** 用户可见错误提示;空表示无错误 */
  errorMessage: string = ''
  /** 是否正在计算(预留异步,目前同步) */
  isComputing: boolean = false
  /** 是否为角度模式;true=角度,false=弧度 */
  isDegree: boolean = false

  private engine: CalcEngine = new CalcEngine()
  private expr: Expression = new Expression()

  /**
   * 设置角度/弧度模式
   * @param isDeg true=角度, false=弧度
   */
  setRadianMode(isDeg: boolean): void {
    this.isDegree = isDeg
  }

  /**
   * 触发重算
   * 流程: 校验 → 预处理 → 循环求值 → Y 轴范围 → 错误处理
   */
  compute(): void {
    this.errorMessage = ''
    if (!this.validateInputs()) {
      this.series = null
      return
    }
    this.isComputing = true
    try {
      ErrorFlags.reset()
      // 预处理表达式 (用户显示 → ASCII 内部)
      const cleanExpr: string = this.expr.getCleanExpression(this.expression, '.', ',')
      if (ErrorFlags.syntax_error) {
        this.errorMessage = '表达式语法错误'
        this.series = null
        return
      }
      // 采样求值
      const evaluator: Evaluator = (e: string, x: number): number | null => {
        return this.engine.evaluateAt(e, x, this.isDegree)
      }
      this.series = PlotUtils.sampleSeries(cleanExpr, this.xMin, this.xMax, this.samples, evaluator)
      // 全失败检查
      if (this.series.points.every((p): boolean => p.y === null)) {
        this.errorMessage = '该函数在选定范围内无有效值'
      }
    } catch (e) {
      this.errorMessage = '计算异常: ' + (e instanceof Error ? e.message : String(e))
      this.series = null
    } finally {
      this.isComputing = false
    }
  }

  /**
   * 校验输入
   * @returns true=通过, false=有错误(errorMessage 已设置)
   */
  private validateInputs(): boolean {
    if (this.expression.trim().length === 0) {
      this.errorMessage = '请输入函数表达式'
      return false
    }
    if (!this.hasVariable(this.expression)) {
      this.errorMessage = '请输入含 x 的函数表达式,如 sin(x)'
      return false
    }
    if (!isFinite(this.xMin) || !isFinite(this.xMax)) {
      this.errorMessage = 'xMin / xMax 必须是有效数字'
      return false
    }
    if (this.xMax <= this.xMin) {
      this.errorMessage = 'xMax 必须大于 xMin'
      return false
    }
    if (this.samples < MIN_SAMPLES || this.samples > MAX_SAMPLES) {
      this.errorMessage = 'samples 需在 ' + MIN_SAMPLES + ' - ' + MAX_SAMPLES + ' 之间'
      return false
    }
    return true
  }

  /**
   * 检查表达式是否含 x 变量(大小写不敏感)
   * 注意: 'x' 作为字面量字母,不能是数字的一部分
   */
  private hasVariable(expr: string): boolean {
    const s: string = expr
    for (let i: number = 0; i < s.length; i++) {
      const c = s.charAt(i)
      if (c === 'x' || c === 'X') {
        // 排除 "exp" 中的 'x'? 实际上 'exp' 是函数,绘图也允许
        // 这里宽松判断:只要含 x 即认为有变量
        return true
      }
    }
    return false
  }
}
