# 需求 SPEC（增量）— Issue #29: 竖屏手势滑动切换三种键盘模式

> 基于 delta-spec-template v1.2，标记"不涉及"的章节保留模板结构。

---

## 系统背景

### 目的

OpenCalc 计算器当前仅支持"基础"和"科学"两种键盘模式,模式切换依赖页面顶部的文字按钮点击。本需求在 CalculatorPage 引入**水平滑动手势** + Swiper 组件实现"基础/科学/程序员"三页键盘的桌面式切换,并补全缺失的"程序员"键盘(HEX/DEC/OCT/BIN + 位运算)。解决用户单手操作时,难以触达顶部模式按钮的痛点。

### 术语与缩写

| 术语/缩写 | 定义 |
| ----- | --- |
| Swiper | HarmonyOS ArkUI 内置滑动容器组件,支持页面切换动画与指示器 |
| KeyboardMode | 键盘模式枚举 (BASIC / SCIENTIFIC / PROGRAMMER) |
| PanGesture | HarmonyOS 平移手势识别器 |
| FMEA | Failure Mode and Effects Analysis 失效分析 |

---

## 系统上下文

### 目标系统

| 字段 | 内容 |
| ----------------- | --- |
| 系统名称 | OpenCalc (HarmonyOS) |
| 系统边界说明 | 单进程 ArkUI 应用,CalculatorPage.ets 为唯一修改页 |

### 周边交互方清单

| 编号 | 外部系统名称 | 类型 | 交互接口类型 | 交互接口主要功能 |
| ----- | ------ | ------------------ | ------------------------------------ | -------- |
| ES-01 | 用户 | 人 | UI 触摸手势 | 滑动 Swiper / 点击模式按钮 |
| ES-02 | @ohos.data.preferences | 系统 Kit | Preferences API | 持久化模式默认值 |

---

## 需求描述

| 需求编号 | 需求名称 | 需求描述 | 设计人员 |
| -------- | -------- | -------- | -------- |
| IR-01 | 竖屏三页滑动切换 | 竖屏 CalculatorPage 支持水平滑动手势在基础/科学/程序员三页之间切换 | claude -p |
| IR-02 | 程序员键盘 | 提供基础版程序员键盘 (HEX/DEC/OCT/BIN 基数切换 + AND/OR/NOT/XOR 位运算 + << >> 位移) | claude -p |
| IR-03 | 模式按钮兼容 | 保留原有"基础/科学"切换按钮,扩展为三态循环 (基础↔科学↔程序员↔基础) | claude -p |
| IR-04 | 模式持久化 | preferences 新增 programmerModeDefault 字段,App 重启恢复上次模式 | claude -p |
| IR-05 | 页面指示器 | Swiper 底部显示三个圆点指示器,指示当前模式 | claude -p |

### 用户旅程

#### 旅程总览

| 旅程编号 | 旅程名称 | 目标用户/角色 | 旅程目标 (G) | 触发与结束条件 | 关键体验路径 (KEP-XXX) |
| ---- | ---- | ------- | ------- | ------- | --------------- |
| J-01 | 三页键盘切换 | 单手操作的手机用户 | G: 快速切换键盘模式而不丢失当前输入 | 触发: 触摸 Swiper;结束: 切换完成 | KEP-01 / KEP-02 |

### 关键体验路径 (KEP)

- **KEP-01: 滑动切换**
  - 用户目标: 通过左/右滑快速切换键盘模式
  - 路径: 竖屏当前模式页 → 手指左滑 → 切换到下一模式页 → 释放手指 → 动画完成 → 圆点指示器更新
  - 体验预期: 切换动画 ≤ 300ms,无卡顿,输入框光标位置保持

