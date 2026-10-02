---
name: knowledge-sync
description: Maintain durable, source-traceable knowledge in an Obsidian research vault after literature, course, project, or research-learning work. Use when the user asks to record, update, link, or sync the vault; do not use for a one-off answer that should leave the vault unchanged.
---

# Knowledge sync

Maintain the vault as a small, trustworthy record of durable knowledge rather than a transcript of every exchange.

In a combined plugin workflow, receive the actual output paths and evidence status from the source Skill. Update only shared links, indexes, MOCs, project/current-context notes, or other cross-note navigation; do not regenerate that Skill's literature card, summary, deep-reading note, parse bundle, comparison, course unit, terminology card or terminology processing record. `terminology-management` owns term extraction, verification and writes; use its actual output/status for navigation, without repeating ingestion. If the user asked for chat-only work, do not write.

## Discover the current vault before acting

1. Starting from a user-supplied vault/note path, the working directory, or a source path, locate the nearest ancestor containing `.obsidian`. Treat that directory as the vault root.
2. If none of those paths is inside a vault, inspect only the currently available workspace roots for directories containing `.obsidian`. Use a candidate automatically only when it is the sole plausible vault; otherwise show the candidates and ask the user to select one. Do not scan arbitrary drives or guess from an old path.
3. Re-read the root `AGENTS.md` on every invocation and follow it as the current source of local conventions, safety boundaries, and required reading order.
4. Resolve the files needed for this task dynamically. Prefer frontmatter (`type`, source identifiers, aliases, course/project fields), wikilinks, and targeted file/content search over assumed directory names. For example, find a current-context note by `type: current_context`, templates by their `type`, and a source note by its title, Zotero key, DOI, source path, or alias.
5. Only inspect the relevant subtree and related notes. Do not maintain a persistent path manifest or assume that a prior folder layout is still valid.

If a renamed or reorganized vault makes a required destination or template ambiguous, show the plausible candidates and ask the user where the new material belongs. Never recreate an obsolete directory merely because it existed in an earlier layout.

## Decide whether and what to retain

- First search for an existing note or card that already covers the source, claim, concept, method, course unit, question, or project. Update it incrementally instead of creating duplicates.
- Retain only material that will be useful beyond the immediate answer: a source locator, evidence-backed claim, clarified concept, method boundary, reproducible artifact, open question, decision rationale, or concrete next action.
- Keep original facts, author claims, the user's interpretation, AI synthesis, and unverified hypotheses visibly distinct. Do not invent citations, page numbers, figures, data versions, experimental conditions, or results.
- Preserve the authority of external systems specified by the vault rules. Do not copy, move, rename, or bulk-edit PDFs, raw data, code, Zotero records, or user-authored notes unless the user has explicitly authorized that exact scope.
- For a request to archive a paper's parsed full text and figures, use this plugin's `paper-ingestion` to match the paper folder, parse with MinerU, review the extraction, and store a source bundle. Use this skill afterward only for durable research notes and links; parsed text alone is not a verified research conclusion.

## Make the smallest coherent update

1. State the planned files and scope before modifying an existing note when the local rules require it.
2. Use a currently discovered template when creating a card or note. Preserve its frontmatter and fill unknown provenance fields with an explicit pending value rather than a guess.
3. Add source links and precise locators whenever the information came from a document, dataset, figure, code revision, or Zotero item.
   If a matching `parse-manifest.json` and `paper.md` exist, use them for navigation and check their review status; retain the PDF/Zotero source pointer as the evidence anchor, especially for unchecked or corrected regions.
4. Add Obsidian wikilinks only after resolving their target against the current vault; do not introduce broken links merely to make a note look connected.
5. When the vault's current `AGENTS.md` requires it, update the dynamically located project home, current-context note, and session/change log with a concise statement of the actual change, its evidence boundary, and the next actionable step.

## Verify and report

- Re-read every changed file. Check that frontmatter remains valid, paths and wikilinks resolve against the current layout, and no duplicate card was created.
- Report the files changed, the durable knowledge retained, the source anchors used, and anything that remains unverified or needs a user decision.

## Layout changes and timing

This skill is not a background watcher. It refreshes its understanding of the vault at the start of **each invocation**, so renaming or reorganizing folders does not itself make the skill depend on stale paths. It may be selected automatically for clearly requested vault-sync work.
