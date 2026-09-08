# Automatic and binary comparison

[Chinese documentation](binary-comparison_zh.md)

Phase 2 implements the accepted [RFC 0003](rfcs/0003-automatic-detection-capability-resolution-and-binary-comparison.md) contract without adding a public plugin API.

Use `BinaryCompareSpec` or `platydiff binary` for exact byte comparison. The comparator opens path inputs once, rejects non-regular files, reads bounded chunks, compares actual bytes, and records SHA-256 only as provenance. `BinarySpan` values contain offsets and lengths, never source bytes. Change item and payload limits may truncate details but never weaken the exact relation or verdict.

Use `AutoCompareSpec` or `platydiff compare --type auto` to opt into bounded text/binary detection. The detector considers strict UTF-8, NUL, control characters, and an explicit `TextSource` signal. It does not use filenames, MIME databases, locale, or network services. The default minimum confidence is `800` and ambiguity margin is `100`; unavailable results ask the caller to select text or binary explicitly.

Omitting `--type` does not enable detection. Public plugin discovery, other modalities, stdin, directories, archives, and approximate binary similarity remain planned.

Pre-release schema v1 now accepts `auto` and `binary` specs, `binary_span` changes, and optional detection provenance. Phase 1 explicit-text payloads remain byte-for-byte unchanged; pre-release Phase 1 readers had no forward-compatibility guarantee for these new closed-union kinds.
