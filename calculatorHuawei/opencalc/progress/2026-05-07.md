# OpenCalc HarmonyOS — 迁移日志

## 2026-05-07

### 项目初始化
- 克隆 OpenCalc Android 源码 (12 files, 4,255 lines Kotlin)
- 分析: 0 第三方库, 🟢 Easy 难度
- 创建 HarmonyOS 项目骨架 → BUILD SUCCESSFUL

### Spec 文档
- ARCH_ANALYSIS.md: 完整架构分析 + C4 模型 + 迁移策略
- TASK_BOARD.md: 24 个原子任务分解 (A1-G2)
- DESIGN.md: 数据模型 + 技术映射 + 关键决策(ADR)

### 实现进度

| Task | 描述 | 状态 |
|------|------|:---:|
| A1-A4 | 项目骨架 + Index 占位 + Models | ✅ DONE |
| B1 | NumberFormatter (格式化/千分位/印度编号) | ✅ DONE |
| B2 | Expression (符号替换/隐式乘/√/%/!/括号补齐) | ✅ DONE |
| B3-B4 | CalcEngine (递归下降解析器 + 全部数学函数) | ✅ DONE |
| C1-C2 | PreferencesStore (8 key 读写 + JSON 序列化) | ✅ DONE |
| D1-D6 | CalculatorPage (UI: 显示+按钮网格+科学模式+错误处理) | ✅ DONE |
| E1-E3 | 历史记录 (List+ForEach+滑动删除+点击回填+长按复制) | ✅ DONE |
| F+G | 设置 + 主题 + 关于 | ⬜ TODO |
| — | 质量验证 | ⬜ TODO |

### 编译
- ✅ BUILD SUCCESSFUL (0 ERRORS, 5s)
- 7 WARN (deprecations + function throws)

### 已知问题
- execute_code write_file 反复损坏 .ets 文件 (pitfall 72/78 再现)
- Calculator.ets 因 file corruption 重写了 4 次
- 偏好存储的 async 初始化可能有时序问题
- 设置面板功能待补全 (boolean toggle 可用但未持久化)

### 下一步
- F1-F3: 设置页面 (偏好持久化 + 即时生效)
- G1-G2: 主题系统 + 关于页面
- 数学函数精度验证 vs Android 原版
- push GitHub
