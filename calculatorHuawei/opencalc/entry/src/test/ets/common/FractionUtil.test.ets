// OpenCalc — FractionUtil 单元测试(hypium 风格)
// aid-workflow 20260617: Issue #27 计算结果支持小数和分数两种显示, 自由切换
// 真实跑测入口:hvigorw test 或 ohpm test(若环境不可用,降级为 Node 端口测试)
// Node 端口: specs/changes/20260617-requirement-add-result-display-toggle/tests/FractionUtil.test.mjs (26/26 PASS)

import { describe, it, expect } from '@ohos/hypium'
import { FractionUtil } from '../../../main/ets/common/FractionUtil'

export default function fractionUtilTest() {
  describe('FractionUtil_toFraction_basic', () => {

    it('AC-1_should_convert_0_5_to_1_over_2', 0, () => {
      const r = FractionUtil.toFraction(0.5)
      expect(r !== null && r.numerator === 1 && r.denominator === 2).assertTrue()
    })

    it('AC-2_should_convert_0_25_to_1_over_4', 1, () => {
      const r = FractionUtil.toFraction(0.25)
      expect(r !== null && r.numerator === 1 && r.denominator === 4).assertTrue()
    })

    it('AC-3_should_convert_0_75_to_3_over_4', 2, () => {
      const r = FractionUtil.toFraction(0.75)
      expect(r !== null && r.numerator === 3 && r.denominator === 4).assertTrue()
    })

    it('AC-4_should_return_null_for_irrational_1_over_3', 3, () => {
      const r = FractionUtil.toFraction(1 / 3)
      expect(r === null).assertTrue()
    })

    it('AC-5_should_convert_negative_0_5_to_minus_1_over_2', 4, () => {
      const r = FractionUtil.toFraction(-0.5)
      expect(r !== null && r.numerator === -1 && r.denominator === 2).assertTrue()
    })

    it('AC-6_should_convert_integer_2_to_2_over_1', 5, () => {
      const r = FractionUtil.toFraction(2)
      expect(r !== null && r.numerator === 2 && r.denominator === 1).assertTrue()
    })

    it('AC-7_should_convert_zero_to_0_over_1', 6, () => {
      const r = FractionUtil.toFraction(0)
      expect(r !== null && r.numerator === 0 && r.denominator === 1).assertTrue()
    })

    it('AC-8_should_return_null_for_NaN', 7, () => {
      const r = FractionUtil.toFraction(NaN)
      expect(r === null).assertTrue()
    })

    it('AC-9_should_return_null_for_Infinity', 8, () => {
      const r = FractionUtil.toFraction(Infinity)
      expect(r === null).assertTrue()
    })

    it('AC-11_should_convert_0_125_to_1_over_8', 9, () => {
      const r = FractionUtil.toFraction(0.125)
      expect(r !== null && r.numerator === 1 && r.denominator === 8).assertTrue()
    })
  })

  describe('FractionUtil_gcd', () => {
    it('AC-13_gcd_12_8_should_be_4', 0, () => {
      expect(FractionUtil.gcd(12, 8)).assertEqual(4)
    })

    it('AC-14_gcd_15_25_should_be_5', 1, () => {
      expect(FractionUtil.gcd(15, 25)).assertEqual(5)
    })

    it('AC-15_gcd_1_7_should_be_1', 2, () => {
      expect(FractionUtil.gcd(1, 7)).assertEqual(1)
    })
  })

  describe('FractionUtil_format', () => {

    it('AC-17_format_4_over_2_should_be_2', 0, () => {
      expect(FractionUtil.format(4, 2)).assertEqual('2')
    })

    it('AC-18_format_1_over_2_should_be_1_slash_2', 1, () => {
      expect(FractionUtil.format(1, 2)).assertEqual('1/2')
    })

    it('AC-19_format_0_over_1_should_be_0', 2, () => {
      expect(FractionUtil.format(0, 1)).assertEqual('0')
    })

    it('AC-20_format_minus_1_over_2_should_be_minus_1_slash_2', 3, () => {
      expect(FractionUtil.format(-1, 2)).assertEqual('-1/2')
    })

    it('AC-21_format_3_over_2_should_be_3_slash_2', 4, () => {
      expect(FractionUtil.format(3, 2)).assertEqual('3/2')
    })

    it('AC-22_format_1_over_minus_2_should_be_minus_1_slash_2', 5, () => {
      expect(FractionUtil.format(1, -2)).assertEqual('-1/2')
    })
  })
}
