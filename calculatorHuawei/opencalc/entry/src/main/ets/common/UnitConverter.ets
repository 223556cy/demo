// OpenCalc — 单位换算核心
// aid-workflow 20260615: Issue #14 单位换算功能 (length/temperature/mass/volume)
// aid-workflow 20260617: Issue #25 单位换算扩展 (area/time/speed)
// 当前支持 7 大类,共 32 个基准单位
// 端口:与 specs/changes/20260617-requirement-add-中等模糊/tests/UnitConverter.port.mjs 1:1 对应

const CATEGORY_LENGTH: string = 'length'
const CATEGORY_TEMPERATURE: string = 'temperature'
const CATEGORY_MASS: string = 'mass'
const CATEGORY_VOLUME: string = 'volume'
const CATEGORY_AREA: string = 'area'
const CATEGORY_TIME: string = 'time'
const CATEGORY_SPEED: string = 'speed'

// 长度:以"米"为基准的换算因子(1 单位 = ? 米)
// aid-workflow 20260615: 使用 Map 满足 ArkTS arkts-no-untyped-obj-literals
function buildLengthFactors(): Map<string, number> {
  const m: Map<string, number> = new Map()
  m.set('m', 1.0)
  m.set('cm', 0.01)
  m.set('mm', 0.001)
  m.set('km', 1000.0)
  m.set('inch', 0.0254)
  m.set('ft', 0.3048)
  m.set('yd', 0.9144)
  m.set('mi', 1609.344)
  return m
}

// 质量:以"千克"为基准
function buildMassFactors(): Map<string, number> {
  const m: Map<string, number> = new Map()
  m.set('kg', 1.0)
  m.set('g', 0.001)
  m.set('lb', 0.45359237)
  m.set('oz', 0.028349523125)
  return m
}

// 体积:以"升"为基准
function buildVolumeFactors(): Map<string, number> {
  const m: Map<string, number> = new Map()
  m.set('L', 1.0)
  m.set('mL', 0.001)
  m.set('gal', 3.785411784)
  m.set('fl_oz', 0.0295735295625)
  return m
}

// aid-workflow 20260617: Issue #25 面积(基准 m²)
function buildAreaFactors(): Map<string, number> {
  const m: Map<string, number> = new Map()
  m.set('m2', 1.0)
  m.set('cm2', 0.0001)
  m.set('km2', 1000000.0)
  m.set('ft2', 0.09290304)
  m.set('in2', 0.00064516)
  m.set('yd2', 0.83612736)
  m.set('acre', 4046.8564224)
  m.set('hectare', 10000.0)
  m.set('mu', 2000.0 / 3.0)
  return m
}

// aid-workflow 20260617: Issue #25 时间(基准 s,1 mo=30 d, 1 yr=365 d 工程近似)
function buildTimeFactors(): Map<string, number> {
  const m: Map<string, number> = new Map()
  m.set('ms', 0.001)
  m.set('s', 1.0)
  m.set('min', 60.0)
  m.set('h', 3600.0)
  m.set('d', 86400.0)
  m.set('wk', 604800.0)
  m.set('mo', 2592000.0)
  m.set('yr', 31536000.0)
  return m
}

// aid-workflow 20260617: Issue #25 速度(基准 m/s,1 mach=340.29 海平面 15°C 标况声速)
function buildSpeedFactors(): Map<string, number> {
  const m: Map<string, number> = new Map()
  m.set('m_s', 1.0)
  m.set('kmh', 1000.0 / 3600.0)
  m.set('mph', 1609.344 / 3600.0)
  m.set('knot', 1852.0 / 3600.0)
  m.set('mach', 340.29)
  return m
}

const LENGTH_FACTORS: Map<string, number> = buildLengthFactors()
const MASS_FACTORS: Map<string, number> = buildMassFactors()
const VOLUME_FACTORS: Map<string, number> = buildVolumeFactors()
const AREA_FACTORS: Map<string, number> = buildAreaFactors()
const TIME_FACTORS: Map<string, number> = buildTimeFactors()
const SPEED_FACTORS: Map<string, number> = buildSpeedFactors()

export class UnitConverter {
  /**
   * aid-workflow 20260615+20260617: 单位换算
   * @param value 输入数值
   * @param from 源单位 canonical key(如 "cm" / "C" / "mu" / "h" / "kmh")
   * @param to 目标单位 canonical key
   * @param category 单位类别("length"|"temperature"|"mass"|"volume"|"area"|"time"|"speed")
   * @returns 换算结果;from/to 类别不匹配或单位未注册 → null
   */
  static convert(value: number, from: string, to: string, category: string): number | null {
    if (from === to) return value
    if (category === CATEGORY_TEMPERATURE) return UnitConverter.convertTemperature(value, from, to)
    const factors: Map<string, number> | null = UnitConverter.getFactors(category)
    if (factors === null) return null
    const fromFactor: number | undefined = factors.get(from)
    const toFactor: number | undefined = factors.get(to)
    if (fromFactor === undefined || toFactor === undefined) return null
    const valueInBase: number = value * fromFactor
    return valueInBase / toFactor
  }

  /**
   * aid-workflow 20260615: 温度换算(非线性,通过摄氏度中转)
   * @returns 换算结果;单位未注册 → null
   */
  private static convertTemperature(value: number, from: string, to: string): number | null {
    let celsius: number
    if (from === 'C') celsius = value
    else if (from === 'F') celsius = (value - 32) * 5 / 9
    else if (from === 'K') celsius = value - 273.15
    else return null

    if (to === 'C') return celsius
    if (to === 'F') return celsius * 9 / 5 + 32
    if (to === 'K') return celsius + 273.15
    return null
  }

  /**
   * aid-workflow 20260615+20260617: 获取类别对应的换算因子表
   */
  private static getFactors(category: string): Map<string, number> | null {
    if (category === CATEGORY_LENGTH) return LENGTH_FACTORS
    if (category === CATEGORY_MASS) return MASS_FACTORS
    if (category === CATEGORY_VOLUME) return VOLUME_FACTORS
    // aid-workflow 20260617: Issue #25 新增 3 类
    if (category === CATEGORY_AREA) return AREA_FACTORS
    if (category === CATEGORY_TIME) return TIME_FACTORS
    if (category === CATEGORY_SPEED) return SPEED_FACTORS
    return null
  }
}
