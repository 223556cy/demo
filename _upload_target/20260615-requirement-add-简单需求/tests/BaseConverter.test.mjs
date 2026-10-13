// BaseConverter 测试用例 — node:test 格式
// 对应 design.md §D11.1 单元测试矩阵
// TDD Iron Law: 先写失败测试，再写生产代码

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { BaseConverter, NumberBase } from './BaseConverter.port.mjs'

// ===== AC-1 ~ AC-4: 正整数多进制转换 =====
test('AC-1: 255 DEC', () => assert.equal(BaseConverter.convert(255, NumberBase.DEC), '255'))
test('AC-2: 255 BIN', () => assert.equal(BaseConverter.convert(255, NumberBase.BIN), '11111111'))
test('AC-3: 255 OCT', () => assert.equal(BaseConverter.convert(255, NumberBase.OCT), '377'))
test('AC-4: 255 HEX', () => assert.equal(BaseConverter.convert(255, NumberBase.HEX), 'FF'))

// ===== 负数 =====
test('AC-5: -1 BIN', () => assert.equal(BaseConverter.convert(-1, NumberBase.BIN), '-1'))
test('AC-6: -255 HEX', () => assert.equal(BaseConverter.convert(-255, NumberBase.HEX), '-FF'))

// ===== 零 =====
test('AC-7: 0 BIN', () => assert.equal(BaseConverter.convert(0, NumberBase.BIN), '0'))

// ===== 小数截断 =====
test('AC-8: 3.14 BIN', () => assert.equal(BaseConverter.convert(3.14, NumberBase.BIN), '11'))
test('AC-9: 3.99 OCT', () => assert.equal(BaseConverter.convert(3.99, NumberBase.OCT), '3'))

// ===== NaN / Infinity 防御 =====
test('AC-10: NaN BIN', () => assert.equal(BaseConverter.convert(NaN, NumberBase.BIN), '-'))
test('AC-11: Infinity HEX', () => assert.equal(BaseConverter.convert(Infinity, NumberBase.HEX), '-'))
test('AC-12: -Infinity BIN', () => assert.equal(BaseConverter.convert(-Infinity, NumberBase.BIN), '-'))

// ===== HEX 进位 =====
test('AC-13: 16 HEX', () => assert.equal(BaseConverter.convert(16, NumberBase.HEX), '10'))

// ===== DEC 保留小数 =====
test('AC-14: 3.14 DEC 保留小数', () => assert.equal(BaseConverter.convert(3.14, NumberBase.DEC), '3.14'))
test('AC-15: -255 DEC 负数', () => assert.equal(BaseConverter.convert(-255, NumberBase.DEC), '-255'))

// ===== withPrefix =====
test('WP-1: 255 HEX prefix', () => assert.equal(BaseConverter.withPrefix(255, NumberBase.HEX), '0xFF'))
test('WP-2: 255 OCT prefix', () => assert.equal(BaseConverter.withPrefix(255, NumberBase.OCT), '0o377'))
test('WP-3: 255 BIN prefix', () => assert.equal(BaseConverter.withPrefix(255, NumberBase.BIN), '0b11111111'))
test('WP-4: 255 DEC no prefix', () => assert.equal(BaseConverter.withPrefix(255, NumberBase.DEC), '255'))
test('WP-5: -1 BIN prefix', () => assert.equal(BaseConverter.withPrefix(-1, NumberBase.BIN), '-0b1'))
test('WP-6: -255 HEX prefix', () => assert.equal(BaseConverter.withPrefix(-255, NumberBase.HEX), '-0xFF'))
test('WP-7: 0 HEX prefix', () => assert.equal(BaseConverter.withPrefix(0, NumberBase.HEX), '0x0'))
test('WP-8: NaN BIN prefix', () => assert.equal(BaseConverter.withPrefix(NaN, NumberBase.BIN), '-'))

// ===== 边界值 =====
test('BC-1: MAX_SAFE_INTEGER BIN length 53', () => {
  const got = BaseConverter.convert(Number.MAX_SAFE_INTEGER, NumberBase.BIN)
  assert.equal(got.length, 53)
  assert.equal(got.indexOf('0'), -1)
})
test('BC-2: 1 BIN', () => assert.equal(BaseConverter.convert(1, NumberBase.BIN), '1'))
test('BC-3: -0 BIN as 0', () => assert.equal(BaseConverter.convert(-0, NumberBase.BIN), '0'))
test('BC-4: 4096 HEX', () => assert.equal(BaseConverter.convert(4096, NumberBase.HEX), '1000'))
test('BC-5: 266 HEX', () => assert.equal(BaseConverter.convert(266, NumberBase.HEX), '10A'))