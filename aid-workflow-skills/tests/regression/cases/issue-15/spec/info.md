# 历史日期分组 - 代码仓理解

> AID PLANNING step5 产出 (rq-codebase) · 自动模式

## 1. 基本信息

- **需求类别**：新增功能 (`requirement-add`)
- **需求名称**：历史列表支持按日期分组
- **分析时间**：2026-06-16
- **分析范围**：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (HistoryPanel 内联段), 新增 `entry/src/main/ets/history/HistoryGroup.ets` 纯函数模块

## 2. 环境能力 (来自 .claude/capabilities.json)

- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: `com.darkempire78.opencalculator`
- 编译命令: `hvigorw --no-daemon assembleHap`
- 单元测试命令: `hvigorw --no-daemon test`
- 测试框架: hypium+hamock, 测试根目录 `opencalc/entry/src/test`
- **UI 测试能力: ✅ 可用 (hdc + 模拟器)**
- 模拟器: `127.0.0.1:5555` (running)
- hdc 路径: `D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe`
- Java: openjdk 21.0.8, hvigorw 6.24.2

## 3. 架构分析

### 现有模块结构
```
entry/src/main/ets/
├── pages/
│   └── CalculatorPage.ets        ← @Entry 主页面,内联 HistoryPanel (lines 441-479)
├── calculator/                    ← 计算引擎 (与本次需求无关)
├── model/
│   └── Models.ets                 ← HistoryItem 接口 (line 27-33), 含 timestamp: number
├── preferences/
│   └── PreferencesStore.ets       ← getHistory()/setHistory() 持久化 (与本次需求无关)
└── entryability/
    └── EntryAbility.ets
```

### 关键发现
- **HistoryPanel 是 CalculatorPage 的内联 @Builder** (CalculatorPage.ets:441-479),不是独立组件文件
- 数据源 `this.history: HistoryItem[]` (line 23)
- 渲染方式 `List() + ForEach(this.history, item => ListItem...)` (line 454-466)
- HistoryItem.timestamp 是 `number` (epoch ms),已在 `onEquals` 中写入 `Date.now()` (line 212)

### 模块依赖关系
```
HistoryPanel (View)
    └─ ForEach(this.history: HistoryItem[])
         └─ HistoryItem.timestamp ← Date.now() (写入)
              └─ PreferencesStore.setHistory() (持久化)
```

## 4. 接口/契约识别

| 接口 | 位置 | 契约 |
|------|------|------|
| `HistoryItem` | `model/Models.ets:27-33` | `{id, expression, result, timestamp}` |
| `loadHistory()` | `CalculatorPage.ets:56-60` | 从 PreferencesStore 读取,赋给 `this.history` |
| `onEquals()` | `CalculatorPage.ets:198-220` | 计算后 prepend 新条目到 `this.history` |
| `onHistoryDelete()` | `CalculatorPage.ets:229-234` | 滑删后持久化 |
| `HistoryPanel()` | `CalculatorPage.ets:441-474` | 渲染 List |

## 5. 公共组件/函数识别 (可复用)

| 名称 | 位置 | 用途 |
|------|------|------|
| `HistoryItem` | model/Models.ets | 已有 timestamp 字段,**无需新增模型** |
| `List()` + `ForEach` | ArkUI 原生 | 现有渲染结构,**直接复用** |
| `ListItem.swipeAction()` | ArkUI 原生 | 滑删行为,**保留不动** |

## 6. 影响范围分析

### 需要修改的文件 (1)
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
  - `HistoryPanel()` @Builder (lines 441-479): 渲染逻辑从直接 `ForEach` 改为遍历已分组数据
  - 新增 `private historySections: HistorySection[] = []` 字段 (或在 build 时即时计算)
  - 新增 `private computeHistorySections(): HistorySection[]` 方法

### 需要新增的文件 (2)
- `opencalc/entry/src/main/ets/history/HistoryGroup.ets`: 纯函数模块,导出 `groupHistoryByDate(items, now)` 和 `HistorySection` 类型
- `opencalc/entry/src/test/ets/history/HistoryGroup.test.ets`: 单元测试

