// Calculator.test.mjs — Node 端 mock 测试
// Issue #26 函数图像 - CalcEngine.evaluateAt 测试
// 简化版:实现与 ArkTS 端 Calculator.ets 相同的 x 变量 + 单点求值逻辑

'use strict'

// ==================== Mock CalcEngine (简化) ====================
//
// 完整 CalcEngine 是 ~180 行的递归下降解析器,支持四则运算 + 数学函数 + 阶乘。
// 为测试 evaluateAt 重点,实现一个简化版,只支持:
// - 数字 (含小数点)
// - 变量 x
// - 四则运算 + - * / ^
// - 括号
// - 函数 sin/cos/tan/log/ln/sqrt
// - 错误通过返回 null 传递

class CalcEngine {
  constructor () {
    this.xValue = 0
    this.deg = false
  }

  evaluate (equation, isDegree) {
    this.deg = isDegree
    const p = new CalcParser(equation, this.xValue, this.deg)
    return p.parse()
  }

  evaluateAt (cleanExpr, x, isDegree) {
    this.xValue = x
    this.deg = isDegree
    try {
      const v = this.evaluate(cleanExpr, isDegree)
      if (!isFinite(v)) return null
      // 简化: 不查 ErrorFlags,只查 isFinite
      return v
    } catch {
      return null
    }
  }
}

class CalcParser {
  constructor (eq, xVal, deg) {
    this.eq = eq
    this.p = 0
    this.xVal = xVal
    this.deg = deg
  }

  parse () {
    this.skipWs()
    const v = this.parseExpr()
    this.skipWs()
    if (this.p < this.eq.length) throw new Error('unparsed chars')
    return v
  }

  skipWs () {
    while (this.p < this.eq.length && (this.eq[this.p] === ' ' || this.eq[this.p] === '\t')) {
      this.p++
    }
  }

  parseExpr () {
    let v = this.parseTerm()
    while (true) {
      this.skipWs()
      if (this.p >= this.eq.length) break
      const c = this.eq[this.p]
      if (c === '+' || c === '-') {
        this.p++
        const r = this.parseTerm()
        v = c === '+' ? v + r : v - r
      } else break
    }
    return v
  }

  parseTerm () {
    let v = this.parseFactor()
    while (true) {
      this.skipWs()
      if (this.p >= this.eq.length) break
      const c = this.eq[this.p]
      if (c === '*' || c === '/' || c === '%') {
        this.p++
        const r = this.parseFactor()
        if ((c === '/' || c === '%') && r === 0) {
          throw new Error('div by 0')
        }
        v = c === '*' ? v * r : c === '/' ? v / r : v % r
      } else break
    }
    return v
  }

  parseFactor () {
    this.skipWs()
    if (this.p >= this.eq.length) throw new Error('eof')
    const c = this.eq[this.p]
    if (c === '+') { this.p++; return this.parseFactor() }
    if (c === '-') { this.p++; return -this.parseFactor() }
    if (c === '(') {
      this.p++
      const v = this.parseExpr()
      this.skipWs()
      if (this.p >= this.eq.length || this.eq[this.p] !== ')') throw new Error(') missing')
      this.p++
      // 解析 ^ 优先级
      if (this.p < this.eq.length && this.eq[this.p] === '^') {
        this.p++
        return Math.pow(v, this.parseFactor())
      }
      return v
    }
    // 变量 x
    if (c === 'x') {
      this.p++
      let v = this.xVal
      // 解析 ^ 优先级
      if (this.p < this.eq.length && this.eq[this.p] === '^') {
        this.p++
        v = Math.pow(v, this.parseFactor())
      }
      return v
    }
    // 数字
    if ((c >= '0' && c <= '9') || c === '.') {
      const start = this.p
      let dotSeen = c === '.'
      this.p++
      while (this.p < this.eq.length) {
        const cc = this.eq[this.p]
        if (cc >= '0' && cc <= '9') this.p++
        else if (cc === '.' && !dotSeen) { dotSeen = true; this.p++ }
        else break
      }
      let v = parseFloat(this.eq.substring(start, this.p))
      if (!isFinite(v)) throw new Error('bad num')
      if (this.p < this.eq.length && this.eq[this.p] === '^') {
        this.p++
        v = Math.pow(v, this.parseFactor())
      }
      return v
    }
    // 函数
    if (c >= 'a' && c <= 'z') {
      const start = this.p
      while (this.p < this.eq.length && ((this.eq[this.p] >= 'a' && this.eq[this.p] <= 'z') || (this.eq[this.p] >= '0' && this.eq[this.p] <= '9'))) {
        this.p++
      }
      const fn = this.eq.substring(start, this.p)
      this.skipWs()
      if (this.p >= this.eq.length || this.eq[this.p] !== '(') {
        throw new Error('expected ( after ' + fn)
      }
      this.p++
      const arg = this.parseExpr()
      this.skipWs()
      if (this.p >= this.eq.length || this.eq[this.p] !== ')') throw new Error(') missing')
      this.p++
      let v
      switch (fn) {
        case 'sin': v = Math.sin(this.deg ? arg * Math.PI / 180 : arg); break
        case 'cos': v = Math.cos(this.deg ? arg * Math.PI / 180 : arg); break
        case 'tan': v = Math.tan(this.deg ? arg * Math.PI / 180 : arg); break
        case 'log': v = Math.log10(arg); break
        case 'ln': v = Math.log(arg); break
        case 'sqrt': v = Math.sqrt(arg); break
        case 'abs': v = Math.abs(arg); break
        default: throw new Error('unknown fn: ' + fn)
      }
      if (this.p < this.eq.length && this.eq[this.p] === '^') {
        this.p++
        v = Math.pow(v, this.parseFactor())
      }
      return v
    }
    throw new Error('bad char: ' + c)
  }
}

