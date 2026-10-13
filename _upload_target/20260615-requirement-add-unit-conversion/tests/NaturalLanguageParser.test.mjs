// specs/changes/20260615-requirement-add-unit-conversion/tests/NaturalLanguageParser.test.mjs
// aid-workflow 20260615: NaturalLanguageParser 单元测试
// TDD:RED 阶段期望 32/32 PASS(因 stub 已含完整实现)

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { NaturalLanguageParser } from './NaturalLanguageParser.port.mjs'

// ============ 中文 NL 命中 ============

test('NL-CN-L01: "100厘米转英寸" → length', () => {
  const r = NaturalLanguageParser.parse('100厘米转英寸')
  assert.deepEqual(r, { value: 100, from: 'cm', to: 'inch', category: 'length' })
})

test('NL-CN-L02: "1英里转千米" → length', () => {
  const r = NaturalLanguageParser.parse('1英里转千米')
  assert.deepEqual(r, { value: 1, from: 'mi', to: 'km', category: 'length' })
})

test('NL-CN-T01: "30摄氏度转华氏度" → temperature', () => {
  const r = NaturalLanguageParser.parse('30摄氏度转华氏度')
  assert.deepEqual(r, { value: 30, from: 'C', to: 'F', category: 'temperature' })
})

test('NL-CN-T02: "0摄氏度转开尔文" → temperature', () => {
  const r = NaturalLanguageParser.parse('0摄氏度转开尔文')
  assert.deepEqual(r, { value: 0, from: 'C', to: 'K', category: 'temperature' })
})

test('NL-CN-M01: "5磅转千克" → mass', () => {
  const r = NaturalLanguageParser.parse('5磅转千克')
  assert.deepEqual(r, { value: 5, from: 'lb', to: 'kg', category: 'mass' })
})

test('NL-CN-M02: "1公斤转克" → mass', () => {
  const r = NaturalLanguageParser.parse('1公斤转克')
  assert.deepEqual(r, { value: 1, from: 'kg', to: 'g', category: 'mass' })
})

test('NL-CN-V01: "1加仑转升" → volume', () => {
  const r = NaturalLanguageParser.parse('1加仑转升')
  assert.deepEqual(r, { value: 1, from: 'gal', to: 'L', category: 'volume' })
})

test('NL-CN-V02: "1000毫升转升" → volume', () => {
  const r = NaturalLanguageParser.parse('1000毫升转升')
  assert.deepEqual(r, { value: 1000, from: 'mL', to: 'L', category: 'volume' })
})

// ============ 英文 NL 命中 ============

test('NL-EN-L01: "100cm to inch" → length', () => {
  const r = NaturalLanguageParser.parse('100cm to inch')
  assert.deepEqual(r, { value: 100, from: 'cm', to: 'inch', category: 'length' })
})

test('NL-EN-L02: "1 mile in km" → length', () => {
  const r = NaturalLanguageParser.parse('1 mile in km')
  assert.deepEqual(r, { value: 1, from: 'mi', to: 'km', category: 'length' })
})

test('NL-EN-T01: "100F to C" → temperature', () => {
  const r = NaturalLanguageParser.parse('100F to C')
  assert.deepEqual(r, { value: 100, from: 'F', to: 'C', category: 'temperature' })
})

test('NL-EN-M01: "1 kg to g" → mass', () => {
  const r = NaturalLanguageParser.parse('1 kg to g')
  assert.deepEqual(r, { value: 1, from: 'kg', to: 'g', category: 'mass' })
})

test('NL-EN-V01: "128 fl oz to gal" → volume', () => {
  const r = NaturalLanguageParser.parse('128 fl oz to gal')
  assert.deepEqual(r, { value: 128, from: 'fl_oz', to: 'gal', category: 'volume' })
})

test('NL-EN-V02: "1L->mL" → volume (箭头)', () => {
  const r = NaturalLanguageParser.parse('1L->mL')
  assert.deepEqual(r, { value: 1, from: 'L', to: 'mL', category: 'volume' })
})

// ============ 别名识别 ============

