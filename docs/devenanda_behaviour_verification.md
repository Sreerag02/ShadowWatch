# Devenanda behaviour analytics verification

Review date: 2026-09-18. Scope: the supplied Member 3 Behaviour Analytics
Workplan, compared against operational CSVs, PostgreSQL schema, implementation,
shared API and ground-truth evaluation.

**Status:** implementation repairs and automated unit/PostgreSQL verification complete.
Detection quality
is not fully calibrated: R006 produces many unlabelled findings and R007/R009
have no matching positive labels in the current datasets. Publishing to a
`behaviour-analytics` branch was not performed; changes remain local.

## Gaps repaired

- R006 now detects copied substantive notes across distinct cases without
  requiring repeated sentences inside a note. Empty vocabulary and missing text
  are safe; comparisons stay within the organization. Vectorized comparison
  removes repeated DataFrame lookups without changing detections.
- R007 uses actual investigation timestamps, both short and long anomalies, and
  peer baselines grouped by entity/severity/category. Removed the dependency on
  a closure-reason phrase and the CRITICAL-only restriction. Candidate cases do
  not influence their own baseline.
- R008 retains complete qualifying windows and later separate episodes, counts
  distinct alerts, and prevents joins across organization ownership.
- R009 combines indicators by entity/case and carries their structured evidence
  and explanations into the common finding format.
- Connected all four rules to the shared request session and findings API.
  Case filtering preserves the full comparison population. Core R001–R005
  algorithms and source datasets were not modified.
- Added the missing scikit-learn dependency. Replaced print-only edge checks
  with assertions and unified organization-aware reports/evaluators.
- Evaluation no longer treats R004 fast-closure labels as R007, drops missing
  observations from false negatives, or ignores asset-only recurrence labels.
  Labels are loaded only after operational detection.

## Verification evidence

- 77 unit/contract tests passed, including 15 detector/evaluation tests and a
  shared-API regression that exercises all R006–R009 on synthetic records.
- All five source datasets passed schema, relationship, uniqueness and
  cross-entity validation.
- Final evaluator output was byte-for-byte identical before and after the
  comparison-loop optimization.
- Read-only PostgreSQL verification passed for all five organizations: source
  values, row counts and entity ownership match the normalized CSVs.
- Exhaustive API verification passed: five organization feeds, all 498 case
  responses and all 152 asset telemetry responses, including stable finding
  identifiers, global/entity/case agreement, summaries, filtering and 404s.
- Existing multi-entity analytics and Alpha core-rule regressions passed.

The live API returns 455 individual findings: R001 5, R002 22, R003 34, R004 18,
R005 4, R006 329, R007 11, R008 20 and R009 12. Entity totals are Alpha 101,
Beta 37, Gamma 87, Metro 144 and PowerGrid 86. These are review findings, not
455 confirmed incidents or an accuracy measure.

Detector-level results (R008 counts windows, not API case-expanded findings):

| Organization | R006 | R007 | R008 | R009 |
| --- | ---: | ---: | ---: | ---: |
| Alpha Bank | 90 | 1 | 0 | 1 |
| Beta Bank | 12 | 6 | 1 | 4 |
| Gamma Bank | 66 | 0 | 0 | 0 |
| Metro Telecom | 95 | 0 | 3 | 5 |
| PowerGrid Utility | 66 | 4 | 0 | 2 |

## Ground-truth results and remaining work

| Organization / rule | TP | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alpha / R006 | 0 | 90 | 1 | 0 | 0 | 0 |
| Alpha / R008 | 0 | 0 | 1 | 0 | 0 | 0 |
| Beta / R006 | 4 | 8 | 0 | 0.3333 | 1 | 0.5000 |
| Beta / R008 | 4 | 1 | 0 | 0.8000 | 1 | 0.8889 |
| Metro / R006 | 6 | 89 | 0 | 0.0632 | 1 | 0.1188 |
| Metro / R008 | 4 | 3 | 0 | 0.5714 | 1 | 0.7273 |
| PowerGrid / R006 | 0 | 66 | 3 | 0 | 0 | 0 |
| PowerGrid / R008 | 0 | 0 | 1 | 0 | 0 | 0 |
| Labelled units overall | 18 | 257 | 6 | 0.0655 | 0.7500 | 0.1204 |

These numbers compare findings to the supplied labels, not independently
adjudicated misconduct. Case and asset evaluation units follow each dataset's
label scope. Unlabelled predictions in an evaluated organization/rule count as
FP. Gamma has no matching positive behaviour labels; R007 and R009 have none
across any organization, so they are excluded from overall accuracy rather than
assigned misleading metrics. Gamma also lacks usable investigation timestamps.

Current normal synthetic notes reuse templates extensively; generic text
similarity cannot establish superficial handling by itself. R006 needs reviewed
examples and a defensible policy for acceptable templates before deployment.
R008 misses the supplied Alpha/PowerGrid recurrence labels under the documented
four-alert/ten-day/same-category criteria. Review those episodes and calibrate
windows/counts against a separate evaluation set; do not change source records
or tune directly to injected scenario phrases to force perfect metrics.

R007/R009 need representative labelled short/long and combined-behaviour
examples for measured accuracy. Their logic is covered by synthetic unit/API
tests, which is a narrower claim. Threshold calibration is explicitly a later
workplan item, but these limits prevent a production-accuracy sign-off.

The workplan's local implementation, explanation, evaluation and integration
deliverables are addressed. Full delivery still includes calibration/label
review and the requested team's Git branch handoff. No commit or push was made.

## Reproduce

From the repository root:

```bash
python3 tests/validate_all_datasets.py
cd backend
venv/bin/python -m unittest test_behaviour_unit test_backend_api_unit test_multi_entity_unit test_contradiction_engine_unit test_workflow_auditor_unit test_negative_space_unit
venv/bin/python verify_multi_entity_db.py
venv/bin/python test_backend_integration.py
venv/bin/python test_multi_entity_analytics.py
venv/bin/python test_behaviour_analytics.py --summary
venv/bin/python validate_behaviour_ground_truth.py --json
```

Database checks are read-only. Unit/contract tests use isolated SQLite. The JSON
evaluation includes the exact false-positive and false-negative identifiers.
See [behaviour analytics](behaviour_analytics.md) for functions, thresholds,
evidence fields and API count semantics.
