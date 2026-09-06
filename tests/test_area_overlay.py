import importlib.util
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


RENDER_AREA = (
    "areas:\n"
    "  - id: area:view-render\n"
    "    purpose: Render budgeted views over derived structure.\n"
    "    anchors:\n"
    "      - code://src/render.py\n"
    "      - code://src/render.py#render\n"
    "      - code://tests/test_render.py\n"
    "    read_next:\n"
    "      - .specmesh/context.md\n"
    "  - id: area:store\n"
    "    purpose: Persist derived map artifacts.\n"
    "    anchors:\n"
    "      - code://src/store.py\n"
    "    read_next:\n"
    "      - SPEC.md\n"
)

SCOPED_MEMORY = (
    "# Core\n\n"
    "- relation: implemented_by | from: `spec://render` | "
    "to: `code://src/render.py` | provenance: asserted | scope: area:view-render\n"
    "- relation: verified_by | from: `spec://render` | "
    "to: `code://tests/test_render.py` | provenance: asserted | scope: area:view-render\n"
)


class AreaOverlayTests(unittest.TestCase):
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
        self._write(".specmesh/memory/core.md", SCOPED_MEMORY)
        self._write(".specmesh/repo-areas.v0.yaml", RENDER_AREA)
        self._write("src/render.py", "def render(view):\n    return view\n")
        self._write("src/store.py", "def persist(payload):\n    return payload\n")
        self._write("tests/test_render.py", "from src.render import render\n\ndef test_render():\n    assert render('x') == 'x'\n")

    def tearDown(self):
        self.tempdir.cleanup()

    def _write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _resolution(self):
        graph = map_v0.build_graph(self.root)
        return graph, graph["source_state"]["area_resolution"]

    def test_normalize_area_id_variants(self):
        self.assertEqual(map_v0.normalize_area_id("area:view-render"), "area:view-render")
        self.assertEqual(map_v0.normalize_area_id("area:View_Render"), "area:view-render")
        self.assertEqual(map_v0.normalize_area_id("View Render"), "area:view-render")
        self.assertEqual(map_v0.normalize_area_id("`area:view--render`"), "area:view-render")
        self.assertEqual(map_v0.normalize_area_id("view__render v2"), "area:view-render-v2")

    def test_unnormalized_id_rejected_with_suggestion(self):
        self._write(".specmesh/repo-areas.v0.yaml", RENDER_AREA.replace("area:view-render", "area:View_Render"))
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("not normalized", str(raised.exception))
        self.assertIn("'area:view-render'", str(raised.exception))

    def test_duplicate_ids_rejected(self):
        duplicated = RENDER_AREA.replace("area:store", "area:view-render").replace(
            "purpose: Persist derived map artifacts.", "purpose: Duplicate identity."
        )
        self._write(".specmesh/repo-areas.v0.yaml", duplicated)
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("duplicate area id 'area:view-render'", str(raised.exception))

    def test_current_state_when_anchors_resolve(self):
        graph, resolution = self._resolution()
        self.assertEqual(resolution["area:view-render"]["state"], "current")
        self.assertEqual(resolution["area:store"]["state"], "current")
        self.assertIsNone(resolution["area:view-render"]["reason"])
        anchor = resolution["area:view-render"]["anchors"][1]
        self.assertEqual(anchor["anchor"], "code://src/render.py#render")
        self.assertEqual(anchor["resolved"], "code://src/render.py#render")
        self.assertEqual(anchor["candidates"], [])
        scope_edges = [edge for edge in graph["edges"] if edge.get("scope") == "area:view-render"]
        self.assertEqual(len(scope_edges), 2)

    def test_unresolved_when_anchor_gone_without_candidate(self):
        (self.root / "src/store.py").unlink()
        _, resolution = self._resolution()
        self.assertEqual(resolution["area:store"]["state"], "unresolved")
        self.assertIn("anchor code://src/store.py: no candidate", resolution["area:store"]["reason"])

    def test_ambiguous_when_symbol_defined_in_two_files(self):
        self._write("src/render.py", "def draw(view):\n    return view\n")
        self._write("src/other.py", "def render(view):\n    return view\n")
        self._write("src/paint.py", "def render(view):\n    return view\n")
        _, resolution = self._resolution()
        self.assertEqual(resolution["area:view-render"]["state"], "ambiguous")
        self.assertIn("anchor code://src/render.py#render: 2 candidates", resolution["area:view-render"]["reason"])
        self.assertIn("code://src/other.py#render", resolution["area:view-render"]["reason"])
        self.assertIn("code://src/paint.py#render", resolution["area:view-render"]["reason"])

    def test_ambiguous_when_two_files_share_basename(self):
        (self.root / "src/render.py").unlink()
        self._write("lib/render.py", "def render(view):\n    return view\n")
        self._write("alt/render.py", "def render(view):\n    return view\n")
        _, resolution = self._resolution()
        self.assertEqual(resolution["area:view-render"]["state"], "ambiguous")
        self.assertIn("code://alt/render.py", resolution["area:view-render"]["reason"])
        self.assertIn("code://lib/render.py", resolution["area:view-render"]["reason"])

    def test_candidate_rebind_on_unique_file_rename(self):
        (self.root / "src/render.py").rename(self.root / "src/view.py")
        _, resolution = self._resolution()
        record = resolution["area:view-render"]
        self.assertEqual(record["state"], "candidate_rebind")
        self.assertIsNone(record["anchors"][0]["resolved"])
        self.assertEqual(record["anchors"][0]["candidates"], [])
        symbol_anchor = record["anchors"][1]
        self.assertIsNone(symbol_anchor["resolved"])
        self.assertEqual(symbol_anchor["candidates"], ["code://src/view.py#render"])
        self.assertIn("awaiting human confirmation", record["reason"])
        self.assertIn("anchor code://src/render.py: no candidate", record["reason"])

    def test_candidate_rebind_when_symbol_moved_out_of_file(self):
        self._write("src/render.py", "def draw(view):\n    return view\n")
        self._write("src/paint.py", "def render(view):\n    return view\n")
        _, resolution = self._resolution()
        record = resolution["area:view-render"]
        self.assertEqual(record["state"], "candidate_rebind")
        symbol_anchor = record["anchors"][1]
        self.assertIsNone(symbol_anchor["resolved"])
        self.assertEqual(symbol_anchor["candidates"], ["code://src/paint.py#render"])

    def test_unrelated_rename_keeps_area_current(self):
        self._write("src/extra.py", "def helper():\n    return 1\n")
        (self.root / "src/extra.py").rename(self.root / "src/misc.py")
        _, resolution = self._resolution()
        self.assertEqual(resolution["area:view-render"]["state"], "current")
        self.assertEqual(resolution["area:store"]["state"], "current")

    def test_dangling_memory_scope_fails(self):
        self._write(
            ".specmesh/memory/core.md",
            SCOPED_MEMORY.replace("scope: area:view-render", "scope: area:no-such-area"),
        )
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("'area:no-such-area' does not match any declared area", str(raised.exception))

    def test_noncanonical_memory_scope_rejected_with_suggestion(self):
        self._write(
            ".specmesh/memory/core.md",
            SCOPED_MEMORY.replace("scope: area:view-render", "scope: area:View_Render"),
        )
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        message = str(raised.exception)
        self.assertIn("'area:View_Render' is not canonical", message)
        self.assertIn("'area:view-render'", message)

    def test_malformed_relation_line_fails_loud(self):
        self._write(
            ".specmesh/memory/core.md",
            SCOPED_MEMORY
            + "- relation: defines | from: `spec://render` | to: `code://src/render.py`\n",
        )
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        message = str(raised.exception)
        self.assertIn("malformed relation", message)
        self.assertIn("line 5", message)

    def test_stale_code_target_is_asserted_and_gated_with_scope(self):
        ghost = "code://src/ghost.py"
        self._write(
            ".specmesh/memory/core.md",
            SCOPED_MEMORY
            + "- relation: implemented_by | from: `spec://render` | "
            "to: `code://src/ghost.py` | provenance: asserted | scope: area:view-render\n",
        )
        graph = map_v0.build_graph(self.root)
        node = {item["id"]: item for item in graph["nodes"]}[ghost]
        self.assertEqual(node["authority"], "asserted")
        current = map_v0.render_view(graph, 400, "render")
        self.assertIn(ghost, current)
        (self.root / "src/render.py").rename(self.root / "src/view.py")
        broken_graph = map_v0.build_graph(self.root)
        broken = map_v0.render_view(broken_graph, 400, "render")
        self.assertNotIn(ghost, broken)
        self.assertNotIn("spec://render", broken)
        scores = map_v0._rank(broken_graph, "render")
        baseline_graph = map_v0.build_graph(self.root)
        baseline_graph["edges"] = [
            edge for edge in baseline_graph["edges"] if edge.get("scope") is None
        ]
        baseline = map_v0._rank(baseline_graph, "render")
        self.assertAlmostEqual(scores[ghost], baseline[ghost], places=12)

    def test_duplicate_area_field_rejected(self):
        duplicated = RENDER_AREA.replace(
            "    purpose: Render budgeted views over derived structure.",
            "    purpose: First purpose.\n    purpose: Second purpose.",
        )
        self._write(".specmesh/repo-areas.v0.yaml", duplicated)
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("duplicate area field 'purpose'", str(raised.exception))

    def test_duplicate_anchor_list_header_rejected(self):
        duplicated = RENDER_AREA.replace(
            "    anchors:\n      - code://src/render.py\n",
            "    anchors:\n      - code://src/render.py\n    anchors:\n      - code://tests/test_render.py\n",
        )
        self._write(".specmesh/repo-areas.v0.yaml", duplicated)
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("duplicate area field 'anchors'", str(raised.exception))

    def test_split_into_field_rejected_documents_v0_boundary(self):
        extended = RENDER_AREA.replace(
            "      - .specmesh/context.md\n  - id: area:store",
            "      - .specmesh/context.md\n    split_into: area:render-a\n  - id: area:store",
        )
        self._write(".specmesh/repo-areas.v0.yaml", extended)
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("unknown area field 'split_into'", str(raised.exception))

    def test_memory_injected_only_while_area_current(self):
        current = map_v0.render_view(map_v0.build_graph(self.root), 400, "render")
        self.assertIn("spec://render", current)
        self.assertIn("area:view-render [current]", current)
        (self.root / "src/render.py").rename(self.root / "src/view.py")
        broken = map_v0.render_view(map_v0.build_graph(self.root), 400, "render")
        self.assertNotIn("spec://render", broken)
        self.assertIn("area:view-render [candidate_rebind]", broken)
        self.assertNotIn("read_next:", broken)

    def test_superseded_area_stops_memory_and_successor_injects(self):
        self._write(
            ".specmesh/repo-areas.v0.yaml",
            RENDER_AREA
            + "  - id: area:legacy-render\n"
            "    purpose: Legacy rendering responsibility kept for history.\n"
            "    anchors:\n"
            "      - code://src/render.py\n"
            "    read_next:\n"
            "      - SPEC.md\n"
            "    superseded_by: area:view-render\n",
        )
        self._write(
            ".specmesh/memory/core.md",
            SCOPED_MEMORY
            + "- relation: implemented_by | from: `spec://legacy` | "
            "to: `code://src/render.py` | provenance: asserted | scope: area:legacy-render\n",
        )
        graph = map_v0.build_graph(self.root)
        resolution = graph["source_state"]["area_resolution"]
        self.assertEqual(resolution["area:legacy-render"]["superseded_by"], "area:view-render")
        view = map_v0.render_view(graph, 400, "render")
        self.assertNotIn("spec://legacy", view)
        self.assertNotIn("area:legacy-render", view)
        self.assertIn("area:view-render [current]", view)
        self.assertIn("spec://render", view)

    def test_supersede_requires_existing_target_and_rejects_chains(self):
        self._write(
            ".specmesh/repo-areas.v0.yaml",
            RENDER_AREA.replace(
                "  - id: area:store",
                "  - id: area:legacy-render\n"
                "    purpose: Legacy rendering responsibility.\n"
                "    anchors:\n"
                "      - code://src/render.py\n"
                "    superseded_by: area:missing-target\n"
                "  - id: area:store",
            ),
        )
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("'area:missing-target' does not exist", str(raised.exception))
        chained = (
            "areas:\n"
            "  - id: area:first\n"
            "    purpose: One.\n"
            "    anchors:\n"
            "      - code://src/render.py\n"
            "    superseded_by: area:second\n"
            "  - id: area:second\n"
            "    purpose: Two.\n"
            "    anchors:\n"
            "      - code://src/store.py\n"
            "    superseded_by: area:store\n"
        )
        self._write(".specmesh/repo-areas.v0.yaml", chained)
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("chains via 'area:second' are not allowed", str(raised.exception))

    def test_parser_rejects_unknown_field_and_bad_anchor_counts(self):
        self._write(
            ".specmesh/repo-areas.v0.yaml",
            "areas:\n"
            "  - id: area:view-render\n"
            "    purpose: Render views.\n"
            "    owner: nobody\n"
            "    anchors:\n"
            "      - code://src/render.py\n",
        )
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("unknown area field 'owner'", str(raised.exception))
        four_anchors = (
            "areas:\n"
            "  - id: area:view-render\n"
            "    purpose: Render views.\n"
            "    anchors:\n"
            "      - code://src/render.py\n"
            "      - code://src/store.py\n"
            "      - code://tests/test_render.py\n"
            "      - code://.specmesh/context.md\n"
        )
        self._write(".specmesh/repo-areas.v0.yaml", four_anchors)
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("expected 1..3 anchors, got 4", str(raised.exception))
        no_purpose = "areas:\n  - id: area:view-render\n    anchors:\n      - code://src/render.py\n"
        self._write(".specmesh/repo-areas.v0.yaml", no_purpose)
        with self.assertRaises(RuntimeError) as raised:
            map_v0.build_graph(self.root)
        self.assertIn("'purpose' is required", str(raised.exception))

    def test_deterministic_rebuild_with_areas(self):
        first = map_v0.canonical_json(map_v0.build_graph(self.root))
        second = map_v0.canonical_json(map_v0.build_graph(self.root))
        self.assertEqual(first, second)
        path = map_v0.write_cache(self.root, map_v0.build_graph(self.root))
        payload = path.read_bytes()
        path.unlink()
        rebuilt = map_v0.write_cache(self.root, map_v0.build_graph(self.root)).read_bytes()
        self.assertEqual(payload, rebuilt)

    def test_focus_view_area_block_respects_budget_and_query(self):
        graph = map_v0.build_graph(self.root)
        view = map_v0.render_view(graph, 400, "store persist")
        self.assertIn("area:store [current]", view)
        self.assertIn("purpose: Persist derived map artifacts.", view)
        self.assertIn("anchors: code://src/store.py", view)
        self.assertIn("read_next: SPEC.md", view)
        self.assertNotIn("area:view-render", view)
        self.assertLessEqual(len(map_v0.tokenize(view)), 400)

    def test_missing_areas_file_keeps_graph_shape(self):
        (self.root / ".specmesh/repo-areas.v0.yaml").unlink()
        self._write(
            ".specmesh/memory/core.md",
            "# Core\n\n"
            "- relation: implemented_by | from: `spec://render` | "
            "to: `code://src/render.py` | provenance: asserted\n",
        )
        graph = map_v0.build_graph(self.root)
        self.assertEqual(graph["source_state"]["area_resolution"], {})
        view = map_v0.render_view(graph, 200, "render")
        self.assertNotIn("## areas", view)
        self.assertIn("spec://render", view)


