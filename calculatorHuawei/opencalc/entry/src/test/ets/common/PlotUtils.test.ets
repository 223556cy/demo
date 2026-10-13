// OpenCalc — PlotUtils 单元测试 (hypium 风格)
// Issue #26 函数图像绘制 - 工具类纯函数测试
// 真实跑测: hvigorw test 或 ohpm test
// Node mock 测试: specs/changes/20260617-requirement-add-plot-graph/tests/PlotUtils.test.mjs

import { describe, it, expect } from '@ohos/hypium'
import { PlotUtils, PlotPoint, PlotSeries, PlotBounds, Evaluator } from '../../../main/ets/common/PlotUtils'

export default function plotUtilsTest() {
  describe('PlotUtils_sampleSeries', () => {
    // 简单求值器: f(x) = x
    const linear: Evaluator = (expr: string, x: number): number | null => x

    it('AC-1_sample_5_points_linear', 0, (): void => {
      const s: PlotSeries = PlotUtils.sampleSeries('x', 0, 4, 5, linear)
      expect(s.points.length).assertEqual(5)
      expect(s.points[0].x).assertEqual(0)
      expect(s.points[4].x).assertEqual(4)
      expect(s.points[2].x).assertEqual(2)
    })

    it('AC-2_sample_returns_null_on_evaluator_null', 1, (): void => {
      const nullEval: Evaluator = (_: string, x: number): number | null => x < 0 ? null : x
      const s: PlotSeries = PlotUtils.sampleSeries('x', -2, 2, 5, nullEval)
      expect(s.points.length).assertEqual(5)
      expect(s.points[0].y === null).assertTrue()
      expect(s.points[2].y).assertEqual(0)
      expect(s.points[4].y).assertEqual(2)
    })

    it('AC-3_sample_at_least_2_points_when_samples_lt_2', 2, (): void => {
      const s: PlotSeries = PlotUtils.sampleSeries('x', 0, 1, 1, linear)
      expect(s.points.length >= 2).assertTrue()
    })

    it('AC-4_sample_xMin_xMax_preserved', 3, (): void => {
      const s: PlotSeries = PlotUtils.sampleSeries('x', -10, 10, 11, linear)
      expect(s.xMin).assertEqual(-10)
      expect(s.xMax).assertEqual(10)
    })
  })

  describe('PlotUtils_mapToCanvas', () => {
    const bounds: PlotBounds = { width: 400, height: 300, paddingLeft: 40, paddingRight: 20, paddingTop: 20, paddingBottom: 30 }

    it('AC-5_map_origin_to_center', 0, (): void => {
      // xMin=-2, xMax=2, yMin=-1, yMax=1, point (0, 0)
      // innerW = 400 - 40 - 20 = 340, innerH = 300 - 20 - 30 = 250
      // px = 40 + ((0 - (-2)) / 4) * 340 = 40 + 0.5*340 = 40 + 170 = 210
      // py = 20 + (1 - (0 - (-1))/2) * 250 = 20 + 0.5*250 = 20 + 125 = 145
      const p: PlotPoint = { x: 0, y: 0 }
      const r = PlotUtils.mapToCanvas(p, bounds, -2, 2, -1, 1)
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.px).assertEqual(210)
        expect(r.py).assertEqual(145)
      }
    })

    it('AC-6_map_null_y_returns_null', 1, (): void => {
      const p: PlotPoint = { x: 0, y: null }
      const r = PlotUtils.mapToCanvas(p, bounds, -2, 2, -1, 1)
      expect(r === null).assertTrue()
    })

    it('AC-7_map_xMin_xMax_equal_returns_null', 2, (): void => {
      const p: PlotPoint = { x: 0, y: 0 }
      const r = PlotUtils.mapToCanvas(p, bounds, 1, 1, -1, 1)
      expect(r === null).assertTrue()
    })

    it('AC-8_map_corner_topleft', 3, (): void => {
      // point at (xMin, yMax) → paddingLeft, paddingTop
      const p: PlotPoint = { x: -2, y: 1 }
      const r = PlotUtils.mapToCanvas(p, bounds, -2, 2, -1, 1)
      expect(r !== null).assertTrue()
      if (r !== null) {
        expect(r.px).assertEqual(40)
        expect(r.py).assertEqual(20)
      }
    })
  })

  describe('PlotUtils_computeYRange', () => {
    it('AC-9_yRange_normal', 0, (): void => {
      const points: PlotPoint[] = [
        { x: 0, y: 0 },
        { x: 1, y: 1 },
        { x: 2, y: 2 }
      ]
      const r = PlotUtils.computeYRange(points)
      // 期望 yMin < 0, yMax > 2, 边距 10%
      expect(r.yMin < 0).assertTrue()
      expect(r.yMax > 2).assertTrue()
      expect(r.yMax - r.yMin).assertEqual(2.4)
    })

    it('AC-10_yRange_filters_null', 1, (): void => {
      const points: PlotPoint[] = [
        { x: 0, y: null },
        { x: 1, y: 5 },
        { x: 2, y: null }
      ]
      const r = PlotUtils.computeYRange(points)
      expect(r.yMin < 5).assertTrue()
      expect(r.yMax > 5).assertTrue()
    })

    it('AC-11_yRange_all_null_returns_default', 2, (): void => {
      const points: PlotPoint[] = [
        { x: 0, y: null },
        { x: 1, y: null }
      ]
      const r = PlotUtils.computeYRange(points)
      expect(r.yMin).assertEqual(-1)
      expect(r.yMax).assertEqual(1)
    })

    it('AC-12_yRange_clamps_to_1e10', 3, (): void => {
      const points: PlotPoint[] = [
        { x: 0, y: 1e20 },
        { x: 1, y: -1e20 }
      ]
      const r = PlotUtils.computeYRange(points)
      expect(r.yMax <= 1e10).assertTrue()
      expect(r.yMin >= -1e10).assertTrue()
    })

    it('AC-13_yRange_single_value_expands', 4, (): void => {
      const points: PlotPoint[] = [
        { x: 0, y: 5 },
        { x: 1, y: 5 }
      ]
      const r = PlotUtils.computeYRange(points)
      expect(r.yMin < 5).assertTrue()
      expect(r.yMax > 5).assertTrue()
    })
  })

  describe('PlotUtils_parseRange', () => {
    it('AC-14_parse_pi', 0, (): void => {
      const v = PlotUtils.parseRange('pi')
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v - Math.PI) < 1e-10).assertTrue()
    })

    it('AC-15_parse_2_times_pi', 1, (): void => {
      const v = PlotUtils.parseRange('2*pi')
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v - 2 * Math.PI) < 1e-10).assertTrue()
    })

    it('AC-16_parse_e', 2, (): void => {
      const v = PlotUtils.parseRange('e')
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v - Math.E) < 1e-10).assertTrue()
    })

    it('AC-17_parse_decimal', 3, (): void => {
      const v = PlotUtils.parseRange('1.5')
      expect(v).assertEqual(1.5)
    })

    it('AC-18_parse_negative', 4, (): void => {
      const v = PlotUtils.parseRange('-3')
      expect(v).assertEqual(-3)
    })

    it('AC-19_parse_invalid_returns_null', 5, (): void => {
      const v = PlotUtils.parseRange('abc')
      expect(v === null).assertTrue()
    })

    it('AC-20_parse_empty_returns_null', 6, (): void => {
      const v = PlotUtils.parseRange('')
      expect(v === null).assertTrue()
    })

    it('AC-21_parse_complex', 7, (): void => {
      const v = PlotUtils.parseRange('-2*pi+1')
      expect(v !== null).assertTrue()
      if (v !== null) expect(Math.abs(v - (-2 * Math.PI + 1)) < 1e-10).assertTrue()
    })
  })
}
