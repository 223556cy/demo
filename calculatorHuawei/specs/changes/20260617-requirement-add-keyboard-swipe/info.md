# Issue #29 — 代码仓理解

## 基本信息

- **需求类别**: 新增功能 (requirement-add)
- **需求名称**: 竖屏手势滑动切换三种键盘模式 (基础/科学/程序员)
- **分析时间**: 2026-06-17
- **分析范围**: CalculatorPage.ets / Models.ets / PreferencesStore.ets / resources

## 环境能力（来自 .claude/capabilities.json）

- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- UI 自动化测试能力: ✅ true
- 模拟器列表: ["127.0.0.1:5555"]
- 模拟器状态: running
- hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- SDK: D:/Program Files/Huawei/DevEco Studio/sdk
- java: openjdk 21.0.8

## 架构分析

```
opencalc/entry/src/main/ets/
├── calculator/
│   ├── Calculator.ets          # 计算引擎 (CalcEngine 类)
│   ├── Expression.ets          # 表达式构造器
│   └── NumberFormatter.ets    # 数字格式化
├── common/
│   ├── NaturalLanguageParser.ets  # NL 单位识别 (issue #18)
│   └── UnitConverter.ets          # 单位换算 (issue #14/#18)
├── entryability/               # Ability 入口
├── history/
│   └── HistoryGroup.ets        # 历史分组 (issue #15)
├── model/
│   └── Models.ets              # 数据模型 + 枚举 (CalculatorError / NumberingSystem / ScientificModeType / HistoryItem / CalculatorPreferences)
├── pages/
│   ├── CalculatorPage.ets      # ★ 本需求核心修改页 (1447 行)
│   ├── Index.ets
│   └── LongPressMenu.ets       # 长按弹菜单 (issue #16)
├── preferences/
│   └── PreferencesStore.ets    # 偏好持久化 ★
└── qrcode/
    └── QrCodeBuilder.ets       # 二维码分享 (issue #13)
```

### 关键模块职责

- **CalculatorPage.ets**: 主页,持有 expression/result/scientific/history 等 @State,通过 PreferencesStore 读写偏好。
- **PreferencesStore.ets**: 封装 @ohos.data.preferences,所有 setXxx 立即 flush,getXxx 提供默认值兜底。
- **Models.ets**: 全部枚举和接口定义,CalculatorPreferences 是 preferences 强类型镜像。

### 模块依赖关系

```
CalculatorPage ──→ Models (枚举/接口)
              ──→ PreferencesStore (持久化)
              ──→ calculator/* (引擎)
              ──→ common/* (NL/单位)
              ──→ history/* (分组)
              ──→ qrcode/* (分享)
              ──→ LongPressMenu (弹菜单)
```

## 接口/契约识别

### 关键接口清单

| 接口 | 位置 | 用途 | 本次影响 |
|------|------|------|----------|
| `CalculatorPreferences.scientificModeDefault` | Models.ets:42 | 旧字段,默认科学模式状态 | **保留**,语义不变 |
| `CalculatorPreferences.programmerModeDefault` | Models.ets (NEW) | **新增**,程序员模式默认状态 | NEW |
| `PreferencesStore.getScientificModeDefault/setScientificModeDefault` | PreferencesStore.ets:138-148 | 读写 scientificModeDefault | 保留,新增镜像 `getProgrammerModeDefault/setProgrammerModeDefault` |
| `CalculatorPage.scientific: boolean` | CalculatorPage.ets:28 | @State 当前模式 (true=科学) | **重构** 为 `currentMode: KeyboardMode` |
| `CalculatorPage.ToggleRow()` | CalculatorPage.ets:604-627 | 模式切换按钮 (text: 科学/基础) | **修改**,label 跟随 currentMode 三态 |
| `CalculatorPage.ButtonGrid()` | CalculatorPage.ets:630-643 | 按钮网格,根据 `scientific` 条件渲染 | **重构**,三页 Swiper 包裹 |

### 调用约束

- `@ohos.data.preferences` 单实例 (key=opencalc_preferences),字段名不可冲突。
- ArkUI 组件 `@State` 修饰的字段变化会触发 UI 重渲染,需谨慎避免循环触发。
- `Swiper.index` 与外部状态双向绑定时,必须保证单向数据流。

## 公共组件或函数识别