- **KEP-02: 按钮循环切换**
  - 用户目标: 通过点击顶部按钮在三模式间循环
  - 路径: 当前 BASIC → 点击 → SCIENTIFIC → 再点击 → PROGRAMMER → 再点击 → BASIC
  - 体验预期: 按钮 label 同步更新 ("基础"/"科学"/"程序员"),Swiper 同步滚动

### 关键体验指标 (KEI)

| 指标编号 | 指标名称 | 定义 | 底线值 | 达标值 | 挑战值 | 测量方法 |
| ---- | ---- | --- | --- | ---- | --- | ---- |
| KEI-01 | 滑动切换耗时 | Swiper 从手势释放到动画完成 | ≤ 500ms | ≤ 300ms | ≤ 200ms | UI 自动化测试 |
| KEI-02 | 模式持久化正确率 | 重启后模式匹配上次退出值 | 100% | 100% | 100% | 单元测试 |
| KEI-03 | 圆点指示器同步延迟 | mode 变化到指示器更新 | ≤ 16ms (一帧) | ≤ 16ms | ≤ 16ms | UI 自动化测试 |

### 假设和约束

| 序号 | 约束类别 | 约束描述 | 对设计的影响 |
| ---- | ------------------------------ | -------- | ------------ |
| 1 | 硬件限制 | 仅竖屏生效;横屏继续只显示科学模式 | Swiper 仅在 `!isLandscape` 时渲染 |
| 2 | 外部系统接口 | @ohos.data.preferences 仅 1 实例,字段名不可冲突 | 新增字段 programmerModeDefault,与旧 scientificModeDefault 共存 |
| 3 | 用户特征约束 | 单手操作场景,滑动比顶部按钮更易触达 | 滑动切换为默认交互 |
| 4 | 标准/规范约束 | HarmonyOS NEXT API 12+ | 使用 Swiper / PanGesture API 12 接口 |
| 5 | 其他硬约束 | 输入框 TextArea 已有内部手势 | 滑动生效区域限定为键盘区域,TextArea 不在 Swiper 内 |

---

## 场景用例分析

### 场景清单

| 场景编号 | 场景名称 | 场景要素覆盖 | 优先级 | 备注 |
| -------- | -------- | ------------ | ------ | ---- |
| SC-001 | 竖屏左滑切到下一模式 | T=运行期 / G=切换 / E=竖屏 / A=用户 / S=BASIC | 高 | KEP-01 主路径 |
| SC-002 | 竖屏右滑切到上一模式 | T=运行期 / G=切换 / E=竖屏 / A=用户 / S=PROGRAMMER | 高 | KEP-01 |
| SC-003 | 模式按钮循环切换 | T=运行期 / G=切换 / E=竖屏 / A=用户 / S=任意 | 高 | KEP-02 |
| SC-004 | 横屏不显示 Swiper | T=运行期 / G=横屏模式 / E=横屏 / A=用户 / S=任意 | 中 | 横屏布局不变 |
| SC-005 | App 重启模式恢复 | T=启动期 / G=恢复 / E=竖屏 / A=用户 / S=上次模式 | 中 | 持久化 |
| SC-006 | 程序员键盘运算 | T=运行期 / G=位运算 / E=竖屏 / A=用户 / S=PROGRAMMER | 中 | IR-02 |

### 场景 SC-001: 竖屏左滑切到下一模式

#### 场景描述

用户在竖屏当前 BASIC 模式,手指向左滑动,Swiper 切换到 SCIENTIFIC 模式页。

#### 场景要素分析

| 场景要素 | 取值 |
| ------------ | --- |
| **T** 生命周期阶段 | 运行期 (App 已启动,CalculatorPage 已挂载) |
| **G** 场景目标 | 切换到下一个键盘模式 (BASIC → SCIENTIFIC) |
| **E** 环境 | HarmonyOS 设备, 竖屏 |
| **A** 参与者 | 用户 (单手) |
| **S** 系统状态 | currentMode = BASIC, Swiper index = 0 |

#### 用例识别

