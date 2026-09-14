#!/usr/bin/env python3
"""Verify declared files in an unpacked SpecMesh distribution (not provenance)."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def verify(package_root):
    """Return JSON-compatible status/version/source_identity/checked_files/errors.

    Only declared regular files beneath package_root may be read. A manifest is
    a consistency record, not a trusted signature. Never write installation files.
    """
    package_root = Path(package_root)
    if not package_root.is_dir():
        return {
            "status": "fail",
            "errors": [f"package_root is not a directory: {package_root}"],
        }

    manifest_path = package_root / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return {
            "status": "fail",
            "errors": ["manifest.json is missing or not a regular file"],
        }

    try:
        raw_manifest = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(raw_manifest)
    except Exception as exc:
        return {
            "status": "fail",
            "errors": [f"failed to read or parse manifest.json: {exc}"],
        }

    if not isinstance(manifest, dict):
        return {
            "status": "fail",
            "errors": ["manifest.json must be a JSON object"],
        }

    if manifest.get("format") != "specmesh.distribution.v1":
        return {
            "status": "fail",
            "errors": [f"invalid manifest format: {manifest.get('format')!r}"],
        }

    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        return {
            "status": "fail",
            "errors": ["manifest version must be a non-empty string"],
        }

    source_identity = manifest.get("source_identity")
    if not isinstance(source_identity, str) or not source_identity:
        return {
            "status": "fail",
            "errors": ["manifest source_identity must be a non-empty string"],
        }

    files = manifest.get("files")
    if not isinstance(files, dict):
        return {
            "status": "fail",
            "errors": ["manifest files must be a dictionary"],
        }

    try:
        resolved_root = package_root.resolve(strict=True)
    except Exception as exc:
        return {
            "status": "fail",
            "errors": [f"failed to resolve package_root: {exc}"],
        }

    errors = []
    checked_count = 0

    for rel_str, expected_sha in files.items():
        if not isinstance(rel_str, str) or not rel_str.strip():
            errors.append(f"invalid file path key: {rel_str!r}")
            continue

        if rel_str.startswith("/") or rel_str.startswith("\\"):
            errors.append(f"absolute path not allowed: {rel_str}")
            continue

        rel_path = Path(rel_str)
        if rel_path.is_absolute() or rel_path.drive or ".." in rel_path.parts:
            errors.append(f"path traversal not allowed: {rel_str}")
            continue

        target = package_root
        has_symlink = False
        for part in rel_path.parts:
            target = target / part
            if target.is_symlink():
                has_symlink = True
                break

        if has_symlink:
            errors.append(f"symlinks not allowed: {rel_str}")
            continue

        try:
            resolved_target = target.resolve(strict=False)
            if not resolved_target.is_relative_to(resolved_root):
                errors.append(f"path escapes package root: {rel_str}")
                continue
        except Exception as exc:
            errors.append(f"path resolution error for {rel_str}: {exc}")
            continue

        if not target.is_file():
            errors.append(f"missing or non-regular file: {rel_str}")
            continue

        if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha):
            errors.append(f"invalid sha256 digest format for {rel_str}: {expected_sha!r}")
            continue

        try:
            hasher = hashlib.sha256()
            with target.open("rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            actual_sha = hasher.hexdigest()
        except Exception as exc:
            errors.append(f"failed reading {rel_str}: {exc}")
            continue

        if actual_sha.lower() != expected_sha.lower():
            errors.append(f"hash mismatch for {rel_str}: expected {expected_sha}, got {actual_sha}")
            continue

        checked_count += 1

    if errors:
        return {
            "status": "fail",
            "version": version,
            "source_identity": source_identity,
            "checked_files": checked_count,
            "errors": errors,
        }

    return {
        "status": "pass",
        "version": version,
        "source_identity": source_identity,
        "checked_files": checked_count,
        "errors": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.package_root)
    except (ValueError, OSError, TypeError, NotImplementedError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
