"""Behavioral checks for the PDF review gate and ingestion handoff."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4

import pymupdf


SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
REVIEW = SKILL / "scripts" / "review.py"
INGEST = SKILL.parent / "paper-ingestion" / "scripts" / "validate_bundle.py"
TMP_ROOT = WORKSPACE / "tmp" / "paper-review-tests"


class ReviewGateTest(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.root = TMP_ROOT / f"case-{uuid4().hex[:10]}"
        self.root.mkdir()
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.pdf = self.root / "source.pdf"
        document = pymupdf.open()
        first = document.new_page()
        first.insert_text((72, 72), "Original page one. Fig. 1 has two panels.")
        first.draw_rect(pymupdf.Rect(72, 100, 260, 180), color=(0, 0, 0))
        second = document.new_page()
        second.insert_text((72, 72), "Original page two. Table 1 value is 42. E = mc2")
        document.save(self.pdf)
        document.close()
        self.markdown = (
            "# Test paper\nOriginal page one. Fig. 1 has two panels.\n"
            "![Fig. 1](assets/parsed/fig-1.png)\n"
            "Original page two. Table 1 value is 42. E = mc2\n"
            "| A | B |\n| --- | --- |\n| x | 42 |\n$$E = mc^2$$\n"
        )
        (self.bundle / "paper.md").write_text(self.markdown, encoding="utf-8")
        self.call(REVIEW, "init", self.bundle, "--source-pdf", self.pdf, "--locator", "doc:test/tier:standard", success=True)
        with pymupdf.open(self.pdf) as source:
            source[0].get_pixmap(clip=pymupdf.Rect(72, 100, 260, 180)).save(self.bundle / "assets" / "parsed" / "fig-1.png")

    def tearDown(self) -> None:
        target, root = self.root.resolve(), TMP_ROOT.resolve()
        if not target.is_relative_to(root) or target == root:
            raise RuntimeError(f"Unsafe test cleanup path: {target}")
        shutil.rmtree(target)

    def call(self, script: Path, *args: object, success: bool) -> dict:
        command = [sys.executable, str(script), *(str(arg) for arg in args)]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Invalid JSON: {result.stdout}\n{result.stderr}") from exc
        if success:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        return output

    def complete_audit(self) -> dict:
        path = self.bundle / "parse-audit.json"
        audit = json.loads(path.read_text(encoding="utf-8"))
        first, second = audit["pages"]
        first.update(text_status="matched", text_anchor="Original page one.", layout_status="matched", visual_inventory_complete=True, notes="Checked page text, figure panels, and caption against the PDF.")
        first["visuals"] = [{
            "kind": "figure", "label": "Fig. 1", "pdf_locator": "doc:test/tier:standard/page:1",
            "status": "matched", "paper_anchor": "![Fig. 1](assets/parsed/fig-1.png)", "asset": "assets/parsed/fig-1.png",
        }]
        second.update(text_status="corrected", text_anchor="Table 1 value is 42", layout_status="matched", visual_inventory_complete=True, notes="Checked table cells, equation, and corrected number against the PDF.")
        second["visuals"] = [
            {"kind": "table", "label": "Table 1", "pdf_locator": "doc:test/tier:standard/page:2", "status": "matched", "paper_anchor": "| x | 42 |"},
            {"kind": "equation", "label": "Eq. 1", "pdf_locator": "doc:test/tier:standard/page:2", "status": "matched", "paper_anchor": "$$E = mc^2$$"},
        ]
        audit["corrections"] = [{
            "page": 2, "kind": "text", "pdf_locator": "doc:test/tier:standard/page:2",
            "problem": "MinerU read the table value as 4Z", "change": "Corrected it to 42 from the PDF",
            "result_anchor": "Table 1 value is 42", "status": "resolved",
        }]
        path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        return audit

    def test_pending_review_cannot_be_imported(self) -> None:
        result = self.call(REVIEW, "check", self.bundle, "--source-pdf", self.pdf, "--require-verified", success=False)
        self.assertEqual(result["status"], "partial")
        self.assertIn("final import", " ".join(result["errors"]))

    def test_corrected_review_and_bundle_pass(self) -> None:
        self.complete_audit()
        result = self.call(REVIEW, "sync", self.bundle, success=True)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["checked_pages"], 2)
        self.call(REVIEW, "check", self.bundle, "--source-pdf", self.pdf, "--require-verified", success=True)
        audit = json.loads((self.bundle / "parse-audit.json").read_text(encoding="utf-8"))
        manifest = {
            "schema_version": 1,
            "identity": {"title": "Test paper", "doi": None, "zotero_item_key": None, "source_pdf": str(self.pdf), "pdf_sha256": hashlib.sha256(self.pdf.read_bytes()).hexdigest()},
            "parse": {"tool": "MinerU", "version": "4.x", "tier": "standard", "remote": False, "locator": "doc:test/tier:standard", "completed_at": "2026-09-26", "page_count": 2},
            "review": {"status": audit["review_status"], "checked_pages": audit["checked_pages"], "open_issues": audit["open_issues"], "reviewed_at": "2026-09-26"},
            "artifacts": {"paper_md": "paper.md", "asset_dir": "assets/parsed", "review_log": "parse-review.md", "audit": "parse-audit.json"},
        }
        (self.bundle / "parse-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.call(INGEST, self.bundle, "--source-pdf", self.pdf, "--require-audit", success=True)

    def test_missing_correction_blocks_sync(self) -> None:
        audit = self.complete_audit()
        audit["corrections"] = []
        (self.bundle / "parse-audit.json").write_text(json.dumps(audit), encoding="utf-8")
        result = self.call(REVIEW, "sync", self.bundle, success=False)
        self.assertIn("correction", result["error"])

    def test_omitted_pdf_page_blocks_sync(self) -> None:
        audit = self.complete_audit()
        audit["pages"].pop()
        (self.bundle / "parse-audit.json").write_text(json.dumps(audit), encoding="utf-8")
        result = self.call(REVIEW, "sync", self.bundle, success=False)
        self.assertIn("every original PDF page", result["error"])

    def test_unresolved_visual_stays_partial(self) -> None:
        audit = self.complete_audit()
        audit["pages"][0]["visuals"][0]["status"] = "unresolved"
        audit["corrections"].append({
            "page": 1, "kind": "figure", "label": "Fig. 1", "pdf_locator": "doc:test/tier:standard/page:1",
            "problem": "Panel labels remain unreadable", "status": "open",
        })
        (self.bundle / "parse-audit.json").write_text(json.dumps(audit), encoding="utf-8")
        result = self.call(REVIEW, "sync", self.bundle, success=True)
        self.assertEqual(result["status"], "partial")
        self.call(REVIEW, "check", self.bundle, "--source-pdf", self.pdf, "--require-verified", success=False)

    def test_missing_image_or_stale_report_blocks_final_check(self) -> None:
        self.complete_audit()
        self.call(REVIEW, "sync", self.bundle, success=True)
        (self.bundle / "assets" / "parsed" / "fig-1.png").unlink()
        result = self.call(REVIEW, "check", self.bundle, "--source-pdf", self.pdf, "--require-verified", success=False)
        self.assertIn("missing", " ".join(result["errors"]))
        with pymupdf.open(self.pdf) as source:
            source[0].get_pixmap(clip=pymupdf.Rect(72, 100, 260, 180)).save(self.bundle / "assets" / "parsed" / "fig-1.png")
        audit = json.loads((self.bundle / "parse-audit.json").read_text(encoding="utf-8"))
        audit["pages"][0]["notes"] = "Changed without regenerating the report"
        (self.bundle / "parse-audit.json").write_text(json.dumps(audit), encoding="utf-8")
        result = self.call(REVIEW, "check", self.bundle, "--source-pdf", self.pdf, "--require-verified", success=False)
        self.assertIn("stale", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
