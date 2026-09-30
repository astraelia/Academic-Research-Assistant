"""Scaffold, summarize, and validate a page-by-page MinerU/PDF review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote


IMAGE_LINK = re.compile(r"!\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)")
GOOD = {"matched", "corrected"}
KINDS = {"text", "layout", "figure", "table", "equation"}
VISUAL_FORMAT_POLICY = "figures-as-images-tables-equations-as-markdown-v1"


def io_path(path: Path) -> Path:
    path = path.absolute()
    if sys.platform != "win32" or str(path).startswith("\\\\?\\"):
        return path
    raw = str(path)
    return Path("\\\\?\\UNC\\" + raw[2:]) if raw.startswith("\\\\") else Path("\\\\?\\" + raw)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_page_count(path: Path) -> int:
    """Count the original PDF pages independently of the MinerU export."""
    try:
        import pymupdf

        with pymupdf.open(str(path)) as document:
            return len(document)
    except (ImportError, OSError, ValueError, RuntimeError):
        pass
    if shutil.which("pdfinfo"):
        result = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, errors="replace", check=False)
        match = re.search(r"^Pages:\s*(\d+)\s*$", result.stdout, re.MULTILINE)
        if result.returncode == 0 and match:
            return int(match.group(1))
    raise RuntimeError("Cannot count PDF pages; install PyMuPDF or pdfinfo")


def locator_for_page(value: object, page: int, base: str) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(rf"{re.escape(base)}/page:{page}(?:/block:\d+)?", value))


def inside_asset_dir(bundle: Path, value: str, errors: list[str], label: str) -> Path | None:
    value = unquote(value).replace("\\", "/")
    relative = Path(value)
    if not value or relative.is_absolute() or ":" in value or ".." in relative.parts:
        errors.append(f"{label} must be a relative path inside assets/parsed: {value!r}")
        return None
    target = (bundle / relative).resolve()
    if not target.is_relative_to(bundle / "assets" / "parsed"):
        errors.append(f"{label} escapes assets/parsed: {value!r}")
        return None
    return target


def image_links(bundle: Path, markdown: str, errors: list[str]) -> set[Path]:
    links: set[Path] = set()
    for match in IMAGE_LINK.finditer(markdown):
        value = match.group(1) or match.group(2)
        target = inside_asset_dir(bundle, value, errors, "Markdown image")
        if target is not None:
            links.add(target)
            if not target.is_file():
                errors.append(f"Markdown image is missing: {value}")
    if "![[" in markdown:
        errors.append("paper.md must use relative Markdown image links, not Obsidian embeds")
    return links


def is_markdown_table_anchor(value: object) -> bool:
    return isinstance(value, str) and any(
        line.strip().startswith("|") and line.strip().endswith("|")
        for line in value.splitlines()
    )

def is_markdown_math_anchor(value: object) -> bool:
    if not isinstance(value, str):
        return False
    delimiters = ("$", r"\(", r"\[", r"\begin{equation}", r"\begin{equation*}",
                  r"\begin{align}", r"\begin{align*}", r"\begin{aligned}",
                  r"\begin{gather}", r"\begin{gather*}", r"\begin{multline}", r"\begin{split}")
    return any(delimiter in value for delimiter in delimiters)

def issue_text(item: dict) -> str:
    element = f" {item['label']}" if item.get("label") else ""
    return f"PDF p. {item['page']} {item['kind']}{element}: {item['problem']}"


def audit_state(bundle: Path, audit: object, markdown: str) -> tuple[list[str], list[int], list[str]]:
    """Validate review evidence; only viewing the PDF can establish semantic accuracy."""
    errors: list[str] = []
    if not isinstance(audit, dict):
        return ["parse-audit.json must contain an object"], [], []
    if audit.get("schema_version") != 1:
        errors.append("audit schema_version must be 1")
    count = audit.get("pdf_page_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        return errors + ["pdf_page_count must be a positive integer"], [], []
    if not re.fullmatch(r"[0-9a-f]{64}", str(audit.get("pdf_sha256") or "")):
        errors.append("pdf_sha256 must be a lowercase SHA-256")
    base = audit.get("mineru_locator")
    if not isinstance(base, str) or not re.fullmatch(r"doc:[^/]+/tier:[^/]+", base):
        errors.append("mineru_locator must identify a MinerU document and tier")
        base = ""
    links = image_links(bundle, markdown, errors)

    format_policy = audit.get("visual_format_policy")
    if format_policy not in (None, VISUAL_FORMAT_POLICY):
        errors.append(f"unsupported visual_format_policy: {format_policy!r}")
    corrections = audit.get("corrections")
    if not isinstance(corrections, list):
        errors.append("corrections must be a list")
        corrections = []
    resolved: set[tuple[int, str, str]] = set()
    open_items: set[tuple[int, str, str]] = set()
    open_issues: list[str] = []
    for index, item in enumerate(corrections, 1):
        label = f"correction {index}"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        page, kind, element = item.get("page"), item.get("kind"), item.get("label") or ""
        if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= count or kind not in KINDS:
            errors.append(f"{label} needs a valid PDF page and kind")
            continue
        if not locator_for_page(item.get("pdf_locator"), page, base):
            errors.append(f"{label} needs a matching PDF page/block locator")
        if not isinstance(item.get("problem"), str) or not item["problem"].strip():
            errors.append(f"{label} needs a description of the original error")
            continue
        key = (page, kind, element)
        if item.get("status") == "resolved":
            resolved.add(key)
            for field in ("change", "result_anchor"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    errors.append(f"{label} needs {field}")
            if item.get("result_anchor") and item["result_anchor"] not in markdown:
                errors.append(f"{label} result_anchor is absent from paper.md")
            if format_policy == VISUAL_FORMAT_POLICY and kind == "table" and not is_markdown_table_anchor(item.get("result_anchor")):
                errors.append(f"{label} table result_anchor must be a Markdown pipe-table row")
            if format_policy == VISUAL_FORMAT_POLICY and kind == "equation" and not is_markdown_math_anchor(item.get("result_anchor")):
                errors.append(f"{label} equation result_anchor must use Markdown math delimiters")
        elif item.get("status") == "open":
            open_items.add(key)
            open_issues.append(issue_text(item))
        else:
            errors.append(f"{label} status must be resolved or open")

    pages = audit.get("pages")
    if not isinstance(pages, list):
        return errors + ["pages must be a list"], [], open_issues
    seen: set[int] = set()
    checked: list[int] = []
    for index, item in enumerate(pages, 1):
        if not isinstance(item, dict):
            errors.append(f"page entry {index} must be an object")
            continue
        page = item.get("page")
        if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= count or page in seen:
            errors.append(f"page entry {index} is invalid or duplicated")
            continue
        seen.add(page)
        if not locator_for_page(item.get("pdf_locator"), page, base):
            errors.append(f"PDF page {page} needs a matching page locator")
        text_status, layout_status = item.get("text_status"), item.get("layout_status")
        for kind, status in (("text", text_status), ("layout", layout_status)):
            if status not in {"pending", "matched", "corrected", "unresolved", "not_applicable"}:
                errors.append(f"PDF page {page} has invalid {kind}_status")
            if status == "corrected" and (page, kind, "") not in resolved:
                errors.append(f"PDF page {page} {kind} corrected without a resolved correction")
            if status == "unresolved" and (page, kind, "") not in open_items:
                errors.append(f"PDF page {page} {kind} unresolved without an open issue")
            if status == "not_applicable" and not str(item.get("notes") or "").strip():
                errors.append(f"PDF page {page} {kind} not_applicable needs a reason")
        if text_status in GOOD:
            anchor = item.get("text_anchor")
            if not isinstance(anchor, str) or not anchor.strip() or anchor not in markdown:
                errors.append(f"PDF page {page} text_anchor is absent from paper.md")
        inventory = item.get("visual_inventory_complete")
        if not isinstance(inventory, bool):
            errors.append(f"PDF page {page} visual_inventory_complete must be boolean")
        if inventory is True and not str(item.get("notes") or "").strip():
            errors.append(f"PDF page {page} needs a brief review note before its visual inventory is complete")
        visuals = item.get("visuals")
        if not isinstance(visuals, list):
            errors.append(f"PDF page {page} visuals must be a list")
            visuals = []
        visuals_complete = True
        visual_keys: set[tuple[str, str]] = set()
        for number, visual in enumerate(visuals, 1):
            label = f"PDF page {page} visual {number}"
            if not isinstance(visual, dict):
                errors.append(f"{label} must be an object")
                visuals_complete = False
                continue
            kind, element, status = visual.get("kind"), visual.get("label"), visual.get("status")
            if kind not in {"figure", "table", "equation"} or not isinstance(element, str) or not element.strip():
                errors.append(f"{label} needs kind and label")
                visuals_complete = False
                continue
            if (kind, element) in visual_keys:
                errors.append(f"{label} is duplicated")
            visual_keys.add((kind, element))
            if not locator_for_page(visual.get("pdf_locator"), page, base):
                errors.append(f"{label} needs a matching PDF locator")
            if status not in {"pending", "matched", "corrected", "unresolved"}:
                errors.append(f"{label} has invalid status")
            if status not in GOOD:
                visuals_complete = False
            if status == "corrected" and (page, kind, element) not in resolved:
                errors.append(f"{label} corrected without a resolved correction")
            if status == "unresolved" and (page, kind, element) not in open_items:
                errors.append(f"{label} unresolved without an open issue")
            if status in GOOD:
                anchor = visual.get("paper_anchor")
                if not isinstance(anchor, str) or not anchor.strip() or anchor not in markdown:
                    errors.append(f"{label} paper_anchor is absent from paper.md")
                asset = visual.get("asset")
                if kind == "figure" and not asset:
                    errors.append(f"{label} needs a figure asset")
                if format_policy == VISUAL_FORMAT_POLICY and kind in {"table", "equation"} and asset:
                    errors.append(f"{label} must be represented in Markdown, not by an image asset")
                if format_policy == VISUAL_FORMAT_POLICY and kind == "table" and not is_markdown_table_anchor(anchor):
                    errors.append(f"{label} paper_anchor must be a Markdown pipe-table row")
                if format_policy == VISUAL_FORMAT_POLICY and kind == "equation" and not is_markdown_math_anchor(anchor):
                    errors.append(f"{label} paper_anchor must use Markdown math delimiters")
                if asset:
                    target = inside_asset_dir(bundle, str(asset), errors, f"{label} asset")
                    if target is not None and (not target.is_file() or target not in links):
                        errors.append(f"{label} asset is missing or not linked from paper.md")
        if text_status in GOOD | {"not_applicable"} and layout_status in GOOD | {"not_applicable"} and inventory is True and visuals_complete:
            checked.append(page)
    if seen != set(range(1, count + 1)):
        errors.append("pages must list every original PDF page exactly once")
    return errors, sorted(checked), open_issues


def report(audit: dict) -> str:
    lines = [
        "# MinerU 解析逐页校验记录", "",
        f"- 原 PDF：{audit.get('source_pdf', '')}",
        f"- PDF SHA-256：`{audit.get('pdf_sha256', '')}`",
        f"- MinerU 定位：`{audit.get('mineru_locator', '')}`",
        f"- 复核状态：`{audit.get('review_status', '')}`",
        f"- 已核页码：{', '.join(map(str, audit.get('checked_pages', []))) or '无'}",
        "", "## 逐页核对", "",
        "| PDF 页 | 文字 | 版式 | 图表公式清单完成 | 元素数 | 备注 |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for item in audit["pages"]:
        note = str(item.get("notes") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {item['page']} | {item['text_status']} | {item['layout_status']} | {item['visual_inventory_complete']} | {len(item['visuals'])} | {note} |")
    lines += ["", "## 图、表、公式", ""]
    for item in audit["pages"]:
        for visual in item["visuals"]:
            lines.append(f"- PDF p. {item['page']} {visual['kind']} {visual['label']}：{visual['status']}；原 PDF `{visual['pdf_locator']}`；解析稿 `{visual.get('paper_anchor') or '待补'}`；资源 `{visual.get('asset') or 'Markdown 内容'}`。")
    if not any(item["visuals"] for item in audit["pages"]):
        lines.append("- 未登记图、表或公式；以逐页清单状态为准。")
    lines += ["", "## 错误与修正", ""]
    for item in audit["corrections"]:
        lines.append(f"- PDF p. {item['page']} {item['kind']} {item.get('label') or ''} [{item['status']}]：{item['problem']} → {item.get('change') or '待修复'}；依据 `{item['pdf_locator']}`；结果定位 `{item.get('result_anchor') or '待补'}`。")
    if not audit["corrections"]:
        lines.append("- 未发现需修正的错误。")
    lines += ["", "## 未解决问题", ""]
    lines.extend(f"- {issue}" for issue in audit.get("open_issues", []))
    if not audit.get("open_issues"):
        lines.append("- 无。")
    return "\n".join(lines) + "\n"


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "sync", "check"):
        command = commands.add_parser(name)
        command.add_argument("bundle", type=Path, help="Staging folder containing paper.md")
        if name in {"init", "check"}:
            command.add_argument("--source-pdf", required=True, type=Path)
        if name == "init":
            command.add_argument("--locator", required=True, help="MinerU document/tier locator")
        if name == "check":
            command.add_argument("--require-verified", action="store_true")
    args = parser.parse_args()
    bundle = io_path(args.bundle).resolve()
    try:
        markdown = (bundle / "paper.md").read_text(encoding="utf-8-sig")
        audit_path = bundle / "parse-audit.json"
        if args.command == "init":
            if audit_path.exists():
                raise FileExistsError(f"Existing audit will not be overwritten: {audit_path}")
            if not re.fullmatch(r"doc:[^/]+/tier:[^/]+", args.locator):
                raise ValueError("--locator must identify a MinerU document and tier")
            source = io_path(args.source_pdf)
            count = pdf_page_count(source)
            if count < 1:
                raise ValueError("original PDF has no pages")
            audit = {
                "schema_version": 1, "source_pdf": str(args.source_pdf), "pdf_sha256": sha256(source),
                "pdf_page_count": count, "mineru_locator": args.locator,
                "visual_format_policy": VISUAL_FORMAT_POLICY,
                "review_status": "partial", "checked_pages": [], "open_issues": [],
                "pages": [
                    {"page": page, "pdf_locator": f"{args.locator}/page:{page}", "text_status": "pending", "text_anchor": "", "layout_status": "pending", "visual_inventory_complete": False, "visuals": [], "notes": ""}
                    for page in range(1, count + 1)
                ], "corrections": [],
            }
            (bundle / "assets" / "parsed").mkdir(parents=True, exist_ok=True)
            save_json(audit_path, audit)
            (bundle / "parse-review.md").write_text(report(audit), encoding="utf-8")
            print(json.dumps({"status": "partial", "pdf_pages": count}, ensure_ascii=False))
            return 0
        audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
        if not isinstance(audit, dict):
            raise ValueError("parse-audit.json must contain an object")
        errors, checked, issues = audit_state(bundle, audit, markdown)
        expected_status = "verified" if len(checked) == audit.get("pdf_page_count") and not issues and not errors else "partial"
        if args.command == "sync":
            if errors:
                raise ValueError("; ".join(errors))
            audit["checked_pages"] = checked
            audit["open_issues"] = issues
            audit["review_status"] = expected_status
            audit["reviewed_at"] = date.today().isoformat()
            save_json(audit_path, audit)
            (bundle / "parse-review.md").write_text(report(audit), encoding="utf-8")
        else:
            if audit.get("checked_pages") != checked or audit.get("open_issues") != issues:
                errors.append("stored review status differs from page audit; run sync")
            if audit.get("review_status") != expected_status:
                errors.append("stored review_status differs from page audit; run sync")
            review_path = bundle / "parse-review.md"
            if not review_path.is_file() or review_path.read_text(encoding="utf-8-sig") != report(audit):
                errors.append("parse-review.md is missing or stale; run sync")
            source = io_path(args.source_pdf)
            if not source.is_file() or sha256(source) != audit.get("pdf_sha256"):
                errors.append("original PDF is missing or its SHA-256 differs from audit")
            elif pdf_page_count(source) != audit.get("pdf_page_count"):
                errors.append("original PDF page count differs from audit")
            if args.require_verified and expected_status != "verified":
                errors.append("final import requires every PDF page verified and every issue resolved")
        print(json.dumps({"ok": not errors, "status": expected_status, "checked_pages": len(checked), "pdf_pages": audit.get("pdf_page_count"), "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
