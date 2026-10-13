# Issue #12 程序员模式 - 代码仓理解

## 基本信息

- **需求类别**：新增功能
- **需求名称**：程序员模式（二进制/八进制/十六进制转换 + 模式切换动画）
- **分析时间**：2026-06-15
- **分析范围**：`opencalc/entry/src/main/ets/`

## 环境能力（来自 .claude/capabilities.json）

- 项目类型: HarmonyOS
- 平台: Windows
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- UI 测试能力: true
- 模拟器列表: 127.0.0.1:5555
- hdc: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- bundleName: com.darkempire78.opencalculator

## 架构分析

OpenCalc HarmonyOS 移植采用单页面 MVVM 架构（无 Hilt/DI），层级清晰：

```
@Entry
  └─ pages/CalculatorPage.ets (@Component, 543 行)
        │
        ├─ calculator/Calculator.ets      (CalcEngine — 递归下降解析器)
        ├─ calculator/Expression.ets     (表达式预处理)
        ├─ calculator/NumberFormatter.ets (千分位/精度)
        ├─ model/Models.ets              (枚举 + 接口 + DEFAULT_PREFERENCES)
        ├─ model/ErrorFlags.ets          (全局错误标志 singleton)
        └─ preferences/PreferencesStore.ets (preferences 封装)
```

### 关键扩展点
- `@State scientific: boolean = false` 在 CalculatorPage:22 — 现有二选一模式标志
- `ToggleRow()` @Builder 在 CalculatorPage:384-397 — 现有二选一按钮
- `aboutToAppear()` 调 `loadPrefs()` → `loadHistory()` — 偏好初始化流程
- `setScientificModeDefault(value: number)` 在 PreferencesStore:144 — 现有科学模式持久化

## 接口/契约识别

| 接口 | 位置 | 说明 |
|------|------|------|
| `CalcEngine.evaluate(clean: string, degree: boolean): number` | Calculator.ets | 返回 number，可能设置 ErrorFlags |
| `Expression.getCleanExpression(raw: string, dec: string, grp: string): string` | Expression.ets | 预处理 + ErrorFlags 副作用 |
| `NumberFormatter.format(value: string, dec: string, grp: string, ns: NumberingSystem): string` | NumberFormatter.ets | 千分位格式化 |
| `PreferencesStore.getScientificModeDefault(): Promise<number>` | PreferencesStore.ets | 返回 0/1/2 |
| `PreferencesStore.setScientificModeDefault(value: number): Promise<void>` | PreferencesStore.ets | 持久化 |
| `ErrorFlags.reset()` / `ErrorFlags.snapshot()` / `ErrorFlags.restore(snap: boolean[])` | ErrorFlags.ets | 错误标志管理 |

## 公共组件或函数识别

| 组件/函数 | 文件 | 可复用方式 |
|-----------|------|-----------|
| `NumberFormatter.format()` | NumberFormatter.ets | 用于 DEC 主结果显示（不变） |
| `CalcEngine.evaluate()` | Calculator.ets | 程序员模式计算复用 |
| `Expression.getCleanExpression()` | Expression.ets | 程序员模式表达式预处理复用 |
| `@Builder ButtonGrid()` | CalculatorPage.ets | 拆分为 BasicKeypad + ScientificKeypad + ProgrammerKeypad 三个 @Builder |
| `@Builder ToggleRow()` | CalculatorPage.ets | 改为 ModeToggleRow（三选一 SegmentedControl） |
| `harmonyos-ui-test` skill | ~/.claude/skills/ | UI 自动化测试 |
| `127.0.0.1:5555` emulator | running | 端到端验证 |

## 影响范围分析

### 需要修改的文件

