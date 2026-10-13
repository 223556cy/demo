# Proposal: 自然语言单位换算 — Issue #18

> **Date**: 2026-06-17
> **Type**: requirement-add (新功能)
> **Category**: UX 增强 / 计算能力扩展
> **Priority**: ⭐⭐ (P1 - 中频实用)
> **Issue**: 让计算器能做单位换算,比如"100厘米转英寸"、"30摄氏度转华氏度"
> **变更名称**: unit-conversion(自然语言查询)

---

## 1. 业务背景

OpenCalc 是从 Android 迁移到 HarmonyOS 的科学计算器,目前支持表达式求值、四则运算、三角函数、百分号、历史记录等。
iOS / macOS 自带计算器普遍支持"温度换算"(0°C = 32°F),Android 自带 Calculator 也有"单位换算"独立面板。
但**在输入框里直接说"100 厘米转英寸"就能算**——这在 iOS / Android 自带计算器里都没有,属于"自然语言查询 + 单位换算"的组合能力,具备差异化价值。

典型场景:
- 出差/留学时快速换算距离、重量、温度
- 学生做物理/化学作业时频繁做单位换算
- 日常生活:身高英尺↔厘米、菜谱克↔盎司

## 2. 目标

| # | 目标 | 验收标准 |
|---|------|----------|
| G1 | 中文 NL 模式识别 | "100 厘米转英寸"、"30 摄氏度转华氏度" 正确换算 |
| G2 | 英文 NL 模式识别 | "5ft in cm"、"5 m to ft" 正确换算 |
| G3 | 紧凑无空格识别 | "100 厘米转英寸"(无空格)同样能识别 |
| G4 | 降级到 CalcEngine | "1+2"、"sin(0)" 等表达式不被误判,走原计算引擎 |
| G5 | 跨维度报错 | "5 米转千克" → errorMsg 提示单位不匹配 |
| G6 | 未知单位报错 | "5 xyz 转米" → errorMsg 提示未知单位 |
| G7 | 历史记录 | 换算结果与原计算共用 history 列表,可在 history 面板查看 |
| G8 | 单元测试覆盖 | UnitConverter + NaturalLanguageParser 各自 100% 覆盖核心分支 |
| G9 | 编译通过 | `hvigorw --no-daemon assembleHap` BUILD SUCCESSFUL |

## 3. 非目标 (Non-Goals)

- 不做"独立单位换算面板"(Android 自带 Calculator 那种 6 大类网格)
- 不做"汇率换算"(需要联网 + 实时数据源,超出 MVP)
- 不做"复合单位换算"(如"1 千米每小时 转 米每秒"那种需要表达式解析)
- 不做"自然语言其他语义"(只做单位换算,不做"100 美元等于多少人民币"那种)

## 4. 范围

### In Scope
- 新增 `opencalc/entry/src/main/ets/common/UnitConverter.ets`:声明式单位表 + 换算函数
- 新增 `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets`:自然语言模式识别
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`:onEquals 增加 NL 优先分支
- 单元测试:hypium + Node 端口双套,覆盖长度/质量/时间/温度/跨维度/未知单位/正负向用例
- 历史记录写入:复用现有 HistoryItem 模型
- 降级路径:NL 失败不污染 CalcEngine

### Out of Scope
- 不做 UI 改造(键盘布局、按钮、菜单)
- 不做主题/样式定制
- 不做实时预览(Preview 已在 issue-11 独立完成,本次换算只在按等号时出结果)
- 不做负数/科学计数法扩展(本次 MVP 暂不支持 `-100 摄氏度` 形式)

## 5. 支持的格式 (MVP)

| 格式 | 示例 | 备注 |
|------|------|------|
| 中文紧凑 | `100厘米转英寸` | 无空格 |
| 中文带空格 | `100 厘米 转 英寸` | 容忍任意空白 |
| 中文温度 | `30摄氏度转华氏度` | 摄氏度/华氏度/开尔文 |
| 英文 in | `5ft in cm` | 紧凑 |
| 英文 to | `5 m to ft` | 带空格 |
| 英文为 | `100cm为m` | 中文"为"作关键字 |
| 小数 | `1.5米转英尺` | 浮点支持 |
| 箭头 | `100厘米→英寸` | 箭头作关键字 |

## 6. 不识别的格式 (降级)

- 表达式 / 函数:`1+2`、`sin(0)`、`2^10` → 走 CalcEngine
- 纯数字:`100` → 走 CalcEngine
- 含运算符但非换算模式:`1+2 转 3` → 走 CalcEngine(NL parse 失败)
- 空字符串:`""` → 走 CalcEngine
- 跨维度但 NL 模式成立:`5米转千克` → 换算器返回 NaN → errorMsg
- 未知单位:`5xyz转米` → 换算器返回 NaN → errorMsg

## 7. 支持的单位 (MVP)

| 维度 | 基准 | 单位 |
|------|------|------|
| 长度 (length) | 米 (m) | 毫米 mm, 厘米 cm, 分米 dm, 米 m, 千米 km, 英寸 in, 英尺 ft, 码 yd, 英里 mi |
| 质量 (mass) | 克 (g) | 毫克 mg, 克 g, 千克 kg, 吨 t, 磅 lb, 盎司 oz |
| 时间 (time) | 秒 (s) | 秒 s, 分钟 min, 小时 h, 天 d |
| 温度 (temperature) | 开尔文 (K) | 摄氏度 °C, 华氏度 °F, 开尔文 K(affine 特殊处理) |

## 8. 风险与约束

| 风险 | 等级 | 缓解 |
|------|------|------|
| 单位别名冲突(`m`=米=分钟) | 中 | 在 parser 中按"出现位置 + 关键字前后"消歧;温度用专用 toBase/fromBase 公式 |
| NL parse 误判(`1+2 转 3`) | 中 | 含 `+`/`-`/`*`/`/` 表达式返回 null,走 CalcEngine |
| 浮点精度(摄氏度→华氏度) | 低 | 单元测试用 1e-4 容差 |
| 真实 hdc 不可用阻塞 UI 验证 | 中 | 记录阻塞到 todo.md;fallback 到单元测试 + 代码 review |
| 集成到 onEquals 影响其他表达式 | 低 | 在 try 块开头加 if 守卫,不命中时与原逻辑一致 |

## 9. 价值与优先级

- **用户感知**: 中等(差异化亮点,但不是每天用)
- **实现成本**: 中(2 个新模块 + CalculatorPage 集成)
- **回归保护**: 高(双套单元测试,1:1 端口,核心算法有 hypium 覆盖)
- **架构影响**: 无(纯新增 common/ 下工具类,不创建新 layer)

## 10. 里程碑

| Milestone | 产出 | 状态 |
|-----------|------|------|
| M1 PLANNING | info.md + design.md + design-review.md + tasks.md + proposal.md + delta-spec.md | 已完成 |
| M2 IMPLEMENTING | tasks.md(TDD 任务清单) | 已完成 |
| M3 APPLYING | RED 测试 + GREEN 实现 + REFACTOR + 构建/测试报告 | 已完成(单元测试 32/32 PASS,UI 测试 BLOCKED) |

## 11. 关联文档

- `delta-spec.md` — 增量需求规格(SR-UC-* / AC-UC-*)
- `info.md` — 代码仓上下文
- `design.md` — 系统设计(组件级)
- `design-review.md` — 设计评审记录
- `tasks.md` — TDD 任务分解
- `apply-report.md` — 应用报告(测试结果 + 编译验证)
- `todo.md` — 进度跟踪 + 阻塞诚实披露
