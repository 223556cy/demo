# Issue #25 单位换算扩展 — 开发任务

## 任务概述

- **功能名称**：单位换算扩展 (Extended Unit Conversion)
- **变更类型**：requirement-add
- **关联特性**：feat-unit-conversion（在 #18 基础上扩展）
- **开发阶段**：扩展实现 + 完整测试 + UI 自动化
- **预计任务数**：8
- **环境能力（来自 .claude/capabilities.json）**：
  - 编译: `hvigorw --no-daemon assembleHap`
  - 单元测试: `hvigorw --no-daemon test` (hypium+hamock)
  - **UI 测试能力: ✅ 可用**（hdc + 模拟器 127.0.0.1:5555，harmonyos-ui-test skill）
  - hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe

## 任务列表

### 阶段 1：基础设施扩展（UnitConverter 因子表）

#### Task 1.1: 扩展 UnitConverter 因子表
**描述**：在 `UnitConverter.ets` 文件末尾追加 3 个 `buildXxxFactors()` 私有工厂函数（area/time/speed），以及 3 个 `CATEGORY_XXX` 常量。所有因子值遵循 delta-spec.md §因子表附录。
**涉及文件**：
- `opencalc/entry/src/main/ets/common/UnitConverter.ets`（extend，+~50 行）
**依赖任务**：无
**验收标准**：
- [ ] 3 个 `CATEGORY_*` 常量已声明（字符串类型）
- [ ] 3 个 `buildXxxFactors()` 函数返回 `Map<string, number>`
- [ ] area 表覆盖 9 个基准：m2/cm2/km2/ft2/in2/yd2/acre/hectare/mu
- [ ] time 表覆盖 8 个基准：ms/s/min/h/d/wk/mo/yr
- [ ] speed 表覆盖 5 个基准：m_s/kmh/mph/knot/mach
- [ ] 因子值精度 ≥ 8 位有效数字
- [ ] 沿用 #18 的 Map 工厂模式（满足 ArkTS arkts-no-untyped-obj-literals）

#### Task 1.2: 扩展 UnitConverter.getFactors 分支
**描述**：在 `getFactors()` 私有方法末尾追加 3 个 `if` 分支（area/time/speed），返回对应因子表。
**涉及文件**：
- `opencalc/entry/src/main/ets/common/UnitConverter.ets`（extend，+3 行）
**依赖任务**：Task 1.1
**验收标准**：
- [ ] `getFactors('area')` → AREA_FACTORS
- [ ] `getFactors('time')` → TIME_FACTORS
- [ ] `getFactors('speed')` → SPEED_FACTORS
- [ ] `getFactors('invalid')` → null（沿用 #18 行为）
- [ ] 不修改现有 length/temperature/mass/volume 分支

### 阶段 2：NL 别名扩展（NaturalLanguageParser）

#### Task 2.1: 扩展 NaturalLanguageParser 别名表
**描述**：在 `buildAliases()` 工厂函数末尾追加 ~50 个 `m.set(...)` 调用，覆盖 area/time/speed 3 个新类别（中英文别名）。
**涉及文件**：
- `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets`（extend，+~50 行）
**依赖任务**：无（与 Task 1.x 独立可并行）
**验收标准**：
- [ ] area 别名：亩/英亩/公顷/平方米/平方厘米/平方千米/平方英尺/平方英寸/平方码/m2/cm2/km2/ft2/in2/yd2/acre/hectare/ha
- [ ] time 别名：秒/毫秒/分钟/小时/天/周/月/年/s/ms/min/h/hour/day/week/month/year
- [ ] speed 别名：米每秒/千米每小时/公里每小时/英里每小时/节/马赫/m/s/km/h/kph/mph/knot/mach
- [ ] 不修改 #18 已有的 ~70 个别名
- [ ] 不修改 `parse()` 方法逻辑

#### Task 2.2: 别名冲突检测测试
**描述**：在 NaturalLanguageParser 测试套件中新增一个 describe 块，使用 `new Set(...allAliases).size === allAliases.length` 验证所有别名（含 #18 + #25）唯一性。
**涉及文件**：
- `opencalc/entry/src/test/ets/common/NaturalLanguageParser.test.ets`（extend）
**依赖任务**：Task 2.1
**验收标准**：
- [ ] describe('NaturalLanguageParser_alias_uniqueness') 存在
- [ ] 1 个 it 用例：构造所有别名，验证 Set 大小 === 别名数
- [ ] 测试通过

### 阶段 3：单元测试扩展

