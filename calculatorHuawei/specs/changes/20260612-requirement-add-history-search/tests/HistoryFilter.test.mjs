// HistoryFilter 单元测试 — node:test 格式
// 对应 delta-design.md §11.2 测试用例
// Iron rule 7: 真实跑测试，不准伪造输出

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { filterHistory, HistoryItem } from './HistoryFilter.port.mjs'

const H = (id, expr) => new HistoryItem(id, expr, '0', 0)

test('TC-001: filterHistory([], "")  === []', () => {
  assert.deepEqual(filterHistory([], ''), [])
})

test('TC-002: filterHistory([{expression: "1+2"}], "")  === [{expression: "1+2"}]  // 空查询返回全部', () => {
  const h = [H(1, '1+2')]
  assert.deepEqual(filterHistory(h, ''), h)
})

test('TC-003: filterHistory([{expression: "sin(30)"}], "sin")  === [match]', () => {
  const h = [H(1, 'sin(30)')]
  assert.deepEqual(filterHistory(h, 'sin'), h)
})

test('TC-004: filterHistory([{expression: "sin(30)"}], "SIN")  === [match]  // 大小写不敏感', () => {
  const h = [H(1, 'sin(30)')]
  assert.deepEqual(filterHistory(h, 'SIN'), h)
})

test('TC-005: filterHistory([{expression: "1+2"}], "1+2")  === [match]  // 特殊字符字面量', () => {
  const h = [H(1, '1+2')]
  assert.deepEqual(filterHistory(h, '1+2'), h)
})

test('TC-006: filterHistory([{expression: "1+2"}], "1 + 2")  === []  // 空格不匹配', () => {
  const h = [H(1, '1+2')]
  assert.deepEqual(filterHistory(h, '1 + 2'), [])
})

test('TC-007: filterHistory([{expression: " 1+2 "}], "1+2")  === [match]  // 字段含空格', () => {
  const h = [H(1, ' 1+2 ')]
  assert.deepEqual(filterHistory(h, '1+2'), h)
})

test('TC-008: filterHistory([{expression: "1+2"}], "  1+2  ")  === [match]  // query 前后空格 trim', () => {
  const h = [H(1, '1+2')]
  assert.deepEqual(filterHistory(h, '  1+2  '), h)
})

test('TC-009: filterHistory([{expression: "1+2"}], "xyz")  === []  // 无匹配', () => {
  const h = [H(1, '1+2')]
  assert.deepEqual(filterHistory(h, 'xyz'), [])
})

test('TC-010: filterHistory([{expression: "1+2"}, {expression: "3+4"}], "+")  === 2  // 多匹配', () => {
  const h = [H(1, '1+2'), H(2, '3+4')]
  assert.equal(filterHistory(h, '+').length, 2)
})

test('TC-011: filterHistory([{expression: "🚀"}], "🚀")  === [match]  // 表情', () => {
  const h = [H(1, '🚀')]
  assert.deepEqual(filterHistory(h, '🚀'), h)
})

test('TC-012: filterHistory([{expression: "1+2"}], "")  === [match]  // 边界：单条', () => {
  const h = [H(1, '1+2')]
  assert.deepEqual(filterHistory(h, ''), h)
})
