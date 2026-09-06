# Platydiff RFC

[English documentation](README.md)

本目录保存 Platydiff 已接受和提议中的设计决策。英文 RFC 是权威版本；中文翻译使用 `_zh.md` 后缀，并必须与英文原文保持一致。

## 状态定义

- **Proposed**：正在接受设计评审，尚未授权实现。
- **Accepted**：已获批准，可作为实现契约。
- **Implemented**：已经交付，并由兼容性测试覆盖。
- **Superseded**：已被其他 RFC 取代；必须链接替代它的 RFC。

## 索引

| RFC | 状态 | 决策 |
| --- | --- | --- |
| [0001](0001-comparison-outcome-and-diff-result_zh.md) | Accepted | 分离执行终态与已完成的差异结果，并定义 schema v1 的结果语义 |
| [0002](0002-development-phases-and-text-slice_zh.md) | Accepted | 为首个 Python/text 切片设置门禁，并把后续能力置于显式契约评审之后 |

计划中的行为在实现并完成验证前，必须继续明确标记为计划能力。
