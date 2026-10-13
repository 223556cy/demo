// specs/changes/20260615-requirement-add-unit-conversion/tests/NaturalLanguageParser.port.mjs
// aid-workflow 20260615: 自然语言单位换算查询解析 — Node 端口
// 1:1 端口:与 ArkTS NaturalLanguageParser.ets 一一对应

const ALIASES = {
  // length
  '米': { key: 'm', category: 'length' },
  '公尺': { key: 'm', category: 'length' },
  'm': { key: 'm', category: 'length' },
  'meter': { key: 'm', category: 'length' },
  'meters': { key: 'm', category: 'length' },
  '厘米': { key: 'cm', category: 'length' },
  '公分': { key: 'cm', category: 'length' },
  'cm': { key: 'cm', category: 'length' },
  'centimeter': { key: 'cm', category: 'length' },
  'centimeters': { key: 'cm', category: 'length' },
  '毫米': { key: 'mm', category: 'length' },
  'mm': { key: 'mm', category: 'length' },
  'millimeter': { key: 'mm', category: 'length' },
  'millimeters': { key: 'mm', category: 'length' },
  '千米': { key: 'km', category: 'length' },
  '公里': { key: 'km', category: 'length' },
  'km': { key: 'km', category: 'length' },
  'kilometer': { key: 'km', category: 'length' },
  'kilometers': { key: 'km', category: 'length' },
  '英寸': { key: 'inch', category: 'length' },
  '时': { key: 'inch', category: 'length' },
  'inch': { key: 'inch', category: 'length' },
  'inches': { key: 'inch', category: 'length' },
  'in': { key: 'inch', category: 'length' },
  '英尺': { key: 'ft', category: 'length' },
  '尺': { key: 'ft', category: 'length' },
  'foot': { key: 'ft', category: 'length' },
  'feet': { key: 'ft', category: 'length' },
  'ft': { key: 'ft', category: 'length' },
  '码': { key: 'yd', category: 'length' },
  'yard': { key: 'yd', category: 'length' },
  'yards': { key: 'yd', category: 'length' },
  'yd': { key: 'yd', category: 'length' },
  '英里': { key: 'mi', category: 'length' },
  '哩': { key: 'mi', category: 'length' },
  'mile': { key: 'mi', category: 'length' },
  'miles': { key: 'mi', category: 'length' },
  'mi': { key: 'mi', category: 'length' },

  // temperature
  '摄氏度': { key: 'C', category: 'temperature' },
  '摄氏': { key: 'C', category: 'temperature' },
  '℃': { key: 'C', category: 'temperature' },
  'C': { key: 'C', category: 'temperature' },
  'Celsius': { key: 'C', category: 'temperature' },
  'celsius': { key: 'C', category: 'temperature' },
  '华氏度': { key: 'F', category: 'temperature' },
  '华氏': { key: 'F', category: 'temperature' },
  '℉': { key: 'F', category: 'temperature' },
  'F': { key: 'F', category: 'temperature' },
  'Fahrenheit': { key: 'F', category: 'temperature' },
  'fahrenheit': { key: 'F', category: 'temperature' },
  '开尔文': { key: 'K', category: 'temperature' },
  'K': { key: 'K', category: 'temperature' },
  'Kelvin': { key: 'K', category: 'temperature' },
  'kelvin': { key: 'K', category: 'temperature' },

  // mass
  '千克': { key: 'kg', category: 'mass' },
  '公斤': { key: 'kg', category: 'mass' },
  'kg': { key: 'kg', category: 'mass' },
  'kilogram': { key: 'kg', category: 'mass' },
  'kilograms': { key: 'kg', category: 'mass' },
  '克': { key: 'g', category: 'mass' },
  'g': { key: 'g', category: 'mass' },
  'gram': { key: 'g', category: 'mass' },
  'grams': { key: 'g', category: 'mass' },
  '磅': { key: 'lb', category: 'mass' },
  'lb': { key: 'lb', category: 'mass' },
  'lbs': { key: 'lb', category: 'mass' },
  'pound': { key: 'lb', category: 'mass' },
  'pounds': { key: 'lb', category: 'mass' },
  '盎司': { key: 'oz', category: 'mass' },
  'oz': { key: 'oz', category: 'mass' },
  'ounce': { key: 'oz', category: 'mass' },
  'ounces': { key: 'oz', category: 'mass' },

  // volume
  '升': { key: 'L', category: 'volume' },
  '公升': { key: 'L', category: 'volume' },
  'L': { key: 'L', category: 'volume' },
  'l': { key: 'L', category: 'volume' },
  'liter': { key: 'L', category: 'volume' },
  'liters': { key: 'L', category: 'volume' },
  '毫升': { key: 'mL', category: 'volume' },
  'mL': { key: 'mL', category: 'volume' },
  'ml': { key: 'mL', category: 'volume' },
  'milliliter': { key: 'mL', category: 'volume' },
  'milliliters': { key: 'mL', category: 'volume' },
  '加仑': { key: 'gal', category: 'volume' },
  'gal': { key: 'gal', category: 'volume' },
  'gallon': { key: 'gal', category: 'volume' },
  'gallons': { key: 'gal', category: 'volume' },
  '液量盎司': { key: 'fl_oz', category: 'volume' },
  'fl_oz': { key: 'fl_oz', category: 'volume' },
  'floz': { key: 'fl_oz', category: 'volume' },
  'fl oz': { key: 'fl_oz', category: 'volume' },
  'fluid ounce': { key: 'fl_oz', category: 'volume' },
  'fluid ounces': { key: 'fl_oz', category: 'volume' }
}

class NaturalLanguageParser {
  static parse(input) {
    const trimmed = input.trim()
    if (trimmed.length === 0) return null

    // 1. 提取数字前缀(支持小数);数字与单位之间空格可选(\s*)
    const numMatch = trimmed.match(/^(\d+(?:\.\d+)?)\s*(.+)$/)
    if (numMatch === null) return null
    const value = parseFloat(numMatch[1])
    const rest = numMatch[2]

    // 2. 尝试中文转换词
    const cnOp = rest.match(/^(.+?)\s*(转|到|换成)\s*(.+)$/)
    let fromStr
    let toStr
    if (cnOp !== null) {
      fromStr = cnOp[1].trim()
      toStr = cnOp[3].trim()
    } else {
      // 3. 尝试英文转换词(to / in / -> / =>)
      const enOp = rest.match(/^(.+?)\s*(?:to|in|->|=>)\s*(.+)$/i)
      if (enOp === null) return null
      fromStr = enOp[1].trim()
      toStr = enOp[2].trim()
    }

    // 4. 别名查表
    const fromAlias = ALIASES[fromStr]
    const toAlias = ALIASES[toStr]
    if (fromAlias === undefined || toAlias === undefined) return null

    // 5. 类别必须一致
    if (fromAlias.category !== toAlias.category) return null

    return {
      value: value,
      from: fromAlias.key,
      to: toAlias.key,
      category: fromAlias.category
    }
  }
}

export { NaturalLanguageParser, ALIASES }
