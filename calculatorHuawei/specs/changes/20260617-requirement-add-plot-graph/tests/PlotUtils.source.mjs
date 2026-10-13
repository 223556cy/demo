// PlotUtils.source.mjs — 共享源码(被其他 test 引用)
// Issue #26 函数图像

'use strict'

export class RangeParser {
  constructor (s) {
    this.s = s
    this.p = 0
    this.end = s.length
  }
  hasUnparsed () { return this.p < this.end }
  parse () {
    this.skipWs()
    const v = this.parseExpr()
    this.skipWs()
    return v
  }
  skipWs () {
    while (this.p < this.end && (this.s[this.p] === ' ' || this.s[this.p] === '\t')) this.p++
  }
  parseExpr () {
    let v = this.parseTerm()
    while (true) {
      this.skipWs()
      if (this.p >= this.end) break
      const c = this.s[this.p]
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
      if (this.p >= this.end) break
      const c = this.s[this.p]
      if (c === '*' || c === '/') {
        this.p++
        const r = this.parseFactor()
        if (c === '/' && r === 0) throw new Error('div by 0')
        v = c === '*' ? v * r : v / r
      } else break
    }
    return v
  }
  parseFactor () {
    this.skipWs()
    if (this.p >= this.end) throw new Error('eof')
    const c = this.s[this.p]
    if (c === '(') {
      this.p++
      const v = this.parseExpr()
      this.skipWs()
      if (this.p >= this.end || this.s[this.p] !== ')') throw new Error(') missing')
      this.p++
      return v
    }
    if (c === '+') { this.p++; return this.parseFactor() }
    if (c === '-') { this.p++; return -this.parseFactor() }
    if (c === 'p' && this.p + 1 < this.end && this.s[this.p + 1] === 'i') { this.p += 2; return Math.PI }
    if (c === 'e' && (this.p + 1 >= this.end || !this.isIdentChar(this.s[this.p + 1]))) { this.p++; return Math.E }
    if ((c >= '0' && c <= '9') || c === '.') {
      const start = this.p
      let dotSeen = c === '.'
      this.p++
      while (this.p < this.end) {
        const cc = this.s[this.p]
        if (cc >= '0' && cc <= '9') this.p++
        else if (cc === '.' && !dotSeen) { dotSeen = true; this.p++ }
        else break
      }
      const num = parseFloat(this.s.substring(start, this.p))
      if (!isFinite(num)) throw new Error('bad num')
      return num
    }
    throw new Error('bad char: ' + c)
  }
  isIdentChar (c) {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c === '_'
  }
}

export const PlotUtils = {
  Y_RANGE_CLAMP: 1e10,
  sampleSeries (expression, xMin, xMax, samples, evaluator) {
    if (samples < 2) samples = 2
    const points = new Array(samples)
    const step = (xMax - xMin) / (samples - 1)
    for (let i = 0; i < samples; i++) {
      const x = xMin + i * step
      const y = evaluator(expression, x)
      points[i] = { x, y }
    }
    const range = this.computeYRange(points)
    return { points, xMin, xMax, yMin: range.yMin, yMax: range.yMax }
  },
  mapToCanvas (p, bounds, xMin, xMax, yMin, yMax) {
    if (p.y === null) return null
    if (xMax === xMin || yMax === yMin) return null
    const innerW = bounds.width - bounds.paddingLeft - bounds.paddingRight
    const innerH = bounds.height - bounds.paddingTop - bounds.paddingBottom
    if (innerW <= 0 || innerH <= 0) return null
    const px = bounds.paddingLeft + ((p.x - xMin) / (xMax - xMin)) * innerW
    const py = bounds.paddingTop + (1 - (p.y - yMin) / (yMax - yMin)) * innerH
    return { px, py }
  },
  computeYRange (points) {
    let min = Infinity, max = -Infinity
    for (const p of points) {
      const y = p.y
      if (y === null) continue
      if (!isFinite(y)) continue
      if (y < min) min = y
      if (y > max) max = y
    }
    if (!isFinite(min) || !isFinite(max)) return { yMin: -1, yMax: 1 }
    if (min === max) { min = min - 1; max = max + 1 }
    const pad = (max - min) * 0.1
    let yMin = min - pad
    let yMax = max + pad
    if (yMin < -this.Y_RANGE_CLAMP) yMin = -this.Y_RANGE_CLAMP
    if (yMax > this.Y_RANGE_CLAMP) yMax = this.Y_RANGE_CLAMP
    return { yMin, yMax }
  },
  parseRange (input) {
    if (input === null || input === undefined) return null
    const s = input.trim()
    if (s.length === 0) return null
    const parser = new RangeParser(s)
    try {
      const v = parser.parse()
      if (parser.hasUnparsed()) return null
      if (typeof v !== 'number' || !isFinite(v)) return null
      return v
    } catch { return null }
  }
}
