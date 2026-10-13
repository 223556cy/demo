# 系统设计 — Issue #13 一键分享二维码

## 1. 架构总览

本次变更属于**纯 UI 增强 + 1 个新工具类**，不涉及架构变更。采用与 SettingsPanel/AboutPanel 相同的"居中浮层"模式，新增 SharePanel 即可。

```
┌─────────────────────────────────────────────────────────┐
│  CalculatorPage (Stack)                                  │
│    ├─ 主内容（DisplayPanel + ButtonGrid）                │
│    ├─ if (showSettings) SettingsPanel   ← 已有          │
│    ├─ if (showAbout)   AboutPanel       ← 已有          │
│    └─ if (showShare)   SharePanel       ← 🆕 新增       │
└─────────────────────────────────────────────────────────┘
        │
        ├─ onShareClick → QrCodeBuilder.buildSharePayload (纯函数)
        ├─                 qrcode.createQrCode(payload)    (HarmonyOS Kit)
        └─ onShareClose → pixelMap.release()
```

## 2. 新增模块设计

### 2.1 QrCodeBuilder.ets（新增）

**位置**：`opencalc/entry/src/main/ets/qrcode/QrCodeBuilder.ets`

**职责**：生成 QR 码内容字符串（纯函数，无副作用）

**导出**：

```typescript
// ==================== 常量 ====================
/** QR payload 字符上限（保守值，规避 Kit 边界问题） */
export const MAX_PAYLOAD_LENGTH: number = 200

/** QR payload 前缀（自定义 URL scheme） */
export const PAYLOAD_PREFIX: string = 'opencalc://calc?expr='

/** 结果字段前缀 */
export const RESULT_PREFIX: string = '&res='

/** 截断标记 */
export const TRUNCATED_FLAG: string = '&truncated=1'

// ==================== 函数 ====================

/**
 * 生成 QR 码分享 payload
 * @param expression 用户输入的算式（如 "1+2"）
 * @param result 计算结果（如 "3"）
 * @returns URL 编码后的 payload
 *          超长则截断 expression 并追加 &truncated=1
 */
export function buildSharePayload(expression: string, result: string): string {
  // 1. 输入归一化（null/undefined → ""）
  const safeExpr: string = (expression === undefined || expression === null) ? '' : expression
  const safeRes: string = (result === undefined || result === null) ? '' : result

  // 2. URL 编码
  const encExpr: string = encodeURIComponent(safeExpr)
  const encRes: string = encodeURIComponent(safeRes)

  // 3. 基础 payload
  let payload: string = PAYLOAD_PREFIX + encExpr + RESULT_PREFIX + encRes

  // 4. 截断处理（保留 result 完整，优先截断 expr）
  if (payload.length > MAX_PAYLOAD_LENGTH) {
    const fixedTail: string = RESULT_PREFIX + encRes
    const maxExprLen: number = MAX_PAYLOAD_LENGTH - PAYLOAD_PREFIX.length - fixedTail.length - TRUNCATED_FLAG.length
    if (maxExprLen > 0) {
      const truncatedExpr: string = encExpr.substring(0, maxExprLen)
      payload = PAYLOAD_PREFIX + truncatedExpr + fixedTail + TRUNCATED_FLAG
    } else {
      // result 本身就超过上限（极罕见），直接截断整个 payload
      payload = payload.substring(0, MAX_PAYLOAD_LENGTH)
    }
  }

  return payload
}

// ==================== 命名空间风格导出（与项目内 HistoryFilter 一致） ====================
export class QrCodeBuilder {
  static readonly MAX_PAYLOAD_LENGTH = MAX_PAYLOAD_LENGTH
  static readonly PAYLOAD_PREFIX = PAYLOAD_PREFIX
  static readonly RESULT_PREFIX = RESULT_PREFIX
  static readonly TRUNCATED_FLAG = TRUNCATED_FLAG
  static buildSharePayload = buildSharePayload
}
```

**测试要点**：
- 单元测试 100% 覆盖（纯函数，无环境依赖）
- 复用上一变更的 Node 端口测试基础设施（.test.mjs + .port.mjs）

### 2.2 CalculatorPage.ets（修改）

**新增 @State**：
```typescript
@State showShare: boolean = false          // SharePanel 显示开关
@State qrImage: PixelMap | null = null     // QR 码 PixelMap
```

