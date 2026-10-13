// OpenCalc — 分数工具
// aid-workflow 20260617: Issue #27 计算结果支持小数和分数两种显示,自由切换
// 移植自: specs/changes/20260617-requirement-add-result-display-toggle/tests/FractionUtil.port.mjs (1:1 端口)
// 对应设计: delta-design.md §3.5

/**
 * 分数结果
 */
export interface FractionResult {
  numerator: number
  denominator: number
}

const EPSILON: number = 1e-9
const DEFAULT_MAX_DENOMINATOR: number = 9999

/**
 * 分数工具类
 * 纯逻辑, 无 UI/系统依赖
 */
export class FractionUtil {

  /**
   * 欧几里得算法求最大公约数(最大公因数)
   * @param a 整数
   * @param b 整数
   * @returns gcd(|a|, |b|)
   */
  static gcd(a: number, b: number): number {
    let x: number = Math.abs(Math.trunc(a))
    let y: number = Math.abs(Math.trunc(b))
    while (y !== 0) {
      const t: number = y
      y = x % y
      x = t
    }
    return x
  }

  /**
   * 将有限精度浮点数转换为最简分数
   * @param value 浮点数
   * @param maxDenominator 允许的最大分母,默认 9999
   * @returns 化简后的 FractionResult; 不满足精度/异常时返回 null
   */
  static toFraction(value: number, maxDenominator: number = DEFAULT_MAX_DENOMINATOR): FractionResult | null {
    // NaN / Infinity 短路
    if (Number.isNaN(value) || !Number.isFinite(value)) return null

    // 零
    if (Math.abs(value) < EPSILON) return { numerator: 0, denominator: 1 } as FractionResult

    const sign: number = value < 0 ? -1 : 1
    const abs: number = Math.abs(value)
    const str: string = abs.toString()

    let numer: number
    let denom: number
    if (str.indexOf('.') !== -1 || str.indexOf('e') !== -1 || str.indexOf('E') !== -1) {
      // 含小数或科学计数 → 通过 1e15 精度截断避免科学计数
      const scaled: number = Math.round(abs * 1e15)
      const g: number = FractionUtil.gcd(scaled, 1e15)
      numer = scaled / g
      denom = 1e15 / g
    } else {
      // 整数
      numer = Math.trunc(abs)
      denom = 1
    }

    // 化简
    const g2: number = FractionUtil.gcd(numer, denom)
    numer = numer / g2
    denom = denom / g2

    if (denom > maxDenominator) return null

    return { numerator: sign * numer, denominator: denom } as FractionResult
  }

  /**
   * 分数转字符串
   * 整数: "5"; 真分数: "1/2"; 负数: "-1/2"; 零: "0"
   * @param numerator 分子
   * @param denominator 分母
   * @returns 字符串
   */
  static format(numerator: number, denominator: number): string {
    if (denominator === 0) return '0'  // 防御
    if (numerator === 0) return '0'

    // 保证 denominator 为正
    if (denominator < 0) {
      numerator = -numerator
      denominator = -denominator
    }

    // 整数简化
    if (numerator % denominator === 0) {
      return String(numerator / denominator)
    }

    return `${numerator}/${denominator}`
  }
}