| 文件 | 改动 |
|------|------|
| `opencalc/entry/src/main/ets/model/Models.ets` | 新增 `CalculatorMode` 枚举、`NumberBase` 枚举；扩展 `CalculatorPreferences` 增加 `mode`/`activeBase` 字段；扩展 `DEFAULT_PREFERENCES` |
| `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets` | 新增 `getMode()/setMode()/getActiveBase()/setActiveBase()`；`getAllPreferences()` 扩展 |
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` | 重构 `scientific: boolean` → `mode: CalculatorMode`；新增 `activeBase: NumberBase` + `baseConversions: BaseConversions` 状态；`ToggleRow()` → `ModeToggleRow()`；新增 `BaseConverterPanel()` + `ProgrammerKeypad()`；`onEquals()`/`onExpressionChange()` 增加多进制刷新；`onModeChange()`/`onActiveBaseChange()` 回调；偏好读写扩展 |
| `opencalc/entry/src/test/ets/calculator/Expression.test.ets` | 已有；保持不变 |

### 新建的文件

| 文件 | 用途 |
|------|------|
| `opencalc/entry/src/main/ets/calculator/BaseConverter.ets` | 纯函数工具类：DEC→BIN/OCT/HEX 转换；NaN/Infinity 防御；toString(0) 截断小数 |
| `opencalc/entry/src/test/ets/calculator/BaseConverter.test.ets` | 单元测试覆盖 |
| `specs/changes/20260615-requirement-add-简单需求/tests/BaseConverter.test.mjs` | Node 端口（环境无 java 时的本地验证） |

### 调用链
```
用户点击模式按钮
  → CalculatorPage.onModeChange(mode)
       → savePref('mode', mode)
       → PreferencesStore.setMode(mode)
       → @State mode = mode 触发 @Watch('onModeChange')
  → CalculatorPage.onEquals() 触发
       → CalcEngine.evaluate()
       → NumberFormatter.format() // DEC 主结果
       → BaseConverter.convert(result, NumberBase.DEC/BIN/OCT/HEX) // 多进制行
       → @State baseConversions = { dec, bin, oct, hex }
