#!/usr/bin/env python3
"""Dependency-free SpecMesh Map v0 spike.

The JSON cache contains derived repository structure plus explicitly asserted
memory relations. It is deterministic, disposable, and invalidated by content
hashes of every participating source file.

Area Overlay v0: reviewed ``.specmesh/repo-areas.v0.yaml`` binds stable
responsibility ids (``area:<kebab-id>``) to current code anchors. The derived
map resolves each anchor into ``current`` / ``unresolved`` / ``ambiguous`` /
``candidate_rebind`` and stops injecting area-scoped memory whenever the area
is not uniquely resolved. The overlay never writes the YAML, the memory, or
any asserted file: rebinding is a human edit.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = "specmesh-map-v0"
DEFAULT_GLOBAL_BUDGET = 1200
DEFAULT_FOCUS_BUDGET = 800
DEFAULT_AREAS_PATH = ".specmesh/repo-areas.v0.yaml"
MAX_AREA_ANCHORS = 3
AREA_STATES = ("current", "unresolved", "ambiguous", "candidate_rebind")
TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
AREA_ID_RE = re.compile(r"^area:[a-z0-9]+(?:-[a-z0-9]+)*$")
AREA_ANCHOR_RE = re.compile(r"^code://(?!/)[^#\s]+(?:#[^\s]+)?$")
AREA_FIELD_KEYS = {"id", "purpose", "anchors", "read_next", "superseded_by"}
RELATION_RE = re.compile(
    r"^- relation:\s*(?P<relation>[^|]+?)\s*\|\s*"
    r"from:\s*`?(?P<from>(?:code|mem|spec)://[^`|\s]+)`?\s*\|\s*"
    r"to:\s*`?(?P<to>(?:code|mem|spec)://[^`|\s]+)`?\s*\|\s*"
    r"provenance:\s*asserted\s*"
    r"(?:\|\s*scope:\s*`?(?P<scope>area:[^`|\s]+)`?\s*)?$"
)
IGNORED_PARTS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _git_files(root: Path) -> list[str] | None:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line]


def participating_files(root: Path) -> list[Path]:
    root = root.resolve()
    candidates = _git_files(root)
    if candidates is None:
        paths = [path for path in root.rglob("*") if path.is_file()]
    else:
        paths = [root / relative for relative in candidates]

    selected: list[Path] = []
    for path in paths:
        try:
            relative = path.resolve().relative_to(root)
        except (OSError, ValueError):
            continue
        if not path.is_file() or any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if relative.parts[:2] == (".specmesh", "cache"):
            continue
        selected.append(path)
    return sorted(set(selected), key=lambda path: path.relative_to(root).as_posix())


def source_manifest(root: Path) -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": file_sha256(path)}
        for path in participating_files(root)
    ]


def manifest_fingerprint(manifest: list[dict[str, str]]) -> str:
    payload = "".join(f"{item['path']}\0{item['sha256']}\n" for item in manifest)
    return sha256_bytes(payload.encode("utf-8"))


def read_context(root: Path) -> dict[str, object]:
    config: dict[str, object] = {
        "global_budget_tokens": DEFAULT_GLOBAL_BUDGET,
        "focus_budget_tokens": DEFAULT_FOCUS_BUDGET,
        "memory_root": ".specmesh/memory/core.md",
        "cache_path": ".specmesh/cache/repo-map.json",
        "areas_path": DEFAULT_AREAS_PATH,
    }
    path = root / ".specmesh/context.md"
    if not path.exists():
        return config
    aliases = {
        "map_global_budget_tokens": "global_budget_tokens",
        "map_focus_budget_tokens": "focus_budget_tokens",
        "memory_root": "memory_root",
        "cache_path": "cache_path",
        "area_overlay": "areas_path",
    }
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        target = aliases.get(key)
        if not target:
            continue
        if target.endswith("budget_tokens"):
            config[target] = int(value)
        else:
            config[target] = value
    return config


# The areas file is asserted (human-reviewed, committed). The parser accepts
# exactly one strict shape and fails loudly on anything else, because silent
# acceptance would turn a typo into a lost responsibility:
#
# areas:
#   - id: area:<kebab-id>
#     purpose: <single line>
#     anchors:
#       - code://<path>
#       - code://<path>#<symbol>
#     read_next:
#       - <relative path>
#     superseded_by: area:<other-id>
#
# Comments occupy whole lines; values are raw text (no inline comments).


def normalize_area_id(raw: str) -> str:
    text = raw.strip().strip("`")
    if text.lower().startswith("area:"):
        text = text[len("area:"):]
    text = re.sub(r"[\s_]+", "-", text.lower())
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return f"area:{text}"


def parse_areas(text: str, source: str) -> list[dict[str, object]]:
    areas: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    list_key: str | None = None
    seen_header = False
    seen_fields: set[str] = set()
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip("\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not seen_header:
            if line != "areas:":
                raise RuntimeError(f"{source}: line {number}: expected 'areas:' header, got: {stripped!r}")
            seen_header = True
            continue
        item = re.match(r"^  - id: (.+)$", line)
        if item:
            current = {
                "id": item.group(1).strip(),
                "purpose": "",
                "anchors": [],
                "read_next": [],
                "superseded_by": None,
            }
            areas.append(current)
            list_key = None
            seen_fields = set()
            continue
        if current is None:
            raise RuntimeError(f"{source}: line {number}: expected '  - id: ...', got: {stripped!r}")
        entry = re.match(r"^      - (.+)$", line)
        if entry and list_key is not None:
            value = entry.group(1).strip()
            if not value or value.startswith("#"):
                raise RuntimeError(f"{source}: line {number}: empty list entry")
            current[list_key].append(value)  # type: ignore[index]
            continue
        field = re.match(r"^    ([A-Za-z_]+): ?(.*)$", line)
        if field:
            key, value = field.group(1), field.group(2).strip()
            if key not in AREA_FIELD_KEYS:
                raise RuntimeError(f"{source}: line {number}: unknown area field {key!r}")
            if key in seen_fields:
                raise RuntimeError(f"{source}: line {number}: duplicate area field {key!r}")
            seen_fields.add(key)
            if key == "id":
                raise RuntimeError(f"{source}: line {number}: 'id' must start an area item ('  - id: ...')")
            if key in {"anchors", "read_next"}:
                if value:
                    raise RuntimeError(f"{source}: line {number}: '{key}:' expects indented entries, got {value!r}")
                list_key = key
                continue
            if not value or value.startswith("#"):
                raise RuntimeError(f"{source}: line {number}: missing value for {key!r}")
            current[key] = value  # type: ignore[assignment]
            list_key = None
            continue
        raise RuntimeError(f"{source}: line {number}: unrecognized line: {stripped!r}")
    if not seen_header:
        raise RuntimeError(f"{source}: missing 'areas:' header")
    _validate_areas(areas, source)
    return areas


def _validate_areas(areas: list[dict[str, object]], source: str) -> None:
    ids: set[str] = set()
    for area in areas:
        area_id = str(area["id"])
        normalized = normalize_area_id(area_id)
        if not AREA_ID_RE.match(area_id) or area_id != normalized:
            raise RuntimeError(f"{source}: area id {area_id!r} is not normalized; use {normalized!r}")
        if area_id in ids:
            raise RuntimeError(f"{source}: duplicate area id {area_id!r}")
        ids.add(area_id)
        if not area["purpose"]:
            raise RuntimeError(f"{source}: area {area_id}: 'purpose' is required")
        anchors = area["anchors"]
        if not 1 <= len(anchors) <= MAX_AREA_ANCHORS:
            raise RuntimeError(
                f"{source}: area {area_id}: expected 1..{MAX_AREA_ANCHORS} anchors, got {len(anchors)}"
            )
        for anchor in anchors:
            if not AREA_ANCHOR_RE.match(str(anchor)):
                raise RuntimeError(f"{source}: area {area_id}: invalid anchor {anchor!r}")
        if len(set(anchors)) != len(anchors):
            raise RuntimeError(f"{source}: area {area_id}: duplicate anchor")
        for entry in area["read_next"]:
            if entry != str(entry).strip() or any(character.isspace() for character in str(entry)):
                raise RuntimeError(f"{source}: area {area_id}: invalid read_next entry {entry!r}")
        superseded_by = area["superseded_by"]
        if superseded_by is not None and (
            not AREA_ID_RE.match(str(superseded_by)) or str(superseded_by) != normalize_area_id(str(superseded_by))
        ):
            raise RuntimeError(
                f"{source}: area {area_id}: superseded_by {superseded_by!r} is not a normalized area id"
            )
    for area in areas:
        superseded_by = area["superseded_by"]
        if superseded_by is None:
            continue
        if superseded_by not in ids:
            raise RuntimeError(
                f"{source}: area {area['id']}: superseded_by {superseded_by!r} does not exist"
            )
        target = next(item for item in areas if item["id"] == superseded_by)
        if target["superseded_by"] is not None:
            raise RuntimeError(
                f"{source}: area {area['id']}: superseded_by chains via {superseded_by!r} are not allowed"
            )


def load_areas(root: Path) -> list[dict[str, object]]:
    path = root / str(read_context(root)["areas_path"])
    if not path.exists():
        return []
    return parse_areas(path.read_text(encoding="utf-8"), source=path.relative_to(root).as_posix())


def _resolve_anchor(
    anchor: str, path_set: set[str], symbol_owners: dict[str, list[str]]
) -> dict[str, object]:
    candidates: list[str] = []
    if "#" in anchor:
        path, _, symbol = anchor[len("code://"):].partition("#")
        if f"code://{path}#{symbol}" in symbol_owners.get(symbol, []):
            resolved: str | None = anchor
        else:
            resolved = None
            candidates = sorted(symbol_owners.get(symbol, []))
    else:
        path = anchor[len("code://"):]
        if path in path_set:
            resolved = anchor
        else:
            resolved = None
            basename = PurePosixPath(path).name
            candidates = sorted(f"code://{other}" for other in path_set if PurePosixPath(other).name == basename)
    return {"anchor": anchor, "resolved": resolved, "candidates": candidates}


def resolve_areas(
    areas: list[dict[str, object]], paths: list[str], symbol_owners: dict[str, list[str]]
) -> dict[str, dict[str, object]]:
    path_set = set(paths)
    resolution: dict[str, dict[str, object]] = {}
    for area in areas:
        records = [_resolve_anchor(str(anchor), path_set, symbol_owners) for anchor in area["anchors"]]
        # Precedence is deliberately conservative: ambiguity outranks everything
        # because injecting against the wrong anchor corrupts memory. A unique
        # candidate outranks total absence because the actionable proposal is
        # what a human needs to see; per-anchor reasons still report anchors
        # with no candidate. Injection safety is unaffected: only `current`
        # injects memory.
        if any(len(record["candidates"]) >= 2 for record in records):  # type: ignore[arg-type]
            state = "ambiguous"
        elif any(record["resolved"] is None and record["candidates"] for record in records):
            state = "candidate_rebind"
        elif any(record["resolved"] is None for record in records):
            state = "unresolved"
        else:
            state = "current"
        reasons: list[str] = []
        for record in records:
            anchor_candidates = record["candidates"]  # type: ignore[assignment]
            if record["resolved"] is not None:
                continue
            if len(anchor_candidates) >= 2:
                reasons.append(
                    f"anchor {record['anchor']}: {len(anchor_candidates)} candidates "
                    f"[{', '.join(anchor_candidates)}]"
                )
            elif anchor_candidates:
                reasons.append(
                    f"anchor {record['anchor']}: unique candidate {anchor_candidates[0]} awaiting human confirmation"
                )
            else:
                reasons.append(f"anchor {record['anchor']}: no candidate")
        resolution[str(area["id"])] = {
            "state": state,
            "anchors": records,
            "reason": "; ".join(reasons) if reasons else None,
            "superseded_by": area["superseded_by"],
            "purpose": area["purpose"],
            "read_next": list(area["read_next"]),  # type: ignore[arg-type]
        }
    return resolution


def _module_index(paths: list[str]) -> dict[str, str]:
    modules: dict[str, str] = {}
    for path in paths:
        if not path.endswith(".py"):
            continue
        module = path[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        modules[module] = path
        modules.setdefault(module.split(".")[-1], path)
    return modules


def _python_facts(path: Path) -> tuple[list[str], list[str], set[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return [], [], set()
    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            symbols.append(node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            symbols.append(node.name)
            symbols.extend(
                f"{node.name}.{member.name}"
                for member in node.body
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not member.name.startswith("_")
            )
    imports: list[str] = []
    references: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Name):
            references.add(node.id)
        elif isinstance(node, ast.Attribute):
            references.add(node.attr)
    return sorted(set(symbols)), sorted(set(imports)), references


def _node(node_id: str, kind: str, name: str, authority: str) -> dict[str, str]:
    return {"id": node_id, "kind": kind, "name": name, "authority": authority}


def _edge(relation: str, source: str, target: str, provenance: str, scope: str | None = None) -> dict[str, str]:
    edge = {
        "relation": relation.strip(),
        "from": source,
        "to": target,
        "provenance": provenance,
    }
    if scope is not None:
        edge["scope"] = scope
    return edge


def build_graph(root: Path) -> dict[str, object]:
    root = root.resolve()
    manifest = source_manifest(root)
    paths = [item["path"] for item in manifest]
    modules = _module_index(paths)
    nodes: dict[str, dict[str, str]] = {}
    edges: dict[tuple[str, str, str, str, str | None], dict[str, str]] = {}
    symbol_owners: dict[str, list[str]] = defaultdict(list)
    python_facts: dict[str, tuple[list[str], list[str], set[str]]] = {}

    for relative in paths:
        file_id = f"code://{relative}"
        nodes[file_id] = _node(file_id, "file", relative, "derived")
        if relative.endswith(".py"):
            facts = _python_facts(root / relative)
            python_facts[relative] = facts
            # Test files already have a navigation surface: their file node plus
            # imports/tests edges. Their test_* symbols are execution units, not
            # landmarks; emitting them also concentrates PageRank degree on the
            # test file and crowds query-relevant nodes out of budgeted views.
            is_test_file = relative.startswith("tests/") or Path(relative).name.startswith("test_")
            for symbol in facts[0] if not is_test_file else ():
                symbol_id = f"{file_id}#{symbol}"
                nodes[symbol_id] = _node(symbol_id, "symbol", symbol, "derived")
                symbol_owners[symbol].append(symbol_id)
                edge = _edge("defines", file_id, symbol_id, "derived")
                edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"], edge.get("scope"))] = edge

    for relative, (symbols, imports, references) in python_facts.items():
        del symbols
        file_id = f"code://{relative}"
        for imported in imports:
            target_path = modules.get(imported) or modules.get(imported.split(".")[0])
            if not target_path or target_path == relative:
                continue
            target_id = f"code://{target_path}"
            edge = _edge("imports", file_id, target_id, "derived")
            edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"], edge.get("scope"))] = edge
            if relative.startswith("tests/") or Path(relative).name.startswith("test_"):
                test_edge = _edge("tests", file_id, target_id, "derived")
                edges[(test_edge["relation"], test_edge["from"], test_edge["to"], test_edge["provenance"], test_edge.get("scope"))] = test_edge
        for reference in references:
            owners = symbol_owners.get(reference, [])
            if len(owners) != 1 or owners[0].startswith(f"{file_id}#"):
                continue
            edge = _edge("references", file_id, owners[0], "derived")
            edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"], edge.get("scope"))] = edge

    memory_root = root / str(read_context(root)["memory_root"])
    area_resolution = resolve_areas(load_areas(root), paths, symbol_owners)
    if memory_root.exists():
        memory_source = str(memory_root)
        for number, line in enumerate(memory_root.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            match = RELATION_RE.match(stripped)
            if not match:
                if stripped.startswith("- relation:"):
                    raise RuntimeError(
                        f"{memory_source}: line {number}: malformed relation, got: {stripped!r}"
                    )
                continue
            values = match.groupdict()
            scope = values.get("scope")
            if scope is not None:
                if not AREA_ID_RE.match(scope):
                    raise RuntimeError(
                        f"{memory_source}: line {number}: memory scope {scope!r} is not canonical; "
                        f"use {normalize_area_id(scope)!r}"
                    )
                if scope not in area_resolution:
                    raise RuntimeError(
                        f"{memory_source}: line {number}: memory scope {scope!r} "
                        "does not match any declared area"
                    )
            for node_id in (values["from"], values["to"]):
                if node_id not in nodes:
                    kind = node_id.split(":", 1)[0]
                    nodes[node_id] = _node(node_id, kind, node_id.rsplit("/", 1)[-1], "asserted")
            edge = _edge(values["relation"], values["from"], values["to"], "asserted", scope)
            edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"], edge.get("scope"))] = edge

    return {
        "schema": SCHEMA_VERSION,
        "source_fingerprint": manifest_fingerprint(manifest),
        "source_state": {"area_resolution": area_resolution},
        "sources": manifest,
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(
            edges.values(),
            key=lambda item: (item["from"], item["relation"], item["to"], item["provenance"]),
        ),
    }


def canonical_json(graph: dict[str, object]) -> bytes:
    return (json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def cache_path(root: Path) -> Path:
    return root / str(read_context(root)["cache_path"])


def write_cache(root: Path, graph: dict[str, object]) -> Path:
    destination = cache_path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(graph)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(destination)
    return destination


def load_cache(root: Path) -> dict[str, object]:
    path = cache_path(root)
    if not path.exists():
        raise RuntimeError("map cache is missing; run: python3 scripts/map_v0.py build")
    return json.loads(path.read_text(encoding="utf-8"))


def cache_is_fresh(root: Path, graph: dict[str, object]) -> bool:
    return graph.get("source_fingerprint") == manifest_fingerprint(source_manifest(root))


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def _rank(graph: dict[str, object], query: str | None) -> dict[str, float]:
    node_ids = [node["id"] for node in graph["nodes"]]
    if not node_ids:
        return {}
    injectable = _injectable_areas(graph)
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for edge in graph["edges"]:
        scope = edge.get("scope")
        if scope is not None and scope not in injectable:
            continue
        source, target = edge["from"], edge["to"]
        if source in adjacency and target in adjacency:
            adjacency[source].add(target)
            adjacency[target].add(source)

    query_terms = {term.casefold() for term in tokenize(query or "") if term.isalnum()}
    weights: dict[str, float] = {}
    for node in graph["nodes"]:
        haystack = f"{node['id']} {node['name']} {node['kind']}".casefold()
        hits = sum(1 for term in query_terms if term in haystack)
        weights[node["id"]] = float(1 + hits * 8) if query_terms else 1.0
    total = sum(weights.values())
    personalization = {node_id: weight / total for node_id, weight in weights.items()}
    scores = dict(personalization)
    damping = 0.85
    for _ in range(24):
        next_scores = {node_id: (1.0 - damping) * personalization[node_id] for node_id in node_ids}
        dangling = sum(scores[node_id] for node_id in node_ids if not adjacency[node_id])
        for node_id in node_ids:
            next_scores[node_id] += damping * dangling * personalization[node_id]
        for source in node_ids:
            targets = adjacency[source]
            if not targets:
                continue
            share = damping * scores[source] / len(targets)
            for target in targets:
                next_scores[target] += share
        scores = next_scores
    return scores


def _injectable_areas(graph: dict[str, object]) -> set[str]:
    resolution = (graph.get("source_state") or {}).get("area_resolution") or {}
    return {
        str(area_id)
        for area_id, record in resolution.items()
        if record["state"] == "current" and not record.get("superseded_by")
    }


def _gated_memory_nodes(graph: dict[str, object], injectable: set[str]) -> set[str]:
    scoped: dict[str, set[str]] = defaultdict(set)
    unscoped: set[str] = set()
    for edge in graph["edges"]:
        scope = edge.get("scope")
        if scope is None:
            unscoped.update((edge["from"], edge["to"]))
        else:
            scoped[edge["from"]].add(scope)
            scoped[edge["to"]].add(scope)
    real_files = {f"code://{source['path']}" for source in graph.get("sources") or []}
    return {
        node_id
        for node_id, scopes in scoped.items()
        if node_id not in unscoped
        and not (scopes & injectable)
        and node_id not in real_files
    }


def _area_haystack(area_id: str, record: dict[str, object]) -> str:
    parts = [area_id, str(record.get("purpose") or "")]
    parts.extend(str(anchor["anchor"]) for anchor in record["anchors"])
    parts.extend(str(path) for path in record.get("read_next") or [])
    return " ".join(parts)


def _area_section(
    resolution: dict[str, dict[str, object]], query_terms: set[str], cap: int
) -> str:
    blocks: list[str] = []
    for area_id in sorted(resolution):
        record = resolution[area_id]
        if record.get("superseded_by"):
            continue
        if query_terms and not any(
            term in _area_haystack(str(area_id), record).casefold() for term in query_terms
        ):
            continue
        if record["state"] == "current":
            lines = [f"- {area_id} [current] purpose: {record['purpose']}\n"]
            lines.append(f"  anchors: {', '.join(str(anchor['anchor']) for anchor in record['anchors'])}\n")
            if record["read_next"]:
                lines.append(f"  read_next: {', '.join(str(path) for path in record['read_next'])}\n")
        else:
            lines = [f"- {area_id} [{record['state']}] {record['reason']}\n"]
        blocks.append("".join(lines))
    if not blocks:
        return ""
    # Area blocks are atomic: a truncated block (read_next without its purpose
    # line) carries no meaning, so a block that does not fit is skipped whole,
    # and the header is only emitted when at least one block fits. The cap
    # keeps area guidance from displacing the ranked map itself.
    kept: list[str] = []
    for block in blocks:
        if len(tokenize("## areas\n" + "".join(kept) + block)) > cap:
            continue
        kept.append(block)
    return "## areas\n" + "".join(kept) if kept else ""


def render_view(graph: dict[str, object], budget: int, query: str | None = None) -> str:
    scores = _rank(graph, query)
    mode = "focus" if query else "global"
    header = f"# SpecMesh Map v0 ({mode})\n"
    if query:
        header += f"task: {query}\n"
    header += f"source: {graph['source_fingerprint']}\n"
    output = header
    injectable = _injectable_areas(graph)
    gated_nodes = _gated_memory_nodes(graph, injectable)
    resolution = (graph.get("source_state") or {}).get("area_resolution") or {}
    query_terms = {term.casefold() for term in tokenize(query or "") if term.isalnum()}
    # The section is built before nodes so its tokens can be reserved; nodes
    # would otherwise consume the whole budget and starve the area guidance.
    section = _area_section(resolution, query_terms, budget // 3)
    section_tokens = len(tokenize(section)) if section else 0
    nodes = sorted(graph["nodes"], key=lambda node: (-scores.get(node["id"], 0.0), node["id"]))
    selected: set[str] = set()
    for node in nodes:
        if node["id"] in gated_nodes:
            continue
        line = f"- {node['id']} [{node['kind']}; {node['authority']}]\n"
        if len(tokenize(output + line)) > budget - section_tokens:
            continue
        output += line
        selected.add(node["id"])
    output += section
    for edge in graph["edges"]:
        scope = edge.get("scope")
        if scope is not None and scope not in injectable:
            continue
        if edge["from"] not in selected or edge["to"] not in selected:
            continue
        line = f"  {edge['from']} -{edge['relation']}-> {edge['to']} ({edge['provenance']})\n"
        if len(tokenize(output + line)) > budget:
            break
        output += line
    return output


def _fresh_graph(root: Path) -> dict[str, object]:
    graph = load_cache(root)
    if not cache_is_fresh(root, graph):
        raise RuntimeError("map cache is stale; run: python3 scripts/map_v0.py build")
    return graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SpecMesh Map v0 spike")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build")
    subparsers.add_parser("check")
    subparsers.add_parser("areas")
    subparsers.add_parser("global")
    focus = subparsers.add_parser("focus")
    focus.add_argument("query")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "build":
            graph = build_graph(root)
            path = write_cache(root, graph)
            print(
                f"built {path.relative_to(root)} fingerprint={graph['source_fingerprint']} "
                f"nodes={len(graph['nodes'])} edges={len(graph['edges'])}"
            )
            return 0
        if args.command == "check":
            graph = load_cache(root)
            fresh = cache_is_fresh(root, graph)
            print("fresh" if fresh else "stale")
            return 0 if fresh else 1
        if args.command == "areas":
            graph = _fresh_graph(root)
            for area_id, record in sorted(graph["source_state"]["area_resolution"].items()):
                superseded_by = record["superseded_by"]
                suffix = f" superseded_by: {superseded_by}" if superseded_by else ""
                print(f"{area_id} [{record['state']}]{suffix}")
                for anchor in record["anchors"]:
                    candidates = anchor["candidates"]
                    if anchor["resolved"]:
                        status = "ok"
                    elif len(candidates) == 1:
                        status = f"candidate {candidates[0]}"
                    elif candidates:
                        status = f"ambiguous [{', '.join(candidates)}]"
                    else:
                        status = "missing"
                    print(f"  {anchor['anchor']} -> {status}")
                if record["reason"]:
                    print(f"  reason: {record['reason']}")
            return 0
        graph = _fresh_graph(root)
        config = read_context(root)
        if args.command == "global":
            view = render_view(graph, int(config["global_budget_tokens"]))
        else:
            view = render_view(graph, int(config["focus_budget_tokens"]), args.query)
        print(view, end="")
        print(f"tokens_v0={len(tokenize(view))}", file=sys.stderr)
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
