// Safe expression evaluator for Node test verification.
// Extends the original expression-eval.mjs (used in the percent-button change)
// to support trigonometric functions (sin/cos/tan) and other math primitives
// needed by the realtime-preview test cases.
//
// Usage:
//   import { safeEval } from './expression-eval.mjs'
//   safeEval('sin(0)', true)   // isDegree=true → 0
//   safeEval('1000+2000', true) // → 3000

function factorial(n) {
  if (n < 0) throw new Error('domain')
  if (n !== Math.floor(n)) throw new Error('domain')
  const T = [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800]
  if (n <= 10) return T[n]
  let r = 1
  for (let i = 2; i <= n; i++) r *= i
  return r
}

function safeEval(expr, isDegree = true) {
  let jsExpr = expr

  // 1. Evaluate factorial(N) calls first
  jsExpr = jsExpr.replace(/factorial\((\d+)\)/g, (_m, n) => String(factorial(parseInt(n, 10))))

  // 2. Trig: sin/cos/tan — apply degree→radian conversion when isDegree=true
  const conv = isDegree ? '*Math.PI/180' : ''
  jsExpr = jsExpr.replace(/\bsin\(([^()]*)\)/g, (_m, a) => `Math.sin((${a})${conv})`)
  jsExpr = jsExpr.replace(/\bcos\(([^()]*)\)/g, (_m, a) => `Math.cos((${a})${conv})`)
  jsExpr = jsExpr.replace(/\btan\(([^()]*)\)/g, (_m, a) => `Math.tan((${a})${conv})`)

  // 3. ln / log / logtwo / xp / sqrt
  jsExpr = jsExpr.replace(/\bln\(/g, 'Math.log(')
  jsExpr = jsExpr.replace(/\blog\(/g, 'Math.log10(')
  jsExpr = jsExpr.replace(/\blogtwo\(/g, 'Math.log2(')
  jsExpr = jsExpr.replace(/\bxp\(/g, 'Math.exp(')
  jsExpr = jsExpr.replace(/\bsqrt\(/g, 'Math.sqrt(')

  // 4. π → Math.PI
  jsExpr = jsExpr.replace(/π/g, 'Math.PI')

  // 5. Standalone e (not part of identifier) → Math.E
  jsExpr = jsExpr.replace(/(^|[^A-Za-z_0-9])e([^A-Za-z_0-9]|$)/g, '$1Math.E$2')

  // eslint-disable-next-line no-new-func
  return Function('"use strict"; return (' + jsExpr + ')')()
}

export { safeEval, factorial }
