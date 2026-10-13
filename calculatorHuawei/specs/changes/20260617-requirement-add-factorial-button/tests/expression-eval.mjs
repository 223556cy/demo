// Simple JS expression evaluator for verification
// Mirrors CalcEngine.evaluate for the percent+factorial cases
// Adapted from Issue #9 percent eval helper

function factorial(n) {
  if (n < 0) throw new Error('domain')
  if (n !== Math.floor(n)) throw new Error('domain')
  const T = [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800]
  if (n <= 10) return T[n]
  let r = 1
  for (let i = 2; i <= n; i++) r *= i
  return r
}

function safeEval(expr) {
  // Recursively pre-evaluate factorial(...) → numeric literal
  // Handle nested: factorial(factorial(3)+1) — resolve inner first
  let jsExpr = expr
  let prev = ''
  while (prev !== jsExpr) {
    prev = jsExpr
    jsExpr = jsExpr.replace(/factorial\(([^()]+)\)/g, (_m, inner) => {
      // First resolve any nested factorial in inner
      const resolved = inner.replace(/factorial\(([^()]+)\)/g, (__m, n) => String(factorial(parseFloat(n))))
      // Evaluate the inner (it's an arithmetic expr like "2+3" or "(2+3)")
      // eslint-disable-next-line no-new-func
      const v = Function('"use strict"; return (' + resolved + ')')()
      return String(factorial(v))
    })
  }
  jsExpr = jsExpr.replace(/π/g, 'Math.PI')
  jsExpr = jsExpr.replace(/(^|[^A-Za-z_0-9])e([^A-Za-z_0-9]|$)/g, '$1Math.E$2')
  // eslint-disable-next-line no-new-func
  return Function('"use strict"; return (' + jsExpr + ')')()
}

export { safeEval, factorial }
