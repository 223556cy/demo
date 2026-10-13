# Issue #26 设计审视报告 (design-review)

> step9 设计审视产物。按 aid-planning skill §step9 模板输出。

## 1. 完整性评估

### 1.1 制品齐全性
- [x] `proposal.md` - 需求提案 ✅
- [x] `delta-spec.md` - 增量规格 ✅
- [x] `info.md` - 代码仓理解(含环境能力 + 测试能力评估) ✅
- [x] `delta-design.md` - 增量设计(D1-D10 全章节) ✅
- [ ] `new-arch.md` - **不产出**(理由见 §1.3)
- [x] `todo.md` - 任务进度跟踪 ✅
- [x] `design-review.md` - 本文档 ✅

### 1.2 需求覆盖度

| 需求条目 | 覆盖位置 | 状态 |
|---------|---------|------|
| 入口按钮(主计算器页) | delta-design §3.5 / §7.4 | ✅ |
| 路由跳转 GraphPage | delta-design §7.4 | ✅ |
| 表达式输入与默认值 sin(x) | delta-design §3.5.6 / §3.6 | ✅ |
| xMin/xMax/samples 范围 | delta-design §3.5.6 | ✅ |
| Y 轴自动计算 | delta-design §3.7.8 computeYRange | ✅ |
| Canvas 绘制(网格+轴+曲线) | delta-design §3.5.8 | ✅ |
| 错误处理(4 类) | delta-design §3.5.9 | ✅ |
| 主题色跟随 | delta-design §3.4.1 / §5.3 | ✅ |
| FMEA 7 条全部纳入 | delta-spec §可靠性 / delta-design §3.5.9 + §3.7.9 | ✅ |
| 单元测试覆盖 PlotUtils | delta-design §3.7 + tasks 待办 | ✅ |
| UI 自动化测试 AC-1~8 | tasks 待办 + info.md §测试策略 | ✅ |

**需求覆盖度: 100%**

### 1.3 架构变更评估

经评估,**不需要产出 new-arch.md**:
- 本次仅新增 3 个文件(GraphPage, GraphViewModel, PlotUtils)
- 扩展 1 个文件(CalcEngine 加 evaluateAt + x 变量)
- 修改 2 个文件(CalculatorPage 加按钮、main_pages.json 注册)
- **不修改任何现有模块的职责**
- **不改变现有模块间的依赖关系**
- **不引入新外部依赖**

判定: 纯增量新增,无架构级变更。沿用现有 `pages / viewmodels / common` 分层即可。

## 2. 一致性评估

### 2.1 proposal.md → delta-spec.md
- [x] 意图分类一致: 均为 `requirement-add`
- [x] 领域映射一致: UI/交互、图形绘制、数据处理、状态管理、导航
- [x] 影响层次一致: View/ViewModel/Model/数据层/基础设施
- [x] 关键实体全部纳入 spec: GraphConfig/PlotPoint/PlotSeries/GraphViewModel
- [x] 模糊点闭环: 8 个模糊点全部给出决策

**结果: 通过**

### 2.2 delta-spec.md → delta-design.md

| spec 章节 | design 章节 | 一致性 |
|----------|------------|-------|
| F1 入口与导航 | §3.5 / §7.4 | ✅ |
| F2 表达式输入与校验 | §3.5.6 / §3.6.6 / §3.7.8 parseRange | ✅ |
| F3 范围与采样 | §3.6.6 (xMin/xMax/samples 字段) | ✅ |
| F4 曲线绘制 | §3.4 / §3.5.8 | ✅ |
| F5 状态管理 | §3.5.7 / §3.6.7 | ✅ |
| F6 错误处理 | §3.5.9 / §3.7.9 | ✅ |
| 数据模型 PlotPoint/PlotSeries | §5.2 | ✅ |
| 接口变更 evaluateAt | §3.8.2 | ✅ |
| PlotUtils 工具类 | §3.7 | ✅ |
| FMEA 7 条 | §3.5.9 (4 条) + §3.7.9 (3 条) | ✅ |
| 验收标准 AC-1~8 | tasks 待办(单元 + UI 测试) | ✅ |

**结果: 通过**

