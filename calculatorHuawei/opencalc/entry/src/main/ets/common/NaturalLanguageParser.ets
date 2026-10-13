// OpenCalc — 自然语言单位换算查询解析
// aid-workflow 20260615: Issue #14 单位换算功能 (4 大类)
// aid-workflow 20260617: Issue #25 单位换算扩展 (新增 area/time/speed)
// 支持中文/英文 NL 模式:"数字+单位A+转/到/换成/to/in/->/=>+单位B"
// 当前覆盖 7 大类 ~140 个中英文别名
// 端口:与 specs/changes/20260617-requirement-add-中等模糊/tests/NaturalLanguageParser.port.mjs 1:1 对应

interface ParseResult {
  value: number
  from: string
  to: string
  category: string
}

interface AliasEntry {
  key: string
  category: string
}

// 别名表:用户输入 → canonical key + category
// 支持 ~70 个中英文别名,覆盖 4 大类 19 个基准单位
// aid-workflow 20260615: 使用 Map 满足 ArkTS arkts-no-untyped-obj-literals
function buildAliases(): Map<string, AliasEntry> {
  const m: Map<string, AliasEntry> = new Map()
  // length (8 基准)
  m.set('米', { key: 'm', category: 'length' })
  m.set('公尺', { key: 'm', category: 'length' })
  m.set('m', { key: 'm', category: 'length' })
  m.set('meter', { key: 'm', category: 'length' })
  m.set('meters', { key: 'm', category: 'length' })
  m.set('厘米', { key: 'cm', category: 'length' })
  m.set('公分', { key: 'cm', category: 'length' })
  m.set('cm', { key: 'cm', category: 'length' })
  m.set('centimeter', { key: 'cm', category: 'length' })
  m.set('centimeters', { key: 'cm', category: 'length' })
  m.set('毫米', { key: 'mm', category: 'length' })
  m.set('mm', { key: 'mm', category: 'length' })
  m.set('millimeter', { key: 'mm', category: 'length' })
  m.set('millimeters', { key: 'mm', category: 'length' })
  m.set('千米', { key: 'km', category: 'length' })
  m.set('公里', { key: 'km', category: 'length' })
  m.set('km', { key: 'km', category: 'length' })
  m.set('kilometer', { key: 'km', category: 'length' })
  m.set('kilometers', { key: 'km', category: 'length' })
  m.set('英寸', { key: 'inch', category: 'length' })
  m.set('时', { key: 'inch', category: 'length' })
  m.set('inch', { key: 'inch', category: 'length' })
  m.set('inches', { key: 'inch', category: 'length' })
  m.set('in', { key: 'inch', category: 'length' })
  m.set('英尺', { key: 'ft', category: 'length' })
  m.set('尺', { key: 'ft', category: 'length' })
  m.set('foot', { key: 'ft', category: 'length' })
  m.set('feet', { key: 'ft', category: 'length' })
  m.set('ft', { key: 'ft', category: 'length' })
  m.set('码', { key: 'yd', category: 'length' })
  m.set('yard', { key: 'yd', category: 'length' })
  m.set('yards', { key: 'yd', category: 'length' })
  m.set('yd', { key: 'yd', category: 'length' })
  m.set('英里', { key: 'mi', category: 'length' })
  m.set('哩', { key: 'mi', category: 'length' })
  m.set('mile', { key: 'mi', category: 'length' })
  m.set('miles', { key: 'mi', category: 'length' })
  m.set('mi', { key: 'mi', category: 'length' })

  // temperature (3 基准)
  m.set('摄氏度', { key: 'C', category: 'temperature' })
  m.set('摄氏', { key: 'C', category: 'temperature' })
  m.set('℃', { key: 'C', category: 'temperature' })
  m.set('C', { key: 'C', category: 'temperature' })
  m.set('Celsius', { key: 'C', category: 'temperature' })
  m.set('celsius', { key: 'C', category: 'temperature' })
  m.set('华氏度', { key: 'F', category: 'temperature' })
  m.set('华氏', { key: 'F', category: 'temperature' })
  m.set('℉', { key: 'F', category: 'temperature' })
  m.set('F', { key: 'F', category: 'temperature' })
  m.set('Fahrenheit', { key: 'F', category: 'temperature' })
  m.set('fahrenheit', { key: 'F', category: 'temperature' })
  m.set('开尔文', { key: 'K', category: 'temperature' })
  m.set('K', { key: 'K', category: 'temperature' })
  m.set('Kelvin', { key: 'K', category: 'temperature' })
  m.set('kelvin', { key: 'K', category: 'temperature' })

  // mass (4 基准)
  m.set('千克', { key: 'kg', category: 'mass' })
  m.set('公斤', { key: 'kg', category: 'mass' })
  m.set('kg', { key: 'kg', category: 'mass' })
  m.set('kilogram', { key: 'kg', category: 'mass' })
  m.set('kilograms', { key: 'kg', category: 'mass' })
  m.set('克', { key: 'g', category: 'mass' })
  m.set('g', { key: 'g', category: 'mass' })
  m.set('gram', { key: 'g', category: 'mass' })
  m.set('grams', { key: 'g', category: 'mass' })
  m.set('磅', { key: 'lb', category: 'mass' })
  m.set('lb', { key: 'lb', category: 'mass' })
  m.set('lbs', { key: 'lb', category: 'mass' })
  m.set('pound', { key: 'lb', category: 'mass' })
  m.set('pounds', { key: 'lb', category: 'mass' })
  m.set('盎司', { key: 'oz', category: 'mass' })
  m.set('oz', { key: 'oz', category: 'mass' })
  m.set('ounce', { key: 'oz', category: 'mass' })
  m.set('ounces', { key: 'oz', category: 'mass' })

  // volume (4 基准)
  m.set('升', { key: 'L', category: 'volume' })
  m.set('公升', { key: 'L', category: 'volume' })
  m.set('L', { key: 'L', category: 'volume' })
  m.set('l', { key: 'L', category: 'volume' })
  m.set('liter', { key: 'L', category: 'volume' })
  m.set('liters', { key: 'L', category: 'volume' })
  m.set('毫升', { key: 'mL', category: 'volume' })
  m.set('mL', { key: 'mL', category: 'volume' })
  m.set('ml', { key: 'mL', category: 'volume' })
  m.set('milliliter', { key: 'mL', category: 'volume' })
  m.set('milliliters', { key: 'mL', category: 'volume' })
  m.set('加仑', { key: 'gal', category: 'volume' })
  m.set('gal', { key: 'gal', category: 'volume' })
  m.set('gallon', { key: 'gal', category: 'volume' })
  m.set('gallons', { key: 'gal', category: 'volume' })
  m.set('液量盎司', { key: 'fl_oz', category: 'volume' })
  m.set('fl_oz', { key: 'fl_oz', category: 'volume' })
  m.set('floz', { key: 'fl_oz', category: 'volume' })
  m.set('fl oz', { key: 'fl_oz', category: 'volume' })
  m.set('fluid ounce', { key: 'fl_oz', category: 'volume' })
  m.set('fluid ounces', { key: 'fl_oz', category: 'volume' })

  // aid-workflow 20260617: Issue #25 area (9 基准)
  m.set('亩', { key: 'mu', category: 'area' })
  m.set('平方米', { key: 'm2', category: 'area' })
  m.set('平方千米', { key: 'km2', category: 'area' })
  m.set('平方厘米', { key: 'cm2', category: 'area' })
  m.set('平方英尺', { key: 'ft2', category: 'area' })
  m.set('平方英寸', { key: 'in2', category: 'area' })
  m.set('平方码', { key: 'yd2', category: 'area' })
  m.set('英亩', { key: 'acre', category: 'area' })
  m.set('公顷', { key: 'hectare', category: 'area' })
  m.set('m2', { key: 'm2', category: 'area' })
  m.set('km2', { key: 'km2', category: 'area' })
  m.set('cm2', { key: 'cm2', category: 'area' })
  m.set('ft2', { key: 'ft2', category: 'area' })
  m.set('in2', { key: 'in2', category: 'area' })
  m.set('yd2', { key: 'yd2', category: 'area' })
  m.set('acre', { key: 'acre', category: 'area' })
  m.set('hectare', { key: 'hectare', category: 'area' })
  m.set('ha', { key: 'hectare', category: 'area' })

  // aid-workflow 20260617: Issue #25 time (8 基准,1 mo=30 d, 1 yr=365 d 工程近似)
  m.set('秒', { key: 's', category: 'time' })
  m.set('毫秒', { key: 'ms', category: 'time' })
  m.set('分钟', { key: 'min', category: 'time' })
  m.set('小时', { key: 'h', category: 'time' })
  m.set('天', { key: 'd', category: 'time' })
  m.set('周', { key: 'wk', category: 'time' })
  m.set('月', { key: 'mo', category: 'time' })
  m.set('年', { key: 'yr', category: 'time' })
  m.set('s', { key: 's', category: 'time' })
  m.set('ms', { key: 'ms', category: 'time' })
  m.set('min', { key: 'min', category: 'time' })
  m.set('h', { key: 'h', category: 'time' })
  m.set('hour', { key: 'h', category: 'time' })
  m.set('day', { key: 'd', category: 'time' })
  m.set('week', { key: 'wk', category: 'time' })
  m.set('month', { key: 'mo', category: 'time' })
  m.set('year', { key: 'yr', category: 'time' })

  // aid-workflow 20260617: Issue #25 speed (5 基准,1 mach=340.29 海平面 15°C 标况声速)
  m.set('米每秒', { key: 'm_s', category: 'speed' })
  m.set('千米每小时', { key: 'kmh', category: 'speed' })
  m.set('公里每小时', { key: 'kmh', category: 'speed' })
  m.set('英里每小时', { key: 'mph', category: 'speed' })
  m.set('节', { key: 'knot', category: 'speed' })
  m.set('马赫', { key: 'mach', category: 'speed' })
  m.set('m/s', { key: 'm_s', category: 'speed' })
  m.set('km/h', { key: 'kmh', category: 'speed' })
  m.set('kph', { key: 'kmh', category: 'speed' })
  m.set('m_s', { key: 'm_s', category: 'speed' })
  m.set('kmh', { key: 'kmh', category: 'speed' })
  m.set('mph', { key: 'mph', category: 'speed' })
  m.set('knot', { key: 'knot', category: 'speed' })
  m.set('mach', { key: 'mach', category: 'speed' })
  return m
}

