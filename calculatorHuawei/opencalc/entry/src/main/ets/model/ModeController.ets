// OpenCalc — 键盘模式状态机 (Issue #29 竖屏滑动切换)
// aid-workflow 20260618: 纯函数式状态机, 不依赖 UI / Preferences, 可独立单测

/**
 * 键盘模式枚举
 * - BASIC: 基础键盘 (数字 + 基础运算)
 * - SCIENTIFIC: 科学键盘 (+ sin/cos/tan/ln/log 等)
 * - PROGRAMMER: 程序员键盘 (+ HEX/DEC/OCT/BIN/位运算)
 */
export enum KeyboardMode {
  BASIC = 0,
  SCIENTIFIC = 1,
  PROGRAMMER = 2
}

/** 模式总数 */
export const KEYBOARD_MODE_COUNT: number = 3

/**
 * 检查 index 是否落在合法范围 [0, KEYBOARD_MODE_COUNT)
 * @param idx 待校验 index
 * @returns true=合法, false=非法
 */
export function isValidModeIndex(idx: number): boolean {
  if (idx < 0) return false
  if (idx >= KEYBOARD_MODE_COUNT) return false
  return true
}

/**
 * 单调前进一格: BASIC -> SCIENTIFIC -> PROGRAMMER -> BASIC
 * @param current 当前模式
 * @returns 下一个模式
 */
export function nextMode(current: KeyboardMode): KeyboardMode {
  const next: number = (current + 1) % KEYBOARD_MODE_COUNT
  return next as KeyboardMode
}

/**
 * cycleMode 别名, 行为等同 nextMode
 * (与设计 D3.5.6 命名保持一致, 便于 CalculatorPage 引用)
 */
export function cycleMode(current: KeyboardMode): KeyboardMode {
  return nextMode(current)
}

/**
 * Swiper onChange 入口: 将 swiper index 转成 KeyboardMode
 * 非法 index (负数 / 越界) 返回 null, 调用方负责 warn + 兜底
 * @param idx Swiper 上报的 index
 * @returns 合法 -> KeyboardMode, 非法 -> null
 */
export function applySwiperIndex(idx: number): KeyboardMode | null {
  if (!isValidModeIndex(idx)) return null
  return idx as KeyboardMode
}

/**
 * 启动优先级解析
 * 优先级: SCIENTIFIC > PROGRAMMER > BASIC
 * - scientificModeDefault == 1 (ACTIVE) -> SCIENTIFIC
 * - else programmerModeDefault == 1 -> PROGRAMMER
 * - else -> BASIC
 * @param scientificModeDefault 旧字段值
 * @param programmerModeDefault 新字段值
 * @returns 启动时的 KeyboardMode
 */
export function resolveStartupMode(
  scientificModeDefault: number,
  programmerModeDefault: number
): KeyboardMode {
  if (scientificModeDefault === 1) return KeyboardMode.SCIENTIFIC
  if (programmerModeDefault === 1) return KeyboardMode.PROGRAMMER
  return KeyboardMode.BASIC
}
