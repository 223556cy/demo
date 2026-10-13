# Issue #25 AID 工作流

## 路径配置
- 变更根目录: `D:/huawei/Demo/worktrees/issue-25/specs/changes/20260617-requirement-add-中等模糊`
- 项目根: `D:/huawei/Demo/calculatorHuawei`
- 分支: `feat/issue-25-中等模糊`
- git_branch_adopted: true

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- 单元测试框架: hypium+hamock
- 测试根: opencalc/entry/src/test
- UI 自动化测试能力: ✅ 可用 (hdc + 模拟器)
- 模拟器: 127.0.0.1:5555 (running)
- hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- hdc 版本: 3.2.0d
- Java: openjdk 21.0.8

## 阶段进度

### PLANNING
- [x] step0.5 环境能力盘点（已记录到 todo.md）
- [x] step1 用户意图理解（requirement-add，中等模糊，分支已创建）
- [x] step2 需求理解（rq-parse 输出已合并到 proposal.md §2）
- [x] step3 需求澄清（方案C全自动；模糊点已在 proposal.md §3.1 决策）
- [x] step4 需求 spec 设计（delta-spec.md）
- [x] step5 代码仓理解（info.md，补充环境能力 + 测试能力评估）
- [x] step6 需求复杂度评估（M 中等，2 个文件改动）
- [x] step7 架构设计（无需 new-arch.md — 纯 Map 扩展，无架构变更）
- [x] step8 组件设计（mod-design → delta-design.md）
- [x] step9 设计审视（design-review.md，5 维度全通过）

### IMPLEMENTING
- [ ] 调用 aid-implementing → tasks.md

### APPLYING
- [x] 调用 aid-applying (+ tdd-enforcer) → 真实代码 + 真实测试 + apply-report.md
- [x] RED-GREEN-REFACTOR 完成（71 个端口用例 100% pass）
- [x] 编译验证 `hvigorw assembleHap` SUCCESSFUL
- [x] apply-report.md 完成
- [ ] git commit
- [ ] gh_helper.py comment

### APPLYING 环境能力核对（2026-06-17）
- hvigorw 6.24.2 ✅
- hdc 3.2.0d ✅
- 模拟器连接：⚠️ `hdc list targets` 仅显示 UART 设备（COM3/COM4），无 127.0.0.1:5555
  - capabilities.json 声明 emulator_status: running，但实际未连接
  - UI 自动化测试降级为 Node 端口测试（沿用 #18 模式）
  - 在 apply-report.md §已知非阻塞限制 中记录实际能力差距
- @ohos/hypium 模块未安装（预存在环境问题，#18 也未跑通 hypium）
  - 测试用端口测试同构验证（1:1 端口对齐）

### 最终状态
- 修改文件：4 个 .ets 文件（2 主代码 + 2 测试）
- 新增 AID 制品：9 个（proposal/delta-spec/info/delta-design/design-review/tasks/apply-report + tests/ + todo）
- 端口测试：71/71 PASS（39 UnitConverter + 32 NaturalLanguageParser）
- 编译：hvigorw assembleHap BUILD SUCCESSFUL
