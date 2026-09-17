# Behaviour analytics handoff

R006–R009 run offline on operational investigations, cases and alerts. The source
schema is `database/schema.sql`: `analyst_notes`, `started_at`, `completed_at`,
case/alert identifiers and alert entity/asset/category/severity fields. Entity
ownership comes from the case because investigations do not have `entity_id`.
Ground truth is never detector input. Findings request human review, not a
conclusion that an analyst acted improperly.

## Prototype configuration

The separate detector functions in `backend/services/behaviour_analytics.py`
accept threshold arguments. Module constants supply defaults for
`analyze_behaviour(investigations, cases, alerts)` and the API.

| Rule | Default and behaviour |
| --- | --- |
| R006 | Normalize whitespace/case, at least 6 words, TF-IDF with English stop words, cosine similarity >= 0.90 across at least 3 distinct cases in the same entity. One finding per qualifying investigation. Internal sentence repetition is not required. |
| R007 | Actual investigation minutes compared with a median of at least 5 other cases in the same entity/severity/category. Each peer case contributes one median duration. Candidate case excluded. Flag ratios < 0.25 or > 4.0. |
| R008 | At least 4 distinct alerts linked to cases on the same entity/asset/category within an inclusive 10-day window. Retain maximal qualifying windows and complete IDs; overlapping windows can exist. |
| R009 | At least 2 distinct R006–R008 indicators affecting the same entity/case. Preserve the contributing reasons and structured evidence; no risk score. |

Missing/blank/short or all-stopword notes do not crash the engine. Missing,
unparseable or negative durations are skipped; sparse or zero baselines are
skipped. Missing asset/category/timestamp prevents recurrence assessment. Exact
duplicate records are collapsed, conflicting duplicate IDs raise an explicit
error, and cross-entity links do not participate in analysis. Missing required
columns raise an explicit error. Skipping insufficient data is not evidence of
normal behaviour; Gamma's missing investigation timestamps prevent R007 analysis.

## API integration

`get_behaviour_findings(case_id=None, db=None, entity_id=None)` in
`services/behaviour_finding_service.py` reads through the shared SQLAlchemy
session. Supply `db` for request-scoped use. Legacy callers without a session
receive a managed session that is closed afterward. The shared findings service
adds stable IDs and combines these records with existing core findings.

Responses contain rule/problem/entity/case/alert/asset identifiers, a reason and
structured evidence. R006 evidence includes the focal investigation, related
investigations/cases, similarity, threshold, count and note excerpt. R007 includes
duration, baseline, peer count and direction. R008 includes alert/case IDs, count,
first/last timestamp and span. R009 includes all contributing indicators.
R006–R008 default to MEDIUM and R009 to HIGH review priority, with
`assessment=REVIEW_REQUIRED`. These priorities are not entity risk scores.

Detector reports count R008 windows. API reports expand each window to one
finding per affected case, so API and detector row counts intentionally differ.
Case-specific requests calculate the full entity baseline before filtering.
Findings are computed on demand and not persisted. TF-IDF comparison uses a
quadratic similarity matrix; production-scale workloads need profiling and
caching/batching before deployment.

## Run and evaluate

Install root `requirements.txt` in the backend environment (includes
scikit-learn), then from `backend`:

```bash
venv/bin/python test_behaviour_analytics.py --summary
venv/bin/python test_behaviour_analytics.py --dataset metro_telecom --rule R007
venv/bin/python -m unittest test_behaviour_unit test_backend_api_unit
venv/bin/python validate_behaviour_ground_truth.py
venv/bin/python validate_behaviour_ground_truth.py --json
```

The old R007/R008 validation entry points delegate to the shared evaluator, and
R007/R008/R009 demonstration scripts delegate to the all-organization reporter.
`test_behaviour_edge_cases.py` now executes assertions and exits nonzero on failure.

Evaluation detects first, then loads labels. It reports TP/FP/FN, precision,
recall, F1 and explicit false-positive/false-negative identifiers per rule and
organization. Case labels are evaluated as case units; asset-only labels as asset
units. Missing observational records remain false negatives. The overall metric
is a micro-average over labelled organization/rule units only. Within those units,
unlabelled detections count as false positives under the supplied synthetic labels.
Incomplete labels limit interpretation. No-positive-label rules report
`NOT_LABELLED` instead of a misleading perfect or zero accuracy.

R007's label is `INVESTIGATION_DURATION_ANOMALY`; `FAST_CRITICAL_CLOSURE`
belongs to R004. R009's label is
`COMBINED_SUSPICIOUS_INVESTIGATION_BEHAVIOUR`; `KPI_GAMING_PATTERN` is not
assumed equivalent. R008 accepts `REPEAT_INCIDENT` and `REPEAT_INCIDENT_PATTERN`.
See the verification report for measured results and remaining calibration work.
