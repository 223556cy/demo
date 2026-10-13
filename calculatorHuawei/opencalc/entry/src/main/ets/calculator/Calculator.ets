// OpenCalc — 计算引擎（递归下降解析器 + 数学函数）
// 移植自：Calculator.kt（417行）
// 使用类方法代替内部函数（ArkTS 限制）
import { ErrorFlags } from '../model/ErrorFlags'

/**
 * 计算引擎核心类
 * 实现了递归下降表达式解析器，支持四则运算、科学函数、
 * 阶乘（Gamma函数扩展）、幂运算等。
 * 使用 ASCII 字符码进行解析以提高性能。
 */
export class CalcEngine {
  /** 当前表达式字符串 */
  private eq: string = ''
  /** 当前解析位置 */
  private p: number = -1
  /** 当前字符的 ASCII 码 */
  private c: number = 0
  /** 是否为角度模式（否则为弧度） */
  private deg: boolean = true
  // aid-workflow 20260617: Issue #26 函数图像 - x 变量当前值
  private xValue: number = 0

  /**
   * 主入口：计算表达式
   * @param equation 数学表达式字符串
   * @param isDegree true=角度模式，false=弧度模式
   * @returns 计算结果
   */
  evaluate(equation: string, isDegree: boolean): number {
    this.eq = equation; this.p = -1; this.c = 0; this.deg = isDegree
    this.nx(); return this.parseExpression()
  }

  /**
   * aid-workflow 20260617: Issue #26 函数图像
   * 在 x 取某值时计算表达式(单点求值)
   * 失败(语法错误/除零/定义域外/NaN/Inf)返回 null,不抛异常,不污染 ErrorFlags
   * @param cleanExpr 已通过 Expression.getCleanExpression 预处理的 ASCII 表达式
   * @param x x 变量值
   * @param isDegree true=角度, false=弧度
   * @returns 数值结果;失败返回 null
   */
  evaluateAt(cleanExpr: string, x: number, isDegree: boolean): number | null {
    ErrorFlags.reset()
    this.xValue = x
    this.deg = isDegree
    try {
      const v = this.evaluate(cleanExpr, isDegree)
      if (!isFinite(v)) {
        return null
      }
      if (ErrorFlags.syntax_error || ErrorFlags.division_by_0 ||
          ErrorFlags.domain_error || ErrorFlags.is_infinity ||
          ErrorFlags.require_real_number) {
        return null
      }
      return v
    } catch {
      return null
    }
  }

  /** 读取下一个字符 */
  private nx(): void { this.p++; this.c = this.p < this.eq.length ? this.eq.charCodeAt(this.p) : -1 }

  /**
   * 尝试匹配指定字符，成功则消费并返回 true
   * 跳过空格
   */
  private eat(ch: number): boolean {
    while (this.c === 32) this.nx()  // 跳过空格
    if (this.c === ch) { this.nx(); return true }
    return false
  }

  /** 解析表达式：Term (+/- Term)* */
  private parseExpression(): number {
    let x: number = this.parseTerm()
    while (true) {
      if (this.eat(43)) x = x + this.parseTerm()       // 43 = '+'
      else if (this.eat(45)) x = x - this.parseTerm()  // 45 = '-'
      else return x
    }
  }

  /** 解析项：Factor (* / # Factor)*  # 为取模运算符 */
  private parseTerm(): number {
    let x: number = this.parseFactor()
    while (true) {
      if (this.eat(42)) x = x * this.parseFactor()     // 42 = '*'
      else if (this.eat(35)) {                          // 35 = '#' 取模
        let d: number = this.parseFactor()
        if (d === 0) { ErrorFlags.division_by_0 = true; x = 0 }
        else x = x % d
      }
      else if (this.eat(47)) {                          // 47 = '/' 除法
        let d: number = this.parseFactor()
        if (d === 0) { ErrorFlags.division_by_0 = true; x = 0 }
        else x = x / d
      }
      else return x
    }
  }

