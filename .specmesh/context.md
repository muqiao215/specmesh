---
map_global_budget_tokens: 1200
map_focus_budget_tokens: 800
map_freshness: content_hash
memory_root: .specmesh/memory/core.md
cache_path: .specmesh/cache/repo-map.json
index_authority: derived
index_git_tracked: false
memory_write_policy: reviewed
memory_auto_promote: false
area_overlay: .specmesh/repo-areas.v0.yaml
---

# SpecMesh Context

This file is the reviewed entry point for Map v0. Code structure is derived from the repository; semantic memory is asserted in reviewed Markdown. The generated cache is disposable.

## Address schemes

- `code://<path>#<symbol>` identifies a repository file or public symbol.
- `mem://<permalink>` identifies reviewed project memory.
- `spec://<permalink>` identifies a requirement or acceptance boundary.
- `area:<kebab-id>` identifies a stable responsibility declared in the reviewed areas file.

## Area overlay

`.specmesh/repo-areas.v0.yaml` declares areas: stable responsibility identities held by
`id`, `purpose`, 1..3 `anchors`, optional `read_next`, and optional `superseded_by`.
Anchors are resolved against the derived map each build:

- `current`: every anchor resolves.
- `unresolved`: an anchor is gone and no candidate exists.
- `ambiguous`: an anchor has two or more candidates; a human must decide.
- `candidate_rebind`: an anchor has exactly one candidate awaiting human confirmation.

Memory relations may carry `scope: area:<id>`. Scoped memory nodes and edges inject into
task views only while their area is `current`; when the area leaves `current`, injection
stops and the reason is visible in the `areas` command. The build never rewrites memory
or the areas file — rebinding is a human edit.

Authority rules for the overlay:

- Memory parsing is strict and fail-loud: a `- relation:` line that does not parse, a
  scope that is not canonical (`area:<kebab-id>` exactly — no silent normalization), or a
  scope naming no declared area aborts the build with file, line, and suggestion.
- Endpoints that exist only because memory asserts them (including stale `code://` paths
  after renames) are labeled `authority: asserted`; code/Git-derived facts stay `derived`.
  The map never fabricates derived facts for references it cannot verify.
- Ranking and rendering operate on the active-scope graph: edges whose scope is not
  injectable are excluded from PageRank adjacency and from views, so a stale anchor's
  ghost path cannot rank or appear while its area is non-current. Real files referenced
  only by gated edges remain visible as files; only their scoped relations are withheld.
- Duplicate area fields (e.g. two `purpose:` lines) are rejected at parse time; one-to-many
  splits are not modeled in v0 — establish a new area ID by hand instead.

## Commands

```bash
python3 scripts/map_v0.py build
python3 scripts/map_v0.py check
python3 scripts/map_v0.py areas
python3 scripts/map_v0.py global
python3 scripts/map_v0.py focus "task description"
```

Map v0 token budgets use a deterministic regex tokenizer. They are hard limits for this spike, not claims about a specific model tokenizer.