| 用例编号 | 用例名称 | 用例目的 | 用例描述 | 是否基础用例 |
| -------- | -------- | -------- | -------- | ------------ |
| UC-001-01 | Swiper 滑动切到下一模式 | 通过 Swiper 水平左滑切换到下一键盘页 | 监听 onChange 事件,更新 currentMode,同步更新 preferences | 是 |

#### 用例 UC-001-01: Swiper 滑动切到下一模式

##### 简要说明

用户通过水平滑动手势触发 Swiper 翻页,Swiper 的 onChange 事件通知模式状态机更新,持久化到 preferences。

##### Actor

| 角色 | 类型 | 与系统的关系 |
| --- | ------------ | ------ |
| 用户 | 主,人 | 发起滑动 |

##### 前置条件

| 场景要素 | 本用例采用的取值 | 对用例的影响点 | 处理方式 |
| ------------ | ------------------ | ------------------------ | --------------------- |
| T | 运行期 | Swiper 必须已挂载 | 保持 |
| G | 切换模式 | onChange 触发 mode 同步 | 扩展 |
| E | 竖屏 | isLandscape 必须为 false | 保持 |
| A | 用户 | 单次左滑手势 | 保持 |
| S | currentMode = BASIC | 目标 → SCIENTIFIC | 扩展 |

##### 最小保证

- 滑动结束必须切换到下一个有效模式 (BASIC → SCIENTIFIC → PROGRAMMER → BASIC 循环)
- currentMode 状态必须更新
- preferences 必须持久化

##### 成功保证 (后置条件)

- Swiper 当前 index 等于 newMode
- 圆点指示器当前项高亮
- preferences.programmerModeDefault / scientificModeDefault 已同步更新

##### 触发事件

用户手指在键盘区域水平滑动距离 ≥ 50vp (HarmonyOS Swiper 默认阈值)。

##### 主成功路径 (基本事件流)

```
1. 用户在 BASIC 模式页手指左滑
2. Swiper 监听到 onGestureEvent 接近翻页阈值
3. Swiper 执行切换动画到 index=1 (SCIENTIFIC)
4. Swiper 触发 onChange(index=1)
5. modeController.onSwiperChange(1) 处理:
   - newMode = KeyboardMode[1] = SCIENTIFIC
   - this.currentMode = newMode
   - this.scientific = true (兼容旧字段)
   - prefs.setScientificModeDefault(1)
6. UI 圆点指示器同步高亮第 2 个点
7. 按钮 label 更新为 "科学"
```

##### 扩展路径

```
1a. 用户滑动距离 < 阈值
   → Swiper 自动回弹到原 index
   → currentMode 不变

2a. 用户在 PROGRAMMER 模式页左滑 (循环)
   → Swiper index = 0 (BASIC)
   → modeController.onSwiperChange(0)
   → currentMode = BASIC

3a. 启动时读取 preferences:
   - scientificModeDefault == 1 → 初始 SCIENTIFIC
   - programmerModeDefault == 1 → 初始 PROGRAMMER
   - 都为 0 → 初始 BASIC
   - 冲突时 SCIENTIFIC 优先
```

##### DFX 属性

| DFX 属性 | 是否涉及 | 要求 (可验证表述) |
| ----------------------------- | -------- | ------------------ |
| 性能 (时延/吞吐/并发) | 是 | 切换动画 ≤ 300ms (KEI-01) |
| 可靠性 (故障恢复/数据一致性) | 是 | preferences 写入失败时不影响 UI 状态 |
| 安全 | 否 | 不涉及 |
| 隐私 | 否 | 不涉及 |
| 韧性 | 否 | 不涉及 |
| 可服务性 | 否 | 不涉及 |
| 可测试性 | 是 | Swiper onChange 可由单元测试触发 |
| 功耗 | 否 | 不涉及 |
| 兼容性 | 是 | 旧 scientificModeDefault 字段保留 |
| 大数据打点 | 否 | 不涉及 |
| 隔离 (共主干/Lite) | 否 | 不涉及 |
| 升级产品适配 | 是 | preferences 新增字段,旧版本可正常读取 |
| 数据兼容性 | 是 | 老用户偏好升级后 scientificModeDefault 仍生效 |
| 性能 (关键体验) | 是 | KEI-03 指示器同步 ≤ 16ms |
| 功耗 | 否 | 不涉及 |
| 其他 | 否 | 不涉及 |

