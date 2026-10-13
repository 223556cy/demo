# Reasoning Methods(推理方法库)

> 5 种推理方法详表, 给 `aid-analysis-root-cause` B-0 选方法时参考。
> **铁律**: B-0 必须先**列 ≥ 2 个候选方法**, 用不同方法攻击同一现象, 看哪个站得更稳。单方法 = 推理脆弱。

## 5 种推理方法

### 1. 演绎 (Deductive)

**适用**: 现象有 SKILL.md 显式规则可对照。

**推理方向**: 规则 → 检查应用情况

**锚点案例**:
- **#25**: signoff / 4 要素 / checkbox 都有规则但漏跳
- **#29**: 降级强制块存在但被跳过

**思维模板**:
```
1. 找 SKILL.md 里的相关规则
2. 检查现象是否符合规则(逐条对照)
3. 不符合 → 直接定位到 step + 行号
4. 符合 → 演绎不命中, 换方法
```

**典型输出**:
- 归类: B(漏掉步骤)或 C(理解偏差)
- 优化方向: 加强制 / 加精确
- 证据强度: literal(SKILL.md 文本 + 现象对照)

### 2. 归纳 (Inductive)

**适用**: 多现象 / 多失败指向同一处。

**推理方向**: 失败清单 → 抽象共同缺失

**锚点案例**:
- **#27**: 整套环境探测失败 → 抽象到"缺 tconn 这一步"

**思维模板**:
```
1. 列出所有失败点
2. 找共性(N 个失败是否缺同一步骤)
3. 抽象到根因层
4. 验证:补上根因层后,N 个失败是否都消失
```

**典型输出**:
- 归类: B(漏掉步骤)
- 优化方向: 加缺失步骤
- 证据强度: literal(失败清单) + inferred(共性抽象)

### 3. 溯因 (Abductive)

**适用**: 现象无明确规则, 多个解释都合理。

**推理方向**: 现象 → 最可能根因(奥卡姆)

**锚点案例**:
- **#26**: 单测全过 UI PASS 还出 fix commit → 抽象到"等价类指标模糊"

**思维模板**:
```
1. 列出 ≥ 2 个可能的解释
2. 奥卡姆:选最简单的(假设最少)
3. 验证:用 B-5 反事实,如果这个根因是 X, 还应该看到 Y, 验证 Y 是否存在
4. 不存在 → 换下一个解释
```

**典型输出**:
- 归类: B(漏掉维度)或 C(规则不严)
- 优化方向: 加缺失维度
- 证据强度: inferred(从现象抽象) + speculated(未验证前)

### 4. 类比 (Analogical)

**适用**: 现象与历史案例相似。

**推理方向**: 历史根因 → 当前套用 → 验差异

**锚点案例**:
- 跨 issue 共性识别(见 [case-library.md](case-library.md))

**思维模板**:
```
1. 扫 case-library 找相似现象
2. 取历史根因作为假设
3. 验证差异:本次与历史的边界条件
4. 差异大 → 不用类比, 换方法
5. 差异小 → 直接套用
```

**典型输出**:
- 归类: 同历史案例
- 优化方向: 同历史案例
- 证据强度: literal(历史案例) + inferred(类比映射)

### 5. 反证 (Counterfactual)

**适用**: 现象需排除其他解释。

**推理方向**: 假设 → 反驳/确认(other things didn't happen)

**锚点案例**:
- **#27**: rev-01 反证 — "跑通" → "环境实际可用"(反驳 dev-01 的"模拟器离线")

**思维模板**:
```
1. 提一个假设 H
2. 推 H 为真时, 还应该看到什么(其他 things)
3. 检查这些 other things 是否真发生
4. 没发生 → 反驳 H
5. 发生了 → 确认 H(暂时)
```

**典型输出**:
- 用作"反驳工具" — 配合其他方法
- 不单独使用, 必须 B-5 + B-6 引用

## B-0 选方法的实操

```python
# 伪代码
def choose_reasoning_method(phenomenon, evidence_count, has_explicit_rule, has_similar_case):
    candidates = []
    
    if has_explicit_rule:
        candidates.append("deductive")
    
    if evidence_count >= 3:
        candidates.append("inductive")
    
    if not has_explicit_rule:
        candidates.append("abductive")
    
    if has_similar_case:
        candidates.append("analogical")
    
    # 反证作为辅助, 必选
    candidates.append("counterfactual")
    
    # 至少 2 个
    assert len(candidates) >= 2, f"现象 '{phenomenon}' 信息不足, 需要更多证据"
    
    # 写入 JSON
    return candidates[0], candidates[1]  # primary, secondary
```

## 写 JSON 时

- `reasoning_method` 字段 = `["primary", "secondary"]`(数组)
- 例: `["abductive", "analogical"]` 或 `["inductive", "counterfactual"]`
- 触发 4 闭环验证可缺 `reasoning_method`(regression-done 路径)

## 与因果链(B-2)的关系

每种方法都通过因果链落地:
```
fact_a → [机制: ...] → fact_b → [机制: ...] → L3
```

- 演绎: fact_a = 规则, fact_b = 现象不命中规则
- 归纳: fact_a = 失败1, fact_b = 失败2, 共同缺失
- 溯因: fact_a = 现象, fact_b = 最可能假设
- 类比: fact_a = 历史 case, fact_b = 当前 case
- 反证: fact_a = 假设, fact_b = other things didn't happen
