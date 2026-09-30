"""Regression checks for paper identity lookup and malformed review JSON."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4


PLUGIN = Path(__file__).resolve().parents[1]
INGESTION = PLUGIN / "skills" / "paper-ingestion" / "scripts"
FIND_EXISTING = INGESTION / "find_existing.py"
VALIDATE_BUNDLE = INGESTION / "validate_bundle.py"
REVIEW = PLUGIN / "skills" / "paper-parse-review" / "scripts" / "review.py"
TMP_ROOT = PLUGIN / "tmp" / "ingestion-identity-tests"


class IngestionIdentityTest(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.root = TMP_ROOT / f"case-{uuid4().hex[:10]}"
        self.root.mkdir()

    def tearDown(self) -> None:
        target, allowed = self.root.resolve(), TMP_ROOT.resolve()
        if target == allowed or not target.is_relative_to(allowed):
            raise RuntimeError(f"Unsafe test cleanup path: {target}")
        shutil.rmtree(target)

    def call(self, script: Path, *args: object, success: bool) -> dict:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), *(str(arg) for arg in args)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        self.assertEqual(result.returncode == 0, success, result.stderr or result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Invalid JSON: {result.stdout}\n{result.stderr}") from exc

    def test_frontmatter_hash_lookup_survives_invalid_neighboring_manifests(self) -> None:
        literature = self.root / "literature"
        paper = literature / "direction" / "known-paper"
        paper.mkdir(parents=True)
        digest = "a" * 64
        (paper / "card.md").write_text(
            f"---\ntitle: Known paper\npdf_sha256: '{digest}'\n---\n",
            encoding="utf-8",
        )
        for folder, content in (("invalid-json", "{"), ("non-object-json", "[]")):
            neighbor = literature / folder
            neighbor.mkdir()
            (neighbor / "parse-manifest.json").write_text(content, encoding="utf-8")
        result = self.call(FIND_EXISTING, literature, "--sha256", digest, success=True)
        self.assertEqual(len(result["candidates"]), 1, result)
        match = result["candidates"][0]
        self.assertEqual(Path(match["folder"]).resolve(), paper.resolve())
        self.assertEqual(match["reasons"], ["pdf_sha256"])
        self.assertEqual(match["strength"], 3)

    def test_non_object_manifest_returns_structured_failure(self) -> None:
        bundle = self.root / "bundle"
        bundle.mkdir()
        (bundle / "parse-manifest.json").write_text("[]", encoding="utf-8")
        result = self.call(VALIDATE_BUNDLE, bundle, success=False)
        self.assertFalse(result["ok"])
        self.assertIn("must contain an object", " ".join(result["errors"]))

    def test_non_object_audit_returns_structured_failure_for_sync_and_check(self) -> None:
        bundle = self.root / "bundle"
        bundle.mkdir()
        (bundle / "paper.md").write_text("# Test paper\n", encoding="utf-8")
        (bundle / "parse-audit.json").write_text("[]", encoding="utf-8")
        for command in ("sync", "check"):
            with self.subTest(command=command):
                args = (command, bundle)
                if command == "check":
                    args += ("--source-pdf", self.root / "source.pdf", "--require-verified")
                result = self.call(REVIEW, *args, success=False)
                self.assertFalse(result["ok"])
                self.assertIn("must contain an object", result["error"])


if __name__ == "__main__":
    unittest.main()
