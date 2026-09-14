#!/usr/bin/env python3
"""Build a deterministic, dependency-free source bundle; dirty builds are candidates only."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


def build(root, output, version, allow_dirty=False):
    root = root.resolve(strict=True)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:rc[0-9]+)?", version):
        raise ValueError("invalid_version")
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    module = ast.parse((root / "specmesh_port/__init__.py").read_text())
    versions = [ast.literal_eval(node.value) for node in module.body if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets)]
    if versions != [version]:
        raise ValueError("runtime_manifest_version_mismatch")
    names = {"LICENSE", "README.md", "SPEC.md", "docs/CODEKIT-INTEGRATION.md",
             "scripts/smoke_release.py", "scripts/build_release.py", "scripts/verify_install.py"}
    for pattern in ("specmesh_port/*.py", "specmesh_port/contracts/*.json", "templates/**/*.md"):
        names.update(p.relative_to(root).as_posix() for p in root.glob(pattern))
    payload, hashes, dirty = {}, {}, []
    for name in sorted(names):
        path = root / name
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ValueError("nonregular_release_input")
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("release_input_too_large")
        raw = path.read_bytes()
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("release_input_too_large")
        payload[name] = raw
        hashes[name] = hashlib.sha256(raw).hexdigest()
        tracked = subprocess.run(["git", "-C", str(root), "show", f"{head}:{name}"], capture_output=True)
        if tracked.returncode or tracked.stdout != raw:
            dirty.append(name)
    if dirty and not allow_dirty:
        raise ValueError("release_inputs_not_committed")
    if subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() != head:
        raise ValueError("release_head_changed")
    for name, raw in payload.items():
        if (root / name).read_bytes() != raw:
            raise ValueError("release_source_changed")
    identity = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    manifest = {"format": "specmesh.distribution.v1", "version": version, "source_head": head,
                "source_identity": identity, "candidate": bool(dirty), "dirty_paths": dirty, "files": hashes}
    payload["manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    output = output.absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves an existing artifact.
    with output.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, raw in sorted(payload.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, raw)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--allow-dirty", action="store_true", help="Build an explicitly labelled candidate")
    args = parser.parse_args()
    manifest = build(args.root, args.output, args.version, args.allow_dirty)
    print(json.dumps({"artifact": str(args.output.absolute()), "candidate": manifest["candidate"],
                      "source_identity": manifest["source_identity"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
