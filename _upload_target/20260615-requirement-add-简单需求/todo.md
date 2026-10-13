# Issue #12 程序员模式 - AID PLANNING/IMPLEMENTING/APPLYING todo

## 路径配置
- 变更目录: `specs/changes/20260615-requirement-add-简单需求/`
- Git worktree: `D:/huawei/Demo/worktrees/issue-12`
- 当前分支: `feat/issue-12-简单需求`（已独立分支，git_branch_adopted: true）

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- 单元测试框架: hypium+hamock
- **UI 自动化测试能力: ✅ 可用 (hdc + 模拟器)**
- 模拟器: 127.0.0.1:5555 (running)
- hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe

## 用户确认方案
- 方案 C：阶段间确认自动同意，理由记录到 todo.md（本文件）
- hvigorw 不在 PATH（已用绝对路径或 hvigorw.bat），hdc 存在 ✅

## PLANNING 阶段
- [x] step0.5 环境能力盘点（已读 capabilities.json，UI 测试能力 ✅）
- [x] step1 用户意图理解（requirement-add / 简单需求 / 分支 feat/issue-12-简单需求）
- [x] step2 需求理解（rq-parse 已执行，proposal.md 已生成）
- [x] step3 需求澄清（方案 C 自动决策 9 项）
- [x] step4 需求spec设计（delta-spec.md 已存在并覆盖完整）
- [x] step5 代码仓理解（rq-codebase 已执行，info.md 已生成）
- [x] step5.1 环境能力已写入 info.md
- [x] step6 复杂度评估（M 中等，4 模块，1 新建）
- [x] step7 架构设计（无架构变更，跳过 new-arch.md）
- [x] step8 组件设计（delta-design.md 已生成）
- [x] step9 设计审视（design-review.md 已生成）

## IMPLEMENTING 阶段
- [x] tasks.md 已生成（10 任务，关键路径 1.1→1.2→1.3→2.1→3.1→3.2-3.7→4.1→4.2）

## APPLYING 阶段
- [x] TDD RED-GREEN-REFACTOR（Task 1.1 BaseConverter）
- [x] 真实代码改动（Task 1.1-3.7）
- [x] 真实单元测试（Task 4.1：28/28 Node 端口通过）
- [ ] UI 自动化测试（Task 4.2：需主仓库 HAP 构建后执行）
- [x] apply-report.md

## 自动决策记录（方案 C）
| # | 决策点 | 自动决定 | 理由 |
|---|--------|---------|------|
| 1 | 输入 vs 显示进制 | DEC 主输入 + 多进制显示行 | 业界标准做法 |
| 2 | 模式关系 | 三选一互斥 | UX 提升 |
| 3 | 切换动画 | fade+slide 200ms/8px | ArkUI 内置 |
| 4 | 小数处理 | 截断为整数 | IEEE 754 |
| 5 | 负数 | `-` 前缀 | 实现简单 |
| 6 | 位宽 | 不限制（安全整数） | 范围内足够 |
| 7 | 键盘布局 | 简化 BIN/HEX | 80% 场景覆盖 |
| 8 | 偏好持久化 | 持久化 | 与现有模式一致 |
| 9 | 输入 BIN | 不支持 | DEC 已覆盖 |

## 高风险检查（无需暂停）
- ✅ capabilities.json 存在
- ✅ hvigorw / hdc / DevEco SDK 可用
- ❌ 非 arch-refactor / platform-migration
- ❌ delta-spec.md / design.md 不涉及删除现有功能（仅扩展 ToggleRow → ModeToggleRow；保留科学模式）