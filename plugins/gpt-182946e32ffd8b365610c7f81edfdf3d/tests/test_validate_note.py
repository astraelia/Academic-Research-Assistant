"""Regression checks for shared summary/deep note validation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4


PLUGIN = Path(__file__).resolve().parents[1]
VALIDATOR = PLUGIN / "scripts" / "validate_note.py"
HEADINGS = {
    "summary": ("📜 研究核心", "🔁 研究内容", "🧠 文献价值", "🤔 阅读总结"),
    "deep": (
        "🧭 01｜论文定位", "🧠 02｜研究逻辑", "📚 03｜背景与问题",
        "🧮 04｜理论、方法与公式", "🔬 05｜实验/数值设计与证据链",
        "🖼️ 06｜图表精读", "🧩 07｜结论边界与批判性分析",
        "💡 08｜研究迁移与最终精读结论",
    ),
}


class ValidateNoteTest(unittest.TestCase):
    def setUp(self) -> None:
        test_root = PLUGIN / "tmp" / "note-validator-tests"
        test_root.mkdir(parents=True, exist_ok=True)
        self.root = test_root / f"case-{uuid4().hex[:10]}"
        self.root.mkdir()

    def tearDown(self) -> None:
        target = self.root.resolve()
        allowed = (PLUGIN / "tmp" / "note-validator-tests").resolve()
        if target == allowed or not target.is_relative_to(allowed):
            raise RuntimeError(f"Unsafe test cleanup path: {target}")
        shutil.rmtree(target)

    def make_note(self, mode: str, folder: str = "Exact Paper Title") -> Path:
        directory = self.root / folder
        directory.mkdir(exist_ok=True)
        prefix = "总结" if mode == "summary" else "精读"
        note = directory / f"{prefix}—{folder}.md"
        body = "\n".join(f"## {heading}\nChecked content." for heading in HEADINGS[mode])
        note.write_text(
            "---\ntitle: Exact Paper Title\nresearch_direction: 测试\n"
            "zotero_item_key: ABCD1234\n---\n# Exact Paper Title\n" + body + "\n",
            encoding="utf-8",
        )
        return note

    def check(self, note: Path, mode: str, *extra: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(note), "--mode", mode, *extra],
            capture_output=True, text=True, encoding="utf-8", check=False,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode == 0, report["valid"], report)
        return report

    def test_both_note_modes_accept_matching_title(self) -> None:
        for mode in HEADINGS:
            with self.subTest(mode=mode):
                self.assertTrue(self.check(self.make_note(mode), mode)["valid"])

    def test_legacy_folder_requires_explicit_verified_override(self) -> None:
        note = self.make_note("deep", "Old Short")
        self.assertFalse(self.check(note, "deep")["valid"])
        self.assertTrue(self.check(note, "deep", "--allow-legacy-folder")["valid"])

    def test_missing_image_is_rejected(self) -> None:
        note = self.make_note("summary")
        with note.open("a", encoding="utf-8") as handle:
            handle.write("![Fig. 1](assets/summary-figures/missing.png)\n")
        self.assertFalse(self.check(note, "summary")["valid"])

    def add_image(self, note: Path, relative: str) -> None:
        asset = note.parent / relative
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"fixture image")

    def append(self, note: Path, text: str) -> None:
        with note.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")

    def test_spaced_angle_image_path_is_checked(self) -> None:
        note = self.make_note("summary")
        self.append(note, "![Fig. 1](<assets/summary-figures/figure one.png>)")
        self.assertFalse(self.check(note, "summary")["valid"])
        self.add_image(note, "assets/summary-figures/figure one.png")
        self.assertTrue(self.check(note, "summary")["valid"])

    def test_reference_image_checks_definition_and_file(self) -> None:
        note = self.make_note("summary")
        self.append(note, "![Fig. 1][figure]")
        self.assertFalse(self.check(note, "summary")["valid"])
        self.append(note, '[figure]: <assets/summary-figures/figure one.png> "Figure title"')
        self.assertFalse(self.check(note, "summary")["valid"])
        self.add_image(note, "assets/summary-figures/figure one.png")
        self.assertTrue(self.check(note, "summary")["valid"])

    def test_reference_image_cannot_escape_paper_folder(self) -> None:
        note = self.make_note("summary")
        (self.root / "outside.png").write_bytes(b"fixture image")
        self.append(note, "![Fig. 1][figure]\n[figure]: ../outside.png")
        result = self.check(note, "summary")
        self.assertFalse(result["valid"])
        self.assertIn("image escapes", " ".join(result["errors"]))

    def test_cross_mode_paths_are_normalized_before_checking(self) -> None:
        note = self.make_note("summary")
        self.add_image(note, "assets/deep-figures/F001.png")
        (note.parent / "assets" / "summary-figures").mkdir()
        original = note.read_text(encoding="utf-8")
        for link in (
            "assets/summary-figures/../deep-figures/F001.png",
            "assets/%64eep-figures/F001.png",
        ):
            with self.subTest(link=link):
                note.write_text(original + f"![Fig. 1]({link})\n", encoding="utf-8")
                result = self.check(note, "summary")
                self.assertFalse(result["valid"])
                self.assertIn("cross-mode", " ".join(result["errors"]))

    def test_percent_encoded_valid_asset_and_escape(self) -> None:
        note = self.make_note("summary")
        self.add_image(note, "assets/summary-figures/figure one.png")
        self.append(note, "![Fig. 1](assets/summary-figures/figure%20one.png)")
        self.assertTrue(self.check(note, "summary")["valid"])
        (self.root / "outside.png").write_bytes(b"fixture image")
        self.append(note, "![Fig. 2](%2e%2e/outside.png)")
        self.assertFalse(self.check(note, "summary")["valid"])

    def test_body_only_direction_is_not_frontmatter(self) -> None:
        note = self.make_note("summary")
        note.write_text(note.read_text(encoding="utf-8").replace("research_direction: 测试\n", ""), encoding="utf-8")
        self.append(note, "research_direction: 测试")
        result = self.check(note, "summary")
        self.assertFalse(result["valid"])
        self.assertIn("research_direction", " ".join(result["errors"]))

    def test_fenced_headings_do_not_satisfy_required_sections(self) -> None:
        note = self.make_note("summary")
        original = note.read_text(encoding="utf-8")
        beginning, headings = original.split("## 📜", 1)
        note.write_text(beginning + "```markdown\n## 📜" + headings + "```\n", encoding="utf-8")
        self.assertFalse(self.check(note, "summary")["valid"])

    def test_fenced_title_is_not_document_title(self) -> None:
        note = self.make_note("summary")
        note.write_text(note.read_text(encoding="utf-8").replace("# Exact Paper Title\n", "~~~markdown\n# Exact Paper Title\n~~~\n"), encoding="utf-8")
        result = self.check(note, "summary")
        self.assertFalse(result["valid"])
        self.assertIn("missing document title", result["errors"])

    def test_fenced_image_examples_are_ignored(self) -> None:
        note = self.make_note("summary")
        self.append(note, "````markdown\n![missing](assets/deep-figures/missing.png)\n```\n![missing][figure]\n[figure]: ../missing.png\n````")
        self.assertTrue(self.check(note, "summary")["valid"])

    def test_single_line_display_math_contract_is_preserved(self) -> None:
        note = self.make_note("summary")
        self.append(note, "$$E = mc^2$$")
        self.assertTrue(self.check(note, "summary")["valid"])
        self.append(note, "$$\nE = mc^2\n$$")
        self.assertFalse(self.check(note, "summary")["valid"])

    def test_required_headings_may_retain_descriptive_suffixes(self) -> None:
        note = self.make_note("summary")
        note.write_text(note.read_text(encoding="utf-8").replace("## 📜 研究核心", "## 📜 研究核心（论文概览）"), encoding="utf-8")
        self.assertTrue(self.check(note, "summary")["valid"])

    def test_malformed_and_invalid_image_paths_report_errors(self) -> None:
        note = self.make_note("summary")
        original = note.read_text(encoding="utf-8")
        for link in ("![Fig. 1](<unfinished", "![Fig. 1](assets/summary-figures/%00.png)"):
            with self.subTest(link=link):
                note.write_text(original + link + "\n", encoding="utf-8")
                self.assertFalse(self.check(note, "summary")["valid"])


if __name__ == "__main__":
    unittest.main()
