# Issue #5 计算历史搜索 — 代码仓理解

## 基本信息

- **需求类别**：新增功能（HistoryPanel 加搜索框）
- **需求名称**：计算历史搜索
- **分析时间**：2026-06-11
- **分析范围**：`opencalc/entry/src/main/ets/` 下 pages/CalculatorPage.ets、model/Models.ets、preferences/PreferencesStore.ets
- **分析人**：planner (aid-planning)

---

## 1. 架构分析

### 1.1 模块结构（ArkTS 声明式 UI 单 HAP）

```
opencalc/entry/src/main/ets/
├── pages/
│   ├── CalculatorPage.ets    ← @Entry 主页（包含 HistoryPanel）
│   └── Index.ets             ← Router 入口
├── calculator/               ← 纯计算逻辑层（无 UI 依赖）
│   ├── Calculator.ets        ← 表达式求值
│   ├── Expression.ets        ← 输入预处理
│   └── NumberFormatter.ets   ← 数字格式化
├── model/
│   ├── Models.ets            ← HistoryItem / Preferences 接口
│   └── ErrorFlags.ets
├── preferences/
│   └── PreferencesStore.ets  ← @ohos.data.preferences 封装
└── entryability/
    └── EntryAbility.ets
```

### 1.2 关键架构特点

- **无 ViewModel 层**：所有 UI 状态用 `@State` 内联在 `CalculatorPage` 内
- **单页面架构**：所有面板（History / Settings / About）都用 `@Builder` 内联在主页面，通过布尔 `@State` 控制显隐
- **无外部依赖**：无第三方 UI 库；搜索功能可直接使用 ArkUI 内置 `TextInput`

---

## 2. 现有代码分析

### 2.1 HistoryPanel 当前实现（`CalculatorPage.ets:311-346`）

```typescript
@Builder HistoryPanel() {
  Column() {
    // 1. 拖拽手柄 / 折叠按钮
    Row() {
      Text('').width(40).height(4).backgroundColor(this.getT2()).borderRadius(2)
    }
    .width('100%').height(24).justifyContent(FlexAlign.Center)
    .onClick((): void => { this.showHistory = false })

    // 2. 主体：空状态 OR 列表
    if (this.history.length === 0) {
      Text('暂无计算记录').fontSize(13).fontColor(this.getT2())...
    } else {
      List() {
        ForEach(this.history, (item: HistoryItem) => {
          ListItem() {
            Column() {
              Text(item.expression).fontSize(12).fontColor(this.getT2())...
              Text(item.result).fontSize(15)...
            }
            .onClick((): void => { this.onHistoryTap(item) })
          }
          .swipeAction({ end: { builder: (): void => { this.DelBtn(item) } } })
        })
      }
      .layoutWeight(1)
    }
  }
  .layoutWeight(this.isLandscape ? 1 : 0)
  .width('100%').height(this.isLandscape ? '100%' : 'auto')
  .backgroundColor(this.getPanelBg())
  .borderRadius(this.isLandscape ? 0 : { topLeft: 16, topRight: 16 })
}
```

### 2.2 关键变量与状态

| 变量 | 类型 | 用途 | 是否需修改 |
| ---- | ---- | ---- | ---------- |
| `history` | `@State HistoryItem[]` | 历史数据源（已持久化） | 不变（数据源） |
| `showHistory` | `@State boolean` | 历史面板显隐 | 不变 |
| `isLandscape` | `@State boolean` | 横竖屏标志 | 不变 |
| `nextId` | `private number` | 历史 id 递增 | 不变 |
| **新增** `searchQuery` | `@State string = ''` | 搜索关键字 | **新增** |
| **新增** `filteredHistory` | （派生）`HistoryItem[]` | 过滤后列表 | **新增**（可作为 getter 或 computed） |

### 2.3 关键方法

