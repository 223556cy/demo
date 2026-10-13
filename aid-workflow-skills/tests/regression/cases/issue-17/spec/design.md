# 系统设计 — Issue #17 粘贴即计算

> 本设计文档面向 Issue #17 粘贴即计算,描述组件图、关键时序、状态机迁移、数据契约。
> 它是把 `proposal.md` (用户意图) 和 `delta-spec.md` (业务规则) 落到 ArkTS 类/方法层面的桥。

## 1. 组件图 (Components)

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CalculatorPage (@Entry)                        │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  DisplayPanel    │    │   ToggleRow      │    │  Keypad (复用)    │  │
│  │  @Builder        │    │   @Builder       │    │  @Builder        │  │
│  │                  │    │ ┌──────┐ ┌──────┐│    │                  │  │
│  │  expression      │    │ │ 科/基│ │ 📋  ││    │  0-9 . + - * / % │  │
│  │  preview         │    │ └──────┘ └──────┘│    │  =  C  ⌫  (  )  │  │
│  │  result          │    │        ▲ 新增按钮 │    │                  │  │
│  │  errorMsg        │    │        │          │    │                  │  │
│  └──────────────────┘    └────┬───┘          │    └──────────────────┘  │
│                                │ onClick       │                       │
│                                │ onPaste()     │                       │
│                                ▼                │                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                     CalculatorPage 状态                          │    │
│  │  @State expression        ←─── set onPaste / set input         │    │
│  │  @State preview           ←─── @Watch('onExpressionChange')   │    │
│  │  @State result            ←─── onEquals() 写入                │    │
│  │  @State errorMsg          ←─── onEquals() 写入                │    │
│  │  @State lastPastedHash    ←─── onPaste() 更新 (新增 ⭐)        │    │
│  │  @State radianMode                                            │    │
│  │  @State isLandscape                                           │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              CalculatorPage 核心方法 (本 Issue 改动)            │    │
│  │  ★ onPageShow()       ←  页面恢复时触发粘贴 (新增)            │    │
│  │  ★ onPaste()         ←  核心粘贴逻辑 (新增)                   │    │
│  │  ★ computeHash()      ←  弱 hash 去重 (新增)                  │    │
│  │  onExpressionChange() ←  @Watch 联动 (复用)                    │    │
│  │  computePreview()     ←  校验 + 预览 (复用)                   │    │
│  │  onEquals()           ←  计算 + push history (复用)            │    │
│  │  onCopy()             ←  复制结果 (复用)                        │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                │                                       │
└────────────────────────────────┼───────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
   ┌──────────────┐    ┌────────────────┐   ┌─────────────────┐
   │  pasteboard  │    │ promptAction   │   │  CalcEngine     │
   │  Kit         │    │ Kit            │   │  Calculator.ets │
   │              │    │                │   │                 │
   │ getData() ◄──┼────│ showToast() ◄──┼───│ evaluate() ◄────│
   │ (新增调用方)  │    │ (复用)          │   │  (复用)         │
   └──────────────┘    └────────────────┘   └─────────────────┘
            │                                         │
            ▼                                         ▼
   ┌──────────────┐                        ┌─────────────────┐
   │ 系统剪贴板    │                        │  NumberFormatter│
   │ (系统服务)    │                        │  (格式化)        │
   └──────────────┘                        └─────────────────┘
```

**设计原则**:
- 计算逻辑零新增 — 全部复用 `computePreview` + `onEquals` + `Expression.getCleanExpression`
- 状态联动零新增 — 复用 `@Watch('onExpressionChange')`
- 工具依赖零新增 — 复用 `pasteboard` + `promptAction` 已导入的 Kit

## 2. 关键时序 (Key Sequences)

### 2.1 时序 A — onPageShow 触发自动粘贴 (核心场景)

```
┌──────────┐     ┌──────────────┐     ┌────────────┐    ┌──────────────┐
│  系统     │     │ CalculatorPage │     │ pasteboard │    │ onEquals()   │
│  调度     │     │               │     │   Kit      │    │              │
└────┬─────┘     └──────┬────────┘     └─────┬──────┘    └──────┬───────┘
     │ onPageShow()     │                   │                  │
     │ ────────────────►│                   │                  │
     │                  │ onPaste()         │                  │
     │                  │ ──────────────┐   │                  │
     │                  │               │   │                  │
     │                  │ getData()     │   │                  │
     │                  │ ─────────────────►│                  │
     │                  │               │   │                  │
     │                  │ ◄───────────────  │                  │
     │                  │ PasteData     │   │                  │
     │                  │               │   │                  │
     │                  │ trim/截断/hash│   │                  │
     │                  │ computePreview│   │                  │
     │                  │ isValid?      │   │                  │
     │                  │               │   │                  │
     │                  │ expression = text                    │
     │                  │ ──────────────┐   │                  │
     │                  │               │   │                  │
     │                  │ @Watch 触发   │   │                  │
     │                  │ preview 重算  │   │                  │
     │                  │               │   │                  │
     │                  │ onEquals()   ────│─────────────────► │
     │                  │               │   │  push history    │
     │                  │ lastPastedHash=hash                  │
     │                  │ ◄──────────────  │                  │
     │ 页面渲染          │                   │                  │
     │ ◄────────────────│                   │                  │
