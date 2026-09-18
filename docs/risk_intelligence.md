# Risk Intelligence Engine — Rajeesh module

This module consumes existing engine findings and Workflow Auditor assessments
from PostgreSQL. It does not change R001–R009, detect new anomalies, read ground
truth, call external AI, write database records or implement the frontend.
Every score is a **prototype ShadowWatch supervisory indicator, not an official
NCIIPC threshold or compliance certification**. LOW describes the observed
prototype score; it does not establish that the organization is safe.

## Repository inspection and finding formats

Inspected `backend/app/services/analytics/rule_engine.py`, `backend/app/services/analytics/negative_space_engine.py`,
`backend/app/services/analytics/workflow_auditor.py`, `backend/app/services/analytics/contradiction_engine.py`, `backend/app/services/analytics/behaviour_analytics.py`,
`backend/app/services/analytics/behaviour_finding_service.py`, `backend/app/services/analytics/findings_service.py`; `backend/app/models.py`,
`backend/app/schemas.py`, `backend/app/core/database.py`, `backend/app/main.py`, `routes/entities.py`; and
`database/schema.sql`. Also queried PostgreSQL entity, sector, peer-group and
monitoring metadata. There is no persisted findings or risk table and there was
no existing risk module.

| Producer | Existing output |
| --- | --- |
| Core R001–R004 | Case dictionaries with parallel `rules` and `reasons`; shared service expands them |
| R005 | Asset/episode dictionaries with timestamps, historical baseline and observed drop |
| Workflow Auditor | Case assessment with `gaps`, `data_issues`, source `records`; HIGH gaps can have no R-rule ID |
| Contradictions | C001–C004, chronology evidence and source record IDs |
| Behaviour | R006–R009 DataFrames; adapter supplies case/asset/entity ownership, reasons and structured evidence |
| Shared findings service | Stable ID, rule/problem IDs, entity/case/alert/asset IDs, severity, `source`, explicit assessment, reason, evidence |

The new aggregator uses that shared service, renames `source` to `source_engine`,
retains original IDs in `source_finding_ids`, and generates a deterministic
normalized ID. Identical content is deduplicated even if input IDs differ.
Meaningfully distinct source records remain visible in counts/evidence; they
cannot multiply the same exposure's score. Normalization is idempotent and rejects
invalid required fields instead of silently dropping them.

Existing auditor output is adapted, not reimplemented. Already-confirmed core
rule/case gaps are not appended twice. Additional HIGH investigation/evidence
gaps use internal IDs `WF_INVESTIGATION` and `WF_EVIDENCE`; these are not new R
rules. The original `/findings` contract stays unchanged. Risk aggregation may
therefore contain more records than `/findings`.

## Configurable component formula

All defaults live in `backend/app/core/risk_config.py`; a complete validated config
can also be passed to pure services or `build_risk_intelligence(db, config)`.
The response returns the effective configuration and version `prototype-v1`.

Severity weights: LOW **0.25**, MEDIUM **0.50**, HIGH **0.75**, CRITICAL **1.00**.
For each eligible case/asset, take the maximum severity weight among that
component's findings. `INSUFFICIENT_DATA` contributes no points but is retained
and counted separately.

```
component score = 100 × sum(max severity weight per eligible exposure)
                        / number of eligible exposures

overall observed score = sum(component score × component weight)
```

| Component | Finding inputs | Eligible exposure | Weight |
| --- | --- | --- | ---: |
| EXECUTION_GAP_RISK | R001–R004 and extra Workflow Auditor gaps | Distinct HIGH/CRITICAL cases | 30% |
| MONITORING_VISIBILITY_RISK | R005 | Assets with `monitoring_expected IS TRUE` | 20% |
| INVESTIGATION_QUALITY_RISK | R006, R007, R009 | Distinct cases with an investigation record | 20% |
| REPEAT_INCIDENT_RISK | R008 | All distinct cases | 15% |
| RECORD_CONSISTENCY_RISK | C001–C004 | All distinct cases | 15% |

Scores are bounded 0–100. Level cutoffs are LOW <25, MODERATE >=25 and <50,
HIGH >=50 and <75, CRITICAL >=75. Levels use the displayed rounded overall score.
A case with several execution gaps contributes once to that component. R009
cannot add its full weight on top of R006/R007 for the same case. A repeated
R005 episode cannot repeatedly increase the same asset's component score.
No detector thresholds were adjusted to produce particular risk levels.

A zero denominator or unavailable engine yields a null component score and an
explicit status. Its contribution is zero in the **observed** score; remaining
weights are not redistributed. `available_component_weight` and
`unavailable_component_upper_bound` show how much scoring capacity is absent.
The upper bound is observed score plus 100 times unavailable component weight;
it is not a statistical confidence interval and does not account for unobserved
problems in otherwise available components. All unavailable yields observed 0,
PARTIAL status and upper bound 100. No findings with valid exposures yields 0.

Engine availability means the existing engine completed, not that all of its
inputs were assessable. `data_coverage` and `limitations` separately report absent
notes/durations, unknown monitoring expectations, monitored assets without
telemetry and auditor data issues. Existing detector skip behavior is preserved.
Entities with fewer than **20 cases** receive a configurable small-population
notice. Unknown/unmapped rules and findings outside a component's eligible
population are retained and explicitly reported, not silently scored.

Counts include all retained findings. Affected-case/asset counts are distinct.
Execution-gap counts exclude insufficient-data triggers. Raw counts are useful
for review workload; component scores use capped exposure rates.

