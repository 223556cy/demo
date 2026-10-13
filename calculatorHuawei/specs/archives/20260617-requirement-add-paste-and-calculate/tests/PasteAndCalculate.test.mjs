// PasteAndCalculate.test.mjs — Node 端 mock 测试
// Issue #17 粘贴即计算 — Node 端口验证
// 模拟 CalculatorPage 的 onPaste 行为

'use strict'

// ==================== Mock 依赖 ====================

// Mock pasteboard
const mockPasteboard = {
  _data: null,
  _throwOnGet: false,
  setMockData: function (data) { this._data = data },
  setThrowOnGet: function (v) { this._throwOnGet = v },
  reset: function () { this._data = null; this._throwOnGet = false },
  getSystemPasteboard: function () {
    return {
      getData: () => {
        if (this._throwOnGet) throw new Error('mock getData error')
        return this._data
      }
    }
  }
}

// Mock promptAction
const mockPromptAction = {
  toasts: [],
  showToast: function (opts) { this.toasts.push(opts); return Promise.resolve() },
  reset: function () { this.toasts = [] }
}

// Mock Expression & CalcEngine (简化版)
const mockExpression = {
  getCleanExpression: function (str) { return str.replace(/×/g, '*').replace(/÷/g, '/') }
}

const mockCalcEngine = {
  evaluate: function (clean, radianMode) {
    // 简单求值（仅支持加减乘除和括号）
    try {
      // eslint-disable-next-line no-new-func
      const fn = new Function('"use strict"; return (' + clean + ')')
      return fn()
    } catch (e) {
      throw new Error('eval failed: ' + e.message)
    }
  }
}

const mockNumberFormatter = {
  format: function (raw) { return String(raw) }
}

// ==================== 复制的 CalculatorPage.onPaste 核心逻辑 ====================
// 这与 CalculatorPage.ets 中的 onPaste 行为一致（Node 端口）

class CalculatorPageMock {
  constructor () {
    this.expression = ''
    this.preview = ''
    this.result = ''
    this.errorMsg = ''
    this.history = []
    this.lastPastedHash = 0
    this.radianMode = false
    this._toastShown = []
  }

  isLastCharComputable (lastChar) {
    if ((lastChar >= '0' && lastChar <= '9') || lastChar === '.') return true
    if (lastChar === ')') return true
    if (lastChar === '%') return true
    return false
  }

  hasConsecutiveBinaryOperators (exprStr) {
    const binaryOps = '+-*/×÷%^#'
    for (let i = 1; i < exprStr.length; i++) {
      const prev = exprStr.charAt(i - 1)
      const curr = exprStr.charAt(i)
      if (binaryOps.indexOf(curr) === -1) continue
      if (prev === '(') continue
      if ((prev >= '0' && prev <= '9') || prev === '.' || prev === ')') continue
      if (binaryOps.indexOf(prev) !== -1) return true
    }
    return false
  }

  computePreview (exprStr) {
    if (exprStr.length === 0) return ''
    const lastChar = exprStr.charAt(exprStr.length - 1)
    if (!this.isLastCharComputable(lastChar)) return ''
    let openP = 0
    let closeP = 0
    for (let i = 0; i < exprStr.length; i++) {
      const c = exprStr.charAt(i)
      if (c === '(') openP++
      else if (c === ')') closeP++
    }
    if (openP > closeP) return ''
    if (this.hasConsecutiveBinaryOperators(exprStr)) return ''
    try {
      const clean = mockExpression.getCleanExpression(exprStr)
      const raw = mockCalcEngine.evaluate(clean, !this.radianMode)
      return mockNumberFormatter.format(raw)
    } catch (_e) {
      return ''
    }
  }

  computeHash (text) {
    let h = 0
    for (let i = 0; i < text.length; i++) {
      h = (h * 31 + text.charCodeAt(i)) | 0
    }
    return (h ^ text.length) | 0
  }

