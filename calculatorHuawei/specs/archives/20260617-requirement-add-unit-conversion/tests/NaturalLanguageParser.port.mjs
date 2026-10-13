// specs/changes/20260617-requirement-add-unit-conversion/tests/NaturalLanguageParser.port.mjs
// aid-workflow 20260617: Issue #18 NL 解析器 — Node 端口
// 1:1 端口:与 ArkTS NaturalLanguageParser.ets 一一对应
// 支持模式: X+单位+to/in/转/为/→+单位 或 X+单位+keyword+单位+keyword+单位

const KEYWORDS = ['转', 'to', 'in', '为', '→']

const KNOWN_UNITS = [
  '米', '厘米', '毫米', '分米', '千米', '英寸', '英尺', '码', '英里',
  '克', '千克', '毫克', '吨', '磅', '盎司',
  '秒', '分钟', '小时', '天',
  '摄氏度', '华氏度', '开尔文',
  'm', 'cm', 'mm', 'dm', 'km', 'in', 'ft', 'yd', 'mi',
  'g', 'kg', 'mg', 't', 'lb', 'oz',
  's', 'h', 'd', 'min',
  'C', 'F', 'K', '°C', '°F'
]

function findFirstKeyword(input) {
  for (const k of KEYWORDS) {
    const pos = input.indexOf(k)
    if (pos !== -1) return [k, pos]
  }
  return null
}

function findUnitSplit(tail) {
  const parts = tail.split(/\s+/)
  if (parts.length === 2 && parts[0].length > 0 && parts[1].length > 0) {
    return [parts[0], parts[1]]
  }
  for (let i = tail.length; i >= 1; i--) {
    const left = tail.substring(0, i)
    if (KNOWN_UNITS.indexOf(left) !== -1) {
      if (i < tail.length) return [left, tail.substring(i)]
    }
  }
  return null
}

class NaturalLanguageParser {
  static parse(input) {
    if (input == null) return null
    const trimmed = String(input).trim()
    if (trimmed.length === 0) return null

    const firstMatch = findFirstKeyword(trimmed)
    if (firstMatch == null) return null

    const keyword = firstMatch[0]
    const kwPos = firstMatch[1]

    // 1. 提取 head
    const head = trimmed.substring(0, kwPos).trim()
    if (head.length === 0) return null

    // 2. head 必须以数字开头
    const valueNumMatch = head.match(/^-?\d+(\.\d+)?/)
    if (valueNumMatch == null) return null
    const value = parseFloat(valueNumMatch[0])
    if (isNaN(value)) return null

    // 3. head 数字之后的尾部
    const headTrailing = head.substring(valueNumMatch[0].length).trim()

    // 4. head 尾部不能含运算符
    if (/[+\-*/(]/.test(headTrailing)) return null

    // 5. 提取 tail
    const tail = trimmed.substring(kwPos + keyword.length).trim()
    if (tail.length === 0) return null

    // 6. 切分 tail 为 [fromUnit, toUnit]
    const secondMatch = findFirstKeyword(tail)
    let fromUnit = ''
    let toUnit = ''
    if (secondMatch != null) {
      const f = tail.substring(0, secondMatch[1]).trim()
      const t = tail.substring(secondMatch[1] + secondMatch[0].length).trim()
      if (f.length > 0 && t.length > 0) {
        fromUnit = f
        toUnit = t
      }
    }
    if (fromUnit.length === 0) {
      const splitPair = findUnitSplit(tail)
      if (splitPair != null) {
        fromUnit = splitPair[0]
        toUnit = splitPair[1]
      }
    }
    if (fromUnit.length === 0) {
      // tail 单一单位场景: 从 head 尾部借 fromUnit
      if (headTrailing.length === 0) return null
      fromUnit = headTrailing
      toUnit = tail
    }

    if (fromUnit.length === 0 || toUnit.length === 0) return null

    return {
      isUnitConversion: true,
      value: value,
      fromUnit: fromUnit,
      toUnit: toUnit
    }
  }
}

export { NaturalLanguageParser, KEYWORDS, KNOWN_UNITS, findFirstKeyword, findUnitSplit }
