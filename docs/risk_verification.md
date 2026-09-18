# Risk Intelligence verification and handoff

Date: 2026-09-18. Scope: `work/w5.txt`, Rajeesh's Risk Intelligence module.
Implementation, isolated tests, live risk endpoint verification and existing
backend regression checks are complete. Frontend work was
not started. Changes are local; no commit or push was performed.

## Live results

All values below were calculated from existing PostgreSQL records and existing
engine outputs, not ground truth. The full compact record is
[risk_results.json](risk_results.json); formulas, exact configuration, inspected
files, normalization design and created/modified files are documented in
[risk_intelligence.md](risk_intelligence.md).

| Entity | Cases | Aggregated findings | Observed score | Level | Component availability |
| --- | ---: | ---: | ---: | --- | --- |
| E001 Alpha Bank | 97 | 106 | 14.62 | LOW | 100% |
| E002 Beta Bank | 104 | 37 | 6.12 | LOW | 100% |
| E003 Gamma Bank | 97 | 87 | 12.19 | LOW | 80%, PARTIAL |
| E004 Metro Telecom | 100 | 153 | 19.44 | LOW | 100% |
| E005 PowerGrid Utility | 100 | 87 | 16.00 | LOW | 100% |

Availability describes components with an executed engine and nonzero
population, not complete underlying evidence. These levels follow the configured
0/25/50/75 scale without tuning scores to desired labels. Underlying behaviour
findings still have the calibration limits documented in the earlier Devenanda
review. Supervisors should inspect components and source evidence rather than
interpret LOW as an assurance statement.

Risk has 470 normalized findings versus 455 in the unchanged shared finding
feed: 15 additional HIGH workflow gaps (Alpha 5, Metro 9, PowerGrid 1). Existing
core/auditor overlaps are suppressed. Multiple investigations/episodes are
retained for evidence while scoring takes one maximum per eligible exposure.

| Entity | Execution | Visibility | Investigation quality | Repeat incidents | Record consistency |
| --- | ---: | ---: | ---: | ---: | ---: |
| E001 | 13.0597 | 5.3571 | 48.1383 | 0 | 0 |
| E002 | 9.5238 | 4.6875 | 9.8039 | 2.4038 | 0 |
| E003 | 17.2414 | unavailable | 35.1064 | 0 | 0 |
| E004 | 28.8462 | 0 | 51.3158 | 3.5000 | 0 |
| E005 | 30.1020 | 0 | 34.8485 | 0 | 0 |

Gamma has 30 assets with unknown monitoring expectations and zero valid
investigation durations. Visibility is null and its observed score's unavailable
component upper bound is 32.19; this is not a confidence interval. Alpha has
telemetry for only 14 of 28 explicitly monitored assets and 91 valid durations
among 94 investigations. Gamma has 28 cases with auditor data issues. These
coverage limitations appear in API output; no missing values were fabricated.

Top three review cases (case priority is independent of entity score):

| Entity | Case and priority score |
| --- | --- |
| E001 | E001-C0003 77.50; E001-C0025 77.50; E001-C0081 77.25 |
| E002 | E002-C0001 70.00; E002-C0013 70.00; E002-C0016 70.00 |
| E003 | CASE-E003-045 77.50; CASE-E003-026 73.50; CASE-E003-062 73.50 |
| E004 | E004-C0034 86.25; E004-C0035 86.25; E004-C0015 77.50 |
| E005 | E005-C0011 77.50; E005-C0082 77.50; E005-C0086 77.50 |

The API and readable report include the point breakdown and actual source
reasons for each case, including timing details where present in findings.

## Banking benchmark

Alpha, Beta and Gamma now all use stored Banking peer groups. Gamma's previous
NULL was corrected in its source CSV and PostgreSQL using
`database/migrations/001_gamma_peer_group.sql`. The default sector fallback is
disabled. Other-peer medians exclude the selected entity; unavailable metrics
are excluded from that metric's peer sample. Telecom and Energy each return
NO_VALID_PEERS. This metadata correction leaves risk scores and peer metric
values unchanged.

