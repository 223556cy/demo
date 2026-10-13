# 程序员模式 (Issue #22) — 代码仓理解

## 基本信息
- **需求类别**：新增功能 (requirement-add)
- **需求名称**：程序员模式（BIN/OCT/DEC/HEX 转换 + 模式切换动画）
- **分析时间**：2026-06-17
- **分析范围**：`opencalc/entry/src/main/ets/`（计算器 App 入口、引擎、UI、模型、偏好设置、转换器）

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- UI 自动化测试能力: ✅ 可用 (hdc + 模拟器)
- 模拟器列表: 127.0.0.1:5555
- hdc: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- 单元测试框架: hypium + hamock

## 1. 架构分析

### 1.1 系统模块结构

```
opencalc/entry/src/main/ets/
├── calculator/                      # 计算引擎层（无 UI 依赖）
│   ├── Calculator.ets               # 递归下降解析器 (CalcEngine)
│   ├── Expression.ets               # 表达式预处理（百分号、清理）
│   └── NumberFormatter.ets          # 数字格式化（千分位/小数）
├── model/                           # 数据模型
│   ├── ErrorFlags.ets               # 错误标志位全局
│   └── Models.ets                   # 枚举 + 接口（HistoryItem, CalculatorPreferences）
├── preferences/                     # 持久化层
│   └── PreferencesStore.ets         # @ohos.data.preferences 封装
├── common/                          # 基础设施
│   ├── NaturalLanguageParser.ets    # NL 解析（#18）
│   └── UnitConverter.ets            # 单位换算（#18）
├── history/
│   └── HistoryGroup.ets             # 历史分组（#15）
├── qrcode/
│   └── QrCodeBuilder.ets            # 二维码分享（#13）
├── entryability/
│   └── EntryAbility.ets             # 鸿蒙 UIAbility 入口
└── pages/                           # 视图层
    ├── Index.ets                    # 启动页（router 跳 CalculatorPage）
    ├── CalculatorPage.ets           # 主页面（797 行，单文件承载所有状态）
    └── LongPressMenu.ets            # 长按菜单（#16）
```

### 1.2 MVVM 分层

| 层 | 当前实现 | 本次变更 |
|----|---------|---------|
| View | `CalculatorPage.ets`（单文件结构体 + @Builder） | 扩展 Page + 新增 `ProgrammerPanel.ets` 组件 |
| ViewModel | **无独立目录** — 状态全在 `CalculatorPage.ets` 内（@State 字段 + 私有方法） | 复用 Page 内联模式；新增 `BaseConverter.ets` 工具作为 ViewModel 辅助 |
| Model | `model/Models.ets` 枚举与接口 | 新增 `NumberBase` / `CalculatorMode` 枚举 |
| 基础设施 | `common/`, `preferences/` | 复用 `PreferencesStore` 模式新增 `getProgrammerMode` / `setProgrammerMode` |

### 1.3 模块依赖关系
- `Calculator.ets` → `model/ErrorFlags.ets`（错误位）
- `CalculatorPage.ets` → `calculator/*`, `model/*`, `preferences/*`, `common/*`, `history/*`, `qrcode/*`, `pages/LongPressMenu.ets`
- `PreferencesStore.ets` → `model/Models.ets`（CalculatorPreferences 接口）
- `LongPressMenu.ets` → 纯静态类（无依赖）

### 1.4 扩展点
- `@ohos.data.preferences`：键值对持久化（每个偏好一个 getX/setX 方法）
- `@ohos.arkui.Animator` / `animateTo`：暂未使用，本次新增动画需引入
- `promptAction.showToast`：Toast 提示

## 2. 接口/契约识别