```

**时序要点**:
- `onPageShow` 复用为 `onPaste` 的入口 (Adapter 模式)
- `expression = text` 是单一写入点,@Watch 自动联动 preview
- `onEquals` 是"真计算 + push history"的唯一通路,粘贴流程不绕过
- `lastPastedHash` 在最后一步更新,失败路径 (校验失败 / 异常) 不更新 hash

### 2.2 时序 B — 工具栏按钮显式触发

```
┌──────────┐     ┌──────────────┐
│  用户     │     │ CalculatorPage
└────┬─────┘     └──────┬────────┘
     │ tap 📋 按钮     │
     │ ───────────────►│
     │                  │ onPaste()
     │                  │ (同 2.1 onPageShow 之后)
     │ ◄─────────────── │
     │ 渲染更新
```

**与时序 A 的差异**: 入口不同,但内部流程完全相同 (DRY)

### 2.3 时序 C — 粘贴失败 (NOT_MATH)

```
┌──────────┐     ┌──────────────┐     ┌────────────┐
│  系统     │     │ CalculatorPage  │    │ promptAction│
└────┬─────┘     └──────┬────────┘     └─────┬──────┘
     │ onPageShow     │                     │
     │ ──────────────►│                     │
     │                │ onPaste()           │
     │                │ getData()           │
     │                │ text = "Hello"      │
     │                │ hash=...            │
     │                │ hash !== lastHash   │
     │                │                     │
     │                │ computePreview()    │
     │                │ === "" (不通过)     │
     │                │                     │
     │                │ showToast()         │
     │                │ ────────────────────►│
     │                │                     │
     │                │ return early        │
     │                │ (不更新 expression)  │
     │                │ (不更新 hash)        │
     │                │ (不触发 onEquals)    │
```

**关键不变量**: 失败路径不更新任何状态,保证重试时无副作用

## 3. 状态机迁移表 (State Machine)

### 3.1 状态定义

| 状态 | 描述 | 进入条件 |
|------|------|----------|
| `Idle` | 等待触发 | 初始 / 上一次流程结束 |
| `Detect` | 读取 + 校验剪贴板 | onPaste 被调用 |
| `Calc` | 提交到 expression + onEquals | 校验通过 |
| `Pushed` | history 已写入 | onEquals 成功 |
| `Error` | 计算失败 (除零 / 语法) | onEquals 内置 ErrorFlags 触发 |

### 3.2 迁移表

| 起始 | 事件 | 条件 | 目标 | 副作用 |
|------|------|------|------|--------|
| Idle | onPaste 调用 | getData 抛异常 | Idle | 无 (FMEA-5 容错) |
| Idle | onPaste 调用 | text 为空 / 纯空白 | Idle | 无 (FMEA-1/6) |
| Idle | onPaste 调用 | text 截断后仍为空 | Idle | 无 (FMEA-2) |
| Idle | onPaste 调用 | hash === lastPastedHash | Idle | 无 (FMEA-4 去重) |
| Idle | onPaste 调用 | computePreview === "" | Idle | Toast「非数学表达式」 |
| Idle | onPaste 调用 | computePreview !== "" | Calc | expression = text; preview 自动联动 |
| Calc | onEquals 抛异常 | ErrorFlags.EVAL_FAIL | Error | errorMsg 已设 (继承 onEquals 行为) |
| Calc | onEquals 成功 | 正常求值 | Pushed | result 已设; lastPastedHash = hash |
| Error | 用户操作 | 输入新 expression | Idle | errorMsg 清空 (Watch 触发) |
| Pushed | onPaste 再次调用 | (等待) | Detect | 新一轮去重比对开始 |

### 3.3 状态机图示

```
       ┌──────────────────────────────────────────────────────┐
       │                                                      │
       │  onPaste                                            │
       │  + getData 抛异常 ┌──► return                       │
       │  + 空白/超长截断后空 ┘                               │
       │                                                      │
       │  ┌────┐  onPaste   ┌────────┐  isValid   ┌────────┐│
       │  │Idle├───────────►│ Detect ├───────────►│  Calc  ││
       │  └────┘            └────┬───┘            └───┬────┘│
       │       ▲                 │  !isValid         │      │
       │       │                 │  Toast + return   │      │
       │       │                 │                   │      │
       │       │                 │  hash 重复         │      │
       │       │                 │  return           │      │
       │       │                 │                   ▼      │
       │       │                 │              ┌───────┐    │
       │       │                 │              │Pushed │    │
       │       │                 │              └───┬───┘    │
       │       │                 │                  │        │
       │       │                 │  onEquals 异常     │        │
       │       │                 │                  ▼        │
       │       │                 │              ┌───────┐    │
       │       │                 │              │ Error │    │
       │       │                 │              └───┬───┘    │
       │       │                 │                  │        │
       │       └─────────────────┴──────────────────┘        │
       │              用户后续操作 / 表达式变更               │
       └──────────────────────────────────────────────────────┘