const ALIASES: Map<string, AliasEntry> = buildAliases()

export { ParseResult }

export class NaturalLanguageParser {
  /**
   * aid-workflow 20260615: 解析自然语言单位换算查询
   * @param input 用户输入字符串
   * @returns ParseResult {value, from, to, category};不匹配 NL 模式 → null
   */
  static parse(input: string): ParseResult | null {
    const trimmed: string = input.trim()
    if (trimmed.length === 0) return null

    // 1. 提取数字前缀(支持小数);数字与单位之间空格可选(\s*)
    const numMatch: RegExpMatchArray | null = trimmed.match(/^(\d+(?:\.\d+)?)\s*(.+)$/)
    if (numMatch === null) return null
    const value: number = parseFloat(numMatch[1])
    const rest: string = numMatch[2]

    // 2. 尝试中文转换词
    const cnOp: RegExpMatchArray | null = rest.match(/^(.+?)\s*(转|到|换成)\s*(.+)$/)
    let fromStr: string
    let toStr: string
    if (cnOp !== null) {
      fromStr = cnOp[1].trim()
      toStr = cnOp[3].trim()
    } else {
      // 3. 尝试英文转换词(to / in / -> / =>)
      const enOp: RegExpMatchArray | null = rest.match(/^(.+?)\s*(?:to|in|->|=>)\s*(.+)$/i)
      if (enOp === null) return null
      fromStr = enOp[1].trim()
      toStr = enOp[2].trim()
    }

    // 4. 别名查表
    const fromAlias: AliasEntry | undefined = ALIASES.get(fromStr)
    const toAlias: AliasEntry | undefined = ALIASES.get(toStr)
    if (fromAlias === undefined || toAlias === undefined) return null

    // 5. 类别必须一致(否则跨类换算)
    if (fromAlias.category !== toAlias.category) return null

    return {
      value: value,
      from: fromAlias.key,
      to: toAlias.key,
      category: fromAlias.category
    }
  }
}