##### 业务威胁建模需求 (消减措施清单, 可选)

| 措施编号 | 适用场景/用例步骤 | 风险/威胁面 (简述) | 消减措施 (可验证表述) | 关联数据/接口 | 验证方式 |
| ----- | --------- | ---------- | ----------- | ------- | -------------- |
| TM-01 | 步骤 5 | preferences 写入失败 | preferences.setXxx 包装 try-catch,失败仅记日志不影响 UI | PreferencesStore.setProgrammerModeDefault | 单元测试 mock 失败 |

##### 可靠性分析需求 (FMEA 消减措施清单)

| 异常事件编号 | 异常事件 | 影响 | 消减措施 | 触发检测/告警/日志要求 | 恢复与兜底 |
| ------ | ------------------- | -------------- | ----------- | ------------ | ------------- |
| FM-01 | Swiper index 越界 (onChange 传入非法 index) | mode 错乱 | modeController.onSwiperChange 内 if/else 严格枚举,非法 index 落到 BASIC | 日志: console.warn('invalid swiper index='+i) | 兜底: 默认 BASIC |
| FM-02 | preferences 写入失败 | 模式不持久化 | try-catch 包装 setXxx;失败时仅 UI 正常运作,下次启动重新尝试 | 日志: console.error('prefs write failed') | 兜底: UI 状态正确,下次启动用上次值 |
| FM-03 | Swiper 与按钮循环方向不一致 | 用户混淆 | 统一 onSwiperChange 与 onButtonClick 都通过同一个 currentMode 状态机 | 日志: 不需要 | 兜底: 通过 onChange 单向触发,反向同步通过 SwiperController.changeIndex |
| FM-04 | 启动时两种 prefs 同时为 1 | currentMode 冲突 | 优先级 SCIENTIFIC > PROGRAMMER > BASIC | 日志: 不需要 | 兜底: 不可能两个都为 1 (代码上互斥) |
| FM-05 | 输入框 TextArea 与 Swiper 手势冲突 | TextArea 横滑失效 | TextArea 保持在 Swiper 之外,不参与手势冲突 | 不需要 | 兜底: 输入框选择文字不受影响 |

##### 验证达成标准

- 单元测试: modeController.onSwiperChange(0/1/2) 三态切换 + 循环正确
- 单元测试: 启动时 prefs 读取优先级
- UI 测试: 真机/模拟器滑动 Swiper → 验证 mode 切换 + 圆点指示器
- UI 测试: 点击按钮 → 验证 Swiper index 同步

##### 是否影响架构

| 是否影响 | 影响范围 | 影响类型 | 影响描述 |
| ---- | ---- | ------------------------------ | ---- |
| 否 | 单页 + 单 ViewModel | 无 | Swiper 包裹 View 层,状态机扩展 currentMode 字段 |

##### 功能影响列表

