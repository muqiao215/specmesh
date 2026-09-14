import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/verify_install.py"


class VerifyInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "module.py").write_text("answer = 42\n")
        self.manifest = {"format": "specmesh.distribution.v1", "version": "1.3.0rc1",
                         "source_identity": "a" * 64,
                         "files": {"module.py": hashlib.sha256((self.root / "module.py").read_bytes()).hexdigest()}}
        self.save()

    def save(self):
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))

    def run_check(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), "--package-root", str(self.root)],
                                capture_output=True, text=True, timeout=10)
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_valid_install_and_extra_user_file_unchanged(self):
        (self.root / "user.txt").write_text("preserve me\n")
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        code, result = self.run_check()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["version"], "1.3.0rc1")
        self.assertEqual(result["source_identity"], "a" * 64)
        self.assertEqual(result["checked_files"], 1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_changed_and_missing_declared_file(self):
        (self.root / "module.py").write_text("changed\n")
        self.assertNotEqual(self.run_check()[0], 0)
        (self.root / "module.py").unlink()
        self.assertNotEqual(self.run_check()[0], 0)

    def test_bad_or_missing_manifest(self):
        for raw in ("{broken", "[]", "{}", '{"files": []}'):
            with self.subTest(raw=raw):
                (self.root / "manifest.json").write_text(raw)
                code, report = self.run_check()
                self.assertNotEqual(code, 0)
                self.assertEqual(report["status"], "fail")
                self.assertTrue(report["errors"])
        (self.root / "manifest.json").unlink()
        self.assertNotEqual(self.run_check()[0], 0)

    def test_paths_and_symlinks_rejected(self):
        digest = self.manifest["files"]["module.py"]
        for path in ("../outside.txt", "/tmp/outside.txt", "folder/../module.py"):
            with self.subTest(path=path):
                self.manifest["files"] = {path: digest}
                self.save()
                self.assertNotEqual(self.run_check()[0], 0)
        (self.root / "alias.py").symlink_to("module.py")
        self.manifest["files"] = {"alias.py": digest}
        self.save()
        self.assertNotEqual(self.run_check()[0], 0)

    def test_bad_digest_rejected(self):
        self.manifest["files"] = {"module.py": "not-a-sha"}
        self.save()
        self.assertNotEqual(self.run_check()[0], 0)