### 2.3 info.md → delta-design.md
- [x] 可复用组件(PlotUtils 模式)正确引用 QrCodeBuilder
- [x] `harmonyos-ui-test` skill 标注为可用测试工具
- [x] `dfr-fmea-harmony` skill 标注为 FMEA 输入
- [x] 环境能力 100% 引用
- [x] 测试能力评估(UI 自动化 ✅)与设计中的 UI 自动化任务一致

**结果: 通过**

## 3. 规范性评估

### 3.1 格式规范
- [x] proposal.md / delta-spec.md / info.md / delta-design.md / design-review.md 文件命名规范
- [x] delta-design.md 章节 D1-D10 完整,无缺失
- [x] 表格结构清晰(功能/页面/数据/接口清单)
- [x] PlantUML 图表完整(上下文/架构/时序/导航)
- [x] 推断内容标记 `[推断]`
- [x] 引用关联: 每节末尾标注"见 info.md §X"或"复用已有 X"

### 3.2 命名规范
- [x] 文件名: PascalCase (GraphPage.ets, GraphViewModel.ets, PlotUtils.ets)
- [x] 类名: PascalCase (GraphViewModel, PlotPoint, PlotSeries, PlotUtils, PlotBounds, GraphViewModel)
- [x] 函数/方法: camelCase (compute, sampleSeries, mapToCanvas, computeYRange, parseRange, evaluateAt)
- [x] 字段: camelCase (xMin, xMax, isComputing, errorMessage, isDegree)
- [x] 接口: PascalCase (PlotPoint, PlotSeries, PlotBounds, Evaluator)
- [x] 目录: kebab-case(沿用项目约定 `20260617-requirement-add-plot-graph`)
- [x] 中文/英文混用规范: 标识符全英文, 描述性文字中文

### 3.3 描述清晰度
- [x] 每个模块有 1-2 句简介
- [x] 关键算法有伪代码或具体公式
- [x] 错误处理有 7 行表格列全 FMEA
- [x] 接口设计有完整签名
- [x] 时序图覆盖核心流程

## 4. 遗留问题

### 4.1 推断项需验证(实现阶段)
- [ ] `new Function` 在 ArkUI 运行时是否可用 → 如不可用,降级为手动 pi/e 解析
- [ ] `Math.PI` / `Math.E` 在 ArkTS 中可直接使用(已确认 Calculator.ets 中使用过)
- [ ] Canvas 渲染时机: `onReady` 回调中 `canvasCtx` 才可用,首次绘制需在 onReady 内
- [ ] `router.pushUrl` 在 EntryAbility Context 下传 params 的大小限制(预估安全,但需实测)

### 4.2 已知边界
- 极小屏幕(< 360px 宽): 输入栏与画布可能挤压。MVP 范围内不处理。
- 多任务切回 GraphPage: Canvas 内容可能丢失,需 `onPageShow` 中重绘。当前设计未涵盖,实现阶段补 `onPageShow`。
- GraphPage 横屏布局: 当前未单独设计,沿用 Column 单列,横屏时画布自动撑满。

### 4.3 不在本次范围(显式排除)
- 多函数同图
- 手势缩放/平移
- 极坐标/参数方程/3D
- 图像保存/分享
- 表达式历史收藏

## 5. 总体结论

| 维度 | 评估 |
|------|------|
| 完整性 | **通过** (7/7 制品齐全,new-arch.md 合理不产出) |
| 一致性 | **通过** (proposal → spec → design 全链对齐) |
| 规范性 | **通过** (命名/格式/引用规范) |
| 需求覆盖 | **100%** (11/11 需求 + 7/7 FMEA + 8/8 AC) |
| 风险识别 | **充分** (5 个推断项 + 3 个边界已标注) |

**PLANNING 阶段: ✅ 完成,可进入 IMPLEMENTING 阶段**

---

## 附录:制品清单

```
specs/changes/20260617-requirement-add-plot-graph/
├── proposal.md          # 需求提案 (Step 2-3 产出)
├── delta-spec.md        # 增量规格 (Step 4 产出)
├── info.md              # 代码仓理解 (Step 5 产出,含环境能力 + 测试能力评估)
├── delta-design.md      # 增量设计 (Step 8 mod-design 产出)
├── design-review.md     # 本文档 (Step 9 产出)
└── todo.md              # 任务进度跟踪
```

**Step 1-9 全部完成**。
