# Delta-Spec — 历史搜索框 (Issue #24)

> AID PLANNING step4 产出 · 增量规格说明
> 在 `opencalc/spec/DESIGN.md` 基础上的增量规范
> 基于 Issue #15 历史分组的扩展(对齐 #15 风格)

## 1. 概述

| 项 | 说明 |
|----|------|
| **变更名** | 历史列表支持关键字搜索 |
| **类型** | requirement-change (用户指定标签) / 实质: 新增功能 (View 增量) |
| **影响层级** | View (CalculatorPage.HistoryPanel) + ViewModel (history/HistorySearch.ets 纯函数模块) |
| **数据模型** | 复用现有 HistoryItem,无新增字段 |
| **持久化** | 不变 (PreferencesStore 仍存原始 HistoryItem[]) |
| **i18n** | 不变 (占位文案使用静态中文字符串) |
| **依赖 #15** | 必须保留 (过滤后仍按 "今天/昨天/更早" 三段分组) |

## 2. 需求分解

### FR-24-01 搜索框位置
- **描述**: HistoryPanel 顶部、折叠手柄下方、List 上方加一个搜索输入框
- **优先级**: P0
- **验收**:
  - 搜索框始终显示(只要 HistoryPanel 可见)
  - 横屏/竖屏都显示
  - 不与折叠手柄冲突(手柄可独立点击关闭面板)

### FR-24-02 搜索框 UI
- **描述**: 单行 TextInput + 占位符 "搜索算式或结果" + 右侧 ✕ 清除按钮
- **优先级**: P0
- **验收**:
  - 占位符仅在 input 为空时显示
  - ✕ 按钮仅在 input 非空时显示
  - ✕ 点击后清空 input 并恢复全部历史
  - input 背景色随主题变化(getPanelBg)
  - ✕ 颜色=getT2 灰色

### FR-24-03 实时过滤
- **描述**: 用户输入时实时过滤 history 列表(无防抖,无 Enter 提交)
- **优先级**: P0
- **验收**:
  - 输入"12"时,List 立即只显示 expression 或 result 包含"12"的条目
  - 删除字符时,List 立即恢复
  - 不阻塞 List 滚动

### FR-24-04 大小写不敏感
- **描述**: 搜索匹配忽略大小写
- **优先级**: P0
- **验收**:
  - 输入"SIN"匹配"SIN(30)"和"sin(30)"和"Sin(30)"
  - 输入"3.14"匹配"3.14"和"3.14000"

### FR-24-05 搜索范围 (expression + result)
- **描述**: 匹配 `HistoryItem.expression` 或 `HistoryItem.result` 任一字段的子串
- **优先级**: P0
- **验收**:
  - 搜索 expression="2+2" 且 result="4" → 输入"2+2"或"4"都能命中
  - 搜索 expression="π*2" 且 result="6.28" → 输入"π"或"6.28"都能命中

### FR-24-06 空查询行为
- **描述**: 空字符串 query → 不过滤,显示全部历史
- **优先级**: P0
- **验收**:
  - query="" 时,getHistorySections() 行为与 #15 完全一致
  - query="   " (全空格) → trim 后视为空,不过滤

### FR-24-07 无结果占位
- **描述**: 过滤后无匹配条目时,显示"无匹配记录"占位(替代空 List)
- **优先级**: P0
- **验收**:
  - 居中显示,fontSize 13,fontColor getT2,与"暂无计算记录"风格一致
  - 分组标题("今天"等)仍按段渲染(虽然 items 都为空,但段在原列表中已 filter 掉)
  - 实际效果: query 无匹配时,HistoryPanel 只显示"无匹配记录",不显示空段

