---
name: course-learning
description: Ingest course materials, answer course questions, and maintain verifiable learning notes in an Obsidian research vault. Use for lecture PDFs, slide decks, textbooks, exercises, and follow-up course learning; do not use to bulk-copy source materials into the vault.
---

# Course learning

Turn course materials into traceable learning notes and checkable understanding without confusing an uploaded file with mastery.

If the user asks only for an explanation or says “暂时不要入库”, answer in chat and do not write to the Vault. An explicit request to import or organize course material authorizes the corresponding course notes. Read course PDFs and slides directly; MinerU paper ingestion is not the course-reading workflow.

## Discover before choosing a destination

1. Locate the current vault from a user-supplied vault/note path, the working directory, or a source path by finding the nearest `.obsidian` ancestor.
2. If none of those paths is inside a vault, inspect only the currently available workspace roots for directories containing `.obsidian`. Use a candidate automatically only when it is the sole plausible vault; otherwise show the candidates and ask the user to select one. Do not scan arbitrary drives or recreate an old path.
3. Re-read the selected vault's root `AGENTS.md` before modifying anything.
4. Rebuild a small, task-specific map on every invocation: locate the course dashboard, target course page, relevant unit(s), source/entry cards, and active templates from frontmatter, wikilinks, titles, aliases, and targeted search. Do not assume any particular folder name, language, or historical course path.
5. Resolve the external source file from the user-provided path or from an existing source locator. Confirm its course and lecture identity from the material itself or an existing index; do not infer it solely from a filename.
6. If the current organization cannot identify a unique course or suitable destination, preserve the source reference in a discovered source-card workflow and ask the user to choose the course or destination. Do not recreate former folders after a restructure.

## Choose the appropriate mode

### First-time material intake

- Read the existing course page and source/index notes before creating anything.
- Preserve the original path, file name, edition/date when known, and exact chapter, page, slide, or exercise locators.
- Create or update a course unit using the currently discovered `course_unit` template or equivalent local convention. Record scope and source pointers, not a copy of the raw lecture or textbook.

### A question about an existing course

- Read the relevant course unit, linked concept/method notes, and source/index card before answering.
- Return to the original PDF, slide deck, textbook, or exercise only when the existing notes lack the needed evidence or locator.
- After answering, update only the affected course unit and any genuinely reusable concept, method, or question card. Link them using targets resolved from the current vault.

### Learning verification

- Keep the distinction between source content, AI explanation, the user's own derivation, and unresolved doubt explicit.
- Set a mastery level only when the vault's current rules define evidence for it. A lecture summary alone is not proof of derivation, reproduction, or transfer.
- For a core topic, leave one proportionate, checkable artifact: a concept map, derivation, independently solved example, minimal script/calculation, or explanation outline. Record its location and the test or comparison used.

## Respect the source boundary

- Treat raw course files as external authoritative sources unless the user expressly authorizes copying a specified file or set of files.
- Do not bulk-import, move, rename, or duplicate PDFs, slides, textbooks, question papers, or archive files into the vault. Keep source pointers and exact locators instead.
- Do not claim that a formula, worked example, course requirement, or answer is present unless it has been verified in the source or an existing note with an adequate locator.

## Finish safely

1. Use the vault's current templates and logging requirements, discovered at run time rather than assumed from past layouts.
2. Where required by `AGENTS.md`, make a concise update to the actual project/course home, current-context note, and session/change log; record changes, evidence limits, and one visible next action. In a combined plugin workflow, pass shared index/current-context updates to `knowledge-sync` as the sole writer of those files; this Skill remains the writer of course units and learning artifacts.
3. Re-read changed notes and verify frontmatter, local links, source locators, and the absence of duplicate units or cards.
4. Report what changed, what source locations support it, the user's current demonstrated mastery boundary, and the smallest recommended next learning action.

## Layout changes and timing

This skill does not run continuously in the background. Each time it is invoked, it re-discovers the live vault structure and current local rules, so folders, courses, templates, and note names may be reorganized without embedding stale paths in this skill. Clear course-material requests may select this plugin's `course-learning` automatically.
