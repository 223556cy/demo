# 代码仓理解 — Issue #17 粘贴即计算

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- 单元测试框架: hypium + hamock
- 测试根: opencalc/entry/src/test
- **UI 自动化测试能力: ✅ 可用 (hdc + 模拟器 127.0.0.1:5555)**
- hdc: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- hdc 版本: 3.2.0d
- 模拟器状态: running

## 1. 项目结构概览

```
opencalc/                                          # HarmonyOS OpenCalc 主项目
├── AppScope/app.json5
├── entry/
│   ├── build-profile.json5
│   ├── hvigorfile.ts
│   └── src/
│       ├── main/ets/
│       │   ├── calculator/                       # 计算引擎（纯逻辑）
│       │   │   ├── Calculator.ets               # CalcEngine 类（求值）
│       │   │   ├── Expression.ets               # Expression 类（预处理）
│       │   │   └── NumberFormatter.ets
│       │   ├── entryability/EntryAbility.ets
│       │   ├── model/
│       │   │   ├── ErrorFlags.ets
│       │   │   └── Models.ets
│       │   ├── pages/
│       │   │   ├── CalculatorPage.ets            # ⭐ 主战场
│       │   │   └── Index.ets
│       │   └── preferences/PreferencesStore.ets
│       ├── ohosTest/
│       └── test/ets/calculator/
│           └── Expression.test.ets
```

## 2. 关键文件分析

### 2.1 ⭐ CalculatorPage.ets（主战场）
**位置**：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（约 543 行）

**已就绪的可复用锚点**：

| 锚点 | 行号 | 类型 | 用途 |
|------|------|------|------|
| `import { pasteboard }` | L4 | import | 剪贴板 Kit（**已导入**） |
| `import { promptAction }` | L3 | import | Toast Kit（**已导入**） |
| `import { common }` | L5 | import | UIAbilityContext（**已导入**） |
| `@State expression` | L18 | @State @Watch | 表达式（**已 @Watch**） |
| `@State preview` | L19 | @State | 实时预览值 |
| `@State result` | L20 | @State | 计算结果 |
| `@State errorMsg` | L21 | @State | 错误信息 |
| `onExpressionChange()` | L74 | 回调 | @Watch 回调 |
| `computePreview()` | L86 | 私有方法 | 实时预览核心（**复用为校验函数**） |
| `isLastCharComputable()` | L143 | 私有方法 | 末字符判定 |
| `hasConsecutiveBinaryOperators()` | L161 | 私有方法 | 连续运算符检测 |
| `onEquals()` | L199 | 公开方法 | 等号计算（含 history 写入） |
| `onCopy()` | L222 | 公开方法 | 复制结果 |
| `ToggleRow()` | L385 | @Builder | 竖屏工具栏（**新增按钮位置**） |
| `DisplayPanel()` | L347 | @Builder | 显示屏 |
| `.gesture(LongPressGesture...)` | L380 | gesture | 已有长按手势 |

**关键发现**：
1. **零新增导入**：所有需要的 Kit 都已存在
2. **零新增状态联动**：expression 已是 @Watch 修饰，赋值即触发 preview
3. **零新增计算**：computePreview + onEquals 已覆盖所有计算需求
4. **history 写入自动**：onEquals 内自动 push HistoryItem

### 2.2 Expression.ets（复用）
- `getCleanExpression(calc, decSep, grpSep): string`
- 内置错误检测
- **完全复用**

### 2.3 Calculator.ets（复用）
- `CalcEngine.evaluate(clean: string, radianMode: boolean): number`
- **完全复用**

### 2.4 NumberFormatter.ets（复用）
- `NumberFormatter.format(raw, decSep, grpSep, sys): string`
- **完全复用**

### 2.5 ErrorFlags.ets（复用）
- 静态类：`snapshot()` / `restore()` / `reset()`
- **完全复用**

### 2.6 Expression.test.ets（测试样板）
- 使用 `import { describe, it, expect, beforeEach } from '@ohos/hypium'`
- `beforeEach` 重置 `ErrorFlags`
- `it('AC-N_xxx', N, () => {...})` 三参数形式
- **新测试沿用此模式**

## 3. 接口依赖关系

```
CalculatorPage.ets (MODIFIED) ──> pasteboard
                              ──> promptAction
                              ──> common
                              ──> Expression
                              ──> CalcEngine
                              ──> NumberFormatter
                              ──> ErrorFlags
                              ──> HistoryItem
                              ──> PreferencesStore
```

**对外依赖**：零新增
**新增对外调用**：
- `pasteboard.getSystemPasteboard().getData()` — 在 onPaste 内调用

## 4. 数据模型说明

**无新增数据模型**。

新增状态字段（全部为会话内 @State）：
- `@State lastPastedHash: number = 0` — 字符 code 累加 hash

