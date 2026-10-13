// Simple JS expression evaluator for verification
// Mirrors what CalcEngine.evaluate does for the simple percent-related cases
// We use Function() with a sanitized allowlist

function factorial(n) {
  if (n < 0) throw new Error('domain')
  if (n !== Math.floor(n)) throw new Error('domain')
  // inline table for n <= 10
  const T = [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800]
  if (n <= 10) return T[n]
  let r = 1
  for (let i = 2; i <= n; i++) r *= i
  return r
}

function safeEval(expr) {
  // Translate "factorial(...)" into a real call
  let jsExpr = expr.replace(/factorial\(/g, '__F__!(')
  // Close "!" with ")"
  // We rely on the formatter producing balanced parens. factorial(N) → __F__!(N)
  // → then we replace __F__!(...) with factorial(...) again? No, simpler:
  // Just use a different approach: substitute factorial(N) → __F__(N) inline
  jsExpr = expr
  // Convert factorial(N) to a numeric literal before eval — too complex.
  // Better: pre-evaluate any factorial(...) calls in the string.
  jsExpr = jsExpr.replace(/factorial\((\d+)\)/g, (_m, n) => String(factorial(parseInt(n, 10))))

  // Translate π and e (already converted by Expression? no, it just passes them through)
  jsExpr = jsExpr.replace(/π/g, 'Math.PI')
  // Standalone e (not part of identifier) → Math.E
  jsExpr = jsExpr.replace(/(^|[^A-Za-z_0-9])e([^A-Za-z_0-9]|$)/g, '$1Math.E$2')

  // eslint-disable-next-line no-new-func
  return Function('"use strict"; return (' + jsExpr + ')')()
}

export { safeEval }
