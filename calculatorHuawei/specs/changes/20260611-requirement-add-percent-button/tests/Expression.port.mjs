// Expression.getCleanExpression — JavaScript port for Node.js testing
// 1:1 port of opencalc/entry/src/main/ets/calculator/Expression.ets (percent path focus)
// ArkTS 限制在 Node 下不影响（纯字符串/数组逻辑）

// ===== ErrorFlags =====
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
}

// ===== Expression =====
class Expression {
  getCleanExpression(calculation, decimalSeparatorSymbol, groupingSeparatorSymbol) {
    let cleanCalculation = this._replaceSymbols(calculation, decimalSeparatorSymbol, groupingSeparatorSymbol)
    cleanCalculation = this._addMultiply(cleanCalculation)
    if (cleanCalculation.indexOf('√') !== -1) {
      cleanCalculation = this._formatSquare(cleanCalculation)
    }
    if (cleanCalculation.indexOf('%') !== -1) {
      cleanCalculation = this._getPercentString(cleanCalculation)
      cleanCalculation = this._replaceAll(cleanCalculation, '%', '/100')
    }
    if (cleanCalculation.indexOf('!') !== -1) {
      cleanCalculation = this._formatFactorial(cleanCalculation)
    }
    cleanCalculation = this._addParenthesis(cleanCalculation)
    return cleanCalculation
  }

  _replaceSymbols(calc, decimalSep, groupingSep) {
    let c = calc
    c = this._replaceAll(c, '×', '*')
    c = this._replaceAll(c, '÷', '/')
    c = this._replaceAll(c, 'log₂(', 'logtwo(')
    c = this._replaceAll(c, 'log(', 'logten(')
    c = this._replaceAll(c, 'E', '*10^')
    c = this._replaceAll(c, 'exp', 'xp')
    c = this._replaceAll(c, 'cos⁻¹', 'arcco')
    c = this._replaceAll(c, 'sin⁻¹', 'arcsi')
    c = this._replaceAll(c, 'tan⁻¹', 'arcta')
    c = this._replaceAll(c, groupingSep, '')
    if (decimalSep !== '.') {
      c = this._replaceAll(c, decimalSep, '.')
    }
    return c
  }

  _addMultiply(calculation) {
    let c = calculation
    let i = 0
    while (i < c.length) {
      const ch = c.charAt(i)
      if (ch === '(') {
        if (i !== 0 && '.e0123456789)'.indexOf(c.charAt(i - 1)) !== -1) {
          c = this._insertChar(c, '*', i)
          i = i + 1
        }
      } else if (ch === ')') {
        if (i + 1 < c.length && '0123456789(.'.indexOf(c.charAt(i + 1)) !== -1) {
          c = this._insertChar(c, '*', i + 1)
          i = i + 1
        }
      } else if (ch === '!' || ch === '%') {
        if (i + 1 < c.length && '0123456789π('.indexOf(c.charAt(i + 1)) !== -1) {
          c = this._insertChar(c, '*', i + 1)
          i = i + 1
        }
      } else if (i >= 1 && ch === '√') {
        if ('+-/*('.indexOf(c.charAt(i - 1)) === -1) {
          c = this._insertChar(c, '*', i)
          i = i + 1
        }
      } else if (ch === 'π' || ch === 'e') {
        if (i + 1 < c.length && '0123456789π('.indexOf(c.charAt(i + 1)) !== -1) {
          c = this._insertChar(c, '*', i + 1)
          i = i + 1
        }
        if (i >= 1 && '.%πe0123456789)'.indexOf(c.charAt(i - 1)) !== -1) {
          c = this._insertChar(c, '*', i)
          i = i + 1
        }
      } else {
        if (i + 1 < c.length) {
          const functionsList = ['arcco', 'arcsi', 'arcta', 'cos', 'sin', 'tan', 'ln', 'log', 'xp']
          for (let fi = 0; fi < functionsList.length; fi++) {
            const func = functionsList[fi]
            const text = c.substring(0, i + 1)
            if (text.endsWith(func) && text.length !== func.length) {
              if ('+-/*(^'.indexOf(text.charAt(text.length - func.length - 1)) === -1) {
                const before = c.substring(0, i - func.length + 1)
                const after = c.substring(i + 1)
                c = before + '*' + func + after
                i = i + 1
                break
              }
            }
          }
        }
      }
      i = i + 1
    }
    return c
  }

