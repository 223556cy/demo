# 错误监控报告

## 会话信息
- 会话描述：{description}
- 会话类型：{aid-workflow | 自由会话}
- 审查日期：{YYYY-MM-DD}
- 项目域：{arkts | workflow | toolchain | ...}
- 关联目录：{specs/changes/YYYYMMDD-type-name/ | N/A}

## 检测到的错误

### 错误 1
- **分类**: {CG | AD | WP | ET | DK | TS | UD}-{序号}
- **严重度**: {high | medium | low}
- **阶段**: {PLANNING | IMPLEMENTING | APPLYING | 自由编码 | 调试}
- **描述**: {发生了什么}
- **上下文**: {相关代码/命令/输出片段}
- **根因分析**: {为什么发生 — Agent 缺少什么知识或做了什么错误假设}
- **修复方式**: {如何修复的}
- **可泛化**: {yes | no}
- **模式描述**: {如果 yes，描述泛化后的模式}

### 错误 2
...

## 统计
- 总错误数：{N}
- 按分类：CG:{n}, AD:{n}, WP:{n}, ET:{n}, DK:{n}, TS:{n}
- 按严重度：high:{n}, medium:{n}, low:{n}
- 新模式提取：{N} 条
- 已知模式命中：{N} 条

## 知识库更新
- 新增模式：{ID: 描述} 列表
- 更新模式（频次+1）：{ID: 描述} 列表
- 本地指南已刷新：{domain} 列表
