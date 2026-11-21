# PR 176: fix: make retrieval ablation honest about manual stressors

Private team repository `barq-sprints-agentic-incident-resolution-platform-g1`, authored by me. **Closed, not merged.**

- State: CLOSED (never merged)
- Base: `main`
- Head branch: `fix/eval-ablation-shapes`
- Opened: 2026-09-28T19:21:32Z; closed: 2026-09-28T19:32:50Z
- Size: +103 / -8 in 2 files
- Diff: `pr-176-retrieval-ablation-honesty.diff` (plain `git diff`-style, no author data)


## Description (as written on the PR)

## What changed

The versioned evaluation file mixes 29 S2.4 article-ID incidents with six S2.6 manual-section stressors. The ablation runner previously crashed when it reached the stressors. Their expected values (`1.1`, `12.2`, `3.3`, `C`) are section IDs, not KB article IDs; converting them into article matches would fabricate six failures. The runner now reports the six exclusions and scores the 29 article-ID cases. It also uses the same retrievable workflow states as application search, including human-resolved articles.

## Verification

- The full ablation completed against local Qdrant with all three retrieval modes. Accuracy margin of hybrid reranked over dense only: +0.0345; context precision margin: -0.0552. These match the existing retrieval report.
- Three new tests cover the checked-in dataset split, section-ID exclusion, and unknown-record failure.
- Ruff, format, mypy, and the default pytest suite passed locally. The repo's PostgreSQL/Redis integration suite is covered in CI.

This does not score the manual stressors. That requires the manual corpus and an explicit section-to-article mapping, and #172 remains separate.
