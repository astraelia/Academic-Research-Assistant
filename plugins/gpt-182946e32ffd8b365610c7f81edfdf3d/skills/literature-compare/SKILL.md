---
name: literature-compare
description: Compare two or more identified papers on a user-specified research question using source-grounded claims. Use for “比较这几篇论文”; do not duplicate their individual summary or deep-reading notes or save a comparison to Obsidian unless requested.
---

# Literature comparison

Compare the papers against the **same question or decision**, preserving differences in setting and evidence strength. Require at least two unambiguously identified papers; accept Zotero keys, DOIs, PDF paths, existing literature cards, summaries, or deep-reading notes. If the comparison criterion is unstated, infer a narrow useful criterion from the request and state it; ask only when multiple materially different comparisons are equally plausible.

Read [paper identity and handoff](../../references/paper-identity-and-handoff.md) when resolving existing Vault folders or combining this Skill with intake. Zotero is read-only. Use the original PDFs for disputed or important scientific claims. Verified notes and parse bundles can speed navigation but cannot turn unchecked passages into verified evidence. For each paper, record source coverage and exact page, section, figure, table, or equation anchors; do not infer data from a title or abstract. When only metadata or abstracts are available, label the output preliminary and restrict claims accordingly.

Build one comparison matrix with rows appropriate to the question, such as research object, assumptions, method, data/setting, baseline, metrics, central result, limitations, and relevance to the user's work. Normalize terms, units, and denominators before comparing numbers. Separate what each author reports from cross-paper synthesis and your own 【分析】. Explain when methods or outcomes are not directly comparable. End with supported common ground, substantive disagreement, evidence gaps, and the next source check or experiment that would distinguish them.

Return the comparison in chat by default. If the user asks to save it, locate the intended Vault and read its current `AGENTS.md`, relevant literature guidance and templates. Search for an existing comparison note on the same papers and question before creating one. Write only that comparison note, linking verified existing paper notes and source anchors; do not overwrite the individual `文献卡—`, `总结—`, or `精读—` files. Hand the comparison path to `knowledge-sync` for an explicitly requested MOC or index update. Re-read changed files and check links and source coverage before reporting.
