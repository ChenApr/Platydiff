# RFC 0004：人类评审 UI 与 Renderer 边界

[English documentation](0004-human-review-ui-and-renderer-boundary.md)

- 状态：Proposed
- 日期：2026-09-07
- 路线决策备案日期：2026-09-09
- Owners：Platydiff 维护者
- 实现 owner：等待 UI 的单独实施授权后指派

## 摘要

本 RFC 提议 Platydiff 的人类评审展示架构。用户于 2026-09-09 批准 U1-U7 作为
路线方向：首个候选是改进 terminal renderer 并增加 self-contained HTML report；
只有得到实际证据后，才继续考虑可选 TUI，随后再考虑本地 Web 或桌面应用。该批准
只记录方向与边界，不授权 UI 实施或排期。

每种界面都消费经过验证的 `CompareOutcome`；renderer 或 UI 不得重新计算 relation、
verdict、fidelity、metric、policy evaluation、change completeness 或 problem 含义。
UI 可以组织、筛选和格式化已有事实，但不能成为第二个比较引擎。

## 边界与数据流

要求的方向为：

```text
CompareOutcome schema JSON
          |
          v
strict schema validation and typed construction
          |
          v
internal read-only UI view model
          |
          +--> terminal renderer
          +--> self-contained HTML renderer
          +--> optional TUI
          `--> future local web or desktop shell
