// OpenCalc — 数字格式化器
// 移植自：NumberFormatter.kt（133行）
// 纯逻辑，无 Android 依赖

import { NumberingSystem } from '../model/Models'

/**
 * 将计算结果格式化为带千分位和小数分隔符的显示文本。
 * 支持国际制（每3位分组）和印度制两种编号体系。
 */
export class NumberFormatter {

  /**
   * 主入口：格式化数字字符串
   * @param text 原始数字文本
   * @param decimalSeparatorSymbol 小数点符号
   * @param groupingSeparatorSymbol 千分位符号
   * @param numberingSystem 编号体系
   * @returns 格式化后的字符串
   */
  static format(
    text: string,
    decimalSeparatorSymbol: string,
    groupingSeparatorSymbol: string,
    numberingSystem: NumberingSystem = NumberingSystem.INTERNATIONAL
  ): string {
    // 先移除已有的千分位符号
    const textNoSeparator: string = NumberFormatter.removeSeparators(text, groupingSeparatorSymbol)
    // 将字符串拆分为数字段和非数字段
    const numbersList: string[] = NumberFormatter.extractString(textNoSeparator, decimalSeparatorSymbol)
    // 对数字段添加千分位
    const numbersWithSeparators: string[] = NumberFormatter.addSeparators(
      numbersList, decimalSeparatorSymbol, groupingSeparatorSymbol, numberingSystem
    )

    // 重新拼接
    let result: string = ''
    for (let i: number = 0; i < numbersWithSeparators.length; i++) {
      result += numbersWithSeparators[i]
    }
    return result
  }

  /**
   * 将字符串拆分为数字段和非数字段
   * 例如 "12+34" → ["12", "+", "34"]
   */
  private static extractString(text: string, decimalSeparatorSymbol: string): string[] {
    const result: string[] = []
    let currentNumber: string = ''

    for (let i: number = 0; i < text.length; i++) {
      const char: string = text.charAt(i)
      if (NumberFormatter.isDigit(char) || char === decimalSeparatorSymbol) {
        currentNumber += char
      } else {
        if (currentNumber.length > 0) {
          result.push(currentNumber)
          currentNumber = ''
        }
        result.push(char)
      }
    }

    if (currentNumber.length > 0) {
      result.push(currentNumber)
    }
    return result
  }

  /**
   * 对数字段列表添加千分位符号
   */
  private static addSeparators(
    numbersList: string[],
    decimalSeparatorSymbol: string,
    groupingSeparatorSymbol: string,
    numberingSystem: NumberingSystem
  ): string[] {
    const result: string[] = []
    for (let i: number = 0; i < numbersList.length; i++) {
      const item: string = numbersList[i]
      // 判断是否为数字（包含小数点）
      if (item.indexOf(decimalSeparatorSymbol) !== -1) {
        if (item.charAt(0) === decimalSeparatorSymbol) {
          result.push(item)  // 以小数点开头的不加千分位
        } else {
          const idx: number = item.indexOf(decimalSeparatorSymbol)
          const integersPart: string = item.substring(0, idx)
          const fractions: string = item.substring(idx + 1)
          result.push(
            NumberFormatter.formatIntegers(integersPart, groupingSeparatorSymbol, numberingSystem === NumberingSystem.INTERNATIONAL) +
            decimalSeparatorSymbol + fractions
          )
        }
      } else {
        result.push(NumberFormatter.formatIntegers(item, groupingSeparatorSymbol, numberingSystem === NumberingSystem.INTERNATIONAL))
      }
    }
    return result
  }

  /**
   * 对整数部分添加千分位
   * 国际制：每3位一组（如 1,234,567）
   * 印度制：首组3位，之后每2位一组（如 12,34,567）
   */
  private static formatIntegers(
    integers: string,
    groupingSeparatorSymbol: string,
    isInternational: boolean
  ): string {
    if (isInternational) {
      // 反转 → 每3位分块 → 连接 → 反转回来
      const reversed: string = integers.split('').reverse().join('')
      const chunks: string[] = []
      for (let i: number = 0; i < reversed.length; i += 3) {
        chunks.push(reversed.substring(i, i + 3))
      }
      return chunks.join(groupingSeparatorSymbol).split('').reverse().join('')
    } else {
      return NumberFormatter.formatIndianNumberingSystem(integers)
    }
  }

  /** 移除字符串中的千分位符号 */
  private static removeSeparators(text: string, groupingSeparatorSymbol: string): string {
    let result: string = text
    while (result.indexOf(groupingSeparatorSymbol) !== -1) {
      result = result.replace(groupingSeparatorSymbol, '')
    }
    return result
  }

  /**
   * 印度编号体系格式化
   * 规则：末3位一组，之后每2位一组
   * 例如 12345678 → 1,23,45,678
   */
  private static formatIndianNumberingSystem(numberStr: string): string {
    const isNegative: boolean = numberStr.charAt(0) === '-'
    const numberWithoutSign: string = isNegative ? numberStr.substring(1) : numberStr

    const dotIdx: number = numberWithoutSign.indexOf('.')
    const integerPart: string = dotIdx >= 0 ? numberWithoutSign.substring(0, dotIdx) : numberWithoutSign
    const decimalPart: string = dotIdx >= 0 ? numberWithoutSign.substring(dotIdx + 1) : ''

    const length: number = integerPart.length
    const chars: string[] = []
    let count: number = 0

    // 从右往左遍历
    for (let i: number = length - 1; i >= 0; i--) {
      chars.push(integerPart.charAt(i))
      count++

      if (count === 3 && i !== 0) {
        chars.push(',')
        count = 0
      } else if (count === 2 && i !== 0 && length - i > 3) {
        chars.push(',')
        count = 0
      }
    }

    const formattedIntegerPart: string = chars.reverse().join('')
    const formattedNumber: string = decimalPart.length > 0 ?
      formattedIntegerPart + '.' + decimalPart : formattedIntegerPart
    return isNegative ? '-' + formattedNumber : formattedNumber
  }

  /** 判断字符是否为数字（0-9） */
  private static isDigit(char: string): boolean {
    return char >= '0' && char <= '9'
  }
}
