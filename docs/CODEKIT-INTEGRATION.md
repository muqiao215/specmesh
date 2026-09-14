# Optional independent machine port (draft)

Product boundary (2026-09-15): SpecMesh develops and releases independently. CM/History/Orca integration is not a required deliverable or acceptance gate. CM adapter descriptions below preserve historical compatibility context, not a mandate for synchronized host changes; use the direct standalone commands below. Existing public contracts remain unchanged.

Unreleased handoff candidate: `dirty_coverage.scope` names the selected task subtree and selected files; `outside_scope` is always `unknown`. `is_clean` is scoped, never a whole-worktree claim. Dirty symlinks and aliased subtrees are unsupported and produce blocked material instead of retaining their target bytes. The legacy request/result contracts and state enums are unchanged.

SpecMesh's normative file convention remains `SPEC.md`. This optional Python 3.11+ POSIX profile exposes the same project-continuity boundary to tools without adding a CM dependency, transcript database, Agent runtime or required daemon. Markdown-only users need no new runtime or platform restriction. Executable snapshots require descriptor-relative opening and `O_NOFOLLOW`; unsupported platforms declare `supported: false`.

```sh
python3 -B -m specmesh_port --capabilities
python3 -B -m specmesh_port --allowed-root /absolute/project < request.json
python3 -B -m specmesh_port --allowed-root /absolute/project --project-state json < request.json
python3 -B -m specmesh_port --allowed-root /absolute/project --project-state text < request.json
python3 -B -m specmesh_port --allowed-root /absolute/project --handoff json < request.json
python3 -B -m specmesh_port --allowed-root /absolute/project --handoff text < request.json
python3 -B -m specmesh_port --allowed-root /absolute/project --task-path plans/example --verify-handoff handoff.json
```

Example request (substitute the full current Git SHA):

```json
{"contract_version":"specmesh.port.v1-draft","operation":"check","repo_root":"/absolute/project","expected_head":"0000000000000000000000000000000000000000","task_path":null,"mode":"read_only"}
```

The zero SHA intentionally fails freshness checks; obtain the actual HEAD first. The standalone command validates a bounded request and returns JSON. The request CLI supports inspect, check, prepare_handoff and verify_closeout. The separate Python `SpecMeshService.propose_update` method generates a proposal only; it never applies it. CM currently exposes the read-only subset through its own optional adapter.

`--project-state json|text` is an explicit, additive state-reading view for `inspect` or
`check` requests. Both forms render the same `specmesh.project-state.v1` model; the JSON
form validates against `specmesh-project-state.schema.json`. Omitting the option preserves
the original request/result contract and exit behavior. State exit code is 0 only for a
stable `observed` model and 3 for `unknown`, `ambiguous`, or `blocked`.

The state model reports project/task identity, goals, constraints, task completion criteria,
blockers, declared status, evidence references, the unique next step, full observed HEAD, and
the exact selected-file coverage. Every extracted statement carries its relative source path,
line, source SHA-256, and `asserted_candidate` authority. Coverage carries current SHA-256 plus
tracked/modified observations. `observed` means these inputs were read and revalidated; it does
not mean the task is complete, externally accepted, or the whole worktree is clean.

`Done` entries are retained in a separate history field and do not satisfy evidence or participate
in current-status classification. Human text visibly escapes C0/C1 terminal controls and includes
the same identity sources and statement authority as JSON. Statement and candidate collections are
bounded before schema validation; excess content yields an explicit non-success state rather than
being misreported as an invalid caller request.