## Case priority formula

Case priority is a separate 0–100 review order. It uses actual linked alert
severity and asset criticality plus capped evidence contributions:

```
priority = min(100, alert points + asset points
                    + sum(component cap × maximum finding severity weight))
```

| Input | LOW | MEDIUM | HIGH | CRITICAL | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alert severity points | 5 | 10 | 20 | 30 | 0 |
| Asset criticality points | 0 | 3 | 6 | 10 | 0 |

Component caps: execution **30**, visibility **0**, investigation quality **15**,
repeat incidents **10**, record consistency **15**. R005 is asset-scoped and is
not attached to unrelated cases. Insufficient-data findings appear in reasons
but do not add finding points. Multiple different components add independently;
repeated findings within one component do not. The number of findings is visible
through `triggered_findings`, not used as an uncapped count bonus.

Every case has a score breakdown, source reasons, finding IDs and triggered
rules. Cases without findings can still receive context points from alert/asset
severity; the reason says so. Ties sort by entity ID then case ID. All cases are
ranked, with pagination at the API boundary.

## Peer metrics

Metrics use actual PostgreSQL exposure sets. Rates are percentages unless marked
as finding density. Rate numerators count distinct affected exposures and exclude
insufficient-data findings. Finding densities retain all normalized findings,
can exceed 100, and are never treated as probabilities.

| Metric | Numerator / denominator |
| --- | --- |
| Findings per 100 cases | All normalized findings / all cases |
| Execution gap rate | Affected serious cases / HIGH+CRITICAL cases |
| Missing escalation rate | Cases with confirmed R003 / CRITICAL cases |
| Missing evidence rate | Cases with R002 or WF_EVIDENCE / investigated HIGH+CRITICAL cases |
| Telemetry blind-spot rate | R005-affected explicitly monitored assets / explicitly monitored assets |
| Repetitive investigation rate | R006-affected investigated cases / investigated cases |
| Repeat incident rate | R008-affected cases / all cases |
| Contradiction rate | C001–C004-affected cases / all cases |
| Behaviour findings per 100 investigated cases | Behaviour finding count / investigated cases |
| Median investigation minutes | Median of valid, nonnegative actual start/completion durations; reports sample count |

R003's denominator is CRITICAL only because the existing policy does not require
HIGH escalation. Median duration is descriptive, not another anomaly detector.
A zero denominator returns null, never a fabricated zero rate.

Peers must match **both group and sector**, ignoring case and surrounding spaces.
Peer means/medians exclude the selected organization and null metric values;
each metric reports its valid peer count and difference from median. Descriptions
are neutral: above/below/near peer median. Near tolerance is **0.01 in the metric's
native units**, configurable. No best/worst ranking is produced.

The live database stores Alpha/Beta as Banking peers but Gamma's `peer_group` is
NULL while its sector is Banking. To satisfy the requested three-bank comparison,
the explicit default fallback mapping is `{'Banking': 'Banking'}`. It applies only
when the stored group is absent, is labelled `configured_sector_fallback`, and
does not update PostgreSQL. Set this mapping to `{}` to require stored groups.
Telecom and Energy each currently have no other peer and return NO_VALID_PEERS.
No unrelated sector is substituted.

Comparisons cover all currently loaded records, without a common reporting period.
Different observation windows and missing data limit interpretation. They are
prototype descriptive comparisons, not validated performance rankings.

## API and files

New GET endpoints:

- `/risk/entities` — complete risk intelligence for all stored organizations.
- `/entities/{entity_id}/risk` — one organization's full report.
- `/entities/{entity_id}/priority-cases?limit=20&offset=0` — case review order;
  limit 1–1000, nonnegative offset.
- `/entities/{entity_id}/peer-benchmark` — group metadata and rate comparisons.
- `/entities/{entity_id}/supervisory-summary` — deterministic summary and top five cases/contributors.

Unknown entities return 404; invalid pagination returns 422. Database failures
use the existing sanitized 503 handler. Other engine failures propagate instead
of becoming empty findings. The request service reads the existing engines once
per report batch and uses the shared SQLAlchemy session. Reports are computed
on demand, not persisted; no migration is needed. Per-entity endpoints currently
compute all organizations to establish peer context. Large workloads require
profiling and caching before deployment.

Created:

- `backend/app/core/risk_config.py`
- `backend/app/services/risk/finding_aggregator.py`, `backend/app/services/risk/risk_engine.py`, `backend/app/services/risk/risk_service.py`,
  `backend/app/services/risk/prioritization.py`, `backend/app/services/risk/benchmark_engine.py`, `backend/app/services/risk/explainability.py`
- `backend/app/api/routes/risk.py`
- `backend/scripts/report_risk.py`, `backend/scripts/report_peers.py`, `backend/tests/unit/test_risk_engine.py`,
  `backend/tests/integration/test_risk_api.py`, `backend/tests/integration/test_risk_live.py`
- `docs/risk_intelligence.md`, `docs/risk_verification.md`, `docs/risk_results.json`

Modified: `backend/app/main.py` (router registration), `backend/app/schemas.py` (new
response contracts), `docs/backend_api.md` (endpoint documentation). Existing
engines, thresholds, database schema, operational data and frontend are unchanged.

See [verification and results](risk_verification.md) for the exact commands,
measured organization scores, Banking comparison and test outcomes.
