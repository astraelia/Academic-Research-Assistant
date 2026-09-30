---
name: paper-parse-review
description: Review a MinerU research-paper parse page by page, preserve correct Markdown, repair text, tables and equations in Markdown, correct figures when needed, and produce a verifiable QA record before full-text import.
metadata:
  version: "1.1.0"
---

# Paper Parse Review

Produce a correct, traceable `paper.md` from one original PDF and its MinerU parse. The PDF is the authority. Preserve accurate Obsidian Markdown tables and equations as-is; correct them in Markdown only when their content is wrong or their format is unsuitable. Preserve accurate figure content and its existing image file. If packaging breaks only the relative image reference, copy the existing image if needed and repair the link without altering the image. Crop and replace from the PDF only when the figure content is missing, incomplete, or wrong, or remains unusable after repairing its path. The final deliverable is a staged bundle containing `paper.md`, `parse-audit.json`, generated `parse-review.md`, and local figure assets. This skill checks and repairs the parse; another workflow decides whether to archive it or create summary/deep-reading notes.

## Inputs and staging

1. Resolve exactly one original PDF and its completed MinerU parse. If parsing has not run, use the installed MinerU skill with `--pages all --json` and an available tier appropriate to the source; record the actual tier and any quality limits. Do not treat a pending, failed, or truncated export as a complete parse. Follow MinerU's existing local/remote authorization rules; do not silently switch to remote processing.
2. Stage the exported Markdown as `STAGE/paper.md` **outside** the destination vault folder. Keep the PDF unchanged. Record the actual MinerU document/tier locator from the structured result, such as `doc:abc123/tier:flash`. If the source has multiple candidate PDFs or versions, resolve its identity before reviewing.
3. Read [references/review-contract.md](references/review-contract.md) when creating or editing audit entries. Initialize the audit from the original PDF, not MinerU's reported page range:

   `py -3 "<SKILL_ROOT>/scripts/review.py" init "STAGE" --source-pdf "PDF_PATH" --locator "doc:.../tier:ACTUAL_TIER"`

   Resolve `<SKILL_ROOT>` to this Skill's absolute directory; never rely on the shell's current directory. The command checks the PDF hash and page count and creates a pending entry for every original page. It refuses to overwrite an existing audit.

## Compare, correct, and record

For **each original PDF page**, inspect the PDF page image and the corresponding MinerU page/block text. Compare the full page with `paper.md`: reading order, headings, columns, footnotes, omitted or duplicated text, numbers, symbols, units, and captions. Use `mineru read` page/block locators and `--format image` for visual comparison. Work in page batches on long papers; record completed pages as you go.

Independently inventory **every figure, table, and central equation visible in the PDF**, including elements missing from the MinerU export. For figures, inspect all panels, labels, legends, axes, and caption correspondence. If figure content is accurate, preserve the image unchanged; if only packaging or its relative Markdown link is broken, copy the existing image if needed and repair the link without altering the image. Crop and replace from the PDF only when the figure content is missing, incomplete, wrong, or remains unusable after repairing its path. For tables, compare every header, cell, unit, footnote, and row/column order. Keep an accurate Obsidian Markdown table unchanged; repair incorrect cells or convert nonconforming output to a Markdown pipe table. Do not insert a screenshot or other image of a table. For equations, verify symbols, subscripts, operators, and numbering. Keep correct Markdown math unchanged; repair errors or convert nonconforming output to inline/display Markdown math (`$...$` or `$$...$$`). Do not insert an equation image. Keep complex aligned formulas in a `$$\begin{aligned}...\end{aligned}$$` block. Mark `visual_inventory_complete` only after inspecting the original PDF page, including a page with no visuals.

Repair errors in the **staged** Markdown and assets using only what the PDF supports. Record each change in `parse-audit.json` with the PDF page/block locator, the original problem, the action, and a literal anchor present in the corrected `paper.md`. A `corrected` page or visual needs a resolved correction entry. Keep ambiguous or unrecoverable regions as `unresolved` with an open issue; never guess missing data or mark them verified. Do not edit the original PDF or Zotero item.

After editing the audit, run:

`py -3 "<SKILL_ROOT>/scripts/review.py" sync "STAGE"`

This validates the recorded page/visual evidence, derives completed pages and open issues, and regenerates `parse-review.md`. Reinspect corrected regions against the PDF. The generated status reflects the recorded audit; it does not itself prove the OCR or scientific content is correct.

## Final gate and handoff

Run this before any knowledge-base import, then again on the copied bundle:

`py -3 "<SKILL_ROOT>/scripts/review.py" check "STAGE" --source-pdf "PDF_PATH" --require-verified`

The gate rejects missing pages, pending checks, unresolved issues, missing or unlinked figure assets, table/equation image crops in audits initialized with the Markdown visual policy, non-Markdown table/math anchors, stale reports, and original-PDF hash or page-count mismatches. If it fails, keep the work in staging and report the exact pages and issues; the bundle is not a verified import. When it passes, hand the corrected bundle and QA artifacts to this plugin's `paper-ingestion` or the caller. Report source PDF identity, reviewed page count, figures/tables/equations checked, corrections made, and any limitations. The machine gate checks review coverage and file integrity; the page-by-page comparison against the PDF is the substantive content check.
