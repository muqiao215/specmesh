import json
import hashlib
import os
import shlex
import time
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specmesh_port.service import SpecMeshService
from specmesh_port.contracts_runtime import validate
from specmesh_port.project_state import render_project_state
from specmesh_port.snapshot import DocumentSnapshot, MAX_DOCUMENT_BYTES
from specmesh_port.git_reader import read_git, MAX_GIT_OUTPUT

class MachinePortTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        for name in ('AGENTS.md','PROJECT.md'): (self.root/name).write_text('# Fixture\n')
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
        self.head=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        self.service=SpecMeshService([self.root])
        self.request=dict(contract_version='specmesh.port.v1-draft',operation='check',repo_root=str(self.root),expected_head=self.head,task_path=None,mode='read_only')
    def tearDown(self): self.tmp.cleanup()
    def test_independent_check_preserves_repository(self):
        before={p.name:p.read_bytes() for p in self.root.glob('*.md')}
        result=self.service.check(self.request)
        self.assertEqual(result['status'],'pass')
        self.assertEqual(result['references'][0]['authority'],'asserted_candidate')
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.glob('*.md')})
    def test_stale_head_and_missing_task_files_block(self):
        self.request['expected_head']='0'*40
        self.assertEqual(self.service.check(self.request)['status'],'blocked')
        self.request['expected_head']=self.head
        (self.root/'task').mkdir();self.request['task_path']='task'
        result=self.service.check(self.request)
        self.assertEqual(sum(x['code']=='missing_task_entry' for x in result['findings']),3)
    def test_symlink_escape_is_rejected(self):
        (self.root/'PROJECT.md').unlink(); (self.root/'PROJECT.md').symlink_to('/etc/hostname')
        self.assertEqual(self.service.check(self.request)['status'],'blocked')
    def test_closeout_cannot_claim_external_verification(self):
        task=self.root/'task';task.mkdir()
        for name in ('task_plan.md','findings.md','progress.md'): (task/name).write_text('# fixture\n')
        (task/'acceptance.json').write_text(json.dumps([dict(id='test',evidence_ref='fixture',head=self.head,content_digest='b'*64,status='passed')]))
        self.request.update(operation='verify_closeout',task_path='task')
        self.assertEqual(self.service.check(self.request)['status'],'unknown')

    def test_explicit_artifact_requirements_are_candidates_not_execution(self):
        requirements = {"schema_version": "specmesh.artifact_requirements.v1", "files": [{"path": "not-created.txt", "mode": "write"}]}
        path = self.root / "requirements.json"
        path.write_text(json.dumps(requirements))
        before = path.read_bytes()
        self.assertNotIn("artifact_requirements", self.service.check(self.request))
        self.request["requirements_path"] = "requirements.json"
        result = self.service.check(self.request)
        self.assertEqual(result["status"], "pass")
        candidate = result["artifact_requirements"]
        self.assertEqual(candidate["authority"], "asserted_candidate")
        self.assertEqual(candidate["requirements"], requirements)
        self.assertEqual(candidate["sha256"], hashlib.sha256(before).hexdigest())
        self.assertIn("requirements.json", [item["path"] for item in result["references"]])
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.root / "not-created.txt").exists())

    def test_invalid_artifact_requirements_fail_closed(self):
        path = self.root / "requirements.json"
        self.request["requirements_path"] = "requirements.json"
        for files in ([], [{"path": "../outside", "mode": "write"}], [{"path": ".git/config", "mode": "read"}],
                      [{"path": "same", "mode": "write"}] * 2, [{"path": "result", "mode": "execute"}],
                      [{"path": "result", "mode": "write", "sha256": "bad"}]):
            path.write_text(json.dumps({"schema_version": "specmesh.artifact_requirements.v1", "files": files}))
            result = self.service.check(self.request)
            self.assertEqual(result["status"], "blocked")
            self.assertNotIn("artifact_requirements", result)
        self.request["requirements_path"] = "../requirements.json"
        self.assertEqual(self.service.check(self.request)["status"], "blocked")

    def test_artifact_requirements_change_during_snapshot_invalidates_candidate(self):
        path = self.root / "requirements.json"
        path.write_text(json.dumps({"schema_version": "specmesh.artifact_requirements.v1", "files": [{"path": "result", "mode": "write"}]}))
        self.request["requirements_path"] = "requirements.json"
        self.during_metadata(lambda: path.write_text("{}"))
        result = self.service.check(self.request)
        self.assertEqual(result["status"], "blocked")
        self.assertNotIn("artifact_requirements", result)

    def during_metadata(self, action):
        original = self.service._metadata
        calls = 0
        def observe(root, selected):
            nonlocal calls
            result = original(root, selected)
            calls += 1
            if calls == 1:
                action()
            return result
        with patch.object(self.service, '_metadata', side_effect=observe):
            return self.service.check(self.request)

    def _write_state_fixture(self):
        (self.root / 'PROJECT.md').write_text(
            '# Demo Project\n\n'
            '## Why\nKeep project knowledge continuous.\n\n'
            '## User Intent\nShip a standalone state reader.\n\n'
            '## Constraints\n- Stay offline.\n\n'
            '## Success\nA new reader can locate the current work.\n\n'
            '## Knowledge Map\n- Active work → [plan](plans/current/task_plan.md)\n')
        task = self.root / 'plans/current'; task.mkdir(parents=True)
        (task / 'task_plan.md').write_text(
            '# Deliver project state\n\n## Goal\nExpose sourced state.\n\n'
            '## Requirements\n- Preserve legacy output.\n\n## Success\nJSON validates.\n\n'
            '## Status\nin progress\n\n## Next Step\nImplement the state reader.\n')
        (task / 'findings.md').write_text('# Findings\n\n## Evidence\n- Baseline behavior recorded.\n')
        (task / 'progress.md').write_text(
            '# Progress\n\n## Current\nin progress\n\n## Done\n- Fixture prepared.\n\n'
            '## Issues\n\n## Next\nImplement the state reader.\n')
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'state fixture'], check=True)
        self.head = subprocess.check_output(['git', '-C', str(self.root), 'rev-parse', 'HEAD'], text=True).strip()
        self.request.update(operation='inspect', expected_head=self.head, task_path='plans/current')

    def test_project_state_model_is_complete_sourced_and_schema_valid(self):
        self._write_state_fixture()
        state = self.service.project_state(self.request)
        self.assertIs(validate('specmesh-project-state', state), state)
        self.assertEqual(state['schema_version'], 'specmesh.project-state.v1')
        self.assertEqual(state['state'], 'observed')
        self.assertEqual(state['project']['value'], 'Demo Project')
        self.assertEqual(state['task']['value'], 'Deliver project state')
        self.assertEqual(state['baseline']['observed_head'], self.head)
        self.assertTrue(state['baseline']['head_matches'])
        self.assertIn('Expose sourced state.', [row['text'] for row in state['goals']])
        self.assertIn('- Preserve legacy output.', [row['text'] for row in state['constraints']])
        self.assertIn('JSON validates.', [row['text'] for row in state['success_criteria']])
        for field in ('goals', 'constraints', 'success_criteria', 'declared_status', 'evidence', 'next_steps'):
            for row in state[field]:
                self.assertEqual(row['authority'], 'asserted_candidate')
                self.assertRegex(row['source']['sha256'], r'^[0-9a-f]{64}$')
                self.assertGreaterEqual(row['source']['line_start'], 1)

    def test_project_state_reads_labeled_acceptance_table_without_header(self):
        self._write_state_fixture()
        plan = self.root / 'plans/current/task_plan.md'
        plan.write_text(
            '# Deliver project state\n\n## Status\nin progress\n\n'
            '### SM-P0.S1\n\n**可观察行为。**\nRead current state.\n\n'
            '**允许写范围。** Only the state module.\n\n'
            '**冻结验收清单（全部满足才关闭 S1）。**\n\n'
            '| Check | Expected |\n|---|---|\n| S1-A | JSON validates |\n\n'
            '**权限、预算与停止。**\nNo provider calls.\n')
        state = self.service.project_state(self.request)
        self.assertIn('Read current state.', [row['text'] for row in state['goals']])
        self.assertIn('Only the state module.', [row['text'] for row in state['constraints']])
        self.assertIn('No provider calls.', [row['text'] for row in state['constraints']])
        self.assertEqual([row['text'] for row in state['success_criteria']], ['| S1-A | JSON validates |'])

    def test_project_state_json_and_text_share_one_model(self):
        self._write_state_fixture()
        source = Path(__file__).resolve().parents[1]
        command = [os.sys.executable, '-m', 'specmesh_port', '--allowed-root', str(self.root)]
        payload = json.dumps(self.request)
        json_result = subprocess.run(command + ['--project-state', 'json'], cwd=source, input=payload,
                                     capture_output=True, text=True, timeout=10)
        text_result = subprocess.run(command + ['--project-state', 'text'], cwd=source, input=payload,
                                     capture_output=True, text=True, timeout=10)
        self.assertEqual(json_result.returncode, 0, json_result.stderr)
        self.assertEqual(text_result.returncode, 0, text_result.stderr)
        state = json.loads(json_result.stdout)
        self.assertEqual(text_result.stdout, render_project_state(state))
        self.assertIn('PROJECT.md:1; sha256:', text_result.stdout)
        self.assertIn('plans/current/task_plan.md:1; sha256:', text_result.stdout)
        self.assertIn('authority:asserted_candidate', text_result.stdout)
        for field in ('goals', 'constraints', 'success_criteria', 'declared_status', 'evidence', 'next_steps'):
            for row in state[field]:
                self.assertIn(row['text'], text_result.stdout)

    def test_project_state_requires_explicit_task_and_reports_ambiguous_candidates(self):
        (self.root / 'PROJECT.md').write_text(
            '# Demo\n\n## Knowledge Map\n'
            '- [First](plans/first/task_plan.md)\n- [Second](plans/second/task_plan.md)\n')
        self.request.update(operation='inspect', task_path=None)
        state = self.service.project_state(self.request)
        self.assertEqual(state['state'], 'ambiguous')
        self.assertEqual(state['task']['state'], 'ambiguous')
        self.assertEqual(state['task']['candidates'], ['plans/first', 'plans/second'])
        self.assertIn('task_selection_ambiguous', [item['code'] for item in state['issues']])

    def test_missing_evidence_and_conflicting_done_failure_never_complete_state(self):
        self._write_state_fixture()
        (self.root / 'plans/current/findings.md').write_text('# Findings\n')
        (self.root / 'plans/current/progress.md').write_text(
            '# Progress\n\n## Current\ndone\n\n## Issues\n- verification failed\n\n## Next\nRepair validation.\n')
        state = self.service.project_state(self.request)
        self.assertEqual(state['state'], 'ambiguous')
        codes = [item['code'] for item in state['issues']]
        self.assertIn('state_field_unknown', codes)
        self.assertIn('declared_status_conflict', codes)
        self.assertIn('- verification failed', [row['text'] for row in state['blockers']])

    def test_done_and_in_progress_current_declarations_conflict_with_sources(self):
        self._write_state_fixture()
        plan = self.root / 'plans/current/task_plan.md'
        plan.write_text(plan.read_text().replace('## Status\nin progress', '## Status\ndone'))
        state = self.service.project_state(self.request)
        self.assertEqual([row['text'] for row in state['declared_status']], ['done', 'in progress'])
        self.assertEqual(state['state'], 'ambiguous')
        self.assertIn('declared_status_conflict', [issue['code'] for issue in state['issues']])
        self.assertIs(validate('specmesh-project-state', state), state)
        rendered = render_project_state(state)
        for row, path in zip(state['declared_status'],
                             ('plans/current/task_plan.md', 'plans/current/progress.md')):
            self.assertEqual(row['source']['path'], path)
            self.assertGreater(row['source']['line_start'], 0)
            self.assertRegex(row['source']['sha256'], r'^[0-9a-f]{64}$')
            self.assertIn(path, rendered)
        self.assertIn('declared_status_conflict', rendered)

    def test_done_claim_does_not_satisfy_missing_evidence(self):
        self._write_state_fixture()
        (self.root / 'plans/current/findings.md').write_text('# Findings\n')
        (self.root / 'plans/current/progress.md').write_text(
            '# Progress\n\n## Current\nin progress\n\n## Done\n- Implementation claims completion.\n\n'
            '## Issues\n\n## Next\nReview the result.\n')
        state = self.service.project_state(self.request)
        self.assertEqual(state['state'], 'unknown')
        self.assertEqual(state['evidence'], [])
        self.assertIn('- Implementation claims completion.', [row['text'] for row in state['history']])
        self.assertIn('evidence', [item['field'] for item in state['issues'] if item['code'] == 'state_field_unknown'])

    def test_historical_failures_remain_visible_without_changing_current_state(self):
        self._write_state_fixture()
        progress = self.root / 'plans/current/progress.md'
        progress.write_text(progress.read_text().replace('- Fixture prepared.',
                                 '- First review failed.\n- Correction completed.'))
        state = self.service.project_state(self.request)
        self.assertEqual(state['state'], 'observed')
        self.assertEqual([row['text'] for row in state['history']],
                         ['- First review failed.', '- Correction completed.'])
        self.assertNotIn('declared_status_conflict', [item['code'] for item in state['issues']])

    def test_current_status_normalization_preserves_observed_contract(self):
        self._write_state_fixture()
        plan = self.root / 'plans/current/task_plan.md'
        progress = self.root / 'plans/current/progress.md'
        for left, right, expected in (('in progress', 'done', 'ambiguous'),
                                      ('ready', 'in progress', 'ambiguous'),
                                      ('completed', 'done', 'observed'),
                                      ('working', 'in-progress', 'observed')):
            with self.subTest(left=left, right=right):
                plan.write_text('# Task\n\n## Goal\nRead state.\n\n## Success\nRead sources.\n\n## Status\n' + left + '\n')
                progress.write_text('# Progress\n\n## Current\n' + right +
                                    '\n\n## Issues\n\n## Next\nReview.\n\n## Done\nOld attempt failed.\n')
                state = self.service.project_state(self.request)
                self.assertEqual(state['state'], expected)
                self.assertIs(validate('specmesh-project-state', state), state)

    def test_missing_blocker_field_is_unknown_but_empty_heading_is_explicit(self):
        self._write_state_fixture()
        state = self.service.project_state(self.request)
        self.assertEqual(state['state'], 'observed')
        self.assertEqual(state['blockers'], [])
        progress = self.root / 'plans/current/progress.md'
        progress.write_text(progress.read_text().replace('## Issues\n\n', ''))
        missing = self.service.project_state(self.request)
        self.assertEqual(missing['state'], 'unknown')
        self.assertIn('blockers', [item['field'] for item in missing['issues'] if item['code'] == 'state_field_unknown'])

    def test_dirty_state_uses_current_hash_and_declared_coverage(self):
        self._write_state_fixture()
        project = self.root / 'PROJECT.md'
        project.write_text(project.read_text() + '\nCurrent dirty fact.\n')
        before = {path.relative_to(self.root).as_posix(): path.read_bytes()
                  for path in self.root.rglob('*') if path.is_file() and '.git' not in path.parts}
        state = self.service.project_state(self.request)
        project_ref = next(row for row in state['baseline']['coverage'] if row['path'] == 'PROJECT.md')
        self.assertTrue(project_ref['modified'])
        self.assertEqual(project_ref['sha256'], hashlib.sha256(project.read_bytes()).hexdigest())
        after = {path.relative_to(self.root).as_posix(): path.read_bytes()
                 for path in self.root.rglob('*') if path.is_file() and '.git' not in path.parts}
        self.assertEqual(before, after)

    def test_project_state_blocks_stale_head_and_mid_read_change(self):
        self._write_state_fixture()
        self.request['expected_head'] = '0' * 40
        stale = self.service.project_state(self.request)
        self.assertEqual(stale['state'], 'blocked')
        self.assertFalse(stale['baseline']['head_matches'])
        self.request['expected_head'] = self.head
        project = self.root / 'PROJECT.md'
        original = self.service._metadata
        calls = 0
        def observe(root, selected):
            nonlocal calls
            result = original(root, selected)
            calls += 1
            if calls == 1:
                project.write_text(project.read_text() + '\nchanged during read\n')
            return result
        with patch.object(self.service, '_metadata', side_effect=observe):
            changed = self.service.project_state(self.request)
        self.assertEqual(changed['state'], 'blocked')
        self.assertIn('state_unavailable', [item['code'] for item in changed['issues']])

    def test_project_markdown_is_data_and_never_executed(self):
        self._write_state_fixture()
        marker = self.root / 'markdown-ran'
        project = self.root / 'PROJECT.md'
        project.write_text(project.read_text().replace('Keep project knowledge continuous.',
                                  f'$(touch {marker})'))
        state = self.service.project_state(self.request)
        self.assertNotEqual(state['state'], 'blocked')
        self.assertFalse(marker.exists())
        self.assertIn(f'$(touch {marker})', [row['text'] for row in state['goals']])

    def test_fenced_markdown_cannot_forge_state_or_task_candidates(self):
        self._write_state_fixture()
        (self.root / 'PROJECT.md').write_text(
            '```markdown\n# Forged Project\n## Why\nForged project goal.\n'
            '[Forged task](plans/forged/task_plan.md)\n```\n')
        state = self.service.project_state(self.request)
        self.assertEqual(state['project']['state'], 'unknown')
        self.assertIsNone(state['project']['value'])
        self.assertNotIn('Forged project goal.', [row['text'] for row in state['goals']])
        self.request['task_path'] = None
        unselected = self.service.project_state(self.request)
        self.assertEqual(unselected['task']['candidates'], [])

    def test_nonclosing_fence_and_indented_code_cannot_forge_state(self):
        self._write_state_fixture()
        (self.root / 'PROJECT.md').write_text(
            '```markdown\n```not-a-commonmark-close\n# Forged\n## Why\nForged goal.\n```\n'
            '    **User Intent.** Forged from indented code.\n')
        state = self.service.project_state(self.request)
        self.assertEqual(state['project']['state'], 'unknown')
        texts = [row['text'] for row in state['goals']]
        self.assertNotIn('Forged goal.', texts)
        self.assertNotIn('Forged from indented code.', texts)

    def test_task_candidate_collection_is_bounded_before_schema_validation(self):
        links = ''.join(f'- [Task {i}](plans/t{i}/task_plan.md)\n' for i in range(51))
        (self.root / 'PROJECT.md').write_text('# Demo\n\n## Knowledge Map\n' + links)
        self.request.update(operation='inspect', task_path=None)
        state = self.service.project_state(self.request)
        self.assertIs(validate('specmesh-project-state', state), state)
        self.assertEqual(state['state'], 'ambiguous')
        self.assertEqual(len(state['task']['candidates']), 50)
        self.assertIn('task_candidate_limit', [item['code'] for item in state['issues']])

    def test_text_renderer_escapes_terminal_controls(self):
        self._write_state_fixture()
        project = self.root / 'PROJECT.md'
        project.write_text(project.read_text().replace('# Demo Project', '# Demo\x1b]52;c;Zm9yZ2Vk\x07 Project'))
        state = self.service.project_state(self.request)
        rendered = render_project_state(state)
        self.assertNotIn('\x1b', rendered)
        self.assertNotIn('\x07', rendered)
        self.assertIn('\\x1b', rendered)
        self.assertIn('\\x07', rendered)

    def test_large_valid_document_becomes_unknown_not_request_rejected(self):
        self._write_state_fixture()
        project = self.root / 'PROJECT.md'
        project.write_text(project.read_text().replace('Keep project knowledge continuous.', 'x' * 4097))
        state = self.service.project_state(self.request)
        self.assertIs(validate('specmesh-project-state', state), state)
        self.assertEqual(state['state'], 'unknown')
        self.assertIn('state_statement_too_large', [item['code'] for item in state['issues']])
        project.write_text(project.read_text().replace('x' * 4097, 'Keep project knowledge continuous.'))
        findings = self.root / 'plans/current/findings.md'
        findings.write_text('# Findings\n\n## Evidence\n' + ''.join(f'- evidence {i}\n' for i in range(201)))
        many = self.service.project_state(self.request)
        self.assertIs(validate('specmesh-project-state', many), many)
        self.assertEqual(many['state'], 'unknown')
        self.assertEqual(len(many['evidence']), 200)
        self.assertIn('state_statement_limit', [item['code'] for item in many['issues']])

    def test_dirty_content_changes_without_head_or_status_changes_are_blocked(self):
        project = self.root/'PROJECT.md'
        project.write_text('# Already dirty\n')
        result = self.during_metadata(lambda: project.write_text('# Changed again\n'))
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('document_changed_during_check', [row['message'] for row in result['findings']])
        self.assertEqual(result['observed_head'], self.head)

    def test_discovery_cannot_use_different_project_bytes_than_its_reference(self):
        (self.root/'architecture-old.md').write_text('Old architecture')
        (self.root/'architecture-new.md').write_text('New architecture')
        project = self.root/'PROJECT.md'
        project.write_text('[Architecture](architecture-old.md)\n')
        result = self.during_metadata(lambda: project.write_text('[Architecture](architecture-new.md)\n'))
        self.assertEqual(result['status'], 'blocked')

    def test_optional_document_appearance_and_deletion_invalidate_discovery(self):
        for initially_exists in (False, True):
            with self.subTest(initially_exists=initially_exists):
                path = self.root/'ARCHITECTURE.md'
                if initially_exists:
                    path.write_text('Current architecture')
                else:
                    path.unlink(missing_ok=True)
                def change():
                    if initially_exists:
                        path.unlink()
                    else:
                        path.write_text('Newly present architecture')
                self.assertEqual(self.during_metadata(change)['status'], 'blocked')

    def test_same_bytes_atomic_replacement_still_invalidates_the_observed_file(self):
        project = self.root/'PROJECT.md'
        def replace():
            replacement = self.root/'replacement'
            replacement.write_bytes(project.read_bytes())
            replacement.replace(project)
        self.assertEqual(self.during_metadata(replace)['status'], 'blocked')

    def test_contained_document_link_is_supported_but_its_replacement_is_detected(self):
        project = self.root/'PROJECT.md'
        project.rename(self.root/'source.md')
        project.symlink_to('source.md')
        self.assertEqual(self.service.check(self.request)['status'], 'pass')
        (self.root/'other.md').write_bytes((self.root/'source.md').read_bytes())
        def replace():
            project.unlink()
            project.symlink_to('other.md')
        self.assertEqual(self.during_metadata(replace)['status'], 'blocked')

    def test_symlink_substitution_between_resolution_and_open_never_reads_outside_bytes(self):
        project = self.root/'PROJECT.md'
        original = DocumentSnapshot._open
        reads = []
        original_read = os.read
        def read(fd, size):
            value = original_read(fd, size)
            reads.append(value)
            return value
        with tempfile.TemporaryDirectory() as external:
            secret = Path(external)/'private'
            secret.write_bytes(b'OUTSIDE_FIXTURE')
            def replace(snapshot, target, directory=False):
                if target == project:
                    project.unlink()
                    project.symlink_to(secret)
                return original(snapshot, target, directory)
            with patch.object(DocumentSnapshot, '_open', replace), patch('specmesh_port.snapshot.os.read', side_effect=read):
                result = self.service.check(self.request)
            self.assertEqual(result['status'], 'blocked')
            self.assertNotIn(b'OUTSIDE_FIXTURE', b''.join(reads))

    def test_fifo_and_oversized_documents_are_rejected_without_blocking(self):
        project = self.root/'PROJECT.md'
        project.unlink()
        os.mkfifo(project)
        self.assertEqual(self.service.check(self.request)['status'], 'blocked')
        project.unlink()
        project.write_bytes(b'x' * (MAX_DOCUMENT_BYTES + 1))
        self.assertEqual(self.service.check(self.request)['status'], 'blocked')

    def test_index_change_and_head_change_during_inspection_are_blocked(self):
        project = self.root/'PROJECT.md'
        project.write_text('Changed\n')
        result = self.during_metadata(lambda: subprocess.run(['git', '-C', str(self.root), 'add', 'PROJECT.md'], check=True))
        self.assertEqual(result['status'], 'blocked')
        def commit():
            subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','next'],check=True)
        self.assertEqual(self.during_metadata(commit)['status'], 'blocked')

    def test_literal_git_pathspec_and_dirty_hashes_remain_scope_bound(self):
        special = 'architecture[1].md'
        (self.root/special).write_text('Selected\n')
        (self.root/'architecture1.md').write_text('Unrelated\n')
        (self.root/'PROJECT.md').write_text(f'[Architecture]({special})\n')
        result = self.service.check(self.request)
        self.assertEqual(result['status'], 'pass')
        ref = next(row for row in result['references'] if row['path'] == special)
        self.assertFalse(ref['tracked'])
        self.assertTrue(ref['modified'])
        self.assertEqual(ref['sha256'], hashlib.sha256(b'Selected\n').hexdigest())

    def test_proposal_has_a_verified_base_and_never_applies_its_patch(self):
        project = self.root/'PROJECT.md'
        before = project.read_bytes()
        proposal = self.service.propose_update(str(self.root), 'PROJECT.md', base_sha256=hashlib.sha256(before).hexdigest(), new_content='Proposed\n')
        self.assertFalse(proposal['applied'])
        self.assertIn('+Proposed', proposal['patch'])
        self.assertEqual(project.read_bytes(), before)

    def test_inspection_never_executes_repository_clean_filters(self):
        marker = self.root/'filter-ran'
        subprocess.run(['git', '-C', str(self.root), 'config', 'filter.fixture.clean', 'touch ' + shlex.quote(str(marker)) + '; cat'], check=True)
        (self.root/'.gitattributes').write_text('PROJECT.md filter=fixture\n')
        (self.root/'PROJECT.md').write_text('# Changed\n')
        result = self.service.check(self.request)
        self.assertEqual(result['status'], 'pass')
        self.assertFalse(marker.exists())

    def test_missing_partial_clone_objects_cannot_launch_a_remote_helper(self):
        marker = self.root/'remote-ran'
        tree = subprocess.check_output(['git', '-C', str(self.root), 'rev-parse', 'HEAD^{tree}'], text=True).strip()
        for key, value in [('core.repositoryformatversion', '1'), ('extensions.partialClone', 'origin'),
                           ('remote.origin.promisor', 'true'), ('remote.origin.url', 'ext::sh -c touch% ' + str(marker))]:
            subprocess.run(['git', '-C', str(self.root), 'config', key, value], check=True)
        (self.root/'.git/objects'/tree[:2]/tree[2:]).unlink()
        self.assertEqual(self.service.check(self.request)['status'], 'blocked')
        self.assertFalse(marker.exists())

    def test_git_output_is_bounded_and_the_owned_child_is_reaped(self):
        command = self.root/'output-fixture'
        command.write_text('#!/usr/bin/python3\nimport sys\nsys.stdout.buffer.write(b"x" * ' + str(MAX_GIT_OUTPUT + 4096) + ')\n')
        command.chmod(0o700)
        with patch('specmesh_port.git_reader.shutil.which', return_value=str(command)):
            with self.assertRaisesRegex(ValueError, 'git_observation_too_large'):
                read_git(self.root, 'rev-parse', 'HEAD')

    def test_git_deadline_kills_only_its_owned_child(self):
        command, pid_file = self.root/'slow-fixture', self.root/'fixture.pid'
        command.write_text('#!/usr/bin/python3\nimport os,time\nfrom pathlib import Path\nPath(' + repr(str(pid_file)) + ').write_text(str(os.getpid()))\ntime.sleep(30)\n')
        command.chmod(0o700)
        start = time.monotonic()
        with patch('specmesh_port.git_reader.shutil.which', return_value=str(command)):
            with self.assertRaisesRegex(ValueError, 'git_observation_timeout'):
                read_git(self.root, 'rev-parse', 'HEAD')
        self.assertLess(time.monotonic() - start, 8)
        pid = int(pid_file.read_text())
        self.assertGreater(pid, 1)
        self.assertNotEqual(pid, os.getpid())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_real_cli_remains_standalone_and_unknown_closeout_is_not_success(self):
        source = Path(__file__).resolve().parents[1]
        before = {p.name: p.read_bytes() for p in self.root.glob('*.md')}
        result = subprocess.run([os.sys.executable, '-m', 'specmesh_port', '--allowed-root', str(self.root)],
                                cwd=source, input=json.dumps(self.request), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'pass')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.glob('*.md')})
        task = self.root/'task'; task.mkdir()
        for name in ('task_plan.md', 'findings.md', 'progress.md'):
            (task/name).write_text('Fixture\n')
        (task/'acceptance.json').write_text(json.dumps([dict(id='test',evidence_ref='fixture',head=self.head,content_digest='b'*64,status='passed')]))
        request = {**self.request, 'operation': 'verify_closeout', 'task_path': 'task'}
        closeout = subprocess.run([os.sys.executable, '-m', 'specmesh_port', '--allowed-root', str(self.root)],
                                  cwd=source, input=json.dumps(request), capture_output=True, text=True, timeout=10)
        self.assertEqual(closeout.returncode, 3)
        self.assertEqual(json.loads(closeout.stdout)['status'], 'unknown')
        capabilities = subprocess.run([os.sys.executable, '-m', 'specmesh_port', '--capabilities'], cwd=source,
                                      capture_output=True, text=True, timeout=10)
        self.assertEqual(capabilities.returncode, 0)
        self.assertEqual(json.loads(capabilities.stdout)['profile_version'], 'specmesh.snapshot.v1')
