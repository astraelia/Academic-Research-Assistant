"""Mechanically validate a staged or archived MinerU paper bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


IMAGE_LINK = re.compile(r"!\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)")


def io_path(path: Path) -> Path:
    path = path.absolute()
    if sys.platform != "win32" or str(path).startswith("\\\\?\\"):
        return path
    raw = str(path)
    return Path("\\\\?\\UNC\\" + raw[2:]) if raw.startswith("\\\\") else Path("\\\\?\\" + raw)


def internal_path(bundle: Path, value: str, label: str, errors: list[str]) -> Path | None:
    value = unquote(value).replace("\\", "/")
    relative = Path(value)
    if not value or relative.is_absolute() or ":" in value or ".." in relative.parts:
        errors.append(f"{label} must be a relative path inside the bundle: {value!r}")
        return None
    target = (bundle / relative).resolve()
    if not target.is_relative_to(bundle):
        errors.append(f"{label} escapes the bundle: {value!r}")
        return None
    return target


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--source-pdf", type=Path, help="Compare the recorded source hash with this PDF")
    parser.add_argument("--require-audit", action="store_true", help="Require a matching paper-parse-review audit for a new import")
    args = parser.parse_args()
    bundle = io_path(args.bundle).resolve()
    errors: list[str] = []

    manifest_path = bundle / "parse-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if not isinstance(manifest, dict):
            raise ValueError("parse-manifest.json must contain an object")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "errors": [f"Cannot read parse-manifest.json: {exc}"]}, ensure_ascii=True, indent=2))
        return 1

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    identity = manifest.get("identity") or {}
    parse = manifest.get("parse") or {}
    review = manifest.get("review") or {}
    artifacts = manifest.get("artifacts") or {}
    if not isinstance(identity, dict) or not isinstance(parse, dict) or not isinstance(review, dict) or not isinstance(artifacts, dict):
        errors.append("identity, parse, review, and artifacts must be objects")
        identity, parse, review, artifacts = {}, {}, {}, {}

    if not identity.get("title"):
        errors.append("identity.title is required")
    if not identity.get("source_pdf"):
        errors.append("identity.source_pdf is required")
    recorded_hash = str(identity.get("pdf_sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", recorded_hash):
        errors.append("identity.pdf_sha256 must be a lowercase SHA-256")
    if parse.get("tool") != "MinerU":
        errors.append("parse.tool must be MinerU")
    if not parse.get("version") or not parse.get("tier") or not isinstance(parse.get("remote"), bool):
        errors.append("parse.version, parse.tier, and boolean parse.remote are required")
    status = review.get("status")
    if status not in {"verified", "partial", "blocked"}:
        errors.append("review.status must be verified, partial, or blocked")
    page_count = parse.get("page_count")
    checked = review.get("checked_pages")
    issues = review.get("open_issues")
    if not isinstance(checked, list) or not all(isinstance(x, int) and x > 0 for x in checked):
        errors.append("review.checked_pages must contain positive page numbers")
        checked = []
    if not isinstance(issues, list):
        errors.append("review.open_issues must be a list")
        issues = []
    if status == "verified":
        if not isinstance(page_count, int) or page_count <= 0:
            errors.append("verified requires a positive parse.page_count")
        elif set(checked) != set(range(1, page_count + 1)):
            errors.append("verified requires checked_pages to cover every PDF page")
        if issues:
            errors.append("verified requires an empty open_issues list")

    expected_artifacts = {"paper_md": "paper.md", "asset_dir": "assets/parsed", "review_log": "parse-review.md"}
    for field, expected in expected_artifacts.items():
        if artifacts.get(field) != expected:
            errors.append(f"artifacts.{field} must be {expected}")

    paper = internal_path(bundle, str(artifacts.get("paper_md") or ""), "artifacts.paper_md", errors)
    log = internal_path(bundle, str(artifacts.get("review_log") or ""), "artifacts.review_log", errors)
    assets = internal_path(bundle, str(artifacts.get("asset_dir") or ""), "artifacts.asset_dir", errors)
    for label, path in (("paper.md", paper), ("parse-review.md", log)):
        if path is not None and (not path.is_file() or path.stat().st_size == 0):
            errors.append(f"{label} is missing or empty")
    if assets is not None and not assets.is_dir():
        errors.append("asset_dir is missing")

    if args.require_audit:
        if artifacts.get("audit") != "parse-audit.json":
            errors.append("artifacts.audit must be parse-audit.json")
        try:
            audit = json.loads((bundle / "parse-audit.json").read_text(encoding="utf-8-sig"))
            if not isinstance(audit, dict):
                raise ValueError("audit must be an object")
            if audit.get("pdf_sha256") != recorded_hash or audit.get("pdf_page_count") != page_count:
                errors.append("audit PDF hash/page count differs from manifest")
            if audit.get("review_status") != status or audit.get("checked_pages") != checked or audit.get("open_issues") != issues:
                errors.append("audit review state differs from manifest")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"Cannot read parse-audit.json: {exc}")

    if paper is not None and paper.is_file():
        try:
            markdown = paper.read_text(encoding="utf-8-sig")
            if "![[" in markdown:
                errors.append("paper.md contains Obsidian image embeds; use relative Markdown image links")
            for match in IMAGE_LINK.finditer(markdown):
                value = match.group(1) or match.group(2)
                target = internal_path(bundle, value, "image link", errors)
                if target is not None and not target.is_file():
                    errors.append(f"image link target does not exist: {value}")
                elif target is not None and assets is not None and not target.is_relative_to(assets):
                    errors.append(f"image link must point inside assets/parsed: {value}")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Cannot read paper.md: {exc}")

    if args.source_pdf is not None:
        source_pdf = io_path(args.source_pdf)
        if not source_pdf.is_file():
            errors.append(f"Source PDF does not exist: {args.source_pdf}")
        elif sha256(source_pdf) != recorded_hash:
            errors.append("Source PDF SHA-256 differs from manifest")

    print(json.dumps({"ok": not errors, "review_status": status, "checked_pages": len(checked), "errors": errors}, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
