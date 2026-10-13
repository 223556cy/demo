// specs/changes/20260617-requirement-add-unit-conversion/tests/UnitConverter.port.mjs
// aid-workflow 20260617: Issue #18 单位换算核心 — Node 端口
// 1:1 端口:与 ArkTS UnitConverter.ets 一一对应
// 支持长度/质量/时间/温度四个维度,温度用 affine 公式独立处理

// 长度(以"米"为基准的换算因子:1 单位 = ? 米)
const LENGTH_FACTORS = {
  m: 1.0, cm: 0.01, mm: 0.001, km: 1000.0, dm: 0.1,
  in: 0.0254, ft: 0.3048, yd: 0.9144, mi: 1609.344
}

// 质量(以"克"为基准)
const MASS_FACTORS = {
  g: 1.0, mg: 0.001, kg: 1000.0, t: 1e6,
  lb: 453.592, oz: 28.3495
}

// 时间(以"秒"为基准)
const TIME_FACTORS = {
  s: 1.0, min: 60.0, h: 3600.0, day: 86400.0, d: 86400.0
}

// 温度 — affine (以"开尔文"为基准)
function toK(value, from) {
  if (from === 'C') return value + 273.15
  if (from === 'F') return (value - 32) * 5 / 9 + 273.15
  if (from === 'K') return value
  return null
}
function fromK(value, to) {
  if (to === 'C') return value - 273.15
  if (to === 'F') return (value - 273.15) * 9 / 5 + 32
  if (to === 'K') return value
  return null
}

const CATEGORY_LENGTH = 'length'
const CATEGORY_TEMPERATURE = 'temperature'
const CATEGORY_MASS = 'mass'
const CATEGORY_TIME = 'time'

function getFactors(category) {
  if (category === CATEGORY_LENGTH) return LENGTH_FACTORS
  if (category === CATEGORY_MASS) return MASS_FACTORS
  if (category === CATEGORY_TIME) return TIME_FACTORS
  return null
}

// 中英文别名映射
const ALIAS_MAP = {
  // length
  '米': 'm', '毫米': 'mm', '厘米': 'cm', '分米': 'dm', '千米': 'km',
  '英寸': 'in', '英尺': 'ft', '码': 'yd', '英里': 'mi',
  // mass
  '克': 'g', '毫克': 'mg', '千克': 'kg', '吨': 't', '磅': 'lb', '盎司': 'oz',
  // time
  '秒': 's', '分钟': 'min', '小时': 'h', '天': 'day',
  // temperature
  '摄氏度': 'C', '华氏度': 'F', '开尔文': 'K',
  '°C': 'C', '°F': 'F'
}

function normalize(name) {
  if (name == null) return null
  const trimmed = String(name).trim()
  if (trimmed in ALIAS_MAP) return ALIAS_MAP[trimmed]
  return trimmed
}

function detectCategory(unit) {
  for (const k of Object.keys(LENGTH_FACTORS)) if (k === unit) return CATEGORY_LENGTH
  for (const k of Object.keys(MASS_FACTORS)) if (k === unit) return CATEGORY_MASS
  for (const k of Object.keys(TIME_FACTORS)) if (k === unit) return CATEGORY_TIME
  if (unit === 'C' || unit === 'F' || unit === 'K') return CATEGORY_TEMPERATURE
  return null
}

class UnitConverter {
  static convert(value, from, to) {
    const fromNorm = normalize(from)
    const toNorm = normalize(to)
    if (fromNorm == null || toNorm == null) return NaN
    const fromCat = detectCategory(fromNorm)
    const toCat = detectCategory(toNorm)
    if (fromCat == null || toCat == null) return NaN
    if (fromCat !== toCat) return NaN
    if (fromCat === CATEGORY_TEMPERATURE) {
      const k = toK(value, fromNorm)
      if (k == null) return NaN
      const r = fromK(k, toNorm)
      if (r == null) return NaN
      return r
    }
    const factors = getFactors(fromCat)
    if (factors == null) return NaN
    const fromFactor = factors[fromNorm]
    const toFactor = factors[toNorm]
    if (fromFactor === undefined || toFactor === undefined) return NaN
    return value * fromFactor / toFactor
  }
}

export { UnitConverter, CATEGORY_LENGTH, CATEGORY_TEMPERATURE, CATEGORY_MASS, CATEGORY_TIME, normalize, detectCategory }
