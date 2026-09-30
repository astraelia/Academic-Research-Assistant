# Obsidian 文献总结输出模板

## 目录与资源

当用户要求按研究方向归档时，输出目录为：

    <vault-root>/20_文献/<研究方向>/<安全文献题名>/
    ├── 总结—<安全文献题名>.md
    └── assets/summary-figures/
        ├── F001.png
        ├── T001.png
        └── E001.png

否则使用 `<vault-root>/20_文献/<安全文献题名>/`。仅使用相对图片链接，例如：

`<安全文献题名>` 是论文原题仅经文件系统必要字符处理后的名称；目录与 `总结—<安全文献题名>.md` 必须使用同一名称。研究方向只决定上级目录，不把英文原题改写成中文短标题。

    ![Fig. 1：模型流程](assets/summary-figures/F001.png)

不要默认覆盖已有的用户笔记或图片。

## Frontmatter

```yaml
---
title: "论文原题"
title_zh: "中文题名；无可靠译名时保留原题"
note_type: "literature-summary"
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
created: "YYYY-MM-DD"
tags: ["文献阅读", "文献总结"]
---
```

## 正文骨架

```markdown
<h1 style="color:#193c47; background-color:#eef9fd; padding:10px;">
（年份）论文原题（中文题名）｜文献总结
</h1>

> 资料范围：全文 / 部分全文 / 仅元数据与摘要
> 事实依据：PDF 优先；MinerU 仅作辅助解析（如使用）

## 📜 研究核心
### 🎯 一句话概括
### ❓ 核心研究问题与 Research Gap
### ⚙️ 核心内容与方法路线
### 💡 核心创新
### 📌 核心结论
### 🧩 主要不足

## 🔁 研究内容
### 🌍 研究背景与研究对象
### 💧 数据、材料或研究场景
### 🔬 实验 / 数值分析 / 理论推导
### 📊 关键结果与图表证据

## 🧠 文献价值
### ⭐ 学术与工程价值
### 🔗 与已有研究的关系
### 📚 后续值得阅读

## 🤔 阅读总结
### 🙋 最重要的知识点
### 📌 尚未解决的问题
### 💭 【分析】研究启发
### 📝 一句话记忆

## 图像索引
## 证据索引
| 主张或结果 | 证据类型 | PDF 定位 | 图/表/公式 |
|---|---|---|---|
```

每个核心事实、数字、图表解读和限制都要带 `[论文：PDF p. N，Section/Fig./Table/Eq.]` 形式定位。只嵌入实际讨论的紧凑裁切图；图像索引列出尚未在正文嵌入的主图。