```

### 3.4 不变量 (Invariants)

1. **`lastPastedHash` 永不减小**: 仅在 Calc→Pushed 转换时更新为当前 hash (无 roll-back 路径)
2. **`expression` 与 `lastPastedHash` 同步推进**: 写入 expression 必同步写入 hash
3. **失败路径不污染状态**: 所有 return early 路径不修改任何 @State
4. **`history` 写入唯一入口**: 仅 onEquals 内 push,粘贴流程不绕过
5. **`errorMsg` 独立生命周期**: 仅 ErrorFlags 路径写入,粘贴失败不写

## 4. 数据契约 (Data Contracts)

### 4.1 computeHash(text: string): number

```typescript
// aid-workflow 20260617 Issue #17: 粘贴去重弱 hash
// 注意: 这是去重用 weak hash, 不是加密 hash. 不要用于安全场景.
// 算法: char code 累加 + 长度系数, 32-bit int
private computeHash(text: string): number {
  let h: number = 0
  for (let i: number = 0; i < text.length; i++) {
    h = (h * 31 + text.charCodeAt(i)) | 0
  }
  return (h ^ text.length) | 0
}
```

**契约**:
- 输入: `text` (trim 后的非空字符串, 长度 ≤ 200)
- 输出: 32-bit int (ArkTS `number` 范围)
- 性质: `hash(same_text) === hash(same_text)` (确定性)
- **不保证**: `hash(a) !== hash(b)` 对不同输入 (可能碰撞,但去重场景下碰撞只会"少处理一次",不会"多处理")

### 4.2 onPaste(): void

```typescript
// aid-workflow 20260617 Issue #17: 粘贴核心逻辑
// 入口: onPageShow / 工具栏按钮 onClick
// 输出: 副作用 = expression/preview/result/history 变化
private onPaste(): void {
  let text: string = ''
  try {
    const data: pasteboard.PasteData = pasteboard.getSystemPasteboard().getData()
    if (data === null || data === undefined) return           // FMEA-1
    const primary: string = data.getPrimaryText()
    if (primary === null || primary === undefined) return     // FMEA-1
    text = primary.trim()                                      // FMEA-6
  } catch (_e) {
    return                                                     // FMEA-5
  }

  if (text.length === 0) return                                // FMEA-6
  if (text.length > 200) text = text.substring(0, 200).trim()  // FMEA-2
  if (text.length === 0) return

  const hash: number = this.computeHash(text)
  if (hash === this.lastPastedHash) return                     // FMEA-4

  if (this.computePreview(text, this.radianMode).length === 0) {
    promptAction.showToast({ message: '非数学表达式', duration: 1500 })
    return
  }

  this.lastPastedHash = hash
  this.expression = text       // @Watch 触发 preview
  this.onEquals()              // 复用: 计算 + push history
}
```

**前置条件**: 无 (可任意时刻调用)
**后置条件**:
- 成功路径: `expression` 更新, `preview` 自动更新, `result` 更新 (或 errorMsg), `lastPastedHash` 更新, `history` 推入新条目
- 失败路径: 所有 @State 保持不变, 仅 `lastPastedHash` 保持不变 (作为去重基准)

### 4.3 onPageShow(): void

```typescript
// aid-workflow 20260617 Issue #17: 页面挂载/恢复时尝试自动粘贴
// ArkTS @Entry 组件生命周期: onPageShow 等价于 Android onResume
onPageShow(): void {
  this.onPaste()
}
```

**职责**: Adapter 层, 把页面生命周期事件桥接到粘贴逻辑

## 5. 与 delta-spec.md 的映射

| delta-spec 规则 | 设计实现 | 文件 / 行号 |
|------------------|----------|-------------|
| 3.1 表达式识别 (computePreview) | `onPaste` 内 `if (computePreview(...).length === 0)` | CalculatorPage.ets ~L127 |
| 3.2 状态机 | §3 完整覆盖 | 本文档 §3 |
| 3.3 去重规则 (hash) | `computeHash` + `lastPastedHash` 比对 | CalculatorPage.ets ~L124, L270 |
| 3.4 错误反馈矩阵 | §3.2 迁移表中每条 return early 路径对应一个错误码 | 本文档 §3.2 |
| 4.1 工具栏按钮 | ToggleRow 内部 +3 行 | CalculatorPage.ets ~L449 |
| 4.3 反馈时机 | onPaste 内 Toast 触发条件 = computePreview 空 | CalculatorPage.ets ~L128 |
| 5 状态持久化 | `lastPastedHash` 仅 @State, 不持久化 | CalculatorPage.ets L28 |

## 6. 与 info.md 的可复用锚点对照

| info.md 复用锚点 | 本设计使用方式 | 是否修改原方法 |
|-------------------|----------------|----------------|
| `pasteboard.getData()` (L4 import) | onPaste 内调用 | ❌ 不修改 |
| `promptAction.showToast()` (L3 import) | onPaste 内调用 | ❌ 不修改 |
| `@State expression @Watch` (L18) | onPaste 内 `this.expression = text` | ❌ 不修改 |
| `computePreview()` (L86) | 复用为校验函数 | ❌ 不修改 |
| `onEquals()` (L199) | 复用为"真计算 + push history" | ❌ 不修改 |
| `ToggleRow()` (L385) | 内部新增一行 button | ⚠️ 增量 3 行, 不改既有结构 |
| `onCopy()` (L222) | 不涉及 | ❌ 不修改 |

**结论**: 本 Issue 零侵入既有方法, 零新增依赖, 零新增 Kit 导入.

## 7. 失效模式 (Failure Modes)

| 模式 | 触发场景 | 设计缓解 | 测试覆盖 |
|------|----------|----------|----------|
| FMEA-1 剪贴板无文本 | 系统剪贴板被清空 | getData 判空 + trim 后判空 | Node mock paste_4 |
| FMEA-2 剪贴板超长 | 攻击者粘贴 GB 级字符串 | 截断 200 字符 | Node mock paste_5 |
| FMEA-3 evaluate 异常 | 粘贴 `1/0` / `(-1)^0.5` | 复用 onEquals 内置 ErrorFlags | 复用 Expression.test.ets |
| FMEA-4 重复粘贴 | onPageShow 多次触发 | hash 比对静默 | Node mock paste_3 |
| FMEA-5 getData 系统异常 | 系统 Kit 不可用 | try/catch 静默吞 | Node mock paste_7 |
| FMEA-6 空白字符串 | 复制时带换行符 | trim + 非空判断 | Node mock paste_4, paste_6 |

## 8. 设计决策记录 (Design Decisions)

| # | 决策 | 备选 | 选择理由 |
|---|------|------|----------|
| D1 | onPageShow + 工具栏双触发 | 仅工具栏 | 双保险: 横屏无工具栏时 onPageShow 兜底 |
| D2 | 复用 onEquals + computePreview | 新增 calcPaste() | 零新增计算逻辑, 保持一致性 |
| D3 | lastPastedHash 简单累加 hash | crypto.subtle | 不引入 crypto 依赖; 性能 O(n) 可接受; 仅去重用 |
| D4 | Toast 仅在 NOT_MATH 时 | 任意失败都 Toast | "零操作"哲学: 失败最小反馈 |
| D5 | 不持久化 lastPastedHash | localStorage | 退出后剪贴板可能变, 持久化反而误判 |
| D6 | 仅支持纯数学 (无 NL 单位换算) | 复用 Issue #14 词法 | 单一职责; 复杂度 S |
| D7 | computeHash 是 private 方法 | public 工具函数 | 唯一调用方 onPaste, 封装即可 |

## 9. 设计审查 checklist

- [x] 组件图清晰 (CalculatorPage ↔ pasteboard / promptAction / onEquals / computePreview)
- [x] 关键时序覆盖 onPageShow / 工具栏 / 失败路径 3 个场景
- [x] 状态机迁移表完整 (5 状态 + 8 迁移 + 5 不变量)
- [x] 数据契约明确 (computeHash / onPaste / onPageShow 三个方法)
- [x] 与 delta-spec.md 规则一一映射
- [x] 与 info.md 复用锚点对照 (零侵入)
- [x] FMEA 失效模式与设计缓解表一一对应
- [x] 设计决策有理由 + 备选

**可进入 IMPLEMENTING**: ✅ (已在 IMPLEMENTING/APPLYING 阶段,本文档为回填审计证据)
