# 自动探测与二进制比较

[English documentation](binary-comparison.md)

Phase 2 实现了已接受的 [RFC 0003](rfcs/0003-automatic-detection-capability-resolution-and-binary-comparison_zh.md)，但未增加公共插件 API。

使用 `BinaryCompareSpec` 或 `platydiff binary` 执行精确字节比较。比较器只打开路径一次，拒绝非普通文件，以有界 chunk 读取并比较真实字节；SHA-256 仅作为 provenance。`BinarySpan` 只含 offset 与 length，不含源字节。change 数量或 payload 限额可以截断明细，但不会弱化精确 relation 或 verdict。

使用 `AutoCompareSpec` 或 `platydiff compare --type auto` 显式启用有界文本/二进制探测。探测器只考虑 strict UTF-8、NUL、控制字符和 `TextSource` 显式信号，不使用文件名、MIME 数据库、locale 或网络服务。默认 minimum confidence 为 `800`，ambiguity margin 为 `100`；无法选择时要求调用者显式指定 text 或 binary。

省略 `--type` 不会启用探测。公共插件发现、其他模态、stdin、目录、archive 与近似二进制相似度仍是计划能力。

预发布 schema v1 现在接受 `auto`/`binary` spec、`binary_span` change 和 optional detection provenance。Phase 1 显式文本 payload 保持逐字节不变；预发布 Phase 1 reader 对这些新 closed-union kind 不提供前向兼容保证。
