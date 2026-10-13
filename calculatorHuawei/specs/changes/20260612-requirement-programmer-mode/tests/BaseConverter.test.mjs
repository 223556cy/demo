// BaseConverter 单元测试 — node:test 格式
// 对应 delta-design.md §11.2 测试用例
// Iron rule 7: 真实跑测试，不准伪造输出

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { BaseConverter, Base, BitWidth, Signedness } from './BaseConverter.port.mjs'

// ==================== toBase ====================

test('TC-001: toBase(0, DEC, 32, true) === "0"', () => {
  assert.equal(BaseConverter.toBase(0, Base.DEC, BitWidth.B32, true), '0')
})

test('TC-002: toBase(255, BIN, 8, false) === "0b11111111"', () => {
  assert.equal(BaseConverter.toBase(255, Base.BIN, BitWidth.B8, false), '0b11111111')
})

test('TC-003: toBase(255, HEX, 8, false) === "0xFF"', () => {
  assert.equal(BaseConverter.toBase(255, Base.HEX, BitWidth.B8, false), '0xFF')
})

test('TC-004: toBase(255, OCT, 8, false) === "0o377"', () => {
  assert.equal(BaseConverter.toBase(255, Base.OCT, BitWidth.B8, false), '0o377')
})

test('TC-005: toBase(256, BIN, 8, false) === "0b00000000"  // 截断', () => {
  assert.equal(BaseConverter.toBase(256, Base.BIN, BitWidth.B8, false), '0b00000000')
})

test('TC-006: toBase(-1, DEC, 8, false) === "255"  // unsigned', () => {
  assert.equal(BaseConverter.toBase(-1, Base.DEC, BitWidth.B8, false), '255')
})

test('TC-007: toBase(-1, DEC, 8, true) === "-1"  // signed', () => {
  assert.equal(BaseConverter.toBase(-1, Base.DEC, BitWidth.B8, true), '-1')
})

test('TC-008: toBase(255, DEC, 8, true) === "-1"  // signed 高位置 1', () => {
  assert.equal(BaseConverter.toBase(255, Base.DEC, BitWidth.B8, true), '-1')
})

test('TC-009: toBase(4096, HEX, 16, false) === "0x1000"', () => {
  assert.equal(BaseConverter.toBase(4096, Base.HEX, BitWidth.B16, false), '0x1000')
})

test('TC-010: toBase(8, BIN, 16, false) === "0b0000000000001000"  // 16 位补零', () => {
  assert.equal(BaseConverter.toBase(8, Base.BIN, BitWidth.B16, false), '0b0000000000001000')
})

test('TC-011: toBase(255, BIN, 32, false) === "0b00000000000000000000000011111111  // 32 位', () => {
  // JavaScript toString(2) on 255 = "11111111" (no padding); for 32-bit we need explicit padding
  const result = BaseConverter.toBase(255, Base.BIN, BitWidth.B32, false)
  assert.equal(result.length, 34) // "0b" + 32 chars
  assert.equal(result, '0b00000000000000000000000011111111')
})

// ==================== fromBase ====================

test('TC-020: fromBase("0xFF", HEX) === 255', () => {
  assert.equal(BaseConverter.fromBase('0xFF', Base.HEX), 255)
})

test('TC-021: fromBase("FF", HEX) === 255', () => {
  assert.equal(BaseConverter.fromBase('FF', Base.HEX), 255)
})

test('TC-022: fromBase("0b1010", BIN) === 10', () => {
  assert.equal(BaseConverter.fromBase('0b1010', Base.BIN), 10)
})

test('TC-023: fromBase("0o17", OCT) === 15', () => {
  assert.equal(BaseConverter.fromBase('0o17', Base.OCT), 15)
})

test('TC-024: fromBase("255", DEC) === 255', () => {
  assert.equal(BaseConverter.fromBase('255', Base.DEC), 255)
})