```

## 现有代码分析

### CalculatorPage 模式相关代码（line 22-69）
```typescript
@State scientific: boolean = false    // 当前二选一
async loadPrefs(): Promise<void> {
  this.scientific = (await this.prefs.getScientificModeDefault()) === 1
}
async savePref(key: string, value: boolean | number): Promise<void> {
  if (key === 'scientific') await this.prefs.setScientificModeDefault(value as number)
}
```

### ToggleRow (line 384-397)
```typescript
@Builder ToggleRow() {
  Row() {
    Text(this.scientific ? '科学' : '基础')
      .onClick((): void => { this.scientific = !this.scientific })
    Blank()
    Text(this.showHistory ? '▲ 历史' : '▼ 历史')
      .onClick((): void => { this.showHistory = !this.showHistory })
    Text('⚙')
      .onClick((): void => { this.showSettings = true })
  }
}
```

### ButtonGrid (line 400-413)
- 5 列布局：科学模式时显示 sin/cos/tan/ln/log 行 + 常量行
- 基础模式时直接显示 5 列数字键盘
- 需拆为 3 个 @Builder：BasicKeypad/ScientificKeypad/ProgrammerKeypad

## 风险识别

### 风险清单

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| `@State scientific: boolean` 重构为 `mode: CalculatorMode` 可能引入回归 | 中 | 保留 loadPrefs/savePref 兼容逻辑；新增测试覆盖模式切换 |
| ArkUI 中条件渲染 SegmentedControl 在横屏下布局可能错乱 | 中 | 横屏下隐藏按钮标签只显示图标 |
| BIN/OCT/HEX 转换对负数/NaN/Infinity 处理不当 | 中 | BaseConverter 显式处理边界值；单元测试覆盖 |
| `toString(0)` 对超大整数精度损失 | 低 | IEEE 754 安全整数 (2^53 - 1) 范围内足够；显示截断提示 |
| 模式切换动画在 ArkTS 中转场性能开销 | 低 | 仅键盘区域动画；fade 200ms + slide 8px（轻量） |
| 现有实时预览在程序员模式下仍可能产生错误（如小数显示） | 低 | 程序员模式 preview 隐藏，仅主结果 + 多进制显示 |
| 横屏下 SegmentedControl 占用空间挤压键盘 | 低 | 横屏下隐藏切换标签，仅显示图标 |

### 技术难点
- ArkTS 中 transition 动画需要使用 `transition()` 修饰符 + enter/exit 子属性
- `Math.trunc` + `Number.toString(base)` 在 ArkTS 中可用（标准 ECMAScript）
- 大整数（> 2^53）需使用 string 操作或 BigInt，**不在本需求范围**

## 测试验证策略

### 测试场景

| 场景 | 验证方法 |
|------|---------|
| BaseConverter.convert(255, BIN) → "11111111" | 单元测试 |
| BaseConverter.convert(255, OCT) → "377" | 单元测试 |
| BaseConverter.convert(255, HEX) → "FF" | 单元测试 |
| BaseConverter.convert(-1, BIN) → "-1" | 单元测试（负数前缀） |
| BaseConverter.convert(3.14, BIN) → "11"（截断小数） | 单元测试 |
| BaseConverter.convert(NaN, BIN) → "-" | 单元测试 |
| BaseConverter.convert(Infinity, BIN) → "-" | 单元测试 |
| 模式切换 BASIC → PROGRAMMER | UI 测试 |
| 程序员模式下输入 255 + =，主结果 DEC=255, BIN=11111111 | UI 测试 |
| activeBase 切换 DEC → HEX，主结果显示 0xFF | UI 测试 |
| 模式切换动画 fade + slide 200ms | 视觉验证 |

### 验收标准
- 模式切换无回归（基础/科学模式行为不变）
- BaseConverter 单元测试覆盖率 ≥ 90%
- UI 自动化测试覆盖模式切换 + 主进制切换
- 不破坏现有 AC-1..AC-12 百分号测试

## 监控运维支持

### 监控指标
- 模式切换次数（AppStorage 可选，本期不实现）
- activeBase 切换次数（本期不实现）

### 配置清单
| 配置项 | 默认值 | 持久化键 |
|--------|--------|----------|
| mode | CalculatorMode.BASIC | 'mode' |
| activeBase | NumberBase.DEC | 'activeBase' |

### 日志要点
- 模式切换：本期不输出日志（业务简单）

## 关键发现

### 可复用组件或函数
- `NumberFormatter.format()` — DEC 主结果格式化
- `CalcEngine.evaluate()` — DEC 计算引擎
- `Expression.getCleanExpression()` — 表达式预处理
- `@Builder` 拆分为 BasicKeypad/ScientificKeypad/ProgrammerKeypad
- `@Watch('onExpressionChange')` 模式 — 多进制显示行同步刷新
- `harmonyos-ui-test` skill — UI 自动化测试
- `127.0.0.1:5555` emulator running — 端到端验证

### 风险提示
- `@State scientific: boolean` 重构为 `@State mode: CalculatorMode` 涉及 **破坏性变更**：需要保留 loadPrefs/savePref 兼容路径
- 现有 `BtnFunc`/`BtnConst` 不适用于程序员模式，需新增 `BtnHexLetter`/`BtnBin` 按钮 builder

### 测试能力评估
- 单元测试能力: ✅
- UI 自动化测试能力: ✅（hdc + 127.0.0.1:5555 running）
- 端到端集成测试能力: ✅
- 不能跑的实际原因: 无

### 建议事项
1. **优先级 1**：新建 BaseConverter.ets + 单元测试（独立模块，无依赖风险）
2. **优先级 2**：扩展 Models.ets + PreferencesStore.ets（向后兼容）
3. **优先级 3**：重构 CalculatorPage.ets 拆分键盘 + 新增多进制面板 + 模式切换动画
4. **使用 .transition() 实现 fade + slide 动画**（ArkUI 内置，无新依赖）