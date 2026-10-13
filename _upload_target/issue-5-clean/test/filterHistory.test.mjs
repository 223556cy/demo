// filterHistory.test.mjs — 10 个单元测试覆盖 delta-spec §4.3.4 FM-002-01~04 + TM-002-01
// 运行：node --test test/filterHistory.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { filterHistory } from './filterHistory.mjs'

const mk = (id, expr, res) => ({ id, expression: expr, result: res, timestamp: id * 1000 })

// 4 条 fixture 历史，覆盖：含 sin 命中、含结果 120、纯数字算式
const FIX = [
  mk(1, 'sin(30)+5!', '6.5'),
  mk(2, '2+3', '5'),
  mk(3, '100/4', '25'),
  mk(4, 'log(100)', '120.5'),  // result 含 120
  mk(5, '5!', '120'),            // expression 与 result 都含 120
  mk(6, 'π*r^2', '314.159')      // 含特殊字符
]

test('T-01: "sin" 命中 expression="sin(30)+5!"', () => {
  const out = filterHistory(FIX, 'sin')
  assert.equal(out.length, 1)
  assert.equal(out[0].id, 1)
})

test('T-02: "120" 命中 result="120.5"', () => {
  const out = filterHistory(FIX, '120')
  // 命中 item 4 (log(100)=120.5) 与 item 5 (5!=120)
  const ids = out.map(i => i.id).sort()
  assert.deepEqual(ids, [4, 5])
})

test('T-03: "SIN" 大小写不敏感，与 "sin" 行为一致', () => {
  const lower = filterHistory(FIX, 'sin').map(i => i.id).sort()
  const upper = filterHistory(FIX, 'SIN').map(i => i.id).sort()
  const mixed = filterHistory(FIX, 'Sin').map(i => i.id).sort()
  assert.deepEqual(upper, lower)
  assert.deepEqual(mixed, lower)
})

test('T-04: "   " 纯空白 query → 返回全量', () => {
  const out = filterHistory(FIX, '   ')
  assert.equal(out.length, FIX.length)
})

test('T-05: "" 空 query → 返回全量', () => {
  const out = filterHistory(FIX, '')
  assert.equal(out.length, FIX.length)
})

test('T-06: "(30)" 正则元字符不抛错，正常命中', () => {
  // expression "sin(30)+5!" 包含 "(30)"
  const out = filterHistory(FIX, '(30)')
  assert.equal(out.length, 1)
  assert.equal(out[0].id, 1)
})

test('T-07: "*" / "?" 字面量匹配不抛错', () => {
  // fixture[5] = { expression: 'π*r^2', ... } 包含 "*"
  // 验证 "*" 命中该条（按字面量），且不抛错；"?" 无命中
  assert.doesNotThrow(() => filterHistory(FIX, '*'))
  assert.doesNotThrow(() => filterHistory(FIX, '?'))
  const star = filterHistory(FIX, '*')
  const ques = filterHistory(FIX, '?')
  assert.equal(star.length, 1)
  assert.equal(star[0].id, 6)
  assert.equal(ques.length, 0)
})

test('T-08: 300 字符 query 不抛错，按前 200 字符匹配', () => {
  // 用 300 个 "x"：FIX 中无任何项含 "x"，应返回 []
  // 但前 200 个字符会被截断用于匹配——验证不抛错
  const long = 'x'.repeat(300)
  assert.doesNotThrow(() => filterHistory(FIX, long))
  const out = filterHistory(FIX, long)
  assert.equal(out.length, 0)
})

test('T-09: "xyz123abc" 无命中 → 返回 []', () => {
  const out = filterHistory(FIX, 'xyz123abc')
  assert.equal(out.length, 0)
})

test('T-10: items=[] → 返回 []', () => {
  assert.equal(filterHistory([], 'sin').length, 0)
  assert.equal(filterHistory([], '').length, 0)
  assert.equal(filterHistory([], '   ').length, 0)
})
