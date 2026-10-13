// BaseConverter Node.js 端口 — 镜像 ArkTS 实现
// 编译时此文件不会被使用；hypium 测试时使用 calculator/BaseConverter.ets
// 这是 TypeScript/ArkTS 代码的算法等价 Node.js 实现
// Iron rule 6: 代码与 ETS 源保持一致

// 进制枚举
export const Base = {
  BIN: 2,
  OCT: 8,
  DEC: 10,
  HEX: 16
}

// 位宽枚举
export const BitWidth = {
  B8: 8,
  B16: 16,
  B32: 32,
  B64: 64
}

// 符号性枚举
export const Signedness = {
  SIGNED: 0,
  UNSIGNED: 1
}

/**
 * 计算位宽对应的 mask
 * 64 位 JavaScript number 精度有限，但 number.MAX_SAFE_INTEGER = 2^53 - 1
 * 64 位用 BigInt 或降级到 2^53
 */
function getMask(bitWidth) {
  if (bitWidth === 64) {
    return Number.MAX_SAFE_INTEGER
  }
  // 使用 Math.pow 避免 JS `<<` 32 位截断
  return Math.pow(2, bitWidth) - 1
}

/**
 * 整数转指定进制字符串
 * @param {number} value
 * @param {number} base 2/8/10/16
 * @param {number} bitWidth 8/16/32/64
 * @param {boolean} signed true=signed, false=unsigned
 * @returns {string} 带 0x/0b/0o 前缀
 */
function toBase(value, base, bitWidth, signed) {
  // 1. 截断为整数并 mask
  const masked = Math.trunc(value) & getMask(bitWidth)

  // 2. signed 模式下，根据高位决定符号
  let isNegative = false
  let unsigned = masked
  if (signed && bitWidth < 64 && (masked & (1 << (bitWidth - 1))) !== 0) {
    isNegative = true
    unsigned = masked  // 直接用补码表示
  }

  // 3. 转字符串并补零
  const raw = unsigned.toString(base).toUpperCase()
  let padded = raw
  if (bitWidth < 64 && base === Base.BIN) {
    padded = raw.padStart(bitWidth, '0')
  }

  // 4. 加前缀（signed 负数仅 DEC 加负号，其他进制显示补码）
  let displayValue
  if (signed && base === Base.DEC) {
    // DEC 模式下，signed 显示真值（含负号）
    let dec = masked
    if (isNegative) dec = masked - (1 << bitWidth)
    displayValue = (dec < 0 ? '-' : '') + Math.abs(dec).toString(10)
  } else {
    displayValue = padded
    if (signed && base === Base.BIN) {
      // BIN signed 已经是补码，无须加负号
    } else if (signed) {
      // OCT/HEX signed 同样是补码表示
    }
  }

  if (base === Base.HEX) return '0x' + displayValue
  if (base === Base.BIN) return '0b' + displayValue
  if (base === Base.OCT) return '0o' + displayValue
  return displayValue
}

/**
 * 进制字符串解析为整数
 * 支持 0x/0b/0o 前缀
 */
function fromBase(text, base) {
  if (typeof text !== 'string') return 0
  const t = text.replace(/^0[xXbBoO]/, '').toUpperCase()
  return parseInt(t, base)
}

/**
 * 4 进制同步格式化（DEC/BIN/OCT/HEX 各一行）
 * @returns {string[]} [DEC, BIN, OCT, HEX]
 */
function format4Bases(value, bitWidth, signed) {
  return [
    toBase(value, Base.DEC, bitWidth, signed),
    toBase(value, Base.BIN, bitWidth, signed),
    toBase(value, Base.OCT, bitWidth, signed),
    toBase(value, Base.HEX, bitWidth, signed)
  ]
}

/**
 * 字符在该进制下是否合法
 */
function isValidCharForBase(ch, base) {
  if (typeof ch !== 'string' || ch.length !== 1) return false
  const upper = ch.toUpperCase()
  if (base === Base.BIN) return upper === '0' || upper === '1'
  if (base === Base.OCT) return upper >= '0' && upper <= '7'
  if (base === Base.DEC) return upper >= '0' && upper <= '9'
  if (base === Base.HEX) {
    return (upper >= '0' && upper <= '9') || (upper >= 'A' && upper <= 'F')
  }
  return false
}

export const BaseConverter = {
  toBase,
  fromBase,
  format4Bases,
  isValidCharForBase
}
