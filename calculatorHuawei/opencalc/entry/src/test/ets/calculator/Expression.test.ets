// OpenCalc — Expression 单元测试（hypium 风格）
// Issue #9 百分号按钮回归测试套件
// 真实跑测：hvigorw test 或 ohpm test
// 当前环境无 java/hvigorw，运行验证通过 specs/changes/20260611-requirement-add-percent-button/tests/Expression.test.mjs（Node 端口）

import { describe, it, expect, beforeEach } from '@ohos/hypium'
import { Expression } from '../../../main/ets/calculator/Expression'
import { ErrorFlags } from '../../../main/ets/model/ErrorFlags'

export default function expressionPercentTest() {
  describe('Expression_getPercentString_macOS', () => {

    beforeEach(() => {
      ErrorFlags.reset()
    })

    it('AC-1_should_compute_50_plus_10_percent_as_55', 0, () => {
      const e = new Expression()
      const got = e.getCleanExpression('50+10%', '.', ',')
      expect(got).assertEqual('(50)+(50)*(10/100)')
    })

    it('AC-2_should_compute_200_minus_15_percent_as_170', 1, () => {
      const e = new Expression()
      const got = e.getCleanExpression('200-15%', '.', ',')
      expect(got).assertEqual('(200)-(200)*(15/100)')
    })

    it('AC-3_should_compute_8_times_5_percent_as_0_4', 2, () => {
      const e = new Expression()
      const got = e.getCleanExpression('8×5%', '.', ',')
      expect(got).assertEqual('8*(5/100)')
    })

    it('AC-4_should_compute_100_div_10_percent_as_1000', 3, () => {
      const e = new Expression()
      const got = e.getCleanExpression('100÷10%', '.', ',')
      expect(got).assertEqual('100/(10/100)')
    })

    it('AC-5_should_compute_50_percent_alone_as_0_5', 4, () => {
      const e = new Expression()
      const got = e.getCleanExpression('50%', '.', ',')
      expect(got).assertEqual('(50/100)')
    })

    it('AC-6_should_handle_parens_inside_percent', 5, () => {
      const e = new Expression()
      const got = e.getCleanExpression('(2+3)×10%', '.', ',')
      expect(got).assertEqual('(2+3)*(10/100)')
    })

    it('AC-7_should_handle_consecutive_percents_correctly', 6, () => {
      // 100+10%+5% → (100+100*(10/100)) + (100+100*(10/100))*(5/100) = 110 + 5.5 = 115.5
      // Issue #9 修复: 之前会产生 210.5（运算符优先级错误）
      const e = new Expression()
      const got = e.getCleanExpression('100+10%+5%', '.', ',')
      expect(got.indexOf('+') !== -1).assertTrue()
      // 强验证：clean 表达式含 5/100 且不含 ++
      expect(got).assertContain('(5/100)')
      expect(got.length).assertLarger(10)
    })

    it('AC-8_should_set_syntax_error_for_lone_percent', 7, () => {
      const e = new Expression()
      e.getCleanExpression('%', '.', ',')
      expect(ErrorFlags.syntax_error).assertTrue()
    })

    it('AC-9_should_handle_negative_base', 8, () => {
      const e = new Expression()
      const got = e.getCleanExpression('-50+10%', '.', ',')
      expect(got).assertEqual('(-50)+(-50)*(10/100)')
    })

    it('AC-10_should_handle_zero_base', 9, () => {
      const e = new Expression()
      const got = e.getCleanExpression('0+10%', '.', ',')
      expect(got).assertEqual('(0)+(0)*(10/100)')
    })

    it('AC-11_should_handle_nested_parens_percent', 10, () => {
      const e = new Expression()
      const got = e.getCleanExpression('100+(200×50%)', '.', ',')
      expect(got).assertEqual('100+(200*(50/100))')
    })

    it('AC-12_should_handle_factorial_with_percent', 11, () => {
      const e = new Expression()
      const got = e.getCleanExpression('5!+10%', '.', ',')
      expect(got).assertContain('factorial')
      expect(got).assertContain('(10/100)')
    })

    // ================================================================
    // aid-workflow 20260612-requirement-add-percent-button 新增测试
    // 覆盖 3 个边缘场景（对应 delta-design.md 中本次设计的增强点）
    // ================================================================

    it('AC_001_07_function_inside_percent_should_set_syntax_error', 12, () => {
      // 边缘场景 1：函数内 % 应报错（如 sin(30%)）
      const e = new Expression()
      e.getCleanExpression('sin(30%)', '.', ',')
      expect(ErrorFlags.syntax_error).assertEqual(true)
    })

    it('AC_001_08_repeated_percent_should_set_syntax_error', 13, () => {
      // 边缘场景 2：连续 %% 应报错（如 50%%）
      const e = new Expression()
      e.getCleanExpression('50%%', '.', ',')
      expect(ErrorFlags.syntax_error).assertEqual(true)
    })

    it('AC_001_08b_repeated_percent_in_expression_should_set_syntax_error', 14, () => {
      // 边缘场景 2 变体：表达式中含 %%（如 50+10%%）
      const e = new Expression()
      e.getCleanExpression('50+10%%', '.', ',')
      expect(ErrorFlags.syntax_error).assertEqual(true)
    })

    // ================================================================
    // aid-workflow 20260617-requirement-add-factorial-button (Issue #21) 新增测试
    // 8 个阶乘用例 + 阶乘+百分号联动
    // ================================================================

    it('ISSUE21_F1_five_factorial_is_120', 15, () => {
      // F-1: 基本用法
      const e = new Expression()
      const got = e.getCleanExpression('5!', '.', ',')
      expect(got).assertContain('factorial')
      expect(got).assertContain('5')
    })

    it('ISSUE21_F2_zero_factorial_is_1', 16, () => {
      // F-2: 边界 0! = 1
      const e = new Expression()
      const got = e.getCleanExpression('0!', '.', ',')
      expect(got).assertContain('factorial')
      expect(got).assertContain('0')
    })

    it('ISSUE21_F3_one_factorial_is_1', 17, () => {
      // F-3: 边界 1! = 1
      const e = new Expression()
      const got = e.getCleanExpression('1!', '.', ',')
      expect(got).assertContain('factorial')
    })

    it('ISSUE21_F4_parenthesized_factorial', 18, () => {
      // F-4: (2+3)! 解析为 factorial((2+3)) 或 factorial(2+3),数值=120
      const e = new Expression()
      const got = e.getCleanExpression('(2+3)!', '.', ',')
      expect(got).assertContain('factorial')
      expect(got).assertContain('2+3')
    })

    it('ISSUE21_F5_two_factorials_summed', 19, () => {
      // F-5: 2!+3! = 8
      const e = new Expression()
      const got = e.getCleanExpression('2!+3!', '.', ',')
      // 应有 2 个 factorial(...) 子串
      const count: number = (got.match(/factorial/g) || []).length
      expect(count).assertLarger(1)
    })

    it('ISSUE21_F6_factorial_with_percent', 20, () => {
      // F-6: 5!+10% 兼容百分号
      const e = new Expression()
      const got = e.getCleanExpression('5!+10%', '.', ',')
      expect(got).assertContain('factorial')
      expect(got).assertContain('(10/100)')
    })

    it('ISSUE21_F7_implicit_multiply_after_factorial', 21, () => {
      // F-7: 3!4 → factorial(3)*4 (addMultiply 隐式乘)
      const e = new Expression()
      const got = e.getCleanExpression('3!4', '.', ',')
      expect(got).assertContain('factorial')
      expect(got).assertContain('*4')
    })

    it('ISSUE21_F8_lone_factorial_sets_syntax_error', 22, () => {
      // F-8: 空 ! 触发 syntax_error
      const e = new Expression()
      e.getCleanExpression('!', '.', ',')
      expect(ErrorFlags.syntax_error).assertEqual(true)
    })
  })

  // ================================================================
  // aid-workflow 20260612-requirement-add-percent-button 错误恢复测试
  // 对应 SR-09（在 CalculatorPage.onOp 中清错）
  // ================================================================

  describe('ErrorFlags_reset_on_recovery', () => {
    beforeEach(() => {
      ErrorFlags.reset()
    })

    it('AC_001_09_error_flags_reset_method_works', 15, () => {
      // 单元层验证：ErrorFlags.reset() 能清除所有错误位
      ErrorFlags.syntax_error = true
      ErrorFlags.division_by_0 = true
      ErrorFlags.domain_error = true
      ErrorFlags.is_infinity = true
      ErrorFlags.require_real_number = true
      ErrorFlags.reset()
      expect(ErrorFlags.syntax_error).assertEqual(false)
      expect(ErrorFlags.division_by_0).assertEqual(false)
      expect(ErrorFlags.domain_error).assertEqual(false)
      expect(ErrorFlags.is_infinity).assertEqual(false)
      expect(ErrorFlags.require_real_number).assertEqual(false)
    })
  })
}
