# UI 自动化测试报告 — Issue #18

## 基本信息

| 项目 | 内容 |
|------|------|
| 应用名称 | OpenCalc HarmonyOS 移植版 |
| 平台 | HarmonyOS (ArkTS) |
| 测试设备 | 模拟器 127.0.0.1:5555 |
| 测试日期 | 2026-06-17 |
| bundleName | com.darkempire78.opencalculator |
| HAP 版本 | entry-default-unsigned.hap (264KB, 含 UnitConverter + NaturalLanguageParser) |
| 测试工具 | hdc 3.2.0d (uitest dumpLayout JSON, uitest screenCap PNG) |

## 测试结果总览

| 用例 | 描述 | 状态 | 证据 |
|------|------|------|------|
| TC-1 | 100厘米转英寸 → 39.3701 | 🚫 阻塞: 无 TextInput | screenshot/02_after_text.png + dump/02_after_text.json |
| TC-2 | 30摄氏度转华氏度 → 86 | 🚫 阻塞: 无 TextInput | 同上 |
| TC-3 | 1+2 不被误判 → 3 | ⚠️ 部分验证: 2+3=5 PASS | screenshot/03_1plus2_result.png |
| TC-4 | 基础功能回归 (按钮 2+3) | ✅ PASS | screenshot/03_1plus2_result.png |

## 关键发现 (P0 阻塞)

### F-1: CalculatorPage 没有 TextInput 组件
**严重度**: P0 (核心功能无法从 UI 触发)
**证据**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets:408-410`:
  ```ts
  Text(this.expression.length > 0 ? this.expression : ' ')
  ```
  是 `Text` 组件,不是 `TextInput`。
- UI 树 dump (`dump/00_initial.json`) 扫描所有节点:0 个 `TextInput` / `TextArea` / `Search`
- 键盘只有按钮:0-9, +, -, ×, ÷, %, (, ), AC, ⌫, =, .
- 没有"厘米"/"转"/"英寸"/"摄氏度"/"华氏度"的输入入口

**影响**:
- 用户**无法**在 UI 里输入"100厘米转英寸"(issue 标题的核心需求)
- `UnitConverter` + `NaturalLanguageParser` 单元测试 32/32 PASS,但集成路径**用户不可达**
- `onEquals` 的 NL 优先分支**永远不会**被真实用户触发

**根因**:
- PLANNING/IMPLEMENTING/APPLYING 阶段**未识别**到 issue 描述的"输入框直接支持自然语言查询"要求新增 TextInput 组件
- design.md / proposal.md / delta-spec.md 误把"NL parse"作为唯一交付物,忽略了 UI 入口
- 单元测试只覆盖 parser/converter 纯函数,未覆盖 UI 集成

**修复建议** (下一个 PR):
- 在 CalculatorPage.DisplayPanel 区域把 `Text(this.expression)` 替换为 `TextInput({ text: this.expression })` + `onChange`
- 或新增一个"自然语言输入模式"切换按钮(切到 NL 模式时键盘隐藏,TextInput 显示)
- 单元测试 32/32 PASS 可以保留(parser/converter 是纯函数,与 UI 无关)

## 已验证项

### V-1: 基础计算器回归
- 操作:点 2 → 点 + → 点 3 → 点 =
- 预期:result = 5
- 实际:screenshot/03_1plus2_result.png 显示 expression="2+3", preview="5", result="5"
- 结论:**通过**,NL 分支未污染 CalcEngine 路径(与 todo.md AC-UC-14 期望一致)

### V-2: 实时预览 (issue-11)
- 观察:在键入"2+3"时 preview 立即显示"5"
- 结论:**通过**,preview 模式正常工作

## 阻塞诚实披露

按铁律 7,不伪造截图与日志。本次 UI 测试**未能**完成 issue #18 标题要求的 3 条验收用例(100厘米转英寸/30摄氏度转华富度/1+2 不被误判),原因是发现 P0 UX gap:calculator 缺 TextInput 入口。

后续如果要在 UI 层验证 NL 换算,必须先解决 F-1(新增 TextInput),否则单元测试 32/32 是唯一证据。

## 附件清单

```
ui-tests/
├── 01_ui_test_report.md            (本文档)
├── screenshot/
│   ├── 00_initial.png              (冷启动,display="0")
│   ├── 02_after_text.png           (尝试 uitest uiInput text "100cm",display 仍="0",证明无文本入口)
│   └── 03_1plus2_result.png        (2+3=5 回归 PASS)
└── dump/
    ├── 00_initial.json             (UI 树扫描:0 个 TextInput)
    └── 02_after_text.json          (UI 树扫描:0 个 TextInput)
```
