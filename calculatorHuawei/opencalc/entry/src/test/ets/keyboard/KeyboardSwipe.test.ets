// OpenCalc — Issue #29 竖屏滑动切换键盘模式 - 单元测试（hypium 风格）
// aid-workflow 20260618: TDD RED 阶段，测试覆盖 KeyboardMode / cycleMode / onSwiperChange / 启动优先级 / PreferencesStore

import { describe, it, expect } from '@ohos/hypium'
import {
  KeyboardMode,
  cycleMode,
  nextMode,
  applySwiperIndex,
  isValidModeIndex,
  resolveStartupMode
} from '../../../main/ets/model/ModeController'
import { DEFAULT_PREFERENCES, ScientificModeType } from '../../../main/ets/model/Models'

export default function keyboardSwipeTest() {
  describe('KeyboardMode_enum_values', () => {

    it('KM_V01_BASIC_equals_0', 0, (): void => {
      expect(KeyboardMode.BASIC).assertEqual(0)
    })

    it('KM_V02_SCIENTIFIC_equals_1', 1, (): void => {
      expect(KeyboardMode.SCIENTIFIC).assertEqual(1)
    })

    it('KM_V03_PROGRAMMER_equals_2', 2, (): void => {
      expect(KeyboardMode.PROGRAMMER).assertEqual(2)
    })
  })

  describe('isValidModeIndex', () => {

    it('VMI_01_zero_is_valid', 3, (): void => {
      expect(isValidModeIndex(0)).assertTrue()
    })

    it('VMI_02_one_is_valid', 4, (): void => {
      expect(isValidModeIndex(1)).assertTrue()
    })

    it('VMI_03_two_is_valid', 5, (): void => {
      expect(isValidModeIndex(2)).assertTrue()
    })

    it('VMI_04_three_is_invalid', 6, (): void => {
      expect(isValidModeIndex(3)).assertFalse()
    })

    it('VMI_05_negative_is_invalid', 7, (): void => {
      expect(isValidModeIndex(-1)).assertFalse()
    })
  })

  describe('nextMode_three_state_cycle', () => {

    it('NM_01_BASIC_to_SCIENTIFIC', 8, (): void => {
      expect(nextMode(KeyboardMode.BASIC)).assertEqual(KeyboardMode.SCIENTIFIC)
    })

    it('NM_02_SCIENTIFIC_to_PROGRAMMER', 9, (): void => {
      expect(nextMode(KeyboardMode.SCIENTIFIC)).assertEqual(KeyboardMode.PROGRAMMER)
    })

    it('NM_03_PROGRAMMER_wraps_to_BASIC', 10, (): void => {
      expect(nextMode(KeyboardMode.PROGRAMMER)).assertEqual(KeyboardMode.BASIC)
    })
  })

  describe('cycleMode_helper', () => {

    it('CM_01_advance_BASIC_to_SCIENTIFIC', 11, (): void => {
      expect(cycleMode(KeyboardMode.BASIC)).assertEqual(KeyboardMode.SCIENTIFIC)
    })

    it('CM_02_advance_SCIENTIFIC_to_PROGRAMMER', 12, (): void => {
      expect(cycleMode(KeyboardMode.SCIENTIFIC)).assertEqual(KeyboardMode.PROGRAMMER)
    })

    it('CM_03_advance_PROGRAMMER_wraps_BASIC', 13, (): void => {
      expect(cycleMode(KeyboardMode.PROGRAMMER)).assertEqual(KeyboardMode.BASIC)
    })
  })

  describe('applySwiperIndex_legal_range', () => {

    it('ASI_01_zero_to_BASIC', 14, (): void => {
      expect(applySwiperIndex(0)).assertEqual(KeyboardMode.BASIC)
    })

    it('ASI_02_one_to_SCIENTIFIC', 15, (): void => {
      expect(applySwiperIndex(1)).assertEqual(KeyboardMode.SCIENTIFIC)
    })

    it('ASI_03_two_to_PROGRAMMER', 16, (): void => {
      expect(applySwiperIndex(2)).assertEqual(KeyboardMode.PROGRAMMER)
    })
  })

  describe('applySwiperIndex_out_of_range_returns_null', () => {

    it('ASI_NEG_negative_returns_null', 17, (): void => {
      expect(applySwiperIndex(-1) === null).assertTrue()
    })

    it('ASI_NEG_three_returns_null', 18, (): void => {
      expect(applySwiperIndex(3) === null).assertTrue()
    })

    it('ASI_NEG_hundred_returns_null', 19, (): void => {
      expect(applySwiperIndex(100) === null).assertTrue()
    })
  })

  describe('resolveStartupMode_priority', () => {

    it('ST_01_scientific_1_wins_over_programmer_1', 20, (): void => {
      expect(resolveStartupMode(1, 1)).assertEqual(KeyboardMode.SCIENTIFIC)
    })

    it('ST_02_scientific_1_wins_over_programmer_0', 21, (): void => {
      expect(resolveStartupMode(1, 0)).assertEqual(KeyboardMode.SCIENTIFIC)
    })

    it('ST_03_programmer_1_with_scientific_0_yields_PROGRAMMER', 22, (): void => {
      expect(resolveStartupMode(0, 1)).assertEqual(KeyboardMode.PROGRAMMER)
    })

    it('ST_04_both_zero_yields_BASIC', 23, (): void => {
      expect(resolveStartupMode(0, 0)).assertEqual(KeyboardMode.BASIC)
    })

    it('ST_05_scientific_2_off_yields_fallthrough_to_programmer_1', 24, (): void => {
      expect(resolveStartupMode(2, 1)).assertEqual(KeyboardMode.PROGRAMMER)
    })

    it('ST_06_scientific_2_programmer_0_yields_BASIC', 25, (): void => {
      expect(resolveStartupMode(2, 0)).assertEqual(KeyboardMode.BASIC)
    })
  })

  describe('KeyboardMode_preferences_default', () => {

    it('PD_01_programmerModeDefault_default_zero', 26, (): void => {
      expect(DEFAULT_PREFERENCES.programmerModeDefault).assertEqual(ScientificModeType.NOT_ACTIVE)
    })

    it('PD_02_scientificModeDefault_default_zero', 27, (): void => {
      expect(DEFAULT_PREFERENCES.scientificModeDefault).assertEqual(ScientificModeType.NOT_ACTIVE)
    })
  })
}