  _formatSquare(calculation) {
    let c = calculation
    let parenthesisOpened = 0
    let i = 0
    while (i < c.length) {
      if (i < c.length - 1) {
        if (parenthesisOpened > 0) {
          if ('(*-/+^)'.indexOf(c.charAt(i + 1)) !== -1) {
            c = this._insertChar(c, ')', i + 1)
            parenthesisOpened = parenthesisOpened - 1
          }
        }
        if (c.charAt(i) === '√' && c.charAt(i + 1) !== '(') {
          c = this._insertChar(c, '(', i + 1)
          parenthesisOpened = parenthesisOpened + 1
        }
      }
      i = i + 1
    }
    return this._replaceAll(c, '√', 'sqrt')
  }

  _formatFactorial(calculation) {
    let i = calculation.length - 1
    if (i === 0) {
      ErrorFlags.syntax_error = true
      return ''
    }
    let c = calculation
    while (i > 0) {
      if (c.charAt(i) === '!') {
        if (c.charAt(i - 1) === ')') {
          c = c.substring(0, i) + c.substring(i + 1)
          let j = i
          let popped = 0
          while (j > 0) {
            if ('*/+^'.indexOf(c.charAt(j - 1)) !== -1 && popped === 0) break
            if (c.charAt(j - 1) === ')') popped = popped + 1
            else if (c.charAt(j - 1) === '(') popped = popped - 1
            if (c.charAt(j - 1) !== ')' && popped === 0) {
              c = this._insertChar(c, 'F', j - 1)
              break
            }
            j = j - 1
          }
        } else {
          c = c.substring(0, i) + ')' + c.substring(i + 1)
          const savedI = i
          let poppedParen = 0
          while (i > 0 && '()*-/+^'.indexOf(c.charAt(i - 1)) === -1) {
            if (c.charAt(i) === ')') poppedParen = poppedParen + 1
            else if (c.charAt(i) === '(') poppedParen = poppedParen - 1
            while (i > 1 && this._isDigit(c.charAt(i - 1)) && '()*-/+^'.indexOf(c.charAt(i - 2)) === -1) {
              i = i - 1
            }
            if (poppedParen === 1) {
              c = this._insertChar(c, '(', i - 1)
              c = this._insertChar(c, 'F', i - 1)
            }
            i = i - 1
          }
          i = savedI
        }
      }
      i = i - 1
    }
    return this._replaceAll(c, 'F', 'factorial')
  }

