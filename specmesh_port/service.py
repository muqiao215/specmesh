"""Independent optional SpecMesh machine profile. No CM/History imports.

Core spec is NOT expanded to require tasks, Map, Area, or acceptance.json.
Only verify_closeout opts into this bundle's proposed acceptance manifest.
"""
from __future__ import annotations
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from .contracts_runtime import validate

MAX_DOCUMENT_BYTES = 256 * 1024


class SpecMeshService:
    def __init__(self, allowed_roots: list[str | Path]):
        self.allowed_roots = tuple(Path(x).resolve(strict=True) for x in allowed_roots)

    def _root(self, value):
        path = Path(value)
        if not path.is_absolute():
            raise ValueError("absolute_repo_root_required")
        root = path.resolve(strict=True)
        if not root.is_dir() or not any(root == p or root.is_relative_to(p) for p in self.allowed_roots):
            raise ValueError("repository_outside_grant")
        return root

    @staticmethod
    def _path(root, relative):
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("relative_in_repo_path_required")
        path = (root / candidate).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError("symlink_path_escape")
        return path

    @staticmethod
    def _git(root, *args):
        binary = shutil.which("git")
        if not binary:
            raise ValueError("git_unavailable")
        env = {"PATH": os.environ.get("PATH", ""), "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0",
               "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
        return subprocess.run([binary,"--no-optional-locks","-c","core.fsmonitor=false","-C",str(root),*args], capture_output=True, check=True, timeout=5, env=env).stdout

    @staticmethod
    def _read(path):
        with path.open("rb") as stream:
            raw = stream.read(MAX_DOCUMENT_BYTES + 1)
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise ValueError("document_too_large")
        return raw

    def check(self, request):
        validate("specmesh-request", request)
        result = {"contract_version":"specmesh.port.v1-draft","observed_head":None,"status":"unknown","findings":[],"references":[]}
        def finding(code, severity, path, message):
            result["findings"].append({"code":code,"severity":severity,"path":path,"message":message})
        try:
            root = self._root(request["repo_root"])
            actual_root = Path(os.fsdecode(self._git(root,"rev-parse","--show-toplevel")).strip()).resolve()
            if actual_root != root:
                raise ValueError("request_must_bind_repository_root")
            head = self._git(root,"rev-parse","HEAD").decode().strip()
            result["observed_head"] = head
            if head != request["expected_head"]:
                finding("head_changed","error",None,"Current checkout does not match expected_head.")
            selected = ["AGENTS.md","PROJECT.md"]
            for required in selected:
                if not (root / required).is_file():
                    finding("missing_project_entry","error",required,"Required project entry is missing.")
            # Progressive discovery: only architectural/decision links from PROJECT.
            if (root / "PROJECT.md").is_file():
                text = self._read(self._path(root,"PROJECT.md")).decode("utf-8")
                for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                    target = link.split("#",1)[0]
                    if not target or "://" in target:
                        continue
                    if any(name in target.lower() for name in ("architecture","decisions")):
                        if target not in selected:
                            selected.append(target)
            # Optional known locations, not an additional obligation for small projects.
            for optional in ("ARCHITECTURE.md","DECISIONS.md","docs/ARCHITECTURE.md","docs/DECISIONS.md"):
                if (root / optional).is_file() and optional not in selected:
                    selected.append(optional)
            task = None
            if request["task_path"]:
                task = self._path(root, request["task_path"])
                if not task.is_dir():
                    raise ValueError("task_path_must_be_directory")
                for filename in ("task_plan.md","findings.md","progress.md"):
                    candidate = task / filename
                    if candidate.is_file():
                        selected.append(str(candidate.relative_to(root)))
                    else:
                        finding("missing_task_entry", "error", str(candidate.relative_to(root)),
                                "Explicit task directory is missing a continuity file.")
            if len(selected) > 50:
                raise ValueError("progressive_reference_limit")
            for relative in selected:
                try:
                    path = self._path(root, relative)
                    raw = self._read(path)
                    tracked = bool(self._git(root,"ls-files","--",relative))
                    modified = bool(self._git(root,"status","--porcelain=v1","--",relative))
                    # Git-tracked is NOT synonymous with human-reviewed or confirmed.
                    authority = "derived" if "/generated/" in "/"+relative or "/.cache/" in "/"+relative else "asserted_candidate"
                    result["references"].append({"path":relative,"sha256":hashlib.sha256(raw).hexdigest(),"authority":authority,"tracked":tracked,"modified":modified})
                    if modified:
                        finding("uncommitted_project_fact","warning",relative,"Preserve this edit; do not treat HEAD as its content hash.")
                except FileNotFoundError:
                    if relative not in ("AGENTS.md","PROJECT.md"):
                        finding("missing_optional_reference","warning",relative,"Referenced document is not present.")
            if request["operation"] == "verify_closeout":
                if task is None:
                    finding("closeout_task_required","error",None,"Optional closeout profile requires an explicit task directory.")
                else:
                    path = task / "acceptance.json"
                    if not path.is_file():
                        finding("closeout_manifest_missing","error",str(path.relative_to(root)),"Optional machine closeout manifest is absent; no completion claim can be checked.")
                    else:
                        rows = json.loads(self._read(self._path(root, str(path.relative_to(root)))))
                        if not isinstance(rows, list) or not rows:
                            raise ValueError("nonempty_acceptance_list_required")
                        for row in rows:
                            if not isinstance(row, dict) or not all(row.get(k) for k in ("id","evidence_ref","head","content_digest")):
                                finding("acceptance_evidence_missing","error",None,"An acceptance item lacks baseline or evidence.")
                            elif row.get("status") != "passed" or row.get("head") != head:
                                finding("acceptance_not_passed_on_head","error",None,"An acceptance item is failed, unknown or on another HEAD.")
                        finding("external_verification_required","warning",None,"Manifest assertions are not execution evidence; the host must verify content snapshot and results.")
            after = self._git(root,"rev-parse","HEAD").decode().strip()
            if after != head:
                finding("head_changed_during_check","error",None,"Retry on a stable baseline.")
            result["status"] = "blocked" if any(x["severity"] == "error" for x in result["findings"]) else ("unknown" if request["operation"] == "verify_closeout" else "pass")
        except (OSError, ValueError, RuntimeError, UnicodeError, subprocess.SubprocessError) as exc:
            finding("check_unavailable","error",None,type(exc).__name__ + ":" + str(exc).split("\n",1)[0][:120])
            result["status"] = "blocked"
        return validate("specmesh-result", result)

    def propose_update(self, repo_root, relative_path, *, base_sha256, new_content):
        """Returns a reviewable patch only. Does not apply it or create files."""
        root = self._root(repo_root)
        path = self._path(root, relative_path)
        old = self._read(path)
        if hashlib.sha256(old).hexdigest() != base_sha256:
            raise ValueError("base_hash_conflict")
        if not isinstance(new_content, str) or len(new_content.encode()) > MAX_DOCUMENT_BYTES:
            raise ValueError("invalid_new_content")
        return {"base_sha256":base_sha256,"new_sha256":hashlib.sha256(new_content.encode()).hexdigest(),
                "path":relative_path,"applied":False,
                "patch":"".join(difflib.unified_diff(old.decode().splitlines(True),new_content.splitlines(True),fromfile="a/"+relative_path,tofile="b/"+relative_path))}
