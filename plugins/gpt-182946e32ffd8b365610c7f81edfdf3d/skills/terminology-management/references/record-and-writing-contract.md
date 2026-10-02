# 持久记录与增量写入契约

The live Vault policy/templates own the field names. Schema `1.0` uses `type: terminology` for cards and `type: terminology_run` for per-paper records. Paper status is `terminology_run_status`, distinct from intake routing's `processing_status`.

## Helper and identity

Resolve the absolute helper path from the installed Skill: two ancestors lead to `<PLUGIN_ROOT>`, then `scripts/terminology.py`. Python 3.10+ and its standard library suffice; no YAML package, background service or network library is required. On Windows use `py -3 -X utf8 -B`; elsewhere use the available Python 3 runtime.

Supply `--vault` explicitly. The helper discovers one `terminology_dashboard`, current template folder from `.obsidian/templates.json`, current term/run destinations and all actual typed cards/records outside templates. `--library`, `--terms-dir`, `--runs-dir` can point to confirmed **existing** moved destinations within that Vault. Missing/ambiguous destinations fail rather than recreate old folders. Owned frontmatter supports flat scalar fields and quoted scalar lists; unsupported syntax requires review and remains unmodified. Unknown user properties/body stay intact.

Identity JSON has `paper_title`, normalized `doi` if known, `zotero_library_id`, `zotero_item_key`, absolute `pdf_path`, optional `pdf_sha256`, `source_version` and resolved `paper_note` such as `[[20_文献/.../文献卡—...]]`. Add existing `paper_id` when known. The helper computes the file hash and rejects a conflicting supplied value. A confirmed title-only identity can set `identity_confirmed: true`; uncertain titles must be resolved first. A Zotero key without its library is not a global identity. Multiple strong matches/conflicting DOI require review.

Existing `paper_id` stays stable. New identities are recorded as aliases when DOI, Zotero metadata or PDF location is discovered later. Processed PDF hash/version stay tied to the completed revision; a different PDF sets `source_changed: true` without reopening the completed scan. Only an explicit supplement/reprocess request permits `--supplement`.

## Commands and states

Write identity/plan JSON to the current task's local staging area; do not store entire external datasets in the Vault. Use actual paths and JSON output tokens:

```text
py -3 -X utf8 -B "<PLUGIN_ROOT>/scripts/terminology.py" inspect --vault "<VAULT>" --identity "<identity.json>"
py -3 -X utf8 -B "<PLUGIN_ROOT>/scripts/terminology.py" begin --vault "<VAULT>" --identity "<identity.json>" --stage literature-intake --coverage full-paper
py -3 -X utf8 -B "<PLUGIN_ROOT>/scripts/terminology.py" checkpoint --vault "<VAULT>" --token "<returned token>" --plan "<decisions.json>"
py -3 -X utf8 -B "<PLUGIN_ROOT>/scripts/terminology.py" finish --vault "<VAULT>" --token "<returned token>"
```

`inspect` is read-only. `begin` performs a serial recheck; completed records return `skip-completed` or `source-changed` and release the lease. Missing material returns `waiting-material`, with “等待资料”. `process` holds a lease until `finish`/`abort`. Pass the true inspected coverage: `unknown`, `abstract-metadata-only`, `partial-paper` or `full-paper`. Never label full-paper merely because the file exists. Terminology coverage does not change the literature card's reading/learning status.

`checkpoint` merges candidate decisions incrementally, retaining the candidate ID and immutable decision payload. It can accept batches. A candidate ID defaults to a stable hash of expression+locator; pass a stable ID when the exact expression/locator will vary in the working plan. After a successfully recorded candidate, reuse its identical payload or omit it; do not silently change its decision. Explicit review/reprocessing uses a new revision.

For an interrupted read, necessary network check or write: call `abort --reason "<actual cause>"` (add `--failed` for a failed execution). Cards already written remain. If the process crashed, read `<library>/.terminology-lock/lease.json`; prove the previous task is no longer writing before `recover --token "<its token>" --reason "<recovery evidence>"`. No time-based expiry or token-free force release. The lock serializes all library writes because different papers may share a term. If a crash occurred after the completion commit, recovery releases the lease without undoing completion.

Atomic file replacement and expected-content checks protect against incomplete files and concurrent manual edits. A per-card event marker makes a crash between card publication and record checkpoint replay safely without a duplicate card/source. Completion is committed last, after coverage/decisions/output fields, active-template body sections/items, visible evidence/relationships/maintenance, links and event markers pass checks. Scientific meaning and actual PDF/external reading remain the Skill's responsibility.

## Decision plan

A plan is an object with `candidates` (list), `scan_completed` (boolean), `coverage_evidence` (actual checked PDF regions), and `blocked` (empty string on success or the necessary unfinished execution step). `scan_completed: true` only after a full-paper screen. Zero candidates can complete. Recorded semantic ambiguities are `pending`; operational failures must populate `blocked`/abort and never become a fake completed scan.

