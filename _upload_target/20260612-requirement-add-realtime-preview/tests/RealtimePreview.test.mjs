// RealtimePreview 单元测试 — node:test 格式
// 对应 design.md §6 测试矩阵（TC-RP-01 ~ TC-RP-15）
// Iron rule 7: 真实跑测试，不准伪造输出
//
// RED phase: most tests FAIL because computePreview() is a stub returning ''.
// GREEN phase: after T3-T5 the same tests will all PASS.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { PreviewCalculator, ErrorFlags } from './RealtimePreview.port.mjs'
import { safeEval } from './expression-eval.mjs'

// ===== 工具：每次测试前重置 ErrorFlags =====
function freshCalc() {
  ErrorFlags.reset()
  return new PreviewCalculator()
}

// Helper: verify that a complete-expression preview equals the expected
// numerical value (within float tolerance) and that the formatted string
// matches expectations.
function checkNumericPreview(input, expectedNumber, expectedFormatted, label) {
  const c = freshCalc()
  const got = c.computePreview(input, false)  // radianMode=false → isDegree=true
  assert.equal(
    got,
    expectedFormatted,
    `[${label}] preview expected "${expectedFormatted}", got "${got}"`,
  )
  // Verify the formatted string parses back to the expected number
  const parsed = parseFloat(got.replace(/,/g, ''))
  assert.ok(
    Math.abs(parsed - expectedNumber) < 1e-6,
    `[${label}] parsed value expected ~${expectedNumber}, got ${parsed}`,
  )
}

// ===== 15 TC-RP test cases =====

test('TC-RP-01: 空表达式 → ""', () => {
  const c = freshCalc()
  assert.equal(c.computePreview('', false), '')
})

test('TC-RP-02: 末位左括号 "(" → "" (不完整)', () => {
  const c = freshCalc()
  assert.equal(c.computePreview('1+(', false), '')
})

test('TC-RP-03: 简单加法 1+2 → "3"', () => {
  checkNumericPreview('1+2', 3, '3', 'TC-RP-03')
})

test('TC-RP-04: 减法负数 5-10 → "-5"', () => {
  checkNumericPreview('5-10', -5, '-5', 'TC-RP-04')
})

test('TC-RP-05: 不完整加法 1+ → "" (末位运算符)', () => {
  const c = freshCalc()
  assert.equal(c.computePreview('1+', false), '')
})

test('TC-RP-06: 函数未闭合 sin(0 → "" (末位左括号)', () => {
  const c = freshCalc()
  assert.equal(c.computePreview('sin(0', false), '')
})

test('TC-RP-07: 语法错误 1++2 → ""', () => {
  // "1++2" — 末位数字 OK，白名单通过；语法错误由 ErrorFlags 捕获
  const c = freshCalc()
  assert.equal(c.computePreview('1++2', false), '')
})

test('TC-RP-08: 函数 sin(0) → "0"', () => {
  // sin(0) in degree mode = 0
  checkNumericPreview('sin(0)', 0, '0', 'TC-RP-08')
})

test('TC-RP-09: 百分号 50+10% → "55"', () => {
  // 50 + 10% of 50 = 50 + 5 = 55
  checkNumericPreview('50+10%', 55, '55', 'TC-RP-09')
})

test('TC-RP-10: 异常输入 1+( → "" (末位左括号)', () => {
  const c = freshCalc()
  assert.equal(c.computePreview('1+(', false), '')
})

test('TC-RP-11: 格式一致 1000+2000 → "3,000"', () => {
  checkNumericPreview('1000+2000', 3000, '3,000', 'TC-RP-11')
})

test('TC-RP-12: 嵌套括号 (1+2)*(3+4) → "21"', () => {
  checkNumericPreview('(1+2)*(3+4)', 21, '21', 'TC-RP-12')
})

test('TC-RP-13: 长表达式 1+2*3/4-5 → "-2.5"', () => {
  checkNumericPreview('1+2*3/4-5', -2.5, '-2.5', 'TC-RP-13')
})

test('TC-RP-14: 除零 1÷0 → "" (division_by_0)', () => {
  // 末位数字 OK，evaluate 触发 division_by_0 → preview=""
  const c = freshCalc()
  assert.equal(c.computePreview('1÷0', false), '')
})

test('TC-RP-15: AC 等价（清空后） → ""', () => {
  // 模拟 AC 后: expression='' → preview=''
  const c = freshCalc()
  c.computePreview('1+2', false)  // 产生预览
  ErrorFlags.reset()              // AC 行为
  assert.equal(c.computePreview('', false), '')
})

// ===== 回归保护：错误状态隔离 =====
test('REG-RP-1: 错误状态不污染主流程（snapshot/restore）', () => {
  // 1) 触发 division_by_0
  const c = freshCalc()
  c.computePreview('1÷0', false)
  // 2) 立即计算合法表达式，preview 应为 2
  const got = c.computePreview('1+1', false)
  assert.equal(got, '2', `After error, fresh preview should be 2, got "${got}"`)
  // 3) ErrorFlags 状态应被恢复（不残留 division_by_0）
  assert.equal(ErrorFlags.division_by_0, false, 'ErrorFlags.division_by_0 should be restored')
})

// ===== 内部 sanity 测试：与 safeEval 对比 (确认端口实现与数学一致) =====
test('SANITY: safeEval 在所有 TC 用例上都正确', () => {
  // 这条用例保证测试基础设施可用，独立的绿/红指示器
  assert.equal(safeEval('1+2', true), 3)
  assert.equal(safeEval('5-10', true), -5)
  assert.equal(safeEval('sin(0)', true), 0)
  assert.equal(Math.abs(safeEval('1+2*3/4-5', true) - (-2.5)) < 1e-9, true)
  assert.equal(safeEval('(1+2)*(3+4)', true), 21)
  assert.equal(safeEval('1000+2000', true), 3000)
})
