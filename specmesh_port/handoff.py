"""Bounded extraction, rendering, and pre-consumption verification for SpecMesh handoff."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from .contracts_runtime import validate
from .git_reader import read_git
from .project_state import (
    MarkdownStateSource,
    _bounded,
    _classifications,
    _heading_key,
    _source_text,
    _statement,
    _visible,
)
from .snapshot import DocumentSnapshot, MAX_DOCUMENT_BYTES

HANDOFF_SCHEMA_VERSION = "specmesh.handoff.v1"


def compute_scope_fingerprint(
    observed_head: str | None,
    coverage: list[dict[str, object]],
    dirty_entries: list[dict[str, object]],
    evidence_bindings: list[dict[str, object]],
) -> str:
    """Deterministic SHA-256 fingerprint over observed baseline, coverage, dirty state, and evidence."""
    hasher = hashlib.sha256()
    hasher.update((observed_head or "none").encode("utf-8"))
    for item in sorted(coverage, key=lambda x: str(x.get("path", ""))):
        hasher.update(
            f"|cov:{item.get('path')}:{item.get('sha256')}:{item.get('tracked')}:{item.get('modified')}".encode("utf-8")
        )
    for item in sorted(dirty_entries, key=lambda x: str(x.get("path", ""))):
        hasher.update(
            f"|dirty:{item.get('path')}:{item.get('kind')}:{item.get('staged_sha256')}:{item.get('worktree_sha256')}".encode("utf-8")
        )
    for item in sorted(evidence_bindings, key=lambda x: str(x.get("evidence_ref") or x.get("statement", ""))):
        hasher.update(
            f"|ev:{item.get('evidence_ref')}:{item.get('evidence_sha256')}:{item.get('baseline_head')}:{item.get('status')}".encode("utf-8")
        )
    return hasher.hexdigest()


def literal_path(value: str) -> str:
    """Only root-relative, non-metadata paths may enter the observation scope."""
    if (not isinstance(value, str) or not value or len(value) > 4096
            or value.startswith("/") or re.search(r"[\\\\\x00-\x1f]", value)
            or any(p in ("", ".", "..", ".git") for p in value.split("/"))):
        raise ValueError("relative_in_repo_path_required")
    return value


def scan_git_dirty(root, head, task_path=None, selected_paths=None, *, snapshot=None):
    """Observe only the caller's task subtree and explicitly selected files."""
    if snapshot is None:
        with DocumentSnapshot(root) as owned:
            result = scan_git_dirty(root, head, task_path, selected_paths, snapshot=owned)
            owned.verify()
            return result
    scope = sorted(set(literal_path(p) for p in (selected_paths or ())))
    if task_path:
        scope.append(literal_path(task_path))
    if not head or not scope:
        return {"staged_count": 0, "unstaged_count": 0, "untracked_count": 0}, []

    def entries(raw, index=False):
        result = {}
        for row in raw.split(b"\0"):
            if not row:
                continue
            header, sep, name = row.partition(b"\t")
            fields = header.decode("ascii").split()
            path = literal_path(name.decode("utf-8"))
            if not sep or len(fields) != 3 or (index and fields[2] != "0"):
                raise ValueError("unmerged_or_invalid_index")
            mode, oid = fields[0], fields[1] if index else fields[2]
            if mode not in ("100644", "100755"):
                raise ValueError("unsupported_dirty_entry_mode")
            result[path] = (mode, oid)
        return result

    index = entries(read_git(root, "ls-files", "--stage", "-z", "--", *scope), True)
    tree = entries(read_git(root, "ls-tree", "-r", "-z", "HEAD", "--", *scope))
    staged = {p for p in set(index) | set(tree) if index.get(p) != tree.get(p)}
    modified = {literal_path(p.decode("utf-8")) for p in
                read_git(root, "ls-files", "--modified", "-z", "--", *scope).split(b"\0") if p}
    untracked = {literal_path(p.decode("utf-8")) for p in
                 read_git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", *scope).split(b"\0") if p}
    def read_regular(path):
        raw = snapshot.read(path, optional=True)
        observed = snapshot.files.get(path)
        # Dirty v1 retains regular file bytes, not symlink targets or aliased subtrees.
        if observed and (observed.git_mode == "120000" or observed.path != root / path):
            raise ValueError("unsupported_dirty_entry_mode")
        return raw

    # Explicit file selection overrides discovery ignores, without broadening task discovery.
    for path in selected_paths or ():
        if path not in index and read_regular(path) is not None:
            untracked.add(path)
    paths = sorted(staged | modified | untracked)
    if len(paths) > 100:
        raise ValueError("dirty_coverage_limit_exceeded")

    def blob(item):
        if item is None:
            return None
        raw = read_git(root, "cat-file", "blob", item[1])
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise ValueError("dirty_blob_too_large")
        return raw

    def sha(raw):
        return hashlib.sha256(raw).hexdigest() if raw is not None else None

    def text(raw):
        if raw is None:
            return None
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return None

    output = []
    for path in paths:
        raw = read_regular(path)
        # v1 cannot represent a deletion as retained worktree bytes. Fail explicitly.
        if raw is None:
            raise ValueError("dirty_file_missing")
        staged_raw = blob(index.get(path))
        head_raw = blob(tree.get(path))
        kind = ("staged_and_unstaged" if path in staged and path in modified else
                "staged" if path in staged else "unstaged" if path in modified else "untracked")
        output.append({"path": path, "kind": kind, "head_sha256": sha(head_raw),
                       "staged_sha256": sha(staged_raw), "staged_content": text(staged_raw),
                       "worktree_sha256": sha(raw), "retained_content": text(raw),
                       "patch": None, "locator": f"code://{path}"})
    return {
        "staged_count": sum(e["kind"] in ("staged", "staged_and_unstaged") for e in output),
        "unstaged_count": sum(e["kind"] in ("unstaged", "staged_and_unstaged") for e in output),
        "untracked_count": sum(e["kind"] == "untracked" for e in output),
    }, output


def extract_evidence_bindings(sources, repo_root, *, snapshot):
    """Bind declared evidence bytes; never certify a reviewer or external acceptance."""
    bindings = []
    for source in sources:
        for heading in ("Evidence", "Verification", "验收", "已通过基线与尚未覆盖的条件", "本轮自查"):
            for section in source.sections.get(_heading_key(heading), []):
                for line, raw in section.rows:
                    text = raw.strip()
                    if not text or text.startswith(("\x60\x60\x60", "|")):
                        continue
                    ref = source.path
                    match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", text)
                    if match:
                        target = match.group(2).split("#", 1)[0].strip()
                        try:
                            literal_path(target)
                            ref = literal_path((Path(source.path).parent / target).as_posix())
                        except ValueError:
                            ref = None
                    evidence = snapshot.read(ref, optional=True) if ref else None
                    content = evidence.decode("utf-8", errors="replace") if evidence is not None else ""
                    head = re.search(r"(?mi)^HEAD:\s*([0-9a-f]{40}|[0-9a-f]{64})\s*$", content)
                    reviewer = re.search(r"(?mi)^(?:审查者|reviewer):\s*([^\n]+)", content)
                    result = re.findall(r"(?mi)^Result:\s*(passed|accepted|failed|rejected)\s*$", content)
                    status = ("failed" if evidence is None or any(x.lower() in ("failed", "rejected") for x in result)
                              else "passed" if result else "unverified")
                    bindings.append({"statement": text, "source": source.source(line),
                                     "evidence_ref": ref,
                                     "evidence_sha256": hashlib.sha256(evidence).hexdigest() if evidence is not None else None,
                                     "reviewer": reviewer.group(1).strip() if reviewer else None,
                                     "baseline_head": head.group(1) if head else None,
                                     "status": status, "is_external": False})
                    if len(bindings) > 50:
                        raise ValueError("evidence_binding_limit_exceeded")
    return bindings


def material_fingerprint(handoff):
    """Canonical material digest; live source reconstruction establishes authenticity."""
    value = dict(handoff)
    value["baseline"] = {k: v for k, v in handoff["baseline"].items() if k != "scope_fingerprint"}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":")).encode()).hexdigest()


