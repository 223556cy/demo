# calculatorHuawei/aid-workflow-skills

> **AID-Workflow 4 阶段所有 skill 的源真（Source of Truth）**。
> skillopt-01 改任何一个 skill，都开 PR → 12 个历史 issue 回归 → 通过后 merge → 自动同步到 4 个 agent profile。

[![Tests: 12 cases](https://img.shields.io/badge/tests-12%20cases-blue)](tests/regression/cases/)
[![Self-hosted runner](https://img.shields.io/badge/runner-self--hosted-orange)](.github/workflows/test-skill-branch.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 仓库是什么

`calculatorHuawei/agent_workflow` 项目运行一套 4 阶段 AID-Workflow：

```
PLANNING (aid-planning)
    ↓
IMPLEMENTING (aid-implementing)
    ↓
APPLYING (aid-applying)
    ↓
ARCHIVING (aid-archiving)
```

每个阶段的"操作指南"就是本仓库的 15 个 `SKILL.md`。dev-01 / rev-01 / pm-01 / skillopt-01 这 4 个数字员工都读这些 skill 来工作。

**本仓库解决 3 个问题**：

1. **源真分散**：4 个 agent profile + 用户全局 + opencode，每个都有自己的 skill 副本，修改容易不同步
2. **回归难**：改了 skill 后，没法快速验证"会不会让 issue 14 又编不过了"
3. **改的人没流程**：skillopt-01 改 skill 没有 review 流程，没有"对比新旧效果"的依据

---

## 架构图

```
┌────────────────────────────────────────────────────────┐
│ GitHub: calculatorHuawei/aid-workflow-skills  (源真)    │
│   skills/  tests/  scripts/  reports/                  │
│   .github/workflows/test-skill-branch.yml              │
└────────────────────────────────────────────────────────┘
        ↑ PR 改 skill    ↓ merge 后同步
        │                │
        │                ├─→ calculatorHuawei/.claude/skills/*
        │                ├─→ C:/Users/26909/.claude/skills/*
        │                ├─→ C:/Users/26909/.opencode/skills/*
        │                └─→ Hermes profile dev-01/skills/*
        │
┌────────────────────────────────────────────────────────┐
│ skillopt-01 改 skill                                   │
│   1. 新分支 skillopt-01-YYYYMMDD-{描述}                │
│   2. 编辑 + 写 CHANGELOG                                │
│   3. push → PR → 触发 CI 跑 12 issue 回归              │
│   4. 报告作为 PR comment                               │
│   5. rev-01 + 老板 review → merge                      │
└────────────────────────────────────────────────────────┘
        │
        ↓
┌────────────────────────────────────────────────────────┐
│ Self-hosted runner (你机器上的 GitHub Action)          │
│   Windows + DevEco Studio + hvigorw + hdc + Java 17    │
│   跑：build_hap.bat + hvigorw test@entry + UI test     │
│   产物：reports/branches/<branch>/report.md            │
└────────────────────────────────────────────────────────┘
```

---

## 15 个 Skill 一览

| Skill | 行数 | 作用 |
|---|---|---|
| `aid-planning` | 338 | 需求分析 + 系统设计 → proposal/info/design |
| `aid-implementing` | 230 | 设计 → tasks.md（任务分解）|
| **`aid-applying`** | **425** | **TDD 写代码 + 编译 + 测试 + 报告** |
| `aid-archiving` | 252 | 归档已完成 change |
| `tdd-enforcer` | 226 | 强制 RED→GREEN→REFACTOR |
| `harmonyos-ui-test` | 1456 | DevEco 模拟器 + hdc shell uitest |
| `aid-init` | 668 | 首次环境检查 |
| `aid-monitor` | 150 | 错误监控 |
| `aid-reviewing` | 108 | SDD/Spec 文档 review |
| `dfr-fmea-harmony` | 503 | FMEA 故障分析 |
| `mod-design` | 433 | 生成 design.md |
| `prd-generator` | 777 | 生成 PRD |
| `rq-parse` | 200 | 解析用户需求 |
| `rq-codebase` | 387 | 代码仓理解 |
| `rq-clarify` | 234 | 需求澄清 |

---

## 快速开始

### 一次性配置（管理员）

```bash
# 1. 在 GitHub 创建仓库 calculatorHuawei/aid-workflow-skills
# 2. 关联本地
cd D:/huawei/Demo/aid-workflow-skills
git remote add origin git@github.com:calculatorHuawei/aid-workflow-skills.git
git add -A
git commit -m "init: mirror 15 skills from calculatorHuawei/.claude/skills/"
git push -u origin main

# 3. 在你机器上注册 self-hosted runner（GitHub repo → Settings → Actions → Runners）
#    label: [self-hosted, windows, dev]
```

### skillopt-01 改一个 skill

```bash
cd D:/huawei/Demo/aid-workflow-skills
git checkout -b skillopt-01-$(date +%Y%m%d)-{描述}
# 编辑 skills/aid-applying/SKILL.md
# 改 docs/CHANGELOG.md
python scripts/package_skills.py      # 校验
git add -A
git commit -m "..."
git push origin skillopt-01-20260706-fix-tdd
# → 开 PR → 等 CI 报告 → review → merge
```

### 同步到 4 个 agent profile（merge 后）

```bash
# 同步全部
python scripts/sync_to_agents.py --target all

# 只同步项目本地
python scripts/sync_to_agents.py --target project

# 只同步一个 skill
python scripts/sync_to_agents.py --target all --skill aid-applying

# 看会做什么（不真执行）
python scripts/sync_to_agents.py --target all --dry-run
```

### 跑回归（手动调试）

```bash
# 全部 12 个 issue（不带 UI，~1-2h）
python tests/regression/run_regression.py --no-ui

# 单个 issue
python tests/regression/run_regression.py --only issue-13

# 带 UI 测试（~2-3h，要 DevEco 模拟器）
python tests/regression/run_regression.py

# 报告位置
cat reports/branches/local/report.md
```

### 重建 12 个 fixtures

```bash
python scripts/build_fixtures.py
```

---

## 仓库结构

```
aid-workflow-skills/
├── skills/                      ← 15 个 skill 的源真
│   ├── aid-applying/
│   │   ├── SKILL.md
│   │   └── templates/apply-report-template.md
│   ├── tdd-enforcer/SKILL.md
│   └── ...
├── tests/
│   └── regression/
│       ├── cases/               ← 12 个 issue 的 fixture
│       │   ├── issue-13/
│       │   │   ├── fixture.json
│       │   │   ├── spec/
│       │   │   │   ├── proposal.md
│       │   │   │   ├── info.md
│       │   │   │   ├── tasks.md
│       │   │   │   └── apply-report.md
│       │   │   └── expected/expected.diff
│       │   └── ... (12 个)
│       ├── run_regression.py
│       └── ui_test_runner.py
├── scripts/
│   ├── sync_to_agents.py        ← 同步到 4 个 agent profile
│   ├── sync_from_source.py      ← 一次性反向同步（已废弃）
│   ├── build_fixtures.py        ← 重建 12 fixtures
│   └── package_skills.py        ← 校验 skill 完整性
├── reports/
│   ├── branches/<branch>/       ← 各分支回归报告
│   │   ├── report.md
│   │   └── results.json
├── docs/
│   ├── CONTRIBUTING.md          ← skillopt-01 改 skill 的流程
│   └── CHANGELOG.md             ← 必填的修改历史
├── .github/workflows/
│   └── test-skill-branch.yml    ← CI: PR 触发回归
├── README.md
└── LICENSE
```

---

## skill 改动的 5 铁律（不可违反）

1. **命令必须具体到 `.bat`**
   - ❌ `hvigorw assembleHap`（env 缺失必失败）
   - ✅ `cmd //c "build_hap.bat assembleHap --no-daemon"`

2. **UI 测试必须用 `skill('harmonyos-ui-test')`**
   - ❌ "CLI 不支持，跳过" / 用 Node 单元测试替代
   - ✅ 必须真机/模拟器跑，或显式降级 + 原因

3. **TDD 不可跳步**
   - ❌ "先写代码再补测试" / "这次跳过"
   - ✅ RED 失败测试 → 验证失败 → GREEN 最小实现 → REFACTOR

4. **apply-report.md 数据必须真实**
   - ❌ 编造 PASS 数、截图数
   - ✅ 与 build / uitest 实际输出一致

5. **跑全量测试，不只跑自己改的**
   - ❌ 改完只跑自己加的 test
   - ✅ 跑全量 `hvigorw test@entry`

---

## 为什么不直接用 SkillOpt

本仓库是"人脑版 SkillOpt"：skillopt-01 改 skill → PR 跑回归 → 看报告 → 决定是否 merge。

SkillOpt（microsoft/SkillOpt）能做类似的事，但**对当前 1+N 团队来说 overkill**：
- setup 成本高（adapter/rollout/evaluator + LLM 训练循环）
- 单 skill 优化，跨 skill 联合优化难
- 量化但失去"为什么改了"的可解释性

本仓库的"12 issue 回归"提供了 SkillOpt 90% 的价值（量化、客观、可回归），剩下 10%（自动 train loop）我们用"skillopt-01 + 老板 review"代替。

---

## 贡献者

- **skillopt-01** (littleleafOptimizer) — 主要维护者
- **老板** (223556cy) — 终审
- **rev-01** (littleleafbbbbb) — code review
- **dev-01** (littleleafccccc) — 反馈

## License

MIT
