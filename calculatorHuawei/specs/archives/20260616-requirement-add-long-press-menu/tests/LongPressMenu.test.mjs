// aid-workflow 20260616: LongPressMenu 单元测试 (Node.js 端口风格)
// 验证: design.md §3.5.6 + delta-spec.md §7 AC 矩阵

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { hasCandidates, getCandidates } from './LongPressMenu.port.mjs'

// ==================== AC-1: 长按 sin/cos/tan 弹出候选菜单 ====================
test('AC-1 hasCandidates sin → true', () => {
  assert.equal(hasCandidates('sin'), true)
})

test('AC-1 hasCandidates cos → true', () => {
  assert.equal(hasCandidates('cos'), true)
})

test('AC-1 hasCandidates tan → true', () => {
  assert.equal(hasCandidates('tan'), true)
})

// ==================== AC-5: 数字/运算符/常量无长按候选 ====================
test('AC-5 hasCandidates 数字 → false', () => {
  assert.equal(hasCandidates('1'), false)
  assert.equal(hasCandidates('0'), false)
  assert.equal(hasCandidates('9'), false)
})

test('AC-5 hasCandidates 运算符 → false', () => {
  assert.equal(hasCandidates('+'), false)
  assert.equal(hasCandidates('-'), false)
  assert.equal(hasCandidates('×'), false)
  assert.equal(hasCandidates('÷'), false)
})

test('AC-5 hasCandidates 常量 → false', () => {
  assert.equal(hasCandidates('π'), false)
  assert.equal(hasCandidates('e'), false)
})

// ==================== AC-5: arcsi/arcco/arcta 已是反函数无下层 ====================
test('AC-5 hasCandidates arcsi → false', () => {
  assert.equal(hasCandidates('arcsi'), false)
})

test('AC-5 hasCandidates arcco → false', () => {
  assert.equal(hasCandidates('arcco'), false)
})

test('AC-5 hasCandidates arcta → false', () => {
  assert.equal(hasCandidates('arcta'), false)
})

// ==================== AC-5: ln/log 首版不映射 (FMEA C4) ====================
test('AC-5 hasCandidates ln → false (首版不映射)', () => {
  assert.equal(hasCandidates('ln'), false)
})

test('AC-5 hasCandidates log → false (首版不映射)', () => {
  assert.equal(hasCandidates('log'), false)
})

// ==================== AC-1: getCandidates 返回 3 项 ====================
test('AC-1 getCandidates sin → [arcsin, arccos, arctan]', () => {
  assert.deepEqual(getCandidates('sin'), ['arcsin', 'arccos', 'arctan'])
})

test('AC-1 getCandidates cos → [arcsin, arccos, arctan]', () => {
  assert.deepEqual(getCandidates('cos'), ['arcsin', 'arccos', 'arctan'])
})

test('AC-1 getCandidates tan → [arcsin, arccos, arctan]', () => {
  assert.deepEqual(getCandidates('tan'), ['arcsin', 'arccos', 'arctan'])
})

// ==================== 边界: 未知 label → [] ====================
test('getCandidates 未知 label → []', () => {
  assert.deepEqual(getCandidates('xxx'), [])
})

test('getCandidates 空字符串 → []', () => {
  assert.deepEqual(getCandidates(''), [])
})