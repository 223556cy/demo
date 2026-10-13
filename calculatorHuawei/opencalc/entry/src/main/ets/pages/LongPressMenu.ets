// aid-workflow 20260616: 长按候选菜单逻辑 (纯静态类, 无 UI 依赖)
// 对应端口: specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.port.mjs
// 对应设计: specs/changes/20260616-requirement-add-long-press-menu/design.md §3.5.6
//
// FR-6 静态注册表 + FR-7 可扩展: 修改 REGISTRY 一行即可新增映射
// FMEA C3: 候选点击复用 onFunc, 禁止另写插入逻辑

export class LongPressMenu {
  /** aid-workflow 20260616: 长按候选注册表, 按钮标签 → 候选函数列表 */
  static REGISTRY: Map<string, string[]> = new Map<string, string[]>([
    ['sin', ['arcsin', 'arccos', 'arctan']],
    ['cos', ['arcsin', 'arccos', 'arctan']],
    ['tan', ['arcsin', 'arccos', 'arctan']],
  ])

  /** aid-workflow 20260616: 按钮是否有长按候选 (FR-1) */
  static hasCandidates(label: string): boolean {
    return LongPressMenu.REGISTRY.has(label)
  }

  /** aid-workflow 20260616: 获取按钮的长按候选列表 (FR-1) */
  static getCandidates(label: string): string[] {
    const v = LongPressMenu.REGISTRY.get(label)
    return v === undefined ? [] : v
  }
}

// aid-workflow 20260616: UI 规格常量 (供 LongPressMenuPanel 引用)
// 集中管理便于 REFACTOR 阶段调整 (design.md §3.4)
export const MENU_WIDTH_RATIO = '60%'
export const MENU_MAX_WIDTH = 280
export const MENU_ITEM_HEIGHT = 44
export const MENU_FONT_SIZE = 16
export const MENU_BORDER_RADIUS = 12
export const MENU_MASK_COLOR = '#000000'
export const MENU_MASK_OPACITY = 0.4
export const MENU_PADDING = 4