def build_handoff(
    *,
    project: MarkdownStateSource | None,
    task_plan: MarkdownStateSource | None,
    findings: MarkdownStateSource | None,
    progress: MarkdownStateSource | None,
    decisions_doc: MarkdownStateSource | None,
    task_path: str | None,
    observed_head: str | None,
    expected_head: str,
    coverage: list[dict[str, object]],
    repo_root: Path,
    issues: list[dict[str, object]],
    selected_paths: set[str] | None = None,
    snapshot=None,
) -> dict[str, object]:
    """Generate a bounded, verifiable handoff material conforming to specmesh.handoff.v1."""
    project_title = project.title_statement() if project else None
    task_title = task_plan.title_statement() if task_plan else None

    if project_title and len(str(project_title["text"])) > 4096:
        issues.append({"code": "handoff_statement_too_large", "severity": "warning", "field": "project_identity",
                       "message": "Project identity exceeds the 4096-character output limit."})
        project_title = None
    if task_title and len(str(task_title["text"])) > 4096:
        issues.append({"code": "handoff_statement_too_large", "severity": "warning", "field": "task",
                       "message": "Task identity exceeds the 4096-character output limit."})
        task_title = None

    candidates = [] if task_path or project is None else project.linked_task_candidates()
    if len(candidates) > 50:
        issues.append({"code": "task_candidate_limit", "severity": "warning", "field": "task",
                       "message": f"{len(candidates)} linked task candidates exceed the 50-item output limit."})
        candidates = candidates[:50]

    project_identity = {
        "state": "known" if project_title else "unknown",
        "value": project_title["text"] if project_title else None,
        "sources": [project_title["source"]] if project_title else [],
    }
    if task_path:
        task_state = "selected" if task_title else "unknown"
    else:
        task_state = "ambiguous" if len(candidates) > 1 else "unknown"

    task = {
        "state": task_state,
        "path": task_path,
        "value": task_title["text"] if task_title else None,
        "candidates": candidates,
        "sources": [task_title["source"]] if task_title else [],
    }

    goals = []
    constraints = []
    decisions = []
    completed = []
    failed = []
    unknown_items = []
    remaining_work = []
    next_steps = []
    blockers = []
    declared_status = []

    if project:
        goals += project.statements("Why", "User Intent")
        constraints += project.statements("Constraints", "Non-goals")
    if decisions_doc:
        for heading in decisions_doc.sections:
            decisions += decisions_doc.statements(heading)
    if task_plan:
        goals += task_plan.statements("Goal", "Context", "目标、背景与边界", "可观察行为")
        constraints += task_plan.statements(
            "Requirements", "Constraints", "Non-goals", "当前不做", "每张卡共同执行约束",
            "允许写范围", "权限、预算与停止",
        )
        remaining_work += task_plan.statements("Remaining", "待完成")
        blockers += task_plan.statements("Issues", "Blockers")
        declared_status += task_plan.statements("Status", "状态与唯一下一步")
        next_steps += task_plan.statements("Next", "Next Step")
    if progress:
        blockers += progress.statements("Issues", "Blockers")
        declared_status += progress.statements("Current")
        completed += progress.statements("Done")
        remaining_work += progress.statements("Remaining", "待完成")
        next_steps = progress.statements("Next", "Next Step") or next_steps

    for b in blockers:
        b_text = str(b["text"]).casefold()
        if re.search(r"\b(fail(?:ed|ure)?|blocked|error)\b|失败|阻塞|错误", b_text):
            failed.append(b)
        elif re.search(r"\bunknown\b|未知", b_text):
            unknown_items.append(b)

    goals = _bounded("goals", goals, issues)
    constraints = _bounded("constraints", constraints, issues)
    decisions = _bounded("decisions", decisions, issues)
    completed = _bounded("work_summary.completed", completed, issues)
    failed = _bounded("work_summary.failed", failed, issues)
    unknown_items = _bounded("work_summary.unknown", unknown_items, issues)
    remaining_work = _bounded("remaining_work", remaining_work, issues)
    next_steps = _bounded("next_step", next_steps, issues)

    if len(next_steps) == 1:
        next_step_state = "selected"
        sole_next_step = next_steps[0]
        next_sources = [sole_next_step["source"]]
    elif len(next_steps) > 1:
        next_step_state = "ambiguous"
        sole_next_step = None
        next_sources = [ns["source"] for ns in next_steps[:10]]
        issues.append({"code": "next_step_ambiguous", "severity": "warning", "field": "next_step",
                       "message": f"Multiple ({len(next_steps)}) next steps declared; unambiguous sole step required."})
    else:
        next_step_state = "unknown"
        sole_next_step = None
        next_sources = []
        issues.append({"code": "next_step_missing", "severity": "warning", "field": "next_step",
                       "message": "No next step declared."})

    next_step_model = {
        "state": next_step_state,
        "statement": sole_next_step,
        "sources": next_sources,
    }

    ev_sources = [s for s in (progress, findings, task_plan) if s is not None]
    evidence_bindings = extract_evidence_bindings(ev_sources, repo_root, snapshot=snapshot) if snapshot else []

    # Scan git dirty with explicit task path and selected paths
    sel_set = set(selected_paths or [])
    dirty_summary, dirty_entries = scan_git_dirty(repo_root, observed_head, task_path, sel_set, snapshot=snapshot) if snapshot else ({"staged_count": 0, "unstaged_count": 0, "untracked_count": 0}, [])
    is_clean = len(dirty_entries) == 0

    head_matches = observed_head == expected_head if observed_head is not None else False
    if not head_matches:
        issues.append({"code": "head_stale", "severity": "error", "field": "baseline",
                       "message": f"Observed HEAD {observed_head} does not match expected HEAD {expected_head}."})

    scope_fingerprint = compute_scope_fingerprint(
        observed_head,
        coverage,
        dirty_entries,
        evidence_bindings,
    )

    is_cancelled = False
    all_status_statements = declared_status + blockers
    for stmt in all_status_statements:
        text = str(stmt["text"]).casefold()
        if re.search(r"\b(cancel(?:led|ed)?)\b|已取消|取消", text):
            is_cancelled = True
            break
    if is_cancelled:
        issues.append({"code": "task_cancelled", "severity": "warning", "field": "declared_status",
                       "message": "Task is declared cancelled; handoff is non-executable."})

    current_classes = _classifications(declared_status)
    classes = current_classes | _classifications(blockers)
    has_status_conflict = len(current_classes) > 1 or ("done" in classes and ("failed" in classes or "unknown" in classes))
    if has_status_conflict:
        issues.append({"code": "declared_status_conflict", "severity": "warning", "field": "declared_status",
                       "message": "Conflicting status declarations coexisting with failed/unknown blockers."})

    if not evidence_bindings or any(e["evidence_sha256"] is None or e["status"] == "failed" for e in evidence_bindings):
        issues.append({"code": "evidence_unavailable", "severity": "warning", "field": "evidence",
                       "message": "Evidence is absent, missing or declared failed; no acceptance is inferred."})
    has_errors = any(item["severity"] == "error" for item in issues)
    if has_errors:
        state = "blocked"
        executable = False
    elif is_cancelled:
        state = "cancelled"
        executable = False
    elif not head_matches or observed_head is None:
        state = "stale"
        executable = False
    elif has_status_conflict or next_step_state != "selected" or task_state != "selected":
        state = "rejected"
        executable = False
    elif not goals or not constraints or len(failed) > 0 or not evidence_bindings or any(e["evidence_sha256"] is None or e["status"] == "failed" for e in evidence_bindings):
        state = "rejected"
        executable = False
    else:
        state = "ready"
        executable = True

    handoff = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "state": state,
        "executable": executable,
        "project": project_identity,
        "task": task,
        "goals": goals,
        "constraints": constraints,
        "decisions": decisions,
        "work_summary": {
            "completed": completed,
            "failed": failed,
            "unknown": unknown_items,
        },
        "remaining_work": remaining_work,
        "next_step": next_step_model,
        "baseline": {
            "observed_head": observed_head,
            "expected_head": expected_head,
            "head_matches": head_matches,
            "scope_fingerprint": scope_fingerprint,
            "coverage": coverage,
        },
        "dirty_coverage": {
            "is_clean": is_clean,
            "scope": {"task_path": task_path, "selected_paths": sorted(sel_set),
                      "outside_scope": "unknown"},
            "summary": dirty_summary,
            "entries": dirty_entries,
        },
        "evidence_bindings": evidence_bindings,
        "issues": issues,
    }
    handoff["baseline"]["scope_fingerprint"] = material_fingerprint(handoff)
    return validate("specmesh-handoff", handoff)


