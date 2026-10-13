// specs/changes/20260617-requirement-add-中等模糊/tests/UnitConverter.port.impl.mjs
// aid-workflow 20260617: Issue #25 GREEN — 完整实现 (#18 4 大类 + #25 area/time/speed)

const CATEGORY_LENGTH = 'length'
const CATEGORY_TEMPERATURE = 'temperature'
const CATEGORY_MASS = 'mass'
const CATEGORY_VOLUME = 'volume'
const CATEGORY_AREA = 'area'
const CATEGORY_TIME = 'time'
const CATEGORY_SPEED = 'speed'

// #18:length (基准 m)
const LENGTH_FACTORS = {
  m: 1.0, cm: 0.01, mm: 0.001, km: 1000.0,
  inch: 0.0254, ft: 0.3048, yd: 0.9144, mi: 1609.344
}
// #18:mass (基准 kg)
const MASS_FACTORS = { kg: 1.0, g: 0.001, lb: 0.45359237, oz: 0.028349523125 }
// #18:volume (基准 L)
const VOLUME_FACTORS = { L: 1.0, mL: 0.001, gal: 3.785411784, fl_oz: 0.0295735295625 }
// #25:area (基准 m²)
const AREA_FACTORS = {
  m2: 1.0,
  cm2: 0.0001,
  km2: 1000000.0,
  ft2: 0.09290304,
  in2: 0.00064516,
  yd2: 0.83612736,
  acre: 4046.8564224,
  hectare: 10000.0,
  mu: 2000.0 / 3.0
}
// #25:time (基准 s) — 月=30 天、年=365 天 工程近似
const TIME_FACTORS = {
  ms: 0.001,
  s: 1.0,
  min: 60.0,
  h: 3600.0,
  d: 86400.0,
  wk: 604800.0,
  mo: 2592000.0,
  yr: 31536000.0
}
// #25:speed (基准 m/s) — mach=340.29 海平面 15°C 标况声速
const SPEED_FACTORS = {
  m_s: 1.0,
  kmh: 1000.0 / 3600.0,
  mph: 1609.344 / 3600.0,
  knot: 1852.0 / 3600.0,
  mach: 340.29
}

export class UnitConverter {
  static convert(value, from, to, category) {
    if (from === to) return value
    if (category === CATEGORY_TEMPERATURE) return UnitConverter.convertTemperature(value, from, to)
    const factors = UnitConverter.getFactors(category)
    if (factors === null) return null
    const fromFactor = factors[from]
    const toFactor = factors[to]
    if (fromFactor === undefined || toFactor === undefined) return null
    return value * fromFactor / toFactor
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
    if (category === CATEGORY_AREA) return AREA_FACTORS
    if (category === CATEGORY_TIME) return TIME_FACTORS
    if (category === CATEGORY_SPEED) return SPEED_FACTORS
    return null
  }
}

// GREEN: NaturalLanguageParser — #18 + #25 别名表
const ALIASES = new Map()

