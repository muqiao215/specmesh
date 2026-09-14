# SM-P0.S1 evidence

> Latest: [independent acceptance](acceptance.md), S1-A–F pass; closure is now 1/4.
> [Attempt 3](attempt-3.md) remains the same candidate, with no additional implementation patch.
> The prior two-round record below is retained unchanged. Its request for a newly named repair
> task is superseded by the user's explicit instruction to keep this task and cumulative count.

## Result

Status: **blocked / not accepted** on 2026-09-14. The frozen close rate remains 0/4.

The candidate implements `specmesh.project-state.v1`, explicit JSON/text CLI output and bounded,
source-linked Markdown extraction. After two correction rounds, final independent review still
found one S1-C failure: mutually exclusive current declarations are not generally detected. Final
repository checks also found two Map v0 real-task retrieval regressions.

## Input baseline and scope

- Repository: `/home/muqiao/桌面/obsidian/my-programming-world/编程/SpecMesh`
- Branch / full HEAD: `main` / `d393c548a2a58989d65e6cdbd60a36e9a81a444f`
- SPEC.md SHA-256: `5ba5820f1d6ab67b6977520dd0cb2be6e02bbe7b45ce077de1eb35743f8d80ca`
- Existing dirty before implementation: planning documents listed in `findings.md`; no product code.
- Product files changed: `specmesh_port/__main__.py`, `service.py`, new `project_state.py`, new
  `specmesh-project-state.schema.json`, `tests/test_machine_port.py`, and interface documentation.
- No CM/History source, SPEC.md, global config, release/install file, credential or private history
  was read or changed. No provider, network, commit, push, release or installation was used.

Candidate source hashes before failure closeout documentation:

```text
project_state.py  2aad1f3945785576b93e2ebe3ce60b38beedd6ebc5603b8d6938c6763518fe56
service.py        c67e3d2d3e18fd3d09f881046684ca81ba7f2637feff16f3f86296ecc7e89ffb
__main__.py       d3350516f4c3f1d8bc932fe12bb54a7299fcef2a87b36af0944da2e24af0ea35
state schema      751817af4846aa875b26bf1e5c3b774c833199d345fa86c229680799922f4aa0
machine tests     f2ff2e89794149526379d231affd5057b932655881279f2e7cfae6552838af6e
```

These hashes bind the candidate before this evidence and final documentation were added. Recompute
against the current dirty range before any future repair or acceptance.

## Verification

Environment: Python 3.12.3, Git 2.43.0, Linux 6.8.0-139-generic x86_64. Cost/token usage: unknown;
no billable provider was invoked by product verification.

| Check | Result |
|---|---|
| `python3 -B -m unittest discover -s tests -p 'test_machine_port.py' -v` | 38/38 pass, exit 0 |
| `python3 -B -m unittest discover -s tests -p 'test_map_v0.py' -v` | 8/10 pass, exit 1; two real-task views omit `.specmesh/context.md` |
| `python3 -B -m unittest discover -s tests -p 'test_area_overlay.py' -v` | 25/25 pass, exit 0 |
| `git diff --check` | pass, exit 0 |
| real repo, `env -i ... --project-state json` | `observed`, exit 0, coverage 7, history 11 |
| real repo, same request with `--project-state text` | exit 0; identity sources/history/authority visible |
| legacy CLI without `--project-state` | pass, exit 0; old result shape unchanged |
| repository before/after read | selected bytes and Git porcelain unchanged |

Covered counterexamples include missing fields/evidence, multiple task candidates, stale HEAD,
same-HEAD dirty bytes, mid-read replacement, old done plus failure, Markdown command text, fenced
and indented code, terminal C0/C1 controls, 4097-character statements, 201 statements and 51 task
candidates. Non-POSIX platforms, CM/History adapters, providers, S2/S3/R1 and remote CI/release were
not tested and are outside this card.

## Review and correction record

Reviewer: independent read-only Codex subagent `/root/s1_independent_review`. It did not modify the
working tree.

1. Initial review rejected 3 P1 + 3 P2: Done-as-evidence, fenced-heading forgery, text terminal
   controls, missing text provenance, missing blocker presence, and output-limit schema escape.
2. Correction 1 fixed those six; review rejected three remaining cases: historical Done polluted
   current state, CommonMark fence/indent bypass, and unbounded task candidates.
3. Correction 2 fixed those cases; final review confirmed them but rejected the current-status
   conflict below. The two-correction limit was reached, so no third correction was attempted.

## Remaining blocking reproduction

Inputs are otherwise complete and valid:

```markdown
# task_plan.md
## Status
done
```

```markdown
# progress.md
## Current
in progress
```

Observed result:

```json
{"state":"observed","declared_status":["done","in progress"],"issues":[]}
```

Expected: `ambiguous` (or another explicit non-success state) with `declared_status_conflict`.
The correct future repair is to define mutually exclusive current-state classes and detect any
set containing more than one class; `history` must remain visible but excluded from that decision.

The Map regression is deterministic at the closeout fingerprint: the queries `fix Python public
symbol extraction` and `verify content hash freshness and cache rebuild` no longer include
`code://.specmesh/context.md` within the 800-token focus budget after the new state-module nodes are
added. Generated cache build/check remains fresh and both Areas resolve current; those facts do not
override the failed real-task acceptance assertions.

## Stop decision

S1-B/S1-C are not fully met, so this unit is not counted and S2 remains blocked. Continuing requires
a new explicit human authorization and a newly bounded S1 repair task; this evidence does not grant
permission to perform that repair.