Each candidate contains:

| Fields | Contract |
| --- | --- |
| `candidate_id` (optional), `expression`, `locator` | Stable decision key; expression and actual PDF page/section/figure/equation locator |
| `decision`, `reason` | `create`, `update`, `skip`, `pending`; specific value/new-information reason or ambiguity with alternatives |
| `context` | For accepted terms, the source's actual usage and relevant new information |
| `term` | For accepted terms: preferred names, definition, definition_scope, list-valued abbr/aliases/domain/category/related_terms/related_concepts, term_status and term_confidence |
| `term.writing` (optional) | Source-backed `first_use`, `variants` and `academic_expressions` lists; missing evidence remains explicitly pending in the body |
| `external_evidence` | Selected, actually read external entries; see the external-verification reference |
| `verification_confirmed` | `true` only after source-grounded identity/expression/definition checks; required for a new `已核验` card |
| `matched_term_id`, `match_confirmed`, `definition_compatible` | For `update`, exact existing ID and both booleans true after reading the existing definition |
| `distinct_sense`, `distinction_reason` | For same-name/abbreviation but different meanings, a confirmed distinction plus domain; never a way around an unresolved conflict |

Create preserves the active template's complete body section names/order, its five academic-expression items, its four-column literature, five-column external-source and three-column maintenance tables, plus additional template sections. `分析与待复核问题` and `AI 分析与待复核问题` are accepted analysis headings; use the one actually configured. Required sections renamed to unsupported names fail for review instead of silently reverting to a hardcoded layout. Create uses a filesystem-safe preferred name, with a domain suffix for different meanings. Update preserves preferred names/definition/status and personal prose, adds confirmed aliases, relevant classifications, source-backed expressions and evidence within the existing sections, and unions resolved source/relationship links in properties **and body**. Definitions or entity identity requiring replacement need an explicit reviewed edit. Existing incomplete bodies require an explicitly authorized template repair. Cards without managed markers and manual processing records without machine checkpoints require careful adoption; the helper leaves them intact and does not synthesize a completed history.

Every entry in `term.writing.first_use` and `term.writing.academic_expressions` is an object with single-line `text` and `basis`. Each `variants` entry also has `scope`. The basis must identify the candidate's inspected `locator` or the exact URL of an actually read entry in `external_evidence`. This verifies provenance linkage, not the truth of a phrase; read and judge the source before supplying it. Example:

```json
{
  "writing": {
    "first_use": [{"text": "peak ground acceleration (PGA)", "basis": "PDF p. 2, Methods"}],
    "variants": [],
    "academic_expressions": [{"text": "本文用法示例：peak ground acceleration", "basis": "PDF p. 2, Methods"}]
  }
}
```

Do not claim an uninspected variant scope or universal usage from a single paper. Without writing evidence, the helper exposes existing names/abbreviations/aliases, labels first-use formatting as writing advice, and marks missing expression evidence or variant scope as `待补`. Those pending examples do not change a verified definition's status. Machine event hashes remain tied to the original decision payload; a layout repair must preserve them rather than replay an altered candidate or reset the completed scan.

Term evidence deduplicates the same paper+PDF version+locator+selected external-source URLs; unchanged source rows are not appended again. Revisions preserve prior candidate decisions in history. `created_count`, `updated_count`, `skipped_count`, `pending_count`, `new_terms` and `updated_terms` reflect this revision; review previous history for earlier totals. A card's stable ID never changes when additional aliases are found.

## Query, single term and audit

```text
py -3 -X utf8 -B "<PLUGIN_ROOT>/scripts/terminology.py" lookup --vault "<VAULT>" --query "<term or abbreviation>"
py -3 -X utf8 -B "<PLUGIN_ROOT>/scripts/terminology.py" single --vault "<VAULT>" --plan "<single-term.json>"
py -3 -X utf8 -B "<PLUGIN_ROOT>/scripts/terminology.py" audit --vault "<VAULT>"
```

`lookup` returns exact normalized preferred/alias/abbreviation candidates; read definitions and use targeted Vault search for plural/translation/near-name variants. `single` takes `{ "candidate": <one create/update decision> }`, requires read external evidence when outside a paper workflow, and makes no per-paper completion record. `audit` checks structural integrity, active-template body completeness and resolved links without changing notes. Hidden/commented or fenced example headings cannot satisfy body checks. All commands with `--chat-only` perform zero writes.

Machine checkpoints are JSON inside Obsidian `%% ... %%` comments within managed regions; human-readable tables expose decisions/history. Do not edit the hidden state independently of the visible record. Preserve content outside `%% terminology:managed:start/end %%` and `%% terminology-run:managed:start/end %%`, especially personal notes.
