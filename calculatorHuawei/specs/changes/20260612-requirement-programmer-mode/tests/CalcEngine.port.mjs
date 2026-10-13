// CalcEngine Node.js 端口 — 镜像 ArkTS 实现
// 验证位运算解析（& | ^ << >> ~）
// Iron rule 6: 代码与 ETS 源保持一致

/**
 * 模拟 CalcEngine 位运算解析
 * 与 ETS 源 Calculator.ets parseTerm/parseFactor 行为一致
 */
export class CalcEngine {
  constructor() {
    this.programmerMode = false
  }

  setProgrammerMode(on) { this.programmerMode = on }

  evaluate(eq) {
    this.eq = eq
    this.p = -1
    this.deg = false
    this._advance()
    return this._parseExpression()
  }

  _advance() {
    this.p++
    this.c = this.p < this.eq.length ? this.eq.charCodeAt(this.p) : -1
  }

  _eat(ch) {
    while (this.c === 32) this._advance()  // skip space
    if (this.c === ch) { this._advance(); return true }
    return false
  }

  _parseExpression() {
    let x = this._parseTerm()
    while (true) {
      if (this._eat(43)) x = x + this._parseTerm()
      else if (this._eat(45)) x = x - this._parseTerm()
      else return x
    }
  }

  _parseTerm() {
    let x = this._parseFactor()
    while (true) {
      if (this._eat(42)) x = x * this._parseFactor()
      else if (this._eat(35)) { const d = this._parseFactor(); x = d === 0 ? 0 : x % d }
      else if (this._eat(47)) { const d = this._parseFactor(); x = d === 0 ? 0 : x / d }
      // aid-workflow 20260612: 位运算
      else if (this.c === 38) {  // '&'
        this._advance()
        x = (x & this._parseFactor()) >>> 0
      } else if (this.c === 124) {  // '|'
        this._advance()
        x = (x | this._parseFactor()) >>> 0
      } else if (this.c === 60 && this.eq.charCodeAt(this.p + 1) === 60) {  // '<<'
        this._advance(); this._advance()
        const n = this._parseFactor()
        x = x * Math.pow(2, n)
      } else if (this.c === 62 && this.eq.charCodeAt(this.p + 1) === 62) {  // '>>'
        this._advance(); this._advance()
        const n = this._parseFactor()
        x = Math.floor(x / Math.pow(2, n))
      } else return x
    }
  }

  _parseFactor() {
    if (this._eat(43)) return +this._parseFactor()
    if (this._eat(45)) return -this._parseFactor()
    if (this.c === 126) {  // '~'
      this._advance()
      return (~this._parseFactor()) >>> 0
    }
    const sp = this.p
    let x = 0
    if (this._eat(40)) {
      x = this._parseExpression()
      if (!this._eat(41)) { return 0 }
    } else if ((this.c >= 48 && this.c <= 57) || this.c === 46) {
      while ((this.c >= 48 && this.c <= 57) || this.c === 46) this._advance()
      const ns = this.eq.substring(sp, this.p)
      x = parseFloat(ns)
    } else {
      return 0
    }
    // 幂运算或异或（aid-workflow 20260612）
    while (this.c === 32) this._advance()  // skip space
    if (this.c === 94) {
      this._advance()
      if (this.programmerMode) {
        x = (Math.trunc(x) ^ Math.trunc(this._parseFactor())) >>> 0
      } else {
        x = Math.pow(x, this._parseFactor())
      }
    }
    return x
  }
}