### 2.1 CalculatorPage 暴露的方法
- `onDigit(d: string)`, `onOp(op: string)`, `onFunc(f: string)`, `onConst(c: string)`, `onBS()`, `onAC()`, `onEquals()` — 输入事件
- `onCopy()` — 复制结果
- `onLongPress(label)`, `onLongPressCandidate(item)` — 长按菜单（#16）
- `onPaste()` — 粘贴即计算（#17）
- `onShareClick()`, `onShareClose()` — 分享二维码（#13）
- `onHistoryTap(item)`, `onHistoryDelete(item)`, `getHistorySections()` — 历史
- `savePref(key, value)` — 写偏好（白名单 5 个 key）

### 2.2 PreferencesStore 暴露的 API（现有）
- `getTheme/setTheme`, `getForceDayNight/setForceDayNight`
- `getVibrationEnabled/setVibrationEnabled`, `getPreventSleep/setPreventSleep`
- `getHistorySize/setHistorySize`, `getHistory/setHistory`
- `getScientificModeDefault/setScientificModeDefault`（数字 0/1/2）
- `getRadiansDefault/setRadiansDefault`
- `getNumberPrecision/setNumberPrecision`
- `getDecimalSeparator/setDecimalSeparator`, `getGroupingSeparator/setGroupingSeparator`
- `getAllPreferences()`

### 2.3 待新增契约
- `PreferencesStore.getProgrammerModeDefault() / setProgrammerModeDefault(value: boolean)` — 持久化模式选择
- `BaseConverter.toBase(n: number, base: NumberBase): string` — 转字符串
- `BaseConverter.fromBase(s: string, base: NumberBase): number` — 反解析（NaN 表示非法）
- `BaseConverter.getRepresentations(n: number): Map<NumberBase, string>` — 四进制映射
- `CalculatorPage.setMode(mode: CalculatorMode)` — 切换模式（带动画）

## 3. 公共组件或函数识别（可复用）

| 名称 | 路径 | 用途 | 复用方式 |
|------|------|------|---------|
| `CalcEngine.evaluate(eq, isDegree)` | `calculator/Calculator.ets` | 算式求值 | 程序员模式 DEC 行的算式复用，**无需修改** |
| `NumberFormatter.format()` | `calculator/NumberFormatter.ets` | 千分位 | **不适用**（BIN/OCT/HEX 不加千分位） |
| `PreferencesStore` 模板 | `preferences/PreferencesStore.ets` | getX/setX 模式 | **完全复用**，新增 `getProgrammerModeDefault` |
| `@Watch('onExpressionChange')` | `CalculatorPage.ets:23` | expression 变动回调 | **复用** — 程序员模式 DEC 值随之重算 |
| `LongPressGesture()` | `CalculatorPage.ets:656` | 长按手势 | 程序员模式 BIN/OCT/HEX 行可点击可参照此模式 |
| `ForEach` + ListItem | `CalculatorPage.ets:691` | 分组列表 | 模式切换器可用 ForEach 渲染 4 行进制 |
| `promptAction.showToast` | `CalculatorPage.ets:271` | 提示 | 复用（如"已切换到程序员模式"） |
| 主题颜色 getters | `CalculatorPage.ets:394-458` | getBg/getBtnBg/getT1/getT2 | **完全复用** — 程序员面板继承主题 |

## 4. 影响范围分析

### 4.1 需要修改的文件清单
| 文件 | 修改内容 | 风险 |
|------|---------|------|
| `pages/CalculatorPage.ets` | 新增 `mode`/`activeBase` 状态；新增 `setMode()`/`onProgrammerBaseTap()`；`ToggleRow` 增加入口；`build()` 条件渲染；`ButtonGrid` 模式分支 | 中（单文件大改动） |

### 4.2 需要新增的文件清单
| 文件 | 内容 |
|------|------|
| `calculator/BaseConverter.ets` | 纯逻辑工具类（无 UI 依赖），便于单元测试 |
| `model/ModeModel.ets` | `NumberBase` / `CalculatorMode` / `ProgrammerDisplayState` 枚举与接口 |
| `pages/ProgrammerPanel.ets` | 4 行进制展示 + A-F 键盘的子组件 |
| `entry/src/test/ets/calculator/BaseConverter.test.ets` | 单元测试套件 |

