# Core Memory

permalink: `mem://core`
authority: asserted
write_policy: reviewed

## Durable boundary

SpecMesh Map v0 shares addresses and retrieval across code structure and project memory while keeping their authority separate. Code and Git remain authoritative for derived structure. Reviewed Markdown remains authoritative for asserted intent, decisions, and constraints.

## Relations

- relation: defines | from: `mem://core` | to: `spec://map-v0` | provenance: asserted | scope: area:memory-authority
- relation: configured_by | from: `spec://map-v0` | to: `code://.specmesh/context.md` | provenance: asserted | scope: area:map-derivation
- relation: implemented_by | from: `spec://map-v0` | to: `code://scripts/map_v0.py` | provenance: asserted | scope: area:map-derivation
- relation: verified_by | from: `spec://map-v0` | to: `code://tests/test_map_v0.py` | provenance: asserted | scope: area:map-derivation
- relation: documented_by | from: `spec://map-v0` | to: `code://SPEC.md` | provenance: asserted | scope: area:map-derivation

## Revisit when

Introduce semantic embeddings only after real task evidence shows that filename, symbol, explicit relation, and personalized graph ranking cannot retrieve the required context.
