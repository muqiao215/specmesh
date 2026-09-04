#!/usr/bin/env python3
"""Dependency-free SpecMesh Map v0 spike.

The JSON cache contains derived repository structure plus explicitly asserted
memory relations. It is deterministic, disposable, and invalidated by content
hashes of every participating source file.
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
from pathlib import Path


SCHEMA_VERSION = "specmesh-map-v0"
DEFAULT_GLOBAL_BUDGET = 1200
DEFAULT_FOCUS_BUDGET = 800
TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
RELATION_RE = re.compile(
    r"^- relation:\s*(?P<relation>[^|]+?)\s*\|\s*"
    r"from:\s*`?(?P<from>(?:code|mem|spec)://[^`|\s]+)`?\s*\|\s*"
    r"to:\s*`?(?P<to>(?:code|mem|spec)://[^`|\s]+)`?\s*\|\s*"
    r"provenance:\s*asserted\s*$"
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
    }
    path = root / ".specmesh/context.md"
    if not path.exists():
        return config
    aliases = {
        "map_global_budget_tokens": "global_budget_tokens",
        "map_focus_budget_tokens": "focus_budget_tokens",
        "memory_root": "memory_root",
        "cache_path": "cache_path",
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


def _edge(relation: str, source: str, target: str, provenance: str) -> dict[str, str]:
    return {
        "relation": relation.strip(),
        "from": source,
        "to": target,
        "provenance": provenance,
    }


def build_graph(root: Path) -> dict[str, object]:
    root = root.resolve()
    manifest = source_manifest(root)
    paths = [item["path"] for item in manifest]
    modules = _module_index(paths)
    nodes: dict[str, dict[str, str]] = {}
    edges: dict[tuple[str, str, str, str], dict[str, str]] = {}
    symbol_owners: dict[str, list[str]] = defaultdict(list)
    python_facts: dict[str, tuple[list[str], list[str], set[str]]] = {}

    for relative in paths:
        file_id = f"code://{relative}"
        nodes[file_id] = _node(file_id, "file", relative, "derived")
        if relative.endswith(".py"):
            facts = _python_facts(root / relative)
            python_facts[relative] = facts
            for symbol in facts[0]:
                symbol_id = f"{file_id}#{symbol}"
                nodes[symbol_id] = _node(symbol_id, "symbol", symbol, "derived")
                symbol_owners[symbol].append(symbol_id)
                edge = _edge("defines", file_id, symbol_id, "derived")
                edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"])] = edge

    for relative, (symbols, imports, references) in python_facts.items():
        del symbols
        file_id = f"code://{relative}"
        for imported in imports:
            target_path = modules.get(imported) or modules.get(imported.split(".")[0])
            if not target_path or target_path == relative:
                continue
            target_id = f"code://{target_path}"
            edge = _edge("imports", file_id, target_id, "derived")
            edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"])] = edge
            if relative.startswith("tests/") or Path(relative).name.startswith("test_"):
                test_edge = _edge("tests", file_id, target_id, "derived")
                edges[(test_edge["relation"], test_edge["from"], test_edge["to"], test_edge["provenance"])] = test_edge
        for reference in references:
            owners = symbol_owners.get(reference, [])
            if len(owners) != 1 or owners[0].startswith(f"{file_id}#"):
                continue
            edge = _edge("references", file_id, owners[0], "derived")
            edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"])] = edge

    memory_root = root / str(read_context(root)["memory_root"])
    if memory_root.exists():
        for line in memory_root.read_text(encoding="utf-8").splitlines():
            match = RELATION_RE.match(line.strip())
            if not match:
                continue
            values = match.groupdict()
            for node_id in (values["from"], values["to"]):
                if node_id not in nodes:
                    kind = node_id.split(":", 1)[0]
                    authority = "asserted" if kind in {"mem", "spec"} else "derived"
                    nodes[node_id] = _node(node_id, kind, node_id.rsplit("/", 1)[-1], authority)
            edge = _edge(values["relation"], values["from"], values["to"], "asserted")
            edges[(edge["relation"], edge["from"], edge["to"], edge["provenance"])] = edge

    return {
        "schema": SCHEMA_VERSION,
        "source_fingerprint": manifest_fingerprint(manifest),
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
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for edge in graph["edges"]:
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


def render_view(graph: dict[str, object], budget: int, query: str | None = None) -> str:
    scores = _rank(graph, query)
    mode = "focus" if query else "global"
    header = f"# SpecMesh Map v0 ({mode})\n"
    if query:
        header += f"task: {query}\n"
    header += f"source: {graph['source_fingerprint']}\n"
    output = header
    nodes = sorted(graph["nodes"], key=lambda node: (-scores.get(node["id"], 0.0), node["id"]))
    selected: set[str] = set()
    for node in nodes:
        line = f"- {node['id']} [{node['kind']}; {node['authority']}]\n"
        if len(tokenize(output + line)) > budget:
            continue
        output += line
        selected.add(node["id"])
    for edge in graph["edges"]:
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
