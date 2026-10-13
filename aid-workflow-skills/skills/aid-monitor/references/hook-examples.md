# Hook 配置示例

## 概述

aid-monitor 支持通过 hook 机制在对话结束时自动触发。
由于不同用户使用不同的 AI 编码工具，hook 的具体实现因工具而异。

本文档提供常见工具的 hook 配置示例，供首次配置时参考。

---

## Claude Code Hooks

Claude Code 支持在 `.claude/hooks/` 目录中配置 hook。

### 方式 1：PostToolUse Hook（推荐）

在项目根目录创建 `.claude/settings.json`，添加 hook 配置：

```json
{
  "hooks": {
    "stop": [
      {
        "matcher": "",
        "command": "echo '/aid-monitor'"
      }
    ]
  }
}
```

> 注意：Claude Code 的 hook 机制可能随版本更新变化，请参考最新文档。

### 方式 2：Session End 提示

在 `CLAUDE.md` 中添加提示：

```markdown
## 会话结束提醒

在每次对话即将结束时（用户说"结束"、"完成"、或长时间无新指令），
主动询问用户是否需要执行 `/aid-monitor` 审查本次会话。
```

---

## OpenCode Hooks

OpenCode 支持自定义 slash command 和 hook。

### 方式：自定义命令链

在 OpenCode 配置中，可以将 `/aid-monitor` 作为会话结束流程的一部分。

---

## Cursor / Windsurf / 其他 IDE Agent

### 方式：Rules 文件提示

在项目的 rules 文件（如 `.cursorrules`、`.windsurfrules`）中添加：

```
在每次对话结束前，如果本次对话涉及代码生成或修改，
主动执行错误审查流程（参考 skills/monitoring/aid-monitor/SKILL.md）。
```

---

## 通用方式：手动触发

如果工具不支持自动 hook，用户可以：
1. 在对话结束前手动输入 `/aid-monitor`
2. 养成习惯：每次编码会话结束前执行一次审查

---

## 配置存储

hook 配置完成后，建议在项目中记录配置方式，便于团队成员复用：

```
specs/guidelines/.monitor-config
```

内容示例：
```
hook_type: claude-code-settings
domain: arkts
auto_trigger: true
```

---

## 注意事项

1. hook 必须在对话结束**前**触发（上下文仍可用时），而非结束后
2. 如果 hook 机制不可靠，建议同时保留手动触发习惯
3. hook 配置是项目级别的，不同项目可以有不同配置
