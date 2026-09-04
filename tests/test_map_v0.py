import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts/map_v0.py"
SPEC = importlib.util.spec_from_file_location("specmesh_map_v0", MODULE_PATH)
map_v0 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(map_v0)


class MapV0Tests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self._write(
            ".specmesh/context.md",
            "---\n"
            "map_global_budget_tokens: 120\n"
            "map_focus_budget_tokens: 80\n"
            "memory_root: .specmesh/memory/core.md\n"
            "cache_path: .specmesh/cache/repo-map.json\n"
            "---\n",
        )
        self._write(
            ".specmesh/memory/core.md",
            "# Core\n\n"
            "- relation: implemented_by | from: `spec://demo` | "
            "to: `code://src/app.py` | provenance: asserted\n"
            "- relation: verified_by | from: `spec://demo` | "
            "to: `code://tests/test_app.py` | provenance: asserted\n"
            "- relation: must_not_import | from: `spec://demo` | "
            "to: `code://src/helper.py` | provenance: derived\n",
        )
        self._write("src/app.py", "import src.helper\n\ndef normalize(value):\n    return helper(value)\n")
        self._write(
            "src/helper.py",
            "def helper(value):\n"
            "    return value.strip().lower()\n\n"
            "class Session:\n"
            "    def validate(self):\n"
            "        return True\n\n"
            "    def _reset(self):\n"
            "        return None\n",
        )
        self._write(
            "tests/test_app.py",
            "from src.app import normalize\n\ndef test_normalize():\n    assert normalize(' X ') == 'x'\n",
        )
        self._write("main.rs", "fn main() {}\n")

    def tearDown(self):
        self.tempdir.cleanup()

    def _write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_extracts_files_public_symbols_imports_references_and_tests(self):
        graph = map_v0.build_graph(self.root)
        node_ids = {node["id"] for node in graph["nodes"]}
        relations = {(edge["relation"], edge["from"], edge["to"]) for edge in graph["edges"]}
        self.assertIn("code://src/app.py#normalize", node_ids)
        self.assertIn("code://src/helper.py#helper", node_ids)
        self.assertIn("code://src/helper.py#Session", node_ids)
        self.assertIn("code://src/helper.py#Session.validate", node_ids)
        self.assertNotIn("code://src/helper.py#Session._reset", node_ids)
        self.assertIn(("imports", "code://tests/test_app.py", "code://src/app.py"), relations)
        self.assertIn(("tests", "code://tests/test_app.py", "code://src/app.py"), relations)
        self.assertIn(("references", "code://src/app.py", "code://src/helper.py#helper"), relations)

    def test_unsupported_language_falls_back_to_file_node(self):
        graph = map_v0.build_graph(self.root)
        rust_nodes = [node for node in graph["nodes"] if node["id"].startswith("code://main.rs")]
        self.assertEqual(rust_nodes, [{"id": "code://main.rs", "kind": "file", "name": "main.rs", "authority": "derived"}])

    def test_asserted_and_derived_provenance_remain_distinct(self):
        graph = map_v0.build_graph(self.root)
        asserted = [edge for edge in graph["edges"] if edge["provenance"] == "asserted"]
        derived = [edge for edge in graph["edges"] if edge["provenance"] == "derived"]
        self.assertTrue(asserted)
        self.assertTrue(derived)
        self.assertNotIn("must_not_import", {edge["relation"] for edge in graph["edges"]})
        self.assertEqual(next(node for node in graph["nodes"] if node["id"] == "spec://demo")["authority"], "asserted")

    def test_repeated_generation_is_byte_identical(self):
        first = map_v0.canonical_json(map_v0.build_graph(self.root))
        second = map_v0.canonical_json(map_v0.build_graph(self.root))
        self.assertEqual(first, second)

    def test_content_change_invalidates_cache(self):
        graph = map_v0.build_graph(self.root)
        map_v0.write_cache(self.root, graph)
        self.assertTrue(map_v0.cache_is_fresh(self.root, graph))
        self._write("src/helper.py", "def helper(value):\n    return value.casefold()\n")
        self.assertFalse(map_v0.cache_is_fresh(self.root, graph))

    def test_deleted_cache_rebuilds_identically(self):
        graph = map_v0.build_graph(self.root)
        path = map_v0.write_cache(self.root, graph)
        first = path.read_bytes()
        path.unlink()
        rebuilt = map_v0.write_cache(self.root, map_v0.build_graph(self.root)).read_bytes()
        self.assertEqual(first, rebuilt)

    def test_global_and_focus_views_obey_hard_budgets(self):
        graph = map_v0.build_graph(self.root)
        global_view = map_v0.render_view(graph, 120)
        focus_view = map_v0.render_view(graph, 80, "normalize test")
        self.assertLessEqual(len(map_v0.tokenize(global_view)), 120)
        self.assertLessEqual(len(map_v0.tokenize(focus_view)), 80)
        self.assertIn("code://src/app.py#normalize", focus_view)

    def test_cache_json_is_canonical_and_contains_no_timestamp(self):
        payload = map_v0.canonical_json(map_v0.build_graph(self.root))
        parsed = json.loads(payload)
        self.assertNotIn("generated_at", parsed)
        self.assertEqual(payload, map_v0.canonical_json(parsed))


class RealTaskFocusTests(unittest.TestCase):
    TASKS = (
        "change global and focus token budgets",
        "fix Python public symbol extraction",
        "document Map v0 authority boundaries",
        "change asserted memory relation parsing",
        "verify content hash freshness and cache rebuild",
    )

    def test_five_real_tasks_locate_context_implementation_and_tests(self):
        graph = map_v0.build_graph(REPO_ROOT)
        for task in self.TASKS:
            with self.subTest(task=task):
                view = map_v0.render_view(graph, 800, task)
                self.assertIn("code://.specmesh/context.md", view)
                self.assertIn("code://scripts/map_v0.py", view)
                self.assertIn("code://tests/test_map_v0.py", view)
                self.assertLessEqual(len(map_v0.tokenize(view)), 800)


class CliTests(unittest.TestCase):
    def test_build_check_and_focus_commands(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            context = root / ".specmesh/context.md"
            context.parent.mkdir(parents=True)
            context.write_text(
                "map_focus_budget_tokens: 80\ncache_path: .specmesh/cache/repo-map.json\n",
                encoding="utf-8",
            )
            (root / "sample.py").write_text("def public():\n    return 1\n", encoding="utf-8")
            build = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "build"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            check = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "check"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            focus = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "focus", "public"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertEqual(check.stdout.strip(), "fresh")
            self.assertEqual(focus.returncode, 0, focus.stderr)
            self.assertIn("code://sample.py#public", focus.stdout)


if __name__ == "__main__":
    unittest.main()
