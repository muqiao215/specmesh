#!/usr/bin/env python3
"""Check an unpacked SpecMesh runtime in an isolated process and disposable Git repository."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

PROBE = r"""
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
repo = pathlib.Path(sys.argv[2]).resolve()
sys.path.insert(0, str(root))
import specmesh_port
from specmesh_port.service import SpecMeshService
module_root = pathlib.Path(specmesh_port.__file__).resolve().parent.parent
assert module_root == root
import subprocess
head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
service = SpecMeshService([repo])
request = {"contract_version": "specmesh.port.v1-draft", "operation": "inspect",
           "repo_root": str(repo), "task_path": "plans/example", "expected_head": head, "mode": "read_only"}
state = service.project_state(request)
assert state["state"] == "observed", state
clean = service.prepare_handoff(request)
assert clean["executable"], clean
assert service.verify_handoff(clean, repo, task_path="plans/example")["executable"]
work = repo / "work.txt"
work.write_text("staged\n")
subprocess.run(["git", "-C", str(repo), "add", "work.txt"], check=True)
work.write_text("worktree\n")
dirty = service.prepare_handoff(request, paths=["work.txt"])
assert dirty["executable"], dirty
entry = next(e for e in dirty["dirty_coverage"]["entries"] if e["path"] == "work.txt")
assert entry["staged_content"] == "staged\n"
assert entry["retained_content"] == "worktree\n"
assert service.verify_handoff(dirty, repo, task_path="plans/example", paths=["work.txt"])["executable"]
assert work.read_text() == "worktree\n"
work.write_text("changed\n")
assert not service.verify_handoff(dirty, repo, task_path="plans/example", paths=["work.txt"])["executable"]
work.write_text("worktree\n")
(repo / "plans/example/progress.md").write_text("# Progress\n\n## Current\ncancelled\n")
assert not service.verify_handoff(dirty, repo, task_path="plans/example", paths=["work.txt"])["executable"]
print(json.dumps({"status": "pass", "module_root": str(module_root),
                  "version": specmesh_port.__version__,
                  "checks": ["isolated_import", "project_state", "clean_handoff", "dirty_preservation",
                             "same_head_change_rejected", "cancelled_rejected"]}))
"""


def smoke(package_root):
    package_root = package_root.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="specmesh-smoke-") as temp:
        repo = Path(temp)
        files = {
            "AGENTS.md": "# Instructions\nRead PROJECT.md.\n",
            "PROJECT.md": "# Smoke Project\n\n## Why\nVerify installed continuity.\n\n## User Intent\nPortable runtime.\n\n## Constraints\nNo network.\n\n## Success\nAll checks pass.\n",
            "plans/example/task_plan.md": "# Smoke Task\n\n## Goal\nCheck installation.\n\n## Success\nPreserve bytes.\n\n## Status\nin progress\n\n## Next\nVerify retained bytes.\n",
            "plans/example/findings.md": "# Findings\n\n## Evidence\nBaseline fixture prepared locally.\n",
            "plans/example/progress.md": "# Progress\n\n## Current\nin progress\n\n## Issues\n\n",
        }
        for name, content in files.items():
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        for args in (["init", "-q"], ["config", "user.name", "SpecMesh Smoke"],
                     ["config", "user.email", "smoke@example.invalid"], ["add", "."],
                     ["commit", "-qm", "fixture baseline"]):
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
        result = subprocess.run([sys.executable, "-I", "-B", "-c", PROBE, str(package_root), str(repo)],
                                cwd=temp, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr[-2000:])
        return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(smoke(args.package_root), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
