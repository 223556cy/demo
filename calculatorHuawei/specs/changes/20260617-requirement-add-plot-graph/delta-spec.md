# Issue #26 增量规格说明 (delta-spec)

> 项目已存在 `feat-calculator` spec,本文档仅描述新增/修改内容。
> 参考模板: aid-planning/templates/delta-spec-template.md

## 需求概述

在 HarmonyOS 计算器 (opencalc) 中新增 **函数图像绘制** 功能。用户从主计算器页进入绘图模式,输入含 `x` 的表达式(默认 `sin(x)`),应用在指定 x 区间内采样求值,并在画布上绘制函数曲线,同时显示坐标轴与网格。

**目标用户**: 学生、工程师、需要直观看到函数行为的用户。
**核心价值**: 把"计算数字"升级为"理解函数"。

## 功能需求

### F1. 入口与导航

| 编号 | 描述 | 优先级 |
|------|------|--------|
| F1.1 | 主计算器页 (`CalculatorPage.ets`) 顶部工具栏新增"📈 绘图"按钮 | P0 |
| F1.2 | 点击按钮后,使用 `router.pushUrl` 跳转到 `GraphPage` | P0 |
| F1.3 | 跳转时传参 `expression`(可选):主计算器当前输入框文本;若不含 `x`,GraphPage 使用默认值 `sin(x)` | P1 |
| F1.4 | GraphPage 顶部返回按钮可回到主计算器页 | P0 |

### F2. 表达式输入与校验

| 编号 | 描述 | 优先级 |
|------|------|--------|
| F2.1 | GraphPage 顶部显示表达式输入框,支持 `+ - * / ^ % ! sin cos tan asin acos atan ln log sqrt exp abs` 与常量 `pi e`,变量 `x`(大小写不敏感) | P0 |
| F2.2 | 输入框右侧"绘制"按钮触发重新绘图 | P0 |
| F2.3 | 表达式语法错误时,在画布上方显示红色错误提示(不绘制曲线) | P0 |
| F2.4 | 表达式不含 `x` 时,显示提示"请输入含 x 的函数表达式,如 sin(x)" | P1 |
| F2.5 | 默认值:首次进入时表达式 = `sin(x)` | P0 |

### F3. 范围与采样

| 编号 | 描述 | 优先级 |
|------|------|--------|
| F3.1 | 4 个数值输入框:`xMin`、`xMax`、`samples`(默认 -2π, 2π, 200) | P0 |
| F3.2 | `xMin` 支持常量 `pi` `e` 解析(如 `-2*pi` 识别为 `-2π`) | P1 |
| F3.3 | `xMax > xMin` 校验,否则提示"xMax 必须大于 xMin" | P0 |
| F3.4 | `samples ∈ [50, 1000]` 校验,默认 200 | P0 |
| F3.5 | Y 轴范围根据采样结果自动计算(min/max + 10% 边距) | P0 |

### F4. 曲线绘制

| 编号 | 描述 | 优先级 |
|------|------|--------|
| F4.1 | 使用 ArkUI `Canvas` 组件 + `CanvasRenderingContext2D` 绘制 | P0 |
| F4.2 | 绘制内容:浅色网格(每 1 单位一格)、坐标轴(x=0 加粗黑色、y=0 加粗黑色)、刻度标签(轴上的数字)、曲线(主色,2px 描边) | P0 |
| F4.3 | 曲线颜色:与主计算器主色调一致(读取 `Preferences` 中的 `appTheme`) | P1 |
| F4.4 | 定义域外的点(NaN/Infinity)跳过,不连线,曲线在该处自然断开 | P0 |
| F4.5 | 坐标轴标签字号 10-12px,曲线粗 2px | P0 |

### F5. 状态管理

| 编号 | 描述 | 优先级 |
|------|------|--------|
| F5.1 | 绘图状态(表达式、范围、采样数)由 `GraphViewModel` 管理,与主计算器状态隔离 | P0 |
| F5.2 | 修改输入后,点"绘制"按钮才刷新(避免实时刷新导致卡顿) | P0 |
| F5.3 | 表达式与范围变化时自动重新计算采样(200 点 < 50ms,无需 loading) | P0 |
| F5.4 | 超过 500 点时显示"计算中..."(保护 UI 流畅) | P1 |