class AreasCliTests(unittest.TestCase):
    def test_build_check_areas_and_focus_commands(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            context = root / ".specmesh/context.md"
            context.parent.mkdir(parents=True)
            context.write_text(
                "map_focus_budget_tokens: 200\ncache_path: .specmesh/cache/repo-map.json\n",
                encoding="utf-8",
            )
            (root / ".specmesh/repo-areas.v0.yaml").write_text(
                "areas:\n"
                "  - id: area:sample\n"
                "    purpose: Sample responsibility.\n"
                "    anchors:\n"
                "      - code://sample.py\n"
                "      - code://sample.py#public\n"
                "    read_next:\n"
                "      - README.md\n",
                encoding="utf-8",
            )
            memory = root / ".specmesh/memory/core.md"
            memory.parent.mkdir(parents=True)
            memory.write_text(
                "- relation: verified_by | from: `spec://sample` | "
                "to: `code://sample.py` | provenance: asserted | scope: area:sample\n",
                encoding="utf-8",
            )
            (root / "sample.py").write_text("def public():\n    return 1\n", encoding="utf-8")
            build = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "build"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            areas = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "areas"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            focus = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "focus", "public sample"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            self.assertEqual(areas.returncode, 0, areas.stderr)
            self.assertIn("area:sample [current]", areas.stdout)
            self.assertIn("code://sample.py -> ok", areas.stdout)
            self.assertIn("code://sample.py#public -> ok", areas.stdout)
            self.assertEqual(focus.returncode, 0, focus.stderr)
            self.assertIn("area:sample [current]", focus.stdout)
            self.assertIn("spec://sample", focus.stdout)
            (root / "sample.py").rename(root / "moved.py")
            rebuild = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "build"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            rebound = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "areas"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(rebuild.returncode, 0, rebuild.stderr)
            self.assertIn("area:sample [candidate_rebind]", rebound.stdout)
            self.assertIn("code://sample.py -> missing", rebound.stdout)
            self.assertIn("code://sample.py#public -> candidate code://moved.py#public", rebound.stdout)
            gated_focus = subprocess.run(
                ["python3", str(MODULE_PATH), "--root", str(root), "focus", "public sample"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(gated_focus.returncode, 0, gated_focus.stderr)
            self.assertNotIn("spec://sample", gated_focus.stdout)


if __name__ == "__main__":
    unittest.main()
