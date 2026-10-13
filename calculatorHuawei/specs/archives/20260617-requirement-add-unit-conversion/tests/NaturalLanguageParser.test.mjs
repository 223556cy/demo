// specs/changes/20260617-requirement-add-unit-conversion/tests/NaturalLanguageParser.test.mjs
// aid-workflow 20260617: Issue #18 NaturalLanguageParser 单元测试(Node 端口)
// 使用 node:test 运行: `node --test NaturalLanguageParser.test.mjs`

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { NaturalLanguageParser } from './NaturalLanguageParser.port.mjs'

// ============== 正向用例 ==============
test('NL-POS-01: 100厘米转英寸 (中文紧凑)', () => {
  const r = NaturalLanguageParser.parse('100厘米转英寸')
  assert.ok(r != null)
  assert.equal(r.isUnitConversion, true)
  assert.equal(r.value, 100)
  assert.equal(r.fromUnit, '厘米')
  assert.equal(r.toUnit, '英寸')
})

test('NL-POS-02: 30摄氏度转华氏度 (中文温度)', () => {
  const r = NaturalLanguageParser.parse('30摄氏度转华氏度')
  assert.ok(r != null)
  assert.equal(r.value, 30)
  assert.equal(r.fromUnit, '摄氏度')
  assert.equal(r.toUnit, '华氏度')
})

test('NL-POS-03: 5ft in cm (英文 in)', () => {
  const r = NaturalLanguageParser.parse('5ft in cm')
  assert.ok(r != null)
  assert.equal(r.value, 5)
  assert.equal(r.fromUnit, 'ft')
  assert.equal(r.toUnit, 'cm')
})

test('NL-POS-04: 5 m to ft (英文 to 带空格)', () => {
  const r = NaturalLanguageParser.parse('5 m to ft')
  assert.ok(r != null)
  assert.equal(r.value, 5)
  assert.equal(r.fromUnit, 'm')
  assert.equal(r.toUnit, 'ft')
})

test('NL-POS-05: 5千克为克 (中文为)', () => {
  const r = NaturalLanguageParser.parse('5千克为克')
  assert.ok(r != null)
  assert.equal(r.value, 5)
  assert.equal(r.fromUnit, '千克')
  assert.equal(r.toUnit, '克')
})

test('NL-POS-06: 1.5米转英尺 (小数)', () => {
  const r = NaturalLanguageParser.parse('1.5米转英尺')
  assert.ok(r != null)
  assert.ok(Math.abs(r.value - 1.5) < 1e-9)
  assert.equal(r.fromUnit, '米')
  assert.equal(r.toUnit, '英尺')
})

// ============== 负向用例 ==============
test('NL-NEG-01: 1+2 不是 NL → null', () => {
  assert.equal(NaturalLanguageParser.parse('1+2'), null)
})
test('NL-NEG-02: sin(0) 不是 NL → null', () => {
  assert.equal(NaturalLanguageParser.parse('sin(0)'), null)
})
test('NL-NEG-03: 空字符串 → null', () => {
  assert.equal(NaturalLanguageParser.parse(''), null)
})
test('NL-NEG-04: 纯数字 100 → null', () => {
  assert.equal(NaturalLanguageParser.parse('100'), null)
})
