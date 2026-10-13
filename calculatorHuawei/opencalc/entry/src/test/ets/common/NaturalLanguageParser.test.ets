// OpenCalc — NaturalLanguageParser 单元测试(hypium 风格)
// aid-workflow 20260615: Issue #14 单位换算功能
// aid-workflow 20260617: Issue #25 单位换算扩展 (area/time/speed 别名)
// 真实跑测入口:hvigorw test 或 ohpm test(若环境不可用,降级为 Node 端口测试)
// 端口:specs/changes/20260617-requirement-add-中等模糊/tests/NaturalLanguageParser.port.mjs

import { describe, it, expect } from '@ohos/hypium'
import { NaturalLanguageParser, ParseResult } from '../../../main/ets/common/NaturalLanguageParser'

export default function naturalLanguageParserTest() {
  describe('NaturalLanguageParser_chinese', () => {
    it('NL_CN_L01_100cm_to_inch', 0, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100厘米转英寸')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(100)
        expect(r.from).assertEqual('cm')
        expect(r.to).assertEqual('inch')
        expect(r.category).assertEqual('length')
      }
    })
    it('NL_CN_L02_1mi_to_km', 1, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1英里转千米')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(1)
        expect(r.from).assertEqual('mi')
        expect(r.to).assertEqual('km')
      }
    })
    it('NL_CN_T01_30C_to_F', 2, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('30摄氏度转华氏度')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(30)
        expect(r.from).assertEqual('C')
        expect(r.to).assertEqual('F')
        expect(r.category).assertEqual('temperature')
      }
    })
    it('NL_CN_T02_0C_to_K', 3, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('0摄氏度转开尔文')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(0)
        expect(r.from).assertEqual('C')
        expect(r.to).assertEqual('K')
      }
    })
    it('NL_CN_M01_5lb_to_kg', 4, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('5磅转千克')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(5)
        expect(r.from).assertEqual('lb')
        expect(r.to).assertEqual('kg')
      }
    })
    it('NL_CN_V01_1gal_to_L', 5, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1加仑转升')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(1)
        expect(r.from).assertEqual('gal')
        expect(r.to).assertEqual('L')
      }
    })
  })

  describe('NaturalLanguageParser_english', () => {
    it('NL_EN_L01_100cm_to_inch', 0, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100cm to inch')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(100)
        expect(r.from).assertEqual('cm')
        expect(r.to).assertEqual('inch')
      }
    })
    it('NL_EN_T01_100F_to_C', 1, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100F to C')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(100)
        expect(r.from).assertEqual('F')
        expect(r.to).assertEqual('C')
      }
    })
    it('NL_EN_M01_1kg_to_g', 2, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1 kg to g')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(1)
        expect(r.from).assertEqual('kg')
        expect(r.to).assertEqual('g')
      }
    })
    it('NL_EN_V01_128floz_to_gal', 3, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('128 fl oz to gal')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(128)
        expect(r.from).assertEqual('fl_oz')
        expect(r.to).assertEqual('gal')
      }
    })
    it('NL_EN_V02_1L_to_mL_arrow', 4, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1L->mL')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(1)
        expect(r.from).assertEqual('L')
        expect(r.to).assertEqual('mL')
      }
    })
  })

  describe('NaturalLanguageParser_aliases', () => {
    it('NL_AL_L01_gongfen_to_cm', 0, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100公分转英寸')
      expect(r !== null).assertTrue()
      if (r !== null) expect(r.from).assertEqual('cm')
    })
    it('NL_AL_L02_gongli_to_km', 1, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1公里转英里')
      expect(r !== null).assertTrue()
      if (r !== null) expect(r.from).assertEqual('km')
    })
    it('NL_AL_T01_huashi_to_F', 2, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100华氏转摄氏')
      expect(r !== null).assertTrue()
      if (r !== null) expect(r.from).assertEqual('F')
    })
    it('NL_AL_M01_gongjin_to_kg', 3, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1公斤转克')
      expect(r !== null).assertTrue()
      if (r !== null) expect(r.from).assertEqual('kg')
    })
  })

  describe('NaturalLanguageParser_errors', () => {
    it('NL_ERR_01_m_to_kg_cross', 0, () => {
      expect(NaturalLanguageParser.parse('1米转千克')).assertEqual(null)
    })
    it('NL_ERR_02_abc_no_digit', 1, () => {
      expect(NaturalLanguageParser.parse('abc 厘米 转 英寸')).assertEqual(null)
    })
    it('NL_ERR_03_unknown_unit', 2, () => {
      expect(NaturalLanguageParser.parse('1 未知单位 转 米')).assertEqual(null)
    })
    it('NL_ERR_04_no_converter', 3, () => {
      expect(NaturalLanguageParser.parse('100cm')).assertEqual(null)
    })
    it('NL_ERR_05_math_expr', 4, () => {
      expect(NaturalLanguageParser.parse('1+2')).assertEqual(null)
    })
    it('NL_ERR_06_empty', 5, () => {
      expect(NaturalLanguageParser.parse('')).assertEqual(null)
    })
  })

  // aid-workflow 20260617: Issue #25 单位换算扩展 — area/time/speed 别名测试
  describe('NaturalLanguageParser_area_cn', () => {
    it('NL_CN_A01_100mu_to_m2', 0, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100亩转平方米')
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.value).assertEqual(100)
        expect(r.from).assertEqual('mu')
        expect(r.to).assertEqual('m2')
        expect(r.category).assertEqual('area')
      }
    })
    it('NL_CN_A02_1acre_to_m2', 1, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1英亩转平方米')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('acre'); expect(r.to).assertEqual('m2') }
    })
    it('NL_CN_A03_1hectare_to_m2', 2, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1公顷转平方米')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('hectare'); expect(r.to).assertEqual('m2') }
    })
    it('NL_CN_A04_1km2_to_m2', 3, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1平方千米转平方米')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('km2'); expect(r.to).assertEqual('m2') }
    })
    it('NL_CN_A05_100ft2_to_m2', 4, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100平方英尺转平方米')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('ft2'); expect(r.to).assertEqual('m2') }
    })
    it('NL_EN_A01_100acre_to_m2', 5, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100 acre to m2')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('acre'); expect(r.to).assertEqual('m2') }
    })
    it('NL_EN_A02_1hectare_to_m2', 6, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1 hectare to m2')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('hectare'); expect(r.to).assertEqual('m2') }
    })
    it('NL_EN_A03_1km2_to_m2', 7, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1 km2 to m2')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('km2'); expect(r.to).assertEqual('m2') }
    })
  })

  describe('NaturalLanguageParser_time_cn', () => {
    it('NL_CN_Ti01_2h_to_min', 0, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('2小时转分钟')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.value).assertEqual(2); expect(r.from).assertEqual('h'); expect(r.to).assertEqual('min') }
    })
    it('NL_CN_Ti02_1d_to_h', 1, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1天转小时')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('d'); expect(r.to).assertEqual('h') }
    })
    it('NL_CN_Ti03_1wk_to_d', 2, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1周转天')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('wk'); expect(r.to).assertEqual('d') }
    })
    it('NL_CN_Ti04_1mo_to_d', 3, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1月转天')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('mo'); expect(r.to).assertEqual('d') }
    })
    it('NL_CN_Ti05_1yr_to_d', 4, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1年转天')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('yr'); expect(r.to).assertEqual('d') }
    })
    it('NL_CN_Ti06_1000ms_to_s', 5, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1000毫秒转秒')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('ms'); expect(r.to).assertEqual('s') }
    })
    it('NL_EN_Ti01_2hour_to_min', 6, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('2 hour to min')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('h'); expect(r.to).assertEqual('min') }
    })
    it('NL_EN_Ti02_1day_to_hour', 7, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1 day to hour')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('d'); expect(r.to).assertEqual('h') }
    })
    it('NL_EN_Ti03_1year_to_day', 8, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1 year to day')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('yr'); expect(r.to).assertEqual('d') }
    })
  })

  describe('NaturalLanguageParser_speed_cn', () => {
    it('NL_CN_S01_60mph_to_kmh', 0, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('60英里每小时转千米每小时')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.value).assertEqual(60); expect(r.from).assertEqual('mph'); expect(r.to).assertEqual('kmh') }
    })
    it('NL_CN_S02_100kmh_to_mps', 1, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('100千米每小时转米每秒')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('kmh'); expect(r.to).assertEqual('m_s') }
    })
    it('NL_CN_S03_1knot_to_kmh', 2, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1节转千米每小时')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('knot'); expect(r.to).assertEqual('kmh') }
    })
    it('NL_CN_S04_1mach_to_mps', 3, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1马赫转米每秒')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('mach'); expect(r.to).assertEqual('m_s') }
    })
    it('NL_CN_S05_10mps_to_kmh', 4, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('10米每秒转千米每小时')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('m_s'); expect(r.to).assertEqual('kmh') }
    })
    it('NL_EN_S01_60mph_to_kmh', 5, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('60 mph to kmh')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('mph'); expect(r.to).assertEqual('kmh') }
    })
    it('NL_EN_S02_1knot_to_kmh', 6, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1 knot to kmh')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('knot'); expect(r.to).assertEqual('kmh') }
    })
    it('NL_EN_S03_1mach_to_mps', 7, () => {
      const r: ParseResult | null = NaturalLanguageParser.parse('1 mach to m/s')
      expect(r !== null).assertTrue()
      if (r !== null) { expect(r.from).assertEqual('mach'); expect(r.to).assertEqual('m_s') }
    })
  })

  describe('NaturalLanguageParser_cross_category_new', () => {
    it('NL_XC_01_area_to_time', 0, () => {
      expect(NaturalLanguageParser.parse('100亩转小时')).assertEqual(null)
    })
    it('NL_XC_02_time_to_speed', 1, () => {
      expect(NaturalLanguageParser.parse('2小时转千米每小时')).assertEqual(null)
    })
    it('NL_XC_03_speed_to_area', 2, () => {
      expect(NaturalLanguageParser.parse('60英里每小时转平方米')).assertEqual(null)
    })
  })
}
