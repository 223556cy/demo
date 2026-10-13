# Info — 历史搜索框 (Issue #24)

> AID PLANNING step5 产出 · 代码仓理解

## 1. 基本信息

- **需求类别**: 新增功能 (View 增量,无架构变更)
- **需求名称**: 历史搜索框
- **分析时间**: 2026-06-17
- **分析范围**: pages/CalculatorPage.ets (HistoryPanel), history/HistoryGroup.ets, model/Models.ets, preferences/PreferencesStore.ets, test/ets/history/

## 2. 环境能力（来自 .claude/capabilities.json）

- **项目类型**: HarmonyOS
- **平台**: Windows
- **bundleName**: com.darkempire78.opencalculator
- **编译命令**: hvigorw --no-daemon assembleHap
- **单元测试命令**: hvigorw --no-daemon test (hypium + hamock)
- **UI 自动化测试能力**: ✅ 可用 (harmonyos-ui-test skill)
- **模拟器列表**: 127.0.0.1:5555
- **hdc 路径**: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- **测试根目录**: opencalc/entry/src/test

## 3. 架构分析

```
entry/src/main/ets/
├── pages/
│   ├── CalculatorPage.ets    # 主页面 (@Entry), 含 HistoryPanel
│   └── LongPressMenu.ets     # 长按菜单 (#16)
├── history/
│   └── HistoryGroup.ets      # 历史分组纯函数 (#15)
├── model/
│   └── Models.ets            # HistoryItem 接口定义
├── preferences/
│   └── PreferencesStore.ets  # @ohos.data.preferences 封装
├── calculator/               # 表达式 + 引擎 + 格式化
├── common/                   # NL 解析 + 单位换算
└── qrcode/                   # 二维码 (#13)
```

