# 贡献指南 — 给 skillopt-01 和人类维护者

> 本仓库是 `calculatorHuawei/agent_workflow` 的 4 阶段 AID-Workflow **所有 skill 的源真**（Source of Truth）。
> 任何 skill 的修改都通过 PR 流程，每个 PR 都会跑 12 个历史 issue 的回归测试。

---

## 仓库结构

```
aid-workflow-skills/
├── skills/                     ← ★ 15 个 skill 的源真
│   ├── aid-planning/SKILL.md
│   ├── aid-implementing/SKILL.md
│   ├── aid-applying/SKILL.md
│   ├── aid-archiving/SKILL.md
│   ├── tdd-enforcer/SKILL.md
│   ├── harmonyos-ui-test/SKILL.md
│   ├── ... (15 个)
├── tests/
│   └── regression/             ← 回归测试
│       ├── cases/              ← 12 个历史 issue fixtures
│       ├── run_regression.py   ← 主 runner
│       └── ui_test_runner.py   ← UI 测试（DevEco 模拟器）
├── scripts/
│   ├── sync_to_agents.py       ← 同步到 4 个 agent profile
│   ├── sync_from_source.py     ← 从 calculatorHuawei 拉（已废弃）
│   ├── build_fixtures.py       ← 重建 12 个 fixtures
│   └── package_skills.py       ← 校验 skill 完整性
├── reports/branches/           ← 各分支的回归报告
├── .github/workflows/          ← CI 配置
└── docs/
```

---

## skillopt-01 改 skill 的标准流程

### Step 1: 创建工作分支

```bash
cd D:/huawei/Demo/aid-workflow-skills
git checkout main
git pull origin main
git checkout -b skillopt-01-$(date +%Y%m%d)-{简短描述}
# 例：skillopt-01-20260706-fix-tdd-red-flag
```

分支命名规范：
- 格式：`skillopt-01-YYYYMMDD-{描述}`
- 描述用 kebab-case，3-5 个词
- 例：`skillopt-01-20260708-add-hvigorw-env-check`

### Step 2: 编辑 skill

```bash
# 用编辑器改 skills/aid-applying/SKILL.md 等
# 例：补一条铁律、改 step 顺序、修变量替换
```

**编辑前必查**：
```bash
python scripts/package_skills.py    # 校验现有 skill 完整性
```

### Step 3: 改 changelog（必填）

在 `docs/CHANGELOG.md` 顶部加一条：

```markdown
## [YYYY-MM-DD] skillopt-01 — {描述}

### 修改
- `skills/aid-applying/SKILL.md`: 
  - 补充铁律 E：必须跑全量 hvigorw test@entry
  - 修正 step3-0-4 中 build_hap.bat 转义示例

### 动机
- Issue #14 单位换算 4 轮才过，根本原因：模型没用 build_hap.bat

### 验证
- 跑 `python tests/regression/run_regression.py --branch {branch-name}`
- 预期：compile_rate >= 100%, test_rate >= 90%
```

### Step 4: 本地跑回归（可选，但推荐）

```bash
# 先不带 UI（快）
python tests/regression/run_regression.py \
  --branch skillopt-01-20260706-fix-tdd \
  --no-ui

# 报告在 reports/branches/skillopt-01-20260706-fix-tdd/report.md
cat reports/branches/skillopt-01-20260706-fix-tdd/report.md
```

### Step 5: 提交 + push + 开 PR

```bash
git add skills/ docs/CHANGELOG.md
git commit -m "fix(aid-applying): add iron law E for full test@entry

详见 docs/CHANGELOG.md"
git push origin skillopt-01-20260706-fix-tdd
# 在 GitHub 上开 PR：main <- skillopt-01-20260706-fix-tdd
```

### Step 6: CI 跑回归

PR 触发 `.github/workflows/test-skill-branch.yml`：
1. Self-hosted runner 跑 12 个 issue
2. 生成 report.md
3. 自动 comment 到 PR
4. 上传 artifacts

### Step 7: rev-01 + 老板 review

review 重点：
- **report.md 的 compile_rate / test_rate / ui_rate**
- CHANGELOG 的"动机"是否合理
- 是否有"破坏性变更"（如改了变量名 → 4 个 agent profile 都会失效）

### Step 8: merge + 同步

merge main 后：
- 自动（或手动）跑 `python scripts/sync_to_agents.py --target all`
- 4 个 agent profile 更新

---

## skill 编写规范（铁律）

来自历史 issue 的失败教训总结：

### 铁律 1：命令必须具体到 .bat
```
❌ hvigorw assembleHap         # env 缺失，必失败
✅ cmd //c "build_hap.bat assembleHap --no-daemon"
```

### 铁律 2：UI 测试必须用 skill('harmonyos-ui-test')
```
❌ 跳过 UI 测试因为"CLI 不支持"
❌ 用 Node.js 单元测试替代 UI 测试
✅ 必须调 skill('harmonyos-ui-test')，或显式声明降级
```

### 铁律 3：TDD 不可跳步
```
❌ "先写实现后补测试"
✅ RED 写失败测试 → 验证失败 → GREEN 写最小实现 → REFACTOR
```

### 铁律 4：apply-report.md 数据必须真实
```
❌ 编造 PASS 数、截图数
✅ 数字必须与 build_hap.bat / uitest 实际输出一致
```

### 铁律 5：跑全量测试，不只跑自己改的
```
❌ 改完只跑自己加的 test
✅ 跑全量 hvigorw test@entry
```

---

## 回归测试 12 个 case 的来源

| Issue | 类别 | rev-01 轮次 | UI 测试 |
|---|---|---|---|
| #1 百分号按钮 | UX 增强 | 0 | ✅ |
| #3 实时预览早期 | 实时预览 | 0 | ✅ |
| #9 百分号回归 | UX 增强 | 0 | ✅ |
| #11 实时预览 | 实时预览 | 0 | ✅ |
| #13 二维码分享 | 分享 | 2 | ✅ |
| #14 单位换算 v1 | 单位换算 | 4 | ✅ |
| #15 历史日期分组 | 历史增强 | 2 | ✅ |
| #16 长按 sin 菜单 | 手势增强 | 1 | ✅ |
| #17 粘贴即计算 | 粘贴计算 | 1 | ✅ |
| #18 NL 单位换算 | 单位换算 | 2 | ✅ |
| #22 程序员模式 | 程序员模式 | 1 | ✅ |
| #24 历史搜索 | 历史增强 | 1 | ✅ |

**为什么不只是 1-2 个简单 case**：
- 12 个覆盖了 6 个常见类别（UX / 实时 / 分享 / 换算 / 手势 / 程序员）
- rev-01 轮次从 0 到 4 都有（防止"过拟合简单 case"）
- 4 轮过的 #14 是"最难的"，逼 skill 处理复杂情况

---

## 紧急情况

### 老板说"这个 skill 有问题，立刻修"
1. 不开 PR，直接在 main 上 hotfix
2. 跑回归确认没破坏其他
3. 同步到 4 个 agent profile
4. **事后**补 PR + 补 CHANGELOG

### 回归发现回归率掉到 < 80%
1. 立即 revert 那个 PR 的 commit
2. 老板发 issue 给 skillopt-01
3. skillopt-01 在新分支重做
4. 重跑回归确认回到 100%

---

## 联系方式

- skillopt-01: GitHub `littleleafOptimizer`
- 老板: GitHub `223556cy`
- 工作流相关 issue: https://github.com/calculatorHuawei/agent_workflow/issues
