// OpenCalc — Expression Preprocessor (ArkTS-safe version)
// Ported from: Expression.kt

import { ErrorFlags } from '../model/ErrorFlags'

export class Expression {

  getCleanExpression(calculation: string, decimalSeparatorSymbol: string, groupingSeparatorSymbol: string): string {
    // aid-workflow 20260612: 重复 %% 错误检测（边缘场景，SR-08）
    if (calculation.indexOf('%%') !== -1) {
      ErrorFlags.syntax_error = true
      return calculation
    }
    let cleanCalculation: string = this.replaceSymbols(calculation, decimalSeparatorSymbol, groupingSeparatorSymbol)
    cleanCalculation = this.addMultiply(cleanCalculation)
    if (cleanCalculation.indexOf('√') !== -1) {
      cleanCalculation = this.formatSquare(cleanCalculation)
    }
    if (cleanCalculation.indexOf('%') !== -1) {
      cleanCalculation = this.getPercentString(cleanCalculation)
      cleanCalculation = this.replaceAll(cleanCalculation, '%', '/100')
    }
    if (cleanCalculation.indexOf('!') !== -1) {
      cleanCalculation = this.formatFactorial(cleanCalculation)
    }
    cleanCalculation = this.addParenthesis(cleanCalculation)
    return cleanCalculation
  }

  private replaceSymbols(calculation: string, decimalSeparatorSymbol: string, groupingSeparatorSymbol: string): string {
    let calc: string = calculation
    calc = this.replaceAll(calc, '×', '*')
    calc = this.replaceAll(calc, '÷', '/')
    calc = this.replaceAll(calc, 'log₂(', 'logtwo(')
    calc = this.replaceAll(calc, 'log(', 'logten(')
    calc = this.replaceAll(calc, 'E', '*10^')
    calc = this.replaceAll(calc, 'exp', 'xp')
    calc = this.replaceAll(calc, 'cos⁻¹', 'arcco')
    calc = this.replaceAll(calc, 'sin⁻¹', 'arcsi')
    calc = this.replaceAll(calc, 'tan⁻¹', 'arcta')
    calc = this.replaceAll(calc, groupingSeparatorSymbol, '')
    if (decimalSeparatorSymbol !== '.') {
      calc = this.replaceAll(calc, decimalSeparatorSymbol, '.')
    }
    return calc
  }

  private addMultiply(calculation: string): string {
    let cleanCalculation: string = calculation
    let i: number = 0
    while (i < cleanCalculation.length) {
      const ch: string = cleanCalculation.charAt(i)
      if (ch === '(') {
        if (i !== 0 && '.e0123456789)'.indexOf(cleanCalculation.charAt(i - 1)) !== -1) {
          cleanCalculation = this.insertChar(cleanCalculation, '*', i)
          i = i + 1
        }
      } else if (ch === ')') {
        if (i + 1 < cleanCalculation.length && '0123456789(.'.indexOf(cleanCalculation.charAt(i + 1)) !== -1) {
          cleanCalculation = this.insertChar(cleanCalculation, '*', i + 1)
          i = i + 1
        }
      } else if (ch === '!' || ch === '%') {
        if (i + 1 < cleanCalculation.length && '0123456789π('.indexOf(cleanCalculation.charAt(i + 1)) !== -1) {
          cleanCalculation = this.insertChar(cleanCalculation, '*', i + 1)
          i = i + 1
        }
      } else if (i >= 1 && ch === '√') {
        if ('+-/*('.indexOf(cleanCalculation.charAt(i - 1)) === -1) {
          cleanCalculation = this.insertChar(cleanCalculation, '*', i)
          i = i + 1
        }
      } else if (ch === 'π' || ch === 'e') {
        if (i + 1 < cleanCalculation.length && '0123456789π('.indexOf(cleanCalculation.charAt(i + 1)) !== -1) {
          cleanCalculation = this.insertChar(cleanCalculation, '*', i + 1)
          i = i + 1
        }
        if (i >= 1 && '.%πe0123456789)'.indexOf(cleanCalculation.charAt(i - 1)) !== -1) {
          cleanCalculation = this.insertChar(cleanCalculation, '*', i)
          i = i + 1
        }
      } else {
        if (i + 1 < cleanCalculation.length) {
          const functionsList: string[] = ['arcco', 'arcsi', 'arcta', 'cos', 'sin', 'tan', 'ln', 'log', 'xp']
          for (let fi: number = 0; fi < functionsList.length; fi++) {
            const func: string = functionsList[fi]
            const text: string = cleanCalculation.substring(0, i + 1)
            if (text.endsWith(func) && text.length !== func.length) {
              if ('+-/*(^'.indexOf(text.charAt(text.length - func.length - 1)) === -1) {
                const before: string = cleanCalculation.substring(0, i - func.length + 1)
                const after: string = cleanCalculation.substring(i + 1)
                cleanCalculation = before + '*' + func + after
                i = i + 1
                break
              }
            }
          }
        }
      }
      i = i + 1
    }
    return cleanCalculation
  }