| 方法 | 用途 | 是否需修改 |
| ---- | ---- | ---------- |
| `onHistoryTap(item)` | 点击历史回填算式 | 不变 |
| `onHistoryDelete(item)` | 左滑删除 | 不变 |
| `loadHistory()` | 从 PreferencesStore 加载 | 不变 |
| `onEquals()` | 计算完成时新增 history | 不变（自动响应 `@State`） |

### 2.4 数据模型（`model/Models.ets:28-33`）

```typescript
export interface HistoryItem {
  id: number
  expression: string   // 算式，如 "sin(30)+5!"
  result: string       // 结果，如 "120.5"
  timestamp: number
}
```

- **无需修改模型**：搜索字段（expression、result）已存在
- 数据通过 `JSON.stringify/parse` 持久化到 `preferences`

### 2.5 持久化层（`preferences/PreferencesStore.ets:113-133`）

```typescript
async getHistory(): Promise<HistoryItem[]> {
  const json: string = await this.store.get('history', '[]') as string
  try { return JSON.parse(json) as HistoryItem[] } catch { return [] }
}

async setHistory(items: HistoryItem[]): Promise<void> {
  const maxSize: number = await this.getHistorySize()
  const trimmed: HistoryItem[] = items.slice(0, maxSize)
  await this.store.put('history', JSON.stringify(trimmed))
  await this.store.flush()
}
```

- **无需修改**：搜索是视图过滤，不写持久化
- 持久化数据格式（JSON 数组）保持兼容

---

## 3. 接口/契约识别

### 3.1 ArkUI TextInput 关键 API（用于搜索框）

| API | 用途 |
| --- | ---- |
| `TextInput({ placeholder: '...' })` | 搜索输入框 |
| `.onChange((value: string) => {...})` | 实时输入回调 |
| `.cancelIcon({ icon: ..., callback: ... })` | 右侧 X 清空按钮（ArkUI 11+） |
| `.type(InputType.Normal)` | 普通文本输入 |
| `.width('100%')` `.height(40)` `.backgroundColor(...)` | 样式 |

**注**：若 `cancelIcon` API 在目标 HarmonyOS API 版本不可用，可降级为 `.onClick` 的 Text 按钮。

### 3.2 数据流契约

```
User Input (TextInput.onChange)
  ↓
@State searchQuery 更新
  ↓
filteredHistory = filter(history, searchQuery)  ← 派生计算
  ↓
List 重新渲染 filteredHistory
```

---

## 4. 公共组件或函数识别

### 4.1 主题色函数（可直接复用）

`CalculatorPage.ets` 已有一组主题色 getter，可在搜索框样式中直接复用：

- `getBg()` / `getBtnBg()` / `getPanelBg()` / `getT1()` / `getT2()` / `getOp()`

例如：搜索框背景用 `getBtnBg()`，占位符文字用 `getT2()`。

### 4.2 无需新增 utility

- 过滤函数足够简单（4 行），可内联在 `HistoryPanel` 内或作为 private getter
- 不必新增 `utils/SearchFilter.ets` 单独文件（避免过度设计）

---

## 5. 影响范围分析

### 5.1 需要修改的文件

| 文件 | 修改类型 | 影响行数 | 说明 |
| ---- | -------- | -------- | ---- |
| `CalculatorPage.ets` | modify | +40~60 | 新增 `@State searchQuery` + `HistoryPanel` 内插 TextInput + 过滤逻辑 |

**单文件改动**，符合简单需求 S 级复杂度。

### 5.2 不需要修改的文件

- `model/Models.ets`：数据模型不变
- `preferences/PreferencesStore.ets`：持久化接口不变
- `calculator/*.ets`：计算逻辑不涉及
- `entryability/EntryAbility.ets`：入口不变

### 5.3 调用链影响

```
onEquals() → history.push(item) → 持久化
                                        ↓
                            触发 @State 响应式更新
                                        ↓
                            filteredHistory 重新计算
                                        ↓
                            List 重新渲染
```

无副作用影响：`onHistoryTap` / `onHistoryDelete` 行为完全保留。

### 5.4 兼容性

- **横竖屏**：HistoryPanel 已在两种布局下使用同一 `@Builder`，搜索框无影响
- **主题**：复用现有 `getT1/getT2/getBtnBg`，三种主题（浅/暗/AMOLED）自动适配
- **数据迁移**：持久化 JSON 格式不变，升级无需数据迁移

---

## 6. 风险识别

| 风险 | 等级 | 描述 | 缓解 |
| ---- | ---- | ---- | ---- |
| 大量历史时 filter 卡顿 | 低 | 100 条以内，string.includes 单次调用 < 1ms | 不需要 debounce；如未来超 1000 条再加 |
| ArkUI `cancelIcon` API 兼容性 | 低 | ArkUI 11+ 才有 | 降级方案：右侧手动加 `Text('✕')` + onClick |
| 搜索状态意外持久化 | 低 | 开发失误可能把 searchQuery 写入 prefs | code review 关注：searchQuery 必须 @State（不入库） |
| 正则元字符注入 | 低 | 用户输入 `(30)`、`*`、`?` 等 | 用 `String.includes()` 而非 `RegExp`（已在 FM-002-01 覆盖） |
| trim 后空白 query 误判 | 低 | 全文空白被识别为"有 query"导致空列表 | 过滤前先 `query.trim()`，trim 后为空视为无 query |
| 中文/特殊字符搜索 | 低 | 现有 string.includes 自然支持 Unicode | 单元测试覆盖 |

---

## 7. 测试验证策略

### 7.1 单元测试（建议添加）

- `filterHistory(history, query): HistoryItem[]` 函数纯函数测试
  - 命中 expression
  - 命中 result
  - 大小写不敏感
  - trim 空白
  - 正则元字符不抛错
  - 极长 query 截断

### 7.2 手工验证

| 场景 | 验证点 |
| ---- | ------ |
| SC-001 空历史 | 首次启动展开历史，无搜索框，显示"暂无计算记录" |
| SC-002 主流程 | 输入 "sin" 实时过滤 |
| SC-003 无匹配 | 输入 "xyz123abc" 显示"无匹配记录" |
| SC-004 清空 | 点击 X 立即恢复全量 |
| SC-005 大小写 | "SIN" 与 "sin" 效果一致 |
| SC-006 新增 | 搜索中完成新计算，新条目按当前 query 过滤 |
| SC-007 删除 | 搜索结果左滑删除，持久化 |
| SC-008 横屏 | 横屏下搜索框位置、行为一致 |

### 7.3 回归范围

- `onHistoryTap`：回填行为不变
- `onHistoryDelete`：删除 + 持久化不变
- `onEquals`：新增 history 行为不变
- 横/竖屏切换、主题切换：均无影响

---

## 8. 监控运维支持

**不涉及**（单机纯前端功能，无远程监控需求）

---

## 9. 关键发现

### 9.1 可复用资产

- 主题色 getter（`getT1/getT2/getBtnBg`）— 直接复用
- 现有 `@State history` — 直接作为过滤源
- ArkUI `TextInput` 内置 cancelIcon — 零成本实现清空按钮

### 9.2 风险提示

- 必须保证 `searchQuery` 是 `@State`（不入库），不要误用 `@StorageLink` 或 `AppStorage`
- 必须用 `String.includes` 而非 `RegExp`（FM-002-01）
- 必须 `query.trim()` 后再判断（FM-002-04）

### 9.3 实施建议

1. 在 `CalculatorPage` 顶部新增 `@State searchQuery: string = ''`
2. 在 `HistoryPanel()` 内：手柄之后、列表之前插入 `TextInput`
3. 用条件分支：`history.length === 0` → 空状态；`searchQuery 非空 且 filtered 为空` → 无匹配；否则渲染 List(filtered)
4. 提取 `getFilteredHistory()` 作为 private getter，返回过滤后数组
5. 推荐将过滤逻辑独立成纯函数便于单元测试
