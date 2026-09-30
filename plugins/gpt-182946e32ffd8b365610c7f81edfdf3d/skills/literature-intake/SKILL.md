---
name: literature-intake
description: Register one identified paper and its source pointers as a literature card in an Obsidian vault. Use for “把论文加入知识库” or bibliographic intake; do not parse full text or generate a summary or deep reading unless separately requested.
---

# Literature intake

Create or update the **source card** for one paper. The card records identity, access, reading purpose, and verified evidence status. A source card is distinct from `总结—...md`, `精读—...md`, and a parsed `paper.md` bundle.

## Resolve identity and destination

1. Accept a Zotero item key, DOI, exact title, unambiguous Zotero query, or local PDF path. Use Zotero read-only for bibliographic fields and attachment discovery. If multiple items or main PDFs are plausible, show candidates and wait for selection. Do not invent missing metadata.
2. Locate the intended Vault from the user path, a current application configuration, or a single unambiguous workspace candidate containing `.obsidian`. Before writing, read its root `AGENTS.md`, current context, literature guidance, and active literature-card template. Do not rely on a historical hardcoded Vault path.
3. Read [paper identity and handoff](../../references/paper-identity-and-handoff.md). Search the whole literature subtree for the same Zotero key, normalized DOI, PDF hash, or corroborated exact title before creating a folder or card. Reuse a strong, unique match; resolve uncertain matches without making a duplicate.
4. For a new folder, use the verified original title after filesystem-required sanitization and the Vault's current literature root/direction convention. Keep the original title in frontmatter. Do not copy the PDF into the Vault by default.

## Write only the source card

Use the Vault's current literature-card template or equivalent local convention. In a Vault with the documented naming pattern, the output is `文献卡—<paper-folder>.md` in the matched paper folder. Record verified title, authors, year, DOI, Zotero key, PDF path, source coverage, reading purpose, and one next action. Mark unknown values as pending; do not promote an abstract, filename, or metadata record into a full-paper finding. Add claim/evidence rows only for source regions actually inspected, with page, figure, table, or section locators. Keep the user-authored fields and prior judgments when updating an existing card; make the smallest supported change.

Do not create a summary, deep-reading note, parsed full text, translation, or new MOC here. When the caller requested those, hand the resolved identity, chosen folder, card path, verified source coverage, and open questions to the responsible plugin Skill. `knowledge-sync` may then update cross-note links or indexes if requested or required by current Vault rules.

Re-read the written card, validate its frontmatter, title, source pointers, and local links, and confirm no duplicate card or paper folder was created. Report the exact files changed and any bibliographic conflict or missing PDF.
