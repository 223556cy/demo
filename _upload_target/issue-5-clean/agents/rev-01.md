# rev-01 — 代码审查员

## 基本信息

| 字段 | 值 |
|------|-----|
| 员工名字 | `rev-01` |
| 角色 | `reviewer`（代码审查员）|
| Agent 类型 | `hermes` |
| GitHub 用户名 | `littleleafbbbbb` |
| GitHub 邮箱 | `2690920195+rev01@qq.com` |
| Gateway 端口 | `8101` |
| Profile 路径 | `~/.hermes/profiles/rev-01` |
| 上岗时间 | 2026-06-08 19:25:40 |
| 状态 | `active` ✅ Token 已填入 |
| Token 过期 | 2026-09-06 |
| Token 权限 | `admin:org, admin:repo_hook, repo, workflow, delete:packages, write:packages` |

## SOUL 来源

- 本地源：`D:\huawei\ai-native-org-guide\souls\02-开发小哥-SOUL.md`（技术型审查视角）
- 角色定位：代码审查员（技术型 — 共享开发技术栈，转为审查视角）
- 技能：技术栈知识、代码审查、安全漏洞、性能优化、架构合理性
- 注入时间：2026-06-08 21:00:00
- 备注：本地无纯代码审查员模板，使用 02-开发小哥 的技术栈 + 审查视角标注

## 启动命令

```bash
hermes profile use rev-01
hermes gateway start --port 8101
```

## 待办事项

- [x] 注册 GitHub 账号 `littleleafbbbbb`
- [x] 生成 PAT Token（过期 2026-09-06，含 `admin:org, admin:repo_hook`）
- [x] 替换 `~/.hermes/profiles/rev-01/.env` 中的 `PENDING_USER_TO_FILL`
- [ ] 加入 `calculatorHuawei` Organization
- [x] 注入 SOUL.md（来自 `02-开发小哥-SOUL.md` + 审查视角标注）
- [ ] 配置定时任务
- [ ] 启动 Gateway 验证连接
