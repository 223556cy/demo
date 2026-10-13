# Team Memory Index — 团队共享记忆索引

> **目的**：让 analysis 沉淀的经验可被 dev-01 / skillopt-01 / rev-01 / pm-01 检索使用
> **写权限**：**仅 analysis** 拥有（单一来源原则，避免脏数据）
> **读权限**：全员（dev-01 / skillopt-01 / rev-01 / pm-01 / 老板）
> **权威优先级**：`SKILL.md` > `Memory` (Memory 是"为什么这样改"的来由记录，不是规则本身)
> **过期策略**：90 天前的条目移入 `archive/` 季度归档

---

## 📁 文件清单

| 文件 | 作用 | 写入触发 | 检索场景 |
|------|------|---------|---------|
| `failures.md` | ❌ 失败案例库 | analysis finalize 时 (verdict=REJECT) | dev-01 被打回时 / skillopt-01 优化时 |
| `successes.md` | ✅ 成功案例库 | analysis finalize 时 (verdict=APPROVE) | skillopt-01 确认优化有效时 |
| `optimization-backlog.md` | 💡 待优化项聚合 | analysis 定期聚合 (频次/优先级) | skillopt-01 找目标时 |
| `archive/` | 季度归档 | 手动 / 自动 | 历史回溯 |

---

## 🔍 检索命令速查

```bash
# 1. 查某个 skill 的所有历史教训
grep -B 1 -A 8 "skill: aid-applying" failures.md successes.md

# 2. 查最近 5 个失败案例
grep -A 7 "^## Issue" failures.md | head -50

# 3. 查高频失败 skill（聚合）
grep "skill:" failures.md | sort | uniq -c | sort -rn

# 4. 查某 priority 的待优化项
grep -A 3 "Priority: HIGH" optimization-backlog.md
```

---

## 📊 统计（自动更新）

<!-- 每次 analysis finalize 时更新 -->

- **失败案例总数**：0
- **成功案例总数**：0
- **待优化项**：0 (HIGH: 0 / MEDIUM: 0 / LOW: 0)
- **最近更新**：2026-07-01

---

## 🗓️ 季度归档

| 季度 | 归档文件 | 条目数 |
|------|---------|--------|
| 2026-Q3 | (待归档) | - |

---

## 📝 写入格式规范

### failures.md / successes.md 条目格式

```markdown
## Issue #<N> - <skill_name> - <YYYY-MM-DD>

- **Verdict**: <APPROVE / REQUEST_CHANGES / CLOSED>
- **Priority**: <🔴 HIGH / 🟡 MEDIUM / 🟢 LOW>
- **Trigger**: <什么场景触发的分析>
- **现象**: <客观描述 50-150 字>
- **根因**: <A/B/C/D 归类 100-300 字>
- **教训**: <可被 dev-01 引用的经验 30-80 字>
- **建议**: <动词开头的具体动作 30-100 字>
- **Session 证据**: `<jsonl 路径>`
- **AID 产物**: `<proposal.md / tasks.md 等>`
```

### optimization-backlog.md 条目格式

```markdown
### <skill_name> - <🔴 HIGH / 🟡 MEDIUM / 🟢 LOW>

- **频次**: <N 次失败 / 30 天>
- **代表性 Issue**: #<N1>, #<N2>, ...
- **根因模式**: <一句话总结>
- **建议优化方向**: <动词开头>
- **首次发现**: <YYYY-MM-DD>
- **状态**: <待处理 / 优化中 / 已合并 / 暂搁置>
```

---

## 🛡️ 维护规则

1. **单一写者** — 只有 analysis 能写入，dev-01 / skillopt-01 有建议可在 issue comment 里 @analysis
2. **不删原则** — 历史不删，过期移归档（保证可追溯）
3. **不复制 SKILL.md** — Memory 是"为什么"，SKILL.md 是"是什么"，不要把规则正文搬过来
4. **不在 Memory 写代码** — 引用 issue / commit 即可
5. **冲突时问老板** — 与 SKILL.md 矛盾时上报，不私自定夺
