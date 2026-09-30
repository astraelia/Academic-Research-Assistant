# Parsed-paper bundle contract

This contract applies to one paper folder, whether already present or newly created:

```text
<vault>/<literature-root>/[direction/]<paper-folder>/
├── paper.md                  # corrected MinerU Markdown, with relative image links
├── parse-manifest.json       # identity, parse provenance, and review state
├── parse-audit.json          # produced and checked by paper-parse-review
├── parse-review.md           # generated readable page/correction record
└── assets/parsed/            # usable figure images referenced by paper.md; PDF crops only for figure corrections
```

Other files in the folder belong to their own workflows and must be preserved. The original PDF normally remains in Zotero or at its supplied path. `paper.md` may contain full paper text, so create it only when the user has asked to archive a parsed paper.

## Manifest

Write UTF-8 JSON with these fields. Use `null` for unavailable optional values rather than inventing them. Keep paths relative to the paper folder except `identity.source_pdf`, which is the original external source path.

```json
{
  "schema_version": 1,
  "identity": {
    "title": "Exact paper title",
    "doi": "10.xxxx/xxxxx",
    "zotero_item_key": "ABCD1234",
    "source_pdf": "<PDF_PATH>",
    "pdf_sha256": "64 lowercase hexadecimal characters"
  },
  "parse": {
    "tool": "MinerU",
    "version": "4.x",
    "tier": "standard",
    "remote": false,
    "locator": "doc:.../tier:standard",
    "completed_at": "YYYY-MM-DD",
    "page_count": 3
  },
  "review": {
    "status": "verified",
    "checked_pages": [1, 2, 3],
    "open_issues": [],
    "reviewed_at": "YYYY-MM-DD"
  },
  "artifacts": {
    "paper_md": "paper.md",
    "asset_dir": "assets/parsed",
    "review_log": "parse-review.md",
    "audit": "parse-audit.json"
  }
}
```

For a new import, copy `review.status`, `checked_pages`, and `open_issues` from this plugin's `paper-parse-review` audit. `verified` requires its final gate to pass against the original PDF; the bundle validator alone does not establish this. `page_count` is the PDF's actual page count, not a count guessed from a truncated Markdown export. Do not keep a second summary/deep-reading status here: the actual note files show whether those workflows ran.

## Review log

`parse-audit.json` and `parse-review.md` are owned by this plugin's `paper-parse-review`; read its [review contract](../../paper-parse-review/references/review-contract.md) before editing them. Its gate verifies the recorded page/visual coverage, corrections, source PDF, and figure links; tables and equations remain Markdown text/math rather than image assets.
