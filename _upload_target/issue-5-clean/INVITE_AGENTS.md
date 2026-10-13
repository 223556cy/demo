# 邀请 3 个员工到仓库 — 老板手工操作指南

> ⚠️ **本步骤必须由老板手工完成**，无法自动化
> 阻塞原因：命中经验教训 #4（dev-01 调 GitHub API 报 401/404）
> 预计耗时：3 分钟

## 📍 操作路径

打开：https://github.com/calculatorHuawei/agent_workflow/settings/access

或者按以下步骤：

1. 访问 https://github.com/calculatorHuawei/agent_workflow
2. 顶部菜单 → **Settings**
3. 左侧菜单 → **Collaborators and teams** → **Add people**

## 👥 需要邀请的 3 个账号

| 员工 | GitHub 用户名 | 邀请时填写的邮箱 |
|------|---------------|-----------------|
| dev-01 | `littleleafccccc` | 2690920195+dev01@qq.com |
| rev-01 | `littleleafbbbbb` | 2690920195+rev01@qq.com |
| pm-01 | `littleleafaaaaa` | 2690920195+pm01@qq.com |

**操作**：复制 GitHub 用户名列，逐个搜索并发送邀请。

## ✅ 接受邀请（员工侧）

每位员工都需要在 **自己的 GitHub 账号** 登录后：

1. 打开 https://github.com/notifications 或查收邮箱（`2690920195+{name}@qq.com`）
2. 找到 `calculatorHuawei invited you to ...` 通知
3. 点击 **Accept invitation**

## 🔍 验证邀请成功

邀请并接受后，老板可以重新跑以下命令验证：

```bash
curl -s -H "Authorization: token <员工 TOKEN>" \
  https://api.github.com/repos/calculatorHuawei/agent_workflow \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('permissions', d.get('message')))"
```

期望输出：
```json
{'admin': True, 'maintain': True, 'push': True, 'triage': True, 'pull': True}
```

如果还是 `Not Found`，说明：
- 邀请没发出 / 没接受
- 老板账号 (`223556cy`) 不是 Org 管理员（无法邀请人）

## ⚠️ 同步待处理事项

邀请完成后，我会立即：
1. 重新验证 API 访问
2. 创建第一个测试 Issue
3. 配置 Windows 计划任务（按经验 #1）
4. 补 handoff.yaml 审计字段

## 📞 完成后请告诉我

完成后回复我"**邀请完成**"，我会接着：
- 验证 3 员工的 API 访问
- 创建测试 Issue
- 配置 cron 计划任务
- 推送最终状态到 GitHub
