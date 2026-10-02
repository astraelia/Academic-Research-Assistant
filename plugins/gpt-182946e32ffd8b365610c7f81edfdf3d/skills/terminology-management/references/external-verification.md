# 外部核验与个人收录

Read this when a candidate needs a definition, translation, abbreviation or scope check. Follow the current Vault's source guide; these are starting points and need runtime verification, not a fixed database ranking.

| Scope | Public entry point | Check |
| --- | --- | --- |
| Chinese professional names and bilingual correspondence | [术语在线](https://www.termonline.cn/about) | Specific entry, discipline, originating publication and approval status; an about page does not verify a term |
| Building materials, structural systems and taxonomy | [GEM taxonomy glossary](https://taxonomy.openquake.org/) | The selected taxonomy version and actual entry; on 2026-10-02 the entry point states v2 alignment |
| Seismic hazard, fragility and risk analysis | [OpenQuake glossary](https://docs.openquake.org/oq-engine/manual/master/user-guide/extras/glossary-of-terms.html) | Specific heading/permalink and document version; distinguish software/model context from general usage |
| PBEE and structural performance assessment | [PEER methodology](https://peer.berkeley.edu/node/189) | Locate the actual report, guide or paper defining the concept rather than citing an institutional home page |
| Seismology, ground motion and site concepts | [USGS earthquake glossary](https://www.usgs.gov/glossary/earthquake-hazards-program) | Specific definition and technical conditions; use a precise entry or document locator |

Use browsing/search or the user's available connector to find and **read** the relevant entry. Do not rely on an untested API, a search excerpt, or the institution's name alone. A source can contain outdated terminology or a scope error; compare it against the actual paper and record disagreements. Expand the route for other domains only as needed.

Every external evidence object records `source`, `entry`, `url`, `version`, `checked_at` (YYYY-MM-DD), `role` and `read_verified: true`. `version` can state “页面未注明版本” when that is what was observed. Save a precise URL/heading and a short paraphrase, never invented publication information. A required source that cannot be read blocks completion unless a reliable alternative actually resolves the check; a substantive ambiguity with recorded alternatives becomes a pending candidate.

Only selected personal term cards are saved. Do not import/mirror whole external glossaries, crawl categories into the Vault, save complete web pages or ingest their JSON/XLSX/code lists. Evidence URLs in frontmatter are specific sources actually used, not every site searched.

Worthiness depends on the user's research/reuse/writing/ambiguity needs. External inclusion cannot substitute for that judgment. External absence can accompany a well-founded original-paper concept. Preserve conflicts and source-specific meanings instead of flattening them into one authoritative definition.
