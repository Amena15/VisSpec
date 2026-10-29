# Repository provenance for JAIT submission

This repository contains the code and evidence trail for the VisSpec
manuscript submitted to JAIT.

## State at submission

- Branch: production4
- HEAD: 9b0a393b1fd0f0d4624a4f0deed51e7bcd3923e2
- Tag: v-jait-submission-code

## What is present
- scripts/04_rq3_traceability_experiment.py — archived tombstone
- scripts/generate_reproducibility_evidence.py — evidence generator
- scripts/verify_manuscript_consistency.py — manuscript verifier
- elements.json — 72 element-condition records
- ratings.csv — 138 grounding ratings
- paper_assets_final/reproducibility_evidence.md — generated evidence
- paper_assets_final/rq3_unreproducible.md — withdrawn-claim history

## What is not recoverable
- scripts/generate_rq3_data.py — the original generation pipeline
  was deleted during RQ3 cleanup. The file is not present in any
  git commit, reflog, stash, or branch as of 2026-10-29. A stub was
  created during revision but has been removed rather than shipped,
  because a non-functional placeholder would misrepresent the state.

## What this means for the paper
No claim in the manuscript depends on re-running generate_rq3_data.py.
The internal 36-case results are backed by the frozen prediction files
reported in paper_numbers.md and the associated saved outputs. The
RQ3 traceability experiment is already disclosed in the manuscript as
unreproducible from retained artifacts.

## For reviewers
If you need to reproduce any reported result, contact the corresponding
author for the frozen predictions and outputs. Do not attempt to
re-run the pipeline; the generation script is not retained.