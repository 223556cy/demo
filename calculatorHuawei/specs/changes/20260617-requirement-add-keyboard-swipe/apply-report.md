# 应用报告 — Issue #29 竖屏手势滑动切换三种键盘模式

## 应用信息

- **变更类型**: requirement-add
- **变更名称**: 键盘滑动 (中等模糊)
- **关联特性**: feat-issue-29-keyboard-swipe
- **应用日期**: 2026-06-18
- **工作目录**: `D:\huawei\Demo\worktrees\issue-29`
- **分支**: `feat/issue-29-中等模糊`
- **关联 Issue**: #29

## 代码完成情况

| 任务 | 状态 | 完成时间 | 备注 |
|------|------|----------|------|
| Task 1.1 Models.ets 扩展 | ✅ 完成 | 2026-06-18 | `KeyboardMode` 枚举 + `programmerModeDefault` 字段 |
| Task 1.2 PreferencesStore.ets 扩展 | ✅ 完成 | 2026-06-18 | `getProgrammerModeDefault` / `setProgrammerModeDefault` |
| Task 1.3 string.json 扩展 | ✅ 完成 | 2026-06-18 | 13 个新字符串 (mode_*/base_*/op_*) |
| Task 2.1 currentMode 状态与控制器 | ✅ 完成 | 2026-06-18 | `@State currentMode` + `SwiperController` |
| Task 2.2 modeController 状态机 | ✅ 完成 | 2026-06-18 | `cycleMode` / `onSwiperChange` 互斥写 |
| Task 2.3 ~ 2.5 UI Swiper 改造 | ✅ 完成 | 2026-06-18 | BasicGrid / ScientificGrid / ProgrammerGrid |
| Task 5.x 测试套件 | ✅ 完成 | 2026-06-18 | 28 个单元测试 (8 describe blocks) |
| Task 6.x 提交准备 | ✅ 完成 | 2026-06-18 | git commit (本动作) |

## 测试结果

### 单元测试 (hvigorw --no-daemon test)

- **Tests run**: 99
- **Pass**: 98
- **Failure**: 1 (见下方"已知遗留问题")
- **Error**: 0
- **Ignore**: 0
- **总体结论**: ✅ 通过 (本 issue 新增 28 个测试全部通过)

#### 本次新增测试 (Issue #29) — 全部通过 ✅

| Class | Tests | Pass |
|-------|-------|------|
| `KeyboardMode_enum_values` | 3 | 3 |
| `isValidModeIndex` | 5 | 5 |
| `nextMode_three_state_cycle` | 3 | 3 |
| `cycleMode_helper` | 3 | 3 |
| `applySwiperIndex_legal_range` | 3 | 3 |
| `applySwiperIndex_out_of_range_returns_null` | 3 | 3 |
| `resolveStartupMode_priority` | 6 | 6 |
| `KeyboardMode_preferences_default` | 2 | 2 |
| **小计** | **28** | **28 (100%)** |

#### 回归测试 (本 issue 之前已有) — 70/71 通过

- `Expression_getPercentString_macOS`: 14 tests, 13 pass
- `ErrorFlags_reset_on_recovery`: 1 test, 1 pass
- `UnitConverter_*` (5 classes): 25 tests, 25 pass
- `NaturalLanguageParser_*` (3 classes): 31 tests, 31 pass

### UI 自动化测试 (harmonyos-ui-test) — ⚠️ 环境受限,无法产出截图

**阻塞原因 (capabilities.json 与实际环境不一致)**:
- `.claude/capabilities.json` 标注 `ui_test.available: true` 且 `emulator_status: running`,但本 worktree 实际执行发现:
  - `hdc list targets` 返回 `[Empty]`,无任何已连接设备
  - `hdc tconn 127.0.0.1:5555` / `127.0.0.1:5554` 失败 (`[Fail]Connect failed`)
  - `hdc list targets -v` 显示 `127.0.0.1:5554/5555` 状态为 `TCP Offline`,`COM3/COM4` 为 `UART Ready` 但 `hdc -t COM3 shell echo hello` 报 `[Fail][E001005] Device not found or connected` (stale 条目)
  - `D:/Program Files/Huawei/DevEco Studio/tools/emulator/Emulator.exe` 启动需 AVD, 系统 `C:/Users/26909` 下 `find -name hvd.xml` 无结果, 没有任何可用 AVD
  - 整个 DevEco SDK 下也未发现已部署的 AVD 文件
- **结论**: capabilities.json 中的 `emulator_status: running` 是 **stale 状态**,并非真实运行;本机当前无任何可用的 HarmonyOS 设备/模拟器

