# Delta-Spec — 历史日期分组

> AID PLANNING step4 产出 · 增量规格说明
> 在 `opencalc/spec/DESIGN.md` 基础上的增量规范

## 1. 概述

| 项 | 说明 |
|----|------|
| **变更名** | 历史列表支持按日期分组 |
| **类型** | requirement-add (新增功能) |
| **影响层级** | View (HistoryPanel 渲染) + ViewModel (新增 HistoryGroup 纯函数模块) |
| **数据模型** | 复用现有 HistoryItem,无新增字段 |
| **持久化** | 不变 (PreferencesStore 仍存原始 HistoryItem[]) |
| **i18n** | 不变 (标题使用静态中文字符串,与现有 "暂无计算记录" 一致) |

## 2. 需求分解

### FR-15-01 历史面板三段分组
- **描述**：HistoryPanel 渲染时,把 `HistoryItem[]` 按 `timestamp` 分为 "今天" / "昨天" / "更早" 三段
- **优先级**：P0
- **验收**：
  - 当某段至少含 1 条记录时,该段标题必须显示
  - 当某段为空时,该段标题不渲染
  - 段内顺序保持现有 newest-first (prepend 顺序)

### FR-15-02 分组边界定义
- **描述**：分组基于**本地时区**日历日划分
  - 今天: `[今日 00:00:00.000, now]`
  - 昨天: `[昨日 00:00:00.000, 今日 00:00:00.000)`
  - 更早: `[..., 昨日 00:00:00.000)`
- **优先级**：P0
- **验收**：边界时间戳 (00:00:00.000) 归属正确 (与 Android DateUtils.isToday 行为对齐)

### FR-15-03 段标题固定中文
- **描述**：段标题使用静态中文字符串 "今天" / "昨天" / "更早"
- **优先级**：P1
- **验收**：渲染输出包含这三个字符串 (在 uiautomator dump 中可见)

### FR-15-04 段内顺序保持
- **描述**：每段内部的渲染顺序与原 `this.history` 数组顺序一致 (newest-first)
- **优先级**：P0
- **验收**：纯函数 `groupHistoryByDate` 内部不排序,只做分组

### FR-15-05 历史操作不变
- **描述**：点击回填、滑删、横竖屏布局、主题色等所有现有行为不改变
- **优先级**：P0
- **验收**：回归测试通过;UI 测试覆盖竖屏 + 横屏两种布局

## 3. 接口规格

### 新增接口: `HistoryGroup.ets`

```typescript
// entry/src/main/ets/history/HistoryGroup.ets
import { HistoryItem } from '../model/Models'

/** 分组类型枚举 (按时间倒序固定) */
export enum HistoryGroupKey {
  TODAY = 'today',
  YESTERDAY = 'yesterday',
  EARLIER = 'earlier'
}

/** 单个分组: 标题 + 条目列表 */
export interface HistorySection {
  key: HistoryGroupKey     // TODAY / YESTERDAY / EARLIER
  title: string            // "今天" / "昨天" / "更早"
  items: HistoryItem[]     // 该段内条目,保持输入顺序
}

/**
 * 把 HistoryItem[] 按 timestamp 分到三段
 * @param items 输入历史 (newest-first, 可为空)
 * @param now 参考"当前时间" (ms epoch),用于计算 today/yesterday 边界
 * @returns 长度固定 3 的 HistorySection[],顺序: 今天/昨天/更早;空段 title 仍为中文,items=[]
 */
export function groupHistoryByDate(items: HistoryItem[], now: number): HistorySection[]

/** 内部工具: 把 Date 转成 "本地日历日起始 ms" (00:00:00.000) */
export function startOfLocalDay(d: Date): number
```

### 接口约束
- `groupHistoryByDate` 必须是**纯函数**,无副作用,便于单测
- 输入 `items=[]` 返回三段均空的数组
- 不修改入参数组

### 内部集成 (CalculatorPage)

```typescript
// CalculatorPage.ets 新增 import
import { groupHistoryByDate, HistorySection } from '../history/HistoryGroup'

// 新增方法
private getHistorySections(): HistorySection[] {
  return groupHistoryByDate(this.history, Date.now())
}
```

## 4. 数据模型

无变更。复用 `HistoryItem.timestamp: number`。

## 5. 可靠性分析 (FMEA)

| 故障模式 | 影响 | 严重度 | 改进措施 |
|----------|------|--------|---------|
| 时区切换 (用户跨时区旅行) | 分组边界偏移 | 低 | 使用设备本地时区 (Date.getFullYear 等),与 Android 一致;首次加载后跨时区罕见 |
| 系统时间被用户改回昨天 | 新条目归入"昨天"段 | 低 | 可接受行为,符合日历感 |
| 凌晨跨日时正打开面板 | 新打开的"今天"段为空 | 低 | 重新 `build()` 时即时计算,无需手动刷新 |
| 测试时 mock now 不准 | 单测结果不稳定 | 中 | 测试用 mock 时间,断言基于 **固定的 now** 与 items 数组,边界用例显式断言 |
| ListItem.Group API 在某些 ArkTS 版本不稳定 | 渲染异常 | 中 | 改用普通 ListItem + Row header (备选方案 A) |

## 6. DFX 简述

- **性能**: O(n) 单次遍历,n ≤ 100 默认,无瓶颈
- **可维护性**: 纯函数模块 + 完整单测,职责清晰
- **可扩展性**: 未来扩展 "本周"/"本月" 段时,只需扩 `HistoryGroupKey` 与 `groupHistoryByDate` 内部逻辑
- **兼容性**: PreferencesStore 数据格式不变,旧数据无缝迁移

## 7. 验收标准汇总

### 功能
- [x] 历史面板含 "今天" / "昨天" / "更早" 三段
- [x] 空段不渲染标题
- [x] 段内顺序与原数组一致 (newest-first)
- [x] 点击/滑删等交互行为不变

### 技术
- [x] 新增 `HistoryGroup.ets` 纯函数模块
- [x] 新增 `HistoryGroup.test.ets` 单元测试 ≥ 7 个用例
- [x] `hvigorw --no-daemon test` 通过
- [x] `harmonyos-ui-test` 真实截图覆盖三段均含记录场景
- [x] commit 含 `Signed-off-by:` (铁律 7)

## 8. 范围外

- 按月份/年份再细分 (后续 issue)
- 时间戳本地化显示 (后续 issue)
- 分组折叠/展开 (后续 issue)
- 多语言 i18n (与现有保持一致,不引入新字符串资源)