### 4.3 调用链
```
用户点击"模式"按钮
  → onModeToggle()
  → promptAction.showActionSheet()  // 选 STANDARD/PROGRAMMER
  → setMode(mode)
  → animateTo { mode change }  // 220ms 过渡
  → persistProgrammerMode(mode === PROGRAMMER)

用户在程序员模式下点 BIN 行
  → onProgrammerBaseTap(BIN)
  → BaseConverter.fromBase(currentBinStr, BIN) → n
  → expression = n.toString()
  → activeBase = BIN
```

### 4.4 影响评估
- **现有功能**：标准模式所有交互（数字键、运算符、函数、长按菜单、复制、粘贴、历史、分享、NL 单位换算）完全不变
- **数据兼容**：不修改现有 `CalculatorPreferences` 字段；新增独立 key `programmerModeDefault`（boolean），向老版本兼容（缺省回退 false）
- **测试影响**：现有 7 个测试套件无需修改；新增 1 个 BaseConverter 套件

## 5. 现有代码分析

### 5.1 Calculator.ets 关键逻辑
- 入口：`evaluate(equation, isDegree): number` — 接受表达式字符串和角度模式
- 数字识别：`(c >= 48 && c <= 57) || c === 46` — ASCII '0'-'9' 或 '.'
- 解析流程：`parseExpression` → `parseTerm` → `parseFactor` → 数字/函数/常量
- **重要**：**本引擎只接受十进制数字字面量**，BIN/OCT/HEX 字符串需要先转换为 number 再喂入引擎

### 5.2 NumberFormatter.ets 关键逻辑
- `format(text, decSep, grpSep, numberingSystem)` — 主入口
- `formatIntegers()` — 千分位
- **不适用场景**：BIN/OCT/HEX 字符串可能含 'A'-'F'，不应走 `format()`，需直接展示

### 5.3 状态管理模式（参考 #16 长按菜单）
- `showLongPressMenu: boolean` + `longPressSource: string` — 状态独立
- 关闭路径：候选点击、外部点击 — 都设置 `showLongPressMenu = false`
- 模板：程序员模式 `showModeSheet: boolean` + `pendingMode: CalculatorMode`

### 5.4 边界条件
- 负数：`expression` 以 `-` 开头，`parseFloat` 直接处理
- Number.MAX_SAFE_INTEGER = 2^53-1 = 9007199254740991，超出后精度丢失
- `parseInt` 的基数：传入字符串带进制字符（如 '1F'），`parseInt('1F', 16) = 31`

## 6. 风险识别

### 6.1 技术风险
| # | 风险 | 缓解 |
|---|------|------|
| R1 | BIN/OCT/HEX 显示很长（64 bit → 19 位），挤压屏幕 | 字号缩小到 12-14，横向滚动支持 |
| R2 | JS Number 精度上限（2^53），超界显示不一致 | 显示提示 "数值过大，已截断" |
| R3 | 用户在 BIN 行点击反解析：'1F0' 是合法 HEX，但 '2' 不是 | `parseInt` 返回 NaN 时回退到当前 activeBase 输入 |
| R4 | animateTo 在 @Builder 嵌套内可用性 | 参考官方文档；用组件级别的 `transition` 属性 |
| R5 | 模式切换后历史记录是否带"模式"标签 | 本期**不做**，历史模式标签作为后续扩展 |

### 6.2 兼容性风险
- 现有横屏布局右侧历史面板、左侧按钮：程序员模式在横屏下保留同样布局
- 现有 ToggleRow 中"科学"/"基础"按钮、粘贴按钮、历史按钮、分享按钮、设置按钮都保留；新增"模式"按钮在 ToggleRow 头部

