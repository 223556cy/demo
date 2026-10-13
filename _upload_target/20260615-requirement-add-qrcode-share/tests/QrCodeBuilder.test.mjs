#!/usr/bin/env node
// OpenCalc — QrCodeBuilder Node 端口测试
// aid-workflow 20260615: Issue #13 一键分享二维码
// 真实跑测：本机无 hvigorw 时通过 Node 端口验证 buildSharePayload 逻辑
import {
  MAX_PAYLOAD_LENGTH,
  PAYLOAD_PREFIX,
  RESULT_PREFIX,
  TRUNCATED_FLAG,
  buildSharePayload,
  QrCodeBuilder
} from './QrCodeBuilder.source.mjs'

let passed = 0, failed = 0
const failures = []

function tc(id, name, fn) {
  try {
    fn()
    passed++
    console.log(`  ✅ ${id}: ${name}`)
  } catch (e) {
    failed++
    failures.push({ id, name, error: e.message })
    console.log(`  ❌ ${id}: ${name} — ${e.message}`)
  }
}

function assertEq(actual, expected) {
  if (actual !== expected) throw new Error(`expected "${expected}", got "${actual}"`)
}
function assertTrue(v, msg = 'assertTrue failed') {
  if (!v) throw new Error(msg)
}
function assertLE(actual, max, msg = '') {
  if (actual > max) throw new Error(`${msg || 'value'} ${actual} > ${max}`)
}
function assertContains(haystack, needle) {
  if (haystack.indexOf(needle) === -1) throw new Error(`"${haystack}" should contain "${needle}"`)
}

console.log('\n=== QrCodeBuilder.buildSharePayload 单元测试 ===\n')

// ── 基本格式 ──
tc('TC01', '1+2=3 → expr=1%2B2&res=3', () => {
  assertEq(buildSharePayload('1+2', '3'), 'opencalc://calc?expr=1%2B2&res=3')
})

tc('TC02', 'sin(π/2)=1 → 含 %CF%80 %2F (括号不被 encodeURIComponent 编码)', () => {
  const got = buildSharePayload('sin(π/2)', '1')
  assertTrue(got.indexOf('%CF%80') !== -1, `missing %CF%80 in ${got}`)
  assertTrue(got.indexOf('%2F') !== -1, `missing %2F in ${got}`)
  // ( 和 ) 在 encodeURIComponent 中是 unreserved/保留字符，不被编码
  assertTrue(got.indexOf('sin(') !== -1, `missing "sin(" in ${got}`)
  assertTrue(got.indexOf(')') !== -1, `missing ")" in ${got}`)
})

tc('TC03', '空字符串不抛异常', () => {
  assertEq(buildSharePayload('', ''), 'opencalc://calc?expr=&res=')
})

tc('TC04', '空格编码为 %20', () => {
  const got = buildSharePayload('1 + 2', '3')
  assertContains(got, '%20')
})

tc('TC05', '斜杠编码为 %2F', () => {
  const got = buildSharePayload('1/2', '0.5')
  assertContains(got, '%2F')
})

tc('TC06', '超长 expr 截断 + 追加 &truncated=1', () => {
  const longExpr = 'a'.repeat(250)
  const got = buildSharePayload(longExpr, '123')
  assertLE(got.length, MAX_PAYLOAD_LENGTH, 'payload length')
  assertContains(got, TRUNCATED_FLAG)
})

tc('TC07', '超长 res 截断整个 payload', () => {
  const longRes = 'b'.repeat(300)
  const got = buildSharePayload('1', longRes)
  assertLE(got.length, MAX_PAYLOAD_LENGTH, 'payload length')
})

tc('TC08', '^ 被编码为 %5E，- 不被编码', () => {
  // ^ 在 encodeURIComponent 中被编码为 %5E
  const got1 = buildSharePayload('2^10', '1024')
  assertTrue(got1.indexOf('2%5E10') !== -1, `^ should be encoded as %5E; got ${got1}`)
  // - 是 unreserved，不编码
  const got2 = buildSharePayload('-5', '-5')
  assertTrue(got2.indexOf('-5') !== -1, `- should NOT be encoded; got ${got2}`)
})

// ── 常量 ──
tc('TC09', 'MAX_PAYLOAD_LENGTH === 200', () => {
  assertEq(MAX_PAYLOAD_LENGTH, 200)
})

tc('TC10', '3 个字符串常量正确', () => {
  assertEq(PAYLOAD_PREFIX, 'opencalc://calc?expr=')
  assertEq(RESULT_PREFIX, '&res=')
  assertEq(TRUNCATED_FLAG, '&truncated=1')
})

tc('TC11', 'QrCodeBuilder 命名空间导出正确', () => {
  assertEq(QrCodeBuilder.MAX_PAYLOAD_LENGTH, 200)
  assertEq(QrCodeBuilder.buildSharePayload('1+2', '3'), 'opencalc://calc?expr=1%2B2&res=3')
})

// ── 额外：保留 result 完整的优先级 ──
tc('TC12', '超长时 result 字段保持完整', () => {
  const got = buildSharePayload('a'.repeat(50), 'XYZ_RESULT')
  assertContains(got, 'XYZ_RESULT')
})

console.log(`\n=== 测试汇总：${passed} passed, ${failed} failed ===\n`)

if (failed > 0) {
  console.log('失败用例：')
  for (const f of failures) console.log(`  - ${f.id}: ${f.name} — ${f.error}`)
  process.exit(1)
}
process.exit(0)
