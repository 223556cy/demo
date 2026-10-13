// OpenCalc — 函数图像绘制工具类（纯函数）
// aid-workflow 20260617: Issue #26 函数图像
// 设计参考: specs/changes/20260617-requirement-add-plot-graph/delta-design.md §3.7

/**
 * 采样点
 * y === null 表示定义域外/求值失败
 */
export interface PlotPoint {
  x: number
  y: number | null
}

/**
 * 一条函数曲线
 */
export interface PlotSeries {
  points: PlotPoint[]
  xMin: number
  xMax: number
  yMin: number
  yMax: number
}

/**
 * 画布尺寸 + 内边距
 */
export interface PlotBounds {
  width: number
  height: number
  paddingLeft: number
  paddingRight: number
  paddingTop: number
  paddingBottom: number
}

/**
 * 表达式求值回调 (单点)
 * 返回 null 表示该点无法求值
 */
export type Evaluator = (expr: string, x: number) => number | null

/**
 * 画布像素坐标
 */
export interface CanvasPoint {
  px: number
  py: number
}

/**
 * Y 轴范围
 */
export interface YRange {
  yMin: number
  yMax: number
}

/**
 * Y 轴范围限幅(防 Canvas 溢出)
 */
const Y_RANGE_CLAMP: number = 1e10

export class PlotUtils {
  /**
   * 在 x ∈ [xMin, xMax] 区间均匀采样 samples 个点
   * @param samples 必须 ≥ 2,否则自动提升为 2
   */
  static sampleSeries(
    expression: string,
    xMin: number,
    xMax: number,
    samples: number,
    evaluator: Evaluator
  ): PlotSeries {
    if (samples < 2) {
      samples = 2
    }
    const points: PlotPoint[] = new Array(samples)
    const step: number = (xMax - xMin) / (samples - 1)
    for (let i: number = 0; i < samples; i++) {
      const x: number = xMin + i * step
      let y: number | null = evaluator(expression, x)
      // 采样到极端值时强制 null (奇点 / 求值爆炸),绘图层断线
      // 任何有奇点的函数 (tan/cot/sec/csc 等) 都不会污染 Y 轴和视觉曲线
      // 不做位置式渐近线检测 (如 |x - (π/2 + kπ)| < step * 0.5):
      //   那样会误杀大步长下 sin/cos/线性等函数(AC-2.4 验证过)
      if (y !== null) {
        if (!isFinite(y) || Math.abs(y) > 1e6) {
          y = null
        }
      }
      points[i] = { x, y }
    }
    const range: YRange = PlotUtils.computeYRange(points)
    return { points, xMin, xMax, yMin: range.yMin, yMax: range.yMax }
  }

  /**
   * 数学坐标 → 画布像素坐标
   * Y 轴翻转(画布 y 向下,数学 y 向上)
   * @returns 像素坐标;y===null 或除零时返回 null
   */
  static mapToCanvas(
    p: PlotPoint,
    bounds: PlotBounds,
    xMin: number,
    xMax: number,
    yMin: number,
    yMax: number
  ): CanvasPoint | null {
    if (p.y === null) {
      return null
    }
    if (xMax === xMin || yMax === yMin) {
      return null
    }
    const innerW: number = bounds.width - bounds.paddingLeft - bounds.paddingRight
    const innerH: number = bounds.height - bounds.paddingTop - bounds.paddingBottom
    if (innerW <= 0 || innerH <= 0) {
      return null
    }
    const px: number = bounds.paddingLeft + ((p.x - xMin) / (xMax - xMin)) * innerW
    const py: number = bounds.paddingTop + (1 - (p.y - yMin) / (yMax - yMin)) * innerH
    return { px, py }
  }

  /**
   * 从采样点计算 Y 轴显示范围
   * - 忽略 null 与非有限值(NaN/Inf)
   * - 加 10% 边距
   * - 限幅 [-1e10, 1e10]
   * - 全失败兜底 [-1, 1]
   * - 单值退化为 [-1, 1] 对称区间
   */
  static computeYRange(points: PlotPoint[]): YRange {
    // 收集所有有效 y 值
    const ys: number[] = []
    for (let i: number = 0; i < points.length; i++) {
      const y: number | null = points[i].y
      if (y === null) continue
      if (!isFinite(y)) continue
      // 丢掉远离主体的极端值 (奇点 / 求值爆炸)
      // 任何有奇点的函数 (tan/cot/sec/csc/log(x-1) 等) 都不会再污染 Y 轴
      if (Math.abs(y) > 1e6) continue
      ys.push(y)
    }
    if (ys.length === 0) {
      const r: YRange = { yMin: -1, yMax: 1 }
      return r
    }
    // 排序后取 2% / 98% 百分位,稳健避开离群点
    ys.sort((a: number, b: number): number => a - b)
    const loIdx: number = Math.floor(ys.length * 0.02)
    const hiIdx: number = Math.floor(ys.length * 0.98)
    let lo: number = ys[loIdx]
    let hi: number = ys[hiIdx]
    // 兜底:单点 / 全相等时给一个对称区间
    if (lo === hi) {
      lo = lo - 1
      hi = hi + 1
    }
    const pad: number = (hi - lo) * 0.1
    let yMin: number = lo - pad
    let yMax: number = hi + pad
    if (yMin < -Y_RANGE_CLAMP) yMin = -Y_RANGE_CLAMP
    if (yMax > Y_RANGE_CLAMP) yMax = Y_RANGE_CLAMP
    const result: YRange = { yMin, yMax }
    return result
  }