test('NL-AL-L01: "100公分转英寸" → cm (别名"公分")', () => {
  const r = NaturalLanguageParser.parse('100公分转英寸')
  assert.deepEqual(r, { value: 100, from: 'cm', to: 'inch', category: 'length' })
})

test('NL-AL-L02: "1公里转英里" → km (别名"公里")', () => {
  const r = NaturalLanguageParser.parse('1公里转英里')
  assert.deepEqual(r, { value: 1, from: 'km', to: 'mi', category: 'length' })
})

test('NL-AL-L03: "1公尺转米" → m (别名"公尺")', () => {
  const r = NaturalLanguageParser.parse('1公尺转米')
  assert.deepEqual(r, { value: 1, from: 'm', to: 'm', category: 'length' })
})

test('NL-AL-L04: "1尺转英尺" → ft (别名"尺")', () => {
  const r = NaturalLanguageParser.parse('1尺转英尺')
  assert.deepEqual(r, { value: 1, from: 'ft', to: 'ft', category: 'length' })
})

test('NL-AL-L05: "1哩转英里" → mi (别名"哩")', () => {
  const r = NaturalLanguageParser.parse('1哩转英里')
  assert.deepEqual(r, { value: 1, from: 'mi', to: 'mi', category: 'length' })
})

test('NL-AL-T01: "100华氏转摄氏" → F (别名"华氏")', () => {
  const r = NaturalLanguageParser.parse('100华氏转摄氏')
  assert.deepEqual(r, { value: 100, from: 'F', to: 'C', category: 'temperature' })
})

test('NL-AL-M01: "1公斤转克" → kg (别名"公斤")', () => {
  const r = NaturalLanguageParser.parse('1公斤转克')
  assert.deepEqual(r, { value: 1, from: 'kg', to: 'g', category: 'mass' })
})

test('NL-AL-V01: "1公升转毫升" → L (别名"公升")', () => {
  const r = NaturalLanguageParser.parse('1公升转毫升')
  assert.deepEqual(r, { value: 1, from: 'L', to: 'mL', category: 'volume' })
})

// ============ 数字格式 ============

test('NL-NUM-01: "0.5公里转米" → value=0.5', () => {
  const r = NaturalLanguageParser.parse('0.5公里转米')
  assert.deepEqual(r, { value: 0.5, from: 'km', to: 'm', category: 'length' })
})

test('NL-NUM-02: "100.5厘米转英寸" → value=100.5', () => {
  const r = NaturalLanguageParser.parse('100.5厘米转英寸')
  assert.deepEqual(r, { value: 100.5, from: 'cm', to: 'inch', category: 'length' })
})

test('NL-NUM-03: "0厘米转英寸" → value=0', () => {
  const r = NaturalLanguageParser.parse('0厘米转英寸')
  assert.deepEqual(r, { value: 0, from: 'cm', to: 'inch', category: 'length' })
})

// ============ 错误输入 ============

test('NL-ERR-01: "1米转千克" → null (跨类)', () => {
  assert.equal(NaturalLanguageParser.parse('1米转千克'), null)
})

test('NL-ERR-02: "abc 厘米 转 英寸" → null (无数字)', () => {
  assert.equal(NaturalLanguageParser.parse('abc 厘米 转 英寸'), null)
})

test('NL-ERR-03: "1 未知单位 转 米" → null (别名未找到)', () => {
  assert.equal(NaturalLanguageParser.parse('1 未知单位 转 米'), null)
})

test('NL-ERR-04: "100cm" → null (无转换词)', () => {
  assert.equal(NaturalLanguageParser.parse('100cm'), null)
})

test('NL-ERR-05: "1+2" → null (普通表达式)', () => {
  assert.equal(NaturalLanguageParser.parse('1+2'), null)
})

test('NL-ERR-06: "" → null (空字符串)', () => {
  assert.equal(NaturalLanguageParser.parse(''), null)
})

test('NL-ERR-07: "  " → null (纯空格)', () => {
  assert.equal(NaturalLanguageParser.parse('  '), null)
})
