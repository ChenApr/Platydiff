# Platydiff RFC

[English documentation](README.md)

本目录保存 Platydiff 已接受和提议中的设计决策。英文 RFC 是权威版本；中文翻译使用 `_zh.md` 后缀，并必须与英文原文保持一致。

## 状态定义

- **Proposed**：正在接受设计评审，尚未授权实现。
- **Accepted**：已获批准，可作为实现契约。
- **Implemented**：已进入默认分支、与文档一致，并由要求的兼容性测试覆盖；
  发布状态另行记录。
- **Superseded**：已被其他 RFC 取代；必须链接替代它的 RFC。

## 索引

| RFC | 状态 | 决策 |
| --- | --- | --- |
| [0001](0001-comparison-outcome-and-diff-result_zh.md) | Implemented | 分离执行终态与已完成的差异结果，并定义 schema v1 的结果语义 |
| [0002](0002-development-phases-and-text-slice_zh.md) | Implemented | 为首个 Python/text 切片设置门禁，并把后续能力置于显式契约评审之后 |
| [0003](0003-automatic-detection-capability-resolution-and-binary-comparison_zh.md) | Implemented | 定义有界自动探测、确定性内部能力解析和精确二进制比较 |
| [0004](0004-human-review-ui-and-renderer-boundary_zh.md) | Proposed | 保持人类评审界面位于 validated outcome 下游，并分阶段规划 terminal、HTML、TUI 和 desktop 工作 |
| [0005](0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md) | Implemented | 定义显式第三方 discovery、版本化 SDK、确定性 capability execution 与兼容性证据 |
| [0006](0006-structured-data-comparison_zh.md) | Accepted | 在 schema v3 与独立授权交付门禁后定义显式 JSON/YAML、表格及稠密数组语义 |
| [0007](0007-image-comparison_zh.md) | Proposed | 定义 schema v4 的显式静态 PNG decoded-sample 切片，并延后 perceptual、artifact、plugin 与 detection 工作 |

计划中的行为在实现并完成验证前，必须继续明确标记为计划能力。
