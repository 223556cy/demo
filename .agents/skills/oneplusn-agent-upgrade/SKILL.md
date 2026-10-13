---
name: oneplusn-agent-upgrade
description: >
  为已上岗的数字员工进行高级配置升级，使其成为具备增强记忆、搜索能力、语音交互、
  效率优化等能力的"超级员工"。
  使用场景：(1) 数字员工基础配置完成后，需要增强其能力，
  (2) 为特定数字员工添加搜索/语音/记忆等高级功能，
  (3) 批量升级所有数字员工的配置，
  (4) 为数字员工添加新的高级能力模块。
  支持：逐个升级、批量升级、参数化配置。
  目前仅支持 Hermes Agent，未来将增加对 OpenClaw 等框架的支持。
---

# 数字员工升级

将已上岗的数字员工升级为具备高级能力的"超级员工"。

> **Agent 框架支持**：目前以下高级配置仅适用于 **Hermes Agent**。
> 未来将增加对 **OpenClaw**、**Codex**、**Cursor Agent** 等框架的支持。

## 升级流程

```
确定升级目标（单个/批量）
       ↓
选择升级模块（记忆/搜索/语音/效率）
       ↓
安装依赖（按需）
       ↓
配置参数
       ↓
重启 Gateway 生效
       ↓
验证
```

## 升级模块

| 模块 | 能力 | 依赖 | 复杂度 |
|------|------|------|--------|
| Hindsight 记忆 | 长期记忆增强 | hindsight-all | 中 |
| 搜索感知 | 网络搜索能力 | ddgs / tavily | 低 |
| 语音交互 | STT/TTS | faster-whisper / edge-tts | 中 |
| 效率优化 | 成本/压缩/进化 | 内置 | 低 |

## 快速开始

### 单个升级

```bash
python3 scripts/upgrade_agent.py \
  --handoff handoff.yaml \
  --name dev-01 \
  --modules hindsight,search,voice
```

### 批量升级

```bash
python3 scripts/upgrade_agent.py \
  --handoff handoff.yaml \
  --all \
  --modules hindsight,search
```

### 交互式升级

```bash
python3 scripts/upgrade_agent.py --handoff handoff.yaml --interactive
```

## 详细配置

详见 [references/advanced-config.md](references/advanced-config.md)。

## 验证

```bash
# 验证记忆系统
hermes memory status

# 验证搜索
curl -s "搜索最新 AI 新闻"

# 验证语音
# /voice on

# 验证效率
hermes insights --days 7
```

## 文件速查

| 文件 | 用途 |
|------|------|
| `references/advanced-config.md` | 各模块的详细安装和配置步骤 |
| `scripts/upgrade_agent.py` | 升级脚本（支持单个/批量/交互式） |