**新增方法**：
```typescript
/**
 * aid-workflow 20260615: 点击分享按钮
 * 校验启用条件 → 生成 payload → 异步生成 QR → 弹出模态
 */
async onShareClick(): Promise<void> {
  // 1. 启用条件校验
  if (this.expression.length === 0) return
  if (this.errorMsg.length > 0) return
  if (this.result.length === 0) return

  try {
    // 2. 生成 payload
    const payload: string = QrCodeBuilder.buildSharePayload(this.expression, this.result)

    // 3. 异步生成 QR 码（HarmonyOS Kit）
    const opts: qrcode.QrCodeOptions = { width: 240, height: 240, backgroundColor: '#FFFFFF', foregroundColor: '#000000' }
    const pm: PixelMap = await qrcode.createQrCode(payload, opts)

    // 4. 释放旧资源（如有） + 保存新资源 + 弹出模态
    if (this.qrImage) this.qrImage.release()
    this.qrImage = pm
    this.showShare = true
  } catch (e) {
    promptAction.showToast({ message: '二维码生成失败' })
  }
}

/**
 * aid-workflow 20260615: 关闭分享模态层
 * 释放 PixelMap 资源，避免内存泄漏
 */
onShareClose(): void {
  if (this.qrImage) {
    this.qrImage.release()
    this.qrImage = null
  }
  this.showShare = false
}

/**
 * aid-workflow 20260615: 分享按钮是否可用（用于 UI 状态控制）
 */
get isShareEnabled(): boolean {
  return this.expression.length > 0 && this.errorMsg.length === 0 && this.result.length > 0
}
```

**新增 Builder**：
```typescript
@Builder SharePanel() {
  Column() {
    // 标题栏
    Row() {
      Text('二维码分享').fontSize(18).fontWeight(FontWeight.Bold).fontColor(this.getT1())
      Blank()
      Text('✕').fontSize(20).fontColor(this.getT2())
        .onClick((): void => { this.onShareClose() })
    }.width('100%').padding(16)

    // QR 码区域（强制白底，不受主题影响）
    if (this.qrImage) {
      Image(this.qrImage)
        .width(240).height(240)
        .backgroundColor('#FFFFFF')
        .borderRadius(8)
    } else {
      // 占位（QR 异步生成中）
      Column().width(240).height(240).backgroundColor('#FFFFFF').borderRadius(8)
    }

    // 文本副本（人工可读）
    Text(this.expression + ' = ' + this.result)
      .fontSize(14).fontColor(this.getT1())
      .padding({ top: 12 })
      .maxLines(2)

    // 截断提示（payload 超长时）
    if (QrCodeBuilder.buildSharePayload(this.expression, this.result).indexOf(QrCodeBuilder.TRUNCATED_FLAG) !== -1) {
      Text('⚠ 算式过长已截断').fontSize(11).fontColor(this.getT2()).padding({ top: 4 })
    }

    // 提示文案
    Text('用手机扫码即可在手机上查看算式与结果')
      .fontSize(11).fontColor(this.getT2()).padding({ top: 8 })
  }
  .width('85%').padding(24).backgroundColor(this.getPanelBg()).borderRadius(16)
}
```

**修改 DisplayPanel**：在 expression 行上方增加 Row，左 Blank + 右分享按钮：

```typescript
@Builder DisplayPanel() {
  Column() {
    // 🆕 新增：分享按钮行
    Row() {
      Blank()
      Text('⎘')
        .fontSize(18)
        .fontColor(this.isShareEnabled ? this.getOp() : this.getT2())
        .padding(8)
        .enabled(this.isShareEnabled)
        .onClick((): void => { this.onShareClick() })
    }
    .width('100%').padding({ right: 8, top: 4 })

    // 原有 expression 行
    Text(this.expression.length > 0 ? this.expression : ' ')
      .fontSize(this.isLandscape ? 14 : 18).fontColor(this.getT2())
      .width('100%').textAlign(TextAlign.End)
      .padding({ right: 12, left: 12 }).maxLines(3)

    // 原有 preview 行 (Issue #11)
    Text(this.preview.length > 0 ? this.preview : ' ')
      .fontSize(this.isLandscape ? 12 : 14).fontColor(this.getT2())
      .width('100%').textAlign(TextAlign.End)
      .padding({ right: 12, left: 12, top: 2, bottom: 2 })
      .maxLines(1)

    // 原有 result / errorMsg 行
    if (this.errorMsg.length > 0) {
      Text(this.errorMsg)...
    } else {
      Text(this.result.length > 0 ? this.result : '0')...
    }
  }
  .width('100%').padding(this.isLandscape ? { top: 8, bottom: 2 } : { top: 24, bottom: 8 })
  .gesture(LongPressGesture().onAction((): void => { this.onCopy() }))  // 保持不变
}
```

**修改 build()**：Stack 中增加 SharePanel 条件渲染：
```typescript
Stack() {
  if (this.isLandscape) { /* ... */ } else { /* ... */ }
  if (this.showSettings) this.SettingsPanel()
  if (this.showAbout) this.AboutPanel()
  if (this.showShare) this.SharePanel()   // 🆕
}
```

