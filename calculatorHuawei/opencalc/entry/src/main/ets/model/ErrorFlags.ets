// OpenCalc — 计算错误标志（共享可变状态）
// ArkTS: 导入的变量是只读的，所以用类的静态可变字段代替

export class ErrorFlags {
  /** 语法错误 */
  static syntax_error: boolean = false
  /** 除数为零 */
  static division_by_0: boolean = false
  /** 定义域错误（如 ln(-1)） */
  static domain_error: boolean = false
  /** 结果无穷大 */
  static is_infinity: boolean = false
  /** 需要实数（负数开偶次方） */
  static require_real_number: boolean = false

  /** 重置所有错误标志 */
  static reset(): void {
    ErrorFlags.syntax_error = false
    ErrorFlags.division_by_0 = false
    ErrorFlags.domain_error = false
    ErrorFlags.is_infinity = false
    ErrorFlags.require_real_number = false
  }

  /**
   * aid-workflow 20260612: 快照当前所有错误标志（用于实时预览计算前保存现场）
   * @returns 5元素 boolean 数组 [syntax_error, division_by_0, domain_error, is_infinity, require_real_number]
   */
  static snapshot(): boolean[] {
    return [
      ErrorFlags.syntax_error,
      ErrorFlags.division_by_0,
      ErrorFlags.domain_error,
      ErrorFlags.is_infinity,
      ErrorFlags.require_real_number
    ]
  }

  /**
   * aid-workflow 20260612: 从快照恢复错误标志（用于实时预览计算后恢复现场）
   * @param snap snapshot() 返回的 5 元素 boolean 数组
   */
  static restore(snap: boolean[]): void {
    ErrorFlags.syntax_error = snap[0]
    ErrorFlags.division_by_0 = snap[1]
    ErrorFlags.domain_error = snap[2]
    ErrorFlags.is_infinity = snap[3]
    ErrorFlags.require_real_number = snap[4]
  }
}