| 组件/函数 | 位置 | 可复用性 | 说明 |
|------|------|----------|------|
| `ToggleRow()` @Builder | CalculatorPage.ets:604 | 直接复用 | 仅修改 label/onClick |
| `ButtonGrid()` @Builder | CalculatorPage.ets:630 | 重构 | 三页 → Swiper 包裹 |
| `BtnDig/BtnOp/BtnFunc/BtnConst/BtnAct/BtnEq/BtnOpPct/BtnActPct` | CalculatorPage.ets:646-672 | 直接复用 | 程序员页可复用 `BtnFunc/BtnOp/BtnDig` 等 |
| `getOp/getBtnBg/getFuncBg/getT1/getT2/getEq/getBtnText/getClr/getPanelBg` | CalculatorPage.ets 颜色方法 | 直接复用 | 程序员页键颜色一致 |
| `harmonyos-ui-test` skill | .claude/skills | UI 自动化 | 本次需要做 UI 自动化测试 |
| `tdd-enforcer` skill | .claude/skills | TDD 强约束 | APPLYING 阶段使用 |

## 影响范围分析

### 需要修改的文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `model/Models.ets` | extend | 新增 `KeyboardMode` 枚举 + `programmerModeDefault` 字段 |
| `preferences/PreferencesStore.ets` | extend | 新增 `getProgrammerModeDefault / setProgrammerModeDefault` |
| `pages/CalculatorPage.ets` | modify | `@State scientific` → `@State currentMode`;外层 Swiper 包裹键盘区;模式按钮 label + onClick 循环 |
| `resources/base/element/string.json` | extend | 新增 "程序员" / "进制" / 位运算键名等 |

### 需要新建的文件清单 (建议)

| 文件 | 说明 |
|------|------|
| `pages/CalculatorPage.ProgrammerGrid.ets` (可选) | 程序员键盘布局,可独立 @Builder 文件 |
| `test/ets/pages/CalculatorPage.mode.test.ets` (可选) | 模式状态机单元测试 |

### 调用链分析

```
启动 App
  → EntryAbility
  → CalculatorPage (aboutToAppear)
    → PreferencesStore.init
    → loadPrefs() ← scientificModeDefault / programmerModeDefault 读取
    → loadHistory()
    → UI 首次渲染 (按 currentMode 决定 Swiper index)
用户切换模式:
  路径A (手势): Swiper.onChange → modeController.onSwiperChange → setXxx + currentMode 更新
  路径B (按钮): onClick → modeController.cycleMode → setXxx + Swiper.changeIndex + currentMode 更新
```

### 修复/实现方案

- **三页 Swiper**: `Swiper() { BasicGrid(); ScientificGrid(); ProgrammerGrid() }`,index 由 currentMode 派生,关闭循环。
- **DotIndicator**: `Swiper({ indicator: new DotIndicator() })`。
- **模式状态机**: `cycleMode() { currentMode = (currentMode + 1) % 3 }`。
- **单向数据流**: Swiper.onChange 是唯一修改 currentMode 的入口,按钮点击通过 SwiperController.changeIndex + onChange 触发。

## 现有代码分析

### 关键代码逻辑

- CalculatorPage.ets:67 — `this.scientific = (await this.prefs.getScientificModeDefault()) === 1`
- CalculatorPage.ets:82 — `else if (key === 'scientific') await this.prefs.setScientificModeDefault(value as number)`
- CalculatorPage.ets:524 — `if (this.isLandscape) this.scientific = true` (横屏强制科学)
- CalculatorPage.ets:604-627 — `ToggleRow()` 模式切换栏,label `'科学'/'基础'`,onClick toggle
- CalculatorPage.ets:630-643 — `ButtonGrid()` 条件渲染 `if (this.scientific) { 科学键两行 }`

### 关键变量

- `scientific: boolean` — 当前是否是科学模式
- `isLandscape: boolean` — 横屏状态,影响布局
- `expression/result/preview` — 输入输出

### 边界条件

- 横屏 (`isLandscape=true`) 强制 `scientific=true`,不显示 ToggleRow(?)
- 模式切换后 expression 保留,只切换键盘
- 旧字段 `scientificModeDefault` 必须保留语义(向后兼容)

## 风险识别

### 技术风险

