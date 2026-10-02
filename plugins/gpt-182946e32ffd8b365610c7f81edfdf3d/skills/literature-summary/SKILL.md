---
name: literature-summary
description: Generate a compact, source-grounded Chinese summary note for one paper and save it to Obsidian. Use for “总结这篇论文”; bibliographic registration belongs to literature-intake and critical deep reading belongs to paper-deep-reading.
metadata:
  version: "1.6.0"
---

# Literature Summary

Create a reliable, reusable **summary note** for exactly one paper. The outcome is a concise Chinese Markdown note that lets the user recall the research question, method, evidence, contribution, and boundary without reopening the paper. A separate `文献卡—...md` is owned by `literature-intake`.

## Required inputs and safe defaults

The user may identify the paper with a Zotero item key, DOI, exact title, an unambiguous Zotero search query, or a local PDF path. Use a default Obsidian vault only when the user or current application configuration identifies one; otherwise locate a unique workspace candidate containing `.obsidian` or ask the user for an absolute vault path. Use the vault’s existing literature root.

- Do not guess a Zotero item or a PDF attachment.
- If a Zotero search has multiple plausible papers, present a compact candidate list with title, year, creator, and item key; wait for a selection.
- If an item has multiple plausible primary PDFs, ask the user which attachment to use. Do not silently pick the first attachment.
- If the target note already exists, do not overwrite it or its assets without the user's explicit instruction to replace or update it.
- Write the normal bundle below `20_文献`. When the user explicitly requests direction classification, infer one concise, source-grounded Chinese research-direction label and write below `20_文献/<direction>/` instead. State the chosen direction in frontmatter and the delivery report.

Use the Zotero skill only for Zotero Desktop readiness, bibliographic metadata, and attachment discovery. This workflow is read-only toward Zotero: never create, edit, delete, or link Zotero notes or items.

For a combined workflow, read [paper identity and handoff](../../references/paper-identity-and-handoff.md) and reuse the caller's confirmed paper folder and source coverage.

## Source hierarchy

Treat sources in this strict order:

1. The selected PDF is authoritative for the paper's claims, numbers, formulas, figures, tables, and conclusions.
2. Zotero supplies bibliographic metadata and attachment location; resolve conflicts in paper content in favor of the PDF and flag metadata conflicts.
3. A MinerU parse is an extraction aid, never independent scientific evidence. Prefer a `paper.md` whose `parse-manifest.json` matches the chosen PDF hash and whose review is verified. Cross-check central claims, equations, and figure references against the PDF. For a partial review, use only checked regions and verify the rest directly. Record material discrepancies in the note.
4. Do not introduce outside knowledge unless the user explicitly asks for it. Mark it as 【外部】 and link or cite the source.

Never promote an abstract, title, caption, OCR fragment, or MinerU output into a claim that the PDF does not support. If no PDF is available, offer a clearly marked metadata/abstract-only source card through `literature-intake`; do not present it as a full-paper summary.

## Terminology handoff

Read [terminology handoff](../../references/terminology-handoff.md) after resolving the paper identity and before extracting terminology. When saving to a Vault with a configured terminology library, invoke this plugin's `terminology-management` with the same identity and source version. Completed processing at intake, summary or deep reading suppresses ingestion here; read existing cards for canonical wording. Otherwise reuse already checked PDF content and finish missing terminology work. A terminology error is reported separately from the requested note's result.

External glossary reading belongs to term verification and its cards; scientific claims in this note still follow the PDF source hierarchy and the user's external-literature scope. Chat-only/no-sync overrides stop all Vault writes, including terminology records.

## Workflow

