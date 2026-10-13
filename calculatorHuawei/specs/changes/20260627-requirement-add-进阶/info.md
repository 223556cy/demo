# Issue #27 分数/小数显示切换 — 代码仓理解

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- UI 测试能力: ✅ 可用
- 模拟器列表: 127.0.0.1:5555
- hdc: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- bundleName: com.darkempire78.opencalculator

## 基本信息

- **需求类别**：新增功能
- **需求名称**：计算结果支持小数和分数两种显示，自由切换
- **分析时间**：2026-06-27
- **分析范围**：CalculatorPage、FractionUtil、PreferencesStore、Models

## 架构分析

项目采用标准的 HarmonyOS ArkTS MVVM 架构：

```
┌─────────────────────────────────────────┐
│  pages/CalculatorPage.ets               │  View 层
├─────────────────────────────────────────┤
│  calculator/Calculator.ets              │  ViewModel / 业务逻辑
│  calculator/Expression.ets              │  ViewModel / 表达式预处理
│  calculator/NumberFormatter.ets         │  ViewModel / 格式化
├─────────────────────────────────────────┤
│  model/Models.ets                       │  Model 层
│  model/ModeModel.ets                    │  Model 层
├─────────────────────────────────────────┤
│  preferences/PreferencesStore.ets       │  数据持久化
│  common/FractionUtil.ets                │  工具函数
├─────────────────────────────────────────┤
│  history/HistoryStore.ets               │  历史记录管理
└─────────────────────────────────────────┘
```

模块职责：
- **CalculatorPage**：主页面，管理所有显示状态与交互
- **CalcEngine**：递归下降解析器，负责表达式求值
- **Expression**：表达式预处理（符号替换、百分比、阶乘等）
- **NumberFormatter**：千分位/小数点格式化
- **FractionUtil**：浮点数转最简分数
- **PreferencesStore**：基于 HarmonyOS preferences 的持久化封装

## 接口/契约识别

### CalcEngine.evaluate
```ts
function evaluate(equation: string, isDegree: boolean): number
```
- 输入：清洗后的数学表达式字符串、角度/弧度标志
- 输出：number 类型计算结果
- 约束：可能抛出 ErrorFlags 异常

### FractionUtil.toFraction
```ts
function toFraction(value: number, maxDenominator?: number): { numerator: number; denominator: number }
```
- 输入：浮点数值
- 输出：分子/分母对象
- 约束：通过 `1e15` 缩放 + GCD 实现，大数场景可能精度受限

### PreferencesStore
```ts
getResultDisplayMode(): DisplayMode
setResultDisplayMode(mode: DisplayMode): void
```
- 输入/输出：DisplayMode 枚举（DECIMAL / FRACTION）
- 约束：异步读写，依赖 HarmonyOS preferences 模块

## 公共组件或函数识别

- **FractionUtil.toFraction / format**：纯逻辑工具，无 UI 依赖，可单元测试
- **NumberFormatter.format**：现有格式化工具，Decimal 模式下复用
- **PreferencesStore**：已有持久化封装，新增 key 即可扩展

## 影响范围分析

### 需要修改/涉及的文件清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| model/Models.ets | extend | 新增 DisplayMode 枚举 |
| common/FractionUtil.ets | new | 新增分数转换工具 |
| preferences/PreferencesStore.ets | extend | 新增显示模式读写 |
| pages/CalculatorPage.ets | modify | 新增状态、toggle 方法、UI 按钮、格式化路由 |

### 调用链关系
```
用户点击切换按钮
  → CalculatorPage.onToggleDisplayMode()
    → PreferencesStore.setResultDisplayMode()
    → 更新 @State displayMode
      → UI 重新渲染
        → formatResultForDisplay()
          → FractionUtil.toFraction() [FRACTION 模式]
          → NumberFormatter.format() [DECIMAL 模式]
```

## 现有代码分析

### CalculatorPage 关键状态（已存在）
```ts
@State displayMode: DisplayMode = DisplayMode.DECIMAL
@State lastRawResult: number = 0
```

### formatResultForDisplay（已存在）
- 根据 `displayMode` 路由到不同格式化器
- FRACTION 模式：调用 `FractionUtil.toFraction(lastRawResult)`
- 分数转换失败时回退到 DECIMAL 格式化

### onToggleDisplayMode（已存在）
- 在 DECIMAL ↔ FRACTION 间切换
- 持久化到 PreferencesStore
- 当前有结果时立即重新格式化

## 风险识别

### 技术难点
- **浮点精度**：`0.1 + 0.2` 类浮点误差可能导致分数转换产生非预期大分母
- **大数分数**：极大/极小数值的分数表示可能超出可读范围

### 问题区域
- 分数按钮仅在竖屏显示，横屏布局下无切换入口（当前实现限制）

### 风险缓解建议
- 对 FractionUtil 增加单元测试覆盖边界值（0、负数、极大数、循环小数近似值）
- 限制最大分母（如 1e6），超限回退小数显示

## 测试验证策略

### 测试场景清单
1. 基础分数转换：`0.5` → `1/2`，`0.25` → `1/4`
2. 负数：`−0.5` → `−1/2`
3. 整数：`2.0` → `2`
4. 不可约分数：`0.333...` → 近似分数
5. 切换持久化：关闭 App 后重新打开保持上次选择
6. 无结果状态：切换按钮在无结果时的行为
7. 横竖屏：确认横屏下按钮隐藏/显示策略

### 验收标准
- 点击切换按钮后，当前结果立即在分数/小数间切换
- 分数显示为最简形式
- 设置持久化跨会话有效
- 不影响历史记录的小数存储格式

### 回归范围
- 标准/科学/程序员模式的计算结果展示
- 历史记录读写
- 首选项持久化

## 监控运维支持

- 无新增监控指标
- 无新增配置项（除 PreferencesStore 内部 key）
- 关键日志：可在 FractionUtil 转换失败时记录降级行为

## 关键发现

### 可复用组件或函数
- **FractionUtil**：已存在，可直接复用
- **PreferencesStore**：已有持久化框架，新增 key-value 即可
- **NumberFormatter**：Decimal 模式下继续复用

### 风险提示
- 浮点精度导致的分数异常是主要风险点
- 横屏无切换入口是已知产品限制

### 建议事项
- 为 FractionUtil 补充 Hypium 单元测试
- 在 UI 自动化中验证切换按钮的可见性与点击响应
- 考虑未来在横屏也提供切换入口

## 测试能力评估
- 单元测试能力: ✅
- UI 自动化测试能力: ✅ (hdc + 模拟器 127.0.0.1:5555 可用)
- 端到端集成测试能力: ✅
- 不能跑的实际原因: 无
