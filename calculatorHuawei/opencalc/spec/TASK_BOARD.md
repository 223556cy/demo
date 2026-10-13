# OpenCalc HarmonyOS — 任务看板

> **Date:** 2026-05-07
> **Methodology:** Spec-First + Atomic Tasks + Depth-First
> **Standard:** 5项验收标准（编译/状态/乐观回滚/中文错误/空态引导）

---

## 验证标准

任务标记为 VERIFIED 需全部通过：
- [ ] 编译零错误（hvigor assembleHap BUILD SUCCESSFUL）
- [ ] 所有状态路径可触发
- [ ] 错误信息中文可读
- [ ] 数字精度与 Android 版本一致
- [ ] 功能行为与 Android 版本一致

---

## 任务分解

### Module A: 项目骨架 (4 tasks)

| # | Task | State | Verification |
|---|------|:-----:|------|
| A1 | 创建 HarmonyOS 项目结构（entry HAP + build-profile + module.json5 + main_pages.json） | ⬜ TODO | hvigor assembleHap BUILD SUCCESSFUL（空页面） |
| A2 | 配置签名（debug cert）+ 资源文件（string.json, media/icon） | ⬜ TODO | 签名配置无报错 |
| A3 | 添加 Index 占位页面（"OpenCalc 迁移中..."） | ⬜ TODO | 页面显示 |
| A4 | 创建 Models.ets（CalculatorError 枚举 + HistoryItem 接口 + Preferences 接口） | ⬜ TODO | 类型定义无编译错误 |

### Module B: 计算引擎 — 纯逻辑 (4 tasks)

| # | Task | State | Verification |
|---|------|:-----:|------|
| B1 | 移植 NumberFormatter（格式化/千分位/精度/小数分隔符） | ⬜ TODO | 移植 Android 的 NumberFormatterTest 用例，全部通过 |
| B2 | 移植 Expression（符号替换/隐式乘/√/%/!/括号补齐） | ⬜ TODO | 移植 ExpressionUnitTest，全部通过 |
| B3 | 移植 Calculator 核心（递归下降解析器 + number 运算） | ⬜ TODO | 100+ 表达式计算结果与 Android 一致 |
| B4 | 移植 Calculator 数学函数（sin/cos/tan/ln/log/exp/√/阶乘/幂/arcsin/arccos/arctan） | ⬜ TODO | 函数计算结果与 Android 一致（精度 1e-10） |

### Module C: 偏好存储 (2 tasks)

| # | Task | State | Verification |
|---|------|:-----:|------|
| C1 | 移植 MyPreferences → ArkTS PreferencesStore（get/set 所有 8 个 key） | ⬜ TODO | 读写 + 默认值 正确 |
| C2 | 历史记录持久化（HistoryItem[] ↔ JSON string → preferences） | ⬜ TODO | 写入→读取→反序列化 无损 |

### Module D: 主计算器页面 — UI (6 tasks)

| # | Task | State | Verification |
|---|------|:-----:|------|
| D1 | 基础布局：显示屏（上下两行：表达式+结果）+ 按钮网格（5列×N行） | ⬜ TODO | 与 Android 布局一致，按钮可见可点 |
| D2 | 数字按钮 + 运算符按钮 → 表达式拼接 + @State 实时更新 | ⬜ TODO | 输入 1+2×3 显示正确 |
| D3 | "=" 按钮：Expression → Calculator → NumberFormatter → 显示结果 + 添加到历史 | ⬜ TODO | 1+1=2, sin(30)=0.5 |
| D4 | 科学模式切换（横屏/按钮触发）：显示 sin/cos/tan/ln/log/√/π/e/^/!/() | ⬜ TODO | 切换后按钮显示/隐藏正确 |
| D5 | 错误处理：除零/syntax error/domain error/infinity 显示中文错误 | ⬜ TODO | 1/0→"除数不能为零", 语法错→"表达式错误" |
| D6 | 辅助功能：AC 清空、退格、复制结果、振动反馈 | ⬜ TODO | 全部功能可用 |

### Module E: 历史记录 (3 tasks)

| # | Task | State | Verification |
|---|------|:-----:|------|
| E1 | 历史列表 UI：List + ForEach 显示历史记录（表达式 + 结果） | ⬜ TODO | 计算后历史列表更新 |
| E2 | 滑动删除历史条目 | ⬜ TODO | 左滑出现删除，删除后列表更新+持久化 |
| E3 | 点击历史条目 → 回填表达式、长按 → 复制结果 | ⬜ TODO | 点击回填、长按复制 |

### Module F: 设置页面 (3 tasks)

| # | Task | State | Verification |
|---|------|:-----:|------|
| F1 | 设置页面 UI（8 项设置，List + Toggle/Slider/Select） | ⬜ TODO | 页面显示，所有控件可交互 |
| F2 | 设置持久化（修改后即时保存到 PreferencesStore） | ⬜ TODO | 关闭重开后设置保持 |
| F3 | 设置生效：主题切换/振动/防休眠/精度/角度弧度/历史数量 | ⬜ TODO | 修改设置后立即生效 |

### Module G: 主题 + 关于 (2 tasks)

| # | Task | State | Verification |
|---|------|:-----:|------|
| G1 | 主题系统：3 种配色（默认/AMOLED/Material You）+ 日夜模式 | ⬜ TODO | 切换主题后所有页面颜色变化 |
| G2 | 关于页面：版本号 + 开源许可 + GitHub 链接 | ⬜ TODO | 页面正确显示 |

---

## 进度追踪

```
总任务: 24
├── ⬜ TODO:     24
├── 🔄 DOING:     0
├── ✅ DONE:      0
└── ⭐ VERIFIED:  0

完成度: 0/24
```

## 迁移日志

见 `progress/2026-05-07.md`
