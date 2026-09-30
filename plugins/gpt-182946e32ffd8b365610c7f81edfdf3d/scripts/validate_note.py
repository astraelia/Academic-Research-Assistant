#!/usr/bin/env python3
"""Validate required note sections, mode-specific assets, image links, and math delimiters."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


REQUIRED = {
    "summary": ("## 📜 研究核心", "## 🔁 研究内容", "## 🧠 文献价值", "## 🤔 阅读总结"),
    "deep": ("## 🧭 01｜论文定位", "## 🧠 02｜研究逻辑", "## 📚 03｜背景与问题", "## 🧮 04｜理论、方法与公式", "## 🔬 05｜实验/数值设计与证据链", "## 🖼️ 06｜图表精读", "## 🧩 07｜结论边界与批判性分析", "## 💡 08｜研究迁移与最终精读结论"),
}
IMAGE = re.compile(r"(?<!\\)!\[((?:\\.|[^\]\\])*)\]")
IMAGE_DESTINATION = re.compile(
    r"\([ \t]*(?:<(?P<angle>(?:\\.|[^<>\r\n])*)>|"
    r"(?P<plain>(?:\\.|[^()\s\\]|\([^()\r\n]*\))+))[ \t]*"
    r"(?:[\"'](?:\\.|[^\"'\\])*[\"'][ \t]*)?\)"
)
REFERENCE = re.compile(r"^ {0,3}\[([^\]\r\n]+)\]:[ \t]*(?:<([^>\r\n]+)>|(\S+))", re.M)


def frontmatter_value(text: str, key: str) -> str:
    block = re.match(r"\A---\r?\n(.*?)\r?\n---", text, re.S)
    if not block:
        return ""
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", block.group(1), re.M)
    if not match:
        return ""
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def without_fenced_code(text: str) -> str:
    """Keep line positions while excluding Markdown fenced code from note checks."""
    lines, fence_character, fence_length = [], "", 0
    for line in text.splitlines():
        if fence_character:
            if re.fullmatch(rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*", line):
                fence_character = ""
            lines.append("")
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opening and not (opening.group(1)[0] == "`" and "`" in opening.group(2)):
            fence_character, fence_length = opening.group(1)[0], len(opening.group(1))
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines)


def image_targets(text: str, errors: list[str]) -> list[str]:
    def label(value: str) -> str:
        return " ".join(value.split()).casefold()

    references = {}
    for definition in REFERENCE.finditer(text):
        references.setdefault(label(definition.group(1)), definition.group(2) or definition.group(3))
    targets = []
    for image in IMAGE.finditer(text):
        suffix = text[image.end():]
        if suffix.startswith("("):
            destination = IMAGE_DESTINATION.match(suffix)
            if destination is None:
                errors.append(f"unsupported or malformed image destination: {image.group(0)}")
            else:
                targets.append(destination.group("angle") if destination.group("angle") is not None else destination.group("plain"))
        elif suffix.startswith("["):
            reference = re.match(r"\[([^\]\r\n]*)\]", suffix)
            if reference is None:
                errors.append(f"malformed image reference: {image.group(0)}")
                continue
            reference_label = label(reference.group(1) or image.group(1))
            if reference_label not in references:
                errors.append(f"missing image reference definition: {reference_label}")
            else:
                targets.append(references[reference_label])
        elif label(image.group(1)) in references:
            targets.append(references[label(image.group(1))])
    return targets


def safe_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)).strip().rstrip(" .")


def io_path(path: Path) -> Path:
    path = path.absolute()
    if sys.platform != "win32" or str(path).startswith("\\\\?\\"):
        return path
    raw = str(path)
    return Path("\\\\?\\UNC\\" + raw[2:]) if raw.startswith("\\\\") else Path("\\\\?\\" + raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=Path)
    parser.add_argument("--mode", choices=REQUIRED, required=True)
    parser.add_argument(
        "--allow-legacy-folder",
        action="store_true",
        help="Allow a separately verified existing paper folder whose name predates the current title rule.",
    )
    args = parser.parse_args()
    note, errors = io_path(args.note).resolve(), []
    if not note.is_file():
        errors.append(f"note not found: {note}")
        text = ""
    else:
        text = note.read_text(encoding="utf-8")
        if not (text.lstrip().startswith("---") and "\n---" in text): errors.append("missing YAML frontmatter")
        body = re.sub(r"\A---\r?\n.*?\r?\n---(?:\r?\n|\Z)", "", text, count=1, flags=re.S)
        rendered = without_fenced_code(body)
        if not re.search(r"<h1(?:\s|>)", rendered, re.I) and not re.search(r"^ {0,3}#\s+", rendered, re.M): errors.append("missing document title")
        if not frontmatter_value(text, "research_direction"): errors.append("missing research_direction frontmatter")
        title = frontmatter_value(text, "title")
        key = frontmatter_value(text, "zotero_item_key") or frontmatter_value(text, "zotero_key")
        if not title:
            errors.append("missing exact paper title in frontmatter")
        else:
            expected_folder = safe_title(title)
            folder = note.parent.name
            if (folder != expected_folder and not (key and folder == f"{expected_folder}—{key}")
                    and not args.allow_legacy_folder):
                errors.append(f"paper folder does not match exact title: {folder}")
            prefix = "总结—" if args.mode == "summary" else "精读—"
            if note.name != f"{prefix}{folder}.md":
                errors.append(f"note filename must match paper folder: {note.name}")
        for section in REQUIRED[args.mode]:
            if not re.search(rf"^ {{0,3}}{re.escape(section)}", rendered, re.M): errors.append(f"missing required section: {section}")
        prohibited = "deep-figures" if args.mode == "summary" else "summary-figures"
        for line_no, line in enumerate(text.splitlines(), 1):
            count = line.count("$$")
            if "$$$" in line: errors.append(f"line {line_no}: invalid $$$ delimiter")
            if count not in (0, 2): errors.append(f"line {line_no}: display math must be one $$...$$ pair")
        for raw in image_targets(rendered, errors):
            relative = unquote(re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])", r"\1", raw).split("#", 1)[0])
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", relative): continue
            try: asset = (note.parent / relative).resolve()
            except (OSError, ValueError, RuntimeError): errors.append(f"invalid image asset path: {raw}"); continue
            try: local_asset = asset.relative_to(note.parent.resolve())
            except ValueError: errors.append(f"image escapes note folder: {raw}"); continue
            parts = tuple(part.casefold() for part in local_asset.parts)
            if parts[:2] == ("assets", prohibited): errors.append(f"cross-mode asset link: {raw}")
            if parts[:2] == ("assets", "figures"): errors.append("obsolete shared asset directory: assets/figures/")
            if not asset.is_file(): errors.append(f"missing image asset: {raw}")
    report = {"note": str(args.note.absolute()), "mode": args.mode, "valid": not errors, "errors": errors}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
