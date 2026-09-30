# Academic Research Assistant · 学术研究助手

[简体中文](README.md) | **English**

A Codex plugin for research and coursework, combining literature registration, paper summaries, critical reading, multi-paper comparison, reviewed full-text extraction, and Obsidian knowledge-base maintenance.

Start with a paper, a lecture file, or a research question, then build reusable notes and knowledge links with precise source references. The plugin works from original materials, separates paper facts and author claims from inference and analysis, and follows the current rules of your vault when saving or updating notes.

| Item | Details |
| --- | --- |
| Plugin display name | 学术研究助手 |
| Current version | `0.4.4`; see the [changelog](CHANGELOG.md) |
| Bundled skills | 9 |
| Plugin identifier | `gpt-182946e32ffd8b365610c7f81edfdf3d` |
| Marketplace name | `astraskye-local`, displayed as “astraskye 本地插件” |
| License | [Apache License 2.0](LICENSE) |

## Contents

- [About the plugin](#about-the-plugin)
- [Repository layout](#repository-layout)
- [Installation](#installation)
- [Skills directory and functions](#skills-directory-and-functions)
- [Usage examples](#usage-examples)
- [Outputs and source rules](#outputs-and-source-rules)
- [Maintenance and validation](#maintenance-and-validation)

## About the plugin

The plugin supports three everyday workflows:

- **Literature research:** identify a paper, register its source, summarize its question and results, examine methods, equations, figures, and evidence, and compare papers against a shared question.
- **Course learning:** explain concepts, organize chapters, and work through derivations using slides, lecture notes, textbooks, and exercises, while retaining page or slide references and checkable learning records.
- **Knowledge building:** reuse existing notes and maintain Obsidian links, indexes, MOCs (Maps of Content), and project context for future research and follow-up questions.

When you request full-text archiving, the plugin also coordinates MinerU extraction, page-by-page comparison with the original PDF, and archival of the reviewed bundle. Summaries and deep reading can usually work directly from the PDF; full-text parsing, OCR, or MinerU is used when explicitly requested.

The package consists primarily of skills and helper scripts. Zotero, MinerU, and other external services are configured separately. Credentials, personal papers, and vault contents are outside this repository. Summary and deep-reading notes currently default to Chinese while preserving original technical terms, variables, and units.

## Repository layout

### Repository root

| Path | Purpose |
| --- | --- |
| [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json) | Registers the marketplace name and plugin source |
| [plugins/](plugins/) | Plugin source and resources |
| [docs/code-review.md](docs/code-review.md) | Code review and validation records |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [requirements-dev.txt](requirements-dev.txt) | Python dependency for PDF review and tests |
| [LICENSE](LICENSE) | Apache 2.0 license |
| [README.md](README.md) / [README.en.md](README.en.md) | Chinese / English documentation |

### Plugin directory

The plugin lives in [`plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/`](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/). Paths below are relative to that directory.

| Path | Purpose |
| --- | --- |
| [plugin.json](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/plugin.json) | Agent Plugins manifest: identity, version, and display metadata |
| [.codex-plugin/plugin.json](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/.codex-plugin/plugin.json) | Codex compatibility manifest, including the skills entry point |
| [skills/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/) | Instructions, templates, and support files for 9 skills |
| [scripts/validate_note.py](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/scripts/validate_note.py) | Shared summary/deep-reading validator for note structure, image links, and math formatting |
| [references/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/references/) | Paper identity matching and cross-skill handoff rules |
| [tests/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/tests/) | Regression tests for note validation and paper identity matching |
| [assets/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/assets/) | Plugin avatars and icons |
| [MAINTENANCE.md](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/MAINTENANCE.md) | Maintenance, upgrade, and migration conventions |

## Installation

### Prerequisites

- Install and sign in to a Codex CLI version that supports `codex plugin`. After installation, manage the plugin through `/plugins` in the CLI or a desktop client that supports plugins.
- Git is required for the local-clone method.
- To save notes, provide an accessible Obsidian vault path. The plugin reads its current `AGENTS.md`, templates, and indexes. Specify the destination when several vaults are available.
- Python 3.10 or later is required for Python validation scripts and tests. PDF review needs a working PDF page-count tool; the repository dependency file provides PyMuPDF.
- For Zotero-backed tasks, configure Zotero and its tools separately. For MinerU full-text extraction, install and configure MinerU capabilities separately. Accessible original PDFs or course files remain the content sources.

### Option 1: Add the marketplace from GitHub

Run these commands in order in PowerShell or a typical macOS / Linux shell:

```sh
codex plugin marketplace add https://github.com/astraelia/Academic-Research-Assistant.git
codex plugin add gpt-182946e32ffd8b365610c7f81edfdf3d@astraskye-local
codex plugin list --marketplace astraskye-local --json
```

`astraskye-local` is the marketplace name declared by the repository. It is also used when installing from GitHub.

### Option 2: Clone locally and install

Use this option to inspect, maintain, or back up the plugin files. Keep the repository in a stable local directory:

```sh
git clone https://github.com/astraelia/Academic-Research-Assistant.git
cd Academic-Research-Assistant
codex plugin marketplace add .
codex plugin add gpt-182946e32ffd8b365610c7f81edfdf3d@astraskye-local
codex plugin list --marketplace astraskye-local --json
```

### Verify installation and start using the plugin

Check the marketplace, plugin identifier, version, and enabled state in the plugin list. In the CLI, run `codex`, then enter `/plugins`. In the plugin browser, choose the “astraskye 本地插件” source and locate “学术研究助手”.

Start a new chat or CLI session after installation. Restart the client if the interface has not refreshed. For each task, provide an unambiguous paper identifier or file path and state whether the result should be saved to your vault.

See the official [CLI command reference](https://learn.chatgpt.com/docs/developer-commands) for installation commands and the [plugins documentation](https://learn.chatgpt.com/docs/plugins) for plugin management.

## Skills directory and functions

All skills live under the plugin's `skills/` directory. Each subdirectory has a `SKILL.md` entry point. Click a skill name to read its full definition.

| Skill / subdirectory | Function | Main output |
| --- | --- | --- |
| [instructions](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/instructions/SKILL.md) | Routes research and study requests, orders combined workflows, and passes paper identity, source coverage, and target files between skills. | Workflow routing and handoff context |
| [literature-intake](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/literature-intake/SKILL.md) | Verifies the title, DOI, Zotero key, and PDF source; finds an existing paper folder; creates or updates a source card with reading purpose and next actions. | Literature source card and source pointers |
| [literature-summary](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/literature-summary/SKILL.md) | Produces a compact Chinese summary of one paper's question, method, evidence, contribution, and limitations, with source locators and relevant figure/table crops. | `总结—…md` and `assets/summary-figures/` |
| [paper-deep-reading](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/paper-deep-reading/SKILL.md) | Reconstructs one core paper's argument, maps claims to evidence, and analyzes essential equations, study design, visuals, conclusion boundaries, and transferable research ideas. | `精读—…md` and `assets/deep-figures/` |
| [literature-compare](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/literature-compare/SKILL.md) | Compares at least two papers against the same question, covering assumptions, methods, data, metrics, results, limitations, and comparability. Returns the comparison in chat by default; saves it when requested. | Comparison matrix and analysis; optional comparison note |
| [paper-ingestion](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/paper-ingestion/SKILL.md) | Resolves and deduplicates one PDF, coordinates external MinerU extraction, hands the staged result to page-by-page review, and archives the bundle after its checks pass. | `paper.md`, parse manifest, review records, and `assets/parsed/` |
| [paper-parse-review](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/paper-parse-review/SKILL.md) | Compares parsed text, reading order, visuals, and equations with every original PDF page; corrects staged output and records evidence. Preserves accurate images and uses Markdown for tables and equations. Incomplete reviews retain their pending status. | Corrected staging bundle, `parse-audit.json`, and `parse-review.md` |
| [course-learning](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/course-learning/SKILL.md) | Organizes course units, answers questions, and supports derivations directly from original materials. Maintains source locators and checkable learning artifacts, distinguishing organized material from demonstrated understanding. | Course notes, concept/method/question cards, and learning artifacts |
| [knowledge-sync](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/knowledge-sync/SKILL.md) | Discovers the current vault structure, reuses existing records, and updates links, indexes, MOCs, and project context. In combined workflows, maintains cross-note navigation while preserving the preceding skill's main output. | Links, indexes, MOCs, and context updates |

Each skill also includes `agents/openai.yaml`. Some include `references/`, `scripts/`, or `tests/`; consult the current repository for the exact files.

## Usage examples

Select “学术研究助手” in a new chat, then provide your materials and objective. Replace the placeholders below with your own identifiers or paths.

### Register and summarize a paper

```text
Register this paper in my Obsidian vault and create a summary.
Paper: <Zotero item key, DOI, or original PDF path>
Vault: <vault path>
Check for an existing paper folder first, reuse it, and retain source locators for major conclusions.
```

### Read a core paper in depth

```text
Read this paper critically, focusing on assumptions, essential equations, figure evidence, and the scope of its conclusions.
Paper: <paper identifier or original PDF path>
Vault: <vault path>
Save the deep-reading note in the matching paper folder and update the relevant indexes.
```

### Compare multiple papers

```text
Compare these papers against the question "<specific research question>": <identifiers or paths for at least two papers>.
Use a matrix to compare methods, data, evaluation metrics, results, and limitations. Explain which results are directly comparable.
Answer in chat only; do not save to the vault yet.
```

### Organize a course and ask follow-up questions

```text
Use these slides to organize learning notes for "<course / chapter>".
Slides: <original file path>
Vault: <vault path>
Keep page or slide locators, explain the key concepts, and leave one checkable derivation or worked example.
```

### Parse, review, and archive full text

```text
Parse this paper's full text with MinerU, review every page against the original PDF, then archive the bundle after its checks pass.
PDF: <original PDF path>
Vault: <vault path>
Report review coverage, corrections, and unresolved issues. Keep incomplete work in staging.
```

Common combined workflows:

| Goal | Workflow |
| --- | --- |
| Register and summarize | `literature-intake` → `literature-summary` |
| Register, read in depth, and update indexes | `literature-intake` → `paper-deep-reading` → `knowledge-sync` |
| Parse and archive full text | `paper-ingestion` extraction and staging → `paper-parse-review` page-by-page review → `paper-ingestion` archival |
| Organize a course and update shared course indexes | `course-learning` → `knowledge-sync` when needed |

## Outputs and source rules

Outputs for a paper serve distinct purposes and share the same confirmed identity and folder:

| Output | What it records |
| --- | --- |
| Literature source card | Bibliographic identity, original file location, source coverage, and reading purpose |
| Summary note | A concise account of the research question, results, and value |
| Deep-reading note | Reasoning, evidence strength, equations, visuals, and research transfer analysis |
| Full-text parse bundle | Reviewed text and images, extraction provenance, and page-by-page review records |

New summaries and deep-reading notes normally use `20_文献/<filesystem-safe original paper title>/`. An existing matched folder is reused; the actual destination follows current vault rules and the task's specified path.

- **Source authority:** the selected original PDF governs scientific paper content. Original slides, lecture notes, textbooks, or exercises govern course content. Zotero supplies bibliographic and attachment identity and is read-only by default. Parsed text helps with navigation and extraction.
- **Traceability:** important claims retain page, section, figure, table, or equation locators. Incomplete materials have an explicit coverage boundary; inference, analysis, and hypotheses remain distinct from source content.
- **Task-scoped writing:** registration, summary, deep reading, and parsing are separately requested outputs. For a one-off answer, explicitly say “answer in chat only; do not save to the vault”.
- **Incremental maintenance:** skills search for duplicates and read current rules before writing, preserve existing notes and user content, and normally leave original PDFs and course files in their original locations.
- **Update timing:** course and knowledge-base skills rediscover the live structure and rules when invoked. Knowledge-base updates are triggered by tasks.
- **Validation scope:** scripts check structure, links, formatting, and recorded review coverage. Content accuracy still depends on actual page-by-page comparison with the original PDF.

## Maintenance and validation

Maintain plugin functionality in this repository's plugin directory. See [MAINTENANCE.md](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/MAINTENANCE.md) for conventions and [CHANGELOG.md](CHANGELOG.md) for history.

The shared summary/deep-reading validation logic lives in the plugin root's `scripts/validate_note.py`; the same-named scripts inside the skills forward to it. For functionality changes, update both manifest versions and run the relevant checks. After committing to GitHub or updating the source, reinstall through the marketplace and verify the installed version.

Run tests from the repository root:

**Windows / PowerShell**

```powershell
py -3 -m pip install -r requirements-dev.txt
$pluginDir = './plugins/gpt-182946e32ffd8b365610c7f81edfdf3d'
py -3 -B -m unittest discover -s "$pluginDir/tests" -p 'test_*.py'
py -3 -B -m unittest discover -s "$pluginDir/skills/paper-parse-review/tests" -p 'test_*.py'
```

**macOS / Linux**

```sh
python3 -m pip install -r requirements-dev.txt
plugin_dir='./plugins/gpt-182946e32ffd8b365610c7f81edfdf3d'
python3 -B -m unittest discover -s "$plugin_dir/tests" -p 'test_*.py'
python3 -B -m unittest discover -s "$plugin_dir/skills/paper-parse-review/tests" -p 'test_*.py'
```

Tests use isolated temporary fixtures and leave real Zotero libraries and Obsidian vaults untouched. This repository stores plugin source, resources, and maintenance documentation. Keep personal environment settings, tokens, original papers, vault contents, and installation caches in their respective environments.
