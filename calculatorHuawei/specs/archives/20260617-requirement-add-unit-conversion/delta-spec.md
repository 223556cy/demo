# Delta Spec: 自然语言单位换算 — Issue #18

> **Date**: 2026-06-17
> **Type**: 增量规格（Δ spec）
> **Base**: opencalc 当前实现（v0.0.0 + 已合入的 issue-11 实时预览、issue-9 百分号）
> **Change**: 计算器输入框直接支持自然语言单位换算

---

## 1. 受影响的需求（User Stories）

| ID | Story | 优先级 |
|----|-------|--------|
| US-1 | 作为用户，我希望输入 `100 厘米转英寸` 直接换算，这样我不用离开计算器 | P0 |
| US-2 | 作为用户，我希望 `30 摄氏度转华氏度` 也能换算，覆盖最常用的温度 | P0 |
| US-3 | 作为用户，我希望英文 `5ft in cm` 也能识别，覆盖英文用户 | P1 |
| US-4 | 作为用户，我希望 `1+2` 这类表达式不被误判为单位换算 | P0 |
| US-5 | 作为用户，我希望 `5 米转千克` 这类跨维度输入有明确错误提示 | P0 |
| US-6 | 作为用户，我希望换算结果也写入历史，方便我回看 | P0 |
| US-7 | 作为开发者，我希望 NL parse 与 CalcEngine 错误隔离，互不污染 | P0 |
| US-8 | 作为开发者，我希望有完整单元测试覆盖核心算法 | P0 |

## 2. 行为规格

### 2.1 NL 模式识别协议

`NaturalLanguageParser.parse(input)` 是唯一入口。命中 NL 模式返回 `NLParseResult`，否则返回 `null`。

**关键字列表**（任一即视为分隔符）：
- 中文：`转` / `为` / `→`
- 英文：`to` / `in`（in 仅在"value unit in unit"格式下作关键字）
- 箭头：`->`

**支持的输入格式**：

| 格式 | 示例 | 解析结果 |
|------|------|---------|
| 中文紧凑 | `100厘米转英寸` | `{v:100, from:厘米, to:英寸}` |
| 中文带空格 | `100 厘米 转 英寸` | 同上（容忍空白） |
| 中文温度 | `30摄氏度转华氏度` | `{v:30, from:摄氏度, to:华氏度}` |
| 英文 in 紧凑 | `5ft in cm` | `{v:5, from:ft, to:cm}` |
| 英文 to 带空格 | `5 m to ft` | `{v:5, from:m, to:ft}` |
| 中文为 | `100cm为m` | `{v:100, from:cm, to:m}` |
| 箭头 | `100厘米→英寸` | 同紧凑 |
| 小数 | `1.5米转英尺` | `{v:1.5, from:米, to:英尺}` |

**降级规则**（返回 null，交给 CalcEngine）：
- 含 `+` `-` `*` `×` `÷` `/` `^` `!` 等运算符
- 含 `sin` `cos` `tan` `log` `ln` `√` 等函数名
- 空字符串
- 纯数字（无单位关键字）
- 数字部分不是合法 `\d+(\.\d+)?`

### 2.2 单位换算协议

`UnitConverter.convert(value, from, to)` 是唯一入口。

| 行为 | 输入 | 输出 |
|------|------|------|
| 成功 | `convert(100, '厘米', '英寸')` | `39.3700787...` |
| 跨维度 | `convert(5, '米', '千克')` | `NaN` |
| 未知单位 | `convert(5, 'xyz', '米')` | `NaN` |

**支持的单位表**：

| 维度 | 基准 | 单位 |
|------|------|------|
| length | m | 毫米, 厘米, 分米, 米, 千米, 英寸, 英尺, 码, 英里 |
| mass | g | 毫克, 克, 千克, 吨, 磅, 盎司 |
| time | s | 秒, 分钟, 小时, 天 |
| temperature | K | 摄氏度, 华氏度, 开尔文 |

**温度特殊处理**（affine，非线性）：

| 转换 | 公式 |
|------|------|
| °C → K | `v + 273.15` |
| K → °C | `v - 273.15` |
| °F → K | `(v - 32) * 5/9 + 273.15` |
| K → °F | `(v - 273.15) * 9/5 + 32` |

### 2.3 CalculatorPage.onEquals 集成

**改造点**：在 `try` 块开头增加 NL 优先分支，三态返回：

```ts
const uc = this.tryUnitConversion(this.expression)
if (uc.ok) {                       // ① NL 成功：写 result + history
  this.result = NumberFormatter.format(uc.value.toString(), '.', ',', NumberingSystem.INTERNATIONAL)
  this.errorMsg = ''
  this.history.push(...)
  return
}
if (uc.error !== undefined) {      // ② NL 失败但识别为换算：直接报错
  this.errorMsg = uc.error          //   '单位不匹配或未知'
  this.result = ''
  return
}
// ③ NL parse null：走原 CalcEngine 降级
try { ... 原逻辑不变 ... }
```

**三态契约**：

| 状态 | 触发 | 行为 |
|------|------|------|
| `ok: true` | NL 成功且单位有效 | result + history 写入 |
| `ok: false, error: string` | NL 成功但单位无效（跨维度/未知） | errorMsg + 空白 result |
| `ok: false, error: undefined` | NL parse 返回 null | 走原 CalcEngine |

### 2.4 UI 行为

- **不改动**键盘布局、按钮、菜单
- **不改动**DisplayPanel 布局（与 issue-11 实时预览共存：换算结果出现在 preview 区与 result 区，preview 由 onEquals 触发时与 result 内容一致）
- **不改动**长按复制、历史列表的交互

## 3. 验收用例（Acceptance Criteria）

