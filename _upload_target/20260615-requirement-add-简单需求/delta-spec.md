# Issue #12 程序员模式 - 增量需求规格 (delta-spec)

## 0. 元信息
- 变更类型：requirement-add（新增功能）
- 关联特性：feat-programmer-mode
- 基线特性：feat-core-calculator（基础计算器 + 科学模式）
- 适用版本：OpenCalc HarmonyOS v0.x

## 1. 需求概述

在现有基础模式（BASIC）和科学模式（SCIENTIFIC）之外，新增**程序员模式（PROGRAMMER）**，提供：

1. DEC / BIN / OCT / HEX 四进制实时显示与切换
2. 顶部模式切换器（三选一 Segment）
3. 模式切换时的 fade + slide 转场动画
4. 用户偏好（mode + activeBase）持久化

## 2. 功能需求（Functional Requirements）

### FR-1 模式切换（Mode Switching）

**描述**：用户通过顶部 SegmentedControl 在 BASIC / SCIENTIFIC / PROGRAMMER 三种模式间切换。

**前置条件**：应用已启动；CalculatorPage 已挂载。

**后置条件**：
- 当前 mode 状态切换并触发键盘区域重新渲染
- mode 写入 PreferencesStore（key=`mode`，value=CalculatorMode 枚举 int 值）
- 键盘区域按新 mode 重新布局

**验收标准**：
| AC | 描述 |
|----|------|
| AC-1.1 | 三选一按钮位于 CalculatorPage 顶部 |
| AC-1.2 | 默认 mode = BASIC |
| AC-1.3 | 点击不同 mode 按钮，键盘区域切换为对应布局 |
| AC-1.4 | 切换有 fade + slide 动画（详见 FR-5） |
| AC-1.5 | mode 切换后写入 PreferencesStore，重启应用后保留 |

### FR-2 程序员键盘（Programmer Keypad）

**描述**：PROGRAMMER 模式下，键盘区域显示 BIN/HEX/数字/运算符组合布局。

**布局规格**（5 列 × 6 行）：
```
[AC]  [⌫]  [(]   [)]   [÷]
[ A ] [ B ] [ C ] [ D ] [×]
[ E ] [ F ] [ 7 ] [ 8 ] [ - ]
[ 1 ] [ 2 ] [ 3 ] [ 4 ] [ + ]
[ 0 ] [ 1 ] [ 5 ] [ 6 ] [ % ]    <- BIN 0/1 单独列；% 退化为占位
[ . ] [ = ] [ 9 ] [±]  [√]      <- ±/√ 程序员模式下保留
```

**验收标准**：
| AC | 描述 |
|----|------|
| AC-2.1 | BIN 0/1 按钮在指定槽位 |
| AC-2.2 | HEX A-F 字母按钮 6 个 |
| AC-2.3 | 数字 2-9 按钮齐全 |
| AC-2.4 | 运算符 + - × ÷ 保留 |
| AC-2.5 | AC/退格/等号 保留 |
| AC-2.6 | 科学函数 sin/cos/tan/ln/log 在程序员模式隐藏 |

### FR-3 多进制实时显示（Multi-Base Live Display）

**描述**：PROGRAMMER 模式下，主结果区下方固定显示 4 行 BIN/OCT/HEX/DEC 实时值。

**显示格式**：
```
DEC:    255
HEX:    0xFF
OCT:    0o377
BIN:    0b11111111
```

**验收标准**：
| AC | 描述 |
|----|------|
| AC-3.1 | 4 行依次为 DEC/HEX/OCT/BIN，每行带 0x/0o/0b 前缀（DEC 无前缀） |
| AC-3.2 | 计算时实时刷新 |
| AC-3.3 | BIN/OCT/HEX 仅显示整数部分（截断小数） |
| AC-3.4 | DEC 行显示完整值（含小数） |
| AC-3.5 | 错误状态（ErrorFlags.snapshot 非空）时 4 行均显示 `-` |
| AC-3.6 | 仅 PROGRAMMER 模式显示此面板，BASIC/SCIENTIFIC 隐藏 |

### FR-4 主进制切换（Active Base Toggle）

**描述**：PROGRAMMER 模式下，主结果"主进制"四选一按钮（DEC/BIN/OCT/HEX），影响主结果数值进制和顶部标签。

**验收标准**：
| AC | 描述 |
|----|------|
| AC-4.1 | 4 个 SegmentedControl 按钮，位于多进制显示行下方 |
| AC-4.2 | 默认 activeBase = DEC |
| AC-4.3 | activeBase = DEC 时主结果 `255`；BIN 时 `0b11111111`；OCT 时 `0o377`；HEX 时 `0xFF` |
| AC-4.4 | 切换 activeBase 后多进制显示行的"高亮行"对应切换（视觉提示） |
| AC-4.5 | activeBase 写入 PreferencesStore（key=`activeBase`） |

### FR-5 模式切换动画（Mode Transition Animation）

**描述**：键盘区域在模式切换时执行 fade + slide 过渡。

**动画规格**：
- enter：`{ type: TransitionType.Insert, opacity: 0, translate: { x: 8 } } → { opacity: 1, translate: { x: 0 } }`
- duration：200ms
- curve：Curve.EaseInOut

**验收标准**：
| AC | 描述 |
|----|------|
| AC-5.1 | 切换有 fade（透明度 0→1） |
| AC-5.2 | 切换有 slide-from-right（x: 8→0） |
| AC-5.3 | 仅键盘区域动画；显示屏与顶部不动画 |
| AC-5.4 | 动画时长 200ms |

## 3. 数据需求

### 3.1 新增枚举/模型

