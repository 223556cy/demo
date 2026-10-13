// PlotUtils.test.mjs — Node 端 mock 测试
// Issue #26 函数图像 - PlotUtils 纯函数测试
// ArkTS 端测试因 @ohos/hypium 无法解析而跑不通,使用 Node 端口验证逻辑
// 端口原则: 1:1 复刻 ArkTS 源码的逻辑,仅替换类型声明

'use strict'

// ==================== 复刻的 PlotUtils ====================
// (从 opencalc/entry/src/main/ets/common/PlotUtils.ets 移植)

class RangeParser {
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
    while (this.p < this.end && (this.s[this.p] === ' ' || this.s[this.p] === '\t')) {
      this.p++
    }
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
    if (c === 'p' && this.p + 1 < this.end && this.s[this.p + 1] === 'i') {
      this.p += 2; return Math.PI
    }
    if (c === 'e' && (this.p + 1 >= this.end || !this.isIdentChar(this.s[this.p + 1]))) {
      this.p++; return Math.E
    }
    if ((c >= '0' && c <= '9') || c === '.') {
      const start = this.p
      let dotSeen = c === '.'
      this.p++
      while (this.p < this.end) {
        const cc = this.s[this.p]
        if (cc >= '0' && cc <= '9') { this.p++ }
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

const PlotUtils = {
  Y_RANGE_CLAMP: 1e10,

  sampleSeries (expression, xMin, xMax, samples, evaluator) {
    if (samples < 2) samples = 2
    const points = new Array(samples)
    const step = (xMax - xMin) / (samples - 1)
    for (let i = 0; i < samples; i++) {
      const x = xMin + i * step
      let y = evaluator(expression, x)
      // 采样到极端值时强制 null (值式检测,不依赖具体函数)
      if (y !== null) {
        if (!isFinite(y) || Math.abs(y) > 1e6) y = null
      }
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
    // 收集 + 过滤极端值
    const ys = []
    for (const p of points) {
      const y = p.y
      if (y === null) continue
      if (!isFinite(y)) continue
      if (Math.abs(y) > 1e6) continue
      ys.push(y)
    }
    if (ys.length === 0) return { yMin: -1, yMax: 1 }
    ys.sort((a, b) => a - b)
    const lo = ys[Math.floor(ys.length * 0.02)]
    const hi = ys[Math.floor(ys.length * 0.98)]
    let lo2 = lo, hi2 = hi
    if (lo2 === hi2) { lo2 = lo2 - 1; hi2 = hi2 + 1 }
    const pad = (hi2 - lo2) * 0.1
    let yMin = lo2 - pad
    let yMax = hi2 + pad
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
    } catch {
      return null
    }
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

// ==================== sampleSeries ====================

{
  // AC-1: 5 点线性
  const linear = (e, x) => x
  const s = PlotUtils.sampleSeries('x', 0, 4, 5, linear)
  assertEq('AC-1.1 sample 5 points', s.points.length, 5)
  assertEq('AC-1.2 first x', s.points[0].x, 0)
  assertEq('AC-1.3 last x', s.points[4].x, 4)
  assertEq('AC-1.4 mid x', s.points[2].x, 2)
}

{
  // AC-2: 失败返回 null
  const nullEval = (e, x) => x < 0 ? null : x
  const s = PlotUtils.sampleSeries('x', -2, 2, 5, nullEval)
  assertEq('AC-2.1 length', s.points.length, 5)
  assertTrue('AC-2.2 first null', s.points[0].y === null)
  assertEq('AC-2.3 mid y=0', s.points[2].y, 0)
  assertEq('AC-2.4 last y=2', s.points[4].y, 2)
}

{
  // AC-3: samples=1 提升为 2
  const s = PlotUtils.sampleSeries('x', 0, 1, 1, (e, x) => x)
  assertTrue('AC-3 length >= 2', s.points.length >= 2)
}

{
  // AC-4: xMin/xMax 保留
  const s = PlotUtils.sampleSeries('x', -10, 10, 11, (e, x) => x)
  assertEq('AC-4 xMin preserved', s.xMin, -10)
  assertEq('AC-4 xMax preserved', s.xMax, 10)
}

// ==================== mapToCanvas ====================

{
  // AC-5: 原点 → 中心
  const bounds = { width: 400, height: 300, paddingLeft: 40, paddingRight: 20, paddingTop: 20, paddingBottom: 30 }
  const r = PlotUtils.mapToCanvas({ x: 0, y: 0 }, bounds, -2, 2, -1, 1)
  assertTrue('AC-5.1 not null', r !== null)
  assertEq('AC-5.2 px=210', r.px, 210)
  assertEq('AC-5.3 py=145', r.py, 145)
}

{
  // AC-6: y=null 返回 null
  const bounds = { width: 400, height: 300, paddingLeft: 40, paddingRight: 20, paddingTop: 20, paddingBottom: 30 }
  const r = PlotUtils.mapToCanvas({ x: 0, y: null }, bounds, -2, 2, -1, 1)
  assertTrue('AC-6 null', r === null)
}

{
  // AC-7: xMin===xMax 返回 null
  const bounds = { width: 400, height: 300, paddingLeft: 40, paddingRight: 20, paddingTop: 20, paddingBottom: 30 }
  const r = PlotUtils.mapToCanvas({ x: 0, y: 0 }, bounds, 1, 1, -1, 1)
  assertTrue('AC-7 null', r === null)
}

{
  // AC-8: 角点 (xMin, yMax) → (paddingLeft, paddingTop)
  const bounds = { width: 400, height: 300, paddingLeft: 40, paddingRight: 20, paddingTop: 20, paddingBottom: 30 }
  const r = PlotUtils.mapToCanvas({ x: -2, y: 1 }, bounds, -2, 2, -1, 1)
  assertEq('AC-8.1 px=40', r.px, 40)
  assertEq('AC-8.2 py=20', r.py, 20)
}

// ==================== computeYRange ====================

{
  const r = PlotUtils.computeYRange([{ x: 0, y: 0 }, { x: 1, y: 1 }, { x: 2, y: 2 }])
  assertTrue('AC-9.1 yMin<0', r.yMin < 0)
  assertTrue('AC-9.2 yMax>2', r.yMax > 2)
  assertClose('AC-9.3 range=2.4', r.yMax - r.yMin, 2.4)
}

{
  const r = PlotUtils.computeYRange([{ x: 0, y: null }, { x: 1, y: 5 }, { x: 2, y: null }])
  assertTrue('AC-10.1 yMin<5', r.yMin < 5)
  assertTrue('AC-10.2 yMax>5', r.yMax > 5)
}

{
  const r = PlotUtils.computeYRange([{ x: 0, y: null }, { x: 1, y: null }])
  assertEq('AC-11.1 yMin=-1', r.yMin, -1)
  assertEq('AC-11.2 yMax=1', r.yMax, 1)
}

{
  const r = PlotUtils.computeYRange([{ x: 0, y: 1e20 }, { x: 1, y: -1e20 }])
  assertTrue('AC-12.1 yMax<=1e10', r.yMax <= 1e10)
  assertTrue('AC-12.2 yMin>=-1e10', r.yMin >= -1e10)
}

{
  const r = PlotUtils.computeYRange([{ x: 0, y: 5 }, { x: 1, y: 5 }])
  assertTrue('AC-13.1 yMin<5', r.yMin < 5)
  assertTrue('AC-13.2 yMax>5', r.yMax > 5)
}

// ==================== parseRange ====================

{
  const v = PlotUtils.parseRange('pi')
  assertTrue('AC-14.1 not null', v !== null)
  assertClose('AC-14.2 ~π', v, Math.PI)
}

{
  const v = PlotUtils.parseRange('2*pi')
  assertTrue('AC-15.1 not null', v !== null)
  assertClose('AC-15.2 ~2π', v, 2 * Math.PI)
}

{
  const v = PlotUtils.parseRange('e')
  assertTrue('AC-16.1 not null', v !== null)
  assertClose('AC-16.2 ~e', v, Math.E)
}

{
  assertEq('AC-17 1.5', PlotUtils.parseRange('1.5'), 1.5)
  assertEq('AC-18 -3', PlotUtils.parseRange('-3'), -3)
  assertTrue('AC-19 abc null', PlotUtils.parseRange('abc') === null)
  assertTrue('AC-20 empty null', PlotUtils.parseRange('') === null)
}

{
  const v = PlotUtils.parseRange('-2*pi+1')
  assertTrue('AC-21.1 not null', v !== null)
  assertClose('AC-21.2 ~-2π+1', v, -2 * Math.PI + 1)
}

// ==================== 渐近线容忍 (issue #37 followup: tan 多周期) ====================

{
  // AC-22: tan(x) 在 [-2π, 2π] 多周期 Y 轴不被奇点污染
  const evalAt = (e, x) => {
    // 模拟真实数学引擎: 接近渐近线时返回 null
    // (真实实现可能返回非有限或大数,这里统一用 null 模拟)
    if (e === 'tan(x)') {
      const tanx = Math.tan(x)
      if (!isFinite(tanx) || Math.abs(tanx) > 5) return null
      return tanx
    }
    return null
  }
  const series = PlotUtils.sampleSeries('tan(x)', -2 * Math.PI, 2 * Math.PI, 200, evalAt)
  assertTrue('AC-22.1 yRange 是有界量级 (<1000)', Math.abs(series.yMax) < 1000 && Math.abs(series.yMin) < 1000)
  const nullCount = series.points.filter(p => p.y === null).length
  assertTrue('AC-22.2 至少 4 个 null 点 (4 个奇点附近)', nullCount >= 4)
  const normalPts = series.points.filter(p => p.y !== null)
  const allBounded = normalPts.every(p => Math.abs(p.y) < 10)
  assertTrue('AC-22.3 正常点的 y 在 [-10, 10] 区间', allBounded)
}

{
  // AC-23: sin/cos 不被回归 (issue #37 修复)
  const evalAt = (e, x) => {
    if (e === 'sin(x)') return Math.sin(x)
    if (e === 'cos(x)') return Math.cos(x)
    return null
  }
  const s1 = PlotUtils.sampleSeries('sin(x)', -2 * Math.PI, 2 * Math.PI, 200, evalAt)
  assertTrue('AC-23.1 sin yMax ≈ 1.1 (±0.1)', Math.abs(s1.yMax - 1.1) < 0.1)
  assertTrue('AC-23.2 sin yMin ≈ -1.1 (±0.1)', Math.abs(s1.yMin + 1.1) < 0.1)
  const s2 = PlotUtils.sampleSeries('cos(x)', -2 * Math.PI, 2 * Math.PI, 200, evalAt)
  assertTrue('AC-23.3 cos yMax ≈ 1.1 (±0.1)', Math.abs(s2.yMax - 1.1) < 0.1)
  assertTrue('AC-23.4 cos yMin ≈ -1.1 (±0.1)', Math.abs(s2.yMin + 1.1) < 0.1)
}

// ==================== 总结 ====================

console.log(`\n========== PlotUtils Node Mock 测试 ==========`)
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
