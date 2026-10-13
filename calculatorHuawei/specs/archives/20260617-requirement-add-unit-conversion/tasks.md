# Issue #18 单位换算 - 开发任务

## 任务概述

- **功能名称**：计算器支持自然语言单位换算
- **变更类型**：requirement-add
- **关联特性**：feat-calc-core
- **开发阶段**：MVP（4 维度单位换算 + NL 解析）
- **预计任务数**：6

## 任务列表

### 阶段 1：基础设施（RED 优先）

#### Task 1.1: UnitConverter 单元测试 RED
**描述**：先写 UnitConverter.test.ets 单元测试，断言失败（RED）
**涉及文件**：
- `opencalc/entry/src/test/ets/common/UnitConverter.test.ets`（新建）
**依赖任务**：无
**验收标准**：
- 4 个维度（长度/质量/温度/时间）× 至少 3 对单位共 12 个断言
- 跨维度 / 未知单位返回 NaN 的 2 个断言
- 测试文件可被 hvigorw test 加载并失败
- **TDD**: [x] RED → [x] GREEN → [ ] REFACTOR

#### Task 1.2: UnitConverter 实现 GREEN
**描述**：实现 UnitConverter.ets，包含 4 维度单位表 + convert 静态方法
**涉及文件**：
- `opencalc/entry/src/main/ets/common/UnitConverter.ets`（新建）
**依赖任务**：Task 1.1
**验收标准**：
- 单元测试全部 PASS（长度 4+ 对、质量 2+ 对、时间 2+ 对、温度 3 对）
- 跨维度/未知单位返回 NaN
- 温度用 affine 公式（K 基准）
- 不引入新状态（纯静态类）
- **TDD**: [x] RED → [x] GREEN → [ ] REFACTOR

#### Task 1.3: NaturalLanguageParser 单元测试 RED
**描述**：先写 NaturalLanguageParser.test.ets
**涉及文件**：
- `opencalc/entry/src/test/ets/common/NaturalLanguageParser.test.ets`（新建）
**依赖任务**：无
**验收标准**：
- 至少 6 个 NL 模式（中文紧凑/中文带空格/英文 to/英文 in/中文→箭头/中文为）
- 至少 2 个非 NL 模式返回 null（1+2 / sin(0)）
- 至少 1 个空字符串返回 null
- **TDD**: [x] RED → [x] GREEN → [ ] REFACTOR

#### Task 1.4: NaturalLanguageParser 实现 GREEN
**描述**：实现 NaturalLanguageParser.ets，含 parse 静态方法
**涉及文件**：
- `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets`（新建）
**依赖任务**：Task 1.3
**验收标准**：
- 单元测试全部 PASS
- 关键字白名单：转/to/in/为/→
- value 解析支持整数和小数
- **TDD**: [x] RED → [x] GREEN → [ ] REFACTOR

### 阶段 2：集成

#### Task 2.1: CalculatorPage 集成 NL 换算分支
**描述**：在 onEquals 增加 NL 换算优先分支，含 tryUnitConversion 私有方法
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 1.2, Task 1.4
**验收标准**：
- onEquals 入口先试 NL
- NL 成功 → result + history（与原逻辑同结构）
- NL 失败但识别为换算 → errorMsg "单位不匹配" 或 "未知单位"
- NL parse null → 走原 CalcEngine 降级
- 不影响 1+2 / sin(0) 等常规表达式
- **TDD**: [x] RED（编译失败）→ [x] GREEN（编译通过）→ [ ] REFACTOR

#### Task 2.2: 编译验证
**描述**：运行 `hvigorw --no-daemon assembleHap`，确保无编译错误
**涉及文件**：无
**依赖任务**：Task 2.1
**验收标准**：
- hvigorw 命令退出码 0
- build/output/default/default/.../entry-*.hap 存在
- **TDD**: 编译通过即 GREEN

### 阶段 3：测试验证

#### Task 5.1: 单元测试
**描述**：运行 `hvigorw --no-daemon test` 验证所有单元测试 PASS
**涉及文件**：无
**依赖任务**：Task 1.2, Task 1.4
**验收标准**：
- UnitConverter 测试 PASS
- NaturalLanguageParser 测试 PASS
- 现有 Expression.test.ets 不退化
- **TDD**: [x] GREEN