| # | 风险 | 等级 | 缓解措施 |
|---|------|------|----------|
| R1 | Swiper 与 TextArea 手势冲突 | 高 | Swiper 包裹键盘区,TextArea 放在 Swiper 外 |
| R2 | Swiper.index 与 currentMode 双向绑定形成循环 | 中 | onChange 单向触发,按钮通过 SwiperController 改变 index |
| R3 | 横屏 isLandscape=true 时 Swiper 渲染浪费 | 低 | 横屏不渲染 Swiper,继续用原 ButtonGrid |
| R4 | 旧 `scientificModeDefault` 字段语义需保持 | 低 | 新增独立 `programmerModeDefault`,启动优先级 SCIENTIFIC > PROGRAMMER > BASIC |
| R5 | preferences 写入失败影响 UI | 低 | try-catch 包装 setXxx |
| R6 | Swiper 默认循环可能让用户从 PROGRAMMER 滑回 PROGRAMMER | 低 | 设置 `loop=false` |
| R7 | 程序员键盘是新增功能,缺少 CalcEngine 支持位运算 | 中 | 范围限定:UI 层提供按键入口,CalcEngine 解析失败时降级(本期可不接 CalcEngine,显示提示) |

### 测试能力评估

- 单元测试能力: ✅ (hypium+hamock)
- UI 自动化测试能力: ✅ (hdc + 模拟器,harmonyos-ui-test skill)
- 端到端集成测试能力: ✅ (build → install → uitest)
- 不能跑的实际原因: 无,环境就绪

## 测试验证策略

### 单元测试场景

| 场景 | 验证内容 |
|------|----------|
| UT-01 | `cycleMode()` BASIC → SCIENTIFIC → PROGRAMMER → BASIC 循环 |
| UT-02 | `modeController.onSwiperChange(0/1/2)` 三态切换 |
| UT-03 | `PreferencesStore.setProgrammerModeDefault` 写入成功 |
| UT-04 | `getAllPreferences` 返回新字段 programmerModeDefault |
| UT-05 | 启动时 prefs 优先级: SCIENTIFIC > PROGRAMMER > BASIC |

### UI 自动化测试场景

| 场景 | 验证内容 |
|------|----------|
| UI-01 | 竖屏从 BASIC 左滑到 SCIENTIFIC,圆点指示器更新 |
| UI-02 | 竖屏从 SCIENTIFIC 右滑回 BASIC |
| UI-03 | 竖屏从 SCIENTIFIC 左滑到 PROGRAMMER,程序员键盘可见 |
| UI-04 | 点击模式按钮 label 从 基础→科学→程序员→基础 循环 |
| UI-05 | 重启 App,模式恢复 |
| UI-06 | 横屏不显示 Swiper,继续只显示科学模式 |

### 验收标准

- 编译通过: `hvigorw --no-daemon assembleHap` 退出码 0
- 单元测试通过: `hvigorw --no-daemon test` 全部 PASS
- UI 测试通过: harmonyos-ui-test skill 跑完 UI-01 ~ UI-06
- 向后兼容: 旧版本 preferences (只有 scientificModeDefault) 启动正常

## 监控运维支持

- 监控指标: 模式切换次数(本期不实现)
- 配置项: `programmerModeDefault` 默认 0 (BASIC)
- 日志记录点: `onSwiperChange` 进入时 console.info,prefs 写入失败时 console.error

## 关键发现

### 可复用组件或函数
- `BtnDig/BtnOp/BtnFunc/BtnConst/BtnAct/BtnEq` 等 @Builder 可直接复用
- `getOp/getBtnBg/getFuncBg` 颜色方法复用
- `harmonyos-ui-test` skill 直接用于 UI 自动化

### 风险提示
- R1 (手势冲突) 是最高风险点,需要 Swiper 仅包裹键盘区,TextArea 独立
- R7 (CalcEngine 不支持位运算) 决定程序员键盘仅作 UI 展示,实际计算降级

### 建议事项
1. 优先保证 Swiper + 三页键盘可演示,程序员键盘可点击但 CalcEngine 暂不深度集成
2. 模式按钮的 onClick 仍走 cycleMode → SwiperController.changeIndex → onChange 单向链路
3. 启动时同步设置 Swiper index 与 currentMode,避免首次渲染闪烁
4. 旧字段 `scientificModeDefault` 保留,新字段 `programmerModeDefault` 仅在用户进入程序员模式时写入 1