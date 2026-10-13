# 增量需求规格 — Issue #17 粘贴即计算

> 本文档为 OpenCalc HarmonyOS 的**增量规格**，仅描述 Issue #17 引入的变更。

## 1. 范围与目标

### 1.1 范围
**包含**：
- 从系统剪贴板读取文本内容
- 校验文本是否为可求值的数学表达式
- 自动填入 expression + 触发计算 + 写入历史
- 静默去重（同一内容不重复处理）
- 工具栏「📋粘贴」按钮（用户显式触发）
- 页面挂载/恢复时自动检测（onPageShow）
- Toast 反馈（仅失败时）

**不包含**：
- 撤销粘贴
- 富文本/HTML 剪贴板
- 单位换算
- 跨设备同步

### 1.2 目标用户
- **主要**：从微信/浏览器/Notion/邮件等 App 复制算式后想快速验算的用户
- **典型场景**：购物比价、复利计算、单位混合运算

### 1.3 成功指标
- 用户从复制到看到结果**零点击**（页面已经在前台时）
- 用户从复制到看到结果**一次点击**（页面不在前台时回到应用一次）
- 重复触发 0 次副作用（无历史污染、无 Toast 噪音）

## 2. 需求用例

### 2.1 UC-1 自动粘贴计算（核心场景）
- **前置条件**：用户已在系统其他 App 复制了 `2+3`
- **操作流程**：
  1. 用户切回 OpenCalc
  2. （onPageShow 触发）
- **预期结果**：
  - expression 显示 `2+3`
  - preview 显示 `5`
  - result 显示 `5`
  - history 第一条新增 `{id:N, expression:"2+3", result:"5", timestamp:...}`

### 2.2 UC-2 工具栏显式粘贴
- **前置条件**：剪贴板有 `10*20%`
- **操作流程**：
  1. 用户在 OpenCalc 界面点击「📋粘贴」按钮
- **预期结果**：
  - expression 显示 `10*20%`
  - result 显示 `2`
  - history 新增对应条目

### 2.3 UC-3 粘贴非数学内容
- **前置条件**：剪贴板有 `Hello World`
- **操作流程**：
  1. 用户切回 OpenCalc
- **预期结果**：
  - Toast 显示「非数学表达式」（1.5s）
  - expression 不变
  - history 不变

### 2.4 UC-4 粘贴空白 / 极短内容
- **前置条件**：剪贴板有 `   ` 或空
- **操作流程**：
  1. 用户切回 OpenCalc
- **预期结果**：
  - 静默 return，无 Toast、无 UI 变化

### 2.5 UC-5 重复粘贴同一内容
- **前置条件**：剪贴板有 `2+3` 且 lastPastedHash === hash(`2+3`)
- **操作流程**：
  1. 用户切回 OpenCalc（第二次）
- **预期结果**：
  - 静默 return
  - history **不**新增条目

### 2.6 UC-6 粘贴时 expression 已有内容
- **前置条件**：expression 当前为 `1+1`，剪贴板有 `5*6`
- **操作流程**：
  1. 用户切回 OpenCalc（或点粘贴）
- **预期结果**：
  - expression 覆盖为 `5*6`
  - result 重算为 `30`
  - errorMsg 清空

### 2.7 UC-7 粘贴触发 onEquals
- **前置条件**：剪贴板有 `1/0`
- **操作流程**：
  1. 用户切回 OpenCalc
- **预期结果**：
  - expression 显示 `1/0`
  - errorMsg 显示「除数不能为零」
  - result 清空
  - history **不**新增

## 3. 业务规则

### 3.1 表达式识别规则
| 输入 | 是否识别为数学 | 备注 |
|------|----------------|------|
| `2+3` | ✅ | 基础算式 |
| `10*20%` | ✅ | 含百分号 |
| `sin(45)` | ✅ | 含函数 |
| `(1+2)*3` | ✅ | 含括号 |
| `3.14` | ✅ | 小数 |
| `1+` | ❌ | 末尾运算符不完整 |
| `+2` | ❌ | 开头运算符 |
| `1++2` | ❌ | 连续二元运算符 |
| `Hello` | ❌ | 含非数学字符 |
| ` ` (空白) | ❌ | 空 |
| `2+3\n` | ✅ | trim 后合法 |
| ` 2+3 ` | ✅ | trim 后合法 |
| 200+ 字符 | ✅（截断 200 字符） | FMEA-2 缓解 |

**识别策略**：复用 `computePreview(exprStr, radianMode)` 的判定逻辑 — 如果该函数能返回非空字符串，则认为可计算。

### 3.2 状态机

```
[Idle] -- onPageShow --> [Detect] -- getData 抛异常 --> [Idle]
                              │
                              ├─ 文本为空/空白/超长截断后空 --> [Idle] (return early)
                              │
                              ├─ hash === lastPastedHash --> [Idle] (return early)
                              │
                              └─ isValidMathExpression(expr) === false
                                          │
                                          └─> [Idle] (Toast: 非数学表达式)

[Detect] -- isValid === true --> [Calc]
                                     │
                                     ├─ onEquals 抛异常（语法/除零/定义域） --> [Error]
                                     │                                              │
                                     │                                              └─> [Idle] (errorMsg 已设)
                                     │
                                     └─ onEquals 成功 --> [Pushed]
                                                          │
                                                          └─> [Idle] (history+1, lastPastedHash 更新)
```

