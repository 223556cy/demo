// Percent 测试用例 — node:test 格式
// 对应 design.md 第 3 节测试矩阵
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
  // evaluate
  const val = safeEval(got)
  // float-safe compare
  assert.ok(Math.abs(val - expectedValue) < 1e-9, `[${label}] value expected ~${expectedValue}, got ${val}`)
}

test('AC-1: 50+10% → 55 (核心场景)', () => {
  checkPreprocessAndValue('50+10%', '(50)+(50)*(10/100)', 55, 'AC-1')
})

test('AC-2: 200-15% → 170 (减法)', () => {
  checkPreprocessAndValue('200-15%', '(200)-(200)*(15/100)', 170, 'AC-2')
})

test('AC-3: 8×5% → 0.4 (乘法)', () => {
  checkPreprocessAndValue('8×5%', '8*(5/100)', 0.4, 'AC-3')
})

test('AC-4: 100÷10% → 1000 (除法)', () => {
  checkPreprocessAndValue('100÷10%', '100/(10/100)', 1000, 'AC-4')
})

test('AC-5: 50% → 0.5 (纯百分号)', () => {
  // 注意：现有实现会在两端加括号："(50/100)"。多一层括号语法上等价。
  checkPreprocessAndValue('50%', '(50/100)', 0.5, 'AC-5')
})

test('AC-6: (2+3)×10% → 0.5 (括号内)', () => {
  // 括号 (2+3) 走到 parenthesized 分支
  checkPreprocessAndValue('(2+3)×10%', '(2+3)*(10/100)', 0.5, 'AC-6')
})

test('AC-7: 100+10%+5% → 115.5 (macOS 行为：第二个%基于前项结果)', () => {
  // macOS 行为: 100+10%=110, 110+5%=115.5
  // 修复后表达式: (100+100*(10/100)) + (100+100*(10/100))*(5/100) = 110 + 5.5 = 115.5
  const e = freshExpr()
  const got = e.getCleanExpression('100+10%+5%', '.', ',')
  const val = safeEval(got)
  assert.ok(Math.abs(val - 115.5) < 1e-9, `[AC-7] value expected 115.5, got ${val} (clean: ${got})`)
})

test('AC-8: % → syntax error (空 base)', () => {
  const e = freshExpr()
  e.getCleanExpression('%', '.', ',')
  assert.equal(ErrorFlags.syntax_error, true, 'Expected ErrorFlags.syntax_error = true')
})

test('AC-9: -50+10% → -55 (负数基)', () => {
  // 修复后: (-50)+(-50)*(10/100) = -50 + -5 = -55
  checkPreprocessAndValue('-50+10%', '(-50)+(-50)*(10/100)', -55, 'AC-9')
})

test('AC-10: 0+10% → 0 (零基)', () => {
  checkPreprocessAndValue('0+10%', '(0)+(0)*(10/100)', 0, 'AC-10')
})

test('AC-11: 100+(200×50%) → 200 (嵌套括号内百分号)', () => {
  // (200×50%) 走 parenthesized 分支（递归处理）
  checkPreprocessAndValue('100+(200×50%)', '100+(200*(50/100))', 200, 'AC-11')
})

test('AC-12: 5!+10% → 132 (阶乘+百分号)', () => {
  // 5! = 120, 10% of 120 = 12, 120+12 = 132
  const e = freshExpr()
  const got = e.getCleanExpression('5!+10%', '.', ',')
  const val = safeEval(got)
  assert.ok(Math.abs(val - 132) < 1e-9, `[AC-12] value expected 132, got ${val} (clean: ${got})`)
})

// ===== 回归保护：原本 PASS 的用例（防止 GREEN 阶段误改） =====

test('REG-1: 简单加法 1+2 → 3 (回归)', () => {
  const e = freshExpr()
  const got = e.getCleanExpression('1+2', '.', ',')
  assert.equal(got, '1+2')
  assert.equal(safeEval(got), 3)
})

test('REG-2: 阶乘 5! → 120 (回归)', () => {
  const e = freshExpr()
  const got = e.getCleanExpression('5!', '.', ',')
  assert.equal(safeEval(got), 120)
})