  /** 解析因子：数字/括号/函数/一元运算符/常量 */
  private parseFactor(): number {
    // 一元正号
    if (this.eat(43)) return +this.parseFactor()
    // 一元负号
    if (this.eat(45)) return -this.parseFactor()

    // aid-workflow 20260617: Issue #26 单字母变量 x (绘图用)
    // 必须在函数名分支前特判,否则 'x' 会被当成未知函数名 → syntax_error
    if (this.c === 120) {  // 'x' = 120
      this.nx()
      return this.xValue
    }

    let x: number = 0; const sp: number = this.p

    // 括号表达式
    if (this.eat(40)) {
      x = this.parseExpression()
      if (!this.eat(41)) { ErrorFlags.syntax_error = true; x = 0 }
    }
    // 数字
    else if ((this.c >= 48 && this.c <= 57) || this.c === 46) {
      while ((this.c >= 48 && this.c <= 57) || this.c === 46) this.nx()
      const ns: string = this.eq.substring(sp, this.p)
      if (ns.split('.').length - 1 > 1 || (ns.length === 1 && ns.charAt(0) === '.')) {
        ErrorFlags.syntax_error = true; x = 0
      } else x = parseFloat(ns)
    }
    // 自然常数 e
    else if (this.eat(101)) x = Math.E
    // 圆周率 π
    else if (this.eat(960)) x = Math.PI
    // 函数名（小写字母开头）
    else if (this.c >= 97 && this.c <= 122) {
      while (this.c >= 97 && this.c <= 122) this.nx()
      const fn: string = this.eq.substring(sp, this.p)
      // 解析函数参数
      if (this.eat(40)) { x = this.parseExpression(); if (!this.eat(41)) x = this.parseFactor() }
      else x = this.parseFactor()

      // 调度到对应数学函数
      if (fn === 'sqrt') {        // 平方根
        if (x >= 0) x = Math.sqrt(x); else ErrorFlags.require_real_number = true
      } else if (fn === 'factorial') x = this.fact(x)       // 阶乘
      else if (fn === 'ln') {     // 自然对数
        if (x <= 0) ErrorFlags.domain_error = true; else x = Math.log(x)
      } else if (fn === 'logtwo') {  // 以2为底对数
        if (x <= 0) ErrorFlags.domain_error = true; else x = Math.log2(x)
      } else if (fn === 'logten') {  // 以10为底对数
        if (x <= 0) ErrorFlags.domain_error = true; else x = Math.log10(x)
      } else if (fn === 'xp') x = this.powx(Math.E, x)     // e^x
      else if (fn === 'sin') {    // 正弦
        x = Math.sin(this.deg ? x * Math.PI / 180 : x)
        if (x > 0 && x < 1e-14) x = Math.round(x)
      } else if (fn === 'cos') {  // 余弦
        x = Math.cos(this.deg ? x * Math.PI / 180 : x)
        if (x > 0 && x < 1e-14) x = Math.round(x)
      } else if (fn === 'tan') {  // 正切
        x = Math.tan(this.deg ? x * Math.PI / 180 : x)
        if (x > 0 && x < 1e-14) x = Math.round(x)
      } else if (fn === 'arcsi') {  // 反正弦
        if (Math.abs(x) > 1) ErrorFlags.domain_error = true
        else { x = Math.asin(x); if (this.deg) x = x * 180 / Math.PI; if (x > 0 && x < 1e-14) x = Math.round(x) }
      } else if (fn === 'arcco') {  // 反余弦
        if (Math.abs(x) > 1) ErrorFlags.domain_error = true
        else { x = Math.acos(x); if (this.deg) x = x * 180 / Math.PI; if (x > 0 && x < 1e-14) x = Math.round(x) }
      } else if (fn === 'arcta') {  // 反正切
        x = Math.atan(x); if (this.deg) x = x * 180 / Math.PI; if (x > 0 && x < 1e-14) x = Math.round(x)
      } else ErrorFlags.syntax_error = true
    } else {
      ErrorFlags.syntax_error = true; x = 0
    }
    // 幂运算（^ 运算符，优先级最高）
    if (this.eat(94)) x = this.powx(x, this.parseFactor())
    return x
  }

  /**
   * 阶乘函数
   * 整数：直接迭代计算
   * 非整数：使用 Lanczos 近似（Gamma 函数）
   * n >= 3000 → 无穷大
   */
  private fact(n: number): number {
    if (n >= 3000) { ErrorFlags.is_infinity = true; return 0 }
    if (n < 0) { ErrorFlags.domain_error = true; return 0 }
    if (n === Math.floor(n)) { let r: number = 1; for (let i: number = 1; i <= n; i++) r = r * i; return r }
    return this.gl(n + 1)  // Gamma(n+1) = n!
  }

  /** Gamma 函数（Lanczos 近似） */
  private gl(x: number): number {
    const p: number[] = [676.5203681218851, -1259.1392167224028, 771.3234287776531, -176.6150291621406, 12.507343278686905, -0.13857109526572012, 9.984369578019572e-6, 1.5056327351493116e-7]
    const z: number = x - 1; let a: number = 0.9999999999998099
    for (let i: number = 0; i < p.length; i++) a = a + p[i] / (z + i + 1)
    return Math.sqrt(2 * Math.PI) * Math.pow(z + 7.5, z + 0.5) * Math.exp(-(z + 7.5)) * a
  }

  /**
   * 幂运算 x^f
   * 支持小数指数（拆分为整数部分和小数部分分别计算）
   */
  private powx(x: number, f: number): number {
    if (x === 0) return 0
    if (f > 10000) { ErrorFlags.is_infinity = true; return 0 }
    const ip: number = Math.trunc(f); const dp: number = f - ip
    // 负数不能开小数次方（会得到复数）
    if (x < 0 && dp !== 0) { ErrorFlags.require_real_number = true; return x }
    if (f > 0) return Math.pow(x, ip) * Math.pow(x, dp)
    return 1 / (Math.pow(x, -ip) * Math.pow(x, -dp))
  }
}