```

进程内 Python caller 可以从类型化 `CompareOutcome` 开始；序列化输入必须先通过
同一个 strict schema parser，再构建 view model。原始 dict 和未经验证的 extension
payload 不得进入 template。

内部 view model 只用于展示，不是公共 interchange schema。它至少表示：

- outcome state 与稳定 problem 信息；
- 不重新解释的 relation、verdict 和 fidelity；
- summary count、metric 与 policy evaluation；
- `ChangeSet` completeness、returned/omitted count、selection 和 limits；
- text hunk、binary span，或明确降级的通用 extension-change 摘要；
- 按 stage 与 severity 分组的 diagnostic；
- execution stage、capability attempt、transformation、comparator/algorithm 版本、
  input hash 和资源 limit/usage；
- 在显式提供安全 artifact-root resolver 前，只作为 inert metadata 的 artifact ref。

允许格式化数值、在可查看完整值时缩写 hash，以及为导航索引已有 change。禁止推导
新 verdict、similarity、change count 或隐藏 normalization。

## 用户状态与信息架构

每个 surface 必须清晰区分：

- `completed/equal/pass`；
- `completed/different/fail`；
- 未来已接受 policy 可能产生的 `completed/*/warn`；
- full 与 degraded fidelity；
- complete、truncated 与 partial change details；
- `unavailable` capability/detection outcome；
- `failed` execution outcome；
- renderer/view-model validation failure，它不是 comparison outcome。

顶部摘要展示 outcome、verdict、relation、fidelity、source label、schema version 和
change-detail completeness。颜色可以强化状态，但不能成为唯一信号。未知 extension
change 以其 namespaced kind 与 plugin ID 展示为不受支持的结构化详情；UI 不得猜测
其含义。

completed view 按如下顺序组织：

1. decision summary 与显式 truncation/degradation banner；
2. change navigation 与模态专属 detail；
3. metric 与 policy evaluation；
4. diagnostic；
5. provenance、execution stage、capability attempt 与 resource usage；
6. inert artifact-reference inventory。

failed 与 unavailable view 先展示 stable code、safe message、stage、retryability 和
非敏感 details，再展示 execution trail；不得渲染空或伪造的 `DiffResult`。

## 文本评审体验

Text hunk 保持 RFC 0002 的一基行位置和来源顺序。每行展示 before/after line number、
operation（`equal`、`delete` 或 `insert`）、content 和 line-terminator state。UI 必须
在不修改内容的前提下区分 LF、CRLF、CR 和 missing final newline。

可选 display aid 可以显示 space、tab、trailing whitespace、BOM 和 control character。
它们是带显式 legend 和关闭状态的 renderer transform；不得改变存储行、comparison、
relation、metric 或 verdict。bidirectional control 和其他 terminal/HTML control
character 必须可见转义或隔离，避免显示顺序冒充逻辑内容。

导航使用 `change-1` 等 view-local 稳定 anchor；它们不是持久 change ID。允许前后
链接、hunk index 和可获得键盘焦点的 heading。search/filter 只有在 UI 明示展示筛选
已开启，且仍可访问全部 returned set 时，才可以隐藏行。

## 二进制评审体验

每个 `BinarySpan` 是一个可导航 change。UI 显示 before/after 的十进制 byte offset 与
length，并只根据经过验证的 length 零/非零形状给出 replacement、insertion 或 deletion
展示标签。可选十六进制 offset 是同一位置值的格式化结果，而不是第二个 location。
binary navigation 保持来源顺序，并清晰区分最终 trailing insertion/deletion。

U1 永远不显示、猜测、decode、preview 或 embed span 覆盖的 bytes；不提供 text/hex
dump，也不读取原始来源。summary、metric、strict-equality evaluation、hash、truncation
和 resource usage 只来自 validated outcome。malformed span 或非法 binary collection
必须阻止 view-model 构建，不能产生 partial UI。

## 交付顺序

### UI-U1：terminal 改进与 self-contained HTML

近期提议为：

- 保持现有安全 terminal output，并增加更清晰的状态 banner、对齐 hunk gutter、
  terminator/whitespace legend 和紧凑 provenance；
- 从同一个 view model 生成 self-contained、无 JavaScript 的 HTML document；
- 使用 semantic HTML landmark、原生 details/summary disclosure、fragment navigation、
  print style 和 responsive CSS；
- 不嵌入 remote font、script、analytics、image 或 stylesheet；
- 除非独立 dependency review 证明标准库实现不安全或不可维护，否则不新增 runtime
  dependency。

提议的 CLI 形式在接受前仅作说明：

```text
platydiff ... --format html --output report.html
```

HTML 应要求显式 output path，在用户明确选择前拒绝意外覆盖，并在目标目录原子发布
完整文件。no-overwrite 与 overwrite 算法在本地文件安全章节定义。它仍是 renderer
output，而不是 `DiffResult.artifacts` item。CI 可以把结果文件发布为 build artifact；
Platydiff 本身不上传。

### UI-U2：Phase 3 或 4 之后的可选 TUI

只有真实 text、binary，以及至少一个 structured 或 plugin-provided change shape
验证过 view model 后，才考虑 TUI。它可增加 virtual scrolling、hunk folding、filter、
side-by-side/narrow layout 和 keyboard navigation。它必须是 optional extra，不能让
core 或 basic CLI 依赖 terminal framework。

### UI-U3：多模态证据后的本地 Web 或桌面端

本地 Web 或 desktop shell 延后到 image/PDF/audio/video 工作表明实际需要哪些
artifact preview、synchronized navigation 和 large-result interaction 后再决定。
它必须复用 validated view model 与 renderer test。如果选择 browser server，只绑定
loopback，使用不可猜 session token，默认不接受任意 upload，也不打开显式 root 外的
artifact path。desktop packaging、code signing、auto-update 和 embedded-browser
license 需要独立评审。

UI-U2 与 UI-U3 是 roadmap 假设，不是自动后继阶段，也未获实现授权。

## 可访问性与交互契约

HTML 与未来 interactive surface 必须提供：

- semantic landmark 与正确 heading order；
- 对表格内容使用带 caption/header 的真实 table 或 list；
- WCAG 2.2 AA contrast 目标，并用文字/icon 而非只用颜色表示状态；
- 完整 keyboard access、visible focus、skip link，且无 keyboard trap；
- 不要求 hover、motion 或 pointer-only gesture；
- reduced-motion 支持且不自动播放 animation；
- responsive reflow，不在窄屏强制 side-by-side diff；
- 使用本地 CSS variable 与 `prefers-color-scheme` 自动提供 light/dark style；由于 U1
  不含 script，report 内 theme selector 延后；
- 可复制的逻辑文本与可见 whitespace marker 分离；
- 为 line number、insertion、deletion、diagnostic 和折叠 section 提供 accessible label。

初始 HTML 可使用无需 JavaScript 的 browser-native fragment link 和 disclosure widget。
U1 不提供 custom live search、filter、sort、persisted preference 或 report 内 theme
switch；用户仍可使用 browser Find、fragment navigation、disclosure control、system
theme 与 print CSS。未来 TUI 必须发布并测试 keyboard map；提议默认 `j/k` 或 arrow
移动、`n/p` 前后 change、`/` 搜索、`Enter` 展开、`q` 退出。shortcut 必须有可发现
替代方式，且不能遮蔽 terminal interrupt 行为。

## 大结果行为

UI 只展示 comparator 返回的有界 `ChangeSet`，并在 change list 前展示 total、returned、
omitted count 和 `limit_reason`。它不能获取、重新计算或暗示被省略的 detail。

View-model 构建和 terminal rendering 对 returned payload size 为线性。HTML output 有
独立确定性 output-byte limit；超出时是 renderer failure，不能修改 completed comparison
outcome。renderer 可为了保持自身预算省略可选 presentation index，但必须说明 navigation
aid 被省略，并保留每个 returned change，否则安全失败。TUI virtualization（如实现）
只作用于已受限的 returned set。

## HTML 与本地文件安全

UI 把每个 label、line、message、diagnostic detail、plugin field、URI 和 media type
都视为不可信。

- 使用与上下文匹配的 text/attribute escaping；不得把不可信值拼接进 HTML、CSS、URL
  或 terminal control sequence。
- U1 不含 script，并在 HTML 前部包含 `<meta http-equiv>` CSP：
  `default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none';
  form-action 'none'`。meta CSP 可执行这些 fetch/form/base 限制，但不能执行
  `frame-ancestors`；因此刻意不写该 directive。
- 不使用 `innerHTML`、executable template、remote asset、inline event handler、form、
  iframe 或 automatic navigation。
- U1 中 artifact URI 只作为 inert text。未来 link 需要 RFC 0001 safe artifact-root
  resolver、hash verification 与 media-type allowlist。
- report 按设计包含 comparison content；文档必须警告用户：发布 CI artifact 可能泄露
  source text、label、hash、diagnostic 和 provenance。
- report 排除绝对本地路径、environment variable、username、temporary path、token 和
  stack trace。
- standalone `file://` report 没有可信 HTTP response header，可能被其他 local content
  frame。用户应把它作为独立文件打开。CI 或未来 local HTTP server 提供 report 时，
  必须增加 response header
  `Content-Security-Policy: frame-ancestors 'none'`（也可增加
  `X-Frame-Options: DENY` 作为 legacy defense）。meta CSP 是纵深防御，不是完整 sandbox；
  browser extension、browser vulnerability、screenshot、copied content 和用户主动
  发布 report 仍是 residual risk。
- 两种模式都固定一次已存在 parent directory，并在平台支持时相对同一个 directory
  handle 完成 temporary creation 与 publication。它们先创建新的 `0600` temporary file
  （支持平台上的 `0600` 等价 owner-only access），flush、在支持时 `fsync`，并在发布前
  close。如果 available platform primitive 无法约束 parent-directory replacement 或
  final-component no-follow 行为，renderer 必须安全失败，不能弱化契约。默认
  no-overwrite mode 使用 exclusive/no-follow 语义，
  把已完成 temporary inode 原子 link 到 absent target，然后删除 temporary name。如果
  filesystem/platform 不能保证该 no-clobber installation，renderer 必须安全失败，
  不得 fallback 到 check-then-replace。默认模式下，已有 file、directory 或 symlink
  始终失败。
- 显式 overwrite mode 仍不打开或 follow target。它拒绝观察到是 symlink 的 target，
  随后用完成的 temporary file 原子替换 directory entry。竞态中被替换成 symlink 仍
  安全，因为 replace 作用于 entry 而非 referent。directory target 和不支持 atomic
  replace 的 filesystem 必须失败。在可用时执行 directory `fsync`；缺少 directory
  `fsync` 只削弱 crash durability，不削弱 no-clobber 或 symlink safety，并作为平台
  limitation 报告。

## Theme 与视觉语言

report 应像科学评审工具，而不是装饰性 dashboard。使用克制的 system-font stack、
高密度但易读的 spacing、monospace diff content、清晰 hierarchy，以及稳定 semantic
token 表示 pass、warn、fail、unavailable、insertion、deletion、diagnostic 和 muted
provenance。theme 只改变 presentation token，不改变文字或含义。

UI-U1 不引入 custom font、icon package、CSS framework 或 chart library。任何后续
dependency 都要评审 purpose、optionality、license、size、platform、security、maintenance
和 no-dependency alternative。icon 必须有 text label 或 accessible name，且具有再分发
许可。

## 测试与接受门禁

UI-U1 要求：

- 覆盖所有 outcome、fidelity、completeness、metric-value、problem、diagnostic、attempt、
  artifact-reference、text-hunk 与 binary-span state 的共享 view-model test matrix；
- 从相同 validated outcome 生成 terminal 与 HTML golden test；
- 对 HTML、attribute、control、bidi text、plugin payload、URI、label 和类似
  `</script>` 的字符串进行 adversarial escaping test，即使 U1 不含 script；
- newline、BOM、tab、trailing space、missing-final-newline、long-line、Unicode 和
  narrow-terminal fixture；
- binary replacement/insertion/deletion span、zero/large/chunk-boundary offset、
  truncated span list、原始 source file 缺失，以及 renderer 不读取或输出 source byte
  的证明；
- keyboard-only、screen-reader structure、contrast、reflow、print、light/dark 和
  reduced-motion review；
- complete/truncated/partial 与 renderer-byte-limit test；
- atomic-write、overwrite、symlink、permission 与 local-path redaction test；
- 除显式规范化的 execution timestamp 外，输出保持确定性；
- 现有 JSON snapshot 与 CLI exit 不变；
- Ruff、strict mypy、完整 pytest、build、package-content inspection 和 CI。

Accessibility automation 可以补充但不能替代 keyboard 与 screen-reader review。若未来
引入 browser-specific snapshot tooling，必须是带固定 provenance 和 license review 的
development-only dependency。

## 提议的 commit 与 owner 门禁

本 RFC 为 `Proposed` 时不指派 UI owner。若 UI-U1 被单独接受，使用以下 commit：

1. `refactor(renderers): add a validated outcome view model`
   - 门禁：每种 schema-v1 state 都不经语义重算完成映射；两个现有 renderer 保持兼容。
2. `feat(terminal): improve human review navigation and detail`
   - 门禁：safe control rendering、narrow layout、状态区分与现有 exit behavior 通过。
3. `feat(html): add a self-contained accessible report`
   - 门禁：无 JavaScript meta CSP 及已记录 framing residual risk、escaping、竞态安全
     no-clobber/overwrite output、binary span、accessibility structure、deterministic
     snapshot 和 renderer limit 通过。
4. `docs: document local and CI review reports`
   - 门禁：双语 example、disclosure warning、browser/platform note 和 dependency/license
     影响与已验证行为一致。

不得把 UI-U2 或 UI-U3 与 UI-U1 合并。merge 前，独立 review 必须确认 view model 不
重新解释 RFC 0001，恶意内容不能逃逸其上下文，且 JSON 行为保持兼容。

## 已批准的路线决策

用户于 2026-09-09 批准 U1-U7 作为路线方向。该批准不会把本 RFC 从 `Proposed`
改为其他状态，也不授权实施：

| ID | 决策 | 已批准路线边界 | 约束对象 |
| --- | --- | --- | --- |
| U1 | 首个美化 surface | 从同一 view model 改进 terminal 并增加 self-contained HTML | UI-U1 范围 |
| U2 | HTML 行为 | 无 JavaScript，以原生 anchor/disclosure、可兑现 meta CSP 和明确的 file framing 限制实现 | 安全架构 |
| U3 | 文件交付 | 要求 `--output`；默认 atomic no-clobber；显式 entry-replacement overwrite；不支持时安全失败 | CLI 与文件系统行为 |
| U4 | Dependency budget | UI-U1 只用标准库与 embedded CSS | packaging/license 门禁 |
| U5 | 排期 | 只有 Phase 2 schema 决策完成后，UI-U1 才具备申请单独授权的条件；其 view-model 设计可评审 Phase 2 | 实现顺序 |
| U6 | TUI framework | 延后到 Phase 3 或 4 提供证据且 UI-U2 被接受后选择 | optional dependency |
| U7 | Desktop/local web | 延后到测得多模态 artifact requirement 后选择 shell | UI-U3 架构 |

只有已接受的 Phase 2 schema 契约进入 `main` 且足够稳定后，UI-U1 才能另行申请用户
实施授权。UI-U2 与 UI-U3 还需要各自的后续证据与授权。本次路线备案没有批准任何
UI code、dependency、owner 或交付排期。

## 后果

本提议在不把比较真值耦合到具体 UI toolkit 的前提下，为人类提供美化评审路径。
static report 易于本地检查或在 CI 留存，而严格边界使 machine JSON 继续作为持久契约。
延后更复杂 shell，可避免当前 text-only 假设过早固化为多模态界面。