def verify_pre_consumption(handoff, repo_root, *, observe=None):
    """Compare against a live observation supplied by a caller-bound service."""
    issues = []
    def issue(code, field, message):
        issues.append({"code": code, "severity": "error", "field": field, "message": message})
    try:
        validate("specmesh-handoff", handoff)
        if observe is None:
            raise ValueError("trusted_task_scope_required")
        if material_fingerprint(handoff) != handoff["baseline"]["scope_fingerprint"]:
            issue("scope_fingerprint_mismatch", "baseline", "Material digest differs.")
        live = observe()
        if not handoff["executable"] or handoff["state"] != "ready":
            issue("handoff_not_ready", "handoff", "Input is not ready.")
        if handoff["state"] == "cancelled":
            issue("task_cancelled", "task", "Input declares cancellation.")
        if not live["executable"]:
            issue("live_handoff_not_ready", "handoff", "Current observation cannot be consumed.")
            issues.extend(live["issues"])
        if live["state"] == "cancelled":
            issue("task_cancelled_in_worktree", "task", "Current task declares cancellation.")
        if handoff["baseline"]["observed_head"] != live["baseline"]["observed_head"]:
            issue("head_stale", "baseline", "HEAD changed.")
        previous = {e["path"]: e for e in handoff["dirty_coverage"]["entries"]}
        current = {e["path"]: e for e in live["dirty_coverage"]["entries"]}
        for path in sorted(set(previous) | set(current)):
            if path not in current:
                issue("dirty_file_missing", "dirty_coverage", path)
            elif path not in previous:
                issue("dirty_coverage_omission", "dirty_coverage", path)
            else:
                if previous[path]["staged_sha256"] != current[path]["staged_sha256"]:
                    issue("staged_content_mismatch", "dirty_coverage", path)
                if previous[path]["worktree_sha256"] != current[path]["worktree_sha256"]:
                    issue("dirty_hash_mismatch", "dirty_coverage", path)
        current_ev = {e["evidence_ref"]: e for e in live["evidence_bindings"]}
        for ev in handoff["evidence_bindings"]:
            found = current_ev.get(ev["evidence_ref"])
            if not found or found["evidence_sha256"] is None:
                issue("evidence_file_missing", "evidence", "Previously bound evidence is missing.")
            elif ev["evidence_sha256"] != found["evidence_sha256"]:
                issue("evidence_file_modified", "evidence", "Evidence bytes changed.")
        if material_fingerprint(handoff) != material_fingerprint(live):
            issue("live_material_mismatch", "handoff", "Source-derived content or scope differs from the input.")
    except (ValueError, OSError, RuntimeError, TypeError) as exc:
        issue("handoff_verification_failed", "handoff", type(exc).__name__ + ": " + str(exc)[:200])
    return {"schema_version": HANDOFF_SCHEMA_VERSION, "verified": not issues,
            "executable": not issues, "state": "blocked" if issues else "ready", "issues": issues}


