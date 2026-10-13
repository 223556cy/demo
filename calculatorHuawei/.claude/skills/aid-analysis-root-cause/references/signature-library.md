# Problem Signature Library(问题签名库)

> 强制从以下 **10 个** problem_signature 里选, **不准自创**。
> dispatch_analysis.py 用此表校验 JSON `problem_signature` 字段, 不在库内的自创签名直接拒收(防止每个分析员发明的命名漂移)。

## 10 个签名(版本 v2.0 trial, 2026-07-08 固化)

| # | Signature | 描述 | 锚点 issue | 典型 reasoning | 典型 target_skill |
|---|-----------|------|-----------|----------------|-------------------|
| 1 | `multi-step-skip` | 多个连续步骤被跳过(合规审计缺失) | **#25** (signoff+4要素+checkbox) | 演绎 | aid-applying |
| 2 | `equiv-class-insufficient` | 等价类覆盖不足(单函数 ≠ 等价类) | **#26** | 溯因 + 类比 | tdd-enforcer |
| 3 | `env-probe-incomplete` | 环境探测步骤不完整(Q&A 排障不全) | **#27** (缺 tconn) | 归纳 + 反证 | harmonyos-ui-test |
| 4 | `forbidden-block-bypassed` | 强制块/反模式示例被跳过(字符级吻合) | **#29** | 演绎(文本比对) | aid-applying |
| 5 | `cross-stage-contract-leak` | 阶段间契约不一致(上游产物 ≠ 下游期望) | (待发现) | 类比 + 归纳 | 跨 skill |
| 6 | `silent-production-failure` | 单测+UI 都过, production 才暴露 | **#26** (78/78 单测+11/11 UI 还出 fix) | 溯因 | tdd-enforcer / aid-applying |
| 7 | `multi-bug-discovered` | 单现象 → 多根因, 任一不修都失败 | **rev01_second_bug**(时序 + 默认值) | 演绎 + 归纳 | aid-applying / 源码 |
| 8 | `default-value-trap` | 默认值/初始状态错导致沉默失败(新装用户必现) | **rev01_second_bug** (`radiansDefault=false` 反向) | 归纳 + 反证 | 源码 / config |
| 9 | `runtime-only-bug` | 静态看逻辑对, 运行时才暴露 | **rev01_second_bug** (hilog 显 deg=true) | 反证 + B-10 | 源码 |
| 10 | `closed-loop-verified` | skillopt 修复落地有效(regression-done 路径) | **#34** | verify(非诊断) | N/A |

## 签名判定规则

- **写 JSON 前**先扫这个表
- 找到匹配的 → 直接用对应 `signature` 值
- 找不到 → **不准**自创, 改用 `multi-bug-discovered`(多 bug 兜底)或回 D 类外部因素
- **新增签名流程**: 出现 5 次以上的未签名模式 → 老板批准后入库(本表更新)

## 签名 vs 归类(A/B/C/D)的关系

| Signature | 常见归类 | 说明 |
|-----------|---------|------|
| `multi-step-skip` | B (漏掉步骤) | 加 imperative 规则 |
| `forbidden-block-bypassed` | B 或 C | 强制块存在但被跳过(B) / 措辞歧义(C) |
| `equiv-class-insufficient` | B | 漏掉等价类维度 |
| `env-probe-incomplete` | B | 漏掉环境探测步骤 |
| `cross-stage-contract-leak` | C | 上下游契约措辞不严 |
| `silent-production-failure` | C 或 B | 测试覆盖盲区 |
| `multi-bug-discovered` | (组合) | 多 bug 同时命中 |
| `default-value-trap` | B (源码/config) | 漏掉默认值校验 |
| `runtime-only-bug` | C (静态 vs 运行时) | 需 B-10 运行时证据 |
| `closed-loop-verified` | (verify 模式) | regression-done 路径专用 |
