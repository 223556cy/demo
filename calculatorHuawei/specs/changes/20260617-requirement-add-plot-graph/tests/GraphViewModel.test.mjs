// GraphViewModel.test.mjs — Node 端 mock 测试
// Issue #26 函数图像 - GraphViewModel 集成测试
// 验证 compute() 流程: 校验 → 预处理 → 采样 → 错误处理

'use strict'

// 复用 PlotUtils
import { PlotUtils } from './PlotUtils.source.mjs'

// 简化的 CalcEngine
import { CalcEngine } from './Calculator.source.mjs'
const engine = new CalcEngine()

// 简化的 Expression (只实现 getCleanExpression 的核心)
class Expression {
  getCleanExpression (calculation, decSep, grpSep) {
    let c = calculation
    c = c.replace(/×/g, '*')
    c = c.replace(/÷/g, '/')
    return c
  }
}

// ==================== GraphViewModel ====================

class GraphViewModel {
  constructor () {
    this.expression = 'sin(x)'
    this.xMin = -2 * Math.PI
    this.xMax = 2 * Math.PI
    this.samples = 200
    this.series = null
    this.errorMessage = ''
    this.isComputing = false
    this.isDegree = false
  }

  setRadianMode (isDeg) { this.isDegree = isDeg }

  compute () {
    this.errorMessage = ''
    if (!this.validateInputs()) {
      this.series = null
      return
    }
    this.isComputing = true
    try {
      const expr = new Expression()
      const cleanExpr = expr.getCleanExpression(this.expression, '.', ',')
      const evaluator = (e, x) => engine.evaluateAt(e, x, this.isDegree)
      this.series = PlotUtils.sampleSeries(cleanExpr, this.xMin, this.xMax, this.samples, evaluator)
      if (this.series.points.every(p => p.y === null)) {
        this.errorMessage = '该函数在选定范围内无有效值'
      }
    } catch (e) {
      this.errorMessage = '计算异常: ' + (e.message || e)
      this.series = null
    } finally {
      this.isComputing = false
    }
  }

  validateInputs () {
    if (this.expression.trim().length === 0) {
      this.errorMessage = '请输入函数表达式'
      return false
    }
    if (!this.hasVariable(this.expression)) {
      this.errorMessage = '请输入含 x 的函数表达式,如 sin(x)'
      return false
    }
    if (!isFinite(this.xMin) || !isFinite(this.xMax)) {
      this.errorMessage = 'xMin / xMax 必须是有效数字'
      return false
    }
    if (this.xMax <= this.xMin) {
      this.errorMessage = 'xMax 必须大于 xMin'
      return false
    }
    if (this.samples < 50 || this.samples > 1000) {
      this.errorMessage = 'samples 需在 50 - 1000 之间'
      return false
    }
    return true
  }

  hasVariable (expr) {
    return /x/i.test(expr)
  }
}

// ==================== 测试 ====================

let passed = 0, failed = 0
const failures = []

function assertEq (l, a, e) { if (a === e) passed++; else { failed++; failures.push({ l, a, e }) } }
function assertTrue (l, a) { if (a) passed++; else { failed++; failures.push({ l, a, e: true }) } }
function assertClose (l, a, e, t = 1e-6) { if (Math.abs(a - e) < t) passed++; else { failed++; failures.push({ l, a, e }) } }

// AC-1: 默认值
{
  const vm = new GraphViewModel()
  assertEq('AC-1.1 default expression', vm.expression, 'sin(x)')
  assertTrue('AC-1.2 default xMin', Math.abs(vm.xMin - (-2 * Math.PI)) < 1e-10)
  assertTrue('AC-1.3 default xMax', Math.abs(vm.xMax - 2 * Math.PI) < 1e-10)
  assertEq('AC-1.4 default samples', vm.samples, 200)
}

// AC-2: 默认 sin(x) 计算成功
{
  const vm = new GraphViewModel()
  vm.compute()
  assertTrue('AC-2.1 no error', vm.errorMessage === '')
  assertTrue('AC-2.2 series exists', vm.series !== null)
  assertEq('AC-2.3 200 points', vm.series.points.length, 200)
  // sin(0) = 0
  assertTrue('AC-2.4 mid y ~ 0', Math.abs(vm.series.points[100].y) < 0.1)
}

// AC-3: x^2 计算
{
  const vm = new GraphViewModel()
  vm.expression = 'x^2'
  vm.compute()
  assertTrue('AC-3.1 no error', vm.errorMessage === '')
  assertTrue('AC-3.2 series exists', vm.series !== null)
  // x=0 → y=0
  assertTrue('AC-3.3 y(0) ~ 0', Math.abs(vm.series.points[100].y) < 0.1)
  // yMax 应该 > 1
  assertTrue('AC-3.4 yMax > 1', vm.series.yMax > 1)
}

// AC-4: 无 x 变量 → 错误
{
  const vm = new GraphViewModel()
  vm.expression = '1+2'
  vm.compute()
  assertTrue('AC-4.1 has error', vm.errorMessage.length > 0)
  assertTrue('AC-4.2 series null', vm.series === null)
}

// AC-5: xMax <= xMin → 错误
{
  const vm = new GraphViewModel()
  vm.xMax = -10
  vm.xMin = 5
  vm.compute()
  assertTrue('AC-5.1 has error', vm.errorMessage.length > 0)
  assertTrue('AC-5.2 message', vm.errorMessage.includes('xMax'))
}

// AC-6: 语法错误
{
  const vm = new GraphViewModel()
  vm.expression = 'sin(x'
  vm.compute()
  // 简化解析器: throw → '计算异常',但 PlotUtils.sampleSeries 不抛错
  // 真实 CalcEngine 会因为 syntax_error 返回 null → series 全 null → 错误
  assertTrue('AC-6.1 series or error', vm.series === null || vm.errorMessage.length > 0)
}

// AC-7: samples 越界
{
  const vm = new GraphViewModel()
  vm.samples = 10
  vm.compute()
  assertTrue('AC-7.1 has error', vm.errorMessage.length > 0)
}

// AC-8: 弧度模式 setRadianMode
{
  const vm = new GraphViewModel()
  vm.setRadianMode(true)  // 角度
  assertTrue('AC-8.1 isDegree=true', vm.isDegree === true)
  vm.setRadianMode(false)  // 弧度
  assertTrue('AC-8.2 isDegree=false', vm.isDegree === false)
}

// AC-9: sin(0)=0 验证精度
{
  const vm = new GraphViewModel()
  vm.expression = 'sin(x)'
  vm.xMin = -1
  vm.xMax = 1
  vm.samples = 200
  vm.compute()
  assertTrue('AC-9.1 no error', vm.errorMessage === '')
  assertTrue('AC-9.2 series exists', vm.series !== null)
  // 中间点附近 (x≈0.005) → sin ≈ 0.005,容差放宽
  assertTrue('AC-9.3 sin(0) ~ 0', Math.abs(vm.series.points[100].y) < 0.02)
}

console.log(`\n========== GraphViewModel Node Mock 测试 ==========`)
console.log(`PASS: ${passed}`)
console.log(`FAIL: ${failed}`)
if (failed > 0) {
  for (const f of failures) console.log(`  ${f.l}: expected ${f.e}, got ${f.a}`)
  process.exit(1)
} else {
  console.log(`\n所有测试通过 ✅`)
  process.exit(0)
}
