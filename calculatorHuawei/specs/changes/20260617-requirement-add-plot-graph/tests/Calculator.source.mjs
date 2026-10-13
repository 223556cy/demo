// Calculator.source.mjs — 共享源码(被其他 test 引用)
// Issue #26 函数图像

'use strict'

export class CalcParser {
  constructor (eq, xVal, deg) {
    this.eq = eq; this.p = 0; this.xVal = xVal; this.deg = deg
  }
  parse () {
    this.skipWs()
    const v = this.parseExpr()
    this.skipWs()
    if (this.p < this.eq.length) throw new Error('unparsed')
    return v
  }
  skipWs () {
    while (this.p < this.eq.length && (this.eq[this.p] === ' ' || this.eq[this.p] === '\t')) this.p++
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
        if ((c === '/' || c === '%') && r === 0) throw new Error('div by 0')
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
      if (this.p < this.eq.length && this.eq[this.p] === '^') {
        this.p++
        return Math.pow(v, this.parseFactor())
      }
      return v
    }
    if (c === 'x') {
      this.p++
      let v = this.xVal
      if (this.p < this.eq.length && this.eq[this.p] === '^') {
        this.p++
        v = Math.pow(v, this.parseFactor())
      }
      return v
    }
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
    if (c >= 'a' && c <= 'z') {
      const start = this.p
      while (this.p < this.eq.length && ((this.eq[this.p] >= 'a' && this.eq[this.p] <= 'z') || (this.eq[this.p] >= '0' && this.eq[this.p] <= '9'))) this.p++
      const fn = this.eq.substring(start, this.p)
      this.skipWs()
      if (this.p >= this.eq.length || this.eq[this.p] !== '(') throw new Error('expected (')
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

export class CalcEngine {
  constructor () { this.xValue = 0; this.deg = false }
  evaluate (equation, isDegree) {
    this.deg = isDegree
    const p = new CalcParser(equation, this.xValue, this.deg)
    return p.parse()
  }
  evaluateAt (cleanExpr, x, isDegree) {
    this.xValue = x; this.deg = isDegree
    try {
      const v = this.evaluate(cleanExpr, isDegree)
      if (!isFinite(v)) return null
      return v
    } catch { return null }
  }
}