  onEquals () {
    if (this.expression.length === 0) return
    try {
      const clean = mockExpression.getCleanExpression(this.expression)
      const raw = mockCalcEngine.evaluate(clean, !this.radianMode)
      const fmt = mockNumberFormatter.format(raw)
      this.result = fmt
      this.errorMsg = ''
      this.history.unshift({ id: this.history.length, expression: this.expression, result: fmt, timestamp: Date.now() })
    } catch (e) {
      this.errorMsg = '计算错误: ' + e.message
    }
  }

  onPaste () {
    let text = ''
    try {
      const data = mockPasteboard.getSystemPasteboard().getData()
      if (data === null || data === undefined) return { action: 'noop' }
      const primary = (typeof data.getPrimaryText === 'function') ? data.getPrimaryText() : data.primaryText
      if (primary === null || primary === undefined) return { action: 'noop' }
      text = primary.trim()
    } catch (_e) {
      return { action: 'noop', reason: 'system_error' }
    }

    if (text.length === 0) return { action: 'noop', reason: 'empty' }

    if (text.length > 200) text = text.substring(0, 200).trim()
    if (text.length === 0) return { action: 'noop', reason: 'empty_after_trim' }

    const hash = this.computeHash(text)
    if (hash === this.lastPastedHash) return { action: 'noop', reason: 'duplicate' }

    if (this.computePreview(text).length === 0) {
      this._toastShown.push({ message: '非数学表达式', duration: 1500 })
      return { action: 'toast', reason: 'not_math' }
    }

    this.lastPastedHash = hash
    this.expression = text
    this.preview = this.computePreview(text)
    this.onEquals()
    return { action: 'paste', expression: this.expression, result: this.result }
  }
}

// ==================== 测试用例 ====================

const tests = []
let passed = 0
let failed = 0

function test (name, fn) {
  tests.push({ name, fn })
}

function assertEqual (actual, expected, msg) {
  if (actual !== expected) {
    throw new Error(`${msg || 'assertEqual'}  expected=${JSON.stringify(expected)}  actual=${JSON.stringify(actual)}`)
  }
}

function assert (cond, msg) {
  if (!cond) throw new Error(msg || 'assertion failed')
}

// Test 1: valid 2+3 → expression='2+3', result=5
test('paste_1_valid_2_plus_3', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setMockData({ getPrimaryText: () => '2+3' })
  const r = cp.onPaste()
  assertEqual(r.action, 'paste', 'should paste')
  assertEqual(cp.expression, '2+3', 'expression')
  assertEqual(cp.result, '5', 'result')
  assertEqual(cp.history.length, 1, 'history should have 1 item')
  assertEqual(cp.history[0].expression, '2+3', 'history.expression')
  assertEqual(cp.history[0].result, '5', 'history.result')
})

// Test 2: invalid text "Hello" → toast
test('paste_2_invalid_text_triggers_toast', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setMockData({ getPrimaryText: () => 'Hello World' })
  const r = cp.onPaste()
  assertEqual(r.action, 'toast', 'should toast')
  assertEqual(cp._toastShown.length, 1, 'toast should be shown once')
  assertEqual(cp._toastShown[0].message, '非数学表达式', 'toast message')
  assertEqual(cp.expression, '', 'expression unchanged')
  assertEqual(cp.history.length, 0, 'no history')
})

// Test 3: duplicate hash skips
test('paste_3_duplicate_hash_skips', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setMockData({ getPrimaryText: () => '2+3' })
  const r1 = cp.onPaste()
  assertEqual(r1.action, 'paste', 'first should paste')
  assertEqual(cp.history.length, 1, 'history 1')
  // 第二次粘贴相同内容
  mockPasteboard.setMockData({ getPrimaryText: () => '2+3' })
  const r2 = cp.onPaste()
  assertEqual(r2.action, 'noop', 'second should noop')
  assertEqual(r2.reason, 'duplicate', 'reason should be duplicate')
  assertEqual(cp.history.length, 1, 'history should still be 1')
})

