// BaseConverter — JavaScript port for Node.js testing
// 1:1 port of opencalc/entry/src/main/ets/calculator/BaseConverter.ets (fixed version)

export const NumberBase = {
  DEC: 0,
  BIN: 1,
  OCT: 2,
  HEX: 3
}

export class BaseConverter {
  static convert(value, base) {
    if (!Number.isFinite(value) || Number.isNaN(value)) return '-'
    if (value === 0) return '0'

    const negative = value < 0

    if (base === NumberBase.DEC) {
      const absStr = Math.abs(value).toString()
      return negative ? '-' + absStr : absStr
    }

    const intPart = Math.trunc(Math.abs(value))
    const radix = base === NumberBase.BIN ? 2
      : base === NumberBase.OCT ? 8
      : 16
    const converted = intPart.toString(radix).toUpperCase()
    return negative ? '-' + converted : converted
  }

  static withPrefix(value, base) {
    if (!Number.isFinite(value) || Number.isNaN(value)) return '-'
    if (base === NumberBase.DEC) {
      return BaseConverter.convert(value, base)
    }

    const negative = value < 0
    const absVal = Math.abs(value)
    const radix = base === NumberBase.BIN ? 2
      : base === NumberBase.OCT ? 8
      : 16
    const prefix = base === NumberBase.BIN ? '0b'
      : base === NumberBase.OCT ? '0o'
      : '0x'
    const body = Math.trunc(absVal).toString(radix).toUpperCase()
    return negative ? '-' + prefix + body : prefix + body
  }
}