### 调用链分析
```
loadHistory() → this.history: HistoryItem[]
                  ↓
        (新增) computeHistorySections(this.history, Date.now())
                  ↓
            HistorySection[]
                  ↓
        HistoryPanel() 渲染 (ListItem.Group 或分隔 Row)
```

### 兼容性
- HistoryItem 接口不变
- PreferencesStore 不变
- 滑删/点击交互不变

## 7. 现有代码分析

### HistoryPanel 渲染逻辑 (CalculatorPage.ets:454-466)
```typescript
List() {
  ForEach(this.history, (item: HistoryItem) => {
    ListItem() {
      Column() {
        Text(item.expression).fontSize(12).fontColor(this.getT2()).maxLines(1)
        Text(item.result).fontSize(15).fontWeight(FontWeight.Bold).fontColor(this.getOp())
      }
      .alignItems(HorizontalAlign.Start).width('100%').padding(this.isLandscape ? 8 : 12)
      .onClick((): void => { this.onHistoryTap(item) })
    }
    .swipeAction({ end: { builder: (): void => { this.DelBtn(item) } } })
  })
}
.layoutWeight(1)
```

### 边界条件
- 空数组 → "暂无计算记录" (line 451-452)
- 横屏: 全屏高度; 竖屏: auto 高度 (line 471)
- 主题色: `getPanelBg()` / `getT1()` / `getT2()` / `getOp()` (line 472)

## 8. 风险识别

| 风险 | 等级 | 缓解 |
|------|------|------|
| 时区/夏令时差异 | 低 | 使用本地日历日 `getFullYear/getMonth/getDate` (设备本地时区),与 Android DateUtils.isToday 行为一致 |
| 大量历史记录性能 | 低 | 单次 O(n) 遍历,n 默认上限 100 (PreferencesStore.historySize) |
| ListItem.Group 在 ArkTS 中支持度 | 中 | 优先用普通 ListItem + Row header (更可控),如 Group API 可用则用之 |
| ArkTS 静态检查严格性 | 低 | 复用现有 `@Builder` 模式,forEach 必须加 `keyGenerator` |
| 分组计算时机 | 低 | 在 build 前用 `@State` 同步计算,避免异步导致 UI 抖动 |

### 测试能力评估
- 单元测试能力: ✅ (hypium+hamock, hvigorw test)
- UI 自动化测试能力: ✅ (hdc 路径已配置, 模拟器 running)
- 端到端集成测试能力: ✅ (harmonyos-ui-test skill 可用)

## 9. 测试验证策略

### 单元测试场景 (HistoryGroup.test.ets)
1. 空数组 → 3 个空段
2. 全部今天 (3 条) → 仅今天段有数据
3. 全部昨天 (2 条) → 仅昨天段有数据
4. 全部更早 (5 条) → 仅更早段有数据
5. 跨三天 (今天 2 + 昨天 1 + 前天 1) → 三段均有数据
6. 边界 00:00:00 → 跨日正确分组
7. 段内顺序保持 newest-first

### UI 测试场景 (harmonyos-ui-test)
- 至少一条今天 + 至少一条昨天 + 至少一条更早时,三个标题都可见
- 截图中可见 "今天" / "昨天" / "更早" 三个中文字符串
- uiautomator dump 包含三个标题文本

### 回归测试
- 历史点击回填 expression 仍生效
- 滑删仍生效
- 横屏/竖屏布局未破坏

## 10. 关键发现

### 可复用
- ✅ `HistoryItem.timestamp` 字段已存在,无需模型变更
- ✅ ArkUI `List` + `ForEach` 渲染框架可直接复用
- ✅ 主题色 getter 系列可直接复用

### 风险提示
- ⚠️ 旧代码无分组逻辑,需新增纯函数模块 + 集成测试
- ⚠️ ListItem.Group 在不同 ArkTS 版本 API 稳定性需验证

### 建议事项
- 📌 纯函数模块便于单测 (`groupHistoryByDate`)
- 📌 段标题用静态中文 "今天" / "昨天" / "更早",无需 i18n 改造
- 📌 commit 用 `-s` 满足铁律 7