// Test 4: empty/whitespace returns silently
test('paste_4_empty_returns_silently', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setMockData({ getPrimaryText: () => '   ' })
  const r = cp.onPaste()
  assertEqual(r.action, 'noop', 'should noop')
  assertEqual(r.reason, 'empty', 'reason should be empty')
  assertEqual(cp.expression, '', 'expression unchanged')
})

// Test 5: too long truncates to 200
test('paste_5_too_long_truncates_to_200', () => {
  const cp = new CalculatorPageMock()
  const longText = '1+' + '2'.repeat(300)  // 302 chars
  mockPasteboard.setMockData({ getPrimaryText: () => longText })
  const r = cp.onPaste()
  // 截断后是 '1+222...2'(200 chars)，末字符是 '2' 可计算
  assertEqual(r.action, 'paste', 'should paste after truncate')
  assert(cp.expression.length <= 200, 'expression should be truncated')
})

// Test 6: whitespace trimmed
test('paste_6_whitespace_trimmed', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setMockData({ getPrimaryText: () => '  3+4  ' })
  const r = cp.onPaste()
  assertEqual(r.action, 'paste', 'should paste')
  assertEqual(cp.expression, '3+4', 'expression should be trimmed')
  assertEqual(cp.result, '7', 'result')
})

// Test 7: system error in getData returns silently
test('paste_7_system_error_silent', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setThrowOnGet(true)
  const r = cp.onPaste()
  assertEqual(r.action, 'noop', 'should noop on system error')
  assertEqual(r.reason, 'system_error', 'reason should be system_error')
  assertEqual(cp.expression, '', 'expression unchanged')
})

// Test 8: data is null returns silently
test('paste_8_null_data_silent', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setMockData(null)
  const r = cp.onPaste()
  assertEqual(r.action, 'noop', 'should noop on null data')
})

// Test 9: different expression (not duplicate) overwrites old
test('paste_9_overwrites_previous_expression', () => {
  const cp = new CalculatorPageMock()
  mockPasteboard.setMockData({ getPrimaryText: () => '2+3' })
  cp.onPaste()
  assertEqual(cp.expression, '2+3', 'first paste')
  // 粘贴不同内容
  mockPasteboard.setMockData({ getPrimaryText: () => '5*6' })
  cp.onPaste()
  assertEqual(cp.expression, '5*6', 'should overwrite')
  assertEqual(cp.result, '30', 'result should be 30')
})

// Test 10: hash function correctness
test('hash_1_empty_string', () => {
  const cp = new CalculatorPageMock()
  const h = cp.computeHash('')
  assertEqual(h, 0, 'empty string hash should be 0')
})

test('hash_2_same_text_same_hash', () => {
  const cp = new CalculatorPageMock()
  const h1 = cp.computeHash('2+3')
  const h2 = cp.computeHash('2+3')
  assertEqual(h1, h2, 'same text should have same hash')
})

test('hash_3_different_text_different_hash', () => {
  const cp = new CalculatorPageMock()
  const h1 = cp.computeHash('2+3')
  const h2 = cp.computeHash('2+4')
  assert(h1 !== h2, 'different text should have different hash')
})

// ==================== 运行测试 ====================

console.log('============================================')
console.log('PasteAndCalculate.test.mjs — Node mock')
console.log('============================================\n')

for (const t of tests) {
  try {
    // 每个测试前重置 mock 状态
    mockPasteboard.reset()
    mockPromptAction.reset()
    t.fn()
    console.log(`✅ ${t.name}`)
    passed++
  } catch (e) {
    console.log(`❌ ${t.name}`)
    console.log(`   ${e.message}`)
    failed++
  }
}

console.log(`\n============================================`)
console.log(`Result: ${passed} PASS / ${failed} FAIL (${tests.length} total)`)
console.log(`============================================`)

process.exit(failed === 0 ? 0 : 1)