### AC-UC-01: 中文长度换算
**Given** 用户输入 `100厘米转英寸`
**When** 按 `=`
**Then** 显示 `39.3701`（容差 1e-4）

### AC-UC-02: 中文温度换算
**Given** 用户输入 `30摄氏度转华氏度`
**When** 按 `=`
**Then** 显示 `86`

### AC-UC-03: 英文 in 格式
**Given** 用户输入 `5ft in cm`
**When** 按 `=`
**Then** 显示 `152.4`（5 × 30.48 = 152.4 cm）

### AC-UC-04: 英文 to 格式
**Given** 用户输入 `5 m to ft`
**When** 按 `=`
**Then** 显示 `16.4042`（容差 1e-4）

### AC-UC-05: 表达式不被误判
**Given** 用户输入 `1+2`
**When** 按 `=`
**Then** 显示 `3`（CalcEngine 降级）

### AC-UC-06: 函数不被误判
**Given** 用户输入 `sin(0)`
**When** 按 `=`
**Then** 显示 `0`（CalcEngine 降级）

### AC-UC-07: 跨维度报错
**Given** 用户输入 `5米转千克`
**When** 按 `=`
**Then** 显示 `单位不匹配或未知`

### AC-UC-08: 未知单位报错
**Given** 用户输入 `5xyz转米`
**When** 按 `=`
**Then** 显示 `单位不匹配或未知`

### AC-UC-09: 紧凑无空格
**Given** 用户输入 `100厘米转英寸`（无空格）
**When** 按 `=`
**Then** 显示 `39.3701`（同 AC-UC-01）

### AC-UC-10: 带空格
**Given** 用户输入 `100 厘米 转 英寸`（带空格）
**When** 按 `=`
**Then** 显示 `39.3701`（同 AC-UC-01）

### AC-UC-11: 小数
**Given** 用户输入 `1.5米转英尺`
**When** 按 `=`
**Then** 显示 `4.9213`（1.5 × 3.28084 = 4.9213，容差 1e-4）

### AC-UC-12: 箭头
**Given** 用户输入 `100厘米→英寸`
**When** 按 `=`
**Then** 显示 `39.3701`（同 AC-UC-01）

### AC-UC-13: 历史记录
**Given** 用户完成 `100厘米转英寸=` 换算
**When** 打开历史记录面板
**Then** 历史第一条为 `100厘米转英寸 = 39.3701`

### AC-UC-14: NL 失败后 CalcEngine 正常
**Given** 用户先输入 `5米转千克=` 看到错误
**When** 输入 `1+2` 再按 `=`
**Then** 显示 `3`（CalcEngine 路径未被污染）

### AC-UC-15: 编译通过
**Given** 项目根目录
**When** 执行 `hvigorw --no-daemon assembleHap`
**Then** 退出码 0，HAP 文件生成

### AC-UC-16: 单元测试通过
**Given** specs/changes/20260617-requirement-add-unit-conversion/tests/
**When** 执行 `node --test UnitConverter.test.mjs NaturalLanguageParser.test.mjs`
**Then** 32/32 PASS

### AC-UC-17: UI 自动化（BLOCKED）
**Given** 模拟器 127.0.0.1:5555
**When** 启动模拟器 + 用 harmonyos-ui-test 跑上述 AC-UC-01/02/05
**Then** 截图 + uiautomator dump 落到 `ui-tests/screenshot/`
**当前状态**：⚠️ BLOCKED（hdc list targets 返回 [Empty]，capabilities.json 标 emulator_status=running 与实际不符，详见 todo.md 与 apply-report.md）

## 4. 不变式（Invariants）

- I-1：`Expression.getCleanExpression` / `CalcEngine.evaluate` / `NumberFormatter.format` 签名与行为不变
- I-2：UI 网格布局、按钮、菜单不变
- I-3：测试只增不改（不删旧行为）
- I-4：ArkTS 兼容性优先，不引入三方库
- I-5：onEquals 入口加 if 守卫而非改 try-catch（保持错误隔离）
- I-6：NL 路径失败不污染 CalcEngine（ErrorFlags 不被 NL 路径读写）

## 5. 度量指标

| 指标 | 当前 | 目标 |
|------|------|------|
| 长度换算自动化测试用例 | 0 | ≥ 7 |
| 质量换算自动化测试用例 | 0 | ≥ 3 |
| 时间换算自动化测试用例 | 0 | ≥ 3 |
| 温度换算自动化测试用例 | 0 | ≥ 6 |
| NL 正向用例 | 0 | ≥ 6 |
| NL 负向用例 | 0 | ≥ 4 |
| 整体 `hvigorw test` 通过率 | N/A | 100% |
| `hvigorw assembleHap` 退出码 | 0 | 0 |

## 6. 风险等级

**R-Medium**：
- NL 模式识别算法有歧义（紧凑 vs 带空格 vs 表达式）
- 单位别名冲突（m=米=分钟）
- 真实 hdc 不可用阻塞 UI 验证（环境问题，已诚实记录阻塞）
- 集成到 onEquals 影响其他表达式（已用 if 守卫缓解）

## 7. 实施顺序（TDD）

1. RED：写 UnitConverter.test.ets + NaturalLanguageParser.test.ets（断言失败）
2. GREEN：实现两个 .ets 模块
3. RED：写 CalculatorPage NL 集成测试（如框架支持）或记录阻塞
4. GREEN：修改 CalculatorPage.onEquals
5. 编译：`hvigorw --no-daemon assembleHap`
6. 单元测试：`node --test specs/changes/20260617-requirement-add-unit-conversion/tests/*.test.mjs`
7. UI 自动化：harmonyos-ui-test（如果 hdc 可用；否则记录阻塞）
8. 提交 + push
