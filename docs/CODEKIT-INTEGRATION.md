# Optional independent machine port (draft)

SpecMesh's normative file convention remains `SPEC.md`. This optional Python 3.11+ POSIX profile exposes the same project-continuity boundary to tools without adding a CM dependency, transcript database, Agent runtime or required daemon. Markdown-only users need no new runtime or platform restriction. Executable snapshots require descriptor-relative opening and `O_NOFOLLOW`; unsupported platforms declare `supported: false`.

```sh
python3 -B -m specmesh_port --capabilities
python3 -B -m specmesh_port --allowed-root /absolute/project < request.json
```

Example request (substitute the full current Git SHA):

```json
{"contract_version":"specmesh.port.v1-draft","operation":"check","repo_root":"/absolute/project","expected_head":"0000000000000000000000000000000000000000","task_path":null,"mode":"read_only"}
```

The zero SHA intentionally fails freshness checks; obtain the actual HEAD first. The standalone command validates a bounded request and returns JSON. The request CLI supports inspect, check, prepare_handoff and verify_closeout. The separate Python `SpecMeshService.propose_update` method generates a proposal only; it never applies it. CM currently exposes the read-only subset through its own optional adapter.

The capability descriptor declares `specmesh.snapshot.v1`, read-only operation, content/Git revalidation and required external closeout verification. It requires no project access. A host must validate both descriptor and request/result contracts; `unknown` is not a passed gate. CLI exit codes are 0 for pass, 3 for blocked/unknown, and 2 for invalid input or invocation.

The service anchors the repository directory and selected files with descriptors. Discovery and hashing reuse the same observed bytes. Before returning, it rechecks full HEAD, selected index/tree entries, file identity/content, selected task directories and missing optional documents. Edits with unchanged HEAD, same-byte atomic replacement, changed symlinks and newly appearing documents invalidate the observation. Internal symlinks are supported; path traversal, external symlinks and non-regular files are rejected. This is a bounded observation, not a filesystem transaction or lasting authorization; a consumer must revalidate freshness when using it.

Reads are limited to 256 KiB per document, 64 observed paths and 50 returned references. Git calls allow only `rev-parse`, `ls-files` and `ls-tree`, with a five-second deadline and 512 KiB combined output limit. Literal pathspecs, disabled lazy fetch/transports, hooks and fsmonitor avoid repository-defined execution. The reader never invokes `git status` or content filters. `modified` conservatively compares raw file bytes and mode against both index and HEAD; content-filter or newline normalization can therefore report modified where porcelain status would not. This avoids executing a repository's clean filter while checking its documents.

A selected task requires task_plan.md, findings.md and progress.md. A tracked document remains asserted_candidate; tracking alone does not make it reviewed authority. Check pass means structural checks passed, not semantic correctness of every project claim. Closeout remains unknown without external verification; a self-reported passed acceptance manifest is insufficient. The service never applies proposals, writes reviewed memory, issues permissions or resumes an Agent.

The draft schemas live inside specmesh_port/contracts and are mirrored by the CM adapter. This is deliberate interface versioning, not shared installation state. The TypeScript CM candidate can register the independent checkout explicitly, check its capability/code identity, gate task preparation, and request handoff/closeout observations. Its trusted runtime profile must already issue reads for selected references; project links cannot expand permissions. These optional hooks do not switch CM's production runtime or establish external acceptance. See each repository's active plan for verified rollout state.
