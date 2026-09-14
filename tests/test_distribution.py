import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import posixpath
import re
from specmesh_port import __version__

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_builder", ROOT / "scripts/build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class DistributionTests(unittest.TestCase):
    def test_candidate_is_deterministic_and_manifest_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "one.zip", Path(temp) / "two.zip"
            builder.build(ROOT, first, __version__, allow_dirty=True)
            builder.build(ROOT, second, __version__, allow_dirty=True)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                names = set(archive.namelist())
                for document in ("README.md", "docs/CODEKIT-INTEGRATION.md"):
                    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", archive.read(document).decode()):
                        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                            continue
                        target = posixpath.normpath(posixpath.join(posixpath.dirname(document), target.split("#")[0]))
                        self.assertTrue(target in names or any(n.startswith(target.rstrip("/") + "/") for n in names),
                                        (document, target))
                for name, digest in manifest["files"].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                self.assertNotIn(".git/config", archive.namelist())
                self.assertFalse(any(".specmesh/cache" in n or "plans/" in n for n in archive.namelist()))
                package = Path(temp) / "installed"
                archive.extractall(package)
            result = subprocess.run([sys.executable, "-I", "-B", str(package / "scripts/smoke_release.py"),
                                     "--package-root", str(package)], cwd=temp, capture_output=True, text=True, timeout=40)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["module_root"], str(package))
            self.assertEqual(report["status"], "pass")
            self.assertEqual(len(report["checks"]), 6)
            integrity = subprocess.run([sys.executable, "-I", "-B", str(package / "scripts/verify_install.py"),
                                        "--package-root", str(package)], cwd=temp, capture_output=True, text=True, timeout=40)
            self.assertEqual(integrity.returncode, 0, integrity.stdout + integrity.stderr)
            self.assertEqual(json.loads(integrity.stdout)["checked_files"], len(manifest["files"]))
            with self.assertRaises(FileExistsError):
                builder.build(ROOT, first, __version__, allow_dirty=True)

    def test_invalid_version_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                builder.build(ROOT, Path(temp) / "bad.zip", "../invalid", allow_dirty=True)

    def test_runtime_version_must_match_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "version_mismatch"):
                builder.build(ROOT, Path(temp) / "bad.zip", "99.0.0", allow_dirty=True)
