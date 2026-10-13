# Issue #26 开发任务 (tasks)

> AID IMPLEMENTING 阶段产物。
> 任务粒度: 1-3 小时/任务,TDD 优先(测试先于实现)。

## 任务概述

- **功能名称**: 函数图像绘制 (function-graph-plot)
- **变更类型**: requirement-add
- **关联特性**: 进阶
- **开发阶段**: 从零新增 3 个文件 + 扩展 1 个文件 + 修改 2 个文件
- **预计任务数**: 11 个任务(分 5 阶段)
- **测试策略**: 单元测试优先(PlotUtils 100%) + UI 自动化(基于 capabilities.json ui_test.available=true)

## 任务列表

### 阶段 1:基础设施(纯函数 + 核心扩展)

#### Task 1.1: PlotUtils 单元测试(RED)
**描述**: 先写测试,定义 PlotUtils 4 个方法的契约
**涉及文件**:
- 新建: `opencalc/entry/src/test/ets/common/PlotUtils.test.ets`
**依赖任务**: 无
**验收标准**:
- [ ] 4 个 describe 块:`sampleSeries` / `mapToCanvas` / `computeYRange` / `parseRange`
- [ ] 每个方法至少 3 个 it 用例(正常 / 边界 / 错误)
- [ ] 测试运行 `hvigorw --no-daemon test` 时**先失败**(因为实现未写)
- [ ] 测试用例覆盖:
  - sampleSeries: 线性函数 f(x)=x、全 null、除零函数
  - mapToCanvas: 中心点、四角点、y=null 跳过
  - computeYRange: 正常、全 null、单点退化
  - parseRange: 'pi' / '2*pi' / 'e' / '1.5' / 'abc' / ''
**TDD**: [x] RED

#### Task 1.2: PlotUtils 实现(GREEN)
**描述**: 实现 4 个静态方法,让测试通过
**涉及文件**:
- 新建: `opencalc/entry/src/main/ets/common/PlotUtils.ets`
- 导出: `PlotPoint` / `PlotSeries` / `PlotBounds` 接口, `PlotUtils` 类, `Evaluator` 类型
**依赖任务**: 1.1
**验收标准**:
- [ ] `hvigorw --no-daemon test` 中 `PlotUtils.test.ets` 全绿
- [ ] 4 个方法签名与 delta-design §3.7.6 完全一致
- [ ] `parseRange` 失败时返回 null,不抛异常
- [ ] `computeYRange` 全 null 时返回 `[-1, 1]` 兜底
- [ ] `mapToCanvas` y=null 返回 null
- [ ] **不允许** ArkTS 编译错误(纯 TS 语法,无 UI 依赖)
**TDD**: [x] GREEN

#### Task 1.3: CalcEngine.evaluateAt 单元测试(RED)
**描述**: 测试 evaluateAt 在各种 x 值下的正确性,以及 x 变量支持
**涉及文件**:
- 修改: `opencalc/entry/src/test/ets/calculator/Expression.test.ets`(或新建 Calculator.test.ets)
**依赖任务**: 1.2
**验收标准**:
- [ ] describe 块 `evaluateAt`
- [ ] 测试用例:
  - `evaluateAt('sin(x)', 0, false)` → 0
  - `evaluateAt('sin(x)', 3.14159, false)` → ≈0(< 1e-10)
  - `evaluateAt('x^2', 3, false)` → 9
  - `evaluateAt('2x', 3, false)` → 6(隐式乘)
  - `evaluateAt('1/0', 0, false)` → null(除零)
  - `evaluateAt('log(x)', -1, false)` → null(定义域)
  - `evaluateAt('sin(x', 0, false)` → null(语法)
- [ ] 测试**先失败**(evaluateAt 未实现)
**TDD**: [x] RED

#### Task 1.4: CalcEngine.evaluateAt 实现(GREEN)
**描述**: 扩展 CalcEngine,加 xValue 字段 + evaluateAt 方法 + parseFactor 中识别 x
**涉及文件**:
- 修改: `opencalc/entry/src/main/ets/calculator/Calculator.ets`
**依赖任务**: 1.3
**验收标准**:
- [ ] 现有 `Calculator.test.ets` / `Expression.test.ets` 全过(回归保护)
- [ ] 新增 `evaluateAt` 测试全绿
- [ ] `parseFactor` 中 ASCII 120 (x) 在函数名前特判 → 返回 xValue
- [ ] `evaluateAt` 入口调 `ErrorFlags.reset()`,出口检查所有 ErrorFlags
- [ ] 不修改现有 `evaluate(equation, isDegree)` 行为
**TDD**: [x] GREEN

### 阶段 2:状态管理 + 业务逻辑

#### Task 2.1: GraphViewModel 实现
**描述**: 实现 @Observed 装饰的 ViewModel,管理表达式/范围/采样数/series/错误
**涉及文件**:
- 新建: `opencalc/entry/src/main/ets/viewmodels/GraphViewModel.ets`
**依赖任务**: 1.4
**验收标准**:
- [ ] 字段: expression, xMin, xMax, samples, series, errorMessage, isComputing, isDegree
- [ ] 方法: `setRadianMode(isDeg)`, `compute()`, 私有 `validateInputs()`, 私有 `hasVariable(expr)`
- [ ] `compute()` 流程: validate → Expression.getCleanExpression → CalcEngine.evaluateAt 循环 → PlotUtils.sampleSeries → 错误处理
- [ ] 编译通过(无 UI 依赖,可独立验证)
**TDD**: [x] GREEN(本任务不写单测,与 GraphPage 一起集成测试)

