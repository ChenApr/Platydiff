# 算法来源

[English documentation](algorithm-references.md)

## `text.myers.linear_space.v1`

Platydiff 的文本编辑引擎独立实现了 Eugene W. Myers 在论文 “An O(ND)
Difference Algorithm and Its Variations,” *Algorithmica* 1, 251–266 (1986),
[doi:10.1007/BF01840446](https://doi.org/10.1007/BF01840446) 中描述的
middle-snake 分治改进。实现没有复制其他实现的源代码、注释、测试或文档措辞。

该算法用于规范化 `TextLine` 值的序列，并返回只包含 insertion 和 deletion 的
最短脚本。Platydiff 另外把固定的 deletion-first 平局规则、公共前后缀剥离、显式
任务栈和确定性工作计数定义为项目行为。

已知限制与失败模式：

- 最坏情况耗时同时随输入大小和编辑距离增长；
- 重复行可能存在多个同样短的脚本，因此 Platydiff 的稳定平局规则属于可观察行为；
- 算法比较完整规范化行，不提供词级或字符级相似度；
- 确定性工作预算耗尽时返回 `failed/compare_resource_limit`，不使用 fallback，
  也不返回 partial result。

实现按项目 Apache-2.0 许可证分发。论文仅作为算法来源引用，不在项目中重新
分发。本记录不构成专利意见；发布审查必须针对预期司法辖区重新评估相关权利要求。
