// HistorySearch 单元测试 - Node.js 端口
// Issue #24 历史搜索框
// 跑测: node HistorySearch.test.mjs
// 期望: 全部 11 个用例通过

import { filterHistoryByQuery } from './HistorySearch.port.mjs'

let passed = 0
let failed = 0

function eq(actual, expected, msg) {
  if (actual === expected) {
    console.log(`  ✅ ${msg}: actual=${actual}`)
    passed++
  } else {
    console.log(`  ❌ ${msg}: expected ${expected}, got ${actual}`)
    failed++
  }
}

function truthy(val, msg) {
  if (val) {
    console.log(`  ✅ ${msg}`)
    passed++
  } else {
    console.log(`  ❌ ${msg}: got ${val}`)
    failed++
  }
}

function mkItem(id, expression, result, timestamp = 0) {
  return { id, expression, result, timestamp }
}

console.log('=== TC-01: 空 query → 返回原 items 引用 ===')
{
  const items = [mkItem(1, '1+1', '2'), mkItem(2, '2+2', '4')]
  const result = filterHistoryByQuery(items, '')
  eq(result === items, true, 'result 是 items 引用')
}

console.log('=== TC-01b: 全空格 query → trim 后视为空, 透传 ===')
{
  const items = [mkItem(1, '1+1', '2')]
  const result = filterHistoryByQuery(items, '   ')
  eq(result === items, true, '全空格视为空, 透传')
}

console.log('=== TC-02: query="12" → 匹配 expression 或 result 含 "12" ===')
{
  const items = [
    mkItem(1, '1+1', '2'),
    mkItem(2, '12+0', '12'),
    mkItem(3, '6*2', '12'),
    mkItem(4, '100-88', '12')
  ]
  const result = filterHistoryByQuery(items, '12')
  eq(result.length, 3, 'result.length')
  eq(result[0].id, 2, 'result[0].id')
  eq(result[1].id, 3, 'result[1].id')
  eq(result[2].id, 4, 'result[2].id')
}

console.log('=== TC-03: query="SIN" (大写) → 匹配 "sin" (大小写不敏感) ===')
{
  const items = [
    mkItem(1, 'sin(30)', '0.5'),
    mkItem(2, 'SIN(45)', '0.707'),
    mkItem(3, 'Sin(60)', '0.866'),
    mkItem(4, 'cos(30)', '0.866')
  ]
  const result = filterHistoryByQuery(items, 'SIN')
  eq(result.length, 3, 'result.length')
  eq(result[0].id, 1, 'lowercase sin matched')
  eq(result[1].id, 2, 'UPPERCASE SIN matched')
  eq(result[2].id, 3, 'Mixed Sin matched')
}

console.log('=== TC-04: query="xyz" (无匹配) → 返回 [] ===')
{
  const items = [mkItem(1, '1+1', '2'), mkItem(2, '2+2', '4')]
  const result = filterHistoryByQuery(items, 'xyz')
  eq(result.length, 0, 'result.length')
}

console.log('=== TC-05: 特殊字符 (π, e) → 正常匹配 ===')
{
  const items = [
    mkItem(1, 'π*2', '6.28'),
    mkItem(2, 'e^2', '7.39'),
    mkItem(3, '1+1', '2')
  ]
  const resultPi = filterHistoryByQuery(items, 'π')
  eq(resultPi.length, 1, 'π matches')
  eq(resultPi[0].id, 1, 'π matches id=1')

  const resultE = filterHistoryByQuery(items, 'e')
  eq(resultE.length, 1, 'e matches 1 item (e^2)')
}

console.log('=== TC-06: result 含数字/逗号 → 正常匹配 ===')
{
  const items = [
    mkItem(1, '1000+1000', '2,000'),
    mkItem(2, '500+500', '1,000')
  ]
  const result = filterHistoryByQuery(items, '2,000')
  eq(result.length, 1, 'comma number matched')
  eq(result[0].id, 1, 'id=1')
}

console.log('=== TC-07: null items → 返回 [] ===')
{
  const result = filterHistoryByQuery(null, 'test')
  eq(result.length, 0, 'null items → empty array')
}

console.log('=== TC-08: undefined items → 返回 [] ===')
{
  const result = filterHistoryByQuery(undefined, 'test')
  eq(result.length, 0, 'undefined items → empty array')
}

console.log('=== TC-09: 空数组 items → 返回 [] ===')
{
  const result = filterHistoryByQuery([], 'test')
  eq(result.length, 0, 'empty array → empty array')
}

console.log('=== TC-10: 子串匹配 (不要求整词) ===')
{
  const items = [
    mkItem(1, '123+456', '579'),
    mkItem(2, '7+8', '15')
  ]
  const result = filterHistoryByQuery(items, '23')
  eq(result.length, 1, 'substring 23 matched')
  eq(result[0].id, 1, 'id=1')
}

console.log('=== TC-11: 不修改入参 items ===')
{
  const items = [mkItem(1, '1+1', '2'), mkItem(2, '2+2', '4')]
  const originalLen = items.length
  filterHistoryByQuery(items, '1')
  eq(items.length, originalLen, 'items.length unchanged')
  eq(items[0].expression, '1+1', 'items[0].expression unchanged')
}

console.log(`\n=== Test Summary ===`)
console.log(`Passed: ${passed}`)
console.log(`Failed: ${failed}`)
console.log(`Total:  ${passed + failed}`)
process.exit(failed > 0 ? 1 : 0)
