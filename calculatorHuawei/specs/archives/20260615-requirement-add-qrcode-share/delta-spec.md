# 增量需求规格 — Issue #13 一键分享二维码

## 1. 需求背景

在跨设备协作场景下，用户需要在手机上使用电脑计算器刚刚算出来的算式与结果。当前只能在设备之间手动复制粘贴或重新输入。本需求提供"二维码分享"能力，实现算式+结果的快速跨设备迁移。

## 2. 需求范围

### 2.1 功能范围
- 在计算器显示屏提供"分享"入口
- 生成可被任意二维码扫描器解析的 QR 码
- 显示包含算式+结果的 QR 码模态层
- 内容格式遵循 opencalc:// 自定义 URL scheme

### 2.2 影响面
| 模块 | 影响 |
|------|------|
| CalculatorPage.ets | 新增 UI 状态、按钮、模态层 |
| QrCodeBuilder.ets (新增) | QR 内容生成工具类 |

## 3. 详细需求

### 3.1 用例清单

| UC 编号 | 名称 | 触发条件 | 主成功场景 | 异常/降级 |
|--------|------|---------|-----------|----------|
| UC-01 | 正常分享 | 用户有合法算式+结果，点击分享按钮 | 显示 QR 码模态层，内容可扫描 | 无 |
| UC-02 | 空表达式场景 | 用户未输入或已 AC | 分享按钮 disabled（灰色） | 点击无反应 |
| UC-03 | 错误状态场景 | 显示屏显示 errorMsg | 分享按钮 disabled | 点击无反应 |
| UC-04 | 关闭模态层 | 用户点击 ✕ 按钮 | 模态层消失，回到主屏 | 无 |
| UC-05 | 特殊字符场景 | 表达式含 `+ - × ÷ π e sin` | URL 编码正确，扫码可还原 | 无 |
| UC-06 | 超长表达式 | 表达式 + 结果 > 200 字符 | 截断至 200 字符，模态层提示"算式已截断" | UI 友好降级 |

### 3.2 功能性需求

#### FR-01 QR 内容格式
- **格式**：`opencalc://calc?expr=<URLEncoded expression>&res=<URLEncoded result>`
- **示例**：
  - 输入 `1+2`，结果 `3` → `opencalc://calc?expr=1%2B2&res=3`
  - 输入 `sin(π/2)`，结果 `1` → `opencalc://calc?expr=sin(%CF%80%2F2)&res=1`
- **字符约束**：仅 ASCII 字母数字 + `+ - * / . ( )` 等保留字符需要 URL 编码

#### FR-02 分享按钮位置
- 位置：DisplayPanel 内、expression 上方右侧
- 样式：图标字符（`⎘` 或 `⇪` 或 `📤`），与现有 ⚙ 设置图标风格统一
- 状态：`enabled`（黑色/深色）vs `disabled`（灰色，不响应点击）

#### FR-03 模态层 UI
- 居中浮层，宽度 80%，圆角 16
- 包含：
  - 标题 "分享到手机"（或"二维码分享"）
  - QR 码图片区域（至少 240x240 vp）
  - 算式 + 结果文本（QR 下方，便于人工识别）
  - 关闭按钮 ✕
- 背景：复用现有 getPanelBg() / getT1() / getT2() 主题 getter

#### FR-04 QR 码规格
- 错误纠正等级：M（中等，~15% 容错）
- 尺寸：240x240 vp
- 前景色：黑（#000000）；背景色：白（#FFFFFF），对比度足够扫码

### 3.3 业务规则

#### BR-01 启用条件
分享按钮在以下条件**同时满足**时启用：
- `expression.length > 0`（有输入）
- `errorMsg.length === 0`（无错误状态）
- `result.length > 0`（有结果，即按过等号）
- `qrPayload.length <= 200`（未超长截断）

#### BR-02 内容截断规则
当生成 payload > 200 字符时：
- 优先截断 `expr` 字段（保留 result 完整）
- 在模态层文本下方追加灰色提示："⚠ 算式过长已截断"

#### BR-03 URL 编码规则
- 使用标准 encodeURIComponent 语义
- 空格 → `%20`，`+` → `%2B`，`/` → `%2F`，`(` → `%28`，`)` → `%29`，`π` → `%CF%80`

### 3.4 UI/UX 规格

