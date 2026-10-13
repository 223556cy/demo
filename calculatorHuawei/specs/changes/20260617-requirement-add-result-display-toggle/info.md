# Info: 计算结果支持小数和分数两种显示，自由切换 - 代码仓理解

## 基本信息

- **需求类别**：新增功能
- **需求名称**：结果小数/分数显示切换
- **Issue**：#27
- **分析时间**：2026-06-17
- **分析范围**：`opencalc/entry/src/main/ets/{calculator, model, preferences, pages, common}`

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- UI 测试能力: ✅ true (skill: harmonyos-ui-test)
- 模拟器列表: ["127.0.0.1:5555"]
- hdc: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- bundleName: com.darkempire78.opencalculator

## 架构分析

### 模块结构
```
opencalc/entry/src/main/ets/
├── calculator/            # 计算引擎层
│   ├── Calculator.ets           # CalcEngine.evaluate(expr, degrees)
│   ├── Expression.ets           # 表达式解析/格式化
│   └── NumberFormatter.ets      # 千分位/小数格式化
├── model/                 # 数据模型
│   ├── ErrorFlags.ets           # 全局错误标志位
│   └── Models.ets               # CalculatorPreferences, HistoryItem, enums
├── preferences/           # 持久化层
│   └── PreferencesStore.ets     # @ohos.data.preferences 封装
├── pages/                 # UI 页面
│   ├── CalculatorPage.ets       # 主计算器页（@Entry）
│   ├── Index.ets                # 入口
│   └── LongPressMenu.ets        # 长按弹窗组件
├── history/               # 历史分组
├── common/                # 工具
├── qrcode/                # 二维码
└── entryability/          # UIAbility
```

### 模块依赖关系
```
CalculatorPage (@Entry, 796行)
  ├── calculator/Calculator       (CalcEngine)
  ├── calculator/Expression       (getCleanExpression)
  ├── calculator/NumberFormatter  (format)
  ├── model/Models                (NumberingSystem, HistoryItem)
  ├── model/ErrorFlags            (错误标志)
  ├── preferences/PreferencesStore (持久化)
  ├── common/NaturalLanguageParser
  ├── common/UnitConverter
  ├── qrcode/QrCodeBuilder
  ├── history/HistoryGroup
  └── pages/LongPressMenu
```

### MVVM 分层
- **View**: CalculatorPage.ets (ArkUI 声明式)
- **ViewModel**: CalculatorPage 内的 @State 字段
- **Model**: calculator/, model/ 下的纯逻辑

## 接口/契约识别

### 关键接口
1. **`NumberFormatter.format(text, decimalSep, groupingSep, numberingSystem): string`**
   - 现有签名：返回带千分位/小数点的字符串
   - 扩展点：可在调用前判断 DisplayMode，分数模式直接走 FractionUtil
   
2. **`CalcEngine.evaluate(cleanExpr, degrees): number`**
   - 纯计算，不做显示
   - 不需修改

3. **`PreferencesStore.getXxx()/setXxx()` 模式**
   - 已有：`getTheme/setTheme`、`getRadiansDefault/setRadiansDefault` 等
   - 扩展：新增 `getResultDisplayMode/setResultDisplayMode`，与 `getRadiansDefault` 同模式

4. **`CalculatorPage.onEquals()`**
   - 当前逻辑：计算 → NumberFormatter.format → 存 result → 写历史
   - 扩展点：需要同时缓存 raw 数值（用于分数模式重新格式化），且 onEquals 后立即按当前 DisplayMode 重新显示

5. **`CalculatorPage.computePreview()`**
   - 实时预览，目前返回小数形式
   - 扩展点：预览仍走小数（分数预览不直观），无需修改

## 公共组件或函数识别

### 可复用
- `NumberFormatter` (calculator/NumberFormatter.ets, 176行)：已处理千分位/印度制，无需重写
- `PreferencesStore` 模板：每个偏好的 getter/setter 都遵循相同模式，新增 `resultDisplayMode` 一致
- `CalculatorPage` 内的事件处理函数（如 `onEquals`、`loadPrefs`）作为参考模板

### 测试相关（按 capabilities.json 强制）
- **UI 自动化测试 skill**: `harmonyos-ui-test`（可用，hdc 路径已配）
- **可用模拟器**: `127.0.0.1:5555`
- **单元测试框架**: hypium + hamock（命令: `hvigorw --no-daemon test`）
- **单元测试根**: `opencalc/entry/src/test/`

### 需新增
- `common/FractionUtil.ets`：纯函数工具（GCD、number→fraction、fraction 格式化）
- `model/DisplayMode.ets`：枚举
- `model/Models.ets` 扩展：增加 `resultDisplayMode` 字段到 `CalculatorPreferences`
- `preferences/PreferencesStore.ets` 扩展：增加 `getResultDisplayMode/setResultDisplayMode`

## 影响范围分析

