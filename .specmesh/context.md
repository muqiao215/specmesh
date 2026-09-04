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
---

# SpecMesh Context

This file is the reviewed entry point for Map v0. Code structure is derived from the repository; semantic memory is asserted in reviewed Markdown. The generated cache is disposable.

## Address schemes

- `code://<path>#<symbol>` identifies a repository file or public symbol.
- `mem://<permalink>` identifies reviewed project memory.
- `spec://<permalink>` identifies a requirement or acceptance boundary.

## Commands

```bash
python3 scripts/map_v0.py build
python3 scripts/map_v0.py check
python3 scripts/map_v0.py global
python3 scripts/map_v0.py focus "task description"
```

Map v0 token budgets use a deterministic regex tokenizer. They are hard limits for this spike, not claims about a specific model tokenizer.
