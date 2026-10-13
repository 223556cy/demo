# 程序员模式 — 开发任务

## 任务概述

- **功能名称**: 程序员模式 (DEC/BIN/OCT/HEX 互转 + 位运算 + 位宽/符号)
- **变更类型**: requirement-add
- **关联变更**: specs/changes/20260612-requirement-programmer-mode/
- **关联 Spec**: proposal.md / delta-spec.md / info.md / delta-design.md
- **开发阶段**: TDD (RED → GREEN → REFACTOR) + 增量实现
- **预计任务数**: 14
- **目标粒度**: XS-S
- **复杂度**: M（中等）

## 任务列表

### 阶段 0：测试基础设施（基线已具备）

#### Task 0.1: 验证 test sourceSet 与 hypium 可用
**描述**: 验证 `entry/src/test/ets/` 目录存在，hypium 框架可用。基线 Issue #9 已建立。
**涉及文件**:
- `opencalc/entry/src/test/ets/calculator/Expression.test.ets`（基线已存在）
**依赖任务**: 无
**验收标准**:
- `hvigorw test` 命令可用
- 现有 percent 测试用例能跑

---

### 阶段 1：数据模型扩展

#### Task 1.1: Models.ets 新增 4 个枚举（CalculatorMode / Base / BitWidth / Signedness）
**描述**: 在 `model/Models.ets` 中新增 4 个枚举类型
- `CalculatorMode`: BASIC, SCIENTIFIC, PROGRAMMER
- `Base`: BIN=2, OCT=8, DEC=10, HEX=16
- `BitWidth`: B8=8, B16=16, B32=32, B64=64
- `Signedness`: SIGNED, UNSIGNED
**涉及文件**:
- `opencalc/entry/src/main/ets/model/Models.ets`（修改）
**依赖任务**: 无
**验收标准**:
- 4 个枚举声明完整
- 编译通过
- 不影响现有 DEFAULT_PREFERENCES 字段

#### Task 1.2: CalculatorPreferences 接口扩展 4 字段 + DEFAULT_PREFERENCES
**描述**: 扩展 `CalculatorPreferences` interface 新增 4 字段：
- `programmerModeEnabled: boolean`
- `programmerActiveBase: number`
- `programmerBitWidth: number`
- `programmerSignedness: number`
并在 `DEFAULT_PREFERENCES` 加默认值
**涉及文件**:
- `opencalc/entry/src/main/ets/model/Models.ets`（修改）
**依赖任务**: Task 1.1
**验收标准**:
- 老 JSON（无新字段）反序列化时使用默认值
- 编译通过

#### Task 1.3: PreferencesStore 加 4 个 getter/setter + 扩展 getAllPreferences
**描述**: 在 `preferences/PreferencesStore.ets` 中：
- 新增 `getProgrammerModeEnabled/setProgrammerModeEnabled`
- 新增 `getProgrammerActiveBase/setProgrammerActiveBase`
- 新增 `getProgrammerBitWidth/setProgrammerBitWidth`
- 新增 `getProgrammerSignedness/setProgrammerSignedness`
- 扩展 `getAllPreferences()` 返回 4 字段
**涉及文件**:
- `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets`（修改）
**依赖任务**: Task 1.2
**验收标准**:
- 4 个 getter/setter 实现风格与现有方法一致
- `getAllPreferences` 返回类型不破坏调用方
- 编译通过

---

### 阶段 2：BaseConverter 纯函数模块（TDD：先 RED 后 GREEN）

#### Task 2.1: 写 BaseConverter 单元测试 (RED)
**描述**: 在 `entry/src/test/ets/calculator/BaseConverter.test.ets` 写 32 项测试用例（覆盖 toBase/fromBase/format4Bases/isValidCharForBase），先全部写出来，**先不实现 BaseConverter**
**涉及文件**:
- `opencalc/entry/src/test/ets/calculator/BaseConverter.test.ets`（新增）
**依赖任务**: Task 0.1
**验收标准**:
- 测试文件语法合法
- 跑测试时**如实记录**全部 FAIL（因为 BaseConverter 不存在）
- 写入 apply-report.md RED 阶段

#### Task 2.2: 实现 BaseConverter.ets (GREEN)
**描述**: 实现 `calculator/BaseConverter.ets`：
- 4 个枚举从 Models 导入（或本文件再导出）
- `BaseConverter.toBase(value, base, bitWidth, signed): string`
- `BaseConverter.fromBase(text, base): number`
- `BaseConverter.format4Bases(value, bitWidth, signed): string[]`
- `BaseConverter.isValidCharForBase(ch, base): boolean`
**涉及文件**:
- `opencalc/entry/src/main/ets/calculator/BaseConverter.ets`（新增）
**依赖任务**: Task 2.1
**验收标准**:
- 32 项测试全部 PASS
- 边界用例：8 位截断、signed/unsigned 切换、HEX 解析带/不带前缀
- 64 位 BigInt 降级处理（typeof 检测）

