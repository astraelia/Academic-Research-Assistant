---
name: instructions
description: Route research and study requests across this plugin's literature, course, and Obsidian skills. Use whenever 学术研究助手 is invoked.
---

# 学术研究助手

根据用户的任务选择本插件 `skills/` 内的具体 Skill；需要组合时按下表交接。单独调用某个 Skill 时，以该 Skill 的规则为准。不要把独立安装的同名 Skill 当成本插件的正式版本；迁移期两者可能同时被发现。

| 用户意图 | 本插件内的 Skill 与顺序 |
| --- | --- |
| 把一篇论文加入知识库、登记来源 | `literature-intake` → `terminology-management` 共享完成检查 → 按需 `knowledge-sync` |
| 总结一篇论文 | `literature-summary`，交接 `terminology-management` 共享完成检查；要求登记来源时先 `literature-intake` |
| 精读一篇论文 | `paper-deep-reading`，交接 `terminology-management` 共享完成检查；要求登记来源时先 `literature-intake` |
| 精读并加入知识库 | `literature-intake` → `paper-deep-reading` → 按需 `knowledge-sync` |
| 比较多篇论文 | `literature-compare`；缺少可靠来源时先逐篇确认身份，按需用总结或精读补证据 |
| 解析并归档论文全文 | `paper-ingestion` → `paper-parse-review` 逐页核对 → `paper-ingestion` 归档 |
| 课程资料入库、章节整理、基于课件解答 | `course-learning`；明确要求更新跨课程索引时接 `knowledge-sync` |
| 学术术语入库、查询、补充或检查术语库 | `terminology-management`；实际写入后按需 `knowledge-sync` |
| 整理知识库、更新双链或 MOC、查重 | `knowledge-sync` |

“加入知识库”通常指登记文献卡与来源指针；不意味着解析全文、复制 PDF、自动生成总结或精读。只在用户明确要求解析全文、OCR 或 MinerU 时调用 `paper-ingestion` 和外部 MinerU 能力。课程资料阅读与整理直接以原件为依据，不调用 MinerU 文献解析流程。若用户明确说“暂时不要入库”或只要一次性回答，停止在聊天结果，不写知识库。

三个文献入口保存到已配置术语库的 Vault 时，都读取 [术语交接规则](../../references/terminology-handoff.md)。同一论文任一阶段首次成功完成后，其他阶段和后续聊天跳过术语提取、外部核验与入库；可以查询已有术语统一表达。资料不足或中断不算完成。术语库初始位置为 Vault 根目录的 `61_学术术语库`，改名后动态发现。课程、普通翻译和独立全文解析不自动触发此流程。

## 多 Skill 交接

开始写入前，确定唯一 Vault、当前 `AGENTS.md`、相关模板与索引。对一篇论文只建立一份身份上下文：Zotero item key、DOI、PDF 路径及 SHA-256（可得时）、规范题名、匹配的既有文献目录、来源覆盖范围和目标产物。读取 [论文身份与交接契约](../../references/paper-identity-and-handoff.md) 处理复用、冲突和写入归属。课程任务传递课程、原件路径、页/幻灯片/章节定位、目标单元和现有记录；不能只凭文件名推断课程身份。

每个产物只有一个写入负责人：`literature-intake` 写文献卡；`literature-summary` 写总结及其图片；`paper-deep-reading` 写精读及其图片；`paper-parse-review` 写暂存复核记录；`paper-ingestion` 写核验过的解析包；`course-learning` 写课程单元与学习工件；`literature-compare` 写比较笔记；`terminology-management` 写术语卡和论文术语处理记录；`knowledge-sync` 写跨笔记链接、索引、MOC 和当前上下文。后一步读取前一步的路径与证据状态，先检查已有文件，再增量更新。不要让两个 Skill 同时编辑同一个文件，也不要用后一步重新生成前一步的笔记。

## 学术证据与权限

- 论文内容以所选原 PDF 为准；Zotero 提供书目和附件身份，默认只读。解析文本是导航辅助，不是第二份科学证据。课程内容以原讲义、课件、教材或练习为准。
- 区分原文事实、作者主张、【推断】、【分析】和【假设】。不虚构作者、DOI、页码、图表、公式、数据或结论；证据不足时标明范围。
- 保留用户的原始资料和已有笔记。复制课程原件、覆盖现有笔记、改动 Zotero 或上传资料，须符合用户指令与当前 Vault 规则。
- 对开放式研究设计、文献综述与概念解释，在没有更具体 Skill 时直接回答；给出可核查的依据和局限，不强行创建笔记。

结束时说明实际调用的 Skill、写入的文件、来源覆盖、验证结果和仍待核对的部分。不要把未执行的解析、逐页复核或知识库更新写成已完成。