### 阶段 3:UI 层(页面 + 资源)

#### Task 3.1: GraphPage 页面骨架
**描述**: 新建 GraphPage,实现工具栏 / Canvas / 输入栏 / 错误条 4 个区块的 UI 布局
**涉及文件**:
- 新建: `opencalc/entry/src/main/ets/pages/GraphPage.ets`
- 修改: `opencalc/entry/src/main/resources/base/profile/main_pages.json`(注册 pages/GraphPage)
**依赖任务**: 2.1
**验收标准**:
- [ ] 4 个区块渲染正常:
  - 工具栏: ← 返回 + 标题
  - Canvas: 全宽 100%, 高度 60%(`vp2px` 后约 432-720)
  - 输入栏: 表达式 TextInput + xMin/xMax/samples TextInput + 绘制按钮
  - 错误条: Text(空时隐藏)
- [ ] `main_pages.json` 包含 `pages/GraphPage`
- [ ] `hvigorw --no-daemon assembleHap` 编译通过
- [ ] 路由可正常跳转(暂时没有"绘制"按钮逻辑也 OK,UI 渲染 OK)
**TDD**: [ ] REFACTOR(整合测试)

#### Task 3.2: GraphPage 绘制逻辑
**描述**: 实现 Canvas.onReady 中的网格/坐标轴/曲线绘制
**涉及文件**:
- 修改: `opencalc/entry/src/main/ets/pages/GraphPage.ets`
**依赖任务**: 3.1
**验收标准**:
- [ ] Canvas onReady 触发 → 调用 `drawCanvas()`
- [ ] `drawCanvas()` 流程:
  1. 清空 + 填充背景
  2. 绘制网格(每 1 单位一格)
  3. 绘制坐标轴(x=0 黑, y=0 黑,带刻度标签)
  4. 绘制曲线(`mapToCanvas` 逐点连线,跳过 y=null)
  5. 若 series === null 或全失败 → 绘制占位文字
- [ ] 颜色从 `themeIdx` 派生(默认蓝色,theme 0/1/2 映射)
- [ ] 性能: 200 点绘制 < 100ms
**TDD**: [ ] REFACTOR

#### Task 3.3: GraphPage 交互接线
**描述**: 把输入框的 onChange + 绘制按钮 onClick 接到 ViewModel.compute()
**涉及文件**:
- 修改: `opencalc/entry/src/main/ets/pages/GraphPage.ets`
**依赖任务**: 3.2
**验收标准**:
- [ ] 表达式 TextInput onChange → vm.expression = newValue
- [ ] xMin/xMax/samples TextInput onChange → vm 字段更新
- [ ] "绘制"按钮 onClick → vm.compute() → Canvas 触发重绘
- [ ] 错误条: vm.errorMessage 非空时显示
- [ ] "← 返回"按钮 onClick → router.back()
**TDD**: [ ] REFACTOR

