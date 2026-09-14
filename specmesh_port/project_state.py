"""Bounded extraction and rendering for the optional project-state view."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


STATE_SCHEMA_VERSION = "specmesh.project-state.v1"


@dataclass(frozen=True)
class MarkdownSection:
    name: str
    line: int
    rows: tuple[tuple[int, str], ...]


class MarkdownStateSource:
    """Parse only headings and source lines; never interpret Markdown as commands."""

    def __init__(self, path: str, raw: bytes):
        self.path = path
        self.raw = raw
        self.sha256 = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8")
        visible_lines: list[str] = []
        self.title: tuple[int, str] | None = None
        sections: dict[str, list[MarkdownSection]] = {}
        current_name: str | None = None
        current_line = 0
        current_rows: list[tuple[int, str]] = []

        def finish() -> None:
            nonlocal current_name, current_line, current_rows
            if current_name is not None:
                section = MarkdownSection(current_name, current_line, tuple(current_rows))
                sections.setdefault(_heading_key(current_name), []).append(section)
            current_name, current_line, current_rows = None, 0, []

        fence: tuple[str, int] | None = None
        for number, line in enumerate(text.splitlines(), start=1):
            marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
            if fence is not None:
                closing = re.match(r"^ {0,3}(`{3,}|~{3,})[ \t]*$", line)
                if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= fence[1]:
                    fence = None
                continue
            if marker:
                fence = (marker.group(1)[0], len(marker.group(1)))
                continue
            if line.startswith("    ") or line.startswith("\t"):
                continue
            visible_lines.append(line)
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if heading:
                depth, name = len(heading.group(1)), heading.group(2).strip()
                if depth == 1 and self.title is None:
                    self.title = (number, name)
                if depth >= 2:
                    finish()
                    current_name, current_line = name, number
                continue
            label = re.match(r"^\*\*(.+?)[。.:：]?\*\*\s*(.*)$", line.strip())
            if label:
                finish()
                current_name, current_line = label.group(1).strip(), number
                if label.group(2).strip():
                    current_rows.append((number, label.group(2).strip()))
                continue
            if current_name is not None:
                current_rows.append((number, line))
        finish()
        self.sections = sections
        self.visible_text = "\n".join(visible_lines)

    def source(self, start: int, end: int | None = None) -> dict[str, object]:
        return {"path": self.path, "line_start": start, "line_end": end or start, "sha256": self.sha256}

    def title_statement(self) -> dict[str, object] | None:
        if self.title is None:
            return None
        line, text = self.title
        return _statement(text, self.source(line))

    def statements(self, *headings: str) -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        for heading in headings:
            for section in self.sections.get(_heading_key(heading), []):
                for index, (line, raw) in enumerate(section.rows):
                    text = raw.strip()
                    if not text or text.startswith("```") or _separator(text):
                        continue
                    if (text.startswith("|") and index + 1 < len(section.rows)
                            and _separator(section.rows[index + 1][1].strip())):
                        continue
                    result.append(_statement(text, self.source(line)))
        return result

    def has_section(self, *headings: str) -> bool:
        return any(_heading_key(heading) in self.sections for heading in headings)

    def linked_task_candidates(self) -> list[str]:
        candidates = set()
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", self.visible_text):
            path = target.split("#", 1)[0]
            if re.fullmatch(r"plans/[^/]+/task_plan\.md", path):
                candidates.add(path.rsplit("/", 1)[0])
        return sorted(candidates)


def _heading_key(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", value.casefold()).strip()


def _separator(value: str) -> bool:
    return bool(re.fullmatch(r"[-:|\s]+", value))


def _statement(text: str, source: dict[str, object]) -> dict[str, object]:
    return {"text": text, "authority": "asserted_candidate", "source": source}


def _classifications(rows: list[dict[str, object]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        text = str(row["text"]).casefold()
        if re.search(r"\b(fail(?:ed|ure)?|blocked|error)\b|失败|阻塞|错误", text):
            result.add("failed")
        if re.search(r"\b(complete(?:d)?|done|pass(?:ed)?|success)\b|完成|通过", text):
            result.add("done")
        if re.search(r"\b(in[ -]?progress|working)\b|进行中|正在", text):
            result.add("in_progress")
        if re.search(r"\bready\b|未启动|待开始", text):
            result.add("ready")
        if re.search(r"\bunknown\b|未知", text):
            result.add("unknown")
    return result


def _bounded(
    field: str, rows: list[dict[str, object]], issues: list[dict[str, object]]
) -> list[dict[str, object]]:
    oversized = [row for row in rows if len(str(row["text"])) > 4096]
    if oversized:
        issues.append({"code": "state_statement_too_large", "severity": "warning", "field": field,
                       "message": f"{len(oversized)} source statement(s) exceed the 4096-character output limit."})
    kept = [row for row in rows if len(str(row["text"])) <= 4096]
    if len(kept) > 200:
        issues.append({"code": "state_statement_limit", "severity": "warning", "field": field,
                       "message": f"{len(kept)} source statements exceed the 200-item output limit."})
        kept = kept[:200]
    return kept


def build_project_state(
    *,
    project: MarkdownStateSource | None,
    task_plan: MarkdownStateSource | None,
    findings: MarkdownStateSource | None,
    progress: MarkdownStateSource | None,
    task_path: str | None,
    observed_head: str | None,
    expected_head: str,
    coverage: list[dict[str, object]],
    issues: list[dict[str, object]],
) -> dict[str, object]:
    project_title = project.title_statement() if project else None
    task_title = task_plan.title_statement() if task_plan else None
    if project_title and len(str(project_title["text"])) > 4096:
        issues.append({"code": "state_statement_too_large", "severity": "warning", "field": "project_identity",
                       "message": "Project identity exceeds the 4096-character output limit."})
        project_title = None
    if task_title and len(str(task_title["text"])) > 4096:
        issues.append({"code": "state_statement_too_large", "severity": "warning", "field": "task",
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
    success = []
    blockers = []
    declared_status = []
    evidence = []
    history = []
    next_steps = []
    blockers_declared = False
    if project:
        goals += project.statements("Why", "User Intent")
        constraints += project.statements("Constraints", "Non-goals")
        success += project.statements("Success")
    if task_plan:
        goals += task_plan.statements("Goal", "Context", "目标、背景与边界", "可观察行为")
        constraints += task_plan.statements(
            "Requirements", "Constraints", "Non-goals", "当前不做", "每张卡共同执行约束",
            "允许写范围", "权限、预算与停止",
        )
        success = task_plan.statements("Success", "冻结验收清单（全部满足才关闭 S1）") or success
        blockers += task_plan.statements("Issues", "Blockers")
        blockers_declared = blockers_declared or task_plan.has_section("Issues", "Blockers")
        declared_status += task_plan.statements("Status", "状态与唯一下一步")
        next_steps += task_plan.statements("Next", "Next Step")
    if progress:
        blockers += progress.statements("Issues", "Blockers")
        blockers_declared = blockers_declared or progress.has_section("Issues", "Blockers")
        declared_status += progress.statements("Current")
        history += progress.statements("Done")
        evidence += progress.statements("Verification", "Evidence", "本轮自查")
        next_steps = progress.statements("Next", "Next Step") or next_steps
    if findings:
        evidence += findings.statements("Evidence", "Verification", "验证", "已通过基线与尚未覆盖的条件")

    values = {
        "goals": goals,
        "constraints": constraints,
        "success_criteria": success,
        "blockers": blockers,
        "declared_status": declared_status,
        "evidence": evidence,
        "history": history,
        "next_steps": next_steps,
    }
    for field, rows in tuple(values.items()):
        values[field] = _bounded(field, rows, issues)
    goals = values["goals"]
    constraints = values["constraints"]
    success = values["success_criteria"]
    blockers = values["blockers"]
    declared_status = values["declared_status"]
    evidence = values["evidence"]
    history = values["history"]
    next_steps = values["next_steps"]

    required = {
        "project_identity": bool(project_title),
        "task": bool(task_title),
        "goals": bool(goals),
        "constraints": bool(constraints),
        "success_criteria": bool(success),
        "blockers": blockers_declared,
        "declared_status": bool(declared_status),
        "evidence": bool(evidence),
        "next_steps": bool(next_steps),
    }
    for field, present in required.items():
        if not present:
            issues.append({"code": "state_field_unknown", "severity": "warning", "field": field,
                           "message": f"No supported source statement was found for {field}."})
    if not task_path:
        code = "task_selection_ambiguous" if len(candidates) > 1 else "task_selection_required"
        message = "Multiple task candidates are linked; select task_path explicitly." if len(candidates) > 1 else "Select task_path explicitly; linked candidates are not auto-selected."
        issues.append({"code": code, "severity": "warning", "field": "task", "message": message})
    if len(next_steps) > 1:
        issues.append({"code": "next_step_ambiguous", "severity": "warning", "field": "next_steps",
                       "message": "More than one next-step statement is present."})

    current_classes = _classifications(declared_status)
    classes = current_classes | _classifications(blockers)
    if len(current_classes) > 1 or ("done" in classes and ("failed" in classes or "unknown" in classes)):
        issues.append({"code": "declared_status_conflict", "severity": "warning", "field": "declared_status",
                       "message": "Conflicting current declarations or completion with failed/unknown blockers; "
                                  "no completion is inferred. Current classes: " + ", ".join(sorted(current_classes))})

    if any(item["severity"] == "error" for item in issues):
        state = "blocked"
    elif task_state == "ambiguous" or any(item["code"] in {"declared_status_conflict", "next_step_ambiguous"} for item in issues):
        state = "ambiguous"
    elif (not all(required.values()) or not task_path or observed_head is None
          or any(item["code"] in {"state_statement_too_large", "state_statement_limit", "task_candidate_limit"} for item in issues)):
        state = "unknown"
    else:
        state = "observed"

    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "state": state,
        "project": project_identity,
        "task": task,
        "goals": goals,
        "constraints": constraints,
        "success_criteria": success,
        "blockers": blockers,
        "declared_status": declared_status,
        "evidence": evidence,
        "history": history,
        "next_steps": next_steps,
        "baseline": {
            "observed_head": observed_head,
            "expected_head": expected_head,
            "head_matches": observed_head == expected_head if observed_head is not None else False,
            "coverage": coverage,
        },
        "issues": issues,
    }


def _visible(value: object) -> str:
    result = []
    for character in str(value):
        code = ord(character)
        if code < 32 or 127 <= code < 160:
            result.append(f"\\x{code:02x}" if code <= 255 else f"\\u{code:04x}")
        else:
            result.append(character)
    return "".join(result)


def _source_text(source: dict[str, object]) -> str:
    return (f"{_visible(source['path'])}:{source['line_start']}; "
            f"sha256:{_visible(source['sha256'])}")


def render_project_state(state: dict[str, object]) -> str:
    lines = ["# SpecMesh project state v1", f"state: {_visible(state['state'])}"]
    baseline = state["baseline"]
    lines += [f"observed_head: {_visible(baseline['observed_head'] or 'unknown')}",
              f"expected_head: {_visible(baseline['expected_head'])}",
              f"head_matches: {str(baseline['head_matches']).lower()}"]
    project, task = state["project"], state["task"]
    project_sources = ", ".join(_source_text(source) for source in project["sources"]) or "no source"
    task_sources = ", ".join(_source_text(source) for source in task["sources"]) or "no source"
    lines += [f"project: {_visible(project['value'] or 'unknown')} [{_visible(project['state'])}; {project_sources}]",
              f"task: {_visible(task['value'] or 'unknown')} [{_visible(task['state'])}; {task_sources}]",
              f"task_path: {_visible(task['path'] or 'unknown')}"]
    if task["candidates"]:
        lines.append("task_candidates: " + ", ".join(_visible(item) for item in task["candidates"]))
    for key, title in (("goals", "Goals"), ("constraints", "Constraints"),
                       ("success_criteria", "Success criteria"), ("blockers", "Blockers"),
                       ("declared_status", "Declared status"), ("evidence", "Evidence"),
                       ("history", "History"),
                       ("next_steps", "Next steps")):
        lines.append(f"\n## {title}")
        rows = state[key]
        if not rows:
            lines.append("- unknown")
        for row in rows:
            source = row["source"]
            lines.append(f"- {_visible(row['text'])} (authority:{_visible(row['authority'])}; {_source_text(source)})")
    lines.append("\n## Coverage")
    for item in baseline["coverage"]:
        lines.append(f"- {_visible(item['path'])} sha256:{_visible(item['sha256'])} tracked:{str(item['tracked']).lower()} modified:{str(item['modified']).lower()}")
    lines.append("\n## Issues")
    if not state["issues"]:
        lines.append("- none")
    for item in state["issues"]:
        lines.append(f"- {_visible(item['severity'])} {_visible(item['code'])} [{_visible(item['field'])}]: {_visible(item['message'])}")
    return "\n".join(lines) + "\n"
