# 文献流程的术语交接

For `literature-intake`, `literature-summary` and `paper-deep-reading`, include terminology handling when saving to a Vault that has a configured terminology library. Use this plugin's `skills/terminology-management/SKILL.md` in the current task. Respect chat-only/no-sync overrides before any record/card/context write. Do not activate it for courses, ordinary translation, comparison or full-text parsing solely because a PDF is read.

After confirming paper identity and the existing paper folder, inspect the persistent terminology record **before extracting new candidates or browsing glossaries**. Share one stable paper identity (including Zotero library+item key, DOI, source PDF/hash/version and the actual paper-card link), current terminology destination and trigger stage. See [paper identity](paper-identity-and-handoff.md) and [terminology Skill](../skills/terminology-management/SKILL.md).

| Result | Caller behavior |
| --- | --- |
| `skip-completed` | Reuse term cards as needed for wording; no candidate extraction, external verification or term write |
| `source-changed` | Persist/report changed source and the explicit-review next step; automatic ingestion remains skipped |
| `waiting-material` | Preserve an unfinished waiting record; continue the requested task only within its source limits |
| `process` / resume | Handoff checked PDF content/locators; terminology Skill finishes missing work and commits the record last |
| Identity conflict / busy writer / execution failure | Report the exact issue; preserve requested literary output and valid partial terminology results; no false completion |

`literature-intake` owns only its bibliographic/source card. With a full readable PDF, it delegates a focused full-paper terminology screen to the terminology Skill; this does not generate a summary/deep-reading note or mark the paper as deeply read. With metadata only, it records waiting material. Source-card reading status remains bibliographic unless actual evidence justifies otherwise.

Summary/deep reading reuse content already checked against the PDF. A prior successfully completed intake terminology run means they skip ingestion. If summary/deep reading completes first, intake and the other stage also skip. Missing records or unfinished runs still need actual full-paper screening; existence of an old summary/deep note is not a completion record.

External glossary use is authorized for the terminology workflow and recorded in term cards. The parent note's scientific claims still use the selected PDF; this handoff does not authorize unrelated external literature in the summary/deep-reading note. Necessary external access failures leave terminology unfinished; an ambiguity with documented alternatives can remain a pending candidate after a completed scan.

Term cards and processing records have exactly one writer, `terminology-management`. Return their actual paths, status, counts and pending issues to the caller; `knowledge-sync` may then update shared navigation/context once for the combined task. Report the requested literature output and terminology result independently so an interrupted terminology check does not erase a valid summary or imply full success.
