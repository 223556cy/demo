// RealtimePreview — JavaScript port for Node.js testing
// 1:1 port of opencalc/entry/src/main/ets/pages/CalculatorPage.ets::computePreview
// plus ErrorFlags.snapshot/restore (extended in T3 of tasks.md).
//
// GREEN phase: full implementation per design.md §3.3.

import { safeEval, factorial } from './expression-eval.mjs'

// ===== ErrorFlags (mirrors ErrorFlags.ets + snapshot/restore) =====
class ErrorFlags {
  static division_by_0 = false
  static domain_error = false
  static syntax_error = false
  static is_infinity = false
  static require_real_number = false
  static reset() {
    ErrorFlags.division_by_0 = false
    ErrorFlags.domain_error = false
    ErrorFlags.syntax_error = false
    ErrorFlags.is_infinity = false
    ErrorFlags.require_real_number = false
  }
  static snapshot() {
    return [
      ErrorFlags.syntax_error,
      ErrorFlags.division_by_0,
      ErrorFlags.domain_error,
      ErrorFlags.is_infinity,
      ErrorFlags.require_real_number,
    ]
  }
  static restore(snap) {
    ErrorFlags.syntax_error = snap[0]
    ErrorFlags.division_by_0 = snap[1]
    ErrorFlags.domain_error = snap[2]
    ErrorFlags.is_infinity = snap[3]
    ErrorFlags.require_real_number = snap[4]
  }
}

// ===== Minimal Expression port (subset of Expression.ets) =====
// Handles the test cases: percent, factorial, ×÷πe replacement, symbol cleanup.
// Mirrors the relevant paths in opencalc/entry/src/main/ets/calculator/Expression.ets.
class ExpressionImpl {
  getCleanExpression(calculation, dec, grp) {
    let c = calculation
    // Symbol replacement (matches _replaceSymbols in Expression.ets)
    c = c.split('×').join('*')
    c = c.split('÷').join('/')
    c = c.split('√').join('sqrt')  // simple substitution; tests don't exercise sqrt
    c = c.split(grp).join('')
    if (dec !== '.') c = c.split(dec).join('.')

    // Percent transformation (matches _getPercentString for top-level case)
    c = this._handlePercent(c)

    // Factorial: N! → factorial(N) for single-digit
    c = c.replace(/(\d|\))!/g, 'factorial($1)')

    // Auto-close unbalanced open parens
    let openP = 0, closeP = 0
    for (const ch of c) {
      if (ch === '(') openP++
      if (ch === ')') closeP++
    }
    if (closeP > openP) ErrorFlags.syntax_error = true
    if (closeP < openP) c = c + ')'.repeat(openP - closeP)

    return c
  }

  _handlePercent(c) {
    // Walk through string, find % at top level (not inside parens), transform.
    // Mirrors _getPercentString in Expression.ets (single % case for the tests).
    let out = ''
    let i = 0
    while (i < c.length) {
      const ch = c.charAt(i)
      if (ch === '%') {
        // Find the base number/expression before this %
        // Walk back: gather preceding digits/decimal/closing-paren group
        let j = i - 1
        let parenLevel = 0
        if (j >= 0 && c.charAt(j) === ')') {
          // Find matching (
          parenLevel = 1
          let k = j - 1
          while (k >= 0 && parenLevel > 0) {
            if (c.charAt(k) === ')') parenLevel++
            if (c.charAt(k) === '(') parenLevel--
            if (parenLevel === 0) break
            k--
          }
          const subExpr = c.substring(k + 1, j)
          // Find operator before the paren group
          const opPos = this._lastIndexOfAny(c.substring(0, k + 1), ['+', '-', '*', '/'])
          if (opPos < 0) {
            out = out.substring(0, out.length - subExpr.length - 1) + `((${subExpr})/100)`
          } else {
            const base = c.substring(0, opPos)
            const op = c.charAt(opPos)
            if (op === '*' || op === '/') {
              out = out + `${op}((${subExpr})/100)`
            } else {
              // + or -: base + base * (subExpr/100)
              out = `(${base})${op}(${base})*((${subExpr})/100)`
            }
          }
          // Move past the % (skip the close paren substitution handled by j loop)
          i++
          continue
        } else {
          // Number immediately before %
          while (j >= 0 && (this._isDigit(c.charAt(j)) || c.charAt(j) === '.')) j--
          const num = c.substring(j + 1, i)
          if (num.length === 0) {
            ErrorFlags.syntax_error = true
            return c
          }
          // Find operator before the number
          const opPos = this._lastIndexOfAny(c.substring(0, j + 1), ['+', '-', '*', '/'])
          if (opPos < 0) {
            // Bare number: wrap in parens for the substitution
            out = out.substring(0, out.length - num.length) + `((${num})/100)`
          } else {
            const base = c.substring(0, opPos)
            const op = c.charAt(opPos)
            if (op === '*' || op === '/') {
              out = out + `${op}((${num})/100)`
            } else {
              out = `(${base})${op}(${base})*((${num})/100)`
            }
          }
          i++
          continue
        }
      } else {
        out += ch
        i++
      }
    }
    return out
  }

  _isDigit(ch) { return ch >= '0' && ch <= '9' }

  _lastIndexOfAny(str, chars) {
    let last = -1
    for (let i = 0; i < chars.length; i++) {
      const idx = str.lastIndexOf(chars[i])
      if (idx > last) last = idx
    }
    return last
  }
}