#### 分享按钮（DisplayPanel 内）
```
┌─────────────────────────────┐
│                  [⎘ 分享]   │  ← 新增图标
│      1+2+3+...              │  ← expression (右对齐)
│           6                 │  ← result
└─────────────────────────────┘
```

#### 模态层（SharePanel）
```
┌─────────────────────────────┐
│  二维码分享          ✕     │
│  ┌─────────────────────┐    │
│  │  ▓▓▓ ▓ ▓▓▓ ▓▓▓ ▓▓   │    │
│  │  ▓  ▓▓ ▓  ▓ ▓ ▓  ▓  │    │
│  │  ▓▓▓ ▓▓ ▓▓▓ ▓▓ ▓▓▓  │    │  ← QR 码 (240x240)
│  │  ▓  ▓  ▓  ▓ ▓ ▓  ▓   │    │
│  │  ▓▓▓ ▓▓ ▓▓▓ ▓ ▓▓▓   │    │
│  └─────────────────────┘    │
│  1+2+3 = 6                  │  ← 文本副本
│  (长按显示屏仍可复制结果)    │
└─────────────────────────────┘
```

### 3.5 可靠性 / FMEA 消减措施

| 故障模式 | 影响 | 严重度 | 改进措施 |
|---------|------|-------|---------|
| QR 内容含特殊字符导致生成失败 | 二维码无法扫描 | 中 | URL 编码 + 测试用例覆盖 `+`, `/`, `(`, `π`, `中文`（如有） |
| QR 内容超长导致 Kit 抛异常 | 模态层打开失败 | 中 | 截断至 200 字符 + try/catch + 错误提示 |
| QR PixelMap 资源未释放 | 内存泄漏 | 低 | 模态层关闭时显式调用 `pixelMap.release()` |
| 主题为 AMOLED 纯黑时 QR 背景为黑 | 无法扫码 | 中 | QR 区域强制使用白色背景（不受主题影响） |
| 长按显示屏手势与新按钮冲突 | 触发复制而非点击分享 | 低 | 按钮单独 onClick，长按手势作用在 DisplayPanel Column 层 |

### 3.6 性能要求
- QR 生成 < 200ms（HarmonyOS Kit 内部 native 实现，预期 < 50ms）
- 模态层切换帧率 ≥ 60fps（动画由 ArkUI 自动处理）

## 4. 接口契约

### 4.1 QrCodeBuilder.buildSharePayload
```typescript
/**
 * 生成 QR 码分享内容
 * @param expression 用户输入的算式（如 "1+2"）
 * @param result 计算结果（如 "3"）
 * @returns URL 编码后的 payload（如 "opencalc://calc?expr=1%2B2&res=3"）
 *          超长则截断 expr 并在尾部追加 "&truncated=1"
 */
export function buildSharePayload(expression: string, result: string): string
```

### 4.2 QrCodeBuilder.MAX_PAYLOAD_LENGTH
- 常量 `200` —— 单条 QR payload 最大字符数

### 4.3 QrCodeBuilder.PAYLOAD_PREFIX
- 常量 `"opencalc://calc?expr="` —— 自定义 scheme 前缀

## 5. 验收清单（可测试）

- [ ] AC-01：`buildSharePayload("1+2", "3")` 返回 `"opencalc://calc?expr=1%2B2&res=3"`
- [ ] AC-02：`buildSharePayload("sin(π/2)", "1")` 返回含 `%CF%80` UTF-8 编码
- [ ] AC-03：expr+res 拼接 > 200 字符时，返回值 ≤ 200 字符且含 `&truncated=1`
- [ ] AC-04：空 expression + 空 result 时返回 `"opencalc://calc?expr=&res="`（不抛异常）
- [ ] AC-05：CalculatorPage 分享按钮在 expression 为空时 disabled
- [ ] AC-06：CalculatorPage 分享按钮在 errorMsg 非空时 disabled
- [ ] AC-07：SharePanel builder 存在并接收 showShare 状态
- [ ] AC-08：单元测试覆盖 ≥ 8 个用例（payload 格式 / 编码 / 截断 / 空值）

## 6. 不涉及

- 网络通信、社交分享、API 调用
- 用户系统、权限申请
- 三方 QR 扫描库（用 HarmonyOS Kit）
- 历史记录条目的 QR 分享
- 接收端 App 还原逻辑