### 6.3 测试能力评估
- **单元测试能力**: ✅ hypium + hamock 框架已就位
- **UI 自动化测试能力**: ✅ hdc 3.2.0d + 模拟器 127.0.0.1:5555 已可用（`harmonyos-ui-test` skill）
- **端到端集成测试能力**: ✅ 可用 hdc shell 启动应用后跑脚本
- **不能跑的实际原因**: 无（环境齐全）

## 7. 测试验证策略

### 7.1 单元测试（BaseConverter.test.ets）
| AC# | 用例 | 期望 |
|-----|------|------|
| AC-1 | toBase(0, BIN) | "0" |
| AC-2 | toBase(10, BIN) | "1010" |
| AC-3 | toBase(8, OCT) | "10" |
| AC-4 | toBase(255, HEX) | "FF" |
| AC-5 | toBase(-10, BIN) | "-1010" |
| AC-6 | toBase(10.7, BIN) | "1010" (取整) |
| AC-7 | toBase(2^53, BIN) | 触发 overflow flag |
| AC-8 | fromBase("FF", HEX) | 255 |
| AC-9 | fromBase("1010", BIN) | 10 |
| AC-10 | fromBase("XYZ", BIN) | NaN（校验失败） |
| AC-11 | getRepresentations(10) | {BIN:"1010", OCT:"12", DEC:"10", HEX:"A"} |
| AC-12 | 0 的四进制 | {BIN:"0", OCT:"0", DEC:"0", HEX:"0"} |

### 7.2 UI 测试（harmonyos-ui-test skill）
- AC-U1: 启动 App 默认进入标准模式
- AC-U2: 点击"模式"按钮 → 弹出 ActionSheet 选"程序员"
- AC-U3: 切换后 220ms 动画完成，4 行进制显示
- AC-U4: 数字键 10 → BIN 显示 "1010"，OCT "12"，HEX "A"
- AC-U5: 点击 HEX 行 → activeBase 切到 HEX
- AC-U6: 在 HEX 模式下按 'F' → 正确追加
- AC-U7: 在 HEX 模式下按 '2' → 弹 Toast "HEX 不支持字符 2"
- AC-U8: 重启 App → 默认进入程序员模式（持久化生效）

## 8. 监控运维支持

### 8.1 配置项
- `programmerModeDefault`: boolean (false=标准, true=程序员)
- `programmerActiveBase` (可选): 默认 DEC，后续可加入

### 8.2 日志要点
- 模式切换：`console.info('[Mode] switched to ' + mode)`
- 进制溢出：`console.warn('[BaseConverter] overflow at n=' + n)`

### 8.3 持久化 key
| key | 类型 | 默认 | 用途 |
|-----|------|------|------|
| `programmerModeDefault` | boolean | false | 启动默认模式 |

## 关键发现

### 可复用组件或函数
- `PreferencesStore` 的 getX/setX 模板 — 100% 复用，新增一个 key
- `CalculatorPage.ets` 的 `@Builder` + `Stack().if()` 条件渲染模式
- 主题颜色 getters — 程序员面板完全复用
- `@Watch('onExpressionChange')` — DEC 值随 expression 变化自动更新
- `harmonyos-ui-test` skill — UI 自动化测试

### 风险提示
- animateTo 在本项目尚无使用先例，需对照官方文档实施
- BIN/OCT/HEX 字符串解析需绕过现有 `CalcEngine`（引擎不识别字母数字）
- 横屏布局下程序员面板与历史面板共存需测试视觉冲突

### 建议事项
- 新增 `model/ModeModel.ets` 而非塞入 `Models.ets`（保持模块清晰）
- `BaseConverter` 用静态方法 + 纯函数实现，零 ArkUI 依赖，方便 hypium 测试
- 模式入口在 ToggleRow 头部（"基础/科学"按钮旁）增加第二个切换按钮，避免冲突
- 程序员键盘使用独立 5×4 网格（0-9 + A-F + 操作符），不要复用现有 BtnDig