#### Task 2.3: BaseConverter REFACTOR（可选）
**描述**: 检查 toBase/fromBase 是否有可抽取的公共模式（如 mask 计算、prefix 拼接），如有则抽取
**涉及文件**:
- `opencalc/entry/src/main/ets/calculator/BaseConverter.ets`（可能微调）
**依赖任务**: Task 2.2
**验收标准**:
- 32 项测试仍 PASS
- 无新行为
- 命名/注释改善

---

### 阶段 3：表达式引擎扩展（位运算）

#### Task 3.1: CalcEngine 识别 band/bor/bxor/bnot/shl/shr 函数
**描述**: 在 `calculator/Calculator.ets` 的 `parseFactor()` 中增加对以下函数名的识别：
- `band(a,b)`, `bor(a,b)`, `bxor(a,b)`, `bnot(x)`
- `shl(a,n)`, `shr(a,n)`
函数实现：
- band/bor/bxor：JS `&` `|` `^` 即可（number 类型，32 位内精确）
- bnot：JS `~`
- shl/shr：JS `<<` `>>`
**涉及文件**:
- `opencalc/entry/src/main/ets/calculator/Calculator.ets`（修改）
**依赖任务**: 无（独立于 UI）
**验收标准**:
- 现有科学函数（sin/cos/ln/log/factorial）不受影响
- band/bor/bxor/bnot/shl/shr 6 个函数可被 evaluate 解析

#### Task 3.2: Expression 预处理位运算符号（程序员模式独占）
**描述**: 在 `calculator/Expression.ets` 的 `replaceSymbols()` 中增加：
- 仅当 `mode === CalculatorMode.PROGRAMMER` 时替换
- `&` → ` band( `，`|` → ` bor( `，`^` → ` bxor( `
- `<<` → ` shl( `，`>>` → ` shr( `
- `~x` → `bnot(x)`（一元，处理负号后）
**涉及文件**:
- `opencalc/entry/src/main/ets/calculator/Expression.ets`（修改）
**依赖任务**: Task 3.1
**验收标准**:
- 基础/科学模式下不替换 `&|^~`（保持原行为）
- 程序员模式下 `5 & 3` 表达式预处理后含 `band`

#### Task 3.3: Expression 单元测试（位运算用例）
**描述**: 在 `Expression.test.ets` 中新增 5 项用例：
- `band(5,3) === 1`
- `bor(5,3) === 7`
- `bxor(5,3) === 6`
- `bnot(0) === -1`
- `shl(1,4) === 16`
- `shr(16,4) === 1`
**涉及文件**:
- `opencalc/entry/src/test/ets/calculator/Expression.test.ets`（修改，扩展）
**依赖任务**: Task 3.2
**验收标准**:
- 6 个新用例全部 PASS
- 老用例仍 PASS

---

### 阶段 4：UI 集成

#### Task 4.1: CalculatorPage 顶部 Tab 切换（3 Tab）
**描述**: 在 `pages/CalculatorPage.ets` 的 `ToggleRow` 改为 3 Tab（基础/科学/程序员），点击切换 `mode: CalculatorMode`
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 1.1
**验收标准**:
- 3 Tab 视觉清晰，当前 mode 高亮
- 点击切换立即生效
- 编译通过

#### Task 4.2: CalculatorPage 加 5 个新 @State + 加载逻辑
**描述**: 在 `CalculatorPage` 加：
- `@State mode: CalculatorMode`
- `@State activeBase: Base`
- `@State bitWidth: BitWidth`
- `@State signedness: Signedness`
- `@State programmerDisplay: string[]`
并在 `aboutToAppear`/`loadPrefs` 中恢复 4 字段
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 1.3
**验收标准**:
- 启动时 4 字段从 Preferences 恢复
- 状态变化时自动 savePref

#### Task 4.3: DisplayPanel 扩展 4 进制显示（程序员模式独占）
**描述**: 在 `DisplayPanel` 内，当 `mode === PROGRAMMER` 时多渲染 4 行：
- DEC: xxxx
- BIN: 0bxxxxxxxx
- OCT: 0oxxx
- HEX: 0xFF
每行 14 号字 + 灰底
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 4.2
**验收标准**:
- 基础/科学模式不渲染 4 行
- 程序员模式 4 行同步显示

#### Task 4.4: 程序员键盘布局（BtnA/BtnB/.../BtnF + 位运算）
**描述**: 在 `ButtonGrid()` 内，当 `mode === PROGRAMMER` 时渲染：
- 顶部行：当前激活进制 Tab 4 个 + 位宽/符号选择
- 数字与字母混合区：A-F 按钮
- 位运算按钮：&、|、^、~、<<、>>
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 4.3
**验收标准**:
- 键盘布局清晰，按钮可点
- 小数点按钮在程序员模式下隐藏或禁用
- 模式切换键盘整体更换

#### Task 4.5: 进制 Tab 切换逻辑
**描述**: 实现 `onBaseChange(base: Base)`：
- 更新 `activeBase`
- 持久化 `programmerActiveBase`
- 输入校验：`onDigit` 中检查 `isValidCharForBase`
- onEquals 后用 `format4Bases` 刷新 4 行
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 4.4
**验收标准**:
- 切换后 4 行全部同步
- DEC 模式输入 A 弹 toast