| Entity | Findings / 100 cases | Missing escalation % | Missing evidence % | Blind-spot assets % | Repetitive investigations % |
| --- | ---: | ---: | ---: | ---: | ---: |
| E001 | 109.2784 | 23.5294 | 6.2500 | 7.1429 | 95.7447 |
| E002 | 35.5769 | 11.1111 | 3.2787 | 6.2500 | 11.7647 |
| E003 | 89.6907 | 45.4545 | 3.4483 | unavailable | 70.2128 |

For example, the missing-escalation comparison is:

| Entity | Entity rate % | Other-peer median % | Difference, percentage points | Description |
| --- | ---: | ---: | ---: | --- |
| E001 | 23.5294 | 28.2828 | -4.7534 | below peer median |
| E002 | 11.1111 | 34.4920 | -23.3809 | below peer median |
| E003 | 45.4545 | 17.3203 | +28.1343 | above peer median |

All ten implemented metrics also return peer mean, valid peer count and neutral
comparison text. No organization is labelled best or worst. Denominators and
metric definitions are in the module document and JSON artifact. Comparison
periods are the loaded datasets and are not assumed equal.

## Verification

- **106 unit/contract tests PASS:** 23 new pure risk tests, six new risk API tests,
  and all 77 pre-existing backend/behaviour/ingestion/core/contradiction tests.
- Covers no/one/multiple findings, distinct categories, duplicate IDs/content,
  repeated-category caps, zero denominators, optional missing data, score bounds,
  level boundaries, invalid configuration, case ranking/explanations, organization
  size normalization, entity isolation, workflow overlap, Banking peers, missing
  peers, unrelated sectors/groups, unavailable peer metrics and missing engines.
- Risk API tests also verify existing feed preservation, normalizer idempotence,
  404/422 handling, pagination, empty database and propagation of engine errors.
- **Live risk integration PASS:** all five organizations, all five new endpoint
  types, schema serialization, deterministic results, exact entity/summary/peer
  parity, all 498 case priorities, source finding retention and unchanged shared
  findings before/after analysis.
- **All five source dataset validations PASS**, including ownership and IDs.
- **Existing full API PASS:** all five organizations, 498 case responses and
  152 asset telemetry responses; global/entity/case findings remain consistent.
- **PostgreSQL source-value/count/ownership verification PASS.** Existing
  multi-entity analytics and Alpha regression checks also passed.
- **Both requested readable terminal scripts PASS**, with captured output in
  `/tmp/shadowwatch_risk_readable.txt` and `/tmp/shadowwatch_peer_benchmark.txt`.
- `git diff --check` passed.

No R001–R009 implementation, threshold, operational CSV, schema, importer or
frontend was modified. New modules consume current PostgreSQL data; no folder or
organization IDs are hard-coded into their calculations.

## Exact terminal commands

From repository root, with the existing `backend/.env` connection and environment:

```bash
cd backend
venv/bin/python -m scripts.validate_all_datasets
venv/bin/python -m unittest tests.unit.test_risk_engine tests.integration.test_risk_api tests.unit.test_behaviour_analytics tests.integration.test_backend_api tests.integration.test_ingestion tests.unit.test_contradiction_engine tests.unit.test_workflow_auditor tests.unit.test_negative_space
venv/bin/python -m scripts.report_risk
venv/bin/python -m scripts.report_peers
venv/bin/python -m scripts.report_risk --json > /tmp/shadowwatch_risk_report.json
venv/bin/python -m tests.integration.test_risk_live
venv/bin/python -m tests.integration.test_backend_live
venv/bin/python -m scripts.verify_database
venv/bin/python -m tests.integration.test_analytics_live
```

With the API already running, example requests:

```bash
curl http://127.0.0.1:8000/risk/entities
curl http://127.0.0.1:8000/entities/E001/risk
curl 'http://127.0.0.1:8000/entities/E001/priority-cases?limit=3'
curl http://127.0.0.1:8000/entities/E001/peer-benchmark
curl http://127.0.0.1:8000/entities/E001/supervisory-summary
```

Unit/API contract tests use isolated SQLite. PostgreSQL reports and integration
checks are read-only. No additional dependency or database migration is required.
