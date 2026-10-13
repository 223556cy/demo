// OpenCalc — HistorySearch 纯函数模块
// Issue #24 历史搜索框
// 移植自：delta-design.md §3.5
// 边界：大小写不敏感,匹配 expression 或 result 子串;空 query 透传

import { HistoryItem } from '../model/Models'

/**
 * 按关键字过滤历史(大小写不敏感,匹配 expression 或 result 子串)
 * @param items 输入历史 (newest-first, 可为空/null)
 * @param query 用户输入的查询字符串(可含首尾空格)
 * @returns 过滤后的 HistoryItem[] (保持原顺序);空 query / 空 items 返回原 items / []
 */
export function filterHistoryByQuery(items: HistoryItem[] | null | undefined, query: string): HistoryItem[] {
  const safeItems: HistoryItem[] = items ? items : []
  const q: string = query.trim().toLowerCase()
  if (q.length === 0) return safeItems
  const result: HistoryItem[] = []
  for (let i: number = 0; i < safeItems.length; i++) {
    const item: HistoryItem = safeItems[i]
    if (item.expression.toLowerCase().includes(q) ||
        item.result.toLowerCase().includes(q)) {
      result.push(item)
    }
  }
  return result
}