#### Task 3.1: UnitConverter area/time/speed 测试
**描述**：在 `UnitConverter.test.ets` 追加 3 个 describe 块（area/time/speed）+ 1 个跨类别 describe 块。
**涉及文件**：
- `opencalc/entry/src/test/ets/common/UnitConverter.test.ets`（extend，+~60 行）
**依赖任务**：Task 1.1, Task 1.2
**验收标准**：
- [ ] describe('UnitConverter_area') 覆盖至少 6 个用例（m2↔cm2, acre→m2, hectare→m2, mu→m2, 100mu→m2, km2→m2）
- [ ] describe('UnitConverter_time') 覆盖至少 6 个用例（h→min, 2h→min, d→h, wk→d, mo→d, yr→d）
- [ ] describe('UnitConverter_speed') 覆盖至少 4 个用例（mph→kmh, kmh→mph, knot→kmh, mach→mps）
- [ ] describe('UnitConverter_cross_category_new') 覆盖 area↔time↔speed 两两拒绝（3 个用例）
- [ ] EPS=1e-6，mach 用 1e-3

#### Task 3.2: NaturalLanguageParser area/time/speed 别名测试
**描述**：在 `NaturalLanguageParser.test.ets` 追加 3 个 describe 块（area/time/speed 中文 NL）。
**涉及文件**：
- `opencalc/entry/src/test/ets/common/NaturalLanguageParser.test.ets`（extend，+~60 行）
**依赖任务**：Task 2.1
**验收标准**：
- [ ] describe('NaturalLanguageParser_area_cn') 至少 5 用例
- [ ] describe('NaturalLanguageParser_time_cn') 至少 5 用例
- [ ] describe('NaturalLanguageParser_speed_cn') 至少 5 用例
- [ ] 覆盖别名：亩/英亩/公顷/秒/分钟/小时/天/米每秒/千米每小时/英里每小时/节/马赫

### 阶段 4：回归验证

#### Task 4.1: 零回归测试（全量套件）
**描述**：跑全量测试套件（hvigorw test），验证 #18 4 大类测试 100% 通过。
**涉及文件**：（只读）
**依赖任务**：Task 1.x, Task 2.x, Task 3.x 全部完成
**验收标准**：
- [ ] length/temperature/mass/volume describe 全部绿
- [ ] NaturalLanguageParser_chinese/english describe 全部绿
- [ ] 新增 area/time/speed describe 全部绿
- [ ] 总用例数 ≥ #18 基线 + #25 新增用例数

#### Task 4.2: 编译验证
**描述**：跑 `hvigorw --no-daemon assembleHap` 验证整体编译通过。
**涉及文件**：（只读）
**依赖任务**：Task 1.x, Task 2.x 全部完成
**验收标准**：
- [ ] 编译成功，生成 .hap 文件
- [ ] 无 ArkTS 语法错误（如 arkts-no-untyped-obj-literals）
- [ ] 无未解析引用

### 阶段 5：UI 自动化测试（强制 — capabilities.json ui_test=true）

#### Task 5.1: UI 自动化测试脚本（run_tests.py）
**描述**：编写 Python 脚本，使用 hdc 在模拟器 127.0.0.1:5555 上执行 NL 单位换算 UI 自动化测试。沿用 #18 ui-tests/ 模式。
**涉及文件**：
- 创建：`specs/changes/20260617-requirement-add-中等模糊/ui-tests/run_tests.py`
- 创建：`specs/changes/20260617-requirement-add-中等模糊/ui-tests/parse_ui.py`
- 创建：`specs/changes/20260617-requirement-add-中等模糊/ui-tests/screenshot/` 目录
- 创建：`specs/changes/20260617-requirement-add-中等模糊/ui-tests/results.json`
**依赖任务**：Task 1.x, Task 2.x, Task 4.2（必须先编译成功并安装）
**验收标准**：
- [ ] hdc list targets 显示 127.0.0.1:5555
- [ ] hdc install -r 成功
- [ ] aa start -b com.darkempire78.opencalculator -a EntryAbility 成功
- [ ] 至少 3 个测试用例：
  - 输入 "100亩转平方米" → 验证预览显示包含 "66666.67"
  - 输入 "2小时转分钟" → 验证预览显示包含 "120"
  - 输入 "60英里每小时转千米每小时" → 验证预览显示包含 "96.56"
- [ ] screenshot/ 目录包含每步截图
- [ ] results.json 包含每个用例的 pass/fail/skip 状态
**TDD**：[x] RED（写脚本） → [x] GREEN（跑通） → [ ] REFACTOR（清理）
**禁止**：标为 ⏭️ Deferred 或 "手动"。capabilities.json ui_test=true 必须真实执行。

