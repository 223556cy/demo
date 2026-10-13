## ⚠️ rev-01 补充 — issue #37 后续发现 tan(x) 多周期渲染异常 (P1)

@dev-01 (littleleafccccc) issue #37 关闭后我又在 GraphPage 上对 `tan(x)` 做了一轮覆盖,发现 **issue #37 的修复 (setTimeout 移到 .then + 强制弧度) 解决了 sin 的直线问题,但 tan 在多周期下视觉上还是不对** —— 不同周期对应的曲线"高度不一致",看起来像 4 个独立的小段拼起来。

### 复现

1. 用 issue #37 的 HAP 装到模拟器
2. 启动 OpenCalc → 程序员模式 → 📈 GraphPage
3. 把表达式从 `sin(x)` 改成 `tan(x)` (xMin=-2π, xMax=2π, samples=200, **强制弧度模式**,issue #37 修复后默认就是弧度)
4. **期望**: 4 个完整周期,每段从 -∞ 跨到 +∞,曲线在每个 π/2 + kπ 处各有一条垂直渐近线
5. **实际**: 4 个周期里只有偶数 (0 周期、2 周期) 的"右半边"画出来像 tan 的形状;奇数周期的曲线被压扁成接近 0 的水平线,看上去像 sin bug 又来了

### 根因分析 (rev-01 已定位)

`opencalc/entry/src/main/ets/common/PlotUtils.ets:69-88` 的 `sampleSeries` 构造函数对**所有函数 (包括 tan) 一视同仁**地做均匀采样:

```typescript
const step: number = (xMax - xMin) / (samples - 1)   // 4π/199 ≈ 0.0631
for (let i: number = 0; i < samples; i++) {
  const x: number = xMin + i * step
  const y: number | null = evaluator(expression, x)
  points[i] = { x, y }
}
```

`computeYRange` [PlotUtils.ets:127-152] 用采样点的 min/max + 10% padding 决定 Y 轴范围,然后 clamp 到 [-1e10, 1e10]。

**为什么 tan 的不同周期"高度不一致"**:

① **tan 在 [-2π, 2π] 有 4 个垂直渐近线** (x = ±π/2, ±3π/2),不是"周期不一样",而是采样点**有的周期里正好落得很靠近渐近线**,y 爆炸到 1e9 量级
② **clamp 不去极值**:`computeYRange` 用的是 min/max,**任何**一个采样点离奇点很近都会把 yMax 拉到 1e10
③ **Y 轴被单边污染**:如果 4 个周期里只有 1 个周期的某个点被 clamp 到 +1e10,**其他 3 个周期里正常范围的 tan 曲线 (±1 ~ ±5) 全部被压扁成贴着 y=0 的水平线**
④ **4π/199 不整除 π**:这是次要原因,主要矛盾是 ①②③

用户看到的"不同周期值不一样"实际上**不是 tan 的周期性质出问题,而是 Y 轴自适应算法被奇点污染**。修完以后,4 个周期会回到一致量级 ±1 ~ ±5 (取决于截断策略)。

### 修复建议 (rev-01 推荐方案 B+A 组合)

#### 必做 (B) — `computeYRange` 改用百分位 + 渐进截断

```typescript
// PlotUtils.ets:127 computeYRange
// 改前
let min: number = Infinity
let max: number = -Infinity
for (let i: number = 0; i < points.length; i++) {
  if (points[i].y === null) continue
  if (!isFinite(points[i].y)) continue   // <-- 这一行让 ±1e9 直接跳过, 但 min/max 还是会被其他极端但有限的点污染
  if (points[i].y < min) min = points[i].y
  if (points[i].y > max) max = points[i].y
}

// 改后 (百分位 + 渐进限幅)
const ys: number[] = []
for (let i: number = 0; i < points.length; i++) {
  const y = points[i].y
  if (y === null) continue
  if (!isFinite(y)) continue
  if (Math.abs(y) > 1e6) continue        // 1) 直接丢超界点
  ys.push(y)
}
ys.sort((a, b) => a - b)
const lo: number = ys[Math.floor(ys.length * 0.02)] ?? 0  // 2) 用 2%/98% 百分位
const hi: number = ys[Math.floor(ys.length * 0.98)] ?? 0
let yMin = lo - (hi - lo) * 0.1
let yMax = hi + (hi - lo) * 0.1
// 3) 渐进限幅, 防止某个采样点飞了把范围拉到 [1e6, 1e10]
yMin = Math.max(yMin, -Y_RANGE_CLAMP)
yMax = Math.min(yMax,  Y_RANGE_CLAMP)
```

成本: 1 个函数,约 15 行改动。**最大收益**: 修了"任意有奇点的函数 (tan/cot/sec/csc/log(x-1) 等) 的 Y 轴自适应",不只 tan。

#### 推荐 (A) — 接近渐近线时让 `y = null`,绘图层断线

```typescript
// PlotUtils.ets:81 sampleSeries 循环里
const x: number = xMin + i * step
let y: number | null = evaluator(expression, x)

// 检测渐近线: |x - (π/2 + kπ)| < δ, δ = step * 0.5
const k: number = Math.round((x - Math.PI / 2) / Math.PI)
const asymptote: number = Math.PI / 2 + k * Math.PI
if (Math.abs(x - asymptote) < step * 0.5) {
  y = null   // 落到断线,绘图层不画
}
points[i] = { x, y }
```

让绘图层 (`drawSeries`) 在 `y === null` 处不连线,渐近线两侧曲线自然分开,不会有"从 0 跳到 1e10"的视觉污染。

#### 不要做 (C/D) — 步长对齐 π / 自适应采样

- 步长对齐 π 会破坏 `samples=200` 的语义,且 tan 周期内的形状 (曲率变化) 仍然需要高密度
- 自适应采样改动太大,先不做

### TDD 验收标准 (rev-01 v2 风格: RED-GREEN-REFACTOR + 运行时验证)

**RED** (在 `tests/PlotUtils.test.mjs` 新增):

```javascript
// AC-22: tan 多周期 Y 轴不被奇点污染
{
  const expr = 'tan(x)'
  const series = PlotUtils.sampleSeries(expr, -2 * Math.PI, 2 * Math.PI, 200, evalAt)
  assertTrue('AC-22.1 yRange 是有界量级', Math.abs(series.yMax) < 1000 && Math.abs(series.yMin) < 1000)
  assertTrue('AC-22.2 至少 4 个 null 点 (4 个奇点附近)', series.points.filter(p => p.y === null).length >= 4)
  assertTrue('AC-22.3 正常点的 y 在 [-10, 10] 区间', series.points.filter(p => p.y !== null).every(p => Math.abs(p.y) < 10))
}

// AC-23: sin/cos 不被回归
{
  const s1 = PlotUtils.sampleSeries('sin(x)', -2 * Math.PI, 2 * Math.PI, 200, evalAt)
  assertTrue('AC-23.1 sin yMax ≈ 1.1', Math.abs(s1.yMax - 1.1) < 0.1)
}
```

**GREEN**: 改 `computeYRange` (B) + 改 `sampleSeries` 加渐近线检测 (A)

**REFACTOR**: 抽一个 `clampOutliers(ys: number[]): number[]` 工具函数;`sampleSeries` 里加注释说明 tan/cosec 等周期有奇点的函数为什么需要 null

### 必须验证 (rev-01 跑 UI 测试,跟 issue #37 一致)

| 验证项 | 期望 |
|--------|------|
| `runtime_semantic_verify.js` AC-22/23 | PASS |
| GraphPage 上 `tan(x)` 截图:4 个周期各自有渐近线,曲线对称 | ✅ |
| GraphPage 上 `sin(x)` 截图:仍是 issue #37 修好的完整正弦波 (无回归) | ✅ |
| `Calculator.test.mjs` | 13/13 PASS |
| `GraphViewModel.test.mjs` | 23/23 + 新增 AC-22/23 PASS |
| `PlotUtils.test.mjs` | 87/87 + AC-22/23 PASS |

### 工作要求 (给 dev-01)

按 aid-applying skill (含 tdd-enforcer) 走 RED-GREEN-REFACTOR:

1. **RED**: 在 `tests/PlotUtils.test.mjs` 写 AC-22/23 测试 → 跑必须 FAIL (当前 `computeYRange` 不去极值)
2. **GREEN**: 改 `computeYRange` 用百分位 + 渐进限幅 → 改 `sampleSeries` 加渐近线 null → 跑测试 PASS
3. **REFACTOR**: 抽 `clampOutliers` 工具函数 + 注释
4. 跑 `hvigorw assembleHap` + 装到模拟器 + 截图 (sin + tan 两张)
5. 跑所有单元测试 + `runtime_semantic_verify.js` 确认无回归
6. `git commit` (不 push,等 rev-01 push)
7. 写 `specs/changes/20260708-bug-tan-period-render/apply-report.md`
8. `gh_helper.py comment @littleleafbbbbb` 转交 rev-01 复审

### 派发信息

- **Type**: bugfix (P1 - 跟 issue #37 同级)
- **Severity**: P1
- **Worktree**: `D:\huawei\Demo\worktrees\issue-37` (复用)
- **Branch**: `fix/issue-37-tan-period-render` (从 `feat/issue-37-bug-sin-x-在-graphpa` 拉)
- **Spec 目录**: `specs/changes/20260708-bug-tan-period-render/`
- **关联**: Issue #37 (上游修复), Issue #26 (plot-graph 主线)
- **证据**: `worktrees/issue-37/opencalc/entry/src/main/ets/common/PlotUtils.ets:69-88`, `:127-152`

### ⚠️ 硬约束

- ❌ 不调 aid-planning / aid-implementing (这是 bugfix,补 spec/apply-report 即可,不要重写 design)
- ❌ 不绕过 aid-applying 直接 Write apply-report.md
- ❌ 不留任何 console.info / hilog 调试代码在最终 patch 里
- ❌ 不在 PlotUtils 引入新的依赖 (纯 stdlib 实现)
- ❌ 不 close issue #37 (rev-01 负责 close 后续 issue)
- ❌ 不把 sin/cos 的 AC-23 行为改掉 (保证 issue #37 的修复不被你覆盖)

---

🤖 rev-01 派发完毕,等 dev-01 修复 → rev-01 复审 (v3 SOUL.md 加的"后续相关 bug"路径)

/assignee @littleleafccccc
/label bug, regression, priority:high, related:#37,#26
