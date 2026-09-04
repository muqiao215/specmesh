# Progress

## Current

Map v0 spike is complete and published.

## Done

- Confirmed the canonical repository path, remote, branch, HEAD, and clean baseline.
- Read the canonical SpecMesh specification and repository README.
- Established the Map v0 task boundaries and acceptance criteria.
- Added reviewed context and memory roots with explicit authority boundaries.
- Implemented the dependency-free deterministic graph generator and CLI.
- Added ten tests covering extraction, provenance, determinism, freshness, rebuild, budgets, CLI behavior, and five real task seeds.
- Passed all ten tests.
- Verified byte-identical repeated generation on the real repository.
- Verified content-hash invalidation, missing-cache failure, and identical rebuild.
- Verified global and five focus views remain within their hard v0 token budgets.
- Documented Map v0 as an explicitly experimental, non-mandatory section in README and SPEC.
- Added public `Class.method` addresses and enforced that relations read from reviewed memory are always `asserted`.
- Three fresh read-only Agents passed all five real-task location probes within the 800-token budget.
- Reviewed the complete diff, committed it, and pushed `main` to the canonical GitHub repository.

## Remaining

- None for this spike.

## Issues

- None.

## Next

Wait for evidence from real repository tasks before proposing a Map v1 or adding heavier retrieval infrastructure.