## 5. 调用链分析

### 5.1 工具栏按钮 onClick 流程
```
用户点击「📋粘贴」
  └─> CalculatorPage.onPaste()
        └─> pasteboard.getSystemPasteboard().getData()
        └─> text.trim()
        └─> if (text === '') return          // FMEA-6
        └─> if (text.length > 200) text = text.substring(0, 200)  // FMEA-2
        └─> hash = computeHash(text)
        └─> if (hash === this.lastPastedHash) return  // FMEA-4
        └─> if (computePreview(text, this.radianMode) === '') {
              promptAction.showToast({ message: '非数学表达式' })
              return
            }
        └─> this.expression = text          // @Watch 自动触发 preview
        └─> this.onEquals()                  // 自动 push history
        └─> this.lastPastedHash = hash
```

### 5.2 onPageShow 流程
```
页面挂载 / 恢复
  └─> CalculatorPage.onPageShow()
        └─> (与 onPaste 相同的后续流程)
```

## 6. 可复用组件或函数

| 组件/函数 | 位置 | 用途 | 复用方式 |
|-----------|------|------|----------|
| `pasteboard.getSystemPasteboard().setData()` | CalculatorPage.onCopy | 写剪贴板 | **已实现** |
| `pasteboard.getSystemPasteboard().getData()` | Kit API | 读剪贴板 | **新增调用方** |
| `promptAction.showToast()` | CalculatorPage.onCopy | Toast 提示 | **复用** |
| `Expression.getCleanExpression()` | Expression.ets | 表达式预处理 | **复用** |
| `CalcEngine.evaluate()` | Calculator.ets | 表达式求值 | **复用** |
| `NumberFormatter.format()` | NumberFormatter.ets | 结果格式化 | **复用** |
| `ErrorFlags.snapshot/restore/reset` | ErrorFlags.ets | 错误隔离 | **复用** |
| `onEquals()` | CalculatorPage.ets:199 | 等号计算 + history | **复用** |
| `computePreview()` | CalculatorPage.ets:86 | 实时预览 | **复用为校验器** |

## 7. 风险识别

### 7.1 技术风险
| 风险 | 等级 | 原因 | 缓解 |
|------|------|------|------|
| ArkTS `pasteboard.getData()` API 调用方式 | 低 | Kit API 文档明确 | 仿照 onCopy 写反向 |
| `onPageShow` 生命周期钩子在 @Entry 中是否生效 | 中 | 需验证 ArkTS 实际行为 | 同时挂工具栏按钮作 backup |
| ArkTS `try/catch` 能否捕获 async 抛错 | 低 | 同步 API 不涉及 async | 同步调用即可 |
| 横屏 ToggleRow 不显示导致粘贴按钮不可见 | 中 | 已有问题，非本期引入 | onPageShow 兜底 |

### 7.2 测试能力评估
- **单元测试能力**: ✅（hypium 框架已可用，oh-package.json5 已声明 @ohos/hypium）
- **UI 自动化测试能力**: ✅（hdc + 模拟器 127.0.0.1:5555 + harmonyos-ui-test skill）
- **端到端集成测试能力**: ✅（可结合两者）

### 7.3 兼容性风险
- **新代码不删除任何现有功能**
- **不修改 computePreview / onEquals / pasteboard 任何既有调用**
- **不修改 Model / Calculator / Expression / NumberFormatter**
- **可安全 merge 到 main**

## 8. 关键决策点（已在 todo.md 拍板）

| # | 决策 | 自动拍板理由 |
|---|------|--------------|
| 1 | onPageShow + 工具栏按钮双触发 | 单一入口风险大；双保险 |
| 2 | 复用 onEquals + computePreview | 零新增计算逻辑，保持一致性 |
| 3 | lastPastedHash 简单累加 hash | 不引入 crypto 依赖；性能 O(n) 可接受 |
| 4 | Toast 仅在 NOT_MATH 时 | "零操作"哲学：失败最小反馈 |
| 5 | 不持久化 lastPastedHash | 退出后剪贴板可能变 |
| 6 | 仅支持纯数学，不含 NL 单位换算 | 单一职责 |

## 9. 缺失的依赖（无需新增）

- ✅ `pasteboard` Kit：CalculatorPage.ets L4 已导入
- ✅ `promptAction` Kit：CalculatorPage.ets L3 已导入
- ✅ `common` Kit：CalculatorPage.ets L5 已导入
- ❌ **无需新增**任何 Kit 依赖

## 10. 已有可参考的相似特性

### 10.1 复制（onCopy）作为反向参考
```typescript
onCopy(): void {
  if (this.result.length === 0) return
  pasteboard.getSystemPasteboard().setData(pasteboard.createData(pasteboard.MIMETYPE_TEXT_PLAIN, this.result))
  promptAction.showToast({ message: '已复制' })
}
```