1. Resolve one Zotero item and its primary PDF. Capture the paper's exact bibliographic title, creators, venue, year, DOI/URL, item key, attachment key, and the chosen PDF path. Check title discrepancies against the PDF before deciding a filename; do not derive it from a translated short label or a possibly truncated attachment filename.
2. Search the whole literature root for the matching paper folder before selecting the output path. Reuse a matching, verified `paper.md` plus its `parse-manifest.json` and `assets/parsed/` when present; also reuse a matching source_map.json, source_bundle.json, or paper-card.md. If a verified match has a legacy short folder name, reuse it and report the mismatch; rename only when the user requested a naming repair. Inspect the PDF wherever extraction or review is uncertain. If the user explicitly asked to archive parsed full text, run this plugin's `paper-ingestion` first. For summary-only work, read the PDF directly; use MinerU only for explicitly requested OCR or parsing. Read enough of the full paper to map the abstract, introduction, method, results, discussion/conclusion, main figures, main tables, and essential equations. Apply source-grounding, figure-crop, and equation-confidence checks without creating an unnecessary full bilingual reader.
3. Build a compact evidence inventory before drafting: research question, gap, approach, data/setting, main results, author-stated limitations, and the figures/tables that support the important conclusions.
4. Crop every main-paper visual that the note discusses. Make tight, individual crops; do not use full-page screenshots when a figure or table can be isolated. Store them under the note folder's `assets/summary-figures/` directory. Never write summary assets into a deep-reading asset directory. Preserve figure/table numbers and page references. Put a compact image index at the end for main figures that are not otherwise discussed.
5. Draft the note with the summary template in references/obsidian-output.md. Use Chinese by default while preserving canonical terms, model names, variables, units, and abbreviations.
6. Validate the completed note and its relative image links:

    py -3 "<PLUGIN_ROOT>/scripts/validate_note.py" "PATH_TO_NOTE" --mode summary

   Resolve the absolute script path from this Skill's plugin root; do not depend on the shell's current directory. Use `--allow-legacy-folder` only after verifying an existing shorter folder belongs to this paper. Resolve every reported error before delivery.
7. Report the generated Obsidian note path, asset directory, Zotero item key for traceability, source coverage, and any source limitations. Do not claim the note was imported into Obsidian; writing it under the configured vault is the import mechanism. Do not create, update, or link any Zotero note.

## Grounding and writing rules

- Put a traceable paper pointer beside every major result, numerical value, figure/table interpretation, central method statement, and limitation. Use forms such as [论文：PDF p. 4，Fig. 2] or [论文：结果部分，Table 1].
- Separate source classes visibly: direct paper facts use paper pointers; use 【推断】 for a reasonable but unstated inference; use 【分析】 for the agent's judgment; use 【外部】 only after the user requests external material.
- State 原文未说明, 论文未提供, or 当前材料不足以判断 rather than filling a template field speculatively.
- Distinguish author-claimed innovation from 【分析】实际创新. Do not inflate novelty.
- Keep author-acknowledged limitations separate from 【分析】可能局限.
- Include only formulas essential to understanding the paper. Preserve symbols, subscripts, units, and equation numbers. A display formula must use one complete $$...$$ pair on one physical Markdown line for Better Notes and Obsidian compatibility. If a formula cannot be transcribed confidently, insert a tight PDF crop and state that the image is authoritative.
- Never infer a plot trend solely from a caption. When a visual cannot be inspected, state that the caption or nearby text is all that can be grounded.

## Delivery layout

Read references/obsidian-output.md before creating the note. For a new paper folder, the normal destination is:

    VAULT_ROOT/20_文献/SAFE_PAPER_TITLE/总结—SAFE_PAPER_TITLE.md

with associated crops in:

    VAULT_ROOT/20_文献/SAFE_PAPER_TITLE/assets/summary-figures/

`SAFE_PAPER_TITLE` is the exact paper title after only filesystem-required sanitization: remove Windows-invalid characters, collapse whitespace, and remove trailing dots/spaces. Use this **same basename** for the paper folder and `总结—...md`; never substitute a Chinese paraphrase for an English title or abbreviate a title merely for convenience. Append a Zotero key to both basenames only for a real collision. Shorten only when the filesystem cannot accommodate the full title, and record the exact title in frontmatter. Honor the user's stated `20_文献` root or requested `20_文献/<direction>` root rather than silently switching to an integration-specific subfolder such as 课题组文献. When the identity search finds an existing correctly named folder, write there and preserve its established direction. Before delivery, compare the folder name, note filename, frontmatter title, and Zotero/PDF title; resolve any mismatch and validate links after a rename.

## Scope boundary

This skill creates a compact evidence-backed literature summary, not:

- a full paragraph-by-paragraph bilingual translation (use nature-reader);
- a bibliographic source card (use literature-intake) or extended critical audit (use paper-deep-reading);
- a multi-paper comparison (use literature-compare) or bibliography search. Zotero is used only as a read-only source for the resolved paper and its attachment.