  _getPercentString(calculation) {
    let result = calculation
    let i = 0
    let parenthesisLevel = 0
    let subStart = -1
    const done = new Array(500).fill(false)

    while (i < result.length) {
      const ch = result.charAt(i)
      if (ch === '(') {
        if (parenthesisLevel === 0) { subStart = i }
        parenthesisLevel = parenthesisLevel + 1
      } else if (ch === ')') {
        parenthesisLevel = parenthesisLevel - 1
        if (parenthesisLevel === 0 && subStart >= 0) {
          const subExpr = result.substring(subStart + 1, i)
          if (subExpr.indexOf('%') !== -1) {
            const processed = this._getPercentString(subExpr)
            result = result.substring(0, subStart + 1) + processed + result.substring(i)
            i = 0
            for (let k = 0; k < 500; k++) { done[k] = false }
            continue
          }
          subStart = -1
        } else if (parenthesisLevel < 0) {
          ErrorFlags.syntax_error = true
          return result
        }
      } else if (ch === '%') {
        if (parenthesisLevel === 0 && !done[i]) {
          done[i] = true
          if (i > 0 && result.charAt(i - 1) === '!') {
            let j = i - 2
            while (j >= 0 && (this._isDigit(result.charAt(j)) || result.charAt(j) === '.')) { j = j - 1 }
            const factBase = result.substring(j + 1, i - 1)
            if (factBase.length === 0) { ErrorFlags.syntax_error = true; return result }
            result = result.substring(0, j + 1) + '((' + factBase + '!)/100)' + result.substring(i + 1)
          } else if (i > 0 && result.charAt(i - 1) === ')') {
            let j = i - 2
            let lvl = 1
            while (j >= 0) {
              if (result.charAt(j) === ')') lvl = lvl + 1
              else if (result.charAt(j) === '(') lvl = lvl - 1
              if (lvl === 0) break
              j = j - 1
            }
            if (lvl !== 0) { ErrorFlags.syntax_error = true; return result }
            const subExpr = result.substring(j + 1, i - 1)
            const opPos = this._lastIndexOfAny(result.substring(0, j), ['+', '-', '*', '/'])
            if (opPos < 0) {
              result = result.substring(0, j) + '((' + subExpr + ')/100)' + result.substring(i + 1)
            } else if (result.charAt(opPos) === '*' || result.charAt(opPos) === '/') {
              result = result.substring(0, opPos + 1) + '((' + subExpr + ')/100)' + result.substring(i + 1)
            } else {
              const base = result.substring(0, opPos).trim()
              // FIX (Issue #9): wrap base in parens to avoid operator-precedence bugs
              // when base itself is a complex expression like "100+100*(10/100)"
              // e.g. 100+10%+5%  →  before: "100+100*(10/100)+100+100*(10/100)*(5/100)" = 210.5
              //                    after:  "(100+100*(10/100))+(100+100*(10/100))*(5/100)" = 115.5
              result = '(' + base + ')' + result.charAt(opPos) + '(' + base + ')*(' + subExpr + '/100)' + result.substring(i + 1)
            }
          } else {
            let start = i - 1
            while (start >= 0 && (this._isDigit(result.charAt(start)) || result.charAt(start) === '.')) { start = start - 1 }
            const opPos = this._lastIndexOfAny(result.substring(0, start + 1), ['+', '-', '*', '/'])
            if (opPos < 0) {
              const num = result.substring(start + 1, i)
              if (num.length === 0) { ErrorFlags.syntax_error = true; return result }
              result = result.substring(0, start + 1) + '(' + num + '/100)' + result.substring(i + 1)
            } else if (result.charAt(opPos) === '*' || result.charAt(opPos) === '/') {
              const num = result.substring(opPos + 1, i)
              if (num.length === 0) { ErrorFlags.syntax_error = true; return result }
              result = result.substring(0, opPos + 1) + '(' + num + '/100)' + result.substring(i + 1)
            } else {
              const base = result.substring(0, opPos).trim()
              const num = result.substring(opPos + 1, i)
              // FIX (Issue #9): wrap base in parens for operator-precedence safety
              // when base is a complex expression
              result = '(' + base + ')' + result.charAt(opPos) + '(' + base + ')*(' + num + '/100)' + result.substring(i + 1)
            }
          }
          i = 0
          continue
        }
      }
      i = i + 1
    }
    return result
  }

  _addParenthesis(calculation) {
    let clean = calculation
    let openP = 0
    let closeP = 0
    for (let i = 0; i < calculation.length; i++) {
      if (calculation.charAt(i) === '(') openP = openP + 1
      if (calculation.charAt(i) === ')') closeP = closeP + 1
    }
    if (closeP < openP) {
      for (let i = 0; i < openP - closeP; i++) { clean = clean + ')' }
    }
    if (closeP > openP) { ErrorFlags.syntax_error = true }
    return clean
  }

  _insertChar(str, ch, idx) { return str.substring(0, idx) + ch + str.substring(idx) }

  _isDigit(ch) { return ch >= '0' && ch <= '9' }

  _replaceAll(str, from, to) {
    let result = str
    let idx = result.indexOf(from)
    while (idx !== -1) {
      result = result.substring(0, idx) + to + result.substring(idx + from.length)
      idx = result.indexOf(from, idx + to.length)
    }
    return result
  }

  _lastIndexOfAny(str, chars) {
    let last = -1
    for (let i = 0; i < chars.length; i++) {
      const idx = str.lastIndexOf(chars[i])
      if (idx > last) last = idx
    }
    return last
  }
}

export { ErrorFlags, Expression }
