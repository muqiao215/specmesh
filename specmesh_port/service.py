"""Independent optional SpecMesh machine profile. No CM/History imports.

Core SpecMesh does not require tasks, Map, Area, or acceptance.json. Closeout
manifests are assertions; they never establish external execution evidence.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from .contracts_runtime import validate
from .git_reader import read_git
from .handoff import build_handoff, verify_pre_consumption, literal_path, scan_git_dirty
from .project_state import MarkdownStateSource, build_project_state
from .snapshot import DocumentSnapshot, MAX_DOCUMENT_BYTES


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

    _git = staticmethod(read_git)

    def _metadata(self, root, selected):
        index, tree = {}, {}
        for args, target, kind in [(('ls-files', '--stage', '-z'), index, 'index'),
                                   (('ls-tree', '-z', 'HEAD'), tree, 'tree')]:
            for row in self._git(root, *args, '--', *selected).split(b'\0'):
                if not row:
                    continue
                header, separator, name = row.partition(b'\t')
                fields = header.decode('ascii').split()
                if not separator or len(fields) != 3:
                    raise ValueError('git_metadata_invalid')
                mode, second, third = fields
                oid = second if kind == 'index' else third
                if not re.fullmatch(r'[0-7]{6}', mode) or not re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})', oid):
                    raise ValueError('git_metadata_invalid')
                entry = (mode, oid, third) if kind == 'index' else (mode, oid)
                target.setdefault(os.fsdecode(name), []).append(entry)
        return {path: (tuple(index.get(path, ())), tuple(tree.get(path, ()))) for path in selected}

    @staticmethod
    def _modified(observed, metadata, head):
        index, tree = metadata
        content = observed.git_content
        header = f'blob {len(content)}\0'.encode()
        oid = hashlib.new('sha256' if len(head) == 64 else 'sha1', header + content).hexdigest()
        value = (observed.git_mode, oid)
        return index != ((*value, '0'),) or tree != (value,)

    @staticmethod
    def _select(snapshot, request, finding):
        selected = ["AGENTS.md", "PROJECT.md"]
        for relative in selected:
            if snapshot.read(relative, optional=True) is None:
                finding("missing_project_entry", "error", relative, "Required project entry is missing.")
        project = snapshot.read("PROJECT.md", optional=True)
        if project is not None:
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", project.decode("utf-8")):
                target = link.split("#", 1)[0]
                if not target or "://" in target:
                    continue
                if any(name in target.lower() for name in ("architecture", "decisions")) and target not in selected:
                    selected.append(target)
        for relative in ("ARCHITECTURE.md", "DECISIONS.md", "docs/ARCHITECTURE.md", "docs/DECISIONS.md"):
            if snapshot.read(relative, optional=True) is not None and relative not in selected:
                selected.append(relative)
        task = None
        if request["task_path"]:
            task = snapshot.directory(request["task_path"])
            for name in ("task_plan.md", "findings.md", "progress.md"):
                relative = str(Path(request["task_path"]) / name)
                if snapshot.read(relative, optional=True) is None:
                    finding("missing_task_entry", "error", relative, "Explicit task directory is missing a continuity file.")
                else:
                    selected.append(relative)
        if len(selected) > 50:
            raise ValueError("progressive_reference_limit")
        return selected, task

    @staticmethod
    def _closeout(snapshot, request, head, task, finding):
        if task is None:
            finding("closeout_task_required", "error", None, "Optional closeout profile requires an explicit task directory.")
            return
        relative = str(Path(request["task_path"]) / "acceptance.json")
        raw = snapshot.read(relative, optional=True)
        if raw is None:
            finding("closeout_manifest_missing", "error", relative, "Optional machine closeout manifest is absent; no completion claim can be checked.")
            return
        rows = json.loads(raw)
        if not isinstance(rows, list) or not rows:
            raise ValueError("nonempty_acceptance_list_required")
        if len(rows) > 128:
            raise ValueError("acceptance_limit_exceeded")
        for row in rows:
            if not isinstance(row, dict) or not all(row.get(k) for k in ("id", "evidence_ref", "head", "content_digest")):
                finding("acceptance_evidence_missing", "error", None, "An acceptance item lacks baseline or evidence.")
            elif row.get("status") != "passed" or row.get("head") != head:
                finding("acceptance_not_passed_on_head", "error", None, "An acceptance item is failed, unknown or on another HEAD.")
        finding("external_verification_required", "warning", None, "Manifest assertions are not execution evidence; the host must verify content snapshot and results.")

    @staticmethod
    def _artifact_requirements(snapshot, relative):
        def literal(path):
            return (isinstance(path, str) and not Path(path).is_absolute()
                    and not re.search(r"[\\\x00-\x1f]", path)
                    and all(part not in ("", ".", "..", ".git") for part in path.split("/")))
        if not literal(relative):
            raise ValueError("invalid_requirements_path")
        raw = snapshot.read(relative)
        requirements = validate("specmesh-artifact-requirements", json.loads(raw))
        files = requirements["files"]
        if not files or len({item["path"] for item in files}) != len(files):
            raise ValueError("invalid_artifact_requirements")
        if not all(literal(item["path"]) for item in files):
            raise ValueError("invalid_artifact_path")
        return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                "authority": "asserted_candidate", "requirements": requirements}

    def check(self, request):
        validate("specmesh-request", request)
        result = {"contract_version": "specmesh.port.v1-draft", "observed_head": None,
                  "status": "unknown", "findings": [], "references": []}

        def finding(code, severity, path, message):
            result["findings"].append({"code": code, "severity": severity, "path": path, "message": message})

        try:
            root = self._root(request["repo_root"])
            with DocumentSnapshot(root) as snapshot:
                actual_root = Path(os.fsdecode(self._git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
                if actual_root != root:
                    raise ValueError("request_must_bind_repository_root")
                head = self._git(root, "rev-parse", "HEAD").decode().strip()
                result["observed_head"] = head
                if head != request["expected_head"]:
                    finding("head_changed", "error", None, "Current checkout does not match expected_head.")
                selected, task = self._select(snapshot, request, finding)
                candidate = None
                if "requirements_path" in request:
                    candidate = self._artifact_requirements(snapshot, request["requirements_path"])
                    if candidate["path"] not in selected:
                        selected.append(candidate["path"])
                    if len(selected) > 50:
                        raise ValueError("progressive_reference_limit")
                for relative in selected:
                    snapshot.read(relative, optional=True)
                metadata = self._metadata(root, selected)
                for relative in selected:
                    raw = snapshot.read(relative, optional=True)
                    if raw is None:
                        if relative not in ("AGENTS.md", "PROJECT.md"):
                            finding("missing_optional_reference", "warning", relative, "Referenced document is not present.")
                        continue
                    tracked = bool(metadata[relative][0])
                    modified = self._modified(snapshot.files[relative], metadata[relative], head)
                    authority = "derived" if "/generated/" in "/" + relative or "/.cache/" in "/" + relative else "asserted_candidate"
                    result["references"].append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                                                 "authority": authority, "tracked": tracked, "modified": modified})
                    if modified:
                        finding("uncommitted_project_fact", "warning", relative, "Working bytes or index differ from HEAD; preserve this state. Git content filters are not executed.")
                if request["operation"] == "verify_closeout":
                    self._closeout(snapshot, request, head, task, finding)
                if self._metadata(root, selected) != metadata:
                    finding("git_metadata_changed_during_check", "error", None, "Retry on a stable index and worktree.")
                snapshot.verify()
                if self._git(root, "rev-parse", "HEAD").decode().strip() != head:
                    finding("head_changed_during_check", "error", None, "Retry on a stable baseline.")
                result["status"] = "blocked" if any(x["severity"] == "error" for x in result["findings"]) else ("unknown" if request["operation"] == "verify_closeout" else "pass")
                if candidate is not None and result["status"] == "pass":
                    result["artifact_requirements"] = candidate
        except (OSError, ValueError, RuntimeError, UnicodeError, subprocess.SubprocessError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]+", str(exc)) else type(exc).__name__
            finding("check_unavailable", "error", None, reason)
            result["status"] = "blocked"
        return validate("specmesh-result", result)

    def project_state(self, request):
        """Return a source-bound semantic state model without changing old results."""
        validate("specmesh-request", request)
        issues: list[dict[str, object]] = []
        coverage: list[dict[str, object]] = []
        sources: dict[str, MarkdownStateSource] = {}
        observed_head = None

        def issue(code, severity, field, message):
            issues.append({"code": code, "severity": severity, "field": field or "observation", "message": message})

        try:
            if request["operation"] not in ("inspect", "check"):
                raise ValueError("project_state_operation_required")
            root = self._root(request["repo_root"])
            with DocumentSnapshot(root) as snapshot:
                actual_root = Path(os.fsdecode(self._git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
                if actual_root != root:
                    raise ValueError("request_must_bind_repository_root")
                observed_head = self._git(root, "rev-parse", "HEAD").decode().strip()
                if observed_head != request["expected_head"]:
                    issue("head_changed", "error", "baseline", "Current checkout does not match expected_head.")
                selected, _ = self._select(snapshot, request, issue)
                for relative in selected:
                    snapshot.read(relative, optional=True)
                metadata = self._metadata(root, selected)
                for relative in selected:
                    raw = snapshot.read(relative, optional=True)
                    if raw is None:
                        if relative not in ("AGENTS.md", "PROJECT.md"):
                            issue("missing_optional_reference", "warning", relative, "Selected document is not present.")
                        continue
                    tracked = bool(metadata[relative][0])
                    modified = self._modified(snapshot.files[relative], metadata[relative], observed_head)
                    coverage.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                                     "tracked": tracked, "modified": modified})
                    sources[relative] = MarkdownStateSource(relative, raw)
                    if modified:
                        issue("uncommitted_project_fact", "warning", relative,
                              "Working bytes or index differ from HEAD; this observation covers the current bytes only.")
                if self._metadata(root, selected) != metadata:
                    issue("git_metadata_changed_during_check", "error", "baseline", "Retry on a stable index and worktree.")
                snapshot.verify()
                if self._git(root, "rev-parse", "HEAD").decode().strip() != observed_head:
                    issue("head_changed_during_check", "error", "baseline", "Retry on a stable baseline.")
        except (OSError, ValueError, RuntimeError, UnicodeError, subprocess.SubprocessError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]+", str(exc)) else type(exc).__name__
            issue("state_unavailable", "error", "observation", reason)

        task_path = request["task_path"]
        prefix = str(Path(task_path)) if task_path else None
        state = build_project_state(
            project=sources.get("PROJECT.md"),
            task_plan=sources.get(str(Path(prefix) / "task_plan.md")) if prefix else None,
            findings=sources.get(str(Path(prefix) / "findings.md")) if prefix else None,
            progress=sources.get(str(Path(prefix) / "progress.md")) if prefix else None,
            task_path=prefix,
            observed_head=observed_head,
            expected_head=request["expected_head"],
            coverage=coverage,
            issues=issues,
        )
        return validate("specmesh-project-state", state)

    def prepare_handoff(self, request, *, paths=()):
        """Observe caller-selected scope in one bounded snapshot; material grants no execution."""
        validate("specmesh-request", request)
        issues, coverage, sources = [], [], {}
        head = None
        task_path = None
        def issue(code, severity, field, message):
            issues.append({"code": code, "severity": severity, "field": field or "observation", "message": message})

        def assemble(root, snapshot=None, selected=()):
            prefix = task_path + "/" if task_path else ""
            return build_handoff(
                project=sources.get("PROJECT.md"),
                task_plan=sources.get(prefix + "task_plan.md"),
                findings=sources.get(prefix + "findings.md"),
                progress=sources.get(prefix + "progress.md"),
                decisions_doc=sources.get("docs/DECISIONS.md") or sources.get("DECISIONS.md"),
                task_path=task_path, observed_head=head, expected_head=request["expected_head"],
                coverage=coverage, repo_root=root, issues=issues,
                selected_paths=set(selected), snapshot=snapshot)

        try:
            if request["operation"] not in ("prepare_handoff", "inspect", "check"):
                raise ValueError("prepare_handoff_operation_required")
            root = self._root(request["repo_root"])
            task_path = literal_path(request["task_path"]) if request["task_path"] else None
            extra = sorted(set(literal_path(p) for p in paths))
            if len(extra) > 50:
                raise ValueError("handoff_scope_limit")
            with DocumentSnapshot(root) as snapshot:
                actual = Path(os.fsdecode(self._git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
                if actual != root:
                    raise ValueError("request_must_bind_repository_root")
                head = self._git(root, "rev-parse", "HEAD").decode().strip()
                selected, _ = self._select(snapshot, request, issue)
                selected = sorted(set(literal_path(p) for p in selected) | set(extra))
                metadata = self._metadata(root, selected)
                for relative in selected:
                    raw = snapshot.read(relative, optional=True)
                    if raw is None:
                        issue("missing_handoff_source", "error", relative, "Selected file is absent.")
                        continue
                    coverage.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                                     "tracked": bool(metadata[relative][0]),
                                     "modified": self._modified(snapshot.files[relative], metadata[relative], head)})
                    if relative not in extra:
                        sources[relative] = MarkdownStateSource(relative, raw)
                handoff = assemble(root, snapshot, selected)
                # Re-scan index and membership; snapshot.verify checks the exact worktree/evidence bytes.
                summary, dirty = scan_git_dirty(root, head, task_path, set(selected), snapshot=snapshot)
                if dirty != handoff["dirty_coverage"]["entries"] or summary != handoff["dirty_coverage"]["summary"]:
                    raise ValueError("dirty_changed_during_check")
                if self._metadata(root, selected) != metadata:
                    raise ValueError("git_metadata_changed_during_check")
                snapshot.verify()
                if self._git(root, "rev-parse", "HEAD").decode().strip() != head:
                    raise ValueError("head_changed_during_check")
                if len(json.dumps(handoff).encode()) > 1024 * 1024:
                    raise ValueError("handoff_material_too_large")
                return handoff
        except (ValueError, OSError, RuntimeError, UnicodeError, subprocess.SubprocessError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]+", str(exc)) else type(exc).__name__
            issue("handoff_unavailable", "error", "observation", reason)
            # Never perform a second ungranted read from a failed observation.
            sources.clear()
            coverage.clear()
            task_path = None
            return assemble(Path("."))

    def verify_handoff(self, handoff, repo_root, *, task_path=None, paths=()):
        """Caller supplies task/files independently of the untrusted handoff payload."""
        root = self._root(repo_root)
        def observe():
            if not task_path:
                raise ValueError("trusted_task_scope_required")
            request = {"contract_version": "specmesh.port.v1-draft", "operation": "prepare_handoff",
                       "repo_root": str(root), "task_path": literal_path(task_path),
                       "expected_head": handoff["baseline"]["expected_head"], "mode": "read_only"}
            return self.prepare_handoff(request, paths=paths)
        return verify_pre_consumption(handoff, root, observe=observe)

    def propose_update(self, repo_root, relative_path, *, base_sha256, new_content):
        """Return a reviewable patch only, against a consistent base; never apply it."""
        root = self._root(repo_root)
        with DocumentSnapshot(root) as snapshot:
            old = snapshot.read(relative_path)
            if hashlib.sha256(old).hexdigest() != base_sha256:
                raise ValueError("base_hash_conflict")
            if not isinstance(new_content, str) or len(new_content.encode()) > MAX_DOCUMENT_BYTES:
                raise ValueError("invalid_new_content")
            patch = "".join(difflib.unified_diff(old.decode().splitlines(True), new_content.splitlines(True),
                                                fromfile="a/" + relative_path, tofile="b/" + relative_path))
            snapshot.verify()
            return {"base_sha256": base_sha256, "new_sha256": hashlib.sha256(new_content.encode()).hexdigest(),
                    "path": relative_path, "applied": False, "patch": patch}
