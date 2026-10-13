# Proposal — Issue #22 程序员模式

## 1. 原始需求
> 支持二进制、八进制、十六进制转换，加一个程序员模式切换。 程序员模式 | ⭐⭐ | 模式切换动画+进制转换 |

**补充说明（来自人工上下文）**：
- 入口：在标准模式顶部或菜单提供"程序员模式"切换入口
- 程序员模式显示区：除主结果（DEC）外，额外展示 BIN/OCT/DEC/HEX 四个值
- 交互：点击某进制标签，把该进制的字符串作为当前输入接续编辑
- 模式切换需有平滑动画（参考 iOS/Android 程序员计算器淡入淡出+位移动效）

## 2. 意图分类
- **类型**：新增功能 (requirement-add)
- **一句话概括**：在标准计算器之外新增"程序员模式"，支持 BIN/OCT/DEC/HEX 四进制实时转换与切换动画

## 3. 领域映射
- **UI/交互**：模式切换器、进制结果区、进制按钮区、切换动画（arkts-animation-builder）
- **状态管理**：模式（standard / programmer）作为 ViewModel 状态；当前输入基数（base）作为派生状态（arkts-state-manager）
- **业务逻辑**：进制转换、负数/小数在 BIN/OCT/HEX 下的表示规则

## 4. 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View (pages/, components/) | modify + new | 新增 `ProgrammerPanel` 组件；扩展 `CalculatorPage.ets` 加入模式切换 |
| ViewModel (viewmodel/) | modify + new | `CalculatorViewModel` 增加 `mode: 'standard' | 'programmer'` 与 `activeBase` 状态；新增 `BaseConverter` 工具 |
| Model (model/) | new | `NumberBase` 枚举、Mode 枚举、`BaseRepresentation` 数据模型 |
| 基础设施 (common/utils/) | new | `BaseConverter.ets` 工具类（仅依赖标准 Number/Math，无第三方） |

## 5. 关键实体
- **数据实体**
  - `NumberBase`：枚举（BIN=2, OCT=8, DEC=10, HEX=16），含 `radix` 与 `validCharRegex`
  - `CalculatorMode`：枚举（STANDARD, PROGRAMMER）
  - `BaseRepresentation`：`{ base: NumberBase, value: string, isNegative: boolean }`
  - `ProgrammerDisplayState`：`{ decimalValue: number, representations: Map<NumberBase, string> }`
- **页面实体**
  - `CalculatorPage.ets`（修改）：增加模式切换按钮与条件渲染
  - `ProgrammerPanel.ets`（新建）：4 行进制显示 + 进制键盘
  - `BaseChip.ets`（新建）：单个进制的"标签+值"行，可点击
- **接口实体**
  - `BaseConverter` 静态方法：`toBase(n: number, base: NumberBase): string`、`fromBase(s: string, base: NumberBase): number`
  - `CalculatorViewModel.setMode(mode)`、`setActiveBase(base)`、`appendDigit(d)` 在程序员模式下按 `activeBase` 校验字符
- **事件实体**
  - `OnModeChanged(mode)`：触发切换动画
  - `OnBaseTapped(base)`：切换 `activeBase`，并把该进制的字符串反解析回 number 作为 currentInput

## 6. 模糊点（方案 C — 自动作答）

| # | 类别 | 描述 | 严重程度 | 自动作答（记录到 todo.md） |
|---|------|------|---------|--------------------------|
| 1 | 行为模糊 | 程序员模式下输入时按哪个基数校验？ | important | 当前 activeBase；用户点击某行切换 activeBase，并把该字符串反解析为 number 继续编辑 |
| 2 | 行为模糊 | 小数与负数在 BIN/OCT/HEX 下的表示 | important | BIN/OCT/HEX 仅显示整数部分（向下取整），负数前置 `-`；DEC 行仍显示完整值 |
| 3 | 数据模糊 | 模式是否需要持久化 | nice-to-have | 持久化到 preferences（key=`calc_mode`，与 #18 现有持久化策略一致） |
| 4 | 交互模糊 | 切换入口位置 | important | 顶部"模式"按钮（汉堡菜单/侧滑之外的常驻入口），点击弹出 ActionSheet 选 STANDARD/PROGRAMMER |
| 5 | 约束模糊 | 动画形式 | nice-to-have | 使用 `animateTo` 实现 opacity 0→1 + translateY 8px→0，时长 220ms curve EaseInOut |
| 6 | 范围模糊 | 是否有上限（如 64-bit 限制） | important | 整数部分按 JS Number 安全范围（Number.MAX_SAFE_INTEGER = 2^53-1）；超过则显示提示 |
| 7 | 行为模糊 | 标准模式是否隐藏原有键盘 | blocker(已解) | 程序员模式使用一套独立的"0-9 A-F"键盘（HEX 字母），标准键盘隐藏 |
| 8 | 兼容模糊 | 不影响现有功能 | important | 标准模式所有现有行为完全不变；历史/复制/长按菜单等特性在两种模式下都生效 |

## 7. 复杂度评估
- **等级**：M（中等）
- **理由**：
  - 涉及 View + ViewModel + Model + 基础设施 4 个层次
  - 需新增 2~3 个组件 / 1 个 ViewModel 扩展 / 1 个工具类
  - 代码改动量估算 200~350 行（含动画与状态联动）
  - 单一 feature（程序员模式），不涉及多模块交叉
  - 无需修改现有计算逻辑，只在 ViewModel 层增加 mode 分支

## 8. 备注
- 无 blocker 模糊点残留；所有 important 项已在 §6 给出明确决策并记录到 todo.md
- 集成复用：与 #15 历史分组、#16 长按菜单、#17 粘贴即计算、#18 单位换算 互不影响，可独立交付
- 后续可扩展：二进制位运算（AND/OR/XOR/SHL/SHR）作为程序员模式后续迭代

## 9. 决策记录
- spec 命名：`feat-programmer-mode` (与 Issue #22 对齐)
- 目录：`specs/changes/20260617-requirement-add-programmer-mode/`
- 分支：`feat/issue-22-简单需求`（已存在）
