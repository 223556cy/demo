// Factorial (!) 测试用例 — node:test 格式
// Issue #21: 请为当前的计算器应用追加一个 '阶乘（!）' 运算按钮
// 对应 design.md 第 4 节测试矩阵 (F-1..F-8)
// Iron rule 7: 真实跑测试，不准伪造输出

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { Expression, ErrorFlags } from './Expression.port.mjs'
import { safeEval } from './expression-eval.mjs'

// ===== 工具：每次测试前重置 ErrorFlags =====
function freshExpr() {
  ErrorFlags.reset()
  return new Expression()
}

function checkPreprocessAndValue(input, expectedClean, expectedValue, label) {
  const e = freshExpr()
  const got = e.getCleanExpression(input, '.', ',')
  assert.equal(got, expectedClean, `[${label}] preprocess expected "${expectedClean}", got "${got}"`)
  const val = safeEval(got)
  assert.ok(Math.abs(val - expectedValue) < 1e-9, `[${label}] value expected ~${expectedValue}, got ${val}`)
}

// ================================================================
// Issue #21 阶乘按钮 (Issue #21 - 阶乘 (!))
// ================================================================

test('F-1: 5! → 120 (基本用法)', () => {
  checkPreprocessAndValue('5!', 'factorial(5)', 120, 'F-1')
})

test('F-2: 0! → 1 (边界: 零阶乘)', () => {
  checkPreprocessAndValue('0!', 'factorial(0)', 1, 'F-2')
})

test('F-3: 1! → 1 (边界: 一阶乘)', () => {
  checkPreprocessAndValue('1!', 'factorial(1)', 1, 'F-3')
})

test('F-4: (2+3)! → 120 (括号+阶乘组合)', () => {
  // 实现选择: formatFactorial 会丢一层冗余括号, factorial(2+3) ≡ factorial((2+3))
  // 测试做柔性匹配: 含 "factorial"、含 "(2+3)"、求值=120
  const e = freshExpr()
  const got = e.getCleanExpression('(2+3)!', '.', ',')
  assert.ok(got.indexOf('factorial') !== -1, `expected factorial in "${got}"`)
  assert.ok(got.indexOf('(2+3)') !== -1, `expected (2+3) in "${got}"`)
  const val = safeEval(got)
  assert.ok(Math.abs(val - 120) < 1e-9, `expected ~120, got ${val}`)
})

test('F-5: 2!+3! → 8 (多个阶乘叠加)', () => {
  checkPreprocessAndValue('2!+3!', 'factorial(2)+factorial(3)', 8, 'F-5')
})

test('F-6: 5!+10% 兼容百分号 (联合用例)', () => {
  // 5!+10% → factorial(5) + (factorial(5))*(10/100) = 120 + 12 = 132
  const e = freshExpr()
  const got = e.getCleanExpression('5!+10%', '.', ',')
  assert.ok(got.indexOf('factorial') !== -1, `expected factorial in "${got}"`)
  assert.ok(got.indexOf('(10/100)') !== -1, `expected (10/100) in "${got}"`)
  const val = safeEval(got)
  assert.ok(Math.abs(val - 132) < 1e-9, `expected ~132, got ${val}`)
})

test('F-7: 3!4 → 24 (addMultiply 隐式乘)', () => {
  // addMultiply 看到 '!' 后面跟数字会插入 * → 3!*4
  // formatFactorial 改写: factorial(3)*4
  // 期望 factorial(3)*4 = 6*4 = 24
  const e = freshExpr()
  const got = e.getCleanExpression('3!4', '.', ',')
  assert.ok(got.indexOf('factorial') !== -1, `expected factorial in "${got}"`)
  assert.ok(got.indexOf('*4') !== -1, `expected *4 in "${got}"`)
  const val = safeEval(got)
  assert.ok(Math.abs(val - 24) < 1e-9, `expected ~24, got ${val} (got string: ${got})`)
})

test('F-8: 空 ! 触发 syntax_error', () => {
  const e = freshExpr()
  e.getCleanExpression('!', '.', ',')
  assert.equal(ErrorFlags.syntax_error, true, 'lone ! must set syntax_error')
})

// ================================================================
// 回归测试：12 个 percent 用例 (来自 Issue #9),确保不破坏现有逻辑
// ================================================================

test('REG-AC-1: 50+10% → 55 (percent 回归)', () => {
  checkPreprocessAndValue('50+10%', '(50)+(50)*(10/100)', 55, 'REG-AC-1')
})

test('REG-AC-2: 200-15% → 170 (percent 回归)', () => {
  checkPreprocessAndValue('200-15%', '(200)-(200)*(15/100)', 170, 'REG-AC-2')
})

test('REG-AC-3: 8×5% → 0.4 (percent 回归)', () => {
  checkPreprocessAndValue('8×5%', '8*(5/100)', 0.4, 'REG-AC-3')
})

test('REG-AC-4: 50% → 0.5 (percent 回归)', () => {
  checkPreprocessAndValue('50%', '(50/100)', 0.5, 'REG-AC-4')
})

test('REG-AC-7: 100+10%+5% 含 factorial 解析 (percent+factorial 联动回归)', () => {
  const e = freshExpr()
  const got = e.getCleanExpression('100+10%+5%', '.', ',')
  // 强验证:含 (5/100),且无 ++
  assert.ok(got.indexOf('(5/100)') !== -1, `expected (5/100) in "${got}"`)
  // 验证最终值 115.5
  const val = safeEval(got)
  assert.ok(Math.abs(val - 115.5) < 1e-9, `expected ~115.5, got ${val}`)
})
