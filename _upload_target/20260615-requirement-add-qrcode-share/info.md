# Issue #13 一键分享二维码 — 代码仓理解

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- UI 测试能力: true (skill: harmonyos-ui-test)
- 模拟器列表: 127.0.0.1:5555 (running)
- hdc: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- bundleName: com.darkempire78.opencalculator

## 基本信息

- **需求类别**：新增功能（New Requirement）
- **需求名称**：qrcode-share
- **分析时间**：2026-06-15
- **分析范围**：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`、`qrcode/QrCodeBuilder.ets`（新增）

## 架构分析

### 模块结构图（涉及范围）

```
opencalc/entry/src/main/ets/
├── pages/
│   ├── Index.ets                    # 启动页
│   └── CalculatorPage.ets           # 主页面（核心改动）
├── calculator/
│   ├── Expression.ets               # 表达式预处理（已有，复用）
│   ├── Calculator.ets               # 计算引擎（已有，复用）
│   ├── HistoryFilter.ets            # 历史过滤（已有，不涉及）
│   └── NumberFormatter.ets          # 数字格式化（已有，复用）
├── model/
│   ├── Models.ets                   # 类型定义
│   └── ErrorFlags.ets               # 错误标志
├── qrcode/                          # 🆕 新增目录
│   └── QrCodeBuilder.ets            # 🆕 QR 内容生成器
├── entryability/
└── preferences/
    └── PreferencesStore.ets
```

### 核心模块职责

| 模块 | 职责 | 关键导出 |
|------|------|----------|
| CalculatorPage.ets | UI 渲染、按钮事件、状态管理 | `@Component CalculatorPage` |
| QrCodeBuilder.ets (🆕) | QR 内容生成（纯函数） | `buildSharePayload(expr, res): string` |
| Expression.ets | 表达式预处理 | `getCleanExpression` |
| CalcEngine | 表达式求值 | `evaluate` |
| NumberFormatter | 数值格式化 | `format` |
| ErrorFlags | 错误标志 | reset/snapshot/restore |

### 依赖关系

```
CalculatorPage
  ├─→ QrCodeBuilder.buildSharePayload  🆕 (新增依赖)
  ├─→ qrcode.createQrCode             🆕 HarmonyOS Kit（标准 API）
  ├─→ Expression.getCleanExpression   (已有)
  ├─→ CalcEngine.evaluate             (已有)
  ├─→ NumberFormatter.format          (已有)
  └─→ ErrorFlags                      (已有)
```

## 接口/契约识别

### 复用接口（无修改）

与 Issue #11 实时预览完全一致：
- `Expression.getCleanExpression(input, dec, grp): string`
- `CalcEngine.evaluate(eq, isDegree): number`
- `NumberFormatter.format(text, dec, grp, sys): string`
- `ErrorFlags.snapshot() / restore() / reset()`

### 新增接口（QR 内容生成）

#### `QrCodeBuilder.buildSharePayload`
```typescript
/**
 * 生成 QR 码分享内容
 * @param expression 用户输入的算式（如 "1+2"）
 * @param result 计算结果（如 "3"）
 * @returns URL 编码后的 payload（如 "opencalc://calc?expr=1%2B2&res=3"）
 */
function buildSharePayload(expression: string, result: string): string
```

- **副作用**：无（纯函数）
- **输入约束**：任意字符串（自动处理空值/特殊字符/超长）
- **返回值**：URL-encoded payload 字符串

### HarmonyOS QR Kit 接口（基础设施）

```typescript
import { qrcode } from '@kit.QRCodeKit'

qrcode.createQrCode(content: string, options?: qrcode.QrCodeOptions): Promise<PixelMap>
```

- **可用性**：HarmonyOS API 9+
- **限制**：content 不能太长（典型上限 ~4296 字节，但 QR 码大小受限，本项目自定义 200 字符）
- **返回值**：QR 码图像的 PixelMap（可直接渲染到 Image 组件）

## 公共组件或函数识别

### 可复用组件
- `SettingsPanel` / `AboutPanel` —— 居中浮层样式（SharePanel 可复用相同布局模式）
- `getBg/getBtnBg/getOp/getT1/getT2/getPanelBg` —— 主题 getter
- `DisplayPanel` —— 显示屏（新增分享按钮）

### 可复用函数
- `Expression.getCleanExpression`（不直接用于 QR，但模式可借鉴：纯函数 + ErrorFlags 隔离）
- `HistoryFilter.filter`（不涉及）
- `NumberFormatter.format`（显示 QR 文本时使用）

### 工具函数（测试基础设施）
- 上一变更（realtime-preview）的 Node 端口测试基础设施可复用（.test.mjs + .port.mjs）

## 影响范围分析

### 需修改的文件
| 文件 | 改动 | 估行数 |
|------|------|--------|
| CalculatorPage.ets | 新增 @State showShare + onShareClick/Close + SharePanel builder + DisplayPanel 分享按钮 | +60 行 |
| (新增) QrCodeBuilder.ets | buildSharePayload 纯函数 + MAX_PAYLOAD_LENGTH 常量 | +30 行 |
| (新增) QrCodeBuilder.test.ets | 单元测试 | +100 行 |

### 复用关系图（QR 分享调用链）

```
用户输入 expression → 按等号 → result 更新
  ↓
用户点击 DisplayPanel 上的"分享"按钮
  ↓
onShareClick()
  ├─ 校验 enabled (expression, errorMsg, result)
  ├─ payload = QrCodeBuilder.buildSharePayload(expression, result)
  ├─ qrImage = await qrcode.createQrCode(payload, { width: 240 })
  ├─ this.qrImage = qrImage
  └─ this.showShare = true
  ↓