#### Task 5.2: UI 自动化测试结果分析
**描述**：解析 results.json，写入 apply-report.md §UI 自动化结果。
**涉及文件**：
- 更新：`specs/changes/20260617-requirement-add-中等模糊/apply-report.md`
**依赖任务**：Task 5.1
**验收标准**：
- [ ] apply-report.md §UI 自动化结果章节存在
- [ ] 列出每个用例的 pass/fail
- [ ] 若失败，包含失败原因 + 截图路径

### 阶段 6：文档与收尾

#### Task 6.1: 编写 apply-report.md
**描述**：汇总 AID APPLYING 阶段的执行结果：实施清单、单元测试结果、UI 自动化结果、零回归验证、最终代码统计。
**涉及文件**：
- 创建：`specs/changes/20260617-requirement-add-中等模糊/apply-report.md`
**依赖任务**：Task 1.x ~ Task 5.x 全部完成
**验收标准**：
- [ ] §1 实施清单（含每个文件的实际变更行数）
- [ ] §2 单元测试结果（hypium 跑测日志片段）
- [ ] §3 UI 自动化测试结果（results.json 摘要）
- [ ] §4 零回归验证（#18 测试通过率 100%）
- [ ] §5 最终代码统计（git diff --stat）
- [ ] §6 已知非阻塞限制

#### Task 6.2: git commit
**描述**：本地 commit（不 push），dev-01 会负责 push。
**涉及文件**：
- 变更根目录下所有新增/修改文件
**依赖任务**：Task 6.1
**验收标准**：
- [ ] `git add specs/changes/20260617-requirement-add-中等模糊/ opencalc/entry/src/main/ets/common/ opencalc/entry/src/test/ets/common/`
- [ ] `git commit -m "feat(issue-25): extend unit conversion with area/time/speed ..."`
- [ ] commit 信息含 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- [ ] 不 push

#### Task 6.3: gh_helper.py comment
**描述**：在 Issue #25 上发评论通知 @littleleafccccc。
**涉及文件**：（外部）
**依赖任务**：Task 6.2
**验收标准**：
- [ ] 评论内容：`@littleleafccccc claude -p 跑完,worktree 在 D:/huawei/Demo/worktrees/issue-25 等 push`
- [ ] gh_helper.py 退出码 0

## 开发顺序

```
Task 1.1 → Task 1.2  ──┐
                      ├─→ Task 2.2 → Task 3.2 → Task 4.1 → Task 4.2 → Task 5.1 → Task 5.2 → Task 6.1 → Task 6.2 → Task 6.3 ✓
Task 2.1 ──────────────┘
           ↓
       Task 3.1
```

**并行可能性**：
- Task 1.1/1.2 与 Task 2.1 完全独立，可并行（不同文件）
- Task 3.1 依赖 Task 1.x，Task 3.2 依赖 Task 2.1，可并行
- Task 4.1 依赖所有 Task 3.x（关键路径）
- Task 4.2 编译可在 Task 4.1 之前并行跑（验证编译）
- Task 5.x 必须在 Task 4.2 之后（必须先安装）
- Task 6.x 收尾依赖前面所有

**关键路径**：Task 1.1 → Task 1.2 → Task 3.1 → Task 4.1 → Task 4.2 → Task 5.1 → Task 6.1 → Task 6.2 → Task 6.3

## 验收计划

| 任务 | 验收方式 | 期望耗时 |
|------|---------|----------|
| Task 1.1 | 代码审查 + Map 构造无报错 | 15 min |
| Task 1.2 | 代码审查 + getFactors 返回值类型 | 5 min |
| Task 2.1 | 代码审查 + 别名查重测试 | 20 min |
| Task 2.2 | 单元测试通过 | 5 min |
| Task 3.1 | 单元测试通过（≥ 19 个新用例） | 20 min |
| Task 3.2 | 单元测试通过（≥ 15 个新用例） | 20 min |
| Task 4.1 | 全量套件 100% 绿 | 5 min |
| Task 4.2 | 编译 0 错误 | 5 min |
| Task 5.1 | UI 自动化脚本跑通 ≥ 3 用例 | 30 min |
| Task 5.2 | results.json + apply-report.md | 10 min |
| Task 6.1 | apply-report.md 完整 | 10 min |
| Task 6.2 | git commit 成功 | 2 min |
| Task 6.3 | gh_helper.py 退出 0 | 1 min |

**总计预计**：~2.5 小时（含测试运行）
