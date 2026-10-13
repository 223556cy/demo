# 设计审视报告 - Issue #18 单位换算

## 1. 完整性评估

### 1.1 制品清单
- [x] `proposal.md` - 需求提案
- [x] `delta-spec.md` - 增量规格
- [x] `info.md` - 代码仓理解
- [x] `design.md` - 增量设计（合并 delta-design.md）
- [x] `todo.md` - 任务进度
- [ ] `new-arch.md` - **不适用**（无架构变更，step7 已跳过）

### 1.2 需求覆盖度
- SR-UC-01 自然语言换算输入 → design.md §2.1 + §2.2 ✅
- SR-UC-02 同维度校验 → design.md §2.2 convert 算法 + §5 ✅
- SR-UC-03 降级兼容 → design.md §2.3 onEquals 改造 + §3 数据流 ✅
- SR-UC-04 单位别名词典 → design.md §2.2 alias 列表 ✅
- SR-UC-05 温度特殊处理 → design.md §2.2 温度 affine 公式 ✅
- SR-UC-06 结果格式化 → design.md §3 NumberFormatter 复用 ✅
- SR-UC-07 历史记录 → design.md §2.3 onEquals history.push ✅
- SR-UC-08 错误提示友好 → design.md §5 错误处理矩阵 ✅

**覆盖度：100%**

## 2. 一致性评估

### 2.1 proposal → delta-spec
- 意图分类一致（requirement-add）
- MVP 子集一致（长度/质量/温度/时间）
- 验收标准一致

### 2.2 delta-spec → design
- 接口契约一致（NLParseResult / UnitConverter.convert 签名）
- 维度定义一致（4 维度 + base unit）
- FMEA 消减措施已映射到 design 错误处理

### 2.3 design → info（代码现状）
- 现有 onEquals 入口位置匹配（CalculatorPage.ets:198）
- 现有 import 模式匹配
- 现有 ErrorFlags 模式可扩展（design 选择不扩展以保持 MVP 简洁）
- 现有 common/ 不存在，design 新建合理

## 3. 规范性评估

### 3.1 格式规范
- [x] 章节结构完整（D1-D8）
- [x] frontmatter/todo.md 存在
- [x] 制品命名规范

### 3.2 命名规范
- [x] 模块名 PascalCase（NaturalLanguageParser, UnitConverter）
- [x] 文件名 PascalCase + .ets
- [x] 私有方法 camelCase
- [x] 常量全大写或描述性 PascalCase

### 3.3 描述清晰
- [x] 每个 API 有完整签名 + 返回值说明
- [x] 错误处理矩阵清晰
- [x] 数据流图覆盖三种路径

## 4. 风险与遗留

### 4.1 已知风险（已缓解）
| 风险 | 缓解 |
|------|------|
| 单位别名歧义（m=米/分钟） | 维度内精确 alias 匹配 |
| 温度不能用通用公式 | 独立 affine 分支 |
| NL parse 误判普通表达式 | parser 内严格正则 + null 降级 |

### 4.2 待确认（非 blocker）
- 跨维度错误信息文案：暂用"单位不匹配"，可在 rev-01 阶段调整
- UI 自动化测试依赖 hdc 真实可用性：若阻塞，fallback 单元测试

### 4.3 范围外确认
- 不做货币/体积/面积（与用户描述一致）
- 不做 i18n 全语种（中英 MVP）

## 5. 复杂度确认

| 维度 | 评估值 | 备注 |
|------|--------|------|
| 等级 | M | 中等 |
| 影响模块 | 3 | common/UnitConverter, common/NLParser, pages/CalculatorPage |
| 架构变更 | 否 | 不创建新 layer |
| 数据模型 | 是 | 新增 UnitDef 常量表（不影响现有 model） |
| 跳过制品 | new-arch.md | 无架构变更 |

## 6. 总结

✅ **通过** - 设计制品齐全、需求覆盖 100%、一致性、规范性均通过。无 blocker 级遗留问题。

进入 IMPLEMENTING 阶段。
