# Experimental pipelines reference

This folder is a frozen reference copy of the experimental pipeline work from
branch `dev_set_curation` at commit `8a1930e`.

The active branch `refactor/modular-pipeline-composition` starts from
`upstream/main` (`5f112d0`), so these files are intentionally not part of the
runtime implementation. They are here only to guide the modularization.

Included:

- Experimental `src/gensie` modules for inline reasoning, schema enrichment,
  self-consistency, judge aggregation, super FSP, tracing, and verbatim entity
  extraction.
- Focused tests for those modules.
- Pipeline proposal documents that describe the experimental behavior.

Excluded:

- Generated evaluation outputs.
- Dataset expansions and result JSON files.
- Unrelated repository changes from `dev_set_curation`.
