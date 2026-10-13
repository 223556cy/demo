// 完整移植 Calculator.ets 的 parseFactor 逻辑 (含 Math.sin)
'use strict'

class CalcEngine {
  constructor() {
    this.eq = ''
    this.p = -1
    this.c = 0
    this.deg = true  // Calculator.ets 默认 deg = true！
    this.xValue = 0
  }

  evaluate(equation, isDegree) {
    this.eq = equation; this.p = -1; this.c = 0; this.deg = isDegree
    this.nx(); return this.parseExpression()
  }

  evaluateAt(cleanExpr, x, isDegree) {
    this.xValue = x
    this.deg = isDegree
    try {
      const v = this.evaluate(cleanExpr, isDegree)
      if (!isFinite(v)) return null
      return v
    } catch { return null }
  }

  nx() { this.p++; this.c = this.p < this.eq.length ? this.eq.charCodeAt(this.p) : -1 }

  eat(ch) {
    while (this.c === 32) this.nx()
    if (this.c === ch) { this.nx(); return true }
    return false
  }

  parseExpression() {
    let x = this.parseTerm()
    while (true) {
      if (this.eat(43)) x = x + this.parseTerm()
      else if (this.eat(45)) x = x - this.parseTerm()
      else return x
    }
  }

  parseTerm() {
    let x = this.parseFactor()
    while (true) {
      if (this.eat(42)) x = x * this.parseFactor()
      else if (this.eat(35)) { let d = this.parseFactor(); x = d === 0 ? 0 : x % d }
      else if (this.eat(47)) { let d = this.parseFactor(); x = d === 0 ? 0 : x / d }
      else return x
    }
  }

  parseFactor() {
    if (this.eat(43)) return +this.parseFactor()
    if (this.eat(45)) return -this.parseFactor()
    if (this.c === 120) { this.nx(); return this.xValue }
    let x = 0; const sp = this.p
    if (this.eat(40)) { x = this.parseExpression(); if (!this.eat(41)) x = 0 }
    else if ((this.c >= 48 && this.c <= 57) || this.c === 46) {
      while ((this.c >= 48 && this.c <= 57) || this.c === 46) this.nx()
      x = parseFloat(this.eq.substring(sp, this.p))
    }
    else if (this.eat(101)) x = Math.E
    else if (this.eat(960)) x = Math.PI
    else if (this.c >= 97 && this.c <= 122) {
      while (this.c >= 97 && this.c <= 122) this.nx()
      const fn = this.eq.substring(sp, this.p)
      if (this.eat(40)) { x = this.parseExpression(); if (!this.eat(41)) x = this.parseFactor() }
      else x = this.parseFactor()
      if (fn === 'sin') x = Math.sin(this.deg ? x * Math.PI / 180 : x)
      else if (fn === 'cos') x = Math.cos(this.deg ? x * Math.PI / 180 : x)
      else if (fn === 'tan') x = Math.tan(this.deg ? x * Math.PI / 180 : x)
    }
    if (this.eat(94)) x = Math.pow(x, this.parseFactor())
    return x
  }
}

const e = new CalcEngine()
console.log('=== evaluateAt("sin(x)", x, false) 模拟 ===')
console.log('x      sin(x) result     expect Math.sin(x)')
for (const x of [-6.28, -3.14, -1.57, 0, 1.57, 3.14, 6.28]) {
  const v = e.evaluateAt('sin(x)', x, false)
  const expect = Math.sin(x)
  console.log(`  ${x.toFixed(2)}  ${(v ?? 'null').toString().padStart(10)}   ${expect.toFixed(6)}   ${v !== null && Math.abs(v - expect) < 1e-9 ? 'OK' : 'FAIL'}`)
}

console.log('\n=== evaluateAt("sin(x)", x, true) 模拟 (角度模式) ===')
for (const x of [-180, -90, 0, 90, 180]) {
  const v = e.evaluateAt('sin(x)', x, true)
  console.log(`  ${x.toString().padStart(4)}  ${v}`)
}