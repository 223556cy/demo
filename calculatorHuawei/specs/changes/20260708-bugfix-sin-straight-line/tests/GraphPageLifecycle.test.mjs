// GraphPageLifecycle.test.mjs — Node 端 mock 测试
// Issue #37 — 验证 GraphPage.aboutToAppear() 中 vm.compute() 必须在 loadPrefs 后触发

'use strict'

import {
  MockPreferencesStore,
  MockGraphViewModel,
  MockGraphPageBuggy,
  MockGraphPageFixed
} from './GraphPageLifecycle.source.mjs'

let passCount = 0
let failCount = 0
const failures = []

function assert (cond, msg) {
  if (cond) {
    passCount++
    console.log('  PASS: ' + msg)
  } else {
    failCount++
    failures.push(msg)
    console.log('  FAIL: ' + msg)
  }
}

function header (title) {
  console.log('\n========== ' + title + ' ==========')
}

// ==================== Test 1: BUG 版本应触发竞态 ====================

header('Test 1: Buggy 版本 - compute 先于 loadPrefs 触发')

{
  const prefs = new MockPreferencesStore()
  const vm = new MockGraphViewModel()
  const page = new MockGraphPageBuggy(vm, prefs)

  page.aboutToAppear()
  await page.waitAll()

  console.log('  [info] compute eventId=' + vm.computeCallLog[0].eventId)
  console.log('  [info] loadPrefsStart=' + page._loadPrefsStartEventId)
  console.log('  [info] loadPrefsEnd=' + page._loadPrefsEndEventId)

  assert(vm.computeCallLog.length === 1, 'compute 被调用 1 次')

  // BUG 关键断言: compute eventId < loadPrefsStartEventId
  // setTimeout(0) 先于 prefs.init() (5ms) resolve
  assert(
    vm.computeCallLog[0].eventId < page._loadPrefsStartEventId,
    'BUG:compute eventId=' + vm.computeCallLog[0].eventId + ' < loadPrefsStart=' + page._loadPrefsStartEventId + ' (compute 先于 loadPrefs 触发)'
  )

  // BUG: sin 渲染为近似直线
  const samples = []
  for (let i = 0; i < 200; i++) {
    const x = -6.28 + (i / 199) * 12.56
    samples.push(vm.evaluateAt(x))
  }
  const yMin = Math.min(...samples)
  const yMax = Math.max(...samples)
  const yRange = yMax - yMin
  console.log('  [info] yRange=' + yRange.toFixed(3))

  assert(yRange < 0.5, 'BUG:sin yRange=' + yRange.toFixed(3) + ' < 0.5 (近似直线)')
}

// ==================== Test 2: Fixed 版本应避免竞态 ====================

header('Test 2: Fixed 版本 - compute 在 loadPrefs 完成后触发 + isDegree=false')

{
  const prefs = new MockPreferencesStore()
  const vm = new MockGraphViewModel()
  const page = new MockGraphPageFixed(vm, prefs)

  page.aboutToAppear()
  await page.waitAll()

  console.log('  [info] compute eventId=' + vm.computeCallLog[0].eventId)
  console.log('  [info] loadPrefsStart=' + page._loadPrefsStartEventId)
  console.log('  [info] loadPrefsEnd=' + page._loadPrefsEndEventId)
  console.log('  [info] isDegreeAtCall=' + vm.computeCallLog[0].isDegreeAtCall)

  assert(vm.computeCallLog.length === 1, 'compute 被调用 1 次')

  // FIXED 关键断言: compute eventId > loadPrefsEndEventId
  assert(
    vm.computeCallLog[0].eventId > page._loadPrefsEndEventId,
    'FIXED:compute eventId=' + vm.computeCallLog[0].eventId + ' > loadPrefsEnd=' + page._loadPrefsEndEventId + ' (compute 在 loadPrefs 完成后触发)'
  )

  // Task 5.3 扩展修复: compute 时 isDegree=false (rad 模式) 才能画正弦波
  assert(
    vm.computeCallLog[0].isDegreeAtCall === false,
    'FIXED:compute 时 isDegree=false (rad 模式,任务 5.3 扩展修复)'
  )

  // FIXED: sin 渲染为完整正弦波
  const samples = []
  for (let i = 0; i < 200; i++) {
    const x = -6.28 + (i / 199) * 12.56
    samples.push(vm.evaluateAt(x))
  }
  const yMin = Math.min(...samples)
  const yMax = Math.max(...samples)
  const yRange = yMax - yMin
  console.log('  [info] yRange=' + yRange.toFixed(3))
  assert(yRange > 1.5, 'FIXED:sin yRange=' + yRange.toFixed(3) + ' > 1.5 (完整正弦波,3 个波峰/波谷)')
}

// ==================== Test 3: 时序对比 ====================

header('Test 3: Buggy vs Fixed 时序差异')

{
  const prefs1 = new MockPreferencesStore()
  const vm1 = new MockGraphViewModel()
  const page1 = new MockGraphPageBuggy(vm1, prefs1)
  page1.aboutToAppear()
  await page1.waitAll()

  const prefs2 = new MockPreferencesStore()
  const vm2 = new MockGraphViewModel()
  const page2 = new MockGraphPageFixed(vm2, prefs2)
  page2.aboutToAppear()
  await page2.waitAll()

  const buggyOrder = vm1.computeCallLog[0].eventId < page1._loadPrefsStartEventId
  const fixedOrder = vm2.computeCallLog[0].eventId > page2._loadPrefsEndEventId

  assert(buggyOrder, 'Buggy:compute 先于 loadPrefs 触发')
  assert(fixedOrder, 'Fixed:compute 在 loadPrefs 完成后触发')
  assert(buggyOrder && fixedOrder, '时序差异明确:Buggy 错误,Fixed 正确')
}

// ==================== 汇总 ====================

console.log('\n========== 汇总 ==========')
console.log('PASS: ' + passCount)
console.log('FAIL: ' + failCount)

if (failCount > 0) {
  console.log('\n失败项:')
  failures.forEach(f => console.log('  - ' + f))
  process.exit(1)
}

console.log('\n所有测试通过')
process.exit(0)