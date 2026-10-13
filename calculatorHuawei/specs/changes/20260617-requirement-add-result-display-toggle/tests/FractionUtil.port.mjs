// aid-workflow 20260617: FractionUtil 端口实现 (Node.js 1:1)
// Issue #27: 计算结果支持小数和分数两种显示, 自由切换
// 对应实现: opencalc/entry/src/main/ets/common/FractionUtil.ets
// 对应设计: specs/changes/20260617-requirement-add-result-display-toggle/delta-design.md §3.5
//
// GREEN 阶段: 完整实现 (TDD - 已在测试中 RED 后填充)

const EPSILON = 1e-9
const DEFAULT_MAX_DENOMINATOR = 9999

/**
 * 欧几里得算法求最大公约数 (最大公因数)
 * @param {number} a 整数
 * @param {number} b 整数
 * @returns {number} gcd(|a|, |b|)
 */
function gcd(a, b) {
  let x = Math.abs(Math.trunc(a))
  let y = Math.abs(Math.trunc(b))
  while (y !== 0) {
    const t = y
    y = x % y
    x = t
  }
  return x
}

/**
 * 将有限精度浮点数转换为最简分数
 * @param {number} value 浮点数
 * @param {number} [maxDenominator=9999] 允许的最大分母
 * @returns {{numerator:number, denominator:number} | null}
 *   化简后的分数; 不满足精度/异常时返回 null
 */
function toFraction(value, maxDenominator = DEFAULT_MAX_DENOMINATOR) {
  // NaN / Infinity 短路
  if (Number.isNaN(value) || !Number.isFinite(value)) return null

  // 零
  if (Math.abs(value) < EPSILON) return { numerator: 0, denominator: 1 }

  const sign = value < 0 ? -1 : 1
  const abs = Math.abs(value)
  const str = abs.toString()

  let numer, denom
  if (str.indexOf('.') !== -1 || str.indexOf('e') !== -1 || str.indexOf('E') !== -1) {
    // 含小数或科学计数 → 通过 Number 精度再处理
    // 直接用 1e15 精度截断避免科学计数
    const scaled = Math.round(abs * 1e15)
    const g = gcd(scaled, 1e15)
    numer = scaled / g
    denom = 1e15 / g
  } else {
    // 整数
    numer = Math.trunc(abs)
    denom = 1
  }

  // 化简
  const g2 = gcd(numer, denom)
  numer = numer / g2
  denom = denom / g2

  if (denom > maxDenominator) return null

  return { numerator: sign * numer, denominator: denom }
}

/**
 * 分数转字符串
 * 整数: "5"; 真分数: "1/2"; 负数: "-1/2"; 零: "0"
 * @param {number} numerator 分子
 * @param {number} denominator 分母
 * @returns {string}
 */
function format(numerator, denominator) {
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

export { gcd, toFraction, format, EPSILON, DEFAULT_MAX_DENOMINATOR }
