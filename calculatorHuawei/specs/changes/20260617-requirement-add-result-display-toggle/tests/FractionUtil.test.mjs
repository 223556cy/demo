// aid-workflow 20260617: FractionUtil 单元测试 (Node.js 端口风格)
// Issue #27: 计算结果支持小数和分数两种显示, 自由切换
// 验证: delta-spec.md §3.2 + delta-design.md §3.5
// 真实跑测入口: node --test --test-reporter=tap FractionUtil.test.mjs

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { gcd, toFraction, format } from './FractionUtil.port.mjs'

// ==================== AC-1: 0.5 → 1/2 ====================
test('AC-1 toFraction(0.5) = {1, 2}', () => {
  const r = toFraction(0.5)
  assert.equal(r.numerator, 1)
  assert.equal(r.denominator, 2)
})

// ==================== AC-2: 0.25 → 1/4 ====================
test('AC-2 toFraction(0.25) = {1, 4}', () => {
  const r = toFraction(0.25)
  assert.equal(r.numerator, 1)
  assert.equal(r.denominator, 4)
})

// ==================== AC-3: 0.75 → 3/4 ====================
test('AC-3 toFraction(0.75) = {3, 4}', () => {
  const r = toFraction(0.75)
  assert.equal(r.numerator, 3)
  assert.equal(r.denominator, 4)
})

// ==================== AC-4: 1/3 (无理) → 回退 null ====================
test('AC-4 toFraction(1/3) = null (回退小数)', () => {
  const r = toFraction(1 / 3)
  assert.equal(r, null)
})

// ==================== AC-5: 负数 -0.5 → -1/2 ====================
test('AC-5 toFraction(-0.5) = {-1, 2}', () => {
  const r = toFraction(-0.5)
  assert.equal(r.numerator, -1)
  assert.equal(r.denominator, 2)
})

// ==================== AC-6: 整数 2 → {2, 1} ====================
test('AC-6 toFraction(2) = {2, 1}', () => {
  const r = toFraction(2)
  assert.equal(r.numerator, 2)
  assert.equal(r.denominator, 1)
})

// ==================== AC-7: 零 → {0, 1} ====================
test('AC-7 toFraction(0) = {0, 1}', () => {
  const r = toFraction(0)
  assert.equal(r.numerator, 0)
  assert.equal(r.denominator, 1)
})

// ==================== AC-8: NaN → null ====================
test('AC-8 toFraction(NaN) = null', () => {
  assert.equal(toFraction(NaN), null)
})

// ==================== AC-9: Infinity → null ====================
test('AC-9 toFraction(Infinity) = null', () => {
  assert.equal(toFraction(Infinity), null)
})

// ==================== AC-10: 0.3333 (3位小数) → {3333, 10000} → 化简后 {3333, 10000} 分母超 9999 → null ====================
test('AC-10 toFraction(0.3333) = null (分母 10000 > 9999)', () => {
  assert.equal(toFraction(0.3333), null)
})

// ==================== AC-11: 0.125 → 1/8 (分母 1000 < 9999) ====================
test('AC-11 toFraction(0.125) = {1, 8}', () => {
  const r = toFraction(0.125)
  assert.equal(r.numerator, 1)
  assert.equal(r.denominator, 8)
})

// ==================== AC-12: 0.0625 → 1/16 ====================
test('AC-12 toFraction(0.0625) = {1, 16}', () => {
  const r = toFraction(0.0625)
  assert.equal(r.numerator, 1)
  assert.equal(r.denominator, 16)
})

// ==================== AC-13: gcd 基本 ====================
test('AC-13 gcd(12, 8) = 4', () => {
  assert.equal(gcd(12, 8), 4)
})

test('AC-14 gcd(15, 25) = 5', () => {
  assert.equal(gcd(15, 25), 5)
})

test('AC-15 gcd(1, 7) = 1 (互素)', () => {
  assert.equal(gcd(1, 7), 1)
})

test('AC-16 gcd(0, 5) = 5', () => {
  assert.equal(gcd(0, 5), 5)
})

// ==================== AC-17: format 整数 ====================
test('AC-17 format(4, 2) = "2"', () => {
  assert.equal(format(4, 2), '2')
})

// ==================== AC-18: format 真分数 ====================
test('AC-18 format(1, 2) = "1/2"', () => {
  assert.equal(format(1, 2), '1/2')
})

// ==================== AC-19: format 零 ====================
test('AC-19 format(0, 1) = "0"', () => {
  assert.equal(format(0, 1), '0')
})

// ==================== AC-20: format 负数 ====================
test('AC-20 format(-1, 2) = "-1/2"', () => {
  assert.equal(format(-1, 2), '-1/2')
})

// ==================== AC-21: format 假分数 ====================
test('AC-21 format(3, 2) = "3/2"', () => {
  assert.equal(format(3, 2), '3/2')
})

// ==================== AC-22: format denominator 负 → 符号归 numerator ====================
test('AC-22 format(1, -2) = "-1/2"', () => {
  assert.equal(format(1, -2), '-1/2')
})

// ==================== AC-23: format 0/任意 = "0" ====================
test('AC-23 format(0, 5) = "0"', () => {
  assert.equal(format(0, 5), '0')
})

// ==================== AC-24: 端到端 (1/8 即 0.125) 完整链路 ====================
test('AC-24 end-to-end toFraction(0.125) + format → "1/8"', () => {
  const r = toFraction(0.125)
  assert.equal(format(r.numerator, r.denominator), '1/8')
})

// ==================== AC-25: 端到端 (负分数) 完整链路 ====================
test('AC-25 end-to-end toFraction(-0.5) + format → "-1/2"', () => {
  const r = toFraction(-0.5)
  assert.equal(format(r.numerator, r.denominator), '-1/2')
})

// ==================== AC-26: 学生场景 3/4 ====================
test('AC-26 toFraction(0.75) + format → "3/4"', () => {
  const r = toFraction(0.75)
  assert.equal(format(r.numerator, r.denominator), '3/4')
})
