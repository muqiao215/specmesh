import json
import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from specmesh_port.contracts_runtime import validate
from specmesh_port.handoff import render_handoff
from specmesh_port.service import SpecMeshService


class HandoffTests(unittest.TestCase):
    def test_scoped_clean_explicitly_leaves_outside_unknown(self):
        (self.root / "outside.txt").write_text("outside scope\n")
        result = self.service.prepare_handoff(self.request)
        self.assertTrue(result["executable"])
        self.assertTrue(result["dirty_coverage"]["is_clean"])
        scope = result["dirty_coverage"]["scope"]
        self.assertEqual(scope["task_path"], self.request["task_path"])
        self.assertIn("PROJECT.md", scope["selected_paths"])
        self.assertNotIn("outside.txt", scope["selected_paths"])
        self.assertEqual(scope["outside_scope"], "unknown")
        rendered = render_handoff(result)
        self.assertNotIn("- clean worktree", rendered)
        self.assertIn("outside scope: unknown", rendered)

    def test_untracked_internal_symlink_is_not_retained(self):
        (self.root / "outside.txt").write_text("SYNTHETIC OUTSIDE DATA\n")
        alias = self.task / "alias.txt"
        alias.symlink_to("../../outside.txt")
        result = self.service.prepare_handoff(self.request)
        self.assertFalse(result["executable"])
        self.assertIn("unsupported_dirty_entry_mode", json.dumps(result))
        self.assertNotIn("SYNTHETIC OUTSIDE DATA", json.dumps(result))
        alias.unlink()
        alias.write_text("SYNTHETIC OUTSIDE DATA\n")
        verified = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"])
        self.assertFalse(verified["executable"])

    def test_regular_dirty_replaced_by_same_content_symlink_is_rejected(self):
        target = self.task / "note.txt"
        target.write_text("same bytes\n")
        result = self.service.prepare_handoff(self.request)
        self.assertTrue(result["executable"])
        (self.root / "outside.txt").write_text("same bytes\n")
        target.unlink()
        target.symlink_to("../../outside.txt")
        verified = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"])
        self.assertFalse(verified["executable"])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "fixture@example.invalid"], check=True)

        (self.root / "AGENTS.md").write_text("# Project instructions\n", encoding="utf-8")
        (self.root / "PROJECT.md").write_text(
            "# SpecMesh\n\n## Why\nProvide continuity.\n\n## User Intent\nIndependent continuity.\n\n"
            "## Constraints\n- Spec is normative.\n- No daemon.\n\n## Non-goals\nNo ops.\n",
            encoding="utf-8",
        )
        (self.root / "docs").mkdir()
        (self.root / "docs" / "DECISIONS.md").write_text(
            "# Decisions\n\n## Keep continuity separate\nDecided to keep it separate.\n",
            encoding="utf-8",
        )
        self.task = self.root / "plans" / "fixture-task"
        self.task.mkdir(parents=True)
        (self.task / "task_plan.md").write_text(
            "# Fixture Task\n\n## Goal\nComplete fixture.\n\n## Status\nin progress\n\n## Next\nExecute step one.\n",
            encoding="utf-8",
        )
        (self.task / "findings.md").write_text(
            "# Findings\n\n## Evidence\n- Verified baseline check: pass\n",
            encoding="utf-8",
        )
        (self.task / "progress.md").write_text(
            "# Progress\n\n## Current\nin progress\n\n## Done\n- Initialized repository\n\n## Evidence\n- Initial commit verified\n",
            encoding="utf-8",
        )

        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "initial"], check=True)
        self.head = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()

        self.service = SpecMeshService([self.root])
        self.scope_paths = []
        self.request = {
            "contract_version": "specmesh.port.v1-draft",
            "operation": "prepare_handoff",
            "repo_root": str(self.root),
            "expected_head": self.head,
            "task_path": "plans/fixture-task",
            "mode": "read_only",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_handoff_clean_success(self):
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["schema_version"], "specmesh.handoff.v1")
        self.assertEqual(result["state"], "ready")
        self.assertTrue(result["executable"])
        self.assertTrue(result["dirty_coverage"]["is_clean"])
        self.assertEqual(result["dirty_coverage"]["summary"]["staged_count"], 0)
        self.assertEqual(result["dirty_coverage"]["summary"]["unstaged_count"], 0)
        self.assertEqual(result["dirty_coverage"]["summary"]["untracked_count"], 0)
        self.assertEqual(result["next_step"]["state"], "selected")
        self.assertEqual(result["next_step"]["statement"]["text"], "Execute step one.")
        self.assertEqual(result["baseline"]["observed_head"], self.head)
        self.assertTrue(result["baseline"]["head_matches"])
        self.assertRegex(result["baseline"]["scope_fingerprint"], r"^[0-9a-f]{64}$")

        # Verify pre-consumption on clean repo
        v_res = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertTrue(v_res["verified"])
        self.assertTrue(v_res["executable"])
        self.assertEqual(v_res["state"], "ready")

    def test_handoff_staged_and_unstaged_preservation(self):
        # Create a file that is staged AND unstaged
        self.scope_paths = ["work.txt"]
        target = self.root / "work.txt"
        target.write_text("v1-staged\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "work.txt"], check=True)
        target.write_text("v2-unstaged\n", encoding="utf-8")

        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "ready")
        self.assertTrue(result["executable"])
        self.assertFalse(result["dirty_coverage"]["is_clean"])

        entries = [e for e in result["dirty_coverage"]["entries"] if e["path"] == "work.txt"]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["kind"], "staged_and_unstaged")
        self.assertEqual(entry["worktree_sha256"], hashlib.sha256(b"v2-unstaged\n").hexdigest())
        self.assertEqual(entry["retained_content"], "v2-unstaged\n")
        self.assertEqual(entry["locator"], "code://work.txt")

        # Verify against this repo passes
        v_res = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertTrue(v_res["verified"])
        self.assertTrue(v_res["executable"])

        # Verify against a separate clean repo (without dirty files) rejects execution
        with tempfile.TemporaryDirectory() as other_tmp:
            subprocess.run(["git", "clone", "-q", str(self.root), other_tmp], check=True)
            other_service = SpecMeshService([other_tmp])
            v_other = other_service.verify_handoff(result, other_tmp, task_path=self.request["task_path"], paths=self.scope_paths)
            self.assertFalse(v_other["executable"])
            self.assertEqual(v_other["state"], "blocked")
            codes = [i["code"] for i in v_other["issues"]]
            self.assertIn("dirty_file_missing", codes)

    def test_handoff_relevant_untracked_file(self):
        untracked = self.task / "notes.md"
        untracked.write_text("# Untracked note\n", encoding="utf-8")

        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "ready")
        self.assertTrue(result["executable"])

        entries = [e for e in result["dirty_coverage"]["entries"] if e["path"] == "plans/fixture-task/notes.md"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["kind"], "untracked")
        self.assertEqual(entries[0]["retained_content"], "# Untracked note\n")

        v_res = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertTrue(v_res["verified"])
        self.assertTrue(v_res["executable"])

        # If deleted, pre-consumption check rejects
        untracked.unlink()
        v_deleted = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_deleted["executable"])
        self.assertIn("dirty_file_missing", [i["code"] for i in v_deleted["issues"]])

    def test_handoff_same_head_modified_rejection(self):
        self.scope_paths = ["dirty.txt"]
        target = self.root / "dirty.txt"
        target.write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "dirty.txt"], check=True)

        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "ready")

        # Now modify content at the same HEAD
        target.write_text("modified\n", encoding="utf-8")
        v_res = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_res["executable"])
        self.assertIn("dirty_hash_mismatch", [i["code"] for i in v_res["issues"]])

    def test_handoff_stale_head_rejection(self):
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "ready")

        # Create a new commit to advance HEAD
        dummy = self.root / "dummy.txt"
        dummy.write_text("dummy\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "dummy.txt"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "advance head"], check=True)

        v_res = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_res["executable"])
        self.assertIn("head_stale", [i["code"] for i in v_res["issues"]])

    def test_handoff_cancelled_task_rejection(self):
        (self.task / "progress.md").write_text(
            "# Progress\n\n## Current\nTask is cancelled.\n\n## Done\n- none\n",
            encoding="utf-8",
        )
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "cancelled")
        self.assertFalse(result["executable"])

        v_res = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_res["executable"])
        self.assertIn("task_cancelled", [i["code"] for i in v_res["issues"]])

    def test_handoff_failure_with_old_done_conflict(self):
        (self.task / "task_plan.md").write_text(
            "# Fixture Task\n\n## Goal\nComplete fixture.\n\n## Status\ndone\n\n## Next\nNext step.\n",
            encoding="utf-8",
        )
        (self.task / "progress.md").write_text(
            "# Progress\n\n## Current\nin progress\n\n## Issues\n- Blocker: fatal error encountered\n",
            encoding="utf-8",
        )
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "rejected")
        self.assertFalse(result["executable"])
        self.assertIn("declared_status_conflict", [i["code"] for i in result["issues"]])

    def test_handoff_ambiguous_next_step(self):
        (self.task / "task_plan.md").write_text(
            "# Fixture Task\n\n## Goal\nComplete fixture.\n\n## Status\nin progress\n\n## Next\n- First step\n- Second step\n",
            encoding="utf-8",
        )
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["next_step"]["state"], "ambiguous")
        self.assertIsNone(result["next_step"]["statement"])
        self.assertEqual(result["state"], "rejected")
        self.assertFalse(result["executable"])

    def test_handoff_evidence_binding(self):
        ev_dir = self.task / "evidence"
        ev_dir.mkdir()
        ev_file = ev_dir / "acceptance.md"
        ev_file.write_text(
            f"# Acceptance\n\n审查者: independent reviewer /root/reviewer\nHEAD: {self.head}\nResult: accepted\n",
            encoding="utf-8",
        )
        (self.task / "findings.md").write_text(
            "# Findings\n\n## Evidence\n- Independent review completed: [acceptance](evidence/acceptance.md)\n",
            encoding="utf-8",
        )
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "ready")
        ebs = [e for e in result["evidence_bindings"] if e.get("evidence_ref", "").endswith("acceptance.md")]
        self.assertGreaterEqual(len(ebs), 1)
        eb = ebs[0]
        self.assertEqual(eb["status"], "passed")
        self.assertFalse(eb["is_external"])
        self.assertIn("reviewer", eb["reviewer"].lower())
        self.assertEqual(eb["baseline_head"], self.head)
        self.assertIsNotNone(eb["evidence_sha256"])

    def test_p1_verifier_rejects_tampered_payload_and_mid_state_change(self):
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertTrue(result["executable"])

        # 1. Modifying progress.md in repo to 'Task is cancelled' at same HEAD must be detected
        (self.task / "progress.md").write_text("# Progress\n\n## Current\nTask is cancelled.\n\n## Done\n- none\n", encoding="utf-8")
        v_cancelled = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_cancelled["executable"])
        self.assertEqual(v_cancelled["state"], "blocked")
        self.assertIn("task_cancelled_in_worktree", [i["code"] for i in v_cancelled["issues"]])

        # 2. Tampering payload to fake ready/executable and blank fingerprint must fail closed
        tampered = json.loads(json.dumps(result))
        tampered["state"] = "ready"
        tampered["executable"] = True
        tampered["baseline"]["scope_fingerprint"] = "0" * 64
        v_tampered = self.service.verify_handoff(tampered, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_tampered["executable"])
        self.assertIn("scope_fingerprint_mismatch", [i["code"] for i in v_tampered["issues"]])

    def test_p1_staged_blob_bound_and_index_change_rejected(self):
        self.scope_paths = ["staged_work.txt"]
        work_file = self.root / "staged_work.txt"
        work_file.write_text("v1-staged\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "staged_work.txt"], check=True)
        work_file.write_text("v2-worktree\n", encoding="utf-8")

        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result["state"], "ready")
        entry = [e for e in result["dirty_coverage"]["entries"] if e["path"] == "staged_work.txt"][0]
        self.assertEqual(entry["kind"], "staged_and_unstaged")
        self.assertEqual(entry["staged_sha256"], hashlib.sha256(b"v1-staged\n").hexdigest())
        self.assertEqual(entry["staged_content"], "v1-staged\n")
        self.assertEqual(entry["worktree_sha256"], hashlib.sha256(b"v2-worktree\n").hexdigest())

        # Verify on this state passes
        v_ok = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertTrue(v_ok["executable"])

        # Change index via git add while worktree remains v2-worktree
        work_file.write_text("v3-staged\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "staged_work.txt"], check=True)
        work_file.write_text("v2-worktree\n", encoding="utf-8")

        v_idx = self.service.verify_handoff(result, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_idx["executable"])
        self.assertIn("staged_content_mismatch", [i["code"] for i in v_idx["issues"]])

    def test_p1_unrelated_untracked_and_array_limit(self):
        # 1. Unrelated untracked file at root must NOT be included in task handoff
        token_file = self.root / "private-token.txt"
        token_file.write_text("super-secret-token\n", encoding="utf-8")

        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        paths = [e["path"] for e in result["dirty_coverage"]["entries"]]
        self.assertNotIn("private-token.txt", paths)

        # 2. 101 untracked files in root must not cause schema ValidationError
        for i in range(101):
            (self.root / f"extra_{i}.txt").write_text(f"extra {i}\n", encoding="utf-8")
        result2 = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(result2["schema_version"], "specmesh.handoff.v1")
        self.assertLessEqual(len(result2["dirty_coverage"]["entries"]), 100)

    def test_p1_evidence_security_and_deletion_rejected(self):
        # 1. Path traversal and absolute link to /tmp must not be read
        (self.task / "findings.md").write_text(
            "# Findings\n\n## Evidence\n- Leak attempt: [leak](/tmp/leak.txt)\n- Traversal: [bad](../../../etc/passwd)\n",
            encoding="utf-8",
        )
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        ebs = [e for e in result["evidence_bindings"] if e.get("evidence_ref")]
        self.assertFalse(any(e["evidence_ref"].startswith("/") or ".." in Path(e["evidence_ref"]).parts for e in ebs))
        self.assertFalse(result["executable"])

        # 2. Deleting an existing valid evidence file causes verification rejection
        ev_dir = self.task / "evidence"
        ev_dir.mkdir()
        ev_file = ev_dir / "valid_acceptance.md"
        ev_file.write_text(f"# Acceptance\nHEAD: {self.head}\nResult: accepted\n", encoding="utf-8")
        (self.task / "findings.md").write_text(
            "# Findings\n\n## Evidence\n- Valid review: [acceptance](evidence/valid_acceptance.md)\n",
            encoding="utf-8",
        )
        h_with_ev = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        self.assertEqual(h_with_ev["state"], "ready")

        # Now delete the evidence file
        ev_file.unlink()
        v_del = self.service.verify_handoff(h_with_ev, self.root, task_path=self.request["task_path"], paths=self.scope_paths)
        self.assertFalse(v_del["executable"])
        self.assertIn("evidence_file_missing", [i["code"] for i in v_del["issues"]])

    def test_handoff_text_rendering_escapes_controls(self):
        result = self.service.prepare_handoff(self.request, paths=self.scope_paths)
        text = render_handoff(result)
        self.assertIn("# SpecMesh handoff v1", text)
        self.assertIn("state: ready", text)
        self.assertIn("executable: true", text)
        self.assertIn("sole_next_step: Execute step one.", text)
        self.assertNotIn("\x00", text)
        self.assertNotIn("\x1b", text)

    def test_cli_handoff_and_verify(self):
        # 1. CLI --handoff json
        p_json = subprocess.run(
            ["python3", "-B", "-m", "specmesh_port", "--allowed-root", str(self.root), "--handoff", "json"],
            input=json.dumps(self.request),
            text=True,
            capture_output=True,
        )
        self.assertEqual(p_json.returncode, 0, p_json.stderr)
        data = json.loads(p_json.stdout)
        self.assertEqual(data["state"], "ready")
        self.assertTrue(data["executable"])

        # 2. CLI --handoff text
        p_text = subprocess.run(
            ["python3", "-B", "-m", "specmesh_port", "--allowed-root", str(self.root), "--handoff", "text"],
            input=json.dumps(self.request),
            text=True,
            capture_output=True,
        )
        self.assertEqual(p_text.returncode, 0, p_text.stderr)
        self.assertIn("# SpecMesh handoff v1", p_text.stdout)

        # 3. CLI --verify-handoff with file
        h_file = self.root / "handoff.json"
        h_file.write_text(json.dumps(data), encoding="utf-8")
        p_verify = subprocess.run(
            ["python3", "-B", "-m", "specmesh_port", "--allowed-root", str(self.root), "--task-path", self.request["task_path"], "--verify-handoff", str(h_file)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(p_verify.returncode, 0, p_verify.stderr)
        v_data = json.loads(p_verify.stdout)
        self.assertTrue(v_data["verified"])
        self.assertTrue(v_data["executable"])

        # 4. CLI --verify-handoff with stdin (-)
        p_verify_stdin = subprocess.run(
            ["python3", "-B", "-m", "specmesh_port", "--allowed-root", str(self.root), "--task-path", self.request["task_path"], "--verify-handoff", "-"],
            input=json.dumps(data),
            text=True,
            capture_output=True,
        )
        self.assertEqual(p_verify_stdin.returncode, 0, p_verify_stdin.stderr)

        # 5. Legacy CLI compatibility: request with operation 'prepare_handoff' without --handoff
        p_legacy = subprocess.run(
            ["python3", "-B", "-m", "specmesh_port", "--allowed-root", str(self.root)],
            input=json.dumps(self.request),
            text=True,
            capture_output=True,
        )
        self.assertEqual(p_legacy.returncode, 0, p_legacy.stderr)
        leg_data = json.loads(p_legacy.stdout)
        self.assertEqual(leg_data["contract_version"], "specmesh.port.v1-draft")
        self.assertEqual(leg_data["status"], "pass")


    def test_consumer_requires_independent_scope(self):
        handoff = self.service.prepare_handoff(self.request)
        self.assertFalse(self.service.verify_handoff(handoff, self.root)["executable"])
        self.assertFalse(self.service.verify_handoff(handoff, self.root, task_path="plans/other")["executable"])

    def test_self_signed_semantics_and_empty_coverage_rejected(self):
        from specmesh_port.handoff import material_fingerprint
        original = self.service.prepare_handoff(self.request)
        for field in ("goals", "constraints", "remaining_work", "next_step", "coverage", "evidence"):
            with self.subTest(field=field):
                forged = json.loads(json.dumps(original))
                if field == "next_step":
                    forged["next_step"]["statement"]["text"] = "Do an unauthorized thing."
                elif field == "coverage":
                    forged["baseline"]["coverage"] = []
                elif field == "evidence":
                    forged["evidence_bindings"] = []
                elif field == "remaining_work":
                    forged[field] = [dict(original["goals"][0], text="Injected remaining work.")]
                else:
                    forged[field] = []
                forged["baseline"]["scope_fingerprint"] = material_fingerprint(forged)
                result = self.service.verify_handoff(forged, self.root, task_path=self.request["task_path"])
                self.assertFalse(result["executable"])

    def test_tracked_scope_and_in_scope_overflow(self):
        secret = self.root / "unrelated.txt"
        secret.write_text("synthetic original")
        subprocess.run(["git", "-C", str(self.root), "add", "unrelated.txt"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "unrelated fixture"], check=True)
        self.request["expected_head"] = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        secret.write_text("SYNTHETIC OUTSIDE SCOPE")
        handoff = self.service.prepare_handoff(self.request)
        self.assertTrue(handoff["executable"])
        self.assertNotIn("SYNTHETIC OUTSIDE SCOPE", json.dumps(handoff))
        for i in range(101):
            (self.task / f"extra-{i}.md").write_text("data")
        limited = self.service.prepare_handoff(self.request)
        self.assertFalse(limited["executable"])
        self.assertIn("dirty_coverage_limit_exceeded", [i["message"] for i in limited["issues"]])

    def test_missing_evidence_and_current_conflict_reject(self):
        (self.task / "findings.md").write_text("# Findings\n")
        (self.task / "progress.md").write_text("# Progress\n\n## Current\nin progress\n")
        self.assertFalse(self.service.prepare_handoff(self.request)["executable"])
        (self.task / "findings.md").write_text("# Findings\n\n## Evidence\nBaseline observed.\n")
        (self.task / "task_plan.md").write_text("# Task\n\n## Goal\nFinish.\n\n## Status\ndone\n\n## Next\nContinue.\n")
        conflict = self.service.prepare_handoff(self.request)
        self.assertFalse(conflict["executable"])
        self.assertIn("declared_status_conflict", [i["code"] for i in conflict["issues"]])

    def test_evidence_parent_symlink_and_scope_oversize_reject(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / "proof.md").write_text("SYNTHETIC OUTSIDE")
            (self.task / "evidence").symlink_to(outside, target_is_directory=True)
            (self.task / "findings.md").write_text("# Findings\n\n## Evidence\n[Proof](evidence/proof.md)\n")
            result = self.service.prepare_handoff(self.request)
            self.assertFalse(result["executable"])
            self.assertNotIn("SYNTHETIC OUTSIDE", json.dumps(result))
        (self.task / "evidence").unlink()
        (self.task / "big.txt").write_bytes(b"x" * (262144 + 1))
        self.assertFalse(self.service.prepare_handoff(self.request)["executable"])

    def test_handoff_detects_mid_observation_change(self):
        from unittest.mock import patch
        from specmesh_port.snapshot import DocumentSnapshot
        original = DocumentSnapshot.verify
        def change(snapshot):
            (self.task / "findings.md").write_text("# Changed during observation\n")
            return original(snapshot)
        with patch.object(DocumentSnapshot, "verify", change):
            result = self.service.prepare_handoff(self.request)
        self.assertFalse(result["executable"])

    def test_cli_payload_limits(self):
        command = ["python3", "-B", "-m", "specmesh_port", "--allowed-root", str(self.root),
                   "--task-path", self.request["task_path"], "--verify-handoff"]
        p = subprocess.run(command + ["-"], input=b"x" * (1048576 + 1), capture_output=True, timeout=10)
        self.assertEqual(p.returncode, 2)
        oversized = self.root / "oversized.json"
        oversized.write_bytes(b"x" * (1048576 + 1))
        p = subprocess.run(command + [str(oversized)], capture_output=True, timeout=10)
        self.assertEqual(p.returncode, 2)

    def test_explicit_ignored_file_is_retained_and_revalidated(self):
        (self.root / ".gitignore").write_text("selected.txt\n")
        (self.root / "selected.txt").write_text("selected content\n")
        result = self.service.prepare_handoff(self.request, paths=["selected.txt"])
        self.assertTrue(result["executable"])
        entry = next(e for e in result["dirty_coverage"]["entries"] if e["path"] == "selected.txt")
        self.assertEqual(entry["kind"], "untracked")
        self.assertEqual(entry["retained_content"], "selected content\n")
        self.assertTrue(self.service.verify_handoff(result, self.root,
                        task_path=self.request["task_path"], paths=["selected.txt"])["executable"])
        (self.root / "selected.txt").write_text("changed\n")
        self.assertFalse(self.service.verify_handoff(result, self.root,
                         task_path=self.request["task_path"], paths=["selected.txt"])["executable"])


if __name__ == "__main__":
    unittest.main()
