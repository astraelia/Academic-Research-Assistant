---
name: paper-deep-reading
description: Generate a source-grounded Chinese deep-reading note from one Zotero paper and its PDF, including claim-evidence analysis, essential formulas, individually cropped figures in deep-reading-specific assets, limitations, and research takeaways in an Obsidian folder. Use for a single core paper, not a lightweight summary, full bilingual translation, or formal peer-review report.
metadata:
  version: "1.5.0"
---

# Paper Deep Reading

Create a critical but fair deep-reading note for exactly one core paper. The note must reconstruct the paper's reasoning:

    problem → prior limitation → core insight → method → evidence → bounded conclusion

The outcome helps a researcher explain what the paper proves, what it does not prove, and which parts are transferable to their own work.

## Required inputs and safe defaults

The user may identify the paper with a Zotero item key, DOI, exact title, an unambiguous Zotero search query, or a local PDF path. Use a default Obsidian vault only when the user or current application configuration identifies one; otherwise locate a unique workspace candidate containing `.obsidian` or ask the user for an absolute vault path. Use the vault’s existing literature root.

- Do not guess a Zotero item or primary PDF attachment.
- The Zotero helper cannot determine the paper currently selected in the Zotero UI. Ask for an item key, DOI, exact title, attachment key, or PDF path when none is supplied.
- If Zotero returns multiple plausible papers or a selected item contains more than one credible main PDF, show a compact selection list and wait for the user.
- Do not overwrite an existing 精读—文献名.md or its assets without an explicit replace/update request.
- Write the normal bundle below `20_文献`. When the user explicitly requests direction classification, infer one concise, source-grounded Chinese research-direction label and write below `20_文献/<direction>/` instead. State the chosen direction in frontmatter and the delivery report.

Use the Zotero skill only for readiness, bibliographic metadata, and attachment discovery. This workflow is read-only toward Zotero: never create, edit, delete, or link Zotero notes or items.

For a combined workflow, read [paper identity and handoff](../../references/paper-identity-and-handoff.md) and reuse the caller's confirmed paper folder and source coverage.

## Source hierarchy and provenance

Use this strict hierarchy:

1. The selected PDF is authoritative for all scientific content: claims, methods, numbers, equations, figures, tables, and conclusions.
2. Zotero is authoritative only for bibliographic metadata and attachment identity. Flag metadata conflicts rather than silently resolving them.
3. Prefer a `paper.md` with a `parse-manifest.json` that matches the chosen PDF hash and has a verified review. It accelerates extraction but never substitutes for PDF visual verification. For a partial review, identify the unchecked pages and unresolved issues before using the bundle.
4. External literature is opt-in. Use it only when the user asks and label it 【外部】 with a direct source.

Label content by provenance:

- [论文：PDF p. N，Section/Fig./Table/Eq.] — directly supported by the paper;
- 【推断】 — reasonable inference that the paper does not explicitly state;
- 【分析】 — the agent's evidence-based interpretation or critique;
- 【假设】 — a testable research extension;
- 【外部】 — user-requested material outside the paper.

When page indices are unreliable, use section, figure, table, equation, or source-block IDs rather than inventing a page number. If the PDF is unavailable or incomplete, set source coverage to partial-paper or abstract-metadata-only and mark unseen content 当前材料不足以判断.

## Workflow

