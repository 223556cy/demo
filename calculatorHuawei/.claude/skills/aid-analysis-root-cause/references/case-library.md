# Case Library(锚点案例库)

> 5 个 issue 经验表 + 推理深度升级路线。给 `aid-analysis-root-cause` B-0 选方法 + 跨 issue 聚类做参考。

## 5 个锚点案例

| Issue | 现象摘要 | 方法 | 签名 | 教训(一句话) |
|-------|----------|------|------|--------------|
| **#25** | signoff 缺 + 4 要素全跳 + checkbox 未勾 | 演绎 | `multi-step-skip` | dev-01 re-dispatch 不审计前序产物 |
| **#26** | 78/78 单测 + 11/11 UI PASS 还出 5 个 fix commit | 溯因 + 类比 | `equiv-class-insufficient` + `silent-production-failure` | "1 测 1 行为" 不够, 缺等价类硬指标 |
| **#27** | dev-01 误判 TCP 模拟器离线, rev-01 反证环境可用 | 归纳 + 反证 | `env-probe-incomplete` | Q1 排障不全, 缺 tconn |
| **#29** | 4 要素全是"诚标注"自由文体, 字符级匹配反模式示例 | 演绎 | `forbidden-block-bypassed` | SKILL.md 反模式示例 = 自检 checklist |
| **#34** | skillopt-01 修复落地 + 找到新 bug | verify | `closed-loop-verified` | 闭环验证不重跑 skillopt |
| **rev01_second_bug** | "图是直线"现象下双根因(时序 + 默认值) | 演绎 + 归纳 | `multi-bug-discovered` + `default-value-trap` + `runtime-only-bug` | 静态看逻辑对, runtime 才暴露; 单 bug 探测会漏 1/2 |

## 案例速查(按 signature 反查)

### `multi-step-skip` (#25)
- 现象: apply-report.md 缺失 / signoff 缺 / checkboxes 未勾
- 根因: skill 流程有 step 但没有 imperative 强制, claude 跳过
- 优化方向: B 类 — 加 imperative (must) 规则
- 验收: 跑 N 个 issue 复测, 每个 step 都执行

### `equiv-class-insufficient` (#26)
- 现象: 78/78 单测 + 11/11 UI PASS, production 出 fix
- 根因: 测试覆盖维度只测"单函数行为", 没测"等价类"(边界 / 异常路径)
- 优化方向: B 类 — tdd-enforcer 加等价类硬指标
- 验收: 等价类覆盖 ≥ N 类 / 函数, 边界值测试齐

### `env-probe-incomplete` (#27)
- 现象: dev-01 报"模拟器离线", 实际可用
- 根因: Q1 排障步骤不全, 缺 `tconn` 探测
- 优化方向: B 类 — harmonyos-ui-test 加 `tconn` + 备用 fallback
- 验收: 跑 N 个 dev-01 issue, 误报率 < 5%

### `forbidden-block-bypassed` (#29)
- 现象: 4 要素用自由文体写, 跳过反模式示例
- 根因: SKILL.md 反模式示例 = 字符级自检 checklist, claude 没看
- 优化方向: B/C 类 — 反模式示例前加"必须字符级匹配, 否则视为未通过"
- 验收: dev-02 跑回归, 4 要素格式 100% 命中

### `multi-bug-discovered` + `default-value-trap` + `runtime-only-bug` (rev01_second_bug)
- 现象: "图是直线" — 静态看逻辑对, runtime 出错
- 双根因:
  1. 时序 race(setTimeout 异步 + loadPrefs 未完成触发 compute)
  2. 默认值反向(`radiansDefault=false`,新装用户走错默认)
- 根因: 单 bug 探测会漏 1/2, 必须 B-9 三问穷尽
- 优化方向:
  - 时序 — aid-applying 加 must (await 链)
  - 默认值 — 源码 / config 加默认值校验 + 反向 case 测试
- 验收: 5 个等价类测试全过, 时序 race 测试不命中

### `closed-loop-verified` (#34)
- 现象: skillopt-01 修复后, dev-02 跑出真 bug
- 根因: 闭环验证发现 skillopt 修复有效 + 暴露新 bug
- 优化方向: 不动 skill(只 verify)
- 验收: regression-done 标签 + analysis 出 [approved] verdict

## 推理深度升级路线

| 升级层 | 何时做 | 怎么做 | 输出字段 |
|--------|--------|--------|----------|
| **单点加深** | 默认 | so why ≥ 3 层 (B-3 已固化) | root_cause_analysis |
| **横向比对** | 同一 signature 在 ≥ 2 issue 出现 | 扫 `analysis-logs/` 同 signature 找模式 | aggregation_report(可选) |
| **纵向穿透** | 沿 AID 主链找契约断点 | 沿 planning → impl → apply → archive 看产物契约 | cross-stage-contract-leak signature |

## 跨 issue 比对的具体执行

每次分析 B-0 选方法时, 自动跑以下比对(Claude 自动):
```
grep -l "problem_signature.*<signature>" .claude/analysis-logs/*/issue-*-diagnosis.json
```

- 找到 ≥ 2 个历史案例 → 在 `related_issues` 数组写入 `[N1, N2, ...]`
- 找到 0 个 → `related_issues = []`(此时该 signature 是首次发现,单独修复也合理)
- 找到 ≥ 3 个 → 标注 `cluster_id`, 触发 skillopt 的"高优先级系统性问题"流程