  /**
   * 解析 xMin/xMax 输入字符串
   * 支持:数字 / pi / e / 四则运算符 / 括号 / 空白
   * 不支持函数 (sin cos 等)
   * @returns number; 解析失败返回 null
   */
  static parseRange(input: string): number | null {
    if (input === null || input === undefined) return null
    const s: string = input.trim()
    if (s.length === 0) return null
    const parser = new RangeParser(s)
    try {
      const v = parser.parse()
      if (parser.hasUnparsed()) return null
      if (typeof v !== 'number' || !isFinite(v)) return null
      return v
    } catch {
      return null
    }
  }
}

// ==================== 内部:RangeParser ====================
//
// 极简递归下降解析器,仅支持 Range 输入所需语法
// 不使用 eval/new Function,ArkTS 安全

class RangeParser {
  private s: string
  private p: number = 0
  private end: number = 0

  constructor(s: string) {
    this.s = s
    this.end = s.length
  }

  hasUnparsed(): boolean {
    return this.p < this.end
  }

  parse(): number {
    this.skipWs()
    const v: number = this.parseExpr()
    this.skipWs()
    return v
  }

  private skipWs(): void {
    while (this.p < this.end && (this.s[this.p] === ' ' || this.s[this.p] === '\t')) {
      this.p++
    }
  }

  private parseExpr(): number {
    let v = this.parseTerm()
    while (true) {
      this.skipWs()
      if (this.p >= this.end) break
      const c = this.s[this.p]
      if (c === '+' || c === '-') {
        this.p++
        const r = this.parseTerm()
        v = c === '+' ? v + r : v - r
      } else {
        break
      }
    }
    return v
  }

  private parseTerm(): number {
    let v = this.parseFactor()
    while (true) {
      this.skipWs()
      if (this.p >= this.end) break
      const c = this.s[this.p]
      if (c === '*' || c === '/') {
        this.p++
        const r = this.parseFactor()
        if (c === '/' && r === 0) {
          throw new Error('division by zero')
        }
        v = c === '*' ? v * r : v / r
      } else {
        break
      }
    }
    return v
  }

  private parseFactor(): number {
    this.skipWs()
    if (this.p >= this.end) {
      throw new Error('unexpected end')
    }
    const c = this.s[this.p]
    if (c === '(') {
      this.p++
      const v = this.parseExpr()
      this.skipWs()
      if (this.p >= this.end || this.s[this.p] !== ')') {
        throw new Error('missing )')
      }
      this.p++
      return v
    }
    if (c === '+') {
      this.p++
      return this.parseFactor()
    }
    if (c === '-') {
      this.p++
      return -this.parseFactor()
    }
    // pi 关键字
    if (c === 'p' && this.p + 1 < this.end && this.s[this.p + 1] === 'i') {
      this.p += 2
      return Math.PI
    }
    // e 关键字(后不能接字母/数字/下划线)
    if (c === 'e' && (this.p + 1 >= this.end || !this.isIdentChar(this.s[this.p + 1]))) {
      this.p++
      return Math.E
    }
    // 数字
    if (c >= '0' && c <= '9' || c === '.') {
      const start = this.p
      let dotSeen = c === '.'
      this.p++
      while (this.p < this.end) {
        const cc = this.s[this.p]
        if (cc >= '0' && cc <= '9') {
          this.p++
        } else if (cc === '.' && !dotSeen) {
          dotSeen = true
          this.p++
        } else {
          break
        }
      }
      const num = parseFloat(this.s.substring(start, this.p))
      if (!isFinite(num)) {
        throw new Error('bad number')
      }
      return num
    }
    throw new Error('unexpected char: ' + c)
  }

  private isIdentChar(c: string): boolean {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c === '_'
  }
}