  private formatSquare(calculation: string): string {
    let cleanCalculation: string = calculation
    let parenthesisOpened: number = 0
    let i: number = 0
    while (i < cleanCalculation.length) {
      if (i < cleanCalculation.length - 1) {
        if (parenthesisOpened > 0) {
          if ('(*-/+^)'.indexOf(cleanCalculation.charAt(i + 1)) !== -1) {
            cleanCalculation = this.insertChar(cleanCalculation, ')', i + 1)
            parenthesisOpened = parenthesisOpened - 1
          }
        }
        if (cleanCalculation.charAt(i) === '√' && cleanCalculation.charAt(i + 1) !== '(') {
          cleanCalculation = this.insertChar(cleanCalculation, '(', i + 1)
          parenthesisOpened = parenthesisOpened + 1
        }
      }
      i = i + 1
    }
    return this.replaceAll(cleanCalculation, '√', 'sqrt')
  }

  private formatFactorial(calculation: string): string {
    let i: number = calculation.length - 1
    if (i === 0) {
      ErrorFlags.syntax_error = true
      return ''
    }
    let cleanCalculation: string = calculation
    while (i > 0) {
      if (cleanCalculation.charAt(i) === '!') {
        if (cleanCalculation.charAt(i - 1) === ')') {
          cleanCalculation = cleanCalculation.substring(0, i) + cleanCalculation.substring(i + 1)
          let j: number = i
          let popped: number = 0
          while (j > 0) {
            if ('*/+^'.indexOf(cleanCalculation.charAt(j - 1)) !== -1 && popped === 0) break
            if (cleanCalculation.charAt(j - 1) === ')') popped = popped + 1
            else if (cleanCalculation.charAt(j - 1) === '(') popped = popped - 1
            if (cleanCalculation.charAt(j - 1) !== ')' && popped === 0) {
              cleanCalculation = this.insertChar(cleanCalculation, 'F', j - 1)
              break
            }
            j = j - 1
          }
        } else {
          cleanCalculation = cleanCalculation.substring(0, i) + ')' + cleanCalculation.substring(i + 1)
          const savedI: number = i
          let poppedParen: number = 0
          while (i > 0 && '()*-/+^'.indexOf(cleanCalculation.charAt(i - 1)) === -1) {
            if (cleanCalculation.charAt(i) === ')') poppedParen = poppedParen + 1
            else if (cleanCalculation.charAt(i) === '(') poppedParen = poppedParen - 1
            while (i > 1 && this.isDigit(cleanCalculation.charAt(i - 1)) && '()*-/+^'.indexOf(cleanCalculation.charAt(i - 2)) === -1) {
              i = i - 1
            }
            if (poppedParen === 1) {
              cleanCalculation = this.insertChar(cleanCalculation, '(', i - 1)
              cleanCalculation = this.insertChar(cleanCalculation, 'F', i - 1)
            }
            i = i - 1
          }
          i = savedI
        }
      }
      i = i - 1
    }
    return this.replaceAll(cleanCalculation, 'F', 'factorial')
  }