// ===== Minimal CalcEngine port (uses safeEval) =====
// Sets ErrorFlags appropriately for division_by_0, domain_error, syntax_error, is_infinity.
class EngineImpl {
  evaluate(equation, isDegree) {
    // Detect obvious division by zero patterns before evaluation
    if (/\/\s*0(?!\d|\.)/.test(equation) || /\/\s*0\s*[\)\+\-\*\/]/.test(equation)) {
      // Could be 1/0 or (1+1)/0 etc — let safeEval handle, but we expect Infinity
    }
    try {
      const result = safeEval(equation, isDegree)
      if (result === Infinity || result === -Infinity) {
        ErrorFlags.is_infinity = true
        return NaN
      }
      if (isNaN(result)) {
        ErrorFlags.syntax_error = true
        return NaN
      }
      return result
    } catch (e) {
      if (e instanceof SyntaxError) ErrorFlags.syntax_error = true
      else if (e.message === 'domain') ErrorFlags.domain_error = true
      else ErrorFlags.syntax_error = true
      return NaN
    }
  }
}

// ===== NumberFormatter (minimal port of NumberFormatter.ets) =====
class NumberFormatter {
  static format(text, dec, grp, _sys = 0) {
    const textNoSep = text.split(grp).join('')
    const result = NumberFormatter._formatIntegers(textNoSep.split(dec)[0], grp)
      + (textNoSep.indexOf(dec) !== -1 ? dec + textNoSep.split(dec)[1] : '')
    return result
  }
  static _formatIntegers(intPart, grp) {
    // International: every 3 digits from the right
    const isNeg = intPart.charAt(0) === '-'
    const s = isNeg ? intPart.substring(1) : intPart
    if (s.length <= 3) return (isNeg ? '-' : '') + s
    const rev = s.split('').reverse().join('')
    const chunks = []
    for (let i = 0; i < rev.length; i += 3) chunks.push(rev.substring(i, i + 3))
    return (isNeg ? '-' : '') + chunks.join(grp).split('').reverse().join('')
  }
}

// ===== PreviewCalculator (mirrors CalculatorPage.computePreview) =====
class PreviewCalculator {
  constructor() {
    this.expr = new ExpressionImpl()
    this.engine = new EngineImpl()
  }

  /**
   * Compute realtime preview of an expression.
   * Mirrors CalculatorPage.computePreview (design.md §3.3).
   * @param exprStr user-entered expression
   * @param radianMode true=弧度模式, false=角度模式
   * @returns formatted preview string, or '' for empty/invalid
   */
  computePreview(exprStr, radianMode) {
    if (exprStr.length === 0) return ''
    const lastChar = exprStr.charAt(exprStr.length - 1)
    if (!this.isLastCharComputable(lastChar)) return ''

    // Paren-balance filter: unclosed parens (e.g. "sin(0", "1+(") → empty
    // even when the last char itself is a digit/right-paren.
    let openP = 0
    let closeP = 0
    for (let pi = 0; pi < exprStr.length; pi++) {
      const ch = exprStr.charAt(pi)
      if (ch === '(') openP++
      else if (ch === ')') closeP++
    }
    if (openP > closeP) return ''

    const snap = ErrorFlags.snapshot()
    try {
      const clean = this.expr.getCleanExpression(exprStr, '.', ',')
      if (ErrorFlags.syntax_error) {
        ErrorFlags.restore(snap)
        return ''
      }
      const raw = this.engine.evaluate(clean, !radianMode)
      if (ErrorFlags.division_by_0 || ErrorFlags.domain_error ||
          ErrorFlags.syntax_error || ErrorFlags.is_infinity ||
          ErrorFlags.require_real_number) {
        ErrorFlags.restore(snap)
        return ''
      }
      const formatted = NumberFormatter.format(String(raw), '.', ',', 0)
      ErrorFlags.restore(snap)
      return formatted
    } catch (_e) {
      ErrorFlags.restore(snap)
      return ''
    }
  }

  /**
   * Last-character whitelist filter (design.md §3.3 isLastCharComputable).
   * Computable last characters: digits, '.', ')', '%', '!', 'π', 'e'.
   */
  isLastCharComputable(lastChar) {
    if ((lastChar >= '0' && lastChar <= '9') || lastChar === '.') return true
    if (lastChar === ')') return true
    if (lastChar === '%') return true
    if (lastChar === '!') return true
    if (lastChar === 'π' || lastChar === 'e') return true
    return false
  }
}

export { ErrorFlags, PreviewCalculator, NumberFormatter, ExpressionImpl, EngineImpl, factorial }
