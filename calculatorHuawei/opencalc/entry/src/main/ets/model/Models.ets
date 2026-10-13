// OpenCalc — 数据模型
// 移植自：Android Models.kt

/** 计算错误类型枚举 */
export enum CalculatorError {
  NONE = 'none',                   // 无错误
  DIVISION_BY_ZERO = 'division_by_zero',  // 除零
  DOMAIN_ERROR = 'domain_error',          // 定义域错误
  SYNTAX_ERROR = 'syntax_error',          // 语法错误
  INFINITY = 'infinity',                  // 无穷大
  REQUIRE_REAL = 'require_real_number'    // 需要实数
}

/** 数字分组编号体系 */
export enum NumberingSystem {
  INTERNATIONAL = 0,  // 国际制（每3位分组）
  INDIAN = 1          // 印度制
}

/** 科学模式切换状态 */
export enum ScientificModeType {
  NOT_ACTIVE = 0,  // 默认关闭
  ACTIVE = 1,      // 默认开启
  OFF = 2          // 强制关闭
}

/** aid-workflow 20260617: Issue #27 结果显示模式（小数/分数） */
export enum DisplayMode {
  DECIMAL = 'decimal',   // 小数显示（如 0.5）
  FRACTION = 'fraction'  // 分数显示（如 1/2）
}

/** 历史记录条目 */
export interface HistoryItem {
  id: number           // 唯一标识
  expression: string   // 计算表达式
  result: string       // 计算结果
  timestamp: number    // 时间戳
}

/** 计算器偏好设置（存储于 @ohos.data.preferences） */
export interface CalculatorPreferences {
  theme: number                    // 主题（0=默认 1=AMOLED 2=Material）
  forceDayNight: number            // 日夜模式（0=系统 1=浅色 2=深色 3=AMOLED）
  vibrationEnabled: boolean        // 振动反馈开关
  preventSleep: boolean            // 防休眠开关
  historySize: number              // 历史记录最大条数
  scientificModeDefault: number    // 默认科学模式状态
  // aid-workflow 20260618: Issue #29 程序员模式默认值 (0=未激活 1=激活 2=强制关闭)
  programmerModeDefault: number
  radiansDefault: boolean          // 默认弧度模式
  numberPrecision: number          // 数字精度
  decimalSeparatorSymbol: string   // 小数点符号
  groupingSeparatorSymbol: string  // 千分位符号
  // aid-workflow 20260617: Issue #27 结果显示模式(小数/分数)
  resultDisplayMode: DisplayMode
}

/** 默认偏好设置 */
export const DEFAULT_PREFERENCES: CalculatorPreferences = {
  theme: 0,
  forceDayNight: 0,
  vibrationEnabled: true,
  preventSleep: false,
  historySize: 100,
  scientificModeDefault: ScientificModeType.NOT_ACTIVE,
  programmerModeDefault: ScientificModeType.NOT_ACTIVE,
  radiansDefault: false,
  numberPrecision: 12,
  decimalSeparatorSymbol: '.',
  groupingSeparatorSymbol: ',',
  // aid-workflow 20260617: Issue #27 默认小数显示
  resultDisplayMode: DisplayMode.DECIMAL
}