// === #18 已存在别名 (完整版) ===
// length
for (const [k, c] of [['米','m'],['公尺','m'],['m','m'],['meter','m'],['meters','m'],
  ['厘米','cm'],['公分','cm'],['cm','cm'],['centimeter','cm'],['centimeters','cm'],
  ['毫米','mm'],['mm','mm'],['millimeter','mm'],['millimeters','mm'],
  ['千米','km'],['公里','km'],['km','km'],['kilometer','km'],['kilometers','km'],
  ['英寸','inch'],['时','inch'],['inch','inch'],['inches','inch'],['in','inch'],
  ['英尺','ft'],['尺','ft'],['foot','ft'],['feet','ft'],['ft','ft'],
  ['码','yd'],['yard','yd'],['yards','yd'],['yd','yd'],
  ['英里','mi'],['哩','mi'],['mile','mi'],['miles','mi'],['mi','mi']]) {
  ALIASES.set(k, { key: c, category: 'length' })
}
// temperature
for (const [k, c] of [['摄氏度','C'],['摄氏','C'],['℃','C'],['C','C'],['Celsius','C'],['celsius','C'],
  ['华氏度','F'],['华氏','F'],['℉','F'],['F','F'],['Fahrenheit','F'],['fahrenheit','F'],
  ['开尔文','K'],['K','K'],['Kelvin','K'],['kelvin','K']]) {
  ALIASES.set(k, { key: c, category: 'temperature' })
}
// mass
for (const [k, c] of [['千克','kg'],['公斤','kg'],['kg','kg'],['kilogram','kg'],['kilograms','kg'],
  ['克','g'],['g','g'],['gram','g'],['grams','g'],
  ['磅','lb'],['lb','lb'],['lbs','lb'],['pound','lb'],['pounds','lb'],
  ['盎司','oz'],['oz','oz'],['ounce','oz'],['ounces','oz']]) {
  ALIASES.set(k, { key: c, category: 'mass' })
}
// volume
for (const [k, c] of [['升','L'],['公升','L'],['L','L'],['l','L'],['liter','L'],['liters','L'],
  ['毫升','mL'],['mL','mL'],['ml','mL'],['milliliter','mL'],['milliliters','mL'],
  ['加仑','gal'],['gal','gal'],['gallon','gal'],['gallons','gal'],
  ['液量盎司','fl_oz'],['fl_oz','fl_oz'],['floz','fl_oz'],['fl oz','fl_oz'],
  ['fluid ounce','fl_oz'],['fluid ounces','fl_oz']]) {
  ALIASES.set(k, { key: c, category: 'volume' })
}

// === #25 新增别名:area (17 个) ===
for (const [k, c] of [['亩','mu'],
  ['平方米','m2'],['平方千米','km2'],['平方厘米','cm2'],
  ['平方英尺','ft2'],['平方英寸','in2'],['平方码','yd2'],
  ['英亩','acre'],['公顷','hectare'],
  ['m2','m2'],['km2','km2'],['cm2','cm2'],['ft2','ft2'],['in2','in2'],['yd2','yd2'],
  ['acre','acre'],['hectare','hectare'],['ha','hectare']]) {
  ALIASES.set(k, { key: c, category: 'area' })
}
// === #25 新增别名:time (17 个) ===
for (const [k, c] of [['秒','s'],['毫秒','ms'],['分钟','min'],['小时','h'],
  ['天','d'],['周','wk'],['月','mo'],['年','yr'],
  ['s','s'],['ms','ms'],['min','min'],['h','h'],
  ['hour','h'],['day','d'],['week','wk'],['month','mo'],['year','yr']]) {
  ALIASES.set(k, { key: c, category: 'time' })
}
// === #25 新增别名:speed (14 个) ===
for (const [k, c] of [['米每秒','m_s'],['千米每小时','kmh'],['公里每小时','kmh'],
  ['英里每小时','mph'],['节','knot'],['马赫','mach'],
  ['m/s','m_s'],['km/h','kmh'],['kph','kmh'],
  ['m_s','m_s'],['kmh','kmh'],
  ['mph','mph'],['knot','knot'],['mach','mach']]) {
  ALIASES.set(k, { key: c, category: 'speed' })
}

export class NaturalLanguageParser {
  static parse(input) {
    const trimmed = input.trim()
    if (trimmed.length === 0) return null
    const numMatch = trimmed.match(/^(\d+(?:\.\d+)?)\s*(.+)$/)
    if (numMatch === null) return null
    const value = parseFloat(numMatch[1])
    const rest = numMatch[2]
    const cnOp = rest.match(/^(.+?)\s*(转|到|换成)\s*(.+)$/)
    let fromStr, toStr
    if (cnOp !== null) { fromStr = cnOp[1].trim(); toStr = cnOp[3].trim() }
    else {
      const enOp = rest.match(/^(.+?)\s*(?:to|in|->|=>)\s*(.+)$/i)
      if (enOp === null) return null
      fromStr = enOp[1].trim(); toStr = enOp[2].trim()
    }
    const fromAlias = ALIASES.get(fromStr)
    const toAlias = ALIASES.get(toStr)
    if (fromAlias === undefined || toAlias === undefined) return null
    if (fromAlias.category !== toAlias.category) return null
    return { value, from: fromAlias.key, to: toAlias.key, category: fromAlias.category }
  }
}

// REFACTOR 验证:别名唯一性
export function getAllAliasCount() { return ALIASES.size }
export function getUniqueAliasCount() { return new Set(ALIASES.keys()).size }