def render_handoff(handoff: dict[str, object]) -> str:
    """Render the handoff material in human-readable Markdown with safe character escaping."""
    lines = [
        "# SpecMesh handoff v1",
        f"state: {_visible(handoff['state'])}",
        f"executable: {str(handoff['executable']).lower()}",
    ]
    baseline = handoff["baseline"]
    lines += [
        f"observed_head: {_visible(baseline['observed_head'] or 'unknown')}",
        f"expected_head: {_visible(baseline['expected_head'])}",
        f"head_matches: {str(baseline['head_matches']).lower()}",
        f"scope_fingerprint: {_visible(baseline['scope_fingerprint'])}",
    ]

    project, task = handoff["project"], handoff["task"]
    p_sources = ", ".join(_source_text(s) for s in project["sources"]) or "no source"
    t_sources = ", ".join(_source_text(s) for s in task["sources"]) or "no source"
    lines += [
        f"project: {_visible(project['value'] or 'unknown')} [{_visible(project['state'])}; {p_sources}]",
        f"task: {_visible(task['value'] or 'unknown')} [{_visible(task['state'])}; {t_sources}]",
        f"task_path: {_visible(task['path'] or 'unknown')}",
    ]

    next_step = handoff["next_step"]
    lines.append(f"next_step_state: {_visible(next_step['state'])}")
    if next_step["statement"]:
        stmt = next_step["statement"]
        lines.append(f"sole_next_step: {_visible(stmt['text'])} ({_source_text(stmt['source'])})")
    else:
        lines.append("sole_next_step: none")

    for key, title in (
        ("goals", "Goals"),
        ("constraints", "Constraints"),
        ("decisions", "Decisions"),
        ("remaining_work", "Remaining work"),
    ):
        lines.append(f"\n## {title}")
        rows = handoff.get(key, [])
        if not rows:
            lines.append("- unknown")
        for row in rows:
            lines.append(f"- {_visible(row['text'])} (authority:{_visible(row['authority'])}; {_source_text(row['source'])})")

    lines.append("\n## Work summary")
    ws = handoff["work_summary"]
    lines.append("### Completed")
    if not ws["completed"]:
        lines.append("- none")
    for row in ws["completed"]:
        lines.append(f"- {_visible(row['text'])} ({_source_text(row['source'])})")

    lines.append("### Failed")
    if not ws["failed"]:
        lines.append("- none")
    for row in ws["failed"]:
        lines.append(f"- {_visible(row['text'])} ({_source_text(row['source'])})")

    lines.append("### Unknown")
    if not ws["unknown"]:
        lines.append("- none")
    for row in ws["unknown"]:
        lines.append(f"- {_visible(row['text'])} ({_source_text(row['source'])})")

    lines.append("\n## Dirty coverage")
    dc = handoff["dirty_coverage"]
    lines.append(f"is_clean: {str(dc['is_clean']).lower()}")
    scope = dc["scope"]
    lines.append(f"task subtree: {_visible(scope['task_path'])}")
    lines.append("selected files: " + ", ".join(_visible(p) for p in scope["selected_paths"]))
    lines.append("outside scope: unknown")
    sm = dc["summary"]
    lines.append(f"staged: {sm['staged_count']}, unstaged: {sm['unstaged_count']}, untracked: {sm['untracked_count']}")
    if not dc["entries"]:
        lines.append("- no dirty entries observed in covered scope (see issues for observation failures)")
    for entry in dc["entries"]:
        st_sha = f" staged_sha256:{_visible(entry['staged_sha256'])}" if entry.get("staged_sha256") else ""
        lines.append(
            f"- {_visible(entry['path'])} [{_visible(entry['kind'])}]{st_sha} sha256:{_visible(entry['worktree_sha256'])} locator:{_visible(entry['locator'])}"
        )

    lines.append("\n## Evidence bindings")
    eb = handoff.get("evidence_bindings", [])
    if not eb:
        lines.append("- none")
    for row in eb:
        reviewer_info = f" reviewer:{_visible(row['reviewer'])}" if row.get("reviewer") else ""
        head_info = f" baseline_head:{_visible(row['baseline_head'])}" if row.get("baseline_head") else ""
        sha_info = f" sha256:{_visible(row['evidence_sha256'])}" if row.get("evidence_sha256") else ""
        lines.append(
            f"- {_visible(row['statement'])} [status:{_visible(row['status'])}; external:{str(row['is_external']).lower()}{reviewer_info}{head_info}{sha_info}]"
        )

    lines.append("\n## Issues")
    issues = handoff.get("issues", [])
    if not issues:
        lines.append("- none")
    for item in issues:
        lines.append(
            f"- {_visible(item['severity'])} {_visible(item['code'])} [{_visible(item['field'])}]: {_visible(item['message'])}"
        )

    return "\n".join(lines) + "\n"
