import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from specmesh_port.service import SpecMeshService

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