SharePanel 显示 QR + 文本副本
  ↓
用户点击 ✕ → onShareClose()
  ├─ if (this.qrImage) this.qrImage.release()
  └─ this.showShare = false
```

### 影响评估
- **现有功能影响**：DisplayPanel 末尾添加按钮 + Stack 中添加 SharePanel 条件渲染（与 SettingsPanel/AboutPanel 同样的模式）
- **风险点**：
  - qrcode Kit 在某些设备/模拟器可能不可用 → 已设计"白底 + 容错"
  - PixelMap 资源管理 → onShareClose 显式 release
- **回归范围**：onEquals、onCopy、onHistoryTap、DisplayPanel 长按手势、SettingsPanel/AboutPanel

## 现有代码分析

### DisplayPanel 当前结构（CalculatorPage.ets:347-382）
```typescript
@Builder DisplayPanel() {
  Column() {
    // expression 行
    Text(this.expression.length > 0 ? this.expression : ' ')
    // preview 行 (Issue #11)
    Text(this.preview.length > 0 ? this.preview : ' ')
    // result / errorMsg 行
    if (this.errorMsg.length > 0) { Text(this.errorMsg) }
    else { Text(this.result.length > 0 ? this.result : '0') }
  }
  .gesture(LongPressGesture().onAction((): void => { this.onCopy() }))
}
```

### 新分享按钮插入位置（设计）
- 在 expression 行**上方**增加 Row：左 Blank + 右分享按钮
- 长按手势仍作用在 Column 层（保持不变）
- 按钮 onClick → onShareClick

### SettingsPanel 当前布局（参考）
```typescript
@Builder SettingsPanel() {
  Column() {
    Row() {
      Text('设置').fontSize(18).fontWeight(FontWeight.Bold)
      Blank()
      Text('✕').fontSize(20).fontColor(this.getT2())
        .onClick((): void => { this.showSettings = false })
    }
    // 内容 List
  }
  .width('85%').backgroundColor(this.getPanelBg()).borderRadius(16)
}
```

SharePanel 复用同样的"标题栏 + ✕关闭按钮 + 内容"模式。

## 风险识别

| 风险 | 等级 | 缓解 |
|------|------|------|
| qrcode Kit 在 API 9 模拟器不可用 | 中 | API 11+ 模拟器可用；若抛异常，SharePanel 显示"暂不支持"占位 |
| QR 内容含未编码特殊字符 | 高 | buildSharePayload 内显式 URL 编码 + 单元测试覆盖 `+/π/空格/中文` |
| QR 内容超长 Kit 抛异常 | 中 | 截断至 200 字符 + try/catch |
| PixelMap 资源未释放 | 低 | onShareClose 显式 release |
| AMOLED 主题下 QR 不可见 | 中 | QR 区域强制白底黑前景（独立于主题） |
| 长按手势冲突 | 低 | 按钮单独 onClick；长按作用在 Column 层 |
| ArkTS 静态分析对 qrcode Kit import 报错 | 中 | 检查 @ohos.qrcode.d.ts 是否随 SDK 包含；不可用时降级为占位 |

### 测试能力评估
- 单元测试能力: ✅ (hypium+hamock)
- UI 自动化测试能力: ✅ (hdc + 模拟器 127.0.0.1:5555)
- 端到端集成测试能力: ✅ (可在模拟器跑 QR 生成)
- 不能跑的实际原因: 无；可在真机/模拟器验证 QR 扫描

## 测试验证策略

### 单元测试（buildSharePayload 纯函数）
1. 基础：`buildSharePayload("1+2", "3")` → 含 `expr=1%2B2&res=3`
2. 特殊字符：`buildSharePayload("sin(π/2)", "1")` → 含 `%CF%80`
3. 空值：`buildSharePayload("", "")` → 不抛异常，返回合法 payload
4. 超长：构造 250 字符 → 返回值 ≤ 200 字符 + `&truncated=1`
5. URL 编码：`+` → `%2B`，`/` → `%2F`，`(` → `%28`，`)` → `%29`，空格 → `%20`
6. 中文（如未来支持）：含 UTF-8 多字节编码

### 端到端 / UI 测试
1. 在模拟器跑 OpenCalc，输入 `1+2` 按 =
2. 显示屏右上角点击"分享"按钮
3. 验证模态层显示 + QR 码像素图非空
4. 用其他设备扫码，验证内容可解析
5. 关闭模态层，验证 QR 区域消失且 PixelMap 已 release

### 回归验证
- onEquals 流程
- 长按显示屏复制功能
- 历史记录持久化
- 三种主题切换

## 监控运维支持

不涉及（本地计算 App，无远程监控需求）

## 关键发现

### 可复用资源
- `SettingsPanel` 的浮层布局模式（SharePanel 复用）
- `ErrorFlags.snapshot/restore` 模式（如果 QR 涉及计算）
- 上一变更（realtime-preview）的 Node 端口测试基础设施

### 风险提示
- QR 内容生成必须用纯函数 + URL 编码（不可拼接字符串）
- qrcode Kit 的 PixelMap 必须显式 release
- AMOLED 主题下 QR 区域强制白底

### 建议事项
1. QrCodeBuilder.ets 实现为纯函数（接收 expr/result，返回 payload），便于 100% 单元测试覆盖
2. URL 编码直接用 ArkTS 标准 `encodeURIComponent`
3. SharePanel 复用 SettingsPanel 的浮层布局（宽度 80-85% + borderRadius 16）
4. PixelMap 释放路径：在 onShareClose 中 release，并在 onPageHide 时兜底 release
5. 测试基础设施：复用上一变更的 .test.mjs + .port.mjs 方案