### F6. 错误处理

| 编号 | 描述 | 优先级 |
|------|------|--------|
| F6.1 | 语法错误 → 红色提示 + 不绘制 | P0 |
| F6.2 | 单点求值失败(NaN/Inf) → 该点 y=null,曲线断开 | P0 |
| F6.3 | 所有点都失败 → 画布显示"该函数在选定范围内无有效值" | P0 |
| F6.4 | Canvas 渲染异常 → 不影响主计算器,只显示 GraphPage 错误占位 | P0 |

## 非功能需求 (DFX)

### 性能 (P)

| 编号 | 描述 | 目标值 |
|------|------|--------|
| P-1 | 200 个采样点同步求值耗时 | < 50ms (中端设备) |
| P-2 | Canvas 渲染耗时 | < 100ms |
| P-3 | 页面冷启动到首帧 | < 300ms |

### 可靠性 (R) / FMEA 消减措施

| 故障模式 | 严重度 | 原因 | 改进措施 | 需求体现 |
|---------|-------|------|---------|---------|
| F1: 表达式含阶乘 `!` 在大数下溢出 | 8 (高) | 平台限制 | 绘图模块不重复实现 `!`,复用 `Expression.ets` 的现有实现(其已含数值保护) | F2.1 + 不重复实现 |
| F2: `xMax <= xMin` 导致空图 | 6 (中) | 用户输入错误 | 范围校验,提示修复 | F3.3 |
| F3: `1/0` 等除零错误未处理 | 7 (高) | 表达式求值崩溃风险 | `evaluateAt` 包装,失败返回 null | F4.4 + F6.2 |
| F4: 极值(如 `1e300`)导致 Canvas 溢出 | 5 (中) | Y 轴范围计算崩溃 | Y 轴范围限幅 [-1e10, 1e10] | F3.5 + PlotUtils 中实现 |
| F5: 空表达式导致解析失败 | 4 (低) | UI 输入校验缺失 | 提交时校验,空 → 提示 | F2.3 |
| F6: 路由参数超长(>1MB) | 3 (低) | router 限制 | 限制表达式长度 ≤ 256 字符 | F2.1 约束 |
| F7: 主题色读取失败 | 3 (低) | Preferences 未初始化 | 默认蓝色 | F4.3 降级 |

### 可维护性 (M)

- 纯函数 `PlotUtils` 单独成文件,100% 单元测试覆盖
- 表达式求值复用 `Expression.ets` 不重写
- `GraphViewModel` 与 `GraphPage` 解耦,可独立测试

### 安全性 (S)

- 不涉及网络,无数据上传
- 不涉及权限申请
- 路由参数做长度校验

### 国际化 (I)

- 错误提示字符串使用 `%string.Resource` 资源(后续 i18n 可扩展)
- 坐标轴数字使用 Locale-aware 格式化

### 可测试性 (T)

- `PlotUtils` 为纯函数,可纯单元测试
- `Expression.evaluateAt` 可纯单元测试(各种 x 值)
- UI 测试覆盖:打开绘图页 → 默认 sin(x) → 修改 → 重绘 → 错误情况

## 数据模型 (新增)

```typescript
// 新增: PlotUtils.ets
export interface PlotPoint {
  x: number;
  y: number | null;  // null 表示定义域外/求值失败
}

export interface PlotSeries {
  points: PlotPoint[];
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
}

export interface PlotBounds {
  width: number;
  height: number;
  paddingLeft: number;
  paddingRight: number;
  paddingTop: number;
  paddingBottom: number;
}

// 新增: GraphViewModel 中定义
@Observed
export class GraphViewModel {
  expression: string = 'sin(x)';
  xMin: number = -2 * Math.PI;
  xMax: number = 2 * Math.PI;
  samples: number = 200;
  series: PlotSeries | null = null;
  errorMessage: string = '';
  isComputing: boolean = false;
}
```

## 接口变更

### Expression.ets (扩展,不破坏)

```typescript
// 新增方法 (在现有 Expression 类中)
static evaluateAt(expr: string, x: number): number | null {
  // 复用现有 SolvePostfix(expr, x.toString()) 求值
  // 成功返回 number,失败(NaN/Infinity)返回 null
  // 内部不抛异常,所有错误转为 null
}
```