```typescript
// model/Models.ets
export enum CalculatorMode {
  BASIC = 0,
  SCIENTIFIC = 1,
  PROGRAMMER = 2
}

export enum NumberBase {
  DEC = 0,
  BIN = 1,
  OCT = 2,
  HEX = 3
}
```

### 3.2 扩展 CalculatorPreferences

| 字段 | 类型 | 默认值 | 持久化键 |
|------|------|--------|----------|
| mode | CalculatorMode | BASIC | `mode` |
| activeBase | NumberBase | DEC | `activeBase` |
| (existing) scientificModeDefault | number | 0 | `scientificModeDefault` |

### 3.3 BaseConverter 工具类契约

```typescript
// calculator/BaseConverter.ets
export class BaseConverter {
  static convert(value: number, base: NumberBase): string
  // 行为契约：
  // - convert(255, NumberBase.BIN) => "11111111"
  // - convert(255, NumberBase.OCT) => "377"
  // - convert(255, NumberBase.HEX) => "FF"
  // - convert(-1, NumberBase.BIN) => "-1"    // 负数 - 前缀
  // - convert(3.14, NumberBase.BIN) => "11"  // 截断小数
  // - convert(NaN, NumberBase.BIN) => "-"    // NaN 防御
  // - convert(Infinity, NumberBase.BIN) => "-"  // Infinity 防御
  // - convert(0, NumberBase.BIN) => "0"
  // - 大于 Number.MAX_SAFE_INTEGER 不在本期范围
}
```

## 4. 接口需求

### 4.1 PreferencesStore 扩展

```typescript
async getMode(): Promise<CalculatorMode>     // 默认 BASIC
async setMode(mode: CalculatorMode): Promise<void>
async getActiveBase(): Promise<NumberBase>   // 默认 DEC
async setActiveBase(base: NumberBase): Promise<void>
```

### 4.2 兼容性

- 保留 `getScientificModeDefault()` / `setScientificModeDefault()` 旧接口（不删除）
- 旧数据（只有 scientificModeDefault）迁移：scientificModeDefault=1 → mode=SCIENTIFIC，=0 → mode=BASIC
- 新数据（mode 字段）优先于旧数据

## 5. 可靠性需求（FMEA）

### 5.1 FMEA 消减措施清单

| 故障模式 | 严重度 | 原因 | 检测方法 | 缓解措施 |
|---------|--------|------|---------|---------|
| NaN 输入导致显示 "NaN" 污染 UI | 中 | 用户除零等错误运算 | 输入校验 | BaseConverter 检测 `Number.isNaN(value)` 返回 `"-"` |
| Infinity 输入导致 "Infinity" 显示 | 中 | 除零 | 输入校验 | BaseConverter 检测 `!Number.isFinite(value)` 返回 `"-"` |
| BIN/OCT/HEX 显示小数导致 0b3.14 非法格式 | 高 | 用户在 DEC 模式输入小数 | 截断 | BaseConverter 使用 `Math.trunc` + `toString(base)` |
| 负数在 HEX 显示为 "-FF" 误读为反码 | 低 | 用户期望 | UI 提示 | 顶部显示"HEX（无符号）"避免误导 |
| 模式切换后 expression 状态错乱 | 中 | 状态机不完整 | UI 测试 | onModeChange 不重置 expression；切换 keyboard @Builder |
| 切换 activeBase 后多进制行未刷新 | 中 | @Watch 缺失 | UI 测试 | @Watch('onActiveBaseChange') 触发 refresh |
| PreferencesStore 写入失败导致下次启动丢失 | 低 | 异步异常 | 异常捕获 | setMode 内部 try-catch，错误不外抛 |
| 横屏下 SegmentedControl 错位 | 中 | 布局未适配 | UI 测试 | 横屏下隐藏文字仅图标 |
| 实时预览在程序员模式显示小数 | 低 | preview 触发 | 单元测试 | 程序员模式下 hidePreview |

## 6. 性能需求

| 指标 | 要求 |
|------|------|
| 模式切换响应 | < 250ms（含动画） |
| BaseConverter 单次调用 | < 1ms |
| 多进制显示行刷新 | < 16ms（一帧内） |

## 7. 兼容性需求

| 项 | 要求 |
|----|------|
| 旧偏好迁移 | scientificModeDefault=1 → SCIENTIFIC；=0 → BASIC |
| 现有科学模式行为 | 100% 不变（保留 ToggleRow 后备路径） |
| 现有 AC-1..AC-12 百分号测试 | 不破坏 |

## 8. 安全/隐私需求

无（本地偏好数据，无网络通信）。

## 9. 国际化需求

- SegmentedControl 标签：`基础` / `科学` / `程序员`（中文）
- 多进制行标签：`DEC` / `HEX` / `OCT` / `BIN`（缩写，国际通用）

## 10. 测试需求

| 测试类型 | 范围 | 工具 |
|---------|------|------|
| 单元测试 | BaseConverter 全部转换场景 + 边界 | hypium+hamock |
| UI 测试 | 模式切换 + activeBase 切换 | harmonyos-ui-test + hdc |
| 视觉验证 | 动画效果 | 人工 + 录屏 |

## 11. 验收清单（不涉及 / 涉及明确）

- [x] 涉及：FR-1 模式切换
- [x] 涉及：FR-2 程序员键盘
- [x] 涉及：FR-3 多进制显示
- [x] 涉及：FR-4 主进制切换
- [x] 涉及：FR-5 切换动画
- [x] 涉及：BaseConverter 新建
- [x] 涉及：PreferencesStore 扩展（向后兼容）
- [x] 涉及：CalculatorPage 重构（拆分键盘 + mode 状态机）
- [x] 涉及：Models 扩展枚举
- [x] 不涉及：删除现有功能
- [x] 不涉及：架构变更（沿用 MVVM）