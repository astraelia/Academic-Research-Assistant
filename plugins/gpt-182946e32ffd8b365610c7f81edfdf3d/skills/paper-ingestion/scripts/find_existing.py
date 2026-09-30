"""Find possible existing paper folders without changing the vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


FIELDS = {"title", "doi", "zotero_key", "zotero_item_key", "source_pdf", "pdf_sha256"}


def io_path(path: Path) -> Path:
    path = path.absolute()
    if sys.platform != "win32" or str(path).startswith("\\\\?\\"):
        return path
    raw = str(path)
    return Path("\\\\?\\UNC\\" + raw[2:]) if raw.startswith("\\\\") else Path("\\\\?\\" + raw)


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip()


def frontmatter(path: Path) -> dict[str, str]:
    try:
        with io_path(path).open("r", encoding="utf-8-sig") as handle:
            if handle.readline().strip() != "---":
                return {}
            data: dict[str, str] = {}
            for index, line in enumerate(handle):
                if index > 100 or line.strip() == "---":
                    break
                key, sep, value = line.partition(":")
                key = key.strip()
                if sep and key in FIELDS:
                    data[key] = scalar(value)
            return data
    except (OSError, UnicodeError):
        return {}


def normalized_doi(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    return value.rstrip("/ ")


def normalized_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in value if char.isalnum())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("literature_root", type=Path)
    parser.add_argument("--doi", default="")
    parser.add_argument("--zotero-key", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--sha256", default="")
    args = parser.parse_args()
    root = args.literature_root.resolve()
    if not root.is_dir():
        parser.error(f"Literature root does not exist: {root}")
    if not any((args.doi, args.zotero_key, args.title, args.sha256)):
        parser.error("Supply at least one identity field")

    records: dict[Path, dict[str, object]] = {}

    def add(folder: Path, reason: str, strength: int) -> None:
        record = records.setdefault(folder, {"folder": str(folder), "reasons": [], "strength": 0})
        reasons = record["reasons"]
        assert isinstance(reasons, list)
        if reason not in reasons:
            reasons.append(reason)
        record["strength"] = max(int(record["strength"]), strength)

    def match(folder: Path, identity: dict[str, object]) -> None:
        key = str(identity.get("zotero_item_key") or identity.get("zotero_key") or "").casefold()
        if args.zotero_key and key == args.zotero_key.casefold():
            add(folder, "zotero_key", 3)
        if args.doi and normalized_doi(str(identity.get("doi") or "")) == normalized_doi(args.doi):
            add(folder, "doi", 3)
        if args.sha256 and str(identity.get("pdf_sha256") or "").casefold() == args.sha256.casefold():
            add(folder, "pdf_sha256", 3)
        if args.title and normalized_title(str(identity.get("title") or "")) == normalized_title(args.title):
            add(folder, "title_only_check_author_year", 1)

    for manifest in root.rglob("parse-manifest.json"):
        try:
            data = json.loads(io_path(manifest).read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                continue
            identity = data.get("identity", {})
            if isinstance(identity, dict):
                match(manifest.parent, identity)
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue

    for note in root.rglob("*.md"):
        data = frontmatter(note)
        if data:
            match(note.parent, data)

    candidates = sorted(records.values(), key=lambda item: (-int(item["strength"]), str(item["folder"])))
    print(json.dumps({"literature_root": str(root), "candidates": candidates}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