### 新增 PlotUtils.ets

```typescript
export class PlotUtils {
  // 采样
  static sampleSeries(expression: string, xMin: number, xMax: number, samples: number, evaluator: (expr: string, x: number) => number | null): PlotSeries;
  // 坐标变换
  static mapToCanvas(p: PlotPoint, bounds: PlotBounds, xMin: number, xMax: number, yMin: number, yMax: number): { px: number; py: number } | null;
  // Y 轴范围
  static computeYRange(points: PlotPoint[]): { yMin: number; yMax: number };
  // 解析带常量的数字字符串 (支持 pi/e)
  static parseRange(str: string): number | null;
}
```

## 兼容性

- **主计算器页**: 新增按钮 + 路由跳转,不修改现有计算逻辑
- **表达式引擎**: 扩展不破坏(新增 `evaluateAt`,原方法保留)
- **历史记录**: 不变(绘图结果不入历史)
- **设置/偏好**: 复用 `appTheme` 主色(已存在),不新增设置项

## 范围外 (本次不做)

- 多函数同图(架构预留 `PlotSeries[]`,UI 仅渲染第 0 条)
- 手势缩放/平移视图
- 极坐标图、参数方程、3D 图
- 图像保存/分享
- 函数历史收藏

## 验收标准 (验收用例)

### AC-1: 打开绘图页
- **Given**: 用户在主计算器页
- **When**: 点击"📈 绘图"按钮
- **Then**: 进入 GraphPage,表达式 = `sin(x)`,看到正弦曲线 + 坐标轴

### AC-2: 修改表达式
- **Given**: 绘图页打开,表达式 = `sin(x)`
- **When**: 修改为 `x^2`,点"绘制"
- **Then**: 看到抛物线

### AC-3: 修改 x 范围
- **Given**: 表达式 = `sin(x)`, x ∈ [-2π, 2π]
- **When**: 设置 xMin = 0, xMax = 4*pi
- **Then**: 只看到 0 到 4π 之间的正弦曲线

### AC-4: 语法错误
- **Given**: 绘图页打开
- **When**: 输入 `sin(x`,点"绘制"
- **Then**: 红色错误提示"表达式语法错误",不绘制曲线

### AC-5: 无 x 变量
- **Given**: 绘图页打开
- **When**: 输入 `1+2`,点"绘制"
- **Then**: 提示"请输入含 x 的函数表达式"

### AC-6: 定义域外断开
- **Given**: 表达式 = `log(x)`, x ∈ [-5, 5]
- **When**: 绘制
- **Then**: x ≤ 0 区域无曲线(断开),x > 0 显示对数曲线

### AC-7: 全部无效
- **Given**: 表达式 = `1/0`
- **When**: 绘制
- **Then**: 画布显示"该函数在选定范围内无有效值"

### AC-8: xMax ≤ xMin
- **Given**: 绘图页打开
- **When**: 设置 xMin = 5, xMax = 1
- **Then**: 提示"xMax 必须大于 xMin",不绘制

## 可靠性分析结果 (FMEA 消减措施清单)

| 编号 | 故障模式 | 改进措施 | 需求编号 | 状态 |
|------|---------|---------|---------|------|
| FMEA-1 | 阶乘大数溢出 | 复用现有 Expression 限制 | F2.1 | 已纳入 |
| FMEA-2 | xMax ≤ xMin | 输入校验 | F3.3 | 已纳入 |
| FMEA-3 | 除零崩溃 | evaluateAt 返回 null | F4.4 | 已纳入 |
| FMEA-4 | 极值 Canvas 溢出 | Y 轴限幅 | F3.5 | 已纳入 |
| FMEA-5 | 空表达式 | 输入校验 | F2.3 | 已纳入 |
| FMEA-6 | 路由参数超长 | 长度限制 | F2.1 | 已纳入 |
| FMEA-7 | 主题色读取失败 | 默认值降级 | F4.3 | 已纳入 |

## 关联文档
- info.md: 代码仓理解与可复用组件清单
- delta-design.md: 组件与接口设计
- design-review.md: 设计审视报告

## 不涉及章节
- 平台迁移相关: 不涉及
- 权限相关: 不涉及(无新权限)
- 后台任务: 不涉及
- 数据持久化: 不涉及(状态仅内存)
