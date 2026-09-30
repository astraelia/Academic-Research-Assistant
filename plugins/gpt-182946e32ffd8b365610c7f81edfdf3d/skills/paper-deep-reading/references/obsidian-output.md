# Obsidian 文献精读输出模板

## 目录与资源

当用户要求按研究方向归档时，输出目录为：

    <vault-root>/20_文献/<研究方向>/<安全文献题名>/
    ├── 精读—<安全文献题名>.md
    └── assets/deep-figures/
        ├── F001.png
        ├── T001.png
        └── E001.png

否则使用 `<vault-root>/20_文献/<安全文献题名>/`。图片必须采用相对路径，例如：

`<安全文献题名>` 是论文原题仅经文件系统必要字符处理后的名称；目录与 `精读—<安全文献题名>.md` 必须使用同一名称。研究方向只决定上级目录，不把英文原题改写成中文短标题。

    ![Fig. 1：模型流程](assets/deep-figures/F001.png)

## Frontmatter

```yaml
---
title: "论文原题"
title_zh: "中文题名；无可靠译名时保留原题"
note_type: "paper-deep-reading"
research_direction: "PDF 支持的中文研究方向；未分类时为未分类"
authors: ["姓, 名"]
year: 2026
venue: "期刊或会议"
doi: "10.xxxx/…"
zotero_item_key: "ABC12345"
zotero_attachment_key: "DEF67890"
zotero_uri: "zotero://select/library/items/ABC12345"
source_pdf: "PDF 文件名"
mineru_status: "已交叉核验 | 未使用 | 不可用"
source_coverage: "full-paper | partial-paper | abstract-metadata-only"
extraction_confidence: "high | mixed | low"
locator_mode: "page-grounded | structure-grounded | source-limited"
paper_type: "methods"
created: "YYYY-MM-DD"
tags: ["文献阅读", "文献精读"]
---
```

## 正文骨架

```markdown
<h1 style="color:#193c47; background-color:#eef9fd; padding:10px;">
（年份）论文原题（中文题名）｜文献精读
</h1>

> 资料范围：全文 / 部分全文 / 仅元数据与摘要
> 定位模式：页码可追溯 / 结构可追溯 / 来源受限
> 事实依据：PDF 优先；MinerU 仅作辅助解析（如使用）

## 🧭 01｜论文定位
### 🎯 一句话概括
### 🌍 研究背景、核心问题与 Research Gap
### 🎯 研究目标与作者声称的贡献
### 🗺️ 论文地图与核心概念

## 🧠 02｜研究逻辑
### 🔗 主论证链
### 🧩 研究框架：输入 → 处理 → 输出
### ⚠️ 关键假设及其成立条件

## 📚 03｜背景与问题
### 📖 相关研究路线与本文定位
### 🕳️ 作者明确的缺口 / 【推断】可归纳缺口
### 🎯 本文真正需要证明的事情

## 🧮 04｜理论、方法与公式
### ⚙️ 方法总览与核心模块
### 🧮 关键公式
### 🔄 可执行方法流程

## 🔬 05｜实验/数值设计与证据链
### 🧪 数据、样本、材料或研究场景
### 🎛️ 实验设置、对照、基线、参数与指标
### 📌 主张—证据矩阵
| 主张 | 比较与条件 | 结果 / 数值 | 可支持的结论 | 不可支持的更强结论 | 定位 |
|---|---|---|---|---|---|

## 🖼️ 06｜图表精读
## 🧩 07｜结论边界与批判性分析
### 📜 作者明确承认的局限
### 🔎 【分析】潜在问题与替代解释
### 📏 结论成立、风险外推与不适用条件

## 💡 08｜研究迁移与最终精读结论
### 🙋 最重要的知识与可迁移方法
### 💭 【假设】对用户研究的候选启发
### 📝 可脱离原文复述的一段话
### ⚡ 一句话记忆

## 图像索引
## 证据索引
| 关键结论 | 来源定位 | 证据强度 | 备注 |
|---|---|---|---|
```

每项主张都要区分 PDF 事实、【推断】、【分析】和【假设】；公式保留为一行完整 `$$...$$`，不能可靠转写时嵌入公式裁切图并声明以原图为准。
