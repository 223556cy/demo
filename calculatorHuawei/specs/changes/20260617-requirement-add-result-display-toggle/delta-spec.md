# Delta Spec: 计算结果支持小数和分数两种显示，自由切换

> 关联特性: feat-calculator-result-display
> 关联 Issue: #27
> 需求类型: requirement-add
> 优先级: ⭐⭐（学生用户强需求）

## 1. 需求概述

### 1.1 背景
当前计算器（`com.darkempire78.opencalculator`）计算结果仅以小数形式显示（如 `0.5`、`0.75`），对需要做分数运算的学生用户不友好。学生用户期望结果既能以小数显示（如 `0.5`），也能以分数显示（如 `1/2`），并能在两种模式间自由切换。

### 1.2 目标
在计算结果显示区新增**显示模式切换**功能，支持在小数（DECIMAL）和分数（FRACTION）两种模式间自由切换；显示模式通过应用首选项持久化，重启后保持用户上次选择。

### 1.3 范围
**包含：**
- 结果显示区右上角新增"切换显示模式"按钮（图标按钮）
- 分数显示格式：`a/b`（已化简），整数显示为 `n`，负数显示为 `-a/b`
- 显示模式持久化（重启后保留）
- 分数化简（基于 GCD 最大公约数）
- 有限精度的小数 → 分数转换（最大分母限制为 9999，超过则回退为小数显示）

**不包含：**
- 历史记录列表项的显示模式切换（历史仍以小数为主，避免视觉混乱）
- 混合分数（带整数的分数，如 `1 1/2`）支持（学生场景下 `3/2` 即可）
- 分数输入（用户仍以小数/整数输入，结果可分数化显示）
- 三级及以上显示精度设置

## 2. 用户故事

| # | 角色 | 故事 | 验收 |
|---|------|------|------|
| US-1 | 学生 | 我希望 `1 ÷ 2` 的结果以分数 `1/2` 显示，方便我检查作业 | 计算 `1÷2`，点击切换按钮，结果由 `0.5` 变为 `1/2` |
| US-2 | 学生 | 我希望切换到小数模式后，结果立即变回 `0.5` | 在分数模式下，再次点击切换按钮，结果变回 `0.5` |
| US-3 | 学生 | 我希望重启 App 后，我的显示模式偏好被保留 | 切换到分数模式，关闭 App，重启后结果显示仍为分数 |
| US-4 | 学生 | 我希望无理数（π、e 等）仍以小数显示 | 计算结果为 `3.14159...`，分数模式下降级显示为 `3.14159...` |
| US-5 | 学生 | 我希望负数结果也支持分数显示 | 计算 `-1 ÷ 2`，分数模式显示 `-1/2` |

## 3. 功能需求

### 3.1 显示模式切换
- **FR-1**：在 `CalculatorPage` 结果显示区右上角增加一个图标按钮（toggle 风格），点击在小数和分数模式间切换。
- **FR-2**：按钮图标使用现有图标库（如 `app.media.icon_fraction` / `app.media.icon_decimal`，或通过文字 `1/2` / `0.5`）。
- **FR-3**：当前模式在按钮上有视觉标识（如高亮/active 态）。
- **FR-4**：切换动画时长 ≤ 200ms（淡入淡出或瞬时切换皆可）。

### 3.2 分数格式化
- **FR-5**：分数化简：使用欧几里得算法计算 GCD，输出最简分数 `a/b`。
- **FR-6**：显示规则：
  - 整数：直接显示 `n`（无斜杠）
  - 真分数：显示 `a/b`（a < b）
  - 负数：显示 `-a/b`
  - 零：显示 `0`
- **FR-7**：分数化简的最大分母阈值：`maxDenominator = 9999`；超过则保留小数显示。
- **FR-8**：容差策略：浮点输入（如 `0.3333`）按有限位小数识别为分数（`3333/10000` → 化简为 `?`）；无理数（如 `Math.PI`）在 GCD 化简中分母超过阈值时回退为小数。
- **FR-9**：分数显示精度：分母超过 9999 时不强制分数化简，回退为默认 6 位小数。

### 3.3 持久化
- **FR-10**：显示模式通过 `PreferencesStore` 持久化（key: `result_display_mode`，value: `"decimal"` | `"fraction"`）。
- **FR-11**：App 启动时读取上次的显示模式作为初始值；默认 `decimal`。
- **FR-12**：用户切换时立即写回 Preferences。

### 3.4 异常处理
- **FR-13**：当结果为 `NaN` 或 `Infinity` 时，不进入分数模式，按现有方式显示。
- **FR-14**：当结果为 0 时，不做分数转换（直接显示 `0`）。
- **FR-15**：切换按钮在计算未完成时（如 `ErrorFlags.error` 为 true）禁用。

## 4. 可靠性分析（FMEA 消减措施清单）

