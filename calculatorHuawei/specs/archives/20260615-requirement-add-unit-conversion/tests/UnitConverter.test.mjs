// specs/changes/20260615-requirement-add-unit-conversion/tests/UnitConverter.test.mjs
// aid-workflow 20260615: UnitConverter 单元测试
// TDD:RED 阶段期望 38/38 PASS(因 stub 已含完整实现)
// 容差:1e-6(科学常量级)

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { UnitConverter } from './UnitConverter.port.mjs'

const EPS = 1e-6

function approxEqual(got, expected, eps = EPS) {
  if (Math.abs(got - expected) < eps) return true
  throw new Error(`approxEqual failed: got=${got}, expected=${expected}, diff=${Math.abs(got - expected)}`)
}

test('UC-Length-01: 100cm → inch ≈ 39.3700787', () => {
  approxEqual(UnitConverter.convert(100, 'cm', 'inch', 'length'), 39.3700787)
})

test('UC-Length-02: 1km → mi ≈ 0.621371192', () => {
  approxEqual(UnitConverter.convert(1, 'km', 'mi', 'length'), 0.621371192)
})

test('UC-Length-03: 1mi → km = 1.609344', () => {
  approxEqual(UnitConverter.convert(1, 'mi', 'km', 'length'), 1.609344)
})

test('UC-Length-04: 1m → cm = 100', () => {
  approxEqual(UnitConverter.convert(1, 'm', 'cm', 'length'), 100)
})

test('UC-Length-05: 1m → mm = 1000', () => {
  approxEqual(UnitConverter.convert(1, 'm', 'mm', 'length'), 1000)
})

test('UC-Length-06: 1ft → m = 0.3048', () => {
  approxEqual(UnitConverter.convert(1, 'ft', 'm', 'length'), 0.3048)
})

test('UC-Length-07: 1yd → m = 0.9144', () => {
  approxEqual(UnitConverter.convert(1, 'yd', 'm', 'length'), 0.9144)
})

test('UC-Length-08: 1inch → mm = 25.4', () => {
  approxEqual(UnitConverter.convert(1, 'inch', 'mm', 'length'), 25.4)
})

test('UC-Length-09: 0m → cm = 0', () => {
  approxEqual(UnitConverter.convert(0, 'm', 'cm', 'length'), 0)
})

test('UC-Length-10: 1m → m = 1 (自转换)', () => {
  approxEqual(UnitConverter.convert(1, 'm', 'm', 'length'), 1)
})

test('UC-Length-11: 1mi → ft = 5280', () => {
  approxEqual(UnitConverter.convert(1, 'mi', 'ft', 'length'), 5280)
})

test('UC-Length-12: 1000mm → m = 1', () => {
  approxEqual(UnitConverter.convert(1000, 'mm', 'm', 'length'), 1)
})

test('UC-Temp-01: 0°C → K = 273.15', () => {
  approxEqual(UnitConverter.convert(0, 'C', 'K', 'temperature'), 273.15)
})

test('UC-Temp-02: 0°C → °F = 32', () => {
  approxEqual(UnitConverter.convert(0, 'C', 'F', 'temperature'), 32)
})

test('UC-Temp-03: 100°C → °F = 212', () => {
  approxEqual(UnitConverter.convert(100, 'C', 'F', 'temperature'), 212)
})

test('UC-Temp-04: 32°F → °C = 0', () => {
  approxEqual(UnitConverter.convert(32, 'F', 'C', 'temperature'), 0)
})

test('UC-Temp-05: 100°F → °C ≈ 37.7777777', () => {
  approxEqual(UnitConverter.convert(100, 'F', 'C', 'temperature'), 37.77777777777778)
})

test('UC-Temp-06: 273.15K → °C = 0', () => {
  approxEqual(UnitConverter.convert(273.15, 'K', 'C', 'temperature'), 0)
})

test('UC-Temp-07: -40°C → °F = -40 (恒等式)', () => {
  approxEqual(UnitConverter.convert(-40, 'C', 'F', 'temperature'), -40)
})

test('UC-Temp-08: 0K → °C = -273.15 (绝对零度)', () => {
  approxEqual(UnitConverter.convert(0, 'K', 'C', 'temperature'), -273.15)
})

test('UC-Mass-01: 1kg → g = 1000', () => {
  approxEqual(UnitConverter.convert(1, 'kg', 'g', 'mass'), 1000)
})

test('UC-Mass-02: 1lb → kg ≈ 0.45359237', () => {
  approxEqual(UnitConverter.convert(1, 'lb', 'kg', 'mass'), 0.45359237)
})

test('UC-Mass-03: 5lb → kg ≈ 2.26796185', () => {
  approxEqual(UnitConverter.convert(5, 'lb', 'kg', 'mass'), 2.26796185)
})

test('UC-Mass-04: 16oz → lb = 1', () => {
  approxEqual(UnitConverter.convert(16, 'oz', 'lb', 'mass'), 1)
})

test('UC-Mass-05: 1kg → oz ≈ 35.27396', () => {
  approxEqual(UnitConverter.convert(1, 'kg', 'oz', 'mass'), 35.27396194958, 1e-4)
})

test('UC-Mass-06: 1kg → kg = 1 (自转换)', () => {
  approxEqual(UnitConverter.convert(1, 'kg', 'kg', 'mass'), 1)
})

test('UC-Mass-07: 1000g → kg = 1', () => {
  approxEqual(UnitConverter.convert(1000, 'g', 'kg', 'mass'), 1)
})

test('UC-Vol-01: 1L → mL = 1000', () => {
  approxEqual(UnitConverter.convert(1, 'L', 'mL', 'volume'), 1000)
})

test('UC-Vol-02: 1gal → L ≈ 3.785411784', () => {
  approxEqual(UnitConverter.convert(1, 'gal', 'L', 'volume'), 3.785411784)
})

test('UC-Vol-03: 128fl_oz → gal = 1', () => {
  approxEqual(UnitConverter.convert(128, 'fl_oz', 'gal', 'volume'), 1)
})

test('UC-Vol-04: 1000mL → L = 1', () => {
  approxEqual(UnitConverter.convert(1000, 'mL', 'L', 'volume'), 1)
})

test('UC-Vol-05: 1L → fl_oz ≈ 33.814', () => {
  approxEqual(UnitConverter.convert(1, 'L', 'fl_oz', 'volume'), 33.814022701, 1e-4)
})

test('UC-Vol-06: 1L → L = 1 (自转换)', () => {
  approxEqual(UnitConverter.convert(1, 'L', 'L', 'volume'), 1)
})

test('UC-ERR-01: 1m → kg → null (跨类)', () => {
  assert.equal(UnitConverter.convert(1, 'm', 'kg', 'length'), null)
})

test('UC-ERR-02: 1C → cm → null (跨类)', () => {
  assert.equal(UnitConverter.convert(1, 'C', 'cm', 'temperature'), null)
})

test('UC-ERR-03: 1m → xyz → null (单位未注册)', () => {
  assert.equal(UnitConverter.convert(1, 'm', 'xyz', 'length'), null)
})

test('UC-ERR-04: 1xyz → m → null (单位未注册)', () => {
  assert.equal(UnitConverter.convert(1, 'xyz', 'm', 'length'), null)
})

test('UC-ERR-05: convert(1, "m", "kg", "invalid") → null (类别无效)', () => {
  assert.equal(UnitConverter.convert(1, 'm', 'kg', 'invalid'), null)
})
