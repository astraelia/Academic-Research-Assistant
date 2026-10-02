"""Exercise persistence, interruption boundaries and source-preserving term updates."""
from __future__ import annotations

import importlib.util
import itertools
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

PLUGIN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("terminology", PLUGIN / "scripts" / "terminology.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
TMP_ROOT = PLUGIN / "tmp" / "terminology-tests"


def note(values: dict, body="") -> str:
    return "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in values.items()) + "\n---\n" + body


TERM_BODY = """# 学术术语

%% terminology:managed:start %%

## 定义与适用边界

模板定义与边界说明。

## 中英文与学术表达

- 首选英文：
- 首选中文：
- 缩写与首次出现的写法：
- 已确认的变体及其适用范围：
- 有依据的常用表达：

## 文献证据

| 稳定论文 ID / 文献入口 | PDF 定位 | 本文含义或用法 | 新增信息 |
| --- | --- | --- | --- |

## 外部核验依据

| 机构／作者 | 条目与 URL | 版本 | 查询日期 | 作用 |
| --- | --- | --- | --- | --- |

## 相关术语与概念

只链接已确认目标。

## 分析与待复核问题

综合解释标为分析。

## 维护记录

| 日期 | 变更 | 依据 |
| --- | --- | --- |

%% terminology:managed:end %%

## 个人备注
"""


class TerminologyTest(unittest.TestCase):
    def setUp(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.root = TMP_ROOT / ("case-" + uuid4().hex[:10])
        self.root.mkdir()
        self.vault = self.root / "vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        (self.vault / ".obsidian" / "templates.json").write_text('{"folder":"Templates"}', encoding="utf-8")
        self.library = self.vault / "61_学术术语库"
        for folder in (self.library / "术语卡", self.library / "处理记录", self.vault / "Templates", self.vault / "Papers"):
            folder.mkdir(parents=True)
        (self.library / "总览.md").write_text(note({"type": "terminology_dashboard"}), encoding="utf-8")
        term = {key: [] for key in t.TERM_LISTS}
        term.update(type="terminology", schema_version="1.0", term_id=None, preferred_en=None, preferred_zh=None,
                    term_status="待复核", term_confidence="low", definition_scope=None, created="{{date}}", updated="{{date}}")
        (self.vault / "Templates" / "term.md").write_text(note(term, TERM_BODY), encoding="utf-8")
        run = {key: None for key in t.RUN_KEYS}
        run.update(type="terminology_run", schema_version="1.0", terminology_run_status="待处理", source_coverage="unknown",
                   scan_completed=False, source_changed=False, new_terms=[], updated_terms=[])
        (self.vault / "Templates" / "run.md").write_text(note(run, "# 模板\n"), encoding="utf-8")
        self.store = t.Store(self.vault)
        self.pdf = self.root / "paper.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic source identity fixture\n")
        self.card = self.vault / "Papers" / "Paper A.md"
        self.card.write_text(note({"type": "literature", "title": "Paper A"}, "# Paper A\n"), encoding="utf-8")
        self.raw_identity = {"paper_title": "Paper A", "doi": "https://doi.org/10.1234/AAA", "pdf_path": str(self.pdf),
                             "paper_note": "[[Papers/Paper A]]", "zotero_library_id": "1", "zotero_item_key": "KEY123"}
        self.ident = t.identity(self.raw_identity, self.store)

    def tearDown(self):
        target, allowed = self.root.resolve(), TMP_ROOT.resolve()
        if target == allowed or not target.is_relative_to(allowed):
            raise RuntimeError("Unsafe fixture cleanup")
        shutil.rmtree(t.io_path(target))

    def start(self, ident=None, stage="literature-intake", coverage="full-paper", supplement=False):
        return t.begin(self.store, ident or self.ident, stage, coverage, supplement)

    def complete(self, started, candidates=None, blocked=""):
        token = started["token"]
        t.checkpoint(self.store, token, {"candidates": candidates or [], "scan_completed": True,
                                       "coverage_evidence": "Checked synthetic fixture coverage for state tests", "blocked": blocked})
        return t.finish(self.store, token)

    def candidate(self, decision="create", **extra):
        return {"expression": "peak ground acceleration", "locator": "PDF p. 2, Methods", "decision": decision,
                "reason": "Reusable ground-motion measure and writing terminology", "context": "Source uses this measure for shaking intensity",
                "term": {"preferred_en": "peak ground acceleration", "preferred_zh": "峰值地面加速度", "abbr": ["PGA"],
                         "aliases": [], "domain": ["地震动"], "category": ["指标"], "definition": "Ground acceleration peak in the specified context.",
                         "definition_scope": "Earthquake ground-motion intensity", "term_status": "已核验", "term_confidence": "high"},
                "verification_confirmed": True, **extra}

    def other_paper(self):
        pdf = self.root / "other.pdf"
        pdf.write_bytes(b"%PDF synthetic other source")
        card = self.vault / "Papers" / "Paper B.md"
        card.write_text(note({"type": "literature"}, "# B"), encoding="utf-8")
        return t.identity({"paper_title": "Paper B", "doi": "10.1234/bbb", "pdf_path": str(pdf),
                           "paper_note": "[[Papers/Paper B]]"}, self.store)

    def test_three_stages_all_orders_persist_one_completion(self):
        for order in itertools.permutations(t.STAGES[:3]):
            with self.subTest(order=order):
                # Each order uses a separate DOI and source card, including a fresh Store between stages.
                suffix = "-".join(order)
                ident = t.identity({"paper_title": suffix, "doi": "10.1234/" + suffix, "identity_confirmed": True}, self.store)
                first = self.start(ident, order[0], "abstract-metadata-only")
                self.assertEqual(first["action"], "waiting-material")
                # Unique PDF for this paper, so its hash cannot match another record.
                pdf = self.root / (suffix + ".pdf")
                pdf.write_bytes(b"%PDF " + suffix.encode())
                ident = t.identity({"paper_title": suffix, "doi": "10.1234/" + suffix, "pdf_path": str(pdf)}, self.store)
                done = self.complete(self.start(ident, order[0]))
                for stage in order[1:]:
                    fresh = t.Store(self.vault)
                    skipped = t.begin(fresh, ident, stage, "full-paper")
                    self.assertEqual(skipped["action"], "skip-completed")
                    self.assertEqual(skipped["paper_id"], done["paper_id"])
                meta = t.fields(t.read(Path(done["record"])), t.RUN_KEYS)
                self.assertEqual(meta["completed_from"], order[0])
                self.assertEqual(meta["created_count"], 0)
        self.assertEqual(len(list(self.store.notes({"terminology_run"}))), 6)

    def test_metadata_then_pdf_keeps_id_and_finishes_from_later_stage(self):
        metadata = t.identity({"paper_title": "Paper A", "doi": self.raw_identity["doi"]}, self.store)
        waiting = self.start(metadata, coverage="abstract-metadata-only")
        self.assertFalse(self.store.lock.exists())
        done = self.complete(self.start(stage="paper-deep-reading"))
        self.assertEqual(done["paper_id"], waiting["paper_id"])
        self.assertEqual(t.fields(t.read(Path(done["record"])), t.RUN_KEYS)["completed_from"], "paper-deep-reading")

    def test_partial_coverage_and_required_network_failure_cannot_finish(self):
        started = self.start(coverage="partial-paper")
        with self.assertRaises(t.GateError):
            self.complete(started)
        t.abort(self.store, started["token"], "Partial text, resume later")
        resumed = self.start()
        with self.assertRaises(t.GateError):
            self.complete(resumed, blocked="Necessary glossary verification unavailable")
        self.assertEqual(t.inspect(self.store, self.ident)["status"], "处理中")
        t.checkpoint(self.store, resumed["token"], {"candidates": [], "blocked": ""})
        self.assertEqual(t.finish(self.store, resumed["token"])["action"], "completed")

    def test_same_term_in_two_papers_updates_and_preserves_personal_content(self):
        first = self.complete(self.start(), [self.candidate()])
        path, text, meta = list(self.store.notes({"terminology"}))[0]
        protected = "\n## My research remarks\nKeep my exact interpretation.\n"
        path.write_text(text + protected, encoding="utf-8")
        new = self.candidate("update", matched_term_id=meta["term_id"], match_confirmed=True, definition_compatible=True)
        new["term"]["preferred_en"] = "Peak Ground Acceleration"
        new["term"]["aliases"] = ["peak acceleration"]
        new["term"]["definition"] = "A proposed rewrite must not replace the established definition."
        second = self.complete(self.start(self.other_paper()), [new])
        cards = list(self.store.notes({"terminology"}))
        self.assertEqual(len(cards), 1)
        final_text, final_meta = cards[0][1:]
        self.assertTrue(final_text.endswith(protected))
        self.assertIn("Ground acceleration peak", final_text)
        self.assertNotIn("A proposed rewrite", final_text)
        self.assertEqual(final_meta["preferred_en"], "peak ground acceleration")
        self.assertEqual(len(final_meta["literature_sources"]), 2)
        self.assertEqual(first["created_count"], 1)
        self.assertEqual(second["updated_count"], 1)

    def test_abbreviation_collision_becomes_pending_without_merge(self):
        self.complete(self.start(), [self.candidate()])
        started = self.start(self.other_paper())
        ambiguous = self.candidate()
        ambiguous["term"]["preferred_en"] = "different meaning"
        with self.assertRaises(t.GateError):
            t.checkpoint(self.store, started["token"], {"candidates": [ambiguous]})
        pending = {"expression": "PGA", "locator": "PDF p. 2", "decision": "pending", "reason": "Ambiguous abbreviation; compare both meanings"}
        done = self.complete(started, [pending])
        self.assertEqual(done["pending_count"], 1)
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 1)

    def test_checkpoint_retry_does_not_duplicate_sources(self):
        started = self.start()
        t.checkpoint(self.store, started["token"], {"candidates": [self.candidate()]})
        t.abort(self.store, started["token"], "Interrupted after first candidate", failed=True)
        resumed = self.start(stage="literature-summary")
        done = self.complete(resumed, [self.candidate()])
        self.assertEqual(done["created_count"], 1)
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 1)
        text = list(self.store.notes({"terminology"}))[0][1]
        self.assertEqual(text.count("Source uses this measure for shaking intensity"), 1)
        self.assertEqual(text.count("创建术语卡"), 1)

    def test_crash_after_card_write_before_record_is_recovered_idempotently(self):
        started = self.start()
        with patch.object(t, "save_run", side_effect=OSError("Injected checkpoint write failure")):
            with self.assertRaises(OSError):
                t.checkpoint(self.store, started["token"], {"candidates": [self.candidate()]})
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 1)
        t.abort(self.store, started["token"], "Recover injected failure")
        done = self.complete(self.start(), [self.candidate()])
        self.assertEqual(done["created_count"], 1)
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 1)

    def test_global_lease_prevents_two_writers_and_requires_exact_token(self):
        started = self.start()
        with self.assertRaises(t.GateError):
            self.start(self.other_paper())
        with self.assertRaises(t.GateError):
            t.abort(self.store, "wrong-token", "Invalid recovery")
        self.assertTrue(self.store.lock.exists())
        self.complete(started)
        self.assertFalse(self.store.lock.exists())

    def test_completed_changed_pdf_requires_explicit_supplement(self):
        done = self.complete(self.start())
        old_hash = self.ident["pdf_sha256"]
        self.pdf.write_bytes(b"%PDF revised source")
        revised = t.identity(self.raw_identity, self.store)
        response = self.start(revised, "paper-deep-reading")
        self.assertEqual(response["action"], "source-changed")
        meta = t.fields(t.read(Path(done["record"])), t.RUN_KEYS)
        self.assertTrue(meta["source_changed"])
        self.assertEqual(meta["pdf_sha256"], old_hash)
        self.assertEqual(meta["terminology_run_status"], "已完成")
        updated = self.complete(self.start(revised, supplement=True))
        self.assertEqual(done["paper_id"], updated["paper_id"])
        data = t.state(t.read(Path(done["record"])), "terminology-run")
        self.assertEqual(data["revision"], 1)
        self.assertIn("Prior revision retained", t.read(Path(done["record"])))

    def test_late_doi_enriches_stable_id_without_processing_again(self):
        original = dict(self.raw_identity, doi="")
        first = self.complete(self.start(t.identity(original, self.store)))
        next_stage = self.start(stage="literature-summary")
        self.assertEqual(first["paper_id"], next_stage["paper_id"])
        self.assertEqual(next_stage["action"], "skip-completed")
        self.assertEqual(t.fields(t.read(Path(first["record"])), t.RUN_KEYS)["doi"], "10.1234/aaa")

    def test_conflicting_doi_and_multiple_record_matches_fail_closed(self):
        self.complete(self.start())
        self.complete(self.start(self.other_paper()))
        conflict = t.identity(dict(self.raw_identity, doi="10.1234/bbb"), self.store)
        with self.assertRaises(t.GateError):
            self.start(conflict)
        self.assertEqual(len(list(self.store.notes({"terminology_run"}))), 2)

    def test_same_item_key_in_different_libraries_is_not_a_global_identifier(self):
        first = t.identity({"paper_title": "First", "zotero_library_id": "1", "zotero_item_key": "SAMEKEY"}, self.store)
        second = t.identity({"paper_title": "Second", "zotero_library_id": "2", "zotero_item_key": "SAMEKEY"}, self.store)
        a = self.start(first, coverage="abstract-metadata-only")
        b = self.start(second, coverage="abstract-metadata-only")
        self.assertNotEqual(a["paper_id"], b["paper_id"])

    def test_pdf_changes_before_commit_cannot_be_marked_complete(self):
        started = self.start()
        t.checkpoint(self.store, started["token"], {"candidates": [], "scan_completed": True, "coverage_evidence": "Complete screening"})
        self.pdf.write_bytes(b"source changed during processing")
        with self.assertRaises(t.GateError):
            t.finish(self.store, started["token"])
        self.assertFalse(t.fields(t.read(Path(started["record"])), t.RUN_KEYS)["scan_completed"])

    def test_duplicate_and_wrongly_typed_completion_fields_are_rejected(self):
        done = self.complete(self.start())
        path = Path(done["record"])
        text = t.read(path)
        path.write_text(text.replace("scan_completed: true", 'scan_completed: "true"'), encoding="utf-8")
        with self.assertRaises(t.GateError):
            t.inspect(self.store, self.ident)
        path.write_text(text.replace("paper_id:", 'paper_id: "another"\npaper_id:', 1), encoding="utf-8")
        with self.assertRaises(t.GateError):
            t.inspect(self.store, self.ident)

    def test_unresolved_links_and_unconfirmed_merges_do_not_write_a_card(self):
        started = self.start()
        broken = self.candidate()
        broken["term"]["related_concepts"] = ["[[missing concept]]"]
        with self.assertRaises(t.GateError):
            t.checkpoint(self.store, started["token"], {"candidates": [broken]})
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 0)
        self.complete(started, [self.candidate()])
        started = self.start(self.other_paper())
        unconfirmed = self.candidate("update", matched_term_id=list(self.store.notes({"terminology"}))[0][2]["term_id"])
        with self.assertRaises(t.GateError):
            t.checkpoint(self.store, started["token"], {"candidates": [unconfirmed]})

    def test_concurrent_edit_is_preserved_instead_of_overwritten(self):
        started = self.start()
        path, text, meta, data = t.open_run(self.store, started["token"])
        path.write_text(text + "\nMy concurrent note\n", encoding="utf-8")
        with self.assertRaises(t.GateError):
            t.save_run(path, text, meta, data)
        self.assertTrue(t.read(path).endswith("My concurrent note\n"))

    def test_managed_updates_preserve_unknown_frontmatter_and_yaml_lists(self):
        text = "---\ntype: terminology\naliases:\n  - 'alias one'\n  - \"alias two\"\nprivate:\n  nested: untouched\n# user comment\n---\nPersonal body\n"
        self.assertEqual(t.fields(text, {"aliases"})["aliases"], ["alias one", "alias two"])
        result = t.patch_fields(text, {"aliases": ["alias one", "alias two", "new alias"]})
        self.assertIn("private:\n  nested: untouched\n# user comment", result)
        self.assertTrue(result.endswith("Personal body\n"))

    def test_renamed_library_and_run_directory_are_discovered(self):
        done = self.complete(self.start())
        moved = self.vault / "Research terms"
        self.library.rename(moved)
        (moved / "处理记录").rename(moved / "Runs moved")
        fresh = t.Store(self.vault)
        self.assertEqual(fresh.library, t.io_path(moved).resolve())
        result = t.begin(fresh, self.ident, "literature-summary", "full-paper")
        self.assertEqual(result["paper_id"], done["paper_id"])
        self.assertEqual(result["action"], "skip-completed")

    def test_standalone_term_is_idempotent_and_does_not_complete_a_paper(self):
        candidate = self.candidate()
        candidate["external_evidence"] = [{"url": "https://example.org/glossary/pga", "source": "Fixture source",
                                             "entry": "PGA", "version": "test", "checked_at": "2026-10-02",
                                             "role": "Synthetic selected-entry fixture", "read_verified": True}]
        first = t.single(self.store, {"candidate": candidate})
        second = t.single(self.store, {"candidate": self.candidate(external_evidence=candidate["external_evidence"])})
        self.assertEqual(first["term_id"], second["term_id"])
        self.assertEqual(len(list(self.store.notes({"terminology_run"}))), 0)
        self.assertEqual(t.audit(self.store)["terms"], 1)
        self.assertEqual(list(self.store.notes({"terminology"}))[0][2]["external_sources"], ["https://example.org/glossary/pga"])

    def test_cli_chat_only_does_not_even_create_a_lock_or_record(self):
        before = {p.relative_to(self.vault): p.read_bytes() for p in self.vault.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, "-X", "utf8", "-B", str(PLUGIN / "scripts" / "terminology.py"),
                                 "begin", "--vault", str(self.vault), "--chat-only"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["writes"], 0)
        self.assertEqual(before, {p.relative_to(self.vault): p.read_bytes() for p in self.vault.rglob("*") if p.is_file()})
        self.assertFalse(self.store.lock.exists())

    def test_cli_malformed_json_returns_structured_error(self):
        payload = self.root / "bad.json"
        payload.write_text("[]", encoding="utf-8")
        result = subprocess.run([sys.executable, "-X", "utf8", "-B", str(PLUGIN / "scripts" / "terminology.py"), "begin",
                                 "--vault", str(self.vault), "--identity", str(payload)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_completed_card_prevents_a_false_skip(self):
        self.complete(self.start(), [self.candidate()])
        path = list(self.store.notes({"terminology"}))[0][0]
        path.rename(path.with_suffix(".removed-for-fixture"))
        with self.assertRaises(t.GateError):
            t.inspect(self.store, self.ident)
        with self.assertRaises(t.GateError):
            self.start(stage="paper-deep-reading")

    def test_recovery_after_completion_commit_does_not_undo_completion(self):
        started = self.start()
        t.checkpoint(self.store, started["token"], {"candidates": [], "scan_completed": True,
                                               "coverage_evidence": "Full fixture screen"})
        with patch.object(self.store, "release", side_effect=OSError("Crash at lease release")):
            with self.assertRaises(OSError):
                t.finish(self.store, started["token"])
        self.assertEqual(t.inspect(self.store, self.ident)["action"], "skip-completed")
        t.abort(self.store, started["token"], "Confirmed the interrupted task ended after commit")
        self.assertEqual(t.inspect(self.store, self.ident)["action"], "skip-completed")

    def test_ambiguous_title_without_strong_identity_does_not_duplicate_record(self):
        self.complete(self.start())
        weak = t.identity({"paper_title": "Paper A", "identity_confirmed": True}, self.store)
        with self.assertRaises(t.GateError):
            self.start(weak, coverage="abstract-metadata-only")
        self.assertEqual(len(list(self.store.notes({"terminology_run"}))), 1)

    def test_applied_candidate_cannot_silently_change_on_retry(self):
        started = self.start()
        candidate = self.candidate()
        t.checkpoint(self.store, started["token"], {"candidates": [candidate]})
        candidate["reason"] = "Different decision rationale after publication"
        with self.assertRaises(t.GateError):
            t.checkpoint(self.store, started["token"], {"candidates": [candidate]})
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 1)

    def test_create_retains_template_sections_and_fills_academic_expression_items(self):
        self.complete(self.start(), [self.candidate()])
        path, text, meta = list(self.store.notes({"terminology"}))[0]
        _, expected = t.body_sections(t.managed_content(TERM_BODY))
        _, actual = t.body_sections(t.managed_content(text))
        self.assertEqual(list(actual), list(expected))
        self.assertIn("首选英文：peak ground acceleration", actual["中英文与学术表达"])
        self.assertIn("首选中文：峰值地面加速度", actual["中英文与学术表达"])
        self.assertIn("PGA", actual["中英文与学术表达"])
        self.assertIn("【写作建议】", actual["中英文与学术表达"])
        self.assertIn("待补", actual["中英文与学术表达"])
        self.assertIn("[[Papers/Paper A]]", actual["文献证据"])
        self.assertIn("暂无已核验", actual["相关术语与概念"])
        self.assertIn("创建术语卡", actual["维护记录"])
        self.assertTrue(t.audit(self.store)["ok"])

    def test_verified_writing_details_are_visible_and_require_source_basis(self):
        candidate = self.candidate()
        candidate["term"]["aliases"] = ["peak acceleration"]
        candidate["term"]["writing"] = {
            "first_use": [{"text": "peak ground acceleration (PGA)", "basis": candidate["locator"]}],
            "variants": [{"text": "peak acceleration", "scope": "Specified ground motion only", "basis": candidate["locator"]}],
            "academic_expressions": [{"text": "PGA as a shaking-intensity measure", "basis": candidate["locator"]}],
        }
        self.complete(self.start(), [candidate])
        text = list(self.store.notes({"terminology"}))[0][1]
        self.assertIn("peak ground acceleration (PGA)（依据：PDF p. 2, Methods）", text)
        self.assertIn("适用范围：Specified ground motion only", text)
        self.assertIn("PGA as a shaking-intensity measure", text)

    def test_unsourced_writing_detail_does_not_publish_a_card(self):
        started = self.start()
        candidate = self.candidate()
        candidate["term"]["writing"] = {"academic_expressions": [{"text": "Unsupported phrase", "basis": "AI recollection"}]}
        with self.assertRaises(t.GateError):
            t.checkpoint(self.store, started["token"], {"candidates": [candidate]})
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 0)

    def test_finish_and_audit_reject_missing_visible_template_section(self):
        started = self.start()
        t.checkpoint(self.store, started["token"], {"candidates": [self.candidate()], "scan_completed": True,
                                                "coverage_evidence": "Full synthetic fixture screen"})
        path, text, _ = list(self.store.notes({"terminology"}))[0]
        path.write_text(text.replace("## 相关术语与概念", "### 相关术语与概念"), encoding="utf-8")
        self.assertFalse(t.audit(self.store)["ok"])
        with self.assertRaises(t.GateError):
            t.finish(self.store, started["token"])
        self.assertEqual(t.inspect(self.store, self.ident)["status"], "处理中")

    def test_completed_record_does_not_hide_template_defect(self):
        self.complete(self.start(), [self.candidate()])
        path, text, _ = list(self.store.notes({"terminology"}))[0]
        path.write_text(text.replace("- 首选中文：峰值地面加速度", "- 首选中文："), encoding="utf-8")
        with self.assertRaises(t.GateError):
            t.inspect(self.store, self.ident)
        with self.assertRaises(t.GateError):
            self.start(stage="paper-deep-reading")
        self.assertFalse(self.store.lock.exists())

    def test_hidden_or_fenced_headings_cannot_satisfy_template_validation(self):
        self.complete(self.start(), [self.candidate()])
        path, text, _ = list(self.store.notes({"terminology"}))[0]
        for replacement in ("%%\n## 维护记录\n%%", "```markdown\n## 维护记录\n```"):
            with self.subTest(replacement=replacement):
                path.write_text(text.replace("## 维护记录", replacement), encoding="utf-8")
                self.assertFalse(t.audit(self.store)["ok"])

    def test_active_template_order_analysis_title_and_extra_section_are_preserved(self):
        path = self.vault / "Templates" / "term.md"
        text = t.read(path).replace("## 分析与待复核问题", "## AI 分析与待复核问题")
        text = text.replace("## 维护记录", "## 自定义写作提醒\n\nKeep this template-specific instruction.\n\n## 维护记录")
        path.write_text(text, encoding="utf-8")
        _, sections = t.body_sections(t.managed_content(text))
        reordered = dict(reversed(list(sections.items())))
        path.write_text(t.replace_region(text, "terminology", "\n\n".join("## " + h + "\n\n" + b for h, b in reordered.items())), encoding="utf-8")
        self.complete(self.start(), [self.candidate()])
        output = list(self.store.notes({"terminology"}))[0][1]
        _, actual = t.body_sections(t.managed_content(output))
        self.assertEqual(list(actual), list(reordered))
        self.assertIn("Keep this template-specific instruction.", output)
        self.assertNotIn("\n## 分析与待复核问题\n", output)

    def test_update_renders_aliases_and_relationships_and_preserves_managed_prose(self):
        self.complete(self.start(), [self.candidate()])
        path, text, meta = list(self.store.notes({"terminology"}))[0]
        text = text.replace("## 文献证据", "My expression-section note must survive.\n\n## 文献证据")
        path.write_text(text + "\nMy personal ending.\n", encoding="utf-8")
        new = self.candidate("update", matched_term_id=meta["term_id"], match_confirmed=True, definition_compatible=True)
        new["term"]["aliases"] = ["peak acceleration"]
        new["term"]["related_concepts"] = ["[[Papers/Paper B]]"]
        ident = self.other_paper()
        self.complete(self.start(ident), [new])
        output = t.read(path)
        _, sections = t.body_sections(t.managed_content(output))
        self.assertIn("peak acceleration", sections["中英文与学术表达"])
        self.assertIn("[[Papers/Paper B]]", sections["相关术语与概念"])
        self.assertIn("My expression-section note must survive.", output)
        self.assertTrue(output.endswith("My personal ending.\n"))
        self.assertEqual(t.fields(output, t.TERM_KEYS)["term_id"], meta["term_id"])
        self.assertEqual(output.count("Source uses this measure for shaking intensity"), 2)

    def test_bad_template_table_is_rejected_before_card_publication(self):
        path = self.vault / "Templates" / "term.md"
        path.write_text(t.read(path).replace("| PDF 定位 | 本文含义或用法 |", "| PDF 定位及含义 |"), encoding="utf-8")
        started = self.start()
        with self.assertRaises(t.GateError):
            t.checkpoint(self.store, started["token"], {"candidates": [self.candidate()]})
        self.assertEqual(len(list(self.store.notes({"terminology"}))), 0)

    def test_deleted_relationship_body_is_reported_by_audit(self):
        self.other_paper()
        candidate = self.candidate()
        candidate["term"]["related_terms"] = ["[[Papers/Paper B]]"]
        self.complete(self.start(), [candidate])
        path, text, _ = list(self.store.notes({"terminology"}))[0]
        path.write_text(text.replace("- 相关术语：[[Papers/Paper B]]", "暂无关系。"), encoding="utf-8")
        self.assertFalse(t.audit(self.store)["ok"])


if __name__ == "__main__":
    unittest.main()
