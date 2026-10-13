// OpenCalc — 历史过滤器
// aid-workflow 20260612 IR-HS-03
// 纯函数模块，便于 100% 单元测试覆盖

import { HistoryItem } from '../model/Models'

/**
 * 过滤历史记录
 * 规则：仅匹配 expression 字段、子串、大小写不敏感
 * @param history 历史记录数组
 * @param query 搜索词（自动 trim + toLowerCase）
 * @returns 过滤后的历史记录（query 为空时返回全部）
 */
export function filterHistory(history: HistoryItem[], query: string): HistoryItem[] {
  const q: string = (query || '').trim().toLowerCase()
  if (q.length === 0) return history
  return history.filter((it: HistoryItem): boolean =>
    it.expression.toLowerCase().indexOf(q) !== -1
  )
}

/** 命名空间风格导出（与项目内 NumberFormatter / BaseConverter 一致） */
export class HistoryFilter {
  static filter = filterHistory
}