| 功能编号 | 功能描述 | 影响类型 | 影响描述 |
| ---- | ---- | -------------- | ----------- |
| F-01 | KeyboardMode 枚举 | 新增 | Models.ets: BASIC/SCIENTIFIC/PROGRAMMER |
| F-02 | currentMode 状态 | 修改 | CalculatorPage.ets: scientific: boolean → currentMode: KeyboardMode |
| F-03 | Swiper 三页容器 | 新增 | CalculatorPage.ets: 包裹三个键盘布局 |
| F-04 | 程序员键盘布局 | 新增 | CalculatorPage.ets: 和科学键并列,提供 HEX/DEC/OCT/BIN + 位运算 |
| F-05 | 模式按钮循环 | 修改 | CalculatorPage.ets: label 跟随 currentMode, click 循环 |
| F-06 | 圆点指示器 | 新增 | CalculatorPage.ets: Swiper 默认 DotIndicator |
| F-07 | preferences 新字段 | 新增 | PreferencesStore.ets: programmerModeDefault |
| F-08 | modeController 单向数据流 | 新增 | CalculatorPage.ets: onSwiperChange 统一处理 |

##### 需求分解列表 (IR → SR)

| IR 编号 | SR 编号 | SR 名称 | SR 描述 | 关联功能 | 关联功能编号 |
| ----- | ----- | ----- | ----- | ---- | ------ |
| IR-01 | SR-01 | Swiper 三页容器 | CalculatorPage 竖屏时外层用 Swiper,index 与 currentMode 双向绑定 | F-03 | F-03 |
| IR-01 | SR-02 | 滑动事件处理 | onChange 触发 modeController.onSwiperChange,统一入口 | F-08 | F-08 |
| IR-02 | SR-03 | 程序员键盘布局 | 程序员页包含: HEX DEC OCT BIN 四基数切换 + AND OR NOT XOR 位运算 + << >> 位移 | F-04 | F-04 |
| IR-03 | SR-04 | 模式按钮循环 | 按钮 onClick 调用 modeController.cycleMode() | F-05 | F-05 |
| IR-04 | SR-05 | preferences 读写 | PreferencesStore.getProgrammerModeDefault / setProgrammerModeDefault | F-07 | F-07 |
| IR-05 | SR-06 | DotIndicator 指示器 | Swiper.indicator = DotIndicator() | F-06 | F-06 |

---

## 系统需求列表 (SR)

| SR 编号 | IR 编号 | SR 名称 | SR 描述 (What) | 关联功能 | 利益相关者 (who) | 系统对外能力行为 (what) | 关联用例/场景 | 可验证达成标准 | 优先级 | 需求来源 |
| ------- | ------- | ------- | --------------- | -------- | ----------------- | ------------------------ | ------------- | -------------- | ------------------ | -------- |
| SR-01 | IR-01 | Swiper 三页容器 | Swiper 包裹三页键盘,index ↔ currentMode 同步 | F-03 | 用户 | 滑动手势触发页面切换 | UC-001-01 | 滑动后 currentMode 与 index 一致 | 高 | IR-01 |
| SR-02 | IR-01 | 滑动事件处理 | onSwiperChange 统一处理 index 变化,更新 currentMode + preferences | F-08 | 用户 | 输入事件驱动状态更新 | UC-001-01 | index 变化时 prefs 同步 | 高 | IR-01 |
| SR-03 | IR-02 | 程序员键盘布局 | 程序员页提供 HEX/DEC/OCT/BIN + 位运算按键 | F-04 | 用户 | 提供位运算入口 | SC-006 | 键入 HEX/DEC 模式可见 | 中 | IR-02 |
| SR-04 | IR-03 | 模式按钮循环 | 点击按钮在 BASIC↔SCIENTIFIC↔PROGRAMMER 之间循环 | F-05 | 用户 | 提供非手势切换通道 | UC-003-01 | 点击 3 次回到 BASIC | 高 | IR-03 |
| SR-05 | IR-04 | preferences 读写 | PreferencesStore 提供 get/setProgrammerModeDefault | F-07 | 用户 | 持久化模式选择 | SC-005 | 重启模式恢复 | 中 | IR-04 |
| SR-06 | IR-05 | DotIndicator | Swiper 底部圆点指示器高亮当前页 | F-06 | 用户 | 提供视觉反馈 | UC-001-01 | 当前 index 对应圆点高亮 | 中 | IR-05 |