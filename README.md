# Academic-Research-Assistant

学术研究助手

本地 Codex 插件的维护与备份仓库。插件整合文献登记、总结、精读、比较、课程学习及 Obsidian 知识库维护。

插件身份为 `gpt-182946e32ffd8b365610c7f81edfdf3d`，本地 marketplace 为 `astraskye-local`。最初复制自已安装的云端插件 0.4.3；保留名称、默认提示词、9 个 skills 和文件布局，插件图标使用用户提供的薄荷绿 AI 少女 SVG。0.4.4 修复代码审查发现的校验与查重问题。

## 目录

```text
.agents/plugins/marketplace.json       本地插件目录
plugins/gpt-182946e32ffd8b365610c7f81edfdf3d/
  plugin.json                         Agent Plugins 清单
  .codex-plugin/plugin.json           Codex 兼容清单
  skills/                            9 个工作流及支持文件
  scripts/                           总结与精读共用校验器
  tests/                             笔记与文献身份回归测试
  references/                        论文身份及交接契约
  assets/                            插件图标
  MAINTENANCE.md                      插件维护约定
docs/code-review.md                   审查范围、修复与验证记录
CHANGELOG.md                          版本记录
```

## 安装

将整个仓库克隆到稳定的本地目录，然后在仓库根目录运行：

```powershell
codex plugin marketplace add .
codex plugin add gpt-182946e32ffd8b365610c7f81edfdf3d@astraskye-local
codex plugin list --marketplace astraskye-local --json
```

在插件界面选择“astraskye 本地插件”来源。若界面未刷新，重启 Codex 并在新聊天中使用。

本插件没有捆绑 MCP 服务器或账号凭据。Zotero、MinerU 等外部工具需要在使用者的环境中另行配置；按原工作流发现 Vault、原始 PDF、当前规则及工具能力。课程阅读直接以课件或教材为依据，仅明确要求论文全文解析、OCR 或 MinerU 时使用解析流程。

## 维护与测试

以本仓库中的插件目录作为源码，修改对应 skill 或脚本。不要直接修改 Codex 安装缓存。总结/精读共用校验逻辑只维护 `scripts/validate_note.py`；skill 中的两个同名入口负责转发。

测试依赖 Python 3.10 或更高版本。PDF 审查测试还需要 PyMuPDF：

```powershell
py -3 -m pip install -r requirements-dev.txt
$pluginDir = './plugins/gpt-182946e32ffd8b365610c7f81edfdf3d'
py -3 -B -m unittest discover -s "$pluginDir/tests" -p 'test_*.py'
py -3 -B -m unittest discover -s "$pluginDir/skills/paper-parse-review/tests" -p 'test_*.py'
```

测试使用插件目录下的独立临时样本，不操作真实 Zotero 或 Obsidian 库。更新时同步递增两份清单的版本，运行相关测试，再通过本地 marketplace 重新安装并核验版本。安装与 GitHub 备份是两个操作；提交仓库本身不会刷新安装缓存。

```powershell
git add .
git commit -m "Describe the change"
git push origin main
```

此仓库保存插件源码和图标。个人环境配置、令牌、论文 PDF、Vault 内容、临时输出及安装缓存不属于仓库内容。

## Skills

| Skill | 用途 |
| --- | --- |
| `instructions` | 意图路由与工作流交接 |
| `literature-intake` | 登记文献身份与来源指针 |
| `literature-summary` | 来源可追溯的论文总结 |
| `paper-deep-reading` | 批判性精读、公式与图表分析 |
| `literature-compare` | 多篇论文的指定问题比较 |
| `paper-ingestion` | 核验后归档 MinerU 论文解析包 |
| `paper-parse-review` | 原 PDF 逐页复核与入库门禁 |
| `course-learning` | 课程原件学习与学习记录 |
| `knowledge-sync` | 跨笔记链接、索引与知识库维护 |