#### Task 5.2: 集成测试（不依赖 UI）
**描述**：在 CalculatorPage 文件中（或测试 helper）验证集成逻辑：NL 路径走通、降级走通
**涉及文件**：可选新建 `CalculatorPage.test.ets`（hypium）
**依赖任务**：Task 2.1
**验收标准**：
- 至少 3 个集成断言（NL 成功 / 跨维度 / 非 NL 降级）
- 现有 CalculatorPage 行为不退化
- **TDD**: [x] GREEN

#### Task 5.3: UI 自动化测试
**描述**：使用 hdc + harmonyos-ui-test skill 在模拟器 127.0.0.1:5555 上执行 AC 验证
**涉及文件**：
- 测试脚本：`specs/changes/20260617-requirement-add-unit-conversion/ui-tests/run_tests.py`
- 截图：`specs/changes/20260617-requirement-add-unit-conversion/ui-tests/screenshot/`
- 结果：`specs/changes/20260617-requirement-add-unit-conversion/ui-tests/results.json`
**依赖任务**：Task 5.1, Task 5.2
**验收标准**：
- [ ] hdc list targets 有输出（设备已连接）
- [ ] 应用安装成功（hdc install -r 成功）
- [ ] 应用启动成功（aa start 成功）
- [ ] AC 1: 键入 "100厘米转英寸" → result 文本 ≈ "39.3701"（截图 + dump 验证）
- [ ] AC 2: 键入 "30摄氏度转华氏度" → result 文本 = "86"
- [ ] AC 3: 键入 "5ft in cm" → result 文本 ≈ "152.4"
- [ ] AC 4: 键入 "5米转千克" → errorMsg = "单位不匹配"
- [ ] AC 5: 键入 "1+2" → result = "3"（降级）
- [ ] screenshot/ 目录包含每步操作截图
- [ ] results.json 包含每个 AC 的 pass/fail/skip 状态
- **TDD**: [x] RED（脚本执行）→ [x] GREEN（验证）→ [ ] REFACTOR

**禁止**：标为 ⏭️ Deferred 或"手动"。如确实无法执行，必须在 todo.md 中说明：
- capabilities.json 中 ui_test 的实际状态（✅ true）
- 模拟器状态（运行中/未运行）
- hdc 状态（可用/不可用）
- 为何无法执行的**具体原因**（不是"用户未指定"这种借口）

## 开发顺序

```
Task 1.1 (RED UnitConverter test) 
   ↓
Task 1.2 (GREEN UnitConverter impl)
   ↓
Task 1.3 (RED NL Parser test) ─┐ (与 1.1/1.2 可并行)
   ↓                          │
Task 1.4 (GREEN NL Parser impl)
   ↓
Task 2.1 (CalculatorPage 集成)
   ↓
Task 2.2 (编译验证)
   ↓
Task 5.1 (单元测试)
   ↓
Task 5.2 (集成测试)
   ↓
Task 5.3 (UI 自动化)
   ↓
完成
```

## 验收计划

| 任务 | 验收方式 | 验收时间 |
|------|---------|----------|
| Task 1.1 | 单元测试 RED（断言失败） | APPLYING 阶段 |
| Task 1.2 | 单元测试 GREEN | APPLYING 阶段 |
| Task 1.3 | 单元测试 RED | APPLYING 阶段 |
| Task 1.4 | 单元测试 GREEN | APPLYING 阶段 |
| Task 2.1 | 编译通过 | APPLYING 阶段 |
| Task 2.2 | hvigorw assembleHap 成功 | APPLYING 阶段 |
| Task 5.1 | hvigorw test 全部 PASS | APPLYING 阶段 |
| Task 5.2 | 集成测试 PASS | APPLYING 阶段 |
| Task 5.3 | UI 自动化 5 个 AC 全 PASS | APPLYING 阶段 |

## 范围外任务（不做）
- ❌ 货币换算（需网络/汇率）
- ❌ 体积/面积/速度/功率等专业单位
- ❌ i18n 全语种
- ❌ 复杂上下文（"那再转成英尺呢"）
- ❌ 模糊输入容错