#### Task 3.4: CalculatorPage 入口按钮
**描述**: 在 CalculatorPage ToggleRow 新增"📈 绘图"按钮,点击 pushUrl 到 GraphPage
**涉及文件**:
- 修改: `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
- 修改: `opencalc/entry/src/main/resources/base/element/string.json`(新增 graph_title 字符串)
**依赖任务**: 3.3
**验收标准**:
- [ ] ToggleRow 中 "📋" 按钮**之前**新增 "📈" 按钮(参考 📋 样式, fontSize 14, padding 8)
- [ ] onClick → `router.pushUrl({ url: 'pages/GraphPage', params: { expression: this.expression } })`
- [ ] `hvigorw --no-daemon assembleHap` 编译通过
- [ ] 现有 CalculatorPage 行为不变(回归保护)
**TDD**: [ ] REFACTOR

### 阶段 4:测试与验证

#### Task 4.1: 单元测试全量回归
**描述**: 跑全量单元测试,确保新功能 + 现有功能都通过
**涉及文件**:
- (无文件改动)
- 命令: `hvigorw --no-daemon test`
**依赖任务**: 3.4
**验收标准**:
- [ ] `PlotUtils.test.ets` 全绿
- [ ] `Calculator.test.ets` / `Expression.test.ets` 全绿(回归)
- [ ] `List.test.ets` 整体跑通
- [ ] 输出测试报告(成功数 / 失败数)
**TDD**: [x] GREEN(已完成)

#### Task 4.2: 单元测试注册
**描述**: 在 `List.test.ets` 中注册新 test suite,确保 hvigorw 能发现
**涉及文件**:
- 修改: `opencalc/entry/src/test/List.test.ets`
**依赖任务**: 4.1
**验收标准**:
- [ ] `import plotUtilsTest from './ets/common/PlotUtils.test.ets'`
- [ ] `plotUtilsTest()` 在 testsuite() 中被调用
- [ ] `import evaluateAtTest from './ets/calculator/Calculator.test.ets'`(如新建)
- [ ] `hvigorw --no-daemon test` 能发现并执行
**TDD**: [x] GREEN

#### Task 4.3: UI 自动化测试
**描述**: 使用 hdc + harmonyos-ui-test skill 在模拟器上执行 AC 验证
**涉及文件**:
- 新建: `specs/changes/20260617-requirement-add-plot-graph/ui-tests/run_tests.py`
- 新建: `specs/changes/20260617-requirement-add-plot-graph/ui-tests/parse_ui.py`
- 新建: `specs/changes/20260617-requirement-add-plot-graph/ui-tests/screenshot/`(目录)
- 新建: `specs/changes/20260617-requirement-add-plot-graph/ui-tests/results.json`
**依赖任务**: 4.1
**验收标准**:
- [ ] hdc 设备已连接(`hdc list targets` 有输出)
- [ ] 应用已安装到设备(`hdc install -r` 成功)
- [ ] 应用已启动(`aa start` 成功)
- [ ] AC-1 验证: 打开绘图页,Canvas 节点存在
- [ ] AC-2 验证: 修改表达式 `x^2`,Canvas 重绘
- [ ] AC-4 验证: 输入 `sin(x`,错误提示 Text 出现
- [ ] AC-5 验证: 输入 `1+2`,提示"请输入含 x"
- [ ] screenshot/ 包含每步操作截图
- [ ] results.json 含每 AC 的 pass/fail/skip
**TDD**: [x] GREEN(集成测试)

### 阶段 5:文档与提交

#### Task 5.1: APPLYING 阶段执行
**描述**: 调用 aid-applying skill + tdd-enforcer,产生 apply-report.md
**涉及文件**:
- 新建: `specs/changes/20260617-requirement-add-plot-graph/apply-report.md`
**依赖任务**: 4.3
**验收标准**:
- [ ] apply-report.md 包含: 真实代码改动、真实测试结果、UI 验证结果、回归验证、DFX 报告

## 开发顺序

```
Task 1.1 (PlotUtils 测试 RED)
  → Task 1.2 (PlotUtils 实现 GREEN)
    → Task 1.3 (evaluateAt 测试 RED)
      → Task 1.4 (evaluateAt 实现 GREEN)
        → Task 2.1 (GraphViewModel 实现)
          → Task 3.1 (GraphPage 骨架)
            → Task 3.2 (GraphPage 绘制逻辑)
              → Task 3.3 (GraphPage 交互接线)
                → Task 3.4 (CalculatorPage 入口按钮)
                  → Task 4.1 (单元测试全量回归)
                    → Task 4.2 (List.test.ets 注册)
                      → Task 4.3 (UI 自动化测试)
                        → Task 5.1 (APPLYING 阶段)
                          → 完成
```

## 验收计划

| 任务 | 验收方式 | 关键指标 |
|------|---------|----------|
| 1.1 | 跑测试 → 失败 | 编译过 + 测试失败 |
| 1.2 | 跑测试 → 通过 | PlotUtils 4 个方法全绿 |
| 1.3 | 跑测试 → 失败 | 新增测试失败 |
| 1.4 | 跑测试 → 通过 | evaluateAt + 回归全绿 |
| 2.1 | 编译检查 | 字段/方法签名匹配 design |
| 3.1 | 编译 + 跳转 | assembleHap 成功 + 路由可达 |
| 3.2 | 编译 + 视觉 | 网格/轴/曲线渲染正确 |
| 3.3 | 编译 + 行为 | 输入 → 绘制 → 错误流 |
| 3.4 | 编译 + 入口 | 📈 按钮可见,点击跳转 |
| 4.1 | 跑全量测试 | 0 失败 |
| 4.2 | 跑全量测试 | 新 test suite 被发现 |
| 4.3 | 跑 UI 自动化 | 5 个 AC pass,截图存档 |
| 5.1 | 文档完整性 | apply-report.md 齐全 |

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| `parseRange` 中 `new Function` 在 ArkUI 不可用 | 降级方案: 手写 pi/e 解析(只识别字面量) |
| Canvas onReady 触发时机不对 | 在 `onPageShow` 中也重绘一次,确保显示 |
| 路由参数 4KB 限制 | 限制 expression 长度 ≤ 256 字符 |
| 现有 Calculator 回归 | Task 1.4 必须先跑回归测试 |
| hvigorw 编译失败(签名问题) | 用相对路径引用,不引入新依赖 |
| UI 自动化截图无法比对 | 用 dump UI 树节点存在性验证,不像素比对 |

## 关键决策记录

- 状态管理: V1(@Observed + @State)
- 路由: pushUrl
- 错误隔离: ErrorFlags.reset() + 标志检查
- 性能目标: 200 点采样 < 50ms, 绘制 < 100ms
- 测试覆盖: PlotUtils 100%, evaluateAt 关键场景, 8 AC 全部 UI 自动化
- 默认值: sin(x), x ∈ [-2π, 2π], samples=200
