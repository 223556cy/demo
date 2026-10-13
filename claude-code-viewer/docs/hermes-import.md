# Hermes Session -> Claude Code Viewer Import

`claude-code-viewer` 只读懂 Claude Code 的标准 JSONL 格式,但你的本地
session 数据(d-kimuson/claude-code-viewer 看不到的)存在
`D:\huawei\my_sessions\` 里 —— 那是 Hermes Agent / Kimi-coding 写出来的
**另一种 session 格式**。

`dev/hermes-to-ccv.py` 把 Hermes 的单个 session JSON 转成 Claude Code 的
流式 JSONL,放到 `<claude-dir>/projects/<encoded cwd>/<uuid>.jsonl`,
CCV 直接就能读。

## 数据格式差异

| Hermes (source) | Claude Code (target) |
|---|---|
| 单文件单 JSON,`{id, model, cwd, messages[]}` | 多个 JSONL 行,`{type, message, uuid, timestamp, ...}` |
| `messages[i].role` = `user` / `assistant` / `tool` | `{"type":"user"\|"assistant"}`;tool 结果包成 user 里的 `tool_result` content block |
| `messages[i].tool_calls[i].function.arguments` 是 JSON 字符串 | assistant content blocks 里的 `tool_use.input` 是 dict |
| `messages[i].reasoning_content` | `content` 里加 `{"type":"thinking","thinking":...}` 在 text 前 |
| 无 `parentUuid` chain | 每条 entry 链式 `parentUuid`,CCV 用它回放 UI 时间线 |

## 用法

```bash
# 干跑(不写文件,只看会落到哪里)
python dev/hermes-to-ccv.py --dry-run

# 默认只挑每个 session 的 _end 完整快照
python dev/hermes-to-ccv.py

# 强制转所有 _start/_turnN/_manual 增量快照(会重复)
python dev/hermes-to-ccv.py --all

# 指定来源/输出(默认读 D:\huawei\my_sessions,写到 %USERPROFILE%\.claude)
python dev/hermes-to-ccv.py \
    --source D:\huawei\my_sessions \
    --claude-dir C:\Users\26909\.claude

# 只转前 5 个会话试水
python dev/hermes-to-ccv.py --limit 5
```

转换完**重启 CCV 服务**触发 fullSync,新文件才会出现在项目列表里
(文件 watcher 对新加的根级目录有时不会自动触发)。

## 文件命名规则

Hermes 把每个 session 切成多个时间快照,大致这样:

```
20260609_142839_65e202_start.jsonl    ~1KB   起始快照,通常只有 1-2 个 message
20260609_142839_65e202_turn1.jsonl     ~30KB  每个 turn 结束时的快照
20260609_142839_65e202_turn2.jsonl     ~30KB  ...
...
20260609_142839_65e202_end.jsonl       ~330KB  最终完整快照(所有 messages)
20260609_142839_65e202_manual.jsonl    用户手动保存的中间快照
```

Converter **默认**只挑 `_end`(最新最全)。同一 session 会被压缩成一个
CCV session 文件,不会重复。

## 输出落点

`<cwd>` 编码方式跟 Claude Code 一致:`:` 和 `\` 都变 `-`,盘符小写:

| Hermes cwd | CCV projects 目录 |
|---|---|
| `D:\huawei\my_ai_company` | `~/.claude/projects/d--huawei-my_ai_company/` |
| `D:\huawei\Demo\worktrees\issue-3` | `~/.claude/projects/d--huawei-Demo-worktrees-issue-3/` |
| `(cron 任务,无 cwd)` | `~/.claude/projects/unknown/` |

**注意:** 跟原生 Claude Code session 会合并到同一个目录(session count
会叠加)。如果想分开,改 `--claude-dir` 指向一个空目录。

## 重跑

脚本对每个 session 生成随机 UUID 文件名,**重复跑不会冲突**也不会
覆盖,可以放心反复执行。但老文件不会自动清理 —— 想从头来可以:

```bash
# 清掉所有 import 出的文件(只删 converter 标记的,不动原生 Claude Code)
python dev/hermes-to-ccv.py  # 先跑一次
# 然后手动清理 (或写个清理脚本)
find ~/.claude/projects -name "*.jsonl" \
    -exec grep -l '"version":"hermes-to-ccv' {} \; \
    | xargs rm
```

Windows 下没有 `xargs rm`,用 PowerShell:

```powershell
Get-ChildItem -Recurse ~/.claude/projects -Filter *.jsonl |
  Where-Object { (Select-String -Path $_ -Pattern 'hermes-to-ccv' -Quiet) } |
  Remove-Item
```

## Converter 不是 100% 保真

为了简单,做了几个简化:

- `model` 字段填的是 Hermes session 顶层的 model(kimi-k2.5 等),但
  Claude Code 行的是 Anthropic 模型,UI 里可能显示有点怪。
- `usage`/`input_tokens`/`output_tokens` 没有转 —— Hermes 没存
  per-message usage 拆分,只在 session 顶层有总数。
- Tool results 用 CCV 的 `{"type":"tool_result"}` 包,本来 CCV 是
  期望 Anthropic SDK 那套。功能上能渲染,UI 样式可能稍差。
- 不输出 `file-history-snapshot` / `queue-operation` /
  `permission-mode` 这些 CCV 会自动加的元数据条目 —— 它们缺失不影响
  渲染。

## 一键导入 + 重启

`dev/import-hermes.sh`(bash)或者 Win 用户用 `start.bat` 那个模板:

```python
# 假定你想每次跑 converter 后强制 CCV 重新 fullSync
# 写个一次性脚本即可,没必要常驻
```
