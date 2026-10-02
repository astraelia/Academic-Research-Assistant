---
name: terminology-management
description: Screen and verify reusable academic terms, query or incrementally maintain an Obsidian terminology library, and share persistent per-paper completion records across literature intake, summary and deep reading. Use for academic terminology requests or those literature workflows' terminology handoff; ordinary translation and course reading do not trigger ingestion.
---

# 学术术语管理

Maintain a selected terminology library with source-backed, reusable concepts. This Skill owns term cards and paper terminology records; the caller owns its literature card, summary or deep-reading note. Execute the handoff within the current task, using this plugin's Skill. No background watcher is installed.

## Destination and source scope

Discover the confirmed Vault and read its current `AGENTS.md`, current context, terminology dashboard (`type: terminology_dashboard`), management policy, external-source guide and active templates. The initial layout is `61_学术术语库` at the Vault root; rediscover moved notes by type and stable IDs. Do not place the library under a graph folder or create a second library when an old path is missing. Resolve ambiguity before writing.

If the user asks for chat-only work, “暂时不要入库” or “不要同步”, do not create records, acquire a write lease, or update cards/context. Query existing cards read-only if helpful. If the Vault has no configured library, report the missing destination; library setup is a separate requested action.

The selected PDF determines a term's usage in the current paper. Zotero supplies bibliographic and attachment identity and remains read-only. Verified parse text may help navigation; it cannot establish uninspected meaning. Use direct PDF reading; terminology work does not implicitly enable MinerU or create a summary/deep-reading note.

## One successful run per paper

Before extracting candidates or querying external sources, read [paper identity and handoff](../../references/paper-identity-and-handoff.md) and [record and writing contract](references/record-and-writing-contract.md). Use the shared helper at `<PLUGIN_ROOT>/scripts/terminology.py`, resolved from this Skill's actual root, with one confirmed identity JSON.

1. `inspect` reads persistent records across the Vault. Strong matches use stable `paper_id`, normalized DOI, Zotero **library plus item key**, selected PDF hash and resolved paper-card link. A late DOI enriches an existing ID. Ambiguous or conflicting matches stop duplicate creation.
2. `begin` rechecks identity while holding the library's writer lease. `skip-completed` means no extraction, external recheck or term writes. `source-changed` records the changed PDF and reports that explicit supplement/reprocessing is needed; it also skips extraction. Both can enrich identity without claiming another successful run.
3. `waiting-material` preserves a bibliographic record without completing terminology. Only a readable full-paper source supports completion. `process` returns a lease token and existing candidate checkpoints; reuse these and process only missing work. If material proves unreadable, abort with the true coverage/error; having a PDF filename does not establish full coverage.
4. Persist decisions with `checkpoint` as candidates are resolved. Re-read output against the **active term template**, including every body section and academic-expression item, then `finish` only after the full paper was screened, all candidates have decisions, necessary external checks finished, and properties, body, links and checkpoints passed validation. Zero accepted terms is a successful completed scan. A recorded semantic ambiguity may remain `pending`; read/network/write interruption remains unfinished.

Completion from **any** of `literature-intake`, `literature-summary` or `paper-deep-reading` suppresses automatic ingestion in both other stages and future chats. Their writing may read cards to normalize terms. Do not derive completion from a summary/deep note merely existing, or confuse terminology coverage with having mastered or deeply read the paper.

On failure, `abort` saves the reason and releases the lease, retaining valid cards and checkpoints. A crash keeps the lease: inspect its `lease.json` and establish that the previous task has ended before `recover` with its exact token and a recorded reason. Do not expire a live writer by elapsed time or forcibly delete the lease. Different papers also serialize card writes to avoid duplicate entities. See the contract for explicit supplements and safe retries.

## Screen and verify candidates

Prefer theories, methods, models, important measures/parameters and recurring domain concepts with traceable meaning. A candidate needs at least one lasting benefit: understanding the user's research, repeated reading, writing/translation, or resolving ambiguity. Record the specific benefit; a paper keyword, basic word or temporary label alone is insufficient.

Search existing cards by preferred English/Chinese, aliases, abbreviation and domain/context. Normalization identifies candidates, not semantic identity. Read the matched definition before deciding:

| Decision | Evidence and result |
| --- | --- |
| `create` | Useful concept, reliable meaning, no same entity; one meaning per stable term ID |
| `update` | Same confirmed meaning; add only new aliases, contexts, source locators and relationships |
| `skip` | No lasting benefit, already fully represented, or no useful new information; retain a short reason |
| `pending` | Substantive uncertainty about meaning, abbreviation, translation or entity; retain alternatives and evidence for review |

For a new term, unclear definition/translation or conflicting sources, read relevant **specific public entries** according to [external verification](references/external-verification.md) and the Vault guide. Public inclusion is supporting evidence, not the acceptance criterion; absence does not reject a sound research concept. Original-paper definitions can suffice when public entries do not exist. Separate a source's reference definition, this paper's usage, AI analysis and personal notes.

Do not merge by abbreviation or fuzzy name alone. Different meanings can share a name but require domain-qualified cards and an explicit distinction reason. Preserve established preferred names/definitions and user notes; append traceable new evidence. No automatic entity merges, renames or deletions. `已核验` needs confirmed identity, expression and definition with no unresolved material conflict; the helper does not establish scientific truth.

## Complete the template body

The current template owns section names and order, including the configured analysis heading and any additional sections. Preserve definitions, bilingual/academic expressions, literature evidence, external verification, relationships, analysis and visible maintenance records. Properties do not substitute for these body sections. Render confirmed `related_terms` and `related_concepts` links in the relationship section; keep source usage and new information in the template's separate table columns.

Supply source-backed first-use forms, variant scopes and useful academic expressions with the optional `term.writing` object described in the writing contract. Read the PDF or selected external entry before supplying each expression; name its exact basis. Label proposed first-use formatting as **writing advice**, not a quotation. A usage example from this paper does not establish a universal preferred collocation. If evidence is missing, retain the template item and state `待补`; never manufacture phrases or scopes to fill it. Definitions may remain verified while supplementary writing examples are explicitly pending.

The helper validates body completeness before card publication, at completion and during `audit`. Existing cards that do not match the current template require an explicitly authorized, reviewed in-place repair; do not bypass validation, delete IDs/history, or reopen a completed paper merely to repair its formatting. Preserve user prose and machine checkpoints, back up affected cards, validate previews and check for concurrent edits before applying the repair.

## Explicit terminology requests

- Query: use `lookup` plus actual card reading; report definition, domain, provenance and unresolved issues. This is read-only.
- Add or supplement one term: verify worthiness and read sources, then `single` with one create/update decision. It writes no paper-completion record. If the source is a paper, prefer its normal paper handoff so PDF locators and stable identity are retained.
- Supplement/reprocess a paper or review its pending candidates: use `begin --supplement` **only after an explicit request**, preserve previous revision history and source evidence, and record the actual new scope. A partial supplement cannot claim a new completed full-paper screen; close it unfinished if that coverage was not checked.
- Check the library: `audit` checks fields, active-template body sections/items, visible relationships/evidence/maintenance, duplicate IDs, checkpoint integrity and links; semantic worthiness still requires reading cards and sources. Propose specific changes before merges, renames or deletion.

After real writes, pass actual term/record paths, counts, source coverage and pending items to `knowledge-sync` when current Vault rules require shared navigation/context updates. That Skill does not re-extract terms or rewrite these cards. Report the library destination, created/updated/skipped/pending counts, processing status, external sources actually read and any unverified behavior.