  private getPercentString(calculation: string): string {
    let result: string = calculation
    let i: number = 0
    let parenthesisLevel: number = 0
    let subStart: number = -1
    const done: boolean[] = []
    for (let k: number = 0; k < 500; k++) { done[k] = false }

    while (i < result.length) {
      const ch: string = result.charAt(i)
      if (ch === '(') {
        if (parenthesisLevel === 0) { subStart = i }
        parenthesisLevel = parenthesisLevel + 1
      } else if (ch === ')') {
        parenthesisLevel = parenthesisLevel - 1
        if (parenthesisLevel === 0 && subStart >= 0) {
          const subExpr: string = result.substring(subStart + 1, i)
          if (subExpr.indexOf('%') !== -1) {
            const processed: string = this.getPercentString(subExpr)
            result = result.substring(0, subStart + 1) + processed + result.substring(i)
            i = 0
            for (let k: number = 0; k < 500; k++) { done[k] = false }
            continue
          }
          subStart = -1
        } else if (parenthesisLevel < 0) {
          ErrorFlags.syntax_error = true
          return result
        }
      } else if (ch === '%') {
        // aid-workflow 20260612: 函数内 % 错误检测（边缘场景，SR-07）
        if (parenthesisLevel > 0) {
          ErrorFlags.syntax_error = true
          return result
        }
        if (parenthesisLevel === 0 && !done[i]) {
          done[i] = true
          // Handle factorial before %
          if (i > 0 && result.charAt(i - 1) === '!') {
            let j: number = i - 2
            while (j >= 0 && (this.isDigit(result.charAt(j)) || result.charAt(j) === '.')) { j = j - 1 }
            const factBase: string = result.substring(j + 1, i - 1)
            if (factBase.length === 0) { ErrorFlags.syntax_error = true; return result }
            result = result.substring(0, j + 1) + '((' + factBase + '!)/100)' + result.substring(i + 1)
          } else if (i > 0 && result.charAt(i - 1) === ')') {
            // Parenthesized expression before %
            let j: number = i - 2
            let lvl: number = 1
            while (j >= 0) {
              if (result.charAt(j) === ')') lvl = lvl + 1
              else if (result.charAt(j) === '(') lvl = lvl - 1
              if (lvl === 0) break
              j = j - 1
            }
            if (lvl !== 0) { ErrorFlags.syntax_error = true; return result }
            const subExpr: string = result.substring(j + 1, i - 1)
            const opPos: number = this.lastIndexOfAny(result.substring(0, j), ['+', '-', '*', '/'])
            if (opPos < 0) {
              result = result.substring(0, j) + '((' + subExpr + ')/100)' + result.substring(i + 1)
            } else if (result.charAt(opPos) === '*' || result.charAt(opPos) === '/') {
              result = result.substring(0, opPos + 1) + '((' + subExpr + ')/100)' + result.substring(i + 1)
            } else {
              const base: string = result.substring(0, opPos).trim()
              // Issue #9: wrap base in parens to avoid operator-precedence bugs
              // when base itself is a complex expression (e.g. "100+100*(10/100)")
              // e.g. 100+10%+5%  →  before: "100+100*(10/100)+100+100*(10/100)*(5/100)" = 210.5
              //                    after:  "(100+100*(10/100))+(100+100*(10/100))*(5/100)" = 115.5
              result = '(' + base + ')' + result.charAt(opPos) + '(' + base + ')*(' + subExpr + '/100)' + result.substring(i + 1)
            }
          } else {
            // Regular number before %
            let start: number = i - 1
            while (start >= 0 && (this.isDigit(result.charAt(start)) || result.charAt(start) === '.')) { start = start - 1 }
            const opPos: number = this.lastIndexOfAny(result.substring(0, start + 1), ['+', '-', '*', '/'])
            if (opPos < 0) {
              const num: string = result.substring(start + 1, i)
              if (num.length === 0) { ErrorFlags.syntax_error = true; return result }
              result = result.substring(0, start + 1) + '(' + num + '/100)' + result.substring(i + 1)
            } else if (result.charAt(opPos) === '*' || result.charAt(opPos) === '/') {
              const num: string = result.substring(opPos + 1, i)
              if (num.length === 0) { ErrorFlags.syntax_error = true; return result }
              result = result.substring(0, opPos + 1) + '(' + num + '/100)' + result.substring(i + 1)
            } else {
              const base: string = result.substring(0, opPos).trim()
              const num: string = result.substring(opPos + 1, i)
              // Issue #9: wrap base in parens for operator-precedence safety
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

  addParenthesis(calculation: string): string {
    let clean: string = calculation
    let openP: number = 0
    let closeP: number = 0
    for (let i: number = 0; i < calculation.length; i++) {
      if (calculation.charAt(i) === '(') openP = openP + 1
      if (calculation.charAt(i) === ')') closeP = closeP + 1
    }
    if (closeP < openP) {
      for (let i: number = 0; i < openP - closeP; i++) { clean = clean + ')' }
    }
    if (closeP > openP) { ErrorFlags.syntax_error = true }
    return clean
  }

  private insertChar(str: string, ch: string, idx: number): string {
    return str.substring(0, idx) + ch + str.substring(idx)
  }

  private isDigit(ch: string): boolean {
    return ch >= '0' && ch <= '9'
  }

  private replaceAll(str: string, from: string, to: string): string {
    let result: string = str
    let idx: number = result.indexOf(from)
    while (idx !== -1) {
      result = result.substring(0, idx) + to + result.substring(idx + from.length)
      idx = result.indexOf(from, idx + to.length)
    }
    return result
  }

  private lastIndexOfAny(str: string, chars: string[]): number {
    let last: number = -1
    for (let i: number = 0; i < chars.length; i++) {
      const idx: number = str.lastIndexOf(chars[i])
      if (idx > last) last = idx
    }
    return last
  }
}