// ==================== 测试运行器 ====================

let passed = 0
let failed = 0
const failures = []

function assertEq (label, actual, expected) {
  if (actual === expected) {
    passed++
  } else {
    failed++
    failures.push({ label, actual, expected })
  }
}

function assertTrue (label, actual) {
  if (actual) {
    passed++
  } else {
    failed++
    failures.push({ label, actual, expected: true })
  }
}

function assertClose (label, actual, expected, tol = 1e-10) {
  if (Math.abs(actual - expected) < tol) {
    passed++
  } else {
    failed++
    failures.push({ label, actual, expected })
  }
}

// ==================== evaluateAt ====================

{
  const e = new CalcEngine()
  const v = e.evaluateAt('sin(x)', 0, false)
  assertTrue('AC-1.1 not null', v !== null)
  assertClose('AC-1.2 sin(0)=0', v, 0)
}

{
  const e = new CalcEngine()
  const v = e.evaluateAt('sin(x)', Math.PI, false)
  assertTrue('AC-2.1 not null', v !== null)
  assertClose('AC-2.2 sin(π)≈0', v, 0, 1e-10)
}

{
  const e = new CalcEngine()
  const v = e.evaluateAt('x^2', 3, false)
  assertEq('AC-3 x^2 at 3 = 9', v, 9)
}

{
  const e = new CalcEngine()
  // 简化解析器不支持隐式乘号,手动用乘法
  const v = e.evaluateAt('2*x', 3, false)
  assertEq('AC-4 2*x at 3 = 6', v, 6)
}

{
  const e = new CalcEngine()
  const v = e.evaluateAt('1/x', 0, false)
  assertTrue('AC-5 div by 0 returns null', v === null)
}

{
  const e = new CalcEngine()
  const v = e.evaluateAt('log(x)', -1, false)
  // 简化: log(-1) 返回 NaN,触发 !isFinite → null
  assertTrue('AC-6 log(-1) returns null', v === null)
}

{
  const e = new CalcEngine()
  const v = e.evaluateAt('sin(x', 0, false)
  assertTrue('AC-7 syntax error returns null', v === null)
}

{
  const e = new CalcEngine()
  const v = e.evaluateAt('cos(x)+sin(x)', 0, false)
  assertTrue('AC-8.1 not null', v !== null)
  assertClose('AC-8.2 cos(0)+sin(0)=1', v, 1, 1e-10)
}

{
  const e = new CalcEngine()
  // x*pi (用 Math.PI 代入)
  const v = e.evaluateAt('x*3.14159265', 1, false)
  assertTrue('AC-9 not null', v !== null)
  assertClose('AC-9 x*π', v, Math.PI, 1e-6)
}

// ==================== 总结 ====================

console.log(`\n========== Calculator.evaluateAt Node Mock 测试 ==========`)
console.log(`PASS: ${passed}`)
console.log(`FAIL: ${failed}`)
if (failed > 0) {
  console.log(`\n失败用例:`)
  for (const f of failures) {
    console.log(`  ${f.label}: expected ${f.expected}, got ${f.actual}`)
  }
  process.exit(1)
} else {
  console.log(`\n所有测试通过 ✅`)
  process.exit(0)
}