test('TC-025: fromBase("ff", HEX) === 255  // 小写', () => {
  assert.equal(BaseConverter.fromBase('ff', Base.HEX), 255)
})

// ==================== format4Bases ====================

test('TC-030: format4Bases(255, 8, false) === ["255","0b11111111","0o377","0xFF"]', () => {
  const arr = BaseConverter.format4Bases(255, BitWidth.B8, false)
  assert.deepEqual(arr, ['255', '0b11111111', '0o377', '0xFF'])
})

test('TC-031: format4Bases(-1, 8, true) === ["-1","0b11111111","0o377","0xFF"]', () => {
  const arr = BaseConverter.format4Bases(-1, BitWidth.B8, true)
  assert.deepEqual(arr, ['-1', '0b11111111', '0o377', '0xFF'])
})

test('TC-032: format4Bases(-1, 8, false) === ["255","0b11111111","0o377","0xFF"]', () => {
  const arr = BaseConverter.format4Bases(-1, BitWidth.B8, false)
  assert.deepEqual(arr, ['255', '0b11111111', '0o377', '0xFF'])
})

test('TC-033: format4Bases(0, 32, true) === ["0","0b0...","0o0","0x0"]', () => {
  const arr = BaseConverter.format4Bases(0, BitWidth.B32, true)
  // BIN 32 位补零；OCT/HEX/DEC 不补
  assert.equal(arr[0], '0')
  assert.equal(arr[1], '0b' + '0'.repeat(32))
  assert.equal(arr[2], '0o0')
  assert.equal(arr[3], '0x0')
})

// ==================== isValidCharForBase ====================

test('TC-040: isValidCharForBase("A", DEC) === false', () => {
  assert.equal(BaseConverter.isValidCharForBase('A', Base.DEC), false)
})

test('TC-041: isValidCharForBase("A", HEX) === true', () => {
  assert.equal(BaseConverter.isValidCharForBase('A', Base.HEX), true)
})

test('TC-042: isValidCharForBase("F", HEX) === true', () => {
  assert.equal(BaseConverter.isValidCharForBase('F', Base.HEX), true)
})

test('TC-043: isValidCharForBase("2", BIN) === false', () => {
  assert.equal(BaseConverter.isValidCharForBase('2', Base.BIN), false)
})

test('TC-044: isValidCharForBase("7", OCT) === true', () => {
  assert.equal(BaseConverter.isValidCharForBase('7', Base.OCT), true)
})

test('TC-045: isValidCharForBase("8", OCT) === false', () => {
  assert.equal(BaseConverter.isValidCharForBase('8', Base.OCT), false)
})

test('TC-046: isValidCharForBase("a", HEX) === true  // 小写字母也接受', () => {
  assert.equal(BaseConverter.isValidCharForBase('a', Base.HEX), true)
})

test('TC-047: isValidCharForBase("0", BIN) === true', () => {
  assert.equal(BaseConverter.isValidCharForBase('0', Base.BIN), true)
})

test('TC-048: isValidCharForBase("1", BIN) === true', () => {
  assert.equal(BaseConverter.isValidCharForBase('1', Base.BIN), true)
})

// ==================== 边界用例 ====================

test('TC-050: toBase(NaN, DEC, 32, true) 返回 "0" 或安全降级', () => {
  // NaN & mask = 0; 0.toString() = "0"
  const result = BaseConverter.toBase(NaN, Base.DEC, BitWidth.B32, true)
  assert.equal(result, '0')
})

test('TC-051: format4Bases(123, 16, false) 16 位显示', () => {
  const arr = BaseConverter.format4Bases(123, BitWidth.B16, false)
  assert.equal(arr[0], '123')
  assert.equal(arr[1], '0b' + '0'.repeat(9) + '1111011')  // 123 = 0b1111011
  assert.equal(arr[2], '0o173')  // OCT 不补零
  assert.equal(arr[3], '0x7B')   // HEX 不补零
})