### FR-24-08 过滤后仍按日期分组
- **描述**: 过滤不影响分组结构,过滤后的 items 仍按 #15 逻辑分到"今天/昨天/更早"
- **优先级**: P0
- **验收**:
  - 搜索"12"后,只显示含 12 的 items,且仍按 timestamp 归到对应段
  - 空段不渲染段标题(#15 既有行为)

### FR-24-09 不影响其他历史操作
- **描述**: 搜索框存在时,点击回填、滑删、主题色等行为不变
- **优先级**: P0
- **验收**:
  - 点击过滤后的 item → 仍回填 expression + 关闭 HistoryPanel + 清空 searchQuery
  - 滑删 item → 即时刷新过滤结果
  - 主题色切换: 搜索框/✕/占位/无结果文字均跟随

### FR-24-10 关闭面板时清空搜索
- **描述**: HistoryPanel 关闭时(无论是点手柄还是其他方式),自动清空 searchQuery
- **优先级**: P1
- **验收**:
  - 关闭后再打开,搜索框为空,显示全部历史
  - 避免"上次搜索残留"

## 3. 接口规格

### 3.1 新增接口: `HistorySearch.ets`

```typescript
// entry/src/main/ets/history/HistorySearch.ets
import { HistoryItem } from '../model/Models'

/**
 * 按关键字过滤历史(大小写不敏感,匹配 expression 或 result 子串)
 * @param items 输入历史 (newest-first, 可为空/null)
 * @param query 用户输入的查询字符串(可含首尾空格)
 * @returns 过滤后的 HistoryItem[] (保持原顺序);空 query / 空 items 返回原 items
 */
export function filterHistoryByQuery(
  items: HistoryItem[] | null | undefined,
  query: string
): HistoryItem[]
```

**行为规则**:
- `query` 经 `query.trim()` 后若为空 → 返回 `items` 原样(不复制)
- 否则对每个 item 检查 `item.expression.toLowerCase().includes(q)` 或 `item.result.toLowerCase().includes(q)`
- 不修改原数组(返回新数组)

### 3.2 View 接口变更 (CalculatorPage.ets)

**新增 @State**:
```typescript
@State searchQuery: string = ''  // aid-workflow 20260617 Issue #24: 搜索框关键字
```

**修改 `getHistorySections()`**:
```typescript
getHistorySections(): HistorySection[] {
  const filtered = filterHistoryByQuery(this.history, this.searchQuery)
  return groupHistoryByDate(filtered, Date.now())
}
```

**修改 `HistoryPanel()`**:
- 在手柄 Row 下方、List 上方插入 `@Builder SearchBox()`
- SearchBox 内含 TextInput + 清除按钮
- input.onChange → `this.searchQuery = value`
- 清除按钮 .onClick → `this.searchQuery = ''`
- List 渲染外层 if 分支: `filteredTotal === 0 && searchQuery.length > 0` → 显示"无匹配记录"占位

**关闭面板时**:
- 折叠手柄 onClick 中追加 `this.searchQuery = ''`

## 4. 数据流

```
searchQuery (State)
    ↓ onChange
filterHistoryByQuery(history, searchQuery)   // 纯函数
    ↓
groupHistoryByDate(filtered, now)           // #15 纯函数
    ↓
List { ForEach sections { ForEach items } }  // 渲染
```

## 5. 可靠性分析 (FMEA 消减措施清单)

| 故障模式 | 严重度 | 概率 | 缓解措施 | 验证 |
|---------|--------|------|---------|------|
| **FMEA-1**: 过滤逻辑错误导致历史丢失 | High | Low | filterHistoryByQuery 单元测试覆盖空 query/全匹配/无匹配/特殊字符 | UT |
| **FMEA-2**: searchQuery 状态污染关闭后再开 | Med | Med | 关闭面板时 reset searchQuery = '' | UT/UI |
| **FMEA-3**: TextInput 抢焦点导致 List 不可滚 | Med | Med | 输入框不抢 List 焦点,搜索框在 List 外层 | UI |
| **FMEA-4**: 大小写敏感导致找不到 | High | Med | 强制 toLowerCase 比较 | UT |
| **FMEA-5**: query 含空格导致无结果 | Med | High | trim() 后比较 + 视为子串 | UT |
| **FMEA-6**: 无结果状态错误显示空段 | Med | Med | 无结果时不渲染 List,只显示"无匹配记录" | UI |
| **FMEA-7**: 主题色不生效 | Low | Low | ✕/占位/无结果均用 getT2,input bg 用 getPanelBg | UI |
| **FMEA-8**: 输入框 keyboard 遮挡历史 | Med | Med | 搜索框固定顶部,List 内容区可滚动 | UI |
| **FMEA-9**: 横屏布局错乱 | Med | Med | searchbox width='100%' padding 16 | UI |
| **FMEA-10**: 过滤函数性能问题 (n=1000) | Low | Low | contains O(n),n≤1000 时 < 10ms | UT (大数据集) |

## 6. 验收标准 (AC)

### AC_HS_01 搜索框渲染
- HistoryPanel 打开时,顶部出现搜索框
- 搜索框含占位符"搜索算式或结果"

### AC_HS_02 输入即过滤
- 输入"2" → 只显示含 2 的条目
- 删除字符 → 恢复

### AC_HS_03 大小写不敏感
- 输入"SIN" → 命中含"sin"或"SIN"或"Sin"的条目

### AC_HS_04 清除按钮
- input 空时 ✕ 隐藏
- input 非空时 ✕ 显示
- 点 ✕ → input 清空 + 全部历史恢复

### AC_HS_05 无结果占位
- query="xyz123" (无匹配) → 显示"无匹配记录"

### AC_HS_06 过滤后分组
- query 命中后,段标题("今天"/"昨天"/"更早")仍按原 timestamp 归类
- 空段不渲染段标题

### AC_HS_07 关闭清空
- 关闭 HistoryPanel → searchQuery 重置为 ''
- 再打开 → 搜索框为空

### AC_HS_08 兼容性
- #15 分组测试用例全部仍通过
- 历史操作(点击回填/滑删)不受影响

### AC_HS_09 主题兼容
- 浅色/暗色/AMOLED 三主题下,搜索框/✕/占位颜色均正确

### AC_HS_10 横屏兼容
- 横屏布局下搜索框正常显示,可输入可清除

## 7. 不涉及

- **不涉及数据模型变更**: HistoryItem 字段不变
- **不涉及持久化变更**: PreferencesStore 仍存原始 HistoryItem[]
- **不涉及新依赖**: 不引入新 npm/ohpm 包
- **不涉及新页面**: 仅在 CalculatorPage 内部加组件
- **不涉及国际化**: 文案使用静态中文(与 #15 一致)
- **不涉及性能优化**: history ≤ 100 条,contains 性能充足
- **不涉及新权限**: 不需要任何权限申请

## 8. 拆分/依赖

- **依赖 #15** (历史分组): 过滤后必须仍走 groupHistoryByDate
- **不破坏 #15/#16/#17/#18**: 任何历史/计算功能不受影响
