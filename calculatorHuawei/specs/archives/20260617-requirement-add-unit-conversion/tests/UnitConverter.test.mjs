// specs/changes/20260617-requirement-add-unit-conversion/tests/UnitConverter.test.mjs
// aid-workflow 20260617: Issue #18 UnitConverter 单元测试(Node 端口)
// 使用 node:test 运行: `node --test UnitConverter.test.mjs`
// 容差:1e-4(浮点科学常量级)

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { UnitConverter } from './UnitConverter.port.mjs'

const EPS = 1e-4

function approxEqual(got, expected, eps = EPS) {
  if (Math.abs(got - expected) < eps) return true
  throw new Error(`approxEqual failed: got=${got}, expected=${expected}, diff=${Math.abs(got - expected)}`)
}

// ============== 长度 ==============
test('UC-L-01: 1m→cm = 100', () => {
  approxEqual(UnitConverter.convert(1, '米', '厘米'), 100)
})
test('UC-L-02: 100cm→m = 1', () => {
  approxEqual(UnitConverter.convert(100, '厘米', '米'), 1)
})
test('UC-L-03: 100cm→inch ≈ 39.3701', () => {
  approxEqual(UnitConverter.convert(100, '厘米', '英寸'), 39.3701)
})
test('UC-L-04: 1km→mi ≈ 0.621371', () => {
  approxEqual(UnitConverter.convert(1, '千米', '英里'), 0.621371)
})
test('UC-L-05: 1ft→m = 0.3048', () => {
  approxEqual(UnitConverter.convert(1, '英尺', '米'), 0.3048)
})
test('UC-L-06: 别名 m→cm 工作', () => {
  approxEqual(UnitConverter.convert(1, 'm', 'cm'), 100)
})
test('UC-L-07: 1mi→km = 1.609344', () => {
  approxEqual(UnitConverter.convert(1, '英里', '千米'), 1.609344)
})

// ============== 质量 ==============
test('UC-M-01: 1kg→g = 1000', () => {
  approxEqual(UnitConverter.convert(1, '千克', '克'), 1000)
})
test('UC-M-02: 1kg→lb ≈ 2.20462', () => {
  approxEqual(UnitConverter.convert(1, '千克', '磅'), 2.20462)
})
test('UC-M-03: 1oz→g ≈ 28.3495', () => {
  approxEqual(UnitConverter.convert(1, '盎司', '克'), 28.3495)
})

// ============== 时间 ==============
test('UC-T-01: 1h→s = 3600', () => {
  approxEqual(UnitConverter.convert(1, '小时', '秒'), 3600)
})
test('UC-T-02: 1day→h = 24', () => {
  approxEqual(UnitConverter.convert(1, '天', '小时'), 24)
})
test('UC-T-03: 60s→min = 1', () => {
  approxEqual(UnitConverter.convert(60, '秒', '分钟'), 1)
})

// ============== 温度 ==============
test('UC-TMP-01: 30C→F = 86', () => {
  approxEqual(UnitConverter.convert(30, '摄氏度', '华氏度'), 86)
})
test('UC-TMP-02: 32F→C = 0', () => {
  approxEqual(UnitConverter.convert(32, '华氏度', '摄氏度'), 0)
})
test('UC-TMP-03: 0C→K = 273.15', () => {
  approxEqual(UnitConverter.convert(0, '摄氏度', '开尔文'), 273.15)
})
test('UC-TMP-04: 273.15K→C = 0', () => {
  approxEqual(UnitConverter.convert(273.15, '开尔文', '摄氏度'), 0)
})
test('UC-TMP-05: 100C→F = 212', () => {
  approxEqual(UnitConverter.convert(100, '摄氏度', '华氏度'), 212)
})
test('UC-TMP-06: -40C→F = -40 (恒等式)', () => {
  approxEqual(UnitConverter.convert(-40, '摄氏度', '华氏度'), -40)
})

// ============== 错误处理 ==============
test('UC-ERR-01: 跨维度 米→千克 → NaN', () => {
  assert.ok(isNaN(UnitConverter.convert(1, '米', '千克')))
})
test('UC-ERR-02: 未知单位 米→xyz → NaN', () => {
  assert.ok(isNaN(UnitConverter.convert(1, '米', 'xyz')))
})
test('UC-ERR-03: 未知源单位 foo→米 → NaN', () => {
  assert.ok(isNaN(UnitConverter.convert(1, 'foo', '米')))
})
