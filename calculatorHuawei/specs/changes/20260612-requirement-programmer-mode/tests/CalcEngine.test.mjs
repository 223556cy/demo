// CalcEngine 位运算测试 — node:test 格式
// 对应 delta-design.md §11.2 位运算用例
// Iron rule 7: 真实跑测试，不准伪造输出

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { CalcEngine } from './CalcEngine.port.mjs'

function engine(programmer = true) {
  const e = new CalcEngine()
  e.setProgrammerMode(programmer)
  return e
}

test('BW-001: 5 & 3 === 1', () => {
  assert.equal(engine().evaluate('5 & 3'), 1)
})

test('BW-002: 5 | 3 === 7', () => {
  assert.equal(engine().evaluate('5 | 3'), 7)
})

test('BW-003: 5 ^ 3 === 6 (XOR, programmer mode)', () => {
  assert.equal(engine().evaluate('5 ^ 3'), 6)
})

test('BW-004: ~0 === 0xFFFFFFFF (32-bit unsigned)', () => {
  assert.equal(engine().evaluate('~0'), 0xFFFFFFFF)
})

test('BW-005: 1 << 4 === 16', () => {
  assert.equal(engine().evaluate('1 << 4'), 16)
})

test('BW-006: 16 >> 2 === 4', () => {
  assert.equal(engine().evaluate('16 >> 2'), 4)
})

test('BW-007: 0xFF & 0x0F === 15', () => {
  assert.equal(engine().evaluate('255 & 15'), 15)
})

test('BW-008: (5 | 3) & 7 === 7', () => {
  assert.equal(engine().evaluate('(5 | 3) & 7'), 7)
})

test('BW-009: 1 << 10 === 1024 (避免 JS << 32 位截断)', () => {
  assert.equal(engine().evaluate('1 << 10'), 1024)
})

test('BW-010: 1 << 31 === 2147483648 (超出 32 位带符号)', () => {
  // 1 << 31 在 JS 实际是 -2147483648（因为 JS 的 << 是 32 位有符号）
  // 但我们的实现用 Math.pow 避免这个截断，结果应为 2147483648
  assert.equal(engine().evaluate('1 << 31'), 2147483648)
})

test('BW-011: 基础模式下 ^ 仍是幂运算 (5 ^ 3 === 125)', () => {
  assert.equal(engine(false).evaluate('5 ^ 3'), 125)
})

test('BW-012: 程序员模式下 ^ 是 XOR (5 ^ 3 === 6)', () => {
  assert.equal(engine(true).evaluate('5 ^ 3'), 6)
})

test('BW-013: 现有乘法不受影响 (4 * 5 === 20)', () => {
  assert.equal(engine().evaluate('4 * 5'), 20)
})

test('BW-014: 现有除法不受影响 (20 / 4 === 5)', () => {
  assert.equal(engine().evaluate('20 / 4'), 5)
})

test('BW-015: 现有取模不受影响 (10 # 3 === 1)', () => {
  assert.equal(engine().evaluate('10 # 3'), 1)
})

test('BW-016: 混合位运算 5 & 3 | 4 === 5（因为 1|4=5）', () => {
  assert.equal(engine().evaluate('5 & 3 | 4'), 5)
})

test('BW-017: 优先级 - 5 & 3 + 4 === 5 （+ 高于 &）', () => {
  // 5 & (3+4) = 5 & 7 = 5
  assert.equal(engine().evaluate('5 & 3 + 4'), 5)
})

test('BW-018: ~5 & 0xFF === 250 (32 位 ~5 = 0xFFFFFFFA, & 0xFF = 0xFA = 250)', () => {
  assert.equal(engine().evaluate('~5 & 255'), 250)
})
