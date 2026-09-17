# Cross-Source Contradiction Engine

Inspected sources: `database/schema.sql`, `backend/models.py` and
`backend/schemas.py` (both empty), `backend/database.py`, the rule engine,
negative-space engine, workflow auditor, and Alpha Bank's alerts, cases,
investigations, escalations, and telemetry CSVs.

Cases link to alerts by `alert_id`; the detector also requires matching
`entity_id`. Investigations and escalations independently link to cases by
`case_id`. Escalations do not link directly to investigations. Telemetry links
to assets, so it is not used in these case timestamp checks.

| Rule | Strict comparison |
| --- | --- |
| C001 | `cases.closed_at < investigations.completed_at` |
| C002 | `investigations.started_at < cases.opened_at` |
| C003 | `escalations.escalated_at > cases.closed_at` |
| C004 | `alerts.timestamp > cases.opened_at` |

C005: **SKIPPED - insufficient source evidence.** There is no investigation
status field. A NULL `completed_at` may reflect missing data and cannot reliably
prove an incomplete investigation, even when the case status is CLOSED.

These are prototype supervisory review checks, not proof of misconduct.
Backfilled case records, delayed escalation recording, and timestamp errors
may explain findings. C003 compares recorded timestamps regardless of the
`escalated` flag; it does not assert that escalation actually occurred.
All finding priorities default to HIGH via `RULE_SEVERITIES`. Original alert
severity is retained separately as `alert_severity`. No risk score is produced.

## Interface and evidence

`detect_cross_source_contradictions(rows=None, entity_id=None)` reads local
PostgreSQL by default using the existing database engine. Explicit joined rows
support isolated tests without database dependencies. Their keys match the
aliases in the service's `QUERY`. `entity_id` optionally filters either source.

Each finding contains rule/type, entity/case/alert/asset IDs, source record IDs,
the actual compared timestamps under table-qualified field names, and a reason
explaining why a supervisor should inspect the records. Timestamps serialize
to ISO strings. Results are sorted deterministically. Findings repeated by
multi-investigation/multi-escalation joins are deduplicated without collapsing
distinct source records.

Missing linked records, NULL/invalid timestamps, and mixed timezone-aware/naive
timestamp pairs are unassessable and skipped. Equal timestamps do not trigger
findings. Zero findings does not prove data completeness. The current schema
uses timestamps without time zones; the engine does not invent timezone data.

## Run

From the repository root:

```bash
cd backend
source venv/bin/activate
python3 test_contradiction_engine.py
python3 test_contradiction_engine.py --entity E001
python3 test_contradiction_engine.py --csv --check-ground-truth
python3 -m unittest test_contradiction_engine_unit test_workflow_auditor_unit test_negative_space_unit
python3 test_rule_engine.py
python3 validate_negative_space.py
python3 test_workflow_auditor.py
```

CSV mode reads unmodified operational files. The optional ground-truth check
runs only after detection and is not part of the detector.

## Verified results

Alpha Bank produces **0 contradictions** in both CSV and local PostgreSQL.
All 31 unit tests pass: 13 contradiction tests and 18 existing tests. Synthetic
in-memory fixtures exercise every supported rule, combined violations, NULLs,
missing records, equal timestamps, duplicate joins, and entity filtering.
The existing five critical case detections, R005 validation (TP=2, FP=0, FN=0),
and workflow report for E001-C0081 retain their results.

Ground-truth validation for cross-source contradictions is not currently
possible because the dataset contains no labelled contradiction scenarios.
No precision/recall/F1 is reported for this engine.

For the separate scenario injector, add labelled scenarios for an investigation
completed after case closure, an investigation started before case opening,
an escalation timestamp after closure, and an alert timestamp after case opening.
Include combined violations and equal-timestamp normal controls. Preserve the
entity, case, and relevant child record IDs in labels for evaluation matching.
These scenarios have not been inserted into operational data.

Only the new service, report, unit tests, and this document were added. Existing
engines, schema, operational data, APIs, frontend, and scoring were not modified.
