# 需求提案 — Issue #14 单位换算功能

## 1. 原始需求

> 让计算器能做单位换算,比如"100厘米转英寸"、"30摄氏度转华氏度" | 单位换算 | ⭐⭐ | 输入框直接支持自然语言查询

**Issue 来源**:Issue #14
**类型**:新增功能(Design/Development - New Requirement)
**变更名称**:unit-conversion
**优先级**:P1(中等模糊 ⭐⭐)
**工作目录**:D:/huawei/Demo/worktrees/issue-14
**分支**:feat/issue-14-中等模糊

## 2. 需求理解

### 2.1 意图分类
- **类型**:新增功能(扩展)
- **一句话概括**:在 CalculatorPage 输入框支持自然语言查询(中文),自动识别单位换算请求并直接给出结果,无需按"="。

### 2.2 领域映射
- **UI/交互**:CalculatorPage.expression 输入框接受中文 NL 查询(如 "100厘米转英寸"),识别后直接显示换算结果
- **状态管理**:新增 `unitConversionResult: string` 状态,与 expression 变化时同步计算
- **计算引擎**:新增 `UnitConverter` 模块,提供 length/temperature/mass/volume 4 大类共 ~20 个常用单位的换算
- **自然语言解析**:新增 `NaturalLanguageParser` 模块,识别 NL 模式 "数字 + 单位A + 转/到/->/=> + 单位B"

### 2.3 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | modify | CalculatorPage: 新增 NL 输入提示;DisplayPanel 可选显示换算结果行 |
| ViewModel | extend | 新增 onNLInput() / parseAndConvert() 方法;新增 @State unitConversionResult |
| Model | new | UnitConverter.ets(单位换算核心)+ UnitConverter.test.ets |
| Model | new | NaturalLanguageParser.ets(NL 模式识别) |
| 数据层 | 无 | 无持久化需求 |
| 基础设施 | 无 | 无新依赖 |

### 2.4 关键实体
- **数据实体**:
  - `UnitConverter.convert(value: number, from: string, to: string, category: UnitCategory): number`
  - `NaturalLanguageParser.parse(input: string): {value: number, from: string, to: string} | null`
  - `UnitCategory`:枚举 'length' | 'temperature' | 'mass' | 'volume'
- **页面实体**:CalculatorPage.expression(已有)+ 新增 unitConversionResult @State
- **事件实体**:expression 变化 → 检查是否 NL 模式 → 是则换算并显示

### 2.5 模糊点(已在 step3 决定)
- **NL 模式识别**(blocker → 决定):使用正则表达式匹配 "数字 + 单位A + 转/到/->/=> + 单位B" 模式
- **支持单位范围**(blocker → 决定):优先 length(米/厘米/毫米/千米/英寸/英尺/码/英里)+ temperature(摄氏度/华氏度/开尔文)+ mass(千克/克/磅/盎司)+ volume(升/毫升/加仑/盎司)4 大类
- **单位别名**(important → 决定):支持中英文别名,如 "厘米/cm/centimeter"、"摄氏度/°C/℃/Celsius"
- **结果展示**(important → 决定):换算结果直接显示在 result 区,expression 仍保留 NL 原文以便用户编辑
- **错误处理**(important → 决定):无法识别的 NL → 降级为普通表达式计算;无法跨类换算 → 显示"不支持的换算"错误
- **优先级**(nice-to-have → 决定):与现有"按 = 计算"流程共存,NL 检测在前,失败则走原计算

### 2.6 复杂度评估
- **等级**:M(中等)
- **理由**:新增 2 个模块(UnitConverter + NaturalLanguageParser),支持 4 大类共 ~20 个单位,需 ~300-400 行代码
- **影响模块数**:3(CalculatorPage.ets + 新 UnitConverter.ets + 新 NaturalLanguageParser.ets)
- **架构变更**:否(在现有计算流程上扩展)
- **数据模型变更**:否

## 3. 验收标准

### 3.1 功能验收
- [ ] 用户输入 "100厘米转英寸" → result 显示 "39.3701" (或更精确格式)
- [ ] 用户输入 "30摄氏度转华氏度" → result 显示 "86" (精确 86°F)
- [ ] 用户输入 "1英里转千米" → result 显示 "1.609344"
- [ ] 用户输入 "5磅转千克" → result 显示 "2.26796"
- [ ] 用户输入 "1加仑转升" → result 显示 "3.78541"
- [ ] 用户输入 "100cm to inch" → result 显示 "39.3701"
- [ ] 用户输入 "0摄氏度转开尔文" → result 显示 "273.15"
- [ ] 用户输入 "100华氏度转摄氏度" → result 显示 "37.7777..."
- [ ] 不支持跨类换算("1米转千克")→ 显示错误提示
- [ ] 普通表达式 "1+2" 不被误识别为 NL → 走原计算流程
- [ ] 输入 "abc 厘米 转 英寸" → NL 解析失败,降级为原计算(显示错误或空)

### 3.2 性能验收
- [ ] NL 解析 < 1ms(纯正则 + 字典查找)
- [ ] 单位换算 < 1ms(纯算术)
- [ ] 总计 < 5ms(对用户按键响应无影响)

### 3.3 兼容性验收
- [ ] 不破坏现有"按 = 计算"流程
- [ ] 不影响实时预览功能(Issue #11)
- [ ] 不影响百分号功能(Issue #9)
- [ ] 不影响历史记录
- [ ] 横竖屏兼容

## 4. 范围边界

### 范围内
- 4 大类单位换算:length / temperature / mass / volume
- 中英文单位别名(厘米/cm/centimeter 等)
- 自然语言模式 "数字+单位A+转/到/->/=>+单位B"
- 单元测试覆盖所有支持单位对
- CalculatorPage 集成 NL 解析层
- UI 自动化测试(harmonyos-ui-test)

### 范围外
- 面积/时间/速度/能量/压强等其他单位类别
- 复杂 NL(如 "100 cm 等于多少 inch")
- 货币换算(汇率实时变化,非本 Issue 范围)
- NL 解析的 ML/NLP 方案(纯正则足够)
- 多步换算(如 "100 厘米 转 英寸 再转 英尺" — 单步换算)
- 历史记录特殊标记换算结果

## 5. 相关文件

| 文件 | 角色 | 预计改动 |
|------|------|----------|
| `opencalc/entry/src/main/ets/common/UnitConverter.ets` | 新建 | 单位换算核心 ~150 行 |
| `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets` | 新建 | NL 模式识别 ~80 行 |
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` | 改 | 集成 NL 解析 + 显示结果 ~30 行 |
| `opencalc/entry/src/test/ets/common/UnitConverter.test.ets` | 新建 | 单元测试 ~30 用例 |
| `specs/changes/20260615-requirement-add-unit-conversion/tests/*.mjs` | 新建 | Node 端口测试 |
| `specs/changes/20260615-requirement-add-unit-conversion/ui-tests/*` | 新建 | UI 自动化测试产物 |

## 6. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 单位别名不全,用户输入不识别 | 中 | 中 | 收集常见别名(中/英/简写),最低支持 20 个别名 |
| NL 误识别(如 "1+1" 被误判) | 低 | 高 | 严格正则:必须包含中文单位词或英文单位 + 转换词 |
| 跨类换算语义错误 | 低 | 中 | 显式单位类别匹配,跨类抛 "不支持的换算" |
| 浮点精度 | 中 | 低 | 使用容差 1e-6 验证,与已知科学常量比对 |
| CalculatorPage 集成破坏现有功能 | 中 | 高 | 完整 TDD 覆盖现有 17 个 preview 用例无回归 |
