// aid-workflow 20260616: 1:1 端口，与 ArkTS LongPressMenu.ets 一一对应
// GREEN 阶段: 完整实现
//
// 对应实现: opencalc/entry/src/main/ets/pages/LongPressMenu.ets
// 对应设计: specs/changes/20260616-requirement-add-long-press-menu/design.md §3.5.6

/**
 * 长按候选注册表: 按钮标签 → 候选函数列表
 * 修改此处即可扩展,无需改 UI 代码 (FR-7)
 */
const LONG_PRESS_REGISTRY = new Map([
  ['sin', ['arcsin', 'arccos', 'arctan']],
  ['cos', ['arcsin', 'arccos', 'arctan']],
  ['tan', ['arcsin', 'arccos', 'arctan']],
])

/**
 * 按钮是否有长按候选 (FR-1)
 * @param {string} label 按钮文本 (sin/cos/tan/ln/...)
 * @returns {boolean} true=有候选, false=无
 */
function hasCandidates(label) {
  return LONG_PRESS_REGISTRY.has(label)
}

/**
 * 获取按钮的长按候选列表 (FR-1)
 * @param {string} label 按钮文本
 * @returns {string[]} 候选列表(若无候选返回空数组)
 */
function getCandidates(label) {
  const v = LONG_PRESS_REGISTRY.get(label)
  return v === undefined ? [] : v
}

export { LONG_PRESS_REGISTRY, hasCandidates, getCandidates }