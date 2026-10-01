# 学术研究助手 · Academic Research Assistant

**简体中文** | [English](README.en.md)

面向科研与课程学习的 Codex 插件，支持文献登记、总结、精读与比较，课程资料学习，以及 Obsidian 知识库维护。

依据原始论文、课件和教材生成带来源定位的笔记，并维护已有知识库中的索引与链接。

| 项目 | 信息 |
| --- | --- |
| 功能 | 文献处理、课程学习、知识库维护 |
| 开发者 | astraskye |
| 类别 | 科研学习 |
| 当前版本 | `0.4.5` · [更新记录](CHANGELOG.md) |
| 内置 Skills | 9 个 |
| 许可证 | [Apache License 2.0](LICENSE) |

## 目录

- [插件介绍](#插件介绍)
- [仓库目录](#仓库目录)
- [安装说明](#安装说明)
- [Skills 目录与功能](#skills-目录与功能)
- [使用示例](#使用示例)
- [产物与来源规则](#产物与来源规则)
- [维护与验证](#维护与验证)

## 插件介绍

插件围绕三个日常场景组织工作：

- **文献研究**：确认论文身份，建立文献卡，提炼研究问题与主要结果，分析方法、公式、图表和证据链，并围绕指定问题比较多篇论文。
- **课程学习**：依据课件、讲义、教材和习题解释概念、梳理章节、辅助推导，保留页码或幻灯片定位，并形成可检查的学习记录。
- **知识积累**：复用已有笔记，维护 Obsidian 双向链接、索引、MOC（内容地图）及项目上下文，让后续研究和提问有可追溯的基础。

需要保存论文全文时，插件还提供 MinerU 解析、原 PDF 逐页复核与归档流程。总结和精读通常可以直接读取原 PDF；全文解析、OCR 或 MinerU 在明确请求这些任务时启用。

这是一个以 skills 和辅助脚本为主的插件包。仓库没有捆绑 Zotero、MinerU 等外部服务，也不包含账号凭据、个人论文或知识库内容。总结与精读笔记默认使用中文，保留原始术语、变量和单位。

## 仓库目录

### 仓库根目录

| 路径 | 用途 |
| --- | --- |
| [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json) | 注册 marketplace 名称及插件来源 |
| [plugins/](plugins/) | 插件源码与资源 |
| [docs/code-review.md](docs/code-review.md) | 代码审查与验证记录 |
| [CHANGELOG.md](CHANGELOG.md) | 版本记录 |
| [requirements-dev.txt](requirements-dev.txt) | PDF 复核及测试所需的 Python 依赖 |
| [LICENSE](LICENSE) | Apache 2.0 许可证 |
| [README.md](README.md) / [README.en.md](README.en.md) | 中文 / 英文说明 |

### 插件目录

插件位于 [`plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/`](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/)。下表中的路径均相对于这个目录。

| 路径 | 用途 |
| --- | --- |
| [plugin.json](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/plugin.json) | Agent Plugins 清单，声明插件身份、版本及展示信息 |
| [.codex-plugin/plugin.json](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/.codex-plugin/plugin.json) | Codex 兼容清单，声明 skills 入口等配置 |
| [skills/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/) | 9 个 skills 的指令、模板及支持文件 |
| [scripts/validate_note.py](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/scripts/validate_note.py) | 总结与精读共用的笔记结构、图片链接及数学格式校验器 |
| [references/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/references/) | 论文身份匹配及跨 skill 交接规则 |
| [tests/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/tests/) | 笔记校验、文献查重等回归测试 |
| [assets/](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/assets/) | 插件头像与图标 |
| [MAINTENANCE.md](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/MAINTENANCE.md) | 维护、升级与迁移约定 |

## 安装说明

安装命令使用插件标识 `gpt-182946e32ffd8b365610c7f81edfdf3d` 和 marketplace 名称 `astraskye-local`；marketplace 在界面中显示为“astraskye 本地插件”。

### 准备环境

- 安装并登录支持 `codex plugin` 命令的 Codex CLI。安装后可通过 Codex CLI 的 `/plugins` 或支持插件的桌面客户端管理插件。
- 使用本地克隆方式时，需要 Git。
- 保存笔记时，准备一个可访问的 Obsidian Vault，并提供其路径。插件会读取当前 `AGENTS.md`、模板及索引；有多个候选 Vault 时，需要明确目标。
- 运行 Python 校验脚本或测试时，需要 Python 3.10 或更高版本。PDF 复核需要可用的页数读取工具，仓库的依赖文件提供 PyMuPDF。
- 使用 Zotero 条目时，另行配置 Zotero 及对应工具；使用 MinerU 全文解析时，另行安装并配置 MinerU 能力。可访问的原 PDF 或课程原件仍是内容依据。

### 方式一：从 GitHub 添加 marketplace

在终端依次执行。以下命令可用于 PowerShell 或常见的 macOS / Linux shell：

```sh
codex plugin marketplace add https://github.com/astraelia/Academic-Research-Assistant.git
codex plugin add gpt-182946e32ffd8b365610c7f81edfdf3d@astraskye-local
codex plugin list --marketplace astraskye-local --json
```

`astraskye-local` 是仓库清单定义的 marketplace 名称，通过 GitHub 安装时也使用这个名称。

### 方式二：克隆到本地后安装

适合需要查看、维护或备份插件文件的用户。将仓库放在稳定的本地目录中：

```sh
git clone https://github.com/astraelia/Academic-Research-Assistant.git
cd Academic-Research-Assistant
codex plugin marketplace add .
codex plugin add gpt-182946e32ffd8b365610c7f81edfdf3d@astraskye-local
codex plugin list --marketplace astraskye-local --json
```

### 确认安装并开始使用

在插件列表中核对 marketplace、插件标识、版本和启用状态。Codex CLI 可先运行 `codex`，再输入 `/plugins`；在插件界面选择“astraskye 本地插件”来源，找到“学术研究助手”。

安装后开启新聊天或新的 CLI 会话，再调用插件。如果界面尚未刷新，可重启客户端。开始处理资料时，提供明确的论文标识或文件路径，并说明是否要保存到知识库。

安装命令参考 [官方 CLI 命令说明](https://learn.chatgpt.com/docs/developer-commands)，插件管理参考 [官方插件文档](https://learn.chatgpt.com/docs/plugins)。

## Skills 目录与功能

所有 skills 均位于插件的 `skills/` 目录，每个子目录以 `SKILL.md` 为说明入口。点击下表名称可查看完整定义。

| Skill / 子目录 | 功能介绍 | 主要产物 |
| --- | --- | --- |
| [instructions](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/instructions/SKILL.md) | 识别研究或学习意图，选择具体 skill，安排组合任务的顺序，并传递论文身份、来源覆盖和目标文件。 | 工作流路由与交接上下文 |
| [literature-intake](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/literature-intake/SKILL.md) | 核实题名、DOI、Zotero key 和原 PDF 来源，查找既有论文目录，建立或更新文献卡，记录阅读目的与待办。 | 文献卡及来源指针 |
| [literature-summary](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/literature-summary/SKILL.md) | 为单篇论文生成简明中文总结，覆盖研究问题、方法、证据、贡献和局限；为主要结论保留原文定位，并保存相关图表裁图。 | `总结—…md`、`assets/summary-figures/` |
| [paper-deep-reading](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/paper-deep-reading/SKILL.md) | 重建单篇核心论文的论证逻辑，建立主张与证据对应关系，分析关键公式、研究设计、图表、结论边界及可迁移思路。 | `精读—…md`、`assets/deep-figures/` |
| [literature-compare](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/literature-compare/SKILL.md) | 围绕同一问题比较两篇或更多论文，整理假设、方法、数据、指标、结果与局限，说明可比性和证据差异。默认在聊天中交付，明确要求时保存。 | 比较矩阵及分析；按需保存比较笔记 |
| [paper-ingestion](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/paper-ingestion/SKILL.md) | 对单篇原 PDF 进行身份匹配和查重，协调外部 MinerU 解析，交给逐页复核流程，再将通过检查的解析包归档到对应论文目录。 | `paper.md`、解析清单、复核记录及 `assets/parsed/` |
| [paper-parse-review](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/paper-parse-review/SKILL.md) | 逐页对照原 PDF 检查解析文本、阅读顺序、图表与公式，在暂存区纠错并记录证据。保留准确图像，表格与公式采用 Markdown；未完成的复核保留待核对状态。 | 修正后的暂存解析包、`parse-audit.json`、`parse-review.md` |
| [course-learning](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/course-learning/SKILL.md) | 直接依据课程原件整理章节、回答问题和辅助推导，维护课程单元、来源定位及可检查的学习工件，区分资料整理与实际掌握程度。 | 课程笔记、概念 / 方法 / 问题卡及学习工件 |
| [knowledge-sync](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/skills/knowledge-sync/SKILL.md) | 根据当前 Vault 结构复用已有记录，更新双向链接、索引、MOC 和项目上下文；组合任务中负责跨笔记导航，保留前序 skill 的正文产物。 | 关联链接、索引、MOC 及上下文更新 |

各 skill 还包含 `agents/openai.yaml`；部分目录提供 `references/`、`scripts/` 或 `tests/`。具体文件以仓库当前目录为准。

## 使用示例

在新聊天中选择“学术研究助手”，提供资料及目标。下列示例中的路径或论文标识需要替换为自己的内容。

### 登记并总结论文

```text
请把这篇论文登记到我的 Obsidian 知识库，并生成总结。
论文：<Zotero item key、DOI 或原 PDF 路径>
Vault：<知识库路径>
先查找是否已有对应文献目录，复用现有目录，并为主要结论保留原文定位。
```

### 精读核心文献

```text
请精读这篇论文，重点分析研究假设、关键公式、图表证据和结论适用范围。
论文：<论文标识或原 PDF 路径>
Vault：<知识库路径>
将精读笔记保存到对应论文目录，并更新相关索引。
```

### 比较多篇论文

```text
围绕“<具体研究问题>”比较以下论文：<至少两篇论文的标识或路径>。
请用比较矩阵说明方法、数据、评价指标、结果和局限，并指出哪些结果可以直接比较。
只在聊天中回答，暂时不要入库。
```

### 整理课程并继续提问

```text
依据这份课件整理“<课程 / 章节>”的学习笔记。
课件：<原件路径>
Vault：<知识库路径>
保留页码或幻灯片定位，解释关键概念，并留下一项可检查的推导或例题。
```

### 解析、复核并归档全文

```text
请用 MinerU 解析这篇论文全文，逐页对照原 PDF 复核，再将通过检查的解析包归档。
PDF：<原 PDF 路径>
Vault：<知识库路径>
请报告复核覆盖、修正内容和未解决问题；复核未完成时保留暂存结果。
```

常见组合顺序：

| 目标 | 工作流 |
| --- | --- |
| 登记并总结 | `literature-intake` → `literature-summary` |
| 登记、精读并更新索引 | `literature-intake` → `paper-deep-reading` → `knowledge-sync` |
| 解析并归档全文 | `paper-ingestion` 解析与暂存 → `paper-parse-review` 逐页复核 → `paper-ingestion` 归档 |
| 整理课程并更新跨课程索引 | `course-learning` → 按需 `knowledge-sync` |

## 产物与来源规则

单篇论文的不同产物各有用途，并复用同一份已确认的论文身份与目录：

| 产物 | 记录内容 |
| --- | --- |
| 文献卡 | 书目身份、原件位置、来源覆盖及阅读目的 |
| 总结笔记 | 便于回顾的研究核心、主要结果与价值 |
| 精读笔记 | 论证过程、证据强度、公式图表与研究迁移分析 |
| 全文解析包 | 核对后的正文和图像，以及解析来源和逐页复核记录 |

新建总结和精读通常使用 `20_文献/<安全处理后的论文原题>/`，已有匹配目录会被复用；具体位置以当前 Vault 规则和任务指定路径为准。

- **内容依据**：论文科学内容以选定的原 PDF 为准，课程内容以原讲义、课件、教材或习题为准。Zotero 提供书目与附件身份，默认只读；解析文本用于导航和提取辅助。
- **来源可追溯**：重要主张保留页、节、图、表或公式定位；材料不完整时说明覆盖范围，并区分原文与推断、分析、假设。
- **按任务写入**：登记、总结、精读和解析是分别请求的产物。只需一次性回答时，可以明确写“只在聊天中回答，暂时不要入库”。
- **增量维护**：写入前查重并读取当前规则，保留已有笔记与用户内容；原 PDF 和课程原件通常保留在原位置。
- **更新时机**：课程和知识库 skills 在任务调用时重新识别当前目录与规则，知识库更新由任务触发。
- **验证范围**：校验脚本检查文件结构、链接、格式和记录中的复核覆盖。内容是否准确仍依赖对原 PDF 的实际逐页检查。

## 维护与验证

后续功能维护以本仓库的插件目录为源码位置。详细约定见 [MAINTENANCE.md](plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/MAINTENANCE.md)，历史变化见 [CHANGELOG.md](CHANGELOG.md)。

总结与精读共用校验逻辑由插件根目录的 `scripts/validate_note.py` 维护；对应 skill 内的同名脚本是转发入口。修改插件功能时同步更新两份清单的版本，并运行相关检查。提交 GitHub 或更新源码后，需要通过 marketplace 重新安装并核验已安装版本。

在仓库根目录运行测试：

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

测试使用独立临时样本，不操作真实 Zotero 或 Obsidian 库。仓库保存插件源码、资源及维护文档；个人环境配置、令牌、论文原件、Vault 内容和安装缓存应保留在各自环境中。