#### Task 4.6: 浮点截断（输入层）
**描述**: 在 `onDigit` 与 `onEquals` 中，对结果 `Math.trunc`
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 4.5
**验收标准**:
- 程序员模式下，输入 1.5 表达式求值后只取整数
- 基础/科学模式不受影响

#### Task 4.7: onEquals 扩展（程序员模式分支）
**描述**: 在 `onEquals()` 中，当 `mode === PROGRAMMER` 时：
- 表达式预处理走 Expression（启用位运算）
- evaluate 后取 Math.trunc
- 调用 `BaseConverter.format4Bases` 填充 4 行
- 错误处理走 ErrorFlags
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 4.6
**验收标准**:
- 4 行显示与 onEquals 结果一致
- 错误状态正常显示

---

### 阶段 5：集成验证

#### Task 5.1: 全量构建
**描述**: 跑 `hvigorw clean && hvigorw build`，确认 0 编译错误
**涉及文件**: 无
**依赖任务**: Task 4.7
**验收标准**:
- 编译退出码 0
- stdout / stderr 关键片段写入 apply-report.md

#### Task 5.2: 全量单元测试
**描述**: 跑 `hvigorw test`，确认所有用例 PASS（含基线 percent 用例 + 32 项 BaseConverter + 6 项 Expression 扩展）
**涉及文件**: 无
**依赖任务**: Task 5.1
**验收标准**:
- 测试退出码 0
- 总用例数 ≥ 38
- PASS 比例 100%

#### Task 5.3: 产出 apply-report.md
**描述**: 记录全过程：
- Task 2.1 RED 输出（伪造禁止）
- Task 2.2 GREEN 输出
- Task 5.1 构建输出
- Task 5.2 测试输出
- 回归保护证据
**涉及文件**:
- `specs/changes/20260612-requirement-programmer-mode/apply-report.md`（新增）
**依赖任务**: Task 5.2
**验收标准**:
- 4 段齐全：RED / GREEN / 构建 / 测试
- 每段真实命令 + 真实输出
- 不准伪造

---

## 开发顺序

```
Task 0.1（验证测试环境）
   ↓
Task 1.1（枚举）→ Task 1.2（接口）→ Task 1.3（PreferencesStore）
                                              ↓
                  Task 2.1（RED 测试）→ Task 2.2（GREEN 实现）→ Task 2.3（REFACTOR）
                                              ↓
                  Task 3.1（CalcEngine 函数）→ Task 3.2（Expression 符号）→ Task 3.3（Expression 测试）
                                              ↓
                  Task 4.1（Tab）→ Task 4.2（@State）→ Task 4.3（DisplayPanel）→ Task 4.4（键盘）→ Task 4.5（进制切换）→ Task 4.6（截断）→ Task 4.7（onEquals）
                                              ↓
                              Task 5.1（构建）→ Task 5.2（测试）→ Task 5.3（apply-report）
```

**关键路径**：1.1 → 1.2 → 1.3 → 2.1 → 2.2 → 4.2 → 4.3 → 4.4 → 4.5 → 4.7 → 5.1 → 5.2 → 5.3
**并行机会**：Task 3.1-3.3（CalcEngine + Expression）可与 Task 4.1-4.2（UI 起始）并行
**风险点**：Task 4.4（键盘布局）可能因横屏 4 列容纳不下所有位运算按钮而需要二次设计

---

## 验收计划

| 任务 | 验收方式 | 验收时间 |
| --- | --- | --- |
| Task 1.1-1.3 | 编译通过 + 4 字段 JSON 兼容 | 阶段 1 末 |
| Task 2.1 | RED 输出全部 FAIL | 阶段 2 起步 |
| Task 2.2 | 32 项测试 PASS | 阶段 2 完成 |
| Task 3.1-3.3 | 6 项新测试 PASS | 阶段 3 完成 |
| Task 4.1-4.7 | UI 手动 + onEquals 集成 | 阶段 4 完成 |
| Task 5.1 | `hvigorw build` 退出码 0 | 阶段 5 起步 |
| Task 5.2 | `hvigorw test` 全 PASS | 阶段 5 中段 |
| Task 5.3 | apply-report.md 完整 | 阶段 5 末 |

---

## 依赖关系图

```
       0.1
        │
        ▼
  ┌──── 1.1 ──── 1.2 ──── 1.3 ────────┐
  │                                   │
  │     ┌── 2.1 ── 2.2 ── 2.3         │
  │     │                            │
  │     └── 3.1 ── 3.2 ── 3.3        │
  │                                  │
  └─ 4.1 ── 4.2 ── 4.3 ── 4.4 ── 4.5 ── 4.6 ── 4.7
                                              │
                                              ▼
                                       5.1 ── 5.2 ── 5.3
```

---

> 本文档由 aid-implementing skill 生成。
> 生成时间：2026-06-12
