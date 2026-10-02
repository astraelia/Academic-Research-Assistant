#!/usr/bin/env python3
"""Persist terminology decisions; semantic screening and source reading belong to the Skill.

Uses only the standard library. Reads the schema's flat YAML fields, preserving
all other frontmatter and text. Unsupported syntax in owned fields fails closed.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import uuid4

SCHEMA = "1.0"
STAGES = ("literature-intake", "literature-summary", "paper-deep-reading", "explicit")
STATUSES = ("待处理", "等待资料", "处理中", "未完成", "失败", "已完成")
COVERAGES = ("unknown", "abstract-metadata-only", "partial-paper", "full-paper")
TERM_LISTS = ("abbr", "aliases", "domain", "category", "literature_sources",
              "external_sources", "related_terms", "related_concepts")
TERM_KEYS = {"type", "schema_version", "term_id", "preferred_en", "preferred_zh",
             "term_status", "term_confidence", "definition_scope", "created", "updated", *TERM_LISTS}
IDENTITY_KEYS = ("paper_title", "doi", "zotero_library_id", "zotero_item_key",
                 "pdf_path", "pdf_sha256", "source_version", "paper_note")
RUN_KEYS = {"type", "schema_version", "paper_id", *IDENTITY_KEYS, "source_coverage",
            "terminology_run_status", "trigger_stage", "completed_from", "completed_at",
            "scan_completed", "source_changed", "candidate_count", "created_count",
            "updated_count", "skipped_count", "pending_count", "new_terms", "updated_terms",
            "last_error", "created", "updated"}


class GateError(ValueError):
    pass


def io_path(path: Path) -> Path:
    raw = str(path.absolute())
    if sys.platform != "win32" or raw.startswith("\\\\?\\"):
        return Path(raw)
    return Path("\\\\?\\UNC\\" + raw[2:]) if raw.startswith("\\\\") else Path("\\\\?\\" + raw)


def stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today() -> str:
    return stamp()[:10]


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def digest(value) -> str:
    data = value if isinstance(value, bytes) else dump(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    path = io_path(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def doi(value: str) -> str:
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "",
                  unquote(value).strip().lower()).rstrip("/ ")


def require_text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a nonempty string")
    if "{{" in value:
        raise GateError(f"{label} contains an unfilled template placeholder")
    return value.strip()


def scalar(value: str):
    value = value.strip()
    if not value or value in ("null", "~"):
        return None
    if value in ("true", "false"):
        return value == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith('"'):
        try:
            return json.loads(value)
        except ValueError as exc:
            raise GateError("Owned YAML fields require JSON-compatible double quotes") from exc
    if value.startswith("'"):
        if not value.endswith("'"):
            raise GateError("Unclosed YAML string")
        return value[1:-1].replace("''", "'")
    if value.startswith("["):
        try:
            result = json.loads(value)
        except ValueError:
            try:
                result = ast.literal_eval(value)
            except (ValueError, SyntaxError) as exc:
                raise GateError("Use quoted scalar list entries in owned YAML fields") from exc
        if not isinstance(result, list):
            raise GateError("Expected a YAML list")
        return result
    if value.startswith(("{", "|", ">", "&", "*", "!")) or " #" in value:
        raise GateError("Unsupported YAML syntax in an owned field; preserve and review it")
    return value


def frontmatter(text: str, keys: set[str]):
    match = re.match(r"\A(?:\ufeff)?---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise GateError("Missing YAML frontmatter")
    block, data, spans = match.group(1), {}, {}
    entries = list(re.finditer(r"^([A-Za-z_][\w-]*):[^\n]*", block, re.M))
    for index, entry in enumerate(entries):
        key = entry.group(1)
        if key in spans:
            raise GateError(f"Duplicate YAML key: {key}")
        end = entries[index + 1].start() if index + 1 < len(entries) else len(block)
        spans[key] = (entry.start(), end)
        if key not in keys:
            continue
        lines = block[entry.start():end].splitlines()
        raw = lines[0].partition(":")[2].strip()
        continuation = [line for line in lines[1:] if line.strip() and not line.lstrip().startswith("#")]
        if continuation:
            if raw or not all(re.match(r"^\s*-\s+", line) for line in continuation):
                raise GateError(f"Unsupported YAML structure for {key}")
            data[key] = [scalar(re.sub(r"^\s*-\s+", "", line)) for line in continuation]
        else:
            data[key] = scalar(raw)
    return match, block, data, spans


def fields(text: str, keys: set[str]) -> dict:
    return frontmatter(text, keys)[2]


def patch_fields(text: str, values: dict) -> str:
    match, block, _, spans = frontmatter(text, set(values))
    edits = []
    missing = []
    for key, value in values.items():
        replacement = f"{key}: {dump(value)}\n"
        if key in spans:
            start, end = spans[key]
            # Preserve comments between fields; replace only the property's lines.
            old = block[start:end].splitlines(keepends=True)
            comments = "".join(line for line in old[1:] if line.lstrip().startswith("#"))
            edits.append((start, end, replacement + comments))
        else:
            missing.append(replacement)
    for start, end, replacement in sorted(edits, reverse=True):
        block = block[:start] + replacement + block[end:]
    block = block.rstrip("\n") + ("\n" + "".join(missing).rstrip("\n") if missing else "")
    return text[:match.start(1)] + block + text[match.end(1):]


def state(text: str, kind: str) -> dict | None:
    matches = list(re.finditer(rf"%% {kind}:state\n(.*?)\n%%", text, re.S))
    if len(matches) > 1:
        raise GateError("Duplicate machine checkpoints")
    if not matches:
        return None
    try:
        result = json.loads(matches[0].group(1))
    except ValueError as exc:
        raise GateError("Malformed machine checkpoint") from exc
    if not isinstance(result, dict):
        raise GateError("Machine checkpoint must be an object")
    return result


def state_block(data: dict, kind: str) -> str:
    return f"%% {kind}:state\n{dump(data).replace('%', chr(92) + 'u0025')}\n%%"


def replace_region(text: str, kind: str, content: str, *, append_missing=False) -> str:
    start, end = f"%% {kind}:managed:start %%", f"%% {kind}:managed:end %%"
    if text.count(start) != 1 or text.count(end) != 1:
        if append_missing and start not in text and end not in text:
            return text.rstrip() + f"\n\n{start}\n\n{content}\n\n{end}\n"
        raise GateError("Missing or duplicate managed-region markers; preserve and review the note")
    left, right = text.index(start) + len(start), text.index(end)
    if right < left:
        raise GateError("Reversed managed-region markers")
    return text[:left] + f"\n\n{content}\n\n" + text[right:]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def atomic_write(path: Path, text: str, expected: bytes | None):
    current = path.read_bytes() if path.exists() else None
    if current != expected:
        raise GateError(f"Concurrent edit detected: {path}")
    temp = path.with_name(path.name + f".{uuid4().hex}.tmp")
    try:
        with temp.open("xb") as stream:
            stream.write(text.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        if (path.read_bytes() if path.exists() else None) != expected:
            raise GateError(f"Concurrent edit detected: {path}")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def object_file(path: Path) -> dict:
    try:
        data = json.loads(read(path))
    except (ValueError, UnicodeError) as exc:
        raise GateError(f"Invalid JSON object: {path}") from exc
    if not isinstance(data, dict):
        raise GateError(f"Expected JSON object: {path}")
    return data


class Store:
    def __init__(self, vault: Path, library: str | None = None, terms_dir=None, runs_dir=None):
        self.vault = io_path(vault).resolve()
        if not (self.vault / ".obsidian").is_dir():
            raise GateError("Target must be a confirmed Obsidian vault")
        config = self.vault / ".obsidian" / "templates.json"
        self.template_root = None
        if config.is_file():
            self.template_root = self.inside(object_file(config).get("folder", "99_模板"))
        dashboards = list(self.notes({"terminology_dashboard"}))
        if library:
            self.library = self.inside(library)
            if not any(path.parent == self.library for path, _, _ in dashboards):
                raise GateError("Library must contain an existing terminology_dashboard")
        elif len(dashboards) == 1:
            self.library = dashboards[0][0].parent
        else:
            raise GateError("Resolve one existing terminology dashboard before writing")
        self.terms_dir = self.destination(terms_dir, "术语卡", "terminology")
        self.runs_dir = self.destination(runs_dir, "处理记录", "terminology_run")
        self.lock = self.library / ".terminology-lock"

    def inside(self, relative) -> Path:
        candidate = Path(relative)
        target = io_path(candidate if candidate.is_absolute() else self.vault / candidate).resolve()
        if not target.is_relative_to(self.vault):
            raise GateError("Target escapes the confirmed vault")
        return target

    def notes(self, types: set[str]):
        for base, dirs, files in os.walk(self.vault, followlinks=False):
            dirs[:] = [name for name in dirs if not name.startswith(".") and name != "assets"
                       and not (Path(base) / name).is_symlink()
                       and (Path(base) / name).resolve() != self.template_root]
            for name in files:
                if not name.endswith(".md"):
                    continue
                path = Path(base) / name
                if path.is_symlink() or not path.resolve().is_relative_to(self.vault):
                    continue
                text = read(path)
                if not re.match(r"\A---\n", text):
                    continue
                kind = fields(text, {"type"}).get("type")
                if kind in types:
                    yield path, text, fields(text, RUN_KEYS if kind == "terminology_run" else TERM_KEYS)

    def destination(self, override, default: str, kind: str) -> Path:
        if override:
            target = self.inside(override)
        elif (self.library / default).is_dir():
            target = self.library / default
        else:
            parents = {path.parent for path, _, _ in self.notes({kind})}
            if len(parents) != 1:
                raise GateError(f"Resolve the moved or empty destination for {kind}")
            target = parents.pop()
        target = self.inside(target)
        if not target.is_dir():
            raise GateError(f"Destination must already exist: {target}")
        return target

    def template(self, kind: str) -> str:
        if not self.template_root or not self.template_root.is_dir():
            raise GateError("Resolve the active template folder in .obsidian/templates.json")
        matches = []
        for path in self.template_root.rglob("*.md"):
            text = read(path)
            if text.startswith("---\n") and fields(text, {"type"}).get("type") == kind:
                matches.append(text)
        if len(matches) != 1:
            raise GateError(f"Resolve one active {kind} template")
        return matches[0]

    def link(self, path: Path) -> str:
        return f"[[{path.relative_to(self.vault).with_suffix('').as_posix()}]]"

    def check_link(self, value: str):
        require_text(value, "wikilink")
        match = re.fullmatch(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", value)
        if not match:
            raise GateError(f"Expected a resolved Vault wikilink: {value}")
        target = self.inside(match.group(1) + ".md")
        if not target.is_file():
            raise GateError(f"Missing link target: {value}")

    def acquire(self) -> str:
        try:
            self.lock.mkdir()
        except FileExistsError as exc:
            raise GateError("Terminology writer is busy; inspect its lease before recovery") from exc
        token = uuid4().hex
        try:
            atomic_write(self.lock / "lease.json", dump({"token": token, "started_at": stamp()}), None)
        except BaseException:
            self.lock.rmdir()
            raise
        return token

    def lease(self, token: str) -> dict:
        data = object_file(self.lock / "lease.json")
        if data.get("token") != token:
            raise GateError("Lease token does not match the active writer")
        return data

    def release(self, token: str):
        self.lease(token)
        (self.lock / "lease.json").unlink()
        self.lock.rmdir()


def identity(data: dict, store: Store) -> dict:
    result = {key: data.get(key) or "" for key in IDENTITY_KEYS}
    result["paper_title"] = require_text(result["paper_title"], "paper_title")
    for key, value in result.items():
        if not isinstance(value, str):
            raise GateError(f"{key} must be a string")
    result["doi"] = doi(result["doi"])
    if result["pdf_path"]:
        source = Path(result["pdf_path"])
        if not source.is_absolute():
            raise GateError("pdf_path must be absolute")
        source = io_path(source)
        if source.is_file():
            actual = file_hash(source)
            if result["pdf_sha256"] and actual != result["pdf_sha256"].lower():
                raise GateError("Supplied PDF hash does not match the selected source")
            result["pdf_sha256"] = actual
    if result["pdf_sha256"] and not re.fullmatch(r"[0-9a-f]{64}", result["pdf_sha256"]):
        raise GateError("pdf_sha256 must be a SHA-256 hex digest")
    if result["paper_note"]:
        store.check_link(result["paper_note"])
    if data.get("paper_id"):
        result["paper_id"] = require_text(data["paper_id"], "paper_id")
    result["identity_confirmed"] = data.get("identity_confirmed") is True
    return result


def identities(meta: dict, text: str) -> list[dict]:
    checkpoint = state(text, "terminology-run") or {}
    return [meta, *checkpoint.get("identity_aliases", [])]


def match_run(store: Store, incoming: dict):
    strong, weak, ids = [], [], set()
    for path, text, meta in store.notes({"terminology_run"}):
        pid = require_text(meta.get("paper_id"), "existing paper_id")
        if pid in ids:
            raise GateError(f"Duplicate stable paper_id: {pid}")
        ids.add(pid)
        aliases = identities(meta, text)
        hit = incoming.get("paper_id") == pid or any(
            (incoming["doi"] and incoming["doi"] == doi(item.get("doi") or ""))
            or (incoming["zotero_library_id"] and incoming["zotero_item_key"]
                and incoming["zotero_library_id"] == item.get("zotero_library_id")
                and incoming["zotero_item_key"] == item.get("zotero_item_key"))
            or (incoming["pdf_sha256"] and incoming["pdf_sha256"] == item.get("pdf_sha256"))
            or (incoming["paper_note"] and incoming["paper_note"] == item.get("paper_note"))
            for item in aliases)
        if hit:
            if incoming.get("paper_id") and incoming["paper_id"] != pid:
                raise GateError("Supplied stable paper_id conflicts with the matched identity")
            known_dois = {doi(item.get("doi") or "") for item in aliases} - {""}
            if incoming["doi"] and known_dois and incoming["doi"] not in known_dois:
                raise GateError(f"Conflicting DOI for {pid}")
            strong.append((path, text, meta))
        elif (norm(incoming["paper_title"]) == norm(meta.get("paper_title") or "")
              or (incoming["zotero_item_key"] and any(
                  incoming["zotero_item_key"] == item.get("zotero_item_key")
                  and (not incoming["zotero_library_id"] or not item.get("zotero_library_id")
                       or incoming["zotero_library_id"] == item.get("zotero_library_id")) for item in aliases))):
            weak.append(str(path))
    if len(strong) > 1:
        raise GateError("Multiple records match this paper; resolve identity before writing")
    if not strong and weak:
        raise GateError("Possible existing paper records require identity review: " + dump(weak))
    if incoming.get("paper_id") and not strong:
        raise GateError("Supplied paper_id was not found; do not silently generate a replacement")
    return strong[0] if strong else None


def validate_run(meta: dict, data: dict | None):
    if meta.get("schema_version") != SCHEMA or meta.get("terminology_run_status") not in STATUSES:
        raise GateError("Unsupported processing record schema or status")
    if meta.get("source_coverage") not in COVERAGES:
        raise GateError("Invalid source coverage")
    for key in ("scan_completed", "source_changed"):
        if type(meta.get(key)) is not bool:
            raise GateError(f"{key} must be a boolean")
    for key in ("candidate_count", "created_count", "updated_count", "skipped_count", "pending_count"):
        if type(meta.get(key)) is not int or meta[key] < 0:
            raise GateError(f"{key} must be a nonnegative integer")
    if data is not None:
        if (not isinstance(data.get("candidates"), dict) or not isinstance(data.get("history"), list)
                or not isinstance(data.get("identity_aliases"), list) or type(data.get("scan_completed")) is not bool
                or type(data.get("revision")) is not int or not isinstance(data.get("blocked"), str)):
            raise GateError("Invalid processing checkpoint structure")
        if any(not isinstance(item, dict) or item.get("decision") not in ("create", "update", "skip", "pending")
               for item in data["candidates"].values()):
            raise GateError("Invalid candidate decision ledger")
    if meta["terminology_run_status"] == "已完成":
        if not meta["scan_completed"] or meta["source_coverage"] != "full-paper" or not meta.get("completed_at"):
            raise GateError("Invalid completion marker; cannot skip this paper")
        if data is None or not data.get("scan_completed") or data.get("blocked"):
            raise GateError("Completed record lacks a valid checkpoint; review before reuse")
        expected = counts(data)
        if any(meta.get(key) != value for key, value in expected.items()):
            raise GateError("Completion counts do not match the candidate ledger")


def inspect(store: Store, incoming: dict) -> dict:
    found = match_run(store, incoming)
    if not found:
        return {"action": "first-run", "paper_id": None, "record": None}
    path, text, meta = found
    data = state(text, "terminology-run")
    validate_run(meta, data)
    if meta["terminology_run_status"] == "已完成":
        validate_outputs(store, meta, data)
    changed = bool(meta.get("pdf_sha256") and incoming["pdf_sha256"]
                   and meta["pdf_sha256"] != incoming["pdf_sha256"])
    action = "skip-completed" if meta["terminology_run_status"] == "已完成" else "resume"
    if changed and action == "skip-completed":
        action = "source-changed"
    return {"action": action, "paper_id": meta["paper_id"], "record": str(path),
            "source_changed": changed, "status": meta["terminology_run_status"],
            "candidates": (data or {}).get("candidates", {})}


def row(*values) -> str:
    return "| " + " | ".join(str(value or "").replace("|", "\\|").replace("\n", "<br>")
                               for value in values) + " |"


def counts(data: dict) -> dict:
    candidates = list(data["candidates"].values())
    return {"candidate_count": len(candidates), **{
        key: sum(item["decision"] == decision for item in candidates)
        for key, decision in (("created_count", "create"), ("updated_count", "update"),
                              ("skipped_count", "skip"), ("pending_count", "pending"))}}


def run_body(data: dict, meta: dict) -> str:
    lines = ["## 论文身份与资料覆盖", "", f"文献入口：{meta.get('paper_note') or '待补'}",
             f"术语筛查范围：{meta.get('source_coverage')}；{data.get('coverage_evidence') or '尚未完成'}", "",
             "## 候选与处理决定", "", row("候选 ID", "原文与定位", "决定", "价值与证据", "结果"),
             row("---", "---", "---", "---", "---")]
    for key, item in data["candidates"].items():
        lines.append(row(key, item["expression"] + "；" + item["locator"], item["decision"],
                         item["reason"], item.get("term_link")))
    lines += ["", "## 待审核候选", "", row("候选", "问题与依据", "状态"), row("---", "---", "---")]
    lines += [row(item["expression"], item["reason"], "待审核")
              for item in data["candidates"].values() if item["decision"] == "pending"]
    lines += ["", "## 执行、恢复与补充历史", "", row("时间", "阶段／操作", "资料版本与说明"),
              row("---", "---", "---")]
    lines += [row(item["at"], item["stage"], item["detail"]) for item in data["history"]]
    lines += ["", "## 完成核验", "", "只有全文筛查、候选决定和实际写入校验全部通过，才提交完成状态。",
              "", state_block(data, "terminology-run")]
    return "\n".join(lines)


def save_run(path: Path, text: str, meta: dict, data: dict):
    values = {**meta, **counts(data), "updated": today(),
              "new_terms": sorted({item["term_link"] for item in data["candidates"].values()
                                   if item["decision"] == "create"}),
              "updated_terms": sorted({item["term_link"] for item in data["candidates"].values()
                                       if item["decision"] == "update"})}
    expected = path.read_bytes() if path.exists() else None
    if expected is not None and read(path) != text:
        raise GateError(f"Concurrent edit detected: {path}")
    rendered = replace_region(patch_fields(text, values), "terminology-run", run_body(data, values),
                              append_missing=True)
    atomic_write(path, rendered, expected)


def begin(store: Store, incoming: dict, stage: str, coverage: str, supplement=False) -> dict:
    token = store.acquire()
    try:
        found = match_run(store, incoming)
        if found:
            path, text, meta = found
            data = state(text, "terminology-run")
            validate_run(meta, data)
            if meta["terminology_run_status"] == "已完成":
                validate_outputs(store, meta, data)
            if data is None:
                raise GateError("Existing record needs checkpoint adoption; preserve its manual history")
        else:
            if not (incoming["doi"] or incoming["pdf_sha256"] or incoming["paper_note"]
                    or (incoming["zotero_library_id"] and incoming["zotero_item_key"])
                    or incoming["identity_confirmed"]):
                raise GateError("Confirm bibliographic identity before creating a title-only record")
            meta = fields(store.template("terminology_run"), RUN_KEYS)
            meta.update(type="terminology_run", schema_version=SCHEMA,
                        paper_id="paper-" + uuid4().hex, created=today(), completed_at="", completed_from="")
            text = store.template("terminology_run")
            # Only new records: replace template prose with the active managed body.
            text = text[:frontmatter(text, RUN_KEYS)[0].end()] + "\n# 论文术语处理记录\n\n## 个人备注\n"
            path = store.runs_dir / (meta["paper_id"] + ".md")
            data = {"candidates": {}, "history": [], "identity_aliases": [], "scan_completed": False,
                    "blocked": "", "revision": 0, "coverage_evidence": ""}
        alias = {key: incoming[key] for key in IDENTITY_KEYS}
        if alias not in data["identity_aliases"]:
            data["identity_aliases"].append(alias)
        changed = bool(meta.get("pdf_sha256") and incoming["pdf_sha256"]
                       and meta["pdf_sha256"] != incoming["pdf_sha256"])
        # Enrich missing identity without replacing the stable ID or the processed source version.
        for key in IDENTITY_KEYS:
            if incoming[key] and (not meta.get(key) or key in ("paper_title", "paper_note")):
                meta[key] = incoming[key]
        if meta.get("terminology_run_status") == "已完成" and not supplement:
            meta["source_changed"] = bool(meta["source_changed"] or changed)
            if changed and not any(item["detail"] == "PDF changed: " + incoming["pdf_sha256"]
                                   for item in data["history"]):
                data["history"].append({"at": stamp(), "stage": stage,
                                        "detail": "PDF changed: " + incoming["pdf_sha256"]})
            save_run(path, text, meta, data)
            store.release(token)
            return {"action": "source-changed" if changed else "skip-completed",
                    "paper_id": meta["paper_id"], "record": str(path)}
        if changed or supplement:
            data["history"].append({"at": stamp(), "stage": "explicit supplement" if supplement else stage,
                                    "detail": "Prior revision retained: " + dump({
                                        "completed_at": meta.get("completed_at"),
                                        "pdf_sha256": meta.get("pdf_sha256"), "candidates": data["candidates"]})})
            data["revision"] += 1
            data["candidates"] = {}
            data["scan_completed"], data["coverage_evidence"] = False, ""
        meta.update({key: incoming[key] or meta.get(key) or "" for key in IDENTITY_KEYS})
        full_source = bool(meta.get("pdf_path") and io_path(Path(meta["pdf_path"])).is_file() and meta.get("pdf_sha256"))
        if coverage == "full-paper" and not full_source:
            coverage = "unknown"
        meta.update(source_coverage=coverage, terminology_run_status="处理中" if full_source else "等待资料",
                    trigger_stage=stage, scan_completed=False, source_changed=False, last_error="")
        data["history"].append({"at": stamp(), "stage": stage, "detail": "begin/resume"})
        save_run(path, text, meta, data)
        lease_path = store.lock / "lease.json"
        atomic_write(lease_path, dump({"token": token, "started_at": stamp(),
                                     "record": str(path.relative_to(store.vault))}), lease_path.read_bytes())
        if not full_source:
            store.release(token)
            return {"action": "waiting-material", "paper_id": meta["paper_id"], "record": str(path)}
        return {"action": "process", "token": token, "paper_id": meta["paper_id"], "record": str(path),
                "candidates": data["candidates"]}
    except BaseException:
        if store.lock.exists():
            store.release(token)
        raise


def open_run(store: Store, token: str):
    lease = store.lease(token)
    if not lease.get("record"):
        raise GateError("Lease has no processing record; inspect interrupted begin before recovery")
    path = store.inside(lease["record"])
    text = read(path)
    meta = fields(text, RUN_KEYS)
    data = state(text, "terminology-run")
    if data is None:
        raise GateError("Missing processing checkpoint")
    return path, text, meta, data


def term_index(store: Store):
    result, ids = [], set()
    for path, text, meta in store.notes({"terminology"}):
        tid = require_text(meta.get("term_id"), "existing term_id")
        if tid in ids:
            raise GateError(f"Duplicate term_id: {tid}")
        ids.add(tid)
        result.append((path, text, meta))
    return result


def names(meta: dict) -> set[str]:
    return {norm(value) for value in [meta.get("preferred_en"), meta.get("preferred_zh"),
                                    *(meta.get("aliases") or []), *(meta.get("abbr") or [])] if value}


def external_evidence(items) -> list[dict]:
    if not isinstance(items, list):
        raise GateError("external_evidence must be a list of selected source entries")
    for item in items:
        if not isinstance(item, dict):
            raise GateError("External evidence must be an object")
        for key in ("url", "source", "entry", "version", "checked_at", "role"):
            require_text(item.get(key), "external_evidence." + key)
        if item.get("read_verified") is not True or urlparse(item["url"]).scheme not in ("http", "https"):
            raise GateError("External evidence needs a read entry and a precise HTTP(S) URL")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", item["checked_at"]):
            raise GateError("External source check date must use YYYY-MM-DD")
    return items


TERM_SECTIONS = {
    "definition": ("定义与适用边界",), "expressions": ("中英文与学术表达",),
    "literature": ("文献证据",), "external": ("外部核验依据",),
    "related": ("相关术语与概念",), "analysis": ("分析与待复核问题", "AI 分析与待复核问题"),
    "maintenance": ("维护记录",),
}
EXPRESSION_LABELS = ("首选英文", "首选中文", "缩写与首次出现的写法",
                     "已确认的变体及其适用范围", "有依据的常用表达")


def managed_content(text: str) -> str:
    # Reuse the marker checks without changing any files.
    replace_region(text, "terminology", "")
    region = text.split("%% terminology:managed:start %%", 1)[1].split("%% terminology:managed:end %%", 1)[0]
    return re.sub(r"%% terminology:state\n.*?\n%%", "", region, flags=re.S).strip("\n")


def visible_markdown(text: str) -> str:
    def blank(match):
        return re.sub(r"[^\n]", " ", match.group())
    text = re.sub(r"%%.*?%%|<!--.*?-->", blank, text, flags=re.S)
    result, fence = [], None
    for line in text.splitlines(keepends=True):
        token = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\n"))
        if fence:
            result.append(re.sub(r"[^\n]", " ", line))
            if token and token[1][0] == fence[0] and len(token[1]) >= len(fence) and not token[2].strip():
                fence = None
        elif token:
            fence = token[1]
            result.append(re.sub(r"[^\n]", " ", line))
        else:
            result.append(line)
    return "".join(result)


def body_sections(region: str):
    headings = list(re.finditer(r"^##[ \t]+([^\n]+?)[ \t]*$", visible_markdown(region), re.M))
    sections = {}
    for index, heading in enumerate(headings):
        title = heading[1]
        if title in sections:
            raise GateError(f"Duplicate terminology body section: {title}")
        end = headings[index + 1].start() if index + 1 < len(headings) else len(region)
        sections[title] = region[heading.end():end].strip("\n")
    return region[:headings[0].start()].strip("\n") if headings else region, sections


def template_layout(store: Store):
    leading, sections = body_sections(managed_content(store.template("terminology")))
    roles = {}
    for role, titles in TERM_SECTIONS.items():
        found = [title for title in titles if title in sections]
        if len(found) != 1:
            raise GateError(f"Active terminology template must have one {role} section; preserve and review it")
        roles[role] = found[0]
    expression_values(sections[roles["expressions"]], allow_empty=True)
    for role, width in (("literature", 4), ("external", 5), ("maintenance", 3)):
        table_header(sections[roles[role]], width)
    return leading, sections, roles


def expression_values(body: str, *, allow_empty=False) -> dict:
    result = {}
    for label in EXPRESSION_LABELS:
        matches = list(re.finditer(r"^- " + re.escape(label) + r"：[ \t]*([^\n]*)$", visible_markdown(body), re.M))
        if len(matches) != 1 or (not allow_empty and not matches[0][1].strip()):
            raise GateError(f"Missing, duplicate or empty academic-expression item: {label}")
        result[label] = matches[0][1].strip()
    return result


def table_header(body: str, width: int) -> str:
    lines = [line for line in visible_markdown(body).splitlines() if line.startswith("|")]
    if len(lines) < 2 or any(len(re.split(r"(?<!\\)\|", line)[1:-1]) != width for line in lines):
        raise GateError(f"Terminology template/output needs a {width}-column evidence/maintenance table")
    if not all(re.fullmatch(r"\s*:?-+:?\s*", cell) for cell in re.split(r"(?<!\\)\|", lines[1])[1:-1]):
        raise GateError("Missing Markdown table separator")
    return "\n".join(lines[:2])


def writing_details(term: dict, candidate: dict, refs: list[dict]) -> dict:
    writing = term.get("writing", {})
    if not isinstance(writing, dict) or set(writing) - {"first_use", "variants", "academic_expressions"}:
        raise GateError("term.writing accepts first_use, variants and academic_expressions")
    allowed = [candidate["locator"], *(item["url"] for item in refs)]
    for key in ("first_use", "variants", "academic_expressions"):
        items = writing.get(key, [])
        if not isinstance(items, list):
            raise GateError(f"term.writing.{key} must be a list")
        for item in items:
            if not isinstance(item, dict):
                raise GateError("Academic-expression evidence must be an object")
            require_text(item.get("text"), "writing.text")
            basis = require_text(item.get("basis"), "writing.basis")
            if any("\n" in value or "\r" in value for value in (item["text"], basis, item.get("scope", ""))):
                raise GateError("Academic-expression fields must be single-line text")
            if not any(source and source in basis for source in allowed):
                raise GateError("Academic expression basis must identify the inspected candidate locator or a read external URL")
            if key == "variants":
                require_text(item.get("scope"), "writing.variant.scope")
    return writing


def render_expressions(body: str, meta: dict, writing: dict, *, new=False) -> str:
    old = expression_values(body, allow_empty=new)
    abbr = "、".join(meta["abbr"]) or "无已确认缩写"
    variants = "、".join(meta["aliases"])
    values = {
        "首选英文": meta.get("preferred_en") or "待补：尚无确认的英文名称",
        "首选中文": meta.get("preferred_zh") or "待补：尚无确认的中文译名",
        "缩写与首次出现的写法": abbr + "；【写作建议】首次出现写完整名称，并注明本次采用的缩写；此建议不冒充原文写法。",
        "已确认的变体及其适用范围": (variants + "；逐项适用范围待补") if variants else "暂无已确认的变体",
        "有依据的常用表达": "待补：尚无经核验的常用学术表达",
    }
    for key, label in (("first_use", EXPRESSION_LABELS[2]), ("variants", EXPRESSION_LABELS[3]),
                       ("academic_expressions", EXPRESSION_LABELS[4])):
        items = writing.get(key, [])
        additions = [item["text"] + ("（适用范围：" + item["scope"] + "）" if key == "variants" else "")
                     + "（依据：" + item["basis"] + "）" for item in items]
        if not new:
            values[label] = old[label]
        if additions:
            if new or values[label].startswith("待补："):
                values[label] = "；".join(additions)
            else:
                values[label] += "".join("；" + value for value in additions if value not in values[label])
    for value in meta["abbr"]:
        if value not in values[EXPRESSION_LABELS[2]]:
            values[EXPRESSION_LABELS[2]] += "；缩写：" + value
    for value in meta["aliases"]:
        if value not in values[EXPRESSION_LABELS[3]]:
            values[EXPRESSION_LABELS[3]] += "；变体：" + value + "（适用范围待补）"
    for label, value in values.items():
        pattern = r"^- " + re.escape(label) + r"：[^\n]*$"
        body = re.sub(pattern, lambda _: "- " + label + "：" + value, body, count=1, flags=re.M)
    return body


def render_term_body(store: Store, meta: dict, term: dict, data: dict, candidate: dict,
                     run: dict | None, refs: list[dict], *, existing: str | None = None,
                     add_evidence=True, definition_body=None) -> str:
    leading, template, roles = template_layout(store)
    new = existing is None
    sections = dict(template) if new else body_sections(managed_content(existing))[1]
    if not new:
        leading = body_sections(managed_content(existing))[0]
    writing = writing_details(term, candidate, refs)
    if new:
        sections[roles["definition"]] = definition_body if definition_body is not None else (
            term["definition"] + "\n\n适用范围：" + term["definition_scope"])
        for role, width in (("literature", 4), ("external", 5), ("maintenance", 3)):
            sections[roles[role]] = table_header(template[roles[role]], width)
        analysis = term.get("analysis") or "暂无新增分析；未核验的学术表达在对应栏目明确待补。"
        sections[roles["analysis"]] = analysis if analysis.startswith(("【分析】", "【推断】")) else "【分析】" + analysis
        sections[roles["related"]] = "暂无已核验的相关术语或概念链接。"
    elif term.get("analysis") and term["analysis"] not in sections[roles["analysis"]]:
        sections[roles["analysis"]] += "\n\n【分析】" + term["analysis"] + "（定位：" + candidate["locator"] + "）"
    sections[roles["expressions"]] = render_expressions(sections[roles["expressions"]], meta, writing, new=new)
    if meta["related_terms"] or meta["related_concepts"]:
        related = sections[roles["related"]].replace("暂无已核验的相关术语或概念链接。", "").strip()
        for key, label in (("related_terms", "相关术语"), ("related_concepts", "相关概念")):
            for link in meta[key]:
                if link not in related:
                    related += "\n\n" + "- " + label + "：" + link
        sections[roles["related"]] = related.strip()
    source = (run or {}).get("paper_id", "显式术语核验") + " " + (run or {}).get("paper_note", "")
    if add_evidence:
        sections[roles["literature"]] += "\n" + row(source.strip(), candidate["locator"],
                                                    require_text(candidate.get("context"), "accepted candidate context"), candidate["reason"])
        for item in refs:
            entry = row(item["source"], item["entry"] + " " + item["url"], item["version"], item["checked_at"], item["role"])
            if entry not in sections[roles["external"]]:
                sections[roles["external"]] += "\n" + entry
    if new and not refs:
        sections[roles["external"]] += "\n\n本次未使用外部核验条目；定义与用法的依据见文献证据。"
    sections[roles["maintenance"]] += "\n" + row(today(), "创建术语卡" if new else "增量补充来源、表达或关系",
                                                 source.strip() + "；" + candidate["locator"])
    content = "\n\n".join(filter(None, [leading, *("## " + title + "\n\n" + body for title, body in sections.items())]))
    return content + "\n\n" + state_block(data, "terminology")


def validate_term_body(store: Store, text: str, meta: dict):
    _, expected, roles = template_layout(store)
    _, sections = body_sections(managed_content(text))
    if [title for title in sections if title in expected] != list(expected):
        raise GateError("Terminology body does not preserve the active template sections and order; explicit repair required")
    for role, title in roles.items():
        body = visible_markdown(sections[title]).strip()
        if not body or "{{" in body or body == visible_markdown(expected[title]).strip():
            raise GateError(f"Empty or unfilled terminology body section: {title}")
    values = expression_values(sections[roles["expressions"]])
    for key, label in (("preferred_en", EXPRESSION_LABELS[0]), ("preferred_zh", EXPRESSION_LABELS[1])):
        if meta.get(key) and meta[key] not in values[label]:
            raise GateError("Preferred name missing from academic-expression body")
    for key, label in (("abbr", EXPRESSION_LABELS[2]), ("aliases", EXPRESSION_LABELS[3])):
        if any(value not in values[label] for value in meta[key]):
            raise GateError("Abbreviation/variant missing from academic-expression body")
    for key, role in (("related_terms", "related"), ("related_concepts", "related"),
                      ("literature_sources", "literature"), ("external_sources", "external")):
        visible = visible_markdown(sections[roles[role]])
        if any(value not in visible and (role == "related" or value.replace("|", "\\|") not in visible) for value in meta[key]):
            raise GateError(f"{key} missing from its visible template section")
    for role, width in (("literature", 4), ("external", 5), ("maintenance", 3)):
        table_header(sections[roles[role]], width)
    if len([line for line in visible_markdown(sections[roles["maintenance"]]).splitlines() if line.startswith("|")]) < 3:
        raise GateError("Visible maintenance record is required")


def validate_term(store: Store, path: Path, *, text: str | None = None):
    text = read(path) if text is None else text
    meta = fields(text, TERM_KEYS)
    require_text(meta.get("term_id"), "term_id")
    if meta.get("schema_version") != SCHEMA or meta.get("type") != "terminology":
        raise GateError("Unsupported terminology schema")
    if not (meta.get("preferred_en") or meta.get("preferred_zh")):
        raise GateError("A preferred term name is required")
    if meta.get("term_status") not in ("已核验", "待复核", "弃用"):
        raise GateError("Invalid term_status")
    if meta.get("term_confidence") not in ("high", "medium", "low"):
        raise GateError("Invalid term_confidence")
    for key in TERM_LISTS:
        if not isinstance(meta.get(key), list) or any(not isinstance(v, str) for v in meta[key]):
            raise GateError(f"{key} must be a list of strings")
    for key in ("literature_sources", "related_terms", "related_concepts"):
        for value in meta[key]:
            store.check_link(value)
    validate_term_body(store, text, meta)
    return meta


def apply_term(store: Store, candidate: dict, event: str, run: dict | None):
    payload_hash = digest(candidate)
    cards = term_index(store)
    for path, text, meta in cards:
        prior = (state(text, "terminology") or {}).get("events", {}).get(event)
        if prior:
            if prior["payload_hash"] != payload_hash:
                raise GateError("Interrupted event changed; preserve the applied decision and review it")
            validate_term(store, path)
            return {"term_link": store.link(path), "term_id": meta["term_id"], "decision": prior["decision"]}
    decision = candidate["decision"]
    term = candidate.get("term")
    if not isinstance(term, dict):
        raise GateError("Accepted candidate requires a term object")
    require_text(term.get("definition"), "term.definition")
    require_text(term.get("definition_scope"), "term.definition_scope")
    refs = external_evidence(candidate.get("external_evidence", []))
    if run is None and not refs:
        raise GateError("A standalone term needs a read external source; paper workflows supply PDF evidence")
    for key in ("abbr", "aliases", "domain", "category", "related_terms", "related_concepts"):
        if key not in term:
            term[key] = []
        if not isinstance(term[key], list) or any(not isinstance(v, str) for v in term[key]):
            raise GateError(f"term.{key} must be a list of strings")
    if decision == "update":
        if candidate.get("match_confirmed") is not True or candidate.get("definition_compatible") is not True:
            raise GateError("Term update requires confirmed identity and definition compatibility")
        matches = [item for item in cards if item[2]["term_id"] == candidate.get("matched_term_id")]
        if len(matches) != 1:
            raise GateError("Resolve one matched_term_id before updating")
        path, text, meta = matches[0]
        expected = path.read_bytes()
        if read(path) != text:
            raise GateError(f"Concurrent edit detected: {path}")
        if (text.count("%% terminology:managed:start %%") != 1
                or text.count("%% terminology:managed:end %%") != 1):
            raise GateError("Existing term needs managed-region adoption; preserve its manual text")
        validate_term(store, path)
        if meta["term_status"] == "弃用":
            raise GateError("Do not silently reuse a deprecated term")
        data = state(text, "terminology") or {"events": {}, "evidence": []}
    else:
        title = term.get("preferred_en") or term.get("preferred_zh")
        require_text(title, "preferred term name")
        clashes = [item for item in cards if names(item[2]) & names(term)]
        if clashes and not (candidate.get("distinct_sense") is True
                            and candidate.get("distinction_reason") and term["domain"]):
            raise GateError("Term name or abbreviation exists; confirm the entity instead of duplicating it")
        base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title).strip().rstrip(" .")[:170].rstrip(" .")
        if not base or re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", base, re.I):
            base = "term-" + uuid4().hex[:8]
        if clashes:
            base += "—" + re.sub(r'[<>:"/\\|?*]', "", term["domain"][0])[:35]
        path = store.terms_dir / (base + ".md")
        if path.exists():
            path = store.terms_dir / (base + "—" + uuid4().hex[:8] + ".md")
        expected = None
        text = store.template("terminology")
        body_start = frontmatter(text, TERM_KEYS)[0].end()
        text = text[:body_start] + text[body_start:].replace("# 学术术语", "# " + title, 1)
        text = re.sub(r"^> \[!todo\].*?(?=^%% terminology:managed:start %%)", "", text, flags=re.S | re.M)
        meta = fields(text, TERM_KEYS)
        meta.update(type="terminology", schema_version=SCHEMA, term_id="term-" + uuid4().hex,
                    preferred_en=term.get("preferred_en") or "", preferred_zh=term.get("preferred_zh") or "",
                    definition_scope=term["definition_scope"], term_status=term.get("term_status", "待复核"),
                    term_confidence=term.get("term_confidence", "low"), created=today())
        data = {"events": {}, "evidence": []}
    for key in ("abbr", "aliases", "domain", "category", "related_terms", "related_concepts"):
        # Preserve preferred names, original definition, status and all personal prose on update.
        meta[key] = sorted(set(meta.get(key) or []) | set(term[key]))
    if decision == "update":
        meta["aliases"] = sorted(set(meta["aliases"]) | {
            name for name in (term.get("preferred_en"), term.get("preferred_zh"))
            if name and name not in (meta.get("preferred_en"), meta.get("preferred_zh"))})
    for key in ("related_terms", "related_concepts"):
        for link in meta[key]:
            store.check_link(link)
    if run and run.get("paper_note"):
        meta["literature_sources"] = sorted(set(meta.get("literature_sources") or []) | {run["paper_note"]})
    meta["external_sources"] = sorted(set(meta.get("external_sources") or []) | {item["url"] for item in refs})
    meta["updated"] = today()
    evidence_key = digest({"paper_id": (run or {}).get("paper_id"), "locator": candidate["locator"],
                           "source_hash": (run or {}).get("pdf_sha256"), "external": sorted(item["url"] for item in refs)})
    add_evidence = evidence_key not in data["evidence"]
    if add_evidence:
        data["evidence"].append(evidence_key)
    data["events"][event] = {"payload_hash": payload_hash, "decision": decision}
    body = render_term_body(store, meta, term, data, candidate, run, refs,
                            existing=text if decision == "update" else None, add_evidence=add_evidence)
    text = replace_region(patch_fields(text, meta), "terminology", body)
    # Validate rendered fields and links before publishing the card.
    preview = fields(text, TERM_KEYS)
    if preview["term_status"] not in ("已核验", "待复核", "弃用") or preview["term_confidence"] not in ("high", "medium", "low"):
        raise GateError("Invalid terminology status or confidence")
    if decision == "create" and preview["term_status"] == "已核验" and candidate.get("verification_confirmed") is not True:
        raise GateError("Verified terms require explicit source-grounded verification confirmation")
    validate_term(store, path, text=text)
    atomic_write(path, text, expected)
    validate_term(store, path)
    return {"term_link": store.link(path), "term_id": meta["term_id"], "decision": decision}


def checkpoint(store: Store, token: str, plan: dict) -> dict:
    path, text, meta, data = open_run(store, token)
    if meta["terminology_run_status"] != "处理中":
        raise GateError("Record must be processing before checkpointing")
    if not isinstance(plan.get("candidates"), list):
        raise GateError("Plan candidates must be a list")
    for raw in plan["candidates"]:
        if not isinstance(raw, dict):
            raise GateError("Candidate must be an object")
        candidate = json.loads(dump(raw))
        for key in ("expression", "locator", "reason"):
            require_text(candidate.get(key), "candidate." + key)
        if candidate.get("decision") not in ("create", "update", "skip", "pending"):
            raise GateError("Every candidate needs a final decision; execution failures are not pending semantics")
        cid = candidate.get("candidate_id") or "candidate-" + digest({
            "expression": norm(candidate["expression"]), "locator": norm(candidate["locator"])})[:16]
        require_text(cid, "candidate_id")
        payload_hash = digest(candidate)
        if cid in data["candidates"]:
            if data["candidates"][cid]["payload_hash"] != payload_hash:
                raise GateError("Candidate decision changed; use an explicit new revision")
            continue
        event = digest({"paper_id": meta["paper_id"], "pdf_sha256": meta["pdf_sha256"],
                        "revision": data["revision"], "candidate_id": cid})
        result = {}
        if candidate["decision"] in ("create", "update"):
            result = apply_term(store, candidate, event, meta)
        data["candidates"][cid] = {"expression": candidate["expression"], "locator": candidate["locator"],
                                    "reason": candidate["reason"], "decision": candidate["decision"],
                                    "payload_hash": payload_hash, "event": event, **result}
        save_run(path, text, meta, data)
        text = read(path)
    if "scan_completed" in plan:
        if type(plan["scan_completed"]) is not bool:
            raise GateError("Plan scan_completed must be a boolean")
        if plan["scan_completed"]:
            if meta["source_coverage"] != "full-paper":
                raise GateError("Only full-paper screening can complete")
            data["coverage_evidence"] = require_text(plan.get("coverage_evidence"), "coverage_evidence")
        data["scan_completed"] = plan["scan_completed"]
    data["blocked"] = plan.get("blocked", data.get("blocked", ""))
    if not isinstance(data["blocked"], str):
        raise GateError("blocked must describe any read/network/write interruption as a string")
    save_run(path, read(path), meta, data)
    return {"action": "checkpointed", "record": str(path), **counts(data)}


def validate_outputs(store: Store, meta: dict, data: dict):
    cards = {item[2]["term_id"]: item for item in term_index(store)}
    for item in data["candidates"].values():
        if item["decision"] in ("create", "update"):
            if item["term_id"] not in cards:
                raise GateError("A checkpointed term card is missing")
            card_path, card_text, _ = cards[item["term_id"]]
            validate_term(store, card_path)
            applied = (state(card_text, "terminology") or {}).get("events", {}).get(item["event"])
            if not applied or applied["payload_hash"] != item["payload_hash"]:
                raise GateError("Card write does not match the paper checkpoint")
            if store.link(card_path) != item["term_link"]:
                raise GateError("Card moved; repair the checkpoint link before completion")
    if meta.get("paper_note"):
        store.check_link(meta["paper_note"])


def finish(store: Store, token: str) -> dict:
    path, text, meta, data = open_run(store, token)
    if not data["scan_completed"] or data.get("blocked") or meta["source_coverage"] != "full-paper":
        raise GateError("Full screening and required verification must complete before commit")
    if not meta.get("pdf_path") or not io_path(Path(meta["pdf_path"])).is_file() or file_hash(Path(meta["pdf_path"])) != meta["pdf_sha256"]:
        raise GateError("Source PDF changed or disappeared during processing")
    validate_outputs(store, meta, data)
    meta.update(terminology_run_status="已完成", scan_completed=True, completed_from=meta["trigger_stage"],
                completed_at=stamp(), last_error="")
    data["history"].append({"at": stamp(), "stage": meta["trigger_stage"], "detail": "commit completed"})
    save_run(path, text, meta, data)
    store.release(token)
    return {"action": "completed", "paper_id": meta["paper_id"], "record": str(path), **counts(data)}


def abort(store: Store, token: str, reason: str, failed=False) -> dict:
    lease = store.lease(token)
    if lease.get("record"):
        path, text, meta, data = open_run(store, token)
        # A crash after the completion commit but before release must not undo a valid completion.
        if meta["terminology_run_status"] != "已完成":
            meta.update(terminology_run_status="失败" if failed else "未完成", scan_completed=False, last_error=reason)
            data["history"].append({"at": stamp(), "stage": "abort/recovery", "detail": reason})
            save_run(path, text, meta, data)
    store.release(token)
    return {"action": "released", "reason": reason}


def single(store: Store, plan: dict):
    candidate = plan.get("candidate")
    if not isinstance(candidate, dict) or candidate.get("decision") not in ("create", "update"):
        raise GateError("Single-term plan needs one create/update candidate")
    for key in ("expression", "locator", "reason"):
        require_text(candidate.get(key), "candidate." + key)
    token = store.acquire()
    try:
        result = apply_term(store, candidate, "single-" + digest(candidate), None)
        return {"action": "term-saved", **result}
    finally:
        store.release(token)


def audit(store: Store) -> dict:
    errors, terms, runs = [], 0, 0
    for path, _, _ in term_index(store):
        terms += 1
        try:
            validate_term(store, path)
        except GateError as exc:
            errors.append(str(path) + ": " + str(exc))
    for path, text, meta in store.notes({"terminology_run"}):
        runs += 1
        try:
            validate_run(meta, state(text, "terminology-run"))
            if meta["terminology_run_status"] == "已完成":
                validate_outputs(store, meta, state(text, "terminology-run"))
            for link in [*(meta.get("new_terms") or []), *(meta.get("updated_terms") or [])]:
                store.check_link(link)
        except GateError as exc:
            errors.append(str(path) + ": " + str(exc))
    return {"ok": not errors, "terms": terms, "runs": runs, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "begin", "checkpoint", "finish", "abort", "recover", "single", "audit", "lookup"))
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--library")
    parser.add_argument("--terms-dir")
    parser.add_argument("--runs-dir")
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--token")
    parser.add_argument("--stage", choices=STAGES, default="explicit")
    parser.add_argument("--coverage", choices=COVERAGES, default="unknown")
    parser.add_argument("--supplement", action="store_true", help="Only after an explicit supplement/reprocess request")
    parser.add_argument("--chat-only", action="store_true")
    parser.add_argument("--failed", action="store_true")
    parser.add_argument("--reason", default="")
    parser.add_argument("--query", default="")
    args = parser.parse_args()
    try:
        if args.chat_only:
            result = {"action": "chat-only", "writes": 0}
        else:
            store = Store(args.vault, args.library, args.terms_dir, args.runs_dir)
            if args.command in ("begin", "inspect"):
                if not args.identity:
                    raise GateError("--identity JSON is required")
                incoming = identity(object_file(args.identity), store)
                result = (inspect(store, incoming) if args.command == "inspect" else
                          begin(store, incoming, args.stage, args.coverage, args.supplement))
            elif args.command in ("checkpoint", "finish", "abort", "recover"):
                require_text(args.token, "--token")
                if args.command == "checkpoint":
                    if not args.plan:
                        raise GateError("--plan JSON is required")
                    result = checkpoint(store, args.token, object_file(args.plan))
                elif args.command == "finish":
                    result = finish(store, args.token)
                else:
                    require_text(args.reason, "--reason")
                    result = abort(store, args.token, args.reason, args.failed)
            elif args.command == "single":
                if not args.plan:
                    raise GateError("--plan JSON is required")
                result = single(store, object_file(args.plan))
            elif args.command == "lookup":
                require_text(args.query, "--query")
                result = {"matches": [{"path": str(path), "term_id": meta["term_id"],
                                       "preferred_en": meta.get("preferred_en"), "domain": meta.get("domain")}
                                      for path, _, meta in term_index(store) if norm(args.query) in names(meta)]}
            else:
                result = audit(store)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 1
    except (GateError, OSError, UnicodeError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
