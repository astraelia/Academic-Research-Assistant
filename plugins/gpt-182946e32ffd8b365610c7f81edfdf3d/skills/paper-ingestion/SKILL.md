---
name: paper-ingestion
description: Parse one research-paper PDF with MinerU, require a separate page-by-page PDF review, then archive its corrected Markdown and visual assets in the matching Obsidian literature folder. Use when the user asks to import parsed full text; a summary or deep-reading note alone does not require this skill.
metadata:
  version: "1.3.0"
---

# Paper ingestion

Create a reusable, source-traceable parse bundle for **one** paper. The PDF remains the scientific authority; `paper.md` is a checked extraction, not a new source of truth. This skill does not draft a literature summary or claim that an unread paper has been critically reviewed.

For a combined workflow, read [paper identity and handoff](../../references/paper-identity-and-handoff.md). Reuse the same confirmed paper folder as `literature-intake`, `literature-summary`, and `paper-deep-reading`.

## Resolve the source and destination

1. Resolve one local PDF and, when available, its Zotero item and attachment. Use Zotero for bibliographic identity and the authoritative PDF location. Do not guess among multiple candidate items or primary attachments.
2. Locate the intended vault from a supplied path, an explicit current application configuration, or a unique workspace candidate containing `.obsidian`. Read its current root `AGENTS.md`, current-context note, and relevant literature-folder guidance before writing. Resolve renamed destinations dynamically.
3. Record the PDF SHA-256, normalized DOI, Zotero item key if known, exact title, and source path. Search the **whole** literature subtree before choosing a folder: first Zotero key/DOI/PDF hash in note frontmatter or a parse manifest, then exact normalized title with author/year and existing folder context. Run the resolved absolute path to this Skill's `scripts/find_existing.py` to surface candidates; inspect the actual notes before accepting one. A unique strong identity match reuses that folder, even if it is inside a research-direction subfolder. Resolve conflicting or weak matches with the user rather than creating a possible duplicate.
4. If no match exists, create one paper folder named from the exact bibliographic title after only filesystem-required sanitization. Add a direction level only when requested or established by current vault conventions. Do not translate, paraphrase, or abbreviate the title for the folder; use a Zotero key suffix only for a real collision. Preserve the original title in metadata. If a matched folder has a legacy short name, reuse its identity and report the mismatch rather than creating a duplicate; perform a link-aware rename when the user asks to normalize existing names.

## Parse and review

1. If the folder already has the same PDF hash, a `parse-audit.json`, and passing this plugin's `paper-parse-review` final and bundle checks, reuse it. An older bundle without that audit, a different PDF version, or an existing unowned `paper.md` requires inspection before any replacement.
2. Use the installed `mineru` skill and its current CLI contract. For full-paper ingestion, stage the full parse outside the destination folder, for example `mineru parse "PDF_PATH" --pages all --json --output "STAGE/paper.md"`. Check structured completion and page coverage; a pending or failed parse is not an imported paper. Do not infer support for extracted figure files from a Markdown export: inspect its actual links and MinerU's available page/block images. An API key alone does not authorize `--remote`; follow the MinerU skill's upload, tier, and recovery gates.
3. Invoke this plugin's `paper-parse-review` skill on the original PDF and staged `paper.md`. It owns the PDF comparison, corrections, `parse-audit.json`, and generated `parse-review.md`. Preserve accurate Obsidian Markdown tables/formulas and MinerU figure image content as-is. If only packaging or a relative image link is broken, copy the existing image if needed and repair the link without altering it. Repair nonconforming or incorrect tables/formulas in Markdown; crop and replace a figure from the PDF only when its content is missing, incomplete, wrong, or unusable after its path is repaired. Run its resolved `scripts/review.py check ... --source-pdf "PDF_PATH" --require-verified` gate before any archive step. Keep partial or blocked work in staging and report its unresolved pages.
4. Copy the review's `review_status`, `checked_pages`, and `open_issues` into `parse-manifest.json` without strengthening them. Include its audit and report in the bundle. Never mark the manifest `verified` when the separate review gate fails.

## Archive without damaging the vault

Read [references/bundle-contract.md](references/bundle-contract.md) for the artifact layout and manifest fields. Run both this plugin's `paper-parse-review` final gate and `py -3 "<SKILL_ROOT>/scripts/validate_bundle.py" "STAGE" --source-pdf "PDF_PATH" --require-audit` before copying into the paper folder, then run both again on the copied bundle and re-read the resulting files. Resolve `<SKILL_ROOT>` to this Skill's absolute directory; never assume the shell's current directory. Preserve existing literature cards, summary/deep-reading notes, user assets, and PDF attachments. Do not copy the PDF into the vault by default; the manifest records its Zotero identity, source path, and hash. Do not overwrite a previous parse for a different PDF hash. If a requested refresh replaces generated parse files, retain the prior generated version under a dated `parse-history/` directory and report the change.

Report the matched or new folder, source identity, MinerU tier and local/remote mode, reviewed page coverage, corrections, unresolved issues, and final artifact paths. A requested summary or deep reading can then use the matching bundle through this plugin's `literature-summary` or `paper-deep-reading`; invoke those workflows only when the user asks for them.