### 3.3 去重规则
- **key** = `text.trim()` 的字符串 hash（字符 code 累加 + 长度系数）
- **作用域** = 单次会话（lastPastedHash 是 @State，不持久化）
- **触发时机** = onPageShow 之前 + 工具栏按钮 onClick
- **静默条件** = hash 完全相同（含 trim 后）

### 3.4 错误反馈矩阵
| 错误码 | 来源 | UI 反馈 | 后台状态 |
|--------|------|---------|----------|
| `EMPTY` | 剪贴板空 / 纯空白 | 静默 | 无变化 |
| `TOO_LONG` | 截断后仍 > 200 字符 | 静默 | 无变化 |
| `NOT_MATH` | 不通过 computePreview 校验 | Toast「非数学表达式」 | 无变化 |
| `DUPLICATE` | hash 重复 | 静默 | 无变化 |
| `EVAL_FAIL` | evaluate 抛异常 | errorMsg（继承 onEquals 既有行为） | expression 保留 |
| `SYSTEM_ERR` | getData 抛异常 | 静默 | 无变化（容错） |

## 4. UI/UX 规格

### 4.1 工具栏按钮（新增）
- **位置**：ToggleRow 内，「科学/基础」按钮与「▼历史」之间
- **样式**：
  - 文字：`📋`（emoji 粘贴图标，跨平台一致）
  - 字号：12pt
  - 颜色：`getT2()`（次要文字色）
  - padding：8px
  - 无背景 / 无边框（与「▼历史」一致）
- **点击**：`onPaste()` 立即触发
- **可见性**：竖屏始终可见；横屏 ToggleRow 不显示

### 4.2 DisplayPanel TapGesture（可选）
- **位置**：DisplayPanel.Column 顶层
- **手势**：双击（TAP_GESTURE）→ 触发 `onPaste()`
- **冲突**：与 LongPressGesture.onCopy() 不冲突
- **不强制实现**（本期不实现，工具栏已能满足"零操作"诉求）

### 4.3 反馈时机
| 时机 | UI 表现 |
|------|---------|
| 粘贴成功 | 静默（expression/preview/result 自动更新） |
| 粘贴失败（非数学） | Toast「非数学表达式」+ 1.5s 自动消失 |
| 粘贴失败（系统错误） | 静默（容错优先） |
| 重复粘贴 | 静默 |

### 4.4 横屏布局
- 横屏时 ToggleRow **不渲染**（CalculatorPage.ets 中 `if (this.isLandscape) ... else ...`）
- 因此「📋粘贴」按钮在横屏**不可见**
- 用户在横屏需要粘贴时只能等 onPageShow 自动触发

## 5. 状态持久化

| 状态 | 持久化 | 理由 |
|------|--------|------|
| `lastPastedHash` | ❌（仅 @State） | 退出应用后剪贴板可能变 |
| 粘贴产生的 history | ✅（沿用 onEquals → prefs.setHistory） | 与手动计算结果同等对待 |

## 6. 可靠性分析（FMEA 消减措施）

| 故障模式 | 严重度 | 原因 | 消减措施 | 验证方式 |
|----------|--------|------|----------|----------|
| 剪贴板无文本内容 | 低 | 系统剪贴板被清空 | FMEA-1：getData 后判空 + trim 后判空 | 单元测试 |
| 剪贴板超长内容 | 中 | 攻击者粘贴 GB 级字符串 | FMEA-2：截断 200 字符 | 单元测试 |
| evaluate 抛异常 | 中 | 用户粘贴了 `1/0` `(-1)^0.5` 等 | FMEA-3：try/catch + 复用 onEquals 内置 ErrorFlags 路径 | 单元测试 |
| 重复粘贴污染历史 | 低 | onPageShow 多次触发 | FMEA-4：hash 去重 | 单元测试 |
| getData 系统异常 | 高 | 系统 Kit 不可用 | FMEA-5：try/catch 静默吞 | 单元测试（mock 抛错） |
| 空白字符串误判 | 低 | 复制时带换行符 | FMEA-6：trim + 非空判断 | 单元测试 |

## 7. 验收对照（可追溯）

| 验收编号 | 覆盖用例 | 覆盖规则 | 覆盖 FMEA |
|----------|----------|----------|-----------|
| AC-1 | UC-1 | 3.1 | FMEA-3, FMEA-4 |
| AC-2 | UC-1 | 3.1 | FMEA-3 |
| AC-3 | UC-1 | 3.1 | FMEA-3 |
| AC-4 | UC-1 | 3.1 + 3.4 | FMEA-6 |
| AC-5 | UC-3 | 3.4 | FMEA-3 |
| AC-6 | UC-5 | 3.3 | FMEA-4 |
| AC-7 | UC-6 | 3.2 | - |
| AC-8 | UC-5 | 3.3 | FMEA-4 |

## 8. 文档与术语

- **零操作体验**：用户从复制算式到看到结果，**不需要**主动点击应用内任何按钮
- **静默**：无 Toast、无震动、无 UI 闪烁
- **去重**：基于 hash 比对，相同内容只处理一次
- **hash 策略**：字符串 trim 后所有 char code 累加（不强加密，仅唯一性）
