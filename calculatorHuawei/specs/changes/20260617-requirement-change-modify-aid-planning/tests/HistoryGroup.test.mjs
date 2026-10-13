// HistoryGroup 单元测试 - Node.js 端口
// Issue #15 历史按日期分组 (今天/昨天/更早)
// 跑测: node HistoryGroup.test.mjs
// 期望: 全部 9 个用例通过

import {
  groupHistoryByDate,
  startOfLocalDay,
  HistoryGroupKey
} from './HistoryGroup.port.mjs'

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

function mkItem(id, timestamp, expr = '1+1', result = '2') {
  return { id, expression: expr, result, timestamp }
}

function msOf(year, month, day, hour = 12, minute = 0, second = 0) {
  return new Date(year, month - 1, day, hour, minute, second).getTime()
}

console.log('=== TC-01: empty items → 3 个空段 ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const sections = groupHistoryByDate([], now)
  eq(sections.length, 3, 'sections.length')
  eq(sections[0].key, HistoryGroupKey.TODAY, 'sections[0].key === TODAY')
  eq(sections[0].title, '今天', 'sections[0].title === 今天')
  eq(sections[0].items.length, 0, 'sections[0].items.length === 0')
  eq(sections[1].key, HistoryGroupKey.YESTERDAY, 'sections[1].key === YESTERDAY')
  eq(sections[1].title, '昨天', 'sections[1].title === 昨天')
  eq(sections[2].key, HistoryGroupKey.EARLIER, 'sections[2].key === EARLIER')
  eq(sections[2].title, '更早', 'sections[2].title === 更早')
}

console.log('\n=== TC-02: 全部今天 (3 条) → 仅今天段有数据 ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const items = [
    mkItem(1, msOf(2026, 6, 16, 9, 0, 0)),
    mkItem(2, msOf(2026, 6, 16, 8, 30, 0)),
    mkItem(3, msOf(2026, 6, 16, 0, 0, 1))
  ]
  const sections = groupHistoryByDate(items, now)
  eq(sections[0].items.length, 3, 'today.items.length')
  eq(sections[1].items.length, 0, 'yesterday.items.length')
  eq(sections[2].items.length, 0, 'earlier.items.length')
}

console.log('\n=== TC-03: 全部昨天 (2 条) → 仅昨天段有数据 ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const items = [
    mkItem(1, msOf(2026, 6, 15, 14, 0, 0)),
    mkItem(2, msOf(2026, 6, 15, 0, 0, 1))
  ]
  const sections = groupHistoryByDate(items, now)
  eq(sections[0].items.length, 0, 'today.items.length')
  eq(sections[1].items.length, 2, 'yesterday.items.length')
  eq(sections[2].items.length, 0, 'earlier.items.length')
}

console.log('\n=== TC-04: 全部更早 (5 条) → 仅更早段有数据 ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const items = [
    mkItem(1, msOf(2026, 6, 14, 12, 0, 0)),
    mkItem(2, msOf(2026, 6, 13, 9, 0, 0)),
    mkItem(3, msOf(2026, 6, 10, 14, 0, 0)),
    mkItem(4, msOf(2026, 5, 1, 8, 0, 0)),
    mkItem(5, msOf(2025, 12, 25, 18, 0, 0))
  ]
  const sections = groupHistoryByDate(items, now)
  eq(sections[0].items.length, 0, 'today.items.length')
  eq(sections[1].items.length, 0, 'yesterday.items.length')
  eq(sections[2].items.length, 5, 'earlier.items.length')
}

console.log('\n=== TC-05: 跨三天混合 → 三段均有数据 ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const items = [
    mkItem(1, msOf(2026, 6, 16, 9, 0, 0)),
    mkItem(2, msOf(2026, 6, 15, 14, 0, 0)),
    mkItem(3, msOf(2026, 6, 14, 8, 0, 0))
  ]
  const sections = groupHistoryByDate(items, now)
  eq(sections[0].items.length, 1, 'today.items.length')
  eq(sections[0].items[0].id, 1, 'today[0].id')
  eq(sections[1].items.length, 1, 'yesterday.items.length')
  eq(sections[1].items[0].id, 2, 'yesterday[0].id')
  eq(sections[2].items.length, 1, 'earlier.items.length')
  eq(sections[2].items[0].id, 3, 'earlier[0].id')
}

console.log('\n=== TC-06: 边界 00:00:00 → 跨日正确分组 ===')
{
  const now = msOf(2026, 6, 16, 12, 0, 0)
  const todayStart = msOf(2026, 6, 16, 0, 0, 0)
  const yesterdayEnd = msOf(2026, 6, 15, 23, 59, 59)
  const items = [
    mkItem(1, todayStart),
    mkItem(2, yesterdayEnd)
  ]
  const sections = groupHistoryByDate(items, now)
  eq(sections[0].items.length, 1, 'today.items.length')
  eq(sections[0].items[0].id, 1, 'today[0].id === 1 (todayStart 归今天)')
  eq(sections[1].items.length, 1, 'yesterday.items.length')
  eq(sections[1].items[0].id, 2, 'yesterday[0].id === 2 (yesterdayEnd 归昨天)')
  eq(sections[2].items.length, 0, 'earlier.items.length')
}

console.log('\n=== TC-07: 段内顺序保持 newest-first ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const items = [
    mkItem(1, msOf(2026, 6, 16, 9, 0, 0)),
    mkItem(2, msOf(2026, 6, 16, 8, 0, 0)),
    mkItem(3, msOf(2026, 6, 16, 11, 0, 0))
  ]
  const sections = groupHistoryByDate(items, now)
  eq(sections[0].items.length, 3, 'today.items.length')
  eq(sections[0].items[0].id, 1, 'today[0].id')
  eq(sections[0].items[1].id, 2, 'today[1].id')
  eq(sections[0].items[2].id, 3, 'today[2].id')
}

console.log('\n=== TC-08: items=null → 返回 3 段均空 (不抛异常) ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const sections = groupHistoryByDate(null, now)
  eq(sections.length, 3, 'sections.length')
  eq(sections[0].items.length, 0, 'today.items.length')
  eq(sections[1].items.length, 0, 'yesterday.items.length')
  eq(sections[2].items.length, 0, 'earlier.items.length')
}

console.log('\n=== TC-09: items=undefined → 返回 3 段均空 (不抛异常) ===')
{
  const now = msOf(2026, 6, 16, 10, 0, 0)
  const sections = groupHistoryByDate(undefined, now)
  eq(sections.length, 3, 'sections.length')
  eq(sections[0].items.length, 0, 'today.items.length')
  eq(sections[1].items.length, 0, 'yesterday.items.length')
  eq(sections[2].items.length, 0, 'earlier.items.length')
}

console.log('\n=== TC-10: startOfLocalDay 应返回当日 00:00:00.000 ===')
{
  const d = new Date(2026, 5, 16, 14, 30, 45)
  const start = startOfLocalDay(d)
  const expected = msOf(2026, 6, 16, 0, 0, 0)
  eq(start, expected, 'startOfLocalDay(2026-06-16 14:30:45)')
}

console.log(`\n=== Summary: ${passed} passed, ${failed} failed ===`)
if (failed > 0) {
  process.exit(1)
}
