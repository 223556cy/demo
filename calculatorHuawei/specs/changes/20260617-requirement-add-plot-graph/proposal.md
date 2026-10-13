# Issue #26 需求提案 - 函数图像绘制

## 原始需求
> 支持绘制函数图像,输入 sin(x) 显示曲线
>
> 类型: 图形 | ⭐⭐⭐⭐ | 从数值到可视化

## 意图分类
- **类型**: 新增功能
- **一句话概括**: 在计算器中新增"函数绘图"模式,用户输入 `f(x)` 表达式（如 `sin(x)`、`x^2`），应用对表达式在指定 x 区间内采样求值,并在画布上绘制函数曲线,支持坐标轴/网格/坐标范围设置。

## 领域映射
- **UI/交互**: 新增"绘图模式"入口(主计算器页加按钮或 Tab)、独立的绘图页/全屏面板、Canvas 画布组件
- **图形绘制**: ArkUI `Canvas` + `CanvasRenderingContext2D`(绘制坐标轴/网格/曲线/标签)
- **数据处理**: 复用现有 `Expression.ets` 表达式求值引擎,支持把 x 作为变量注入
- **状态管理**: 绘图状态(表达式字符串、xMin/xMax、采样数、视图状态)与计算器主状态隔离
- **导航路由**: 从主计算器页跳转到绘图页(路由参数传表达式可选)

## 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View (pages/) | new + modify | 新增 `GraphPage.ets`;`CalculatorPage.ets` 添加"绘图"入口按钮 |
| ViewModel (新建) | new | 新建 `viewmodels/GraphViewModel.ets`(管理绘图状态、采样、坐标变换) |
| Model | extend | 复用 `Expression.ets` 的 `SolvePostfix` 求值,新增 `evaluateAt(expression, x)` 包装 |
| 数据层 | new (内存) | 仅内存状态,不持久化绘图结果;但允许读取最近一次表达式作为默认 |
| 基础设施 | new | 新建 `common/PlotUtils.ets`(采样/坐标变换工具函数,便于单元测试) |

## 关键实体
- **数据实体**:
  - `GraphConfig { expression: string, xMin: number, xMax: number, samples: number }`
  - `PlotPoint { x: number; y: number | null }` (null 表示定义域外/错误)
  - `PlotSeries { points: PlotPoint[]; config: GraphConfig }`
- **页面实体**:
  - `GraphPage`(新建,全屏画布 + 顶部工具栏 + 底部输入栏)
  - `CalculatorPage`(加 "📈 绘图" 按钮,点击跳转 GraphPage)
- **接口实体**:
  - `Expression.evaluateAt(expr: string, x: number): number | null`(包装 `SolvePostfix`,失败返回 null)
  - `PlotUtils.sampleSeries(expr, xMin, xMax, samples): PlotPoint[]`
  - `PlotUtils.mapToCanvas(p, bounds, canvasSize): { px, py }`
- **事件实体**:
  - "绘制中"加载状态(异步求值耗时场景)
  - "表达式错误"提示(语法错误时显示)
  - "定义域外"跳过(单点求值失败时该点用 null,曲线断开)

## 模糊点
| # | 类别 | 描述 | 严重程度 | 决策 |
|---|------|------|---------|------|
| 1 | 范围模糊 | "函数图像"支持哪些函数? | important | **决策**: 复用现有 `Expression.ets` 支持的所有运算与函数(`+ - * / ^ ! % sin cos tan asin acos atan ln log sqrt exp abs`) + 常量 `pi e`;支持 `x` 变量(大小写不敏感)。 |
| 2 | 行为模糊 | 自变量 x 的范围怎么定? | important | **决策**: 默认 `x ∈ [-2π, 2π]`,UI 提供 4 个输入框 `xMin / xMax`(数值,支持 pi/e 常量识别);Y 轴根据采样结果自动缩放(留 10% 边距)。 |
| 3 | 交互模糊 | 绘图页怎么打开? | important | **决策**: 主计算器页右上角加 "📈" 图标按钮,点击 push 到 `GraphPage`,初始表达式 = 当前计算器输入框内容(若含 `x`)或默认值 `sin(x)`。 |
| 4 | 行为模糊 | 定义域外的点怎么处理(比如 `log(-1)`、`1/0`)? | important | **决策**: 单点求值失败(NaN/Infinity) → 该点 y=null,绘图时跳过该点,曲线在该处断开(不连线)。 |
| 5 | 数据模糊 | 采样密度多少合适? | nice-to-have | **决策**: 默认 200 个采样点(在 360×720 屏幕上 1 像素 ≈ 1.8 个采样,曲线平滑)。可通过 `samples` 字段调整(50-1000)。 |
| 6 | 约束模糊 | 性能要求? | nice-to-have | **决策**: 200 点同步计算目标 < 50ms(实测可达成);若超 1000 点,显示"计算中..."loading。 |
| 7 | 交互模糊 | 是否支持多函数同图? | nice-to-have | **决策**: MVP 不支持,只画 1 条曲线。架构上 `PlotSeries` 预留数组扩展。 |
| 8 | 行为模糊 | 视图是否可缩放/平移? | nice-to-have | **决策**: MVP 不支持手势缩放/平移,只支持改输入框刷新。 |

> **无 blocker 级别模糊点**,可继续。重要模糊点已通过以上决策闭环。

## 复杂度评估
- **等级**: **L(复杂)**
- **理由**:
  - 涉及 3 个技术领域(UI 交互、Canvas 图形、表达式求值)
  - 需要新增 1 个页面 + 1 个 ViewModel + 1 个工具类,涉及 3-4 个文件
  - 需要扩展 `Expression.ets` 接口(`evaluateAt` 包装)
  - 需要新增数学工具(`PlotUtils`)便于单元测试
  - 需要 UI 自动化测试验证绘图结果
  - 但单一核心功能点(画一条曲线),不涉及架构变更

## 备注
- 不涉及阶乘/! 的平台拦截问题(平台封禁的是阶乘算子,绘图是新增模块,不互相影响)
- 绘图模块独立成页,不污染主计算器状态
- 复用 `Expression.ets` 的 `SolvePostfix` 已有能力,扩展而非重写
- 单元测试重点:`PlotUtils` 纯函数 + `Expression.evaluateAt` 在不同 x 下的精度
- UI 测试重点:打开绘图页 → 输入 sin(x) → 看到曲线 + 坐标轴(可用 dump 验证 Canvas 节点存在)

## 输入/输出示例
- 用户操作:在主计算器页点 "📈" → 跳转绘图页 → 默认 `sin(x)` 表达式 → 看到正弦曲线 + 坐标轴
- 用户操作:修改 xMin = -10, xMax = 10, 表达式 = `x^2` → 看到抛物线
- 错误情况:输入 `1/0` (无 x) → 提示"请输入含 x 的函数表达式"
- 错误情况:输入 `log(x)`, x ∈ [-5, 5] → 曲线在 x ≤ 0 处断开(定义域外)
