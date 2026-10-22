"""Regression checks for memory integrity and topic-faithful research output."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class ResearchTests(unittest.TestCase):
    def test_no_invented_report_content(self):
        module = runpy.run_path(str(ROOT / "mineintel-report-export/scripts/save_report.py"))
        self.assertEqual(module["paper_results_with_fallback"]([]), [])
        self.assertEqual(module["parse_baseline"](""), [])
        self.assertEqual(module["parse_advisors"]("", {}), [])
        self.assertEqual(module["parse_route"]("", {})["branches"], [])
        self.assertEqual(module["ensure_minimum_report_content"]("题目", "矿井语音调研", {}), "矿井语音调研\n")

    def test_non_visual_route(self):
        module = runpy.run_path(str(ROOT / "mineintel-html-poster/scripts/render_html_poster.py"))
        self.assertEqual(module["route_steps"]("## 技术路线\n1. 采集矿井语音\n2. 评估语音转写"), ["采集矿井语音", "评估语音转写"])
        self.assertEqual(module["route_steps"](""), [])

    def test_empty_deck_does_not_recommend_yolo(self):
        module = runpy.run_path(str(ROOT / "mineintel-deck-export/scripts/render_deck.py"))
        for name in ("slide_baseline", "slide_route"):
            self.assertNotIn("YOLO", module[name](10, []))

    def test_empty_review_does_not_invent_references(self):
        module = runpy.run_path(str(ROOT / "mineintel-literature-review/scripts/build_literature_review.py"))
        self.assertEqual(module["extract_papers"](""), [])
        self.assertEqual(module["collect_reference_items"]([], ""), [])
        self.assertNotIn("YOLO", module["build_review_markdown"]("矿井语音", ""))

    def test_search_errors_are_not_empty_success(self):
        from mineintel_common.web_search import normalize_response
        with self.assertRaises(RuntimeError):
            normalize_response({"status": "error", "code": 401}, "主题", 5)
        self.assertEqual(normalize_response({"data": {"results": []}}, "主题", 5)["count"], 0)

    def test_memory_update_delete_and_corruption(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            profile, project = folder / "profile.json", folder / "project.json"
            def call(*args):
                result = subprocess.run([sys.executable, str(ROOT / "mineintel-research/scripts/project_memory.py"), "--profile", str(profile), *args], capture_output=True, encoding="utf-8")
                return result.returncode, json.loads(result.stdout)
            self.assertEqual(call("context")[1]["status"], "needs_profile")
            item = {"id": "p1", "title": "语音项目", "status": "completed", "contribution": "实现界面", "source": "user_statement"}
            project.write_text(json.dumps(item), encoding="utf-8")
            self.assertEqual(call("add", "--project", str(project))[0], 0)
            item["contribution"] = "处理数据"
            project.write_text(json.dumps(item), encoding="utf-8")
            self.assertEqual(call("add", "--project", str(project))[1]["project_count"], 1)
            self.assertEqual(call("context")[1]["profile"]["projects"][0]["contribution"], "处理数据")
            self.assertEqual(call("forget", "--id", "p1")[1]["project_count"], 0)
            profile.write_text("broken", encoding="utf-8")
            self.assertEqual(call("add", "--project", str(project))[0], 2)
            self.assertEqual(profile.read_text(), "broken")


if __name__ == "__main__":
    unittest.main()