- **入口组件**: `CalculatorPage` (单页面应用)
- **历史状态**: `@State history: HistoryItem[]`, `@State showHistory: boolean`
- **历史持久化**: `PreferencesStore.getHistory() / setHistory()`
- **历史分组** (#15): `history/HistoryGroup.ets` 纯函数模块

## 4. 接口/契约识别

### 4.1 数据模型 `HistoryItem` (model/Models.ets)
```typescript
export interface HistoryItem {
  id: number           // 唯一标识
  expression: string   // 算式 (含数字/运算符/函数名/单位等)
  result: string       // 计算结果 (已格式化字符串)
  timestamp: number    // ms epoch
}
```

### 4.2 现有分组接口 `HistoryGroup.ets` (#15)
```typescript
export enum HistoryGroupKey { TODAY, YESTERDAY, EARLIER }
export interface HistorySection { key, title: string, items: HistoryItem[] }
export function groupHistoryByDate(items: HistoryItem[] | null | undefined, now: number): HistorySection[]
```

### 4.3 HistoryPanel 渲染 (CalculatorPage.ets:676-715)
- 折叠手柄 (24dp) → List → 段标题(可选) → ListItem (item.expression + item.result)
- `swipeAction` 滑出"删除"按钮
- `getHistorySections()` 即时计算分组(无缓存)
- 点击 `onHistoryTap(item)` → 回填 expression + 关闭面板

## 5. 公共组件或函数识别 (可复用)

| 名称 | 位置 | 复用方式 |
|------|------|---------|
| `groupHistoryByDate()` | history/HistoryGroup.ets | 在过滤后的 items 上复用,保持分组结构 |
| `HistorySection`, `HistoryGroupKey` | 同上 | 复用接口 |
| `mkItem()` 测试工具 | test/ets/history/HistoryGroup.test.ets | 复用为测试 fixture |
| `harmonyos-ui-test` skill | .claude/skills/ | UI 自动化测试复用 |
| hdc.exe (3.2.0d) | DevEco SDK | UI 测试工具 |

## 6. 影响范围分析

| 模块 | 文件 | 变更类型 | 说明 |
|------|------|---------|------|
| 纯函数模块 | `history/HistorySearch.ets` (新) | new | 过滤逻辑独立可测 |
| 主页面 | `pages/CalculatorPage.ets` | modify | HistoryPanel 顶部加 SearchBox;增加 @State searchQuery;改 getHistorySections() 先过滤再分组 |
| 单元测试 | `test/ets/history/HistorySearch.test.ets` (新) | new | TDD RED-GREEN 驱动 |
| UI 测试 | `specs/changes/.../ui-tests/` (新) | new | hdc 驱动模拟器验证 |
| 设计文档 | `delta-design.md` (新) | new | 组件设计 |
| 设计审视 | `design-review.md` (新) | new | step9 产出 |

**调用链**:
```
用户输入 → TextInput.onChange → this.searchQuery = q (State)
         → build() 重新执行 → getHistorySections() 调用 filterHistoryByQuery → groupHistoryByDate
         → List 重渲染 (含段标题 + 匹配项)
         → 无结果时显示 "无匹配记录"
```

**无破坏性**:
- PreferencesStore 不变
- groupHistoryByDate 不变
- 现有 #15 分组行为不变 (空查询时过滤是 no-op)
- 现有 #16/#17/#18 行为不变

## 7. 现有代码分析

**HistoryPanel 关键状态** (CalculatorPage.ets:29-32):
```typescript
@State history: HistoryItem[] = []
@State showHistory: boolean = false
```

**分组调用** (CalculatorPage.ets:382-386):
```typescript
getHistorySections(): HistorySection[] {
  return groupHistoryByDate(this.history, Date.now())
}
```

**List 渲染** (CalculatorPage.ets:689-707):
```typescript
List() {
  ForEach(this.getHistorySections(), (section: HistorySection) => {
    if (section.items.length > 0) {
      ListItem() { this.SectionHeader(section.title) }
      ForEach(section.items, (item: HistoryItem) => { ... })
    }
  })
}
```

**关键观察**:
- `getHistorySections()` 每次 build 时调用,无缓存 → 过滤逻辑加在内部开销可忽略
- ArkTS @State 装饰字段 → 修改 searchQuery 触发 build() 重渲染
- 现有输入控件(无): CalculatorPage 没有任何 TextInput

## 8. 风险识别

| 风险 | 等级 | 缓解 |
|------|------|------|
| TextInput 抢焦点导致 List 滚动受限 | low | 输入框 focus 不阻止 List 滚动 |
| 横屏时搜索框布局紧凑 | low | 搜索框 width=100%,padding 16 |
| 过滤函数性能 (history 数百条) | low | contains 是 O(n),n≤100 时 <1ms |
| 大小写不一致 | low | 统一 toLowerCase 比较 |
| 与 #15 分组兼容 | low | 过滤后调用 groupHistoryByDate,空查询直接透传 |
| 输入框 keyboard 弹起遮挡历史 | medium | 历史 List 是 scroll,内容可滚;但建议固定搜索框在顶部 |
| 用户长按复制/粘贴冲突 | low | searchbox 不响应 swipeAction |

### 测试能力评估
- **单元测试能力**: ✅ (hypium 框架已有 HistoryGroup.test.ets 模板)
- **UI 自动化测试能力**: ✅ (hdc + 模拟器 127.0.0.1:5555)
- **端到端集成测试能力**: ✅ (harmonyos-ui-test skill)
- **不能跑的实际原因**: N/A (全能力可用)

## 9. 测试验证策略

### 单元测试 (test/ets/history/HistorySearch.test.ets)
- TC-01: 空 query → 原样返回
- TC-02: query="12" → 匹配 expression 或 result 含 "12" 的 items
- TC-03: query="SIN" (大写) → 匹配 "sin" (大小写不敏感)
- TC-04: query="xxx" (无匹配) → 空数组
- TC-05: expression 含特殊字符 (π, e) → 正常匹配
- TC-06: result 含数字/逗号 → 正常匹配
- TC-07: query 含空格 → 视为子串 (e.g. "1 + 1" 匹配 "1+1"? 或精确?)
  - **决策**: 子串匹配(查询词去掉首尾空格后 contains)

### UI 测试 (specs/changes/.../ui-tests/)
- 打开历史面板 → 输入"2" → 验证只显示含 2 的项
- 验证 ✕ 清除按钮工作
- 验证无结果显示"无匹配记录"
- 验证清除后还原全部历史
- 验证分组标题在过滤后仍正确显示

### 回归
- 现有 HistoryGroup.test.ets 必须仍通过
- 现有 UI 截图测试: 竖屏+横屏历史面板显示不变(空查询时)

## 10. 监控运维支持

- 无需新增监控指标
- 无需新增配置项
- 无需新增日志点
- 搜索是纯 View 行为,无网络/存储副作用

## 11. 关键发现

### 可复用资产
- `groupHistoryByDate` 是纯函数,可直接复用 (HistoryGroup.ets:37)
- `HistorySection` 接口直接复用
- `mkItem` 测试 fixture 模式可复用
- harmonyos-ui-test skill 可驱动模拟器做 UI 验证

### 风险提示
- TextInput 是新增控件类型,需确认 ArkTS TextInput 在鸿蒙 4.0+ 的 onChange 行为
- history 列表的 size 由 PreferencesStore 决定,可能远大于 100;contains 性能可接受
- 现有 .port.mjs 模式 (HistoryGroup.port.mjs) 用于 Web 端对照测试;建议 HistorySearch 也建一个 .port.mjs 便于跨平台验证

### 建议事项
- **建议 1**: 过滤逻辑独立成 history/HistorySearch.ets,纯函数 + 单元测试驱动 (对齐 #15 风格)
- **建议 2**: 复用 #15 的 getHistorySections() 入口,内部先 filter 再 group (避免改外部接口)
- **建议 3**: ✕ 清除按钮用 Text('✕') + onClick,风格与 AboutPanel/SettingsPanel 一致
- **建议 4**: 无结果占位用 Text('无匹配记录') + fontSize 13 + 灰色,与"暂无计算记录"一致
- **建议 5**: searchQuery 状态放 CalculatorPage 内,无需全局状态
- **建议 6**: UI 测试覆盖搜索流程,evidence 入 specs/changes/.../ui-tests/
