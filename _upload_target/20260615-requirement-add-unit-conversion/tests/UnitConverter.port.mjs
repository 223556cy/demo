// specs/changes/20260615-requirement-add-unit-conversion/tests/UnitConverter.port.mjs
// aid-workflow 20260615: Issue #14 单位换算核心 — Node 端口
// 1:1 端口:与 ArkTS UnitConverter.ets 一一对应(语法限制:无 TypeScript 类型注解)

const CATEGORY_LENGTH = 'length'
const CATEGORY_TEMPERATURE = 'temperature'
const CATEGORY_MASS = 'mass'
const CATEGORY_VOLUME = 'volume'

// 长度:以"米"为基准的换算因子(1 单位 = ? 米)
const LENGTH_FACTORS = {
  m: 1.0, cm: 0.01, mm: 0.001, km: 1000.0,
  inch: 0.0254, ft: 0.3048, yd: 0.9144, mi: 1609.344
}

// 质量:以"千克"为基准
const MASS_FACTORS = {
  kg: 1.0, g: 0.001, lb: 0.45359237, oz: 0.028349523125
}

// 体积:以"升"为基准
const VOLUME_FACTORS = {
  L: 1.0, mL: 0.001, gal: 3.785411784, fl_oz: 0.0295735295625
}

class UnitConverter {
  static convert(value, from, to, category) {
    if (from === to) return value
    if (category === CATEGORY_TEMPERATURE) return UnitConverter.convertTemperature(value, from, to)
    const factors = UnitConverter.getFactors(category)
    if (factors === null) return null
    const fromFactor = factors[from]
    const toFactor = factors[to]
    if (fromFactor === undefined || toFactor === undefined) return null
    const valueInBase = value * fromFactor
    return valueInBase / toFactor
  }

  static convertTemperature(value, from, to) {
    let celsius
    if (from === 'C') celsius = value
    else if (from === 'F') celsius = (value - 32) * 5 / 9
    else if (from === 'K') celsius = value - 273.15
    else return null

    if (to === 'C') return celsius
    if (to === 'F') return celsius * 9 / 5 + 32
    if (to === 'K') return celsius + 273.15
    return null
  }

  static getFactors(category) {
    if (category === CATEGORY_LENGTH) return LENGTH_FACTORS
    if (category === CATEGORY_MASS) return MASS_FACTORS
    if (category === CATEGORY_VOLUME) return VOLUME_FACTORS
    return null
  }
}

export { UnitConverter, CATEGORY_LENGTH, CATEGORY_TEMPERATURE, CATEGORY_MASS, CATEGORY_VOLUME }