### 需修改/新增的文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `common/FractionUtil.ets` | new | GCD + number→fraction 转换 + fraction 格式化 |
| `model/Models.ets` | modify | 新增 `DisplayMode` 枚举 + `CalculatorPreferences` 加 `resultDisplayMode` 字段 + `DEFAULT_PREFERENCES` 默认值 |
| `preferences/PreferencesStore.ets` | modify | 新增 `getResultDisplayMode/setResultDisplayMode` + `getAllPreferences` 加新字段 |
| `pages/CalculatorPage.ets` | modify | 加 `@State displayMode: DisplayMode`；在结果区右侧加 toggle 按钮；onEquals 缓存 `rawResult: number` 用于重格式化；切换时刷新 result 显示 |
| `opencalc/entry/src/test/common/FractionUtil.test.ets` | new | 单元测试（GCD、化简、负数、超大分母回退、NaN 处理） |
| `opencalc/entry/src/test/preferences/PreferencesStore.test.ets` | modify | 增加 DisplayMode 持久化测试（如有现成测试） |

### 不影响
- `Calculator.ets`、`Expression.ets`：计算引擎不修改
- `model/ErrorFlags.ets`：错误流不变
- `history/`、`qrcode/`、`common/UnitConverter`、`common/NaturalLanguageParser`：与本需求正交

## 现有代码分析

### CalculatorPage 结果显示流程（关键）
1. `onEquals()` → 调 `CalcEngine.evaluate()` → `raw: number`
2. `NumberFormatter.format(raw.toString(), '.', ',', ...)` → `fmt: string`
3. `this.result = fmt` → 触发 UI 重渲染
4. `Text(this.result.length > 0 ? this.result : '0')` 显示

### 关键发现
- `this.result` 当前存的是**格式化后的字符串**（小数带千分位）
- 切换到分数模式时，若 `this.result` 已是小数字符串，重新解析回 number 会丢精度
- **解决方案**：`onEquals` 后同时缓存 `this.lastRawResult: number`，分数模式直接用 number 走 `FractionUtil.toFraction(raw).format()`
- `errorMsg` 不为空时显示错误信息，覆盖 result，分数模式按钮禁用（FR-15）

### ToggleRow 位置
- 竖屏模式有 `ToggleRow()` Builder (L604-627)，含科学模式切换、粘贴、历史、分享、设置
- 横屏模式结果区右侧无按钮
- 切换按钮放 `result` Text 行内的右上角（叠加在结果区上方），用 Stack 包裹

## 风险识别

### 技术难点
- **浮点精度**：0.1+0.2=0.30000000000000004，化简后分母巨大
  - 缓解：最大分母 9999（FR-7），超过回退小数
- **负数零**：-0 在浮点里存在但视觉上应是 0
  - 缓解：toFraction 检测 `Math.abs(value) < Number.EPSILON` 返回 `{0, 1}`

### 风险清单
| 风险 | 严重度 | 缓解 |
|------|--------|------|
| 切换模式后历史记录显示混乱 | 中 | 历史列表不跟随显示模式（FR 明确） |
| GCD 在 JS/ArkTS 中大数运算溢出 | 低 | ArkTS Number 是双精度，分母 ≤ 9999 不会溢出 |
| 横屏布局中按钮重叠 | 中 | 横屏模式下隐藏切换按钮（只竖屏显示，仿 ToggleRow） |
| Preferences 写失败导致模式丢失 | 低 | try-catch + 默认 DECIMAL |

## 测试验证策略

### 单元测试
- `FractionUtil.toFraction` 覆盖：
  - 整数: 2 → {2, 1} 或 null（按设计）
  - 0.5 → {1, 2}
  - 0.25 → {1, 4}
  - -0.5 → {-1, 2}
  - 0.3333 → 化简后分母 > 9999 → null（回退）
  - NaN / Infinity → null
  - 0 → {0, 1}
- `FractionUtil.gcd`: (12, 8)→4, (15, 25)→5, (1, 7)→1
- `NumberFormatter.format(value, mode)` 验证模式切换

### UI 自动化测试
- 在 CalculatorPage 输入 `1/2`（或 `1÷2`），确认显示 `0.5`
- 点击切换按钮，确认显示 `1/2`
- 再次点击确认显示回 `0.5`
- 错误状态下按钮禁用验证
- 横屏/竖屏布局验证

### 手动验证
- 重启 App，验证显示模式持久化

## 监控运维支持

- 无特殊监控需求（前端展示）
- 偏好读写失败时静默回退到默认（DECIMAL）

## 关键发现

### 可复用组件或函数
- `NumberFormatter` (千分位) 继续作为小数模式后处理
- `PreferencesStore` getter/setter 模式直接套用
- `ErrorFlags` 用于切换按钮禁用条件

### 风险提示
- **历史记录不动**：仅修改结果显示，历史仍存小数
- **横屏布局**：切换按钮仅竖屏显示
- **精度降级**：分母超 9999 退回小数

### 建议事项
- **优先级**：核心改动在 `CalculatorPage.onEquals` 缓存 raw + 新增 FractionUtil
- **测试粒度**：先单元测试 FractionUtil 纯函数，再 UI 自动化测试切换流程
- **回滚点**：移除 DisplayMode 字段、切换按钮、`FractionUtil` 调用即可

### 测试能力评估
- 单元测试能力: ✅
- UI 自动化测试能力: ✅ (hdc + 模拟器 127.0.0.1:5555)
- 端到端集成测试能力: ✅
- 不能跑的实际原因: 无
