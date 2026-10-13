# Screenshots 目录 — 8 个 SC 场景

## 限制声明（铁律 7 诚实记录）

**当前环境无 hdc 设备**：`hdc list targets` 返回 `[Empty]`，无法在真机/模拟器上跑 UI 自动化。

按 aid-applying skill step3-2-2 + harmonyos-ui-test skill，本应在此目录存放 8 个 SC 场景的截图（SC-001~SC-008）：

| 场景 | 预期文件 | 状态 |
|------|---------|------|
| SC-001 空历史不显示搜索框 | `sc-001-empty-history.png` | ⚠️ 待 hdc 设备 |
| SC-002 搜索 "sin" 实时过滤 | `sc-002-search-sin.png` | ⚠️ 待 hdc 设备 |
| SC-003 搜索 "xyz123abc" 无匹配 | `sc-003-no-match.png` | ⚠️ 待 hdc 设备 |
| SC-004 点击 X 清空恢复全量 | `sc-004-clear-x.png` | ⚠️ 待 hdc 设备 |
| SC-005 大小写不敏感 "SIN" | `sc-005-case-insensitive.png` | ⚠️ 待 hdc 设备 |
| SC-006 搜索时新增历史 | `sc-006-new-item-during-search.png` | ⚠️ 待 hdc 设备 |
| SC-007 搜索时左滑删除 | `sc-007-delete-during-search.png` | ⚠️ 待 hdc 设备 |
| SC-008 横屏布局 | `sc-008-landscape.png` | ⚠️ 待 hdc 设备 |

## 替代验证：逻辑等价

由于 UI 截图无法采集，用 `test/scenarios.test.mjs` 做逻辑等价验证（8/8 pass）：

```bash
$ node --test test/scenarios.test.mjs
ℹ tests 8
ℹ pass 8
ℹ fail 0
```

## 重跑命令（设备就绪后）

```bash
# 1. 启动模拟器（DevEco Studio 设备管理器）
# 2. 确认 hdc 可见
hdc list targets
# 3. 启动应用
hdc shell aa start -a EntryAbility -b <bundleName>
# 4. 跑场景 + 截图（按 harmonyos-ui-test skill）
```
