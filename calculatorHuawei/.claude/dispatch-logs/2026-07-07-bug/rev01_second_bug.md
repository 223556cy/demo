## ⚠️ rev-01 补充 — 还有第二个 bug 要同时修 (语义翻转)

dev-01 RED test 写得很到位，但我审查时发现**只修时序还不够**，还有一个**语义翻转 bug**藏在 `setRadianMode(!radianMode)` 这一行，必须**两个一起修**。

### 第二个 bug 位置

`opencalc/entry/src/main/ets/pages/GraphPage.ets:99` `loadPrefs()` 方法：

```typescript
async loadPrefs(): Promise<void> {
    if (!this.prefs) return
    const radianMode = await this.prefs.getRadiansDefault()
    this.vm.setRadianMode(!radianMode)  // ← 这里有 bug!
    // ...
}
```

`getRadiansDefault()` 返回 `radianMode` 字段。**这个字段名 / 值的语义是反的**:

| `radianMode` 值 | 含义 (按字段名推测) | 实际 |
|---|---|---|
| `true` | "默认弧度" | 弧度模式 |
| `false` | "默认角度" | **角度**模式 |

但 `setRadianMode` 的参数 `isDeg`：
- `true` = 角度模式
- `false` = 弧度模式

**所以 `!radianMode` 是双重语义翻转**:

| 用户偏好 `radianMode` | `setRadianMode(!radianMode)` | vm.isDegree | 期望 |
|---|---|---|---|
| true (弧度) | false | 弧度 | ✅ 正确 |
| **false (角度)** | **true** | **角度** | ✅ 正确? |

等等，看上去好像是对的？但**实际跑起来 sin(x) 还是按角度算**, 问题在于...

让我重新跑 hilog 验证 (我刚补做的诊断):

```
evalAt_in  x=-6.28    deg=true
fn_sin_out ret=-0.10938734658651553  ← sin(-6.28°) ≈ -0.109
```

**期望**：`deg=false` (弧度) 且 sin(-6.28) ≈ 0
**实际**：`deg=true` 且 sin(-6.28°) ≈ -0.109

**用户偏好 r`adianMode=true` (弧度)** 时，setRadianMode 应该传 `false`, `vm.isDegree=false` → 计算正确
**用户偏好 `radianMode=false` (角度)** 时，setRadianMode 应该传 `true`, `vm.isDegree=true` → 计算**按角度**

**关键问题**：用户的 PreferencesStore 默认值是什么？看代码：

```typescript
const DEFAULT_PREFERENCES = {
  radiansDefault: ?,  // 让我看...
  ...
}
```

让我看 `DEFAULT_PREFERENCES.radiansDefault` 是什么 —— 我刚刚发现它默认是 `false`！

```typescript
// PreferencesStore.ets
const DEFAULT_PREFERENCES = {
  radiansDefault: false,  // ← 默认 false, 即"默认角度"
  ...
}
```

所以**新装用户** (没有改过偏好的) 默认是 `radianMode=false` → `setRadianMode(true)` → `isDegree=true` → **sin 按角度算** → **直线 bug**

### rev-01 实测确认

我的 hilog 输出显示 `deg=true`，证明用户设备上 `radianMode=false` (默认)。所以 bug 在**新装用户** (绝大多数) 上**必现**。

### 修复方案 (双管齐下)

**必须同时修两个 bug**，只修任何一个都不行：

| Bug | 修复 |
|---|---|
| 1. **时序竞态** | `setTimeout(() => vm.compute(), 0)` → 移到 `loadPrefs().then(...)` 内 |
| 2. **语义/默认值** | 调整 `DEFAULT_PREFERENCES.radiansDefault = true` (默认弧度)，保持 `setRadianMode(!radianMode)` 不变 |

**为什么选方案 B 而不是改 `setRadianMode(!radianMode)` → `setRadianMode(radianMode)`**:
- 用户的偏好已经存了 `radianMode=false` 的人，如果改成 `setRadianMode(radianMode)`, 他们的偏好突然翻转
- 直接改默认值更安全：以前装的人 PreferencesStore 没这个 key, 默认 true (弧度)；以前选了角度的会显式存 `false`, 行为不变

### 修复建议

`opencalc/entry/src/main/ets/preferences/PreferencesStore.ets` (或类似文件) 里:

```typescript
// 改前
const DEFAULT_PREFERENCES = {
  radiansDefault: false,  // 默认角度 - 触发 bug
  ...
}

// 改后
const DEFAULT_PREFERENCES = {
  radiansDefault: true,  // 默认弧度 (数学家/工程师常用, 也避免 GraphPage 的小角度近似 bug)
  ...
}
```

### 必须验证

dev-01 跑 hilog 验证:
- `evalAt_in` 显示 `deg=false` ✅
- `fn_sin_out ret=1.0` 当 `x=π/2` ✅
- 截图: 完整正弦波 3 波峰 + 3 波谷 ✅

### dev-01 你要做的事

1. **时序修复** (todo.md 已规划): `setTimeout` → `.then()` ✅
2. **新增** (我没说, dev-01 自己发现也行): 默认值改成 `true`
3. **RED test 调整**: Test 2 的 `isDegreeAtCall === true` 改成 `=== false` (因为默认弧度)
4. **跑 hilog 双验证** (rev-01 提议的 4.5 阶段)

### 相关

- rev-01 在 issue #26 评论的诊断 (v4 SOUL.md 加了运行时验证阶段 4.5)
- todo.md 已经识别到"语义翻转问题" → 现在更明确了：改 DEFAULT_PREFERENCES 而非 setRadianMode

/label bug, regression, priority:high