| 故障模式 | 影响 | 严重度 | RPN（暂定） | 改进措施（约束/需求） | 责任模块 |
|---------|------|--------|------------|----------------------|----------|
| 浮点精度导致分数化简异常（如 `0.1 + 0.2 = 0.30000000000000004`） | 用户看到奇怪分数 | 中 | 高 | FR-7（最大分母 9999） + 化简后再判断分母阈值，超过则回退小数 | NumberFormatter |
| 用户在错误状态下点击切换 | 崩溃或异常 | 低 | 中 | FR-15（错误状态禁用切换按钮） | CalculatorPage |
| 持久化失败 | 重启后模式丢失 | 低 | 低 | FR-10 + PreferencesStore 容错：失败时回退默认 `decimal` | PreferencesStore |
| 负数分数格式错误 | 显示 `−1/−2` | 中 | 中 | FR-6 强制约定：负号只在分子前，denominator 永远为正 | NumberFormatter |
| 切换按钮在 resultDisplayText 为空时仍可点击 | UI 闪烁 | 低 | 低 | FR-15（计算未完成/无结果时禁用） | CalculatorPage |
| 历史记录中存的是浮点数，但显示模式切换不会影响历史 | 用户困惑 | 中 | 中 | 历史记录展示仍为小数；历史与结果切换解耦（FR 不要求历史跟随） | History 模块 |

## 5. DFX 需求

### 5.1 可用性
- **DFX-US-1**：切换按钮在浅色/深色主题下均可识别。
- **DFX-US-2**：切换按钮位置固定（不随输入内容左右移动）。
- **DFX-US-3**：按钮 hit target ≥ 32vp（适合学生手指操作）。

### 5.2 性能
- **DFX-PERF-1**：分数格式化单次耗时 < 1ms（简单 GCD 计算）。
- **DFX-PERF-2**：切换显示时无明显卡顿（< 100ms 切换延迟）。

### 5.3 可测试性
- **DFX-TEST-1**：`FractionUtil.toFraction(value)` 与 `NumberFormatter.format(value, mode)` 暴露为纯函数，便于单元测试。
- **DFX-TEST-2**：UI 自动化测试覆盖切换按钮的存在性与点击响应。

## 6. 接口与数据模型

### 6.1 枚举
```ts
// model/DisplayMode.ets (新增)
export enum DisplayMode {
  DECIMAL = 'decimal',
  FRACTION = 'fraction'
}
```

### 6.2 工具函数
```ts
// common/FractionUtil.ets (新增)
export class FractionUtil {
  static toFraction(value: number, maxDenominator: number = 9999): {numerator: number, denominator: number} | null
  static gcd(a: number, b: number): number
  static format(numerator: number, denominator: number): string  // 输出 "1/2" 形式
}
```

### 6.3 格式化器扩展
```ts
// calculator/NumberFormatter.ets (扩展)
export class NumberFormatter {
  static format(value: number, mode: DisplayMode = DisplayMode.DECIMAL): string
}
```

### 6.4 持久化
```ts
// preferences/PreferencesStore.ets (扩展)
class PreferencesStore {
  async getResultDisplayMode(): Promise<DisplayMode>
  async setResultDisplayMode(mode: DisplayMode): Promise<void>
}
```

## 7. 验收标准

| AC# | 描述 | 测试方法 |
|-----|------|----------|
| AC-1 | 计算 `1÷2`，分数模式显示 `1/2` | 单元测试 + UI 自动化 |
| AC-2 | 计算 `3÷4`，分数模式显示 `3/4` | 单元测试 |
| AC-3 | 计算 `1÷3`，分数模式降级显示为 `0.33333...` | 单元测试 |
| AC-4 | 计算 `-1÷2`，分数模式显示 `-1/2` | 单元测试 |
| AC-5 | 切换按钮存在且可点击 | UI 自动化 |
| AC-6 | 切换后立即生效，文本变化 | UI 自动化 |
| AC-7 | 重启 App 后显示模式保留 | 手动验证 |
| AC-8 | 历史记录仍以小数显示 | UI 自动化 |

## 8. 风险与回滚

- **风险 R-1**：分数化简与现有计算引擎逻辑耦合，可能影响历史/科学计算展示
  - **缓解**：只修改显示层，不修改 Calculator.ets 核心计算
- **风险 R-2**：Preferences 读写失败
  - **缓解**：try-catch + 默认值 `DECIMAL`
- **回滚方案**：移除 `DisplayMode` 相关代码 + 移除切换按钮；`NumberFormatter.format(value)` 兼容旧调用

## 9. 不涉及

- 架构变更：不涉及（仍沿用 MVVM）
- 网络通信：不涉及
- 媒体播放：不涉及
- 导航路由：不涉及
- WebView：不涉及
- 后台任务：不涉及
