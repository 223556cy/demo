# Info: 代码仓上下文 — Issue #9

> **Date**: 2026-06-11
> **Project**: opencalc-harmonyos (HarmonyOS 计算器)
> **Source Repo**: github.com/JungleTestLabs/opencalc-harmonyos
> **Migrated From**: github.com/clementwzk/OpenCalc (Android 3.2.1)

---

## 1. 项目结构

```
D:/huawei/Demo/worktrees/issue-9/
├── opencalc/                                 # HarmonyOS 工程根
│   ├── AppScope/                             # 应用作用域
│   ├── build-profile.json5                   # 工程级构建配置
│   ├── oh-package.json5                      # 工程级依赖（声明 @ohos/hypium + @ohos/hamock）
│   ├── entry/                                # Entry 模块
│   │   ├── build-profile.json5
│   │   ├── hvigorfile.ts
│   │   ├── oh-package.json5                  # 模块依赖
│   │   └── src/main/ets/                     # ArkTS 源码
│   │       ├── calculator/
│   │       │   ├── Calculator.ets            # 计算引擎（100 行）
│   │       │   ├── Expression.ets            # 表达式预处理（298 行）★ 关键
│   │       │   └── NumberFormatter.ets       # 数字格式化（140 行）
│   │       ├── model/
│   │       │   ├── ErrorFlags.ets            # 错误标志位（静态）
│   │       │   └── Models.ets                # 数据模型
│   │       ├── pages/
│   │       │   ├── CalculatorPage.ets        # 主计算器页（415 行）★ 关键
│   │       │   └── Index.ets
│   │       ├── preferences/
│   │       │   └── PreferencesStore.ets
│   │       └── entryability/
│   │           └── EntryAbility.ets
│   ├── spec/                                 # 既有规格
│   │   ├── ARCH_ANALYSIS.md
│   │   ├── DESIGN.md
│   │   └── TASK_BOARD.md
│   ├── docs/
│   │   ├── 增强需求-修改分析.md
│   │   └── 增强需求-一句话需求列表.md         # Issue #9 原始出处
│   ├── progress/2026-05-07.md
│   ├── MIGRATION_SUMMARY.md
│   └── README.md
├── specs/changes/20260611-requirement-add-percent-button/  # 本次变更目录
│   ├── todo.md
│   ├── proposal.md
│   ├── delta-spec.md
│   └── info.md（本文件）
```

## 2. 关键文件清单

| 文件 | 行数 | 角色 | 改动点 |
|------|------|------|--------|
| `entry/src/main/ets/calculator/Expression.ets` | 298 | 表达式预处理；macOS 风格 % 在 `getPercentString` | **可能小改**（如果发现 bug） |
| `entry/src/main/ets/pages/CalculatorPage.ets` | 415 | UI；% 按钮在 ButtonGrid 行 1 列 2 | **不改**（按钮已存在） |
| `entry/src/main/ets/calculator/Calculator.ets` | 100 | 计算引擎 | **不改** |
| `entry/oh-package.json5` | - | 模块依赖 | 可能需加测试模块引用 |
| `opencalc/oh-package.json5` | - | 工程依赖（已有 @ohos/hypium@1.0.15） | **不改** |

## 3. 现有百分号实现（已存在，需验证正确性）

### 3.1 表达式预处理入口
`Expression.ets:8-23` 的 `getCleanExpression` 流程：
```
input → replaceSymbols → addMultiply → [条件]getPercentString → replaceAll('%','/100') → addParenthesis → output
```

### 3.2 `getPercentString`（行 169-255）
关键逻辑（行 245）：
```typescript
const base: string = result.substring(0, opPos).trim()
const num: string = result.substring(opPos + 1, i)
result = base + result.charAt(opPos) + base + '*(' + num + '/100)' + result.substring(i + 1)
```

→ 把 `50+10%` 转为 `50+50*10/100` → 计算得 55 ✅

### 3.3 UI 入口
`CalculatorPage.ets:278`：
```typescript
Row() { this.BtnActPct('AC'); this.BtnOpPct('%'); this.BtnOpPct('('); this.BtnOpPct(')'); this.BtnOpPct('÷') }
```

→ `%` 按钮存在，点击 → `onOp('%')` → 追加到 expression

## 4. 测试基础设施现状

- `@ohos/hypium@1.0.15` 已声明在 `opencalc/oh-package.json5` devDependencies
- `@ohos/hamock@1.0.0` 已声明
- **未发现任何 .test.ets 文件**
- 无现成的 hvigorw test 配置

→ **首次建立测试基础设施**。需要：
1. 创建 `entry/src/test/` 目录
2. 写 `Expression.test.ets` 使用 `describe` / `it` / `expect` 模式（hypium 风格）
3. 配置 `entry/build-profile.json5` 启用 test target
4. 验证 `hvigorw test` 命令可用

## 5. ArkTS 限制

- `Number` 仅 64-bit 浮点（15-17 位精度）
- 无 `BigDecimal` 类
- 无 `RegExp`
- 字符串操作只能 `substring` / `indexOf` / `charAt`，不能 `match` / `split(re)`
- 数组只有 `forEach` 没问题
- 泛型 `Array<T>` 可用
- 类的 `static` 字段需初始化为字面量数组

## 6. 既有约束

- 0 三方库
- 单一 `EntryAbility`
- 主题：默认浅色 / 暗色 / AMOLED（settings 可切）
- 偏好持久化：`PreferencesStore.ets`

## 7. 编译/运行验证手段

| 手段 | 状态 | 说明 |
|------|------|------|
| `hvigorw clean` | 可尝试 | 清理构建 |
| `hvigorw build` | 可尝试 | 构建 HAP |
| `hvigorw test` | 需先配置 | 跑单元测试 |
| 模拟器/真机运行 | 受限 | 当前环境可能无设备 |

## 8. 与原 Issue 的对应

| Issue #9 需求 | 现状 | 行动 |
|---------------|------|------|
| 加一个百分号按钮 | ✅ 已存在（行 278） | 无需添加 UI |
| 输入 50+10% 自动算出 55 | ✅ 逻辑已实现（行 245） | TDD 验证 + 边界补强 |
| UX 增强 ⭐ | ✅ | - |
| 日常高频 | ✅ | - |

## 9. 决策点

| 决策 | 选择 | 理由 |
|------|------|------|
| 是否需要新增 UI 按钮？ | **否** | 按钮已存在 |
| 是否需要重写 `getPercentString`？ | **视 TDD 结果定** | RED 阶段先写测试，发现 bug 再 GREEN |
| 测试放在哪？ | `entry/src/test/ets/calculator/Expression.test.ets` | 跟源码目录对齐 |
| 测试目标？ | `Expression.getCleanExpression` 的 percent 行为 | 黑盒、纯函数、易测 |
| 是否跑 `hvigorw test` 真实执行？ | **是**（铁律 7） | 不准伪造输出 |

## 10. 待办

- [ ] 验证 `hvigorw test` 在当前环境是否可用
- [ ] 如不可用，配置 `entry/build-profile.json5` 的 test sourceSet
- [ ] 写 RED 阶段测试
- [ ] 跑测试，捕获现状
- [ ] 根据 RED 决定 GREEN 改什么