Extraction is deliberately finite. It recognizes H1 identity; common SpecMesh H2/H3 sections
such as Why, User Intent, Goal, Context, Constraints, Requirements, Non-goals, Success, Status,
Current, Done, Issues, Evidence, Next and Next Step; plus the bounded-delivery labels 可观察行为、
允许写范围、权限、预算与停止 and 冻结验收清单. Markdown table rows in a selected acceptance
section remain source statements, while its header/separator are omitted. Unsupported or missing
formats produce `unknown`; multiple linked task candidates produce `ambiguous`. A linked task is
never auto-selected: callers must pass `task_path`. Multiple normalized current-status classes
produce `declared_status_conflict`; aliases within one class do not. Completion coexisting with
failure/unknown blockers also remains a conflict. Repository Markdown is data only and no command
found in it is executed. The third authorized repair detects `done` plus `in progress` as
`ambiguous`, preserving both source declarations and the existing public enum. Its targeted
verification and subsequent independent S1-A–F acceptance pass for the recorded candidate;
see [S1 acceptance](https://github.com/muqiao215/specmesh/blob/main/plans/bounded-delivery/evidence/SM-P0.S1/acceptance.md).
Each phase has separate evidence; a local state observation is never release verification.

S2 and S3 status (2026-09-15): **independently accepted**.
S2's scoped handoff passed 107 regressions and independent acceptance; a fresh Agent B then
completed the installation integrity command and passed S3's fixed tests and preservation checks.
See [S2 acceptance](https://github.com/muqiao215/specmesh/blob/main/plans/bounded-delivery/evidence/SM-P1.S2/acceptance.md)
and [S3 acceptance](https://github.com/muqiao215/specmesh/blob/main/plans/bounded-delivery/evidence/SM-P4.S3/acceptance.md).
Historical review failures remain recorded, not current blockers. The snapshot limit is 64 paths.

`--handoff json|text` is an additive handoff-generation view for `prepare_handoff`, `inspect`,
or `check` requests. Both forms render the `specmesh.handoff.v1` model; the JSON form validates
against `specmesh-handoff.schema.json`. Omitting the option preserves the legacy request/result
contract. CLI exit code is 0 only when `executable` is true (state `ready`) and 3 for non-executable
states (`rejected`, `stale`, `cancelled`, `blocked`, `unknown`).

The handoff material bundles project/task identity, goals, constraints, decisions, work summary
(completed, failed, unknown), remaining work, the sole next step, observed baseline HEAD, deterministic
scope fingerprint, explicit dirty coverage (staged, unstaged, staged_and_unstaged, untracked), and
evidence bindings. Staged, unstaged, and untracked file entries record their SHA-256 and locator URI,
retaining inline UTF-8 content or patches within document bounds. A new worktree or downstream consumer
cannot assume dirty contents exist automatically: `--verify-handoff <file>` (or `-` via stdin) and
Python `SpecMeshService.verify_handoff(handoff, repo_root, task_path=..., paths=())` enforce pre-consumption verification.
The gate rejects execution (returning `executable: false` and exit 3) if the target repository has a
stale HEAD, content modified at the same HEAD, missing dirty files, hash mismatches, failed evidence,
or if the task was declared cancelled. Handoff material is a structured continuity report, not an
automatic execution grant or daemon scheduler.

The consumer independently supplies its trusted task selection. Generation accepts extra files
through `prepare_handoff(request, paths=[...])`; use the same files at verification. CLI equivalents
are repeatable `--scope-path src/example.py` and required `--task-path plans/example` when verifying.
The payload cannot expand this scope. These arguments tighten the previously unreleased handoff view;
the existing default request/result contracts remain unchanged.

Dirty coverage includes selected continuity files, explicit extra files and Git-visible files in
the selected task subtree. Ignored files are included only when explicitly selected. `is_clean`
describes this coverage, never the entire repository. Deletions and unsupported file modes yield
a blocked observation. At most 100 dirty entries are allowed, subject to the shared 64-document
snapshot, 256 KiB per-file and 1 MiB total-material limits. Overflow never silently becomes ready.

Source parsing, evidence reads and dirty retention share one descriptor snapshot. Index and membership
are observed again before content/identity and HEAD revalidation. The material digest binds all
serialized semantics, sources, coverage and evidence; consumption reconstructs current material from
authorized sources and compares it. A caller-recomputed digest is insufficient. Locators use
root-relative `code://path` addresses for equivalent preserved worktrees.

Inline Evidence binds its declaration file; linked Evidence binds its target. Explicit Result, HEAD
and Reviewer fields remain declarations with `is_external: false`. Missing evidence blocks handoff;
no statement becomes external acceptance. The CLI reads at most 1 MiB of handoff file/stdin; files
use a regular-file descriptor, bounded read and post-read metadata check. `--version` reports the
runtime version independently of the normative SPEC version.

The capability descriptor declares `specmesh.snapshot.v1`, read-only operation, content/Git revalidation and required external closeout verification. It requires no project access. A host must validate both descriptor and request/result contracts; `unknown` is not a passed gate. CLI exit codes are 0 for pass, 3 for blocked/unknown, and 2 for invalid input or invocation.

The service anchors the repository directory and selected files with descriptors. Discovery and hashing reuse the same observed bytes. Before returning, it rechecks full HEAD, selected index/tree entries, file identity/content, selected task directories and missing optional documents. Edits with unchanged HEAD, same-byte atomic replacement, changed symlinks and newly appearing documents invalidate the observation. Internal symlinks are supported; path traversal, external symlinks and non-regular files are rejected. This is a bounded observation, not a filesystem transaction or lasting authorization; a consumer must revalidate freshness when using it.

Reads are limited to 256 KiB per document, 64 observed paths and 50 returned references. Git calls allow `rev-parse`, `ls-files`, `ls-tree` and bounded `cat-file blob` reads by full object ID, with a five-second deadline and 512 KiB combined output limit. Literal pathspecs, disabled lazy fetch/transports, hooks and fsmonitor avoid repository-defined execution. The reader never invokes `git status` or content filters. `modified` conservatively compares raw file bytes and mode against both index and HEAD; content-filter or newline normalization can therefore report modified where porcelain status would not. This avoids executing a repository's clean filter while checking its documents.

A selected task requires task_plan.md, findings.md and progress.md. A tracked document remains asserted_candidate; tracking alone does not make it reviewed authority. Check pass means structural checks passed, not semantic correctness of every project claim. Closeout remains unknown without external verification; a self-reported passed acceptance manifest is insufficient. The service never applies proposals, writes reviewed memory, issues permissions or resumes an Agent.

The draft schemas live inside specmesh_port/contracts and are mirrored by the CM adapter. This is deliberate interface versioning, not shared installation state. The TypeScript CM candidate can register the independent checkout explicitly, check its capability/code identity, gate task preparation, and request handoff/closeout observations. Its trusted runtime profile must already issue reads for selected references; project links cannot expand permissions. These optional hooks do not switch CM's production runtime or establish external acceptance. See each repository's active plan for verified rollout state.

## Optional artifact requirement candidates

A request may explicitly select `requirements_path`, a repository-relative JSON file.
The standalone format is independent of any runtime:

```json
{"schema_version":"specmesh.artifact_requirements.v1","files":[{"path":"output/report.md","mode":"write"}]}
```

Each of the 1–32 unique entries declares `read` or `write` and may include an exact
lowercase SHA-256. Paths are literal, relative, and exclude traversal and `.git`.
The manifest is subject to the same bounded descriptor snapshot as project documents.
A passing result includes `artifact_requirements` with manifest path, observed SHA-256,
`asserted_candidate` authority, and parsed requirements; it also references that source.
Without an explicit request, or when inspection fails/becomes stale, no candidate is
returned. The service does not read or create the declared output files.

This candidate is neither an execution grant nor evidence of successful completion.
A consumer must revalidate the source, explicitly adopt requirements into its task,
and verify actual execution independently. CM's draft adapter checks matching source
hashes and rejects unrequested candidates; automatic task adoption is not implemented.
The additive draft schemas must be synchronized by consumers before using this field.
