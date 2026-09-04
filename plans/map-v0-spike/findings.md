# Findings

## Baseline

- Repository: `/home/muqiao/桌面/obsidian/my-programming-world/编程/SpecMesh`
- Remote: `https://github.com/muqiao215/specmesh.git`
- Branch/HEAD: `main` / `a2697ae18a16af8ab4ad7e4834849fa17d4790a2`
- Worktree was clean before the spike.
- The repository currently contains only the canonical specification, README, license, and templates; no executable Map implementation exists.

## Design constraints from research

- Code/Git is authoritative for derived structure.
- Reviewed Markdown is authoritative for asserted project memory.
- Both can share addresses and retrieval, but every relation must retain provenance.
- Cache identity must use content hashes rather than mtime.
- The first version should remain deterministic and dependency-free.

## Map v0 implementation

- `.specmesh/context.md` is the reviewed configuration and address entry point.
- `.specmesh/memory/core.md` contains asserted relations linking `mem://core`, `spec://map-v0`, implementation, configuration, documentation, and tests.
- `scripts/map_v0.py` uses only the Python standard library. It derives file and Python symbol nodes, import/reference/test edges, content fingerprints, canonical JSON, and global/focus views.
- Non-Python sources fall back to file nodes.
- Token limits use a deterministic regex tokenizer, explicitly avoiding a false claim of compatibility with every model tokenizer.
- Ten tests pass, including five real task seeds that locate context, implementation, and tests within the 800-token focus budget.
- Final review added public `Class.method` extraction and prevents reviewed memory from introducing edges falsely labelled `derived`.

## Real repository acceptance

- Two consecutive builds produced identical cache SHA-256 `d169656151717c6ec132982a3ac6938c34f76eddc699831be28330481eefe44c` from source fingerprint `66a9bfd5583dab9ea3e36d75f724d4152dd0cafd39a00aee039571ce79f028e4`.
- The graph contained 39 nodes and 30 edges at that source state.
- Adding a participating source made `check` return `stale` with exit 1; removing it restored freshness.
- Deleting the cache made `check` fail explicitly. Rebuilding recreated the exact prior SHA-256.
- The global view used 1176/1200 v0 tokens. Five focus views used 778–780/800.

## Fresh-Agent acceptance

- Three read-only Agents started from `.specmesh/context.md` and independently tested five task seeds.
- All five located the relevant entry, `scripts/map_v0.py`, and `tests/test_map_v0.py` within the 800-token focus budget.
- Authority documentation also surfaced `SPEC.md`; asserted-relation work promoted `.specmesh/memory/core.md`; freshness work surfaced the cache and hashing functions.
- The deliberate v0 limit remains: private implementation helpers are located at file level rather than individually indexed, because the extractor only publishes public symbols.
