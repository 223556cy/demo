# 💡 Optimization Backlog — 待优化项聚合

> **聚合者**：analysis (定期从 failures.md 聚合高频 skill)
> **消费者**：skillopt-01 找目标时
> **更新机制**：每次 analysis finalize 时增量更新

---

## 当前 Backlog

<!-- 按 Priority + 频次 排序 -->

### aid-applying - 🔴 HIGH

- **代表性 Issue**: #25, #28, #22
- **频次**: 1 次
- **代表性 Issue**: #29
- **根因模式**: 归类为 B(漏掉步骤)。aid-applying/SKILL.md:251-318 的 'step3-2-2b-降级:强制检查块 (铁律 7 兜底)' 明确写出当 hdc list targets=E
- **建议优化方向**: 在 step3-2-2b-降级 第 5 步末尾追加 imperative self-check 块:写完 apply-report.md 后必须跑 SKILL.md:278-300 的四条 grep 自检命令 (用户书面同意/todo ⏳ 三要素/capabilities.json unavailable/hdc 原始输出),任一 FAIL 禁止 commit/push 并自动 verdict=REQUEST_CHANGES;同时删除重复的第二份降级块 (lines 320-386 是 251-318 的完全重复,违反单一可信源)。
- **首次发现**: 2026-07-07
- **状态**: 待处理

---
### (暂无) 🔴 HIGH

### (暂无) 🟡 MEDIUM

### (暂无) 🟢 LOW

---

## 已优化 / 已合并

<!-- skillopt-01 合并后移到此处（保留证据链） -->

| Skill | 优化轮次 | 合并 Issue | 状态 |
|-------|---------|-----------|------|
| (暂无) | - | - | - |

---

## 已搁置（需老板决策）

| Skill | 搁置原因 | 提出日期 | 决策状态 |
|-------|---------|---------|---------|
| (暂无) | - | - | - |

---

<!--
### 模板（analysis 聚合后追加）

### <skill_name> - <🔴 HIGH / 🟡 MEDIUM / 🟢 LOW>

- **频次**: <N 次失败 / 30 天>
- **代表性 Issue**: #<N1>, #<N2>, ...
- **根因模式**: <一句话总结>
- **建议优化方向**: <动词开头>
- **首次发现**: <YYYY-MM-DD>
- **状态**: 待处理 / 优化中 / 已合并 / 暂搁置
- **关联失败条目**: <failures.md 行号或锚点>
-->
