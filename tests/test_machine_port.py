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