**新增 import**：
```typescript
import { qrcode } from '@kit.QRCodeKit'
import { image } from '@kit.ImageKit'  // PixelMap 类型
import { QrCodeBuilder } from '../qrcode/QrCodeBuilder'
```

## 3. 状态机

```
[closed] -- onShareClick (enabled) --> [generating] -- success --> [open]
                                       ↓ fail
                                       [closed] + Toast

[open] -- onShareClose --> [closed] (release PixelMap)
[open] -- onPageHide --> [closed] (release PixelMap, 兜底)
```

## 4. 关键交互流

### 4.1 正常分享流
```
1. 用户输入 "1+2" → expression="1+2"
2. 用户按 "=" → result="3", errorMsg=""
3. 显示屏右上角"⎘"按钮高亮 (isShareEnabled=true)
4. 用户点击 "⎘"
5. onShareClick() 校验通过 → buildSharePayload("1+2", "3") = "opencalc://calc?expr=1%2B2&res=3"
6. await qrcode.createQrCode(...) → PixelMap
7. showShare=true → SharePanel 显示
8. 用户看到 QR + 文本 "1+2 = 3"
9. 手机扫码 → 解析出 expr="1+2" res="3"
10. 用户点击 ✕ → onShareClose() → release PixelMap → showShare=false
```

### 4.2 降级流（无结果）
```
1. 用户输入 "1+2" 但未按 =
2. result="" → isShareEnabled=false
3. "⎘"按钮显示灰色（fontColor=getT2()），enabled=false
4. 点击无反应（ArkTS .enabled(false) 自动拦截）
```

### 4.3 异常流（Kit 失败）
```
1. onShareClick() 校验通过
2. qrcode.createQrCode() throws
3. catch → promptAction.showToast({ message: '二维码生成失败' })
4. showShare 保持 false，qrImage 保持 null
```

## 5. 测试设计

### 5.1 单元测试（QrCodeBuilder.test.ets）

| 用例 | 输入 | 期望输出 |
|------|------|----------|
| TC-01 基本 | expr="1+2", res="3" | `opencalc://calc?expr=1%2B2&res=3` |
| TC-02 特殊字符 π | expr="sin(π/2)", res="1" | 含 `%CF%80`、`%28`、`%29` |
| TC-03 空字符串 | expr="", res="" | `opencalc://calc?expr=&res=` |
| TC-04 空格 | expr="1 + 2", res="3" | 空格编码为 `%20` |
| TC-05 斜杠 | expr="1/2", res="0.5" | `/` 编码为 `%2F` |
| TC-06 超长（截断） | expr=250*'a', res="123" | 长度 ≤ 200 + 含 `&truncated=1` |
| TC-07 极长 result | expr="1", res=200*'b' | 截断整个 payload 至 200 |
| TC-08 幂运算 | expr="2^10", res="1024" | `^` 不编码（encodeURIComponent 不编码 `^`） |
| TC-09 负数 | expr="-5", res="-5" | `-` 不编码 |
| TC-10 MAX 常量 | MAX_PAYLOAD_LENGTH=200 | 类型为 number |

### 5.2 端到端测试（模拟器 + hdc）
- TC-E2E-01：启动 OpenCalc → 输入 "1+2" → 按 = → 点击 "⎘" → 截图 + 验证 QR 像素非空
- TC-E2E-02：SharePanel 关闭 → 验证 PixelMap.release 被调用（可通过 harmonyos-ui-test skill 验证）

## 6. 兼容性 & 风险控制

| 风险 | 控制措施 |
|------|----------|
| qrcode Kit 不可用 | try/catch + Toast 提示 |
| AMOLED 主题下 QR 不可见 | QR 区域强制 `#FFFFFF` 白底 |
| PixelMap 内存泄漏 | onShareClose + onPageHide 双重 release |
| 长按显示屏冲突 | 长按作用在 Column 层；按钮 onClick 独立 |
| 测试环境无 hvigorw | 复用上一变更 Node 端口测试方案 |
| URL 编码不完整 | 用 ArkTS 标准 encodeURIComponent（已覆盖 `+/π/空格/` 等） |

## 7. 性能 & DFX

- **性能**：QR 生成由 HarmonyOS native 实现，预期 < 50ms
- **可靠性**：PixelMap 资源双重释放（onShareClose + onPageHide）
- **可维护性**：QR 内容生成独立为 QrCodeBuilder.ets，便于复用
- **可测试性**：buildSharePayload 是纯函数，100% 单元测试覆盖
- **安全性**：URL scheme 限定为 `opencalc://`，不会误触发其他 App
- **国际化**：QR 内容格式固定（opencalc scheme），未来如需支持 i18n 显示可在文本副本层扩展