1. Resolve one Zotero item and primary PDF. Record the exact bibliographic title, creators, venue, year, DOI/URL, Zotero item and attachment keys, and PDF path. Check title discrepancies against the PDF before deciding a filename; do not use a translated short label or a possibly truncated attachment filename.
2. Search the whole literature root for the matching paper folder. Reuse a matching, verified `paper.md`, `parse-manifest.json`, `assets/parsed/`, source_map.json, source_bundle.json, translation_notes.md, or paper-card.md. If a verified match has a legacy short folder name, reuse it and report the mismatch; rename only when the user requested a naming repair. Favor a matching source map when it has stable text, figure, and page anchors. Inspect the parse review log and independently verify key PDF regions. If the user explicitly asked to archive parsed full text and no bundle exists, run this plugin's `paper-ingestion` first.
3. For a PDF or source map that lacks a reliable preparation bundle, read the PDF directly and record page, figure, table, and equation locators. Use MinerU only for explicitly requested OCR or parsing; use an optional external preparation workflow only when its source map or evidence audit is actually needed. Do not duplicate OCR or replace a valid extraction merely to satisfy a fixed sequence. Inspect its validation block and locator mode when used. This skill's final note is validated separately.
4. Build an evidence inventory before drafting: research question, paper type, core assumptions, method components, formulas, datasets/materials, baselines, metrics, main figures/tables, result claims, author-stated limitations, and source pointers.
5. Create a claim-evidence matrix. For every central conclusion, record the evidence, comparison/condition, metric or observation, justified conclusion, stronger unsupported interpretation, and source pointer.
6. Inspect every main figure and table. Make tight individual crops that retain labels, axes, legends, color bars, and subpanel markers; exclude headers, footers, adjacent prose, and captions. Put the image crops in `assets/deep-figures/`. Never write deep-reading assets into a summary asset directory. Supplementary visuals are optional unless they support a point in the note.
7. Draft the note using references/obsidian-output.md. Use Chinese by default, preserve technical names and notation, and make the reader's reasoning path visible.
8. Validate the final note and all local image links:

    py -3 "<PLUGIN_ROOT>/scripts/validate_note.py" "PATH_TO_NOTE" --mode deep

   Resolve the absolute script path from this Skill's plugin root; do not depend on the shell's current directory. Use `--allow-legacy-folder` only after verifying an existing shorter folder belongs to this paper. Correct all errors before delivery.
9. Report the final Obsidian note and asset paths, Zotero item key for traceability, PDF coverage, locator mode, MinerU status, and any incomplete or low-confidence parts. Do not create, update, or link any Zotero note.

## Analytical discipline

- Read the full supplied paper before making full-paper claims. Do not substitute an abstract, conclusion, caption, or MinerU fragment for missing sections.
- Keep author-stated limitations separate from 【分析】 potential weaknesses, alternative explanations, missing controls, reproducibility risks, and generalization limits.
- Evaluate claims proportionately. Use verbs such as reports, observes, supports, is consistent with, or suggests. Say demonstrates necessity/sufficiency or causes only when the design genuinely supports it.
- Do not call an idea novel, first, state-of-the-art, or unprecedented without a user-requested and cited external prior-art check.
- Do not turn the note into a formal reviewer report or create a self-test/quiz unless the user asks. The required critical analysis should be concrete, falsifiable, and useful to the user's research.
- Build a terminology ledger for recurring models, variables, datasets, metrics, and abbreviations. Use one canonical term throughout the note.

## Formula and visual protocol

- Include only essential formulas. Preserve the source variables, indices, numerical constants, operators, and equation labels; explain the formula's role, assumptions, inputs/outputs, and relation to the evidence.
- Display each transcribed formula as one complete $$...$$ expression on one physical Markdown line. Never emit $$$, mixed delimiters, repeated equations, or a reconstructed formula that cannot be confidently verified against the PDF.
- For low-confidence or image-only equations, use a tight equation crop and label any transcription 低置信度转写（以原图为准）.
- A figure/table analysis must identify what is shown, comparison/conditions, the directly readable trend or number, the author interpretation, and the conclusion it can support. Do not infer plot details from a caption alone.

## Delivery layout

Read references/obsidian-output.md before writing. For a new paper folder, the normal destination is:

    VAULT_ROOT/20_文献/SAFE_PAPER_TITLE/精读—SAFE_PAPER_TITLE.md

with relative assets:

    VAULT_ROOT/20_文献/SAFE_PAPER_TITLE/assets/deep-figures/

`SAFE_PAPER_TITLE` is the exact paper title after only filesystem-required sanitization: remove Windows-invalid characters, collapse whitespace, and remove trailing dots/spaces. Use this **same basename** for the paper folder and `精读—...md`; never substitute a Chinese paraphrase for an English title or abbreviate a title merely for convenience. Append a Zotero key to both basenames only for a real collision. Shorten only when the filesystem cannot accommodate the full title, and preserve the exact title in frontmatter and H1. Honor the requested `20_文献` or `20_文献/<direction>` root rather than silently switching to 课题组文献. When the identity search finds an existing correctly named folder, write there and preserve its established direction. Before delivery, compare the folder name, note filename, frontmatter title, and Zotero/PDF title; resolve any mismatch and validate links after a rename.

## Scope boundary

This skill creates one in-depth evidence note. It is not:

- a full paragraph-aligned bilingual reader (use nature-reader);
- a quick summary or batch literature database entry (use literature-summary);
- a multi-paper comparison (use literature-compare) or citation search;
- a formal peer-review report.