**替代验证 (非 UI dump,纯静态/逻辑层)**:
| 维度 | 验证方式 | 结果 |
|------|----------|------|
| Swiper 三页构建 | 28 个 `KeyboardSwipe` 单元测试覆盖 `nextMode` / `cycleMode` / `applySwiperIndex` (含合法/越界) | ✅ 28/28 通过 |
| 模式状态机 | `ModeController.ets` 纯函数抽离, 3 个 `KeyboardMode` 枚举值, 6 个 `resolveStartupMode` 启动优先级测试 | ✅ 6/6 通过 |
| onSwiperChange 单一可信源 | `CalculatorPage.ets` 中 `onSwiperChange` 同步 `currentMode` / `scientific` / preferences, 互斥写避免双开 | ✅ 设计 + 单元测试覆盖 |
| 横屏分支不受影响 | `isLandscape` 分支仍走 `LandscapeGrid`, 不渲染 Swiper (代码 Review 已确认) | ✅ |
| Lint / 编译 | `hvigorw --no-daemon assembleHap` | ✅ BUILD SUCCESSFUL |

**缺口与请求**:
- 缺三页 (基础/科学/程序员) 的实际 UI 截图与 uiautomator dump
- **请 dev-01 / 人类协助**:
  - 选项 A: 在有可用 HarmonyOS 设备/模拟器的环境(如 CI runner 或本地 DevEco Studio)上重跑 `harmonyos-ui-test` skill,补齐三页切换截图 + dump
  - 选项 B: 确认本机 emulator 长期不可用,更新 `.claude/capabilities.json` 的 `ui_test.emulator_status` 为 `unavailable` 或 `stale`,并在本 PR 描述中说明此限制已与 dev-01 沟通
- 在此之前,本次 re-dispatch 诚实标注此缺口,不伪造截图/uiautomator dump 输出 (符合铁律 7)

### Lint / ArkTS 编译检查 (hvigorw --no-daemon assembleHap)

- **结果**: ✅ BUILD SUCCESSFUL
- **Warnings**: 4 个全部是 deprecation 警告 (pre-existing `showToast` API, READ_PASTEBOARD 权限提示),与本 issue 无关
- **Errors**: 0

### 已知遗留问题 (非本 issue 引入)

#### 1. `AC-11_should_handle_nested_parens_percent` 测试失败

- **位置**: `opencalc/entry/src/test/ets/calculator/Expression.test.ets:85`
- **引入方**: Issue #9 / Issue #21 (百分号按钮功能),非本 issue (#29)
- **原因**: `100+(200*50/100)` 应等于 `100+(200*(50/100))` — 预期表达式的括号解析行为差异
- **影响**: 仅影响 Issue #9 的边界用例;本 issue 的所有 28 个测试全绿
- **处理建议**: 由后续 issue 处理 (例如 Issue #30~ 表达式解析优化);不在本 PR 修复范围

## 测试详情

### TDD RED-GREEN-REFACTOR 循环

| 阶段 | 行为 | 验证 |
|------|------|------|
| RED | 写 28 个失败测试 (`KeyboardSwipe.test.ets`) | ✅ 测试覆盖 KeyboardMode 枚举、index 校验、cycle/next 转换、Swiper 回调、启动优先级、preferences 默认值 |
| GREEN | 写 `ModeController.ets` 纯函数状态机 | ✅ 28/28 通过 |
| REFACTOR | 命名统一 + 别名 (cycleMode = nextMode) | ✅ 测试仍绿 |

### 关键设计决策

1. **状态机抽离为纯函数**: `ModeController.ets` 不依赖 UI/Preferences,可在 hypium 中独立单测
2. **Swiper onChange 是单一可信源**: `onSwiperChange(idx)` 兜底同步 `currentMode` / `scientific` / preferences;模式按钮和手势滑动都走这条路
3. **互斥写**: `onSwiperChange` 一次只写 `scientific` 或 `programmer` 中一个为 1,避免双开
4. **启动优先级**: `SCIENTIFIC > PROGRAMMER > BASIC`,沿用旧 `scientificModeDefault` 字段语义
5. **横屏保留旧布局**: `isLandscape` 分支仍走 `LandscapeGrid`,不渲染 Swiper,科学模式切换不受影响

## 代码改动清单

### 新增文件
- `opencalc/entry/src/main/ets/model/ModeController.ets` (76 行)
- `opencalc/entry/src/test/ets/keyboard/KeyboardSwipe.test.ets` (~165 行,28 个测试)

### 修改文件
- `opencalc/entry/src/main/ets/model/Models.ets` (+3 行: `programmerModeDefault` 字段 + 默认值)
- `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets` (+18 行: get/set/getAllPreferences)
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (+~110 行: KeyboardMode 引入、currentMode 状态、Swiper 包裹、3 个 Grid 子组件)
- `opencalc/entry/src/main/resources/base/element/string.json` (+13 个 string resource)
- `opencalc/entry/src/test/List.test.ets` (+2 行: 注册 KeyboardSwipe 套件)

## 下一步

1. ✅ 本地 commit 完成
2. 通知 dev-01 push 到远端
3. dev-01 / rev-01 / 用户 决定是否 close Issue #29

执行 `aid-archiving` 进入归档阶段 (由 dev-01 / archiving 阶段处理,本 issue 不做)。
