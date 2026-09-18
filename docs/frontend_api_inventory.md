# Supervisor frontend API inventory

Inspected against `backend/app/main.py`, `app/api/routes/` and `app/schemas.py`.
All application endpoints below are **GET** and read-only. Paths are backend paths;
the frontend adds the configured API base (`/api` by default).

| Path | Purpose / parameters | Response |
| --- | --- | --- |
| `/` | API identification; none | Message object |
| `/health` | Backend/database health; none | `status`, `database`; database failure returns 503 |
| `/entities` | Organization registry; none | Array: `entity_id`, `entity_name`, `sector`, `peer_group`, `country` |
| `/entities/{entity_id}` | Organization metadata and operational counts | Entity summary object |
| `/entities/{entity_id}/assets` | Inventory; `limit` default 100, max 1000; `offset` default 0 | Array of assets including type, criticality, business function and nullable `monitoring_expected` |
| `/entities/{entity_id}/cases` | Cases; `limit` default 100, max 1000; `offset` default 0 | Case summaries; no nested alert severity/category |
| `/entities/{entity_id}/findings` | Shared findings for one organization | Array of `FindingResponse` objects |
| `/findings` | Shared findings; optional `entity_id` | Array with IDs, rule, problem, entity/case/asset references, severity, assessment, reason, source and structured evidence |
| `/cases/{case_id}` | Case investigation detail | Case fields, alert, all investigations/escalations, shared findings and workflow; singular compatibility records can be null |
| `/analytics/summary` | Operational and findings summary; none | Counts and breakdowns by rule and assessment |
| `/assets/{asset_id}/telemetry` | Recorded telemetry; optional `entity_id`, `start_time`, `end_time`; `limit` default 500, max 5000; `offset` default 0 | Array of telemetry records including ID, timestamp and nullable event count. Date bounds are inclusive; timezone-aware bounds are rejected by the current service |
| `/risk/entities` | Complete risk workspace; none | Array of `RiskResponse`, including normalized findings, priority cases, peer context and supervisory summary |
| `/entities/{entity_id}/risk` | One complete risk report | `RiskResponse` |
| `/entities/{entity_id}/priority-cases` | Backend-ranked cases; `limit` default 20, max 1000; `offset` default 0 | Case ID, entity ID, score/level, triggered finding IDs/rules, reason, score breakdown and disclaimer |
| `/entities/{entity_id}/peer-benchmark` | Valid peer comparison | Stored/resolved peer group, peer membership/source/status, metrics, explanation |
| `/entities/{entity_id}/supervisory-summary` | Report narrative and leading evidence | Components, top contributors, explanation, priority cases, peer context, limitations and disclaimer |

FastAPI also exposes `/openapi.json`, `/docs`, `/redoc` and the Swagger OAuth redirect.
Invalid identifiers return backend errors (normally 404); validation errors return 422.

## Contracts used by the interface

`RiskResponse` supplies the score, level, score status, five weighted components,
aggregation, denominators, data coverage, engine status, contributors, findings,
priority cases, peer context, summary, configuration, limitations and disclaimer.
A component includes score (nullable), weight, contribution, exposure, denominator,
affected counts, status, missing engines and evidence IDs. Missing input remains
unavailable; the UI does not rescore it as zero.

The frontend fetches `/risk/entities`, `/entities` and `/health` once per workspace
refresh. It reuses each complete report instead of repeatedly calling the four
per-entity risk projections. Details fetch cases, assets and telemetry as needed.
Priority table alert metadata comes from case detail, not guessed from priorities.
Paginated inventory and telemetry are fetched until the API returns a short page.

Normalized risk findings include additional workflow gaps and `source_finding_ids`
aliases. They are the canonical frontend collection so priority evidence links use
the same identifiers. Consequently their count can exceed `/findings`; this is
labelled in the UI. A finding's engine assessment is not a human review decision.

Workflow rendering uses the exact `expected`, `observed`, `gaps`, `data_issues`,
`explanation` and `limitations` returned with a case. In particular, no mandatory
closure policy is inferred from a null expected value.

Peer metrics include entity value, peer median/mean, difference, unit, status and
valid peer count. Membership and comparisons come exclusively from the backend;
no cross-sector fallback is performed in React.

## Missing capabilities

There are no persisted human review, comment, audit-event, reviewer identity or
PDF export endpoints. No POST/PATCH/DELETE calls are made by this frontend.
See [frontend delivery and proposed persistence contract](frontend_verification.md).
