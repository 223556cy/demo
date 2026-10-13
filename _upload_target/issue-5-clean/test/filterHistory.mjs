// filterHistory.mjs — Pure-JS 对照实现（与 ArkTS filterHistory 保持 1:1 逻辑）
//
// 来源：specs/changes/20260611-requirement-add-history-search/delta-design §3.5.8
//   1. query.trim().slice(0, 200) — 去空白 + 截断
//   2. trim 后空 → 返回 items 全量
//   3. needle = q.toLowerCase() — 大小写归一
//   4. 命中：item.expression.toLowerCase().includes(needle) || item.result.toLowerCase().includes(needle)
//   5. 用 String.includes（禁止 RegExp — FM-002-01）
//   6. 不修改入参 items，返回新数组
//
// HistoryItem 形状（来自 model/Models.ets）：
//   { id: number, expression: string, result: string, timestamp: number }
//
// 不变量：
//   I-1: query 经 .trim() 去前后空白
//   I-2: query 超过 200 字符时按前 200 字符截断
//   I-3: 大小写不敏感（统一 .toLowerCase()）
//   I-4: 不修改入参 items（返回新数组）
export function filterHistory(items, query) {
  const q = (query ?? '').trim().slice(0, 200)   // I-1 + I-2
  if (q.length === 0) return items              // I-1 后空 → 全量
  const needle = q.toLowerCase()                // I-3
  return items.filter((item) =>
    item.expression.toLowerCase().includes(needle) ||
    item.result.toLowerCase().includes(needle)
  )                                              // I-4 (filter 返回新数组)
}
