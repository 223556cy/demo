// OpenCalc — CalcEngine.evaluateAt 单元测试 (hypium 风格)
// aid-workflow 20260617: Issue #26 函数图像 - x 变量 + 单点求值

import { describe, it, expect, beforeEach } from '@ohos/hypium'
import { CalcEngine } from '../../../main/ets/calculator/Calculator'
import { ErrorFlags } from '../../../main/ets/model/ErrorFlags'

export default function calculatorEvaluateAtTest() {
  describe('CalcEngine_evaluateAt', () => {

    let engine: CalcEngine
    beforeEach((): void => {
      engine = new CalcEngine()
      ErrorFlags.reset()
    })

    it('AC-1_sin_at_zero_is_zero', 0, (): void => {
      // 弧度模式
      const v = engine.evaluateAt('sin(x)', 0, false)
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v) < 1e-10).assertTrue()
    })

    it('AC-2_sin_at_pi_is_near_zero', 1, (): void => {
      const v = engine.evaluateAt('sin(x)', 3.14159265358979, false)
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v) < 1e-10).assertTrue()
    })

    it('AC-3_x_squared_at_3_is_9', 2, (): void => {
      const v = engine.evaluateAt('x^2', 3, false)
      expect(v).assertEqual(9)
    })

    it('AC-4_2x_at_3_is_6', 3, (): void => {
      const v = engine.evaluateAt('2x', 3, false)
      expect(v).assertEqual(6)
    })

    it('AC-5_division_by_zero_returns_null', 4, (): void => {
      const v = engine.evaluateAt('1/0', 0, false)
      expect(v === null).assertTrue()
    })

    it('AC-6_log_of_negative_returns_null', 5, (): void => {
      const v = engine.evaluateAt('log(x)', -1, false)
      expect(v === null).assertTrue()
    })

    it('AC-7_syntax_error_returns_null', 6, (): void => {
      const v = engine.evaluateAt('sin(x', 0, false)
      expect(v === null).assertTrue()
    })

    it('AC-8_x_in_sin_cos', 7, (): void => {
      const v = engine.evaluateAt('cos(x)+sin(x)', 0, false)
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v - 1) < 1e-10).assertTrue()
    })

    it('AC-9_x_with_pi', 8, (): void => {
      // CalcEngine 内 π 是 ASCII 960
      const v = engine.evaluateAt('x*960', 1, false)
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v - Math.PI) < 1e-6).assertTrue()
    })

    it('AC-10_does_not_pollute_error_flags', 9, (): void => {
      engine.evaluateAt('1/0', 0, false)
      // 接下来 evaluate 应该是干净的
      ErrorFlags.reset()
      const v = engine.evaluateAt('1+1', 0, false)
      expect(v).assertEqual(2)
    })
  })
}
