# 需求提案 — Issue #13 一键分享二维码

## 1. 原始需求

> 把当前算式和结果一键生成二维码，方便手机扫到电脑上用 | 分享 | ⭐⭐ | 跨设备协作场景

**Issue 来源**：Issue #13
**类型**：新增功能（Design/Development - New Requirement）
**变更名称**：qrcode-share

## 2. 需求理解

### 2.1 意图分类
- **类型**：新增功能
- **一句话概括**：在计算器主屏提供"分享"按钮，把当前表达式与结果生成为二维码，手机扫码后可在另一台设备复用算式与结果。

### 2.2 领域映射
- **UI/交互**：在 DisplayPanel 右侧（或长按弹层）新增"分享"图标；点击弹出全屏/居中 QR 码模态层
- **二维码生成**：HarmonyOS 内置 `@kit.QRCodeKit`（API 9+）生成 QR 码 pixelMap
- **内容格式**：把 expression + " = " + result 编码为可解析字符串（接收端可直接看到算式与结果）
- **状态管理**：新增 `showShare: boolean` 状态；分享模态层独立于历史/设置面板

### 2.3 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | modify | CalculatorPage.ets: DisplayPanel 新增分享按钮 + SharePanel 模态层 |
| ViewModel | extend | CalculatorPage 新增 onShareClick()、onShareClose()；新增 @State showShare、qrPixelMap |
| Model | 无 | 不需要新增数据模型 |
| 数据层 | 无 | 无持久化 |
| 基础设施 | extend | 引入 @ohos.qrcode（HarmonyOS 标准 Kit，无需新增三方依赖） |

### 2.4 关键实体
- **数据实体**：无（QR 内容从 expression/result 派生）
- **页面实体**：CalculatorPage.SharePanel（新增）
- **接口实体**：
  - `qrcode.createQrCode(content, options): Promise<PixelMap>`（HarmonyOS 标准 API）
  - `image.createPixelMap(...)` （已有，可复用）
- **事件实体**：onShareClick → 生成 QR → 弹出模态；onShareClose → 关闭模态

### 2.5 关键决策（已自行拍板）
- **触发入口**（decision）：在显示屏右上角加"分享"图标（紧邻历史折叠图标），保持现有 ToggleRow 布局稳定
- **QR 内容格式**（decision）：`opencalc://calc?expr=<URL编码后的表达式>&res=<URL编码后的结果>` —— 既能让手机看到原始算式，又能在同 App 直接还原（容错性：URL 解析失败时按纯文本显示）
- **降级条件**（decision）：expression 为空 或 errorMsg 非空 → 分享按钮置灰（disabled 状态），避免生成无意义二维码
- **大小限制**（decision）：QR 内容 < 200 字符（防止超大数据触发 QR 生成失败）；超长则截断 + 提示
- **模态层**（decision）：与 SettingsPanel/AboutPanel 一致的居中浮层样式；显示 QR + 算式/结果文本 + 关闭按钮

### 2.6 复杂度评估
- **等级**：S（简单）
- **理由**：单页面 UI 增强 + 1 个模态层 + 1 个新工具类，< 150 行代码改动
- **影响模块数**：1（CalculatorPage.ets）+ 1 新文件（QrCodeBuilder.ets 工具类）
- **架构变更**：否
- **数据模型变更**：否

## 3. 验收标准

### 3.1 功能验收
- [ ] 用户输入合法表达式后按 =，显示屏右上角出现"分享"图标
- [ ] 点击"分享"图标，弹出居中 QR 码模态层，显示算式/结果文本
- [ ] QR 码内容为 `opencalc://calc?expr=<expr>&res=<result>` 格式
- [ ] QR 码像素图清晰可扫（黑底白块，3 静默区）
- [ ] expression 为空或 errorMsg 非空时，分享按钮不可点击
- [ ] 模态层"关闭"按钮可关闭 QR 码
- [ ] 长按显示屏（现有复制手势）不影响新分享按钮

### 3.2 性能验收
- [ ] QR 生成耗时 < 200ms
- [ ] 模态层打开/关闭动画流畅

### 3.3 兼容性验收
- [ ] 不破坏现有"按等号"流程
- [ ] 不影响历史记录功能
- [ ] 不影响偏好设置
- [ ] 不破坏现有复制手势（长按显示屏）
- [ ] 三种主题（默认/暗色/AMOLED）下 QR 模态层对比度足够

## 4. 范围边界

### 范围内
- DisplayPanel 分享按钮（图标 + 点击事件）
- 居中 QR 码模态层（SharePanel builder）
- QR 内容生成工具类 QrCodeBuilder.ets（纯函数：buildSharePayload → string）
- 单元测试 QrCodeBuilder.test.ets（payload 格式化、URL 编码、特殊字符、超长截断）

### 范围外
- 接收端 App 实现（手机扫码端逻辑）
- 三方社交分享（微信/QQ 等）
- QR 码扫描读取（仅生成）
- 历史记录条目的 QR 分享（仅当前屏幕的 expression + result）

## 5. 相关文件

| 文件 | 角色 | 预计改动 |
|------|------|----------|
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` | 主页面 | 新增 showShare @State、onShareClick/Close、SharePanel builder、DisplayPanel 添加分享按钮 |
| `opencalc/entry/src/main/ets/qrcode/QrCodeBuilder.ets` | 新增：QR 内容生成器 | buildSharePayload(expression, result): string |
| `opencalc/entry/src/test/ets/qrcode/QrCodeBuilder.test.ets` | 新增：单元测试 | payload 格式、特殊字符、转义、超长截断等 8-10 个用例 |
