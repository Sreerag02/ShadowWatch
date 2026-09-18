# Project structure and migration

The refactor groups application code by responsibility and separates production
modules, runnable tools and tests. Existing algorithms, thresholds, data and
uncommitted risk work were retained.

## Before

The backend root mixed the FastAPI app, database/models/schemas, importers,
evaluators, read-only reports named `test_*`, real tests and inspectors.
`services/` mixed ingestion, analytics, API orchestration and risk. Additional
validation/repair tools were under `tests/` and `tests/tests/`; dataset generation
scripts and a source ZIP were at repository root. Python imports relied on the
backend working directory, and two scripts inserted `backend` into `sys.path`.a
Root requirements and README commands referenced the old app entry point.

## After

`app` is a Python package: core configuration, API routes, analytics, ingestion
and risk are separated. Models and schemas remain single files. `scripts`
contains reports/imports/evaluation; `legacy` preserves historical diagnostics;
`maintenance` contains explicitly invoked dataset-writing tools. Tests separate
pure functions from SQLite/API contracts and optional live PostgreSQL checks.
Editable packaging supports module imports outside the backend directory.

The following listing is equivalent to `tree -L 5 -a` with `.git`, `node_modules`,
`venv`, `__pycache__`, `.vscode`, generated `dist` and `*.egg-info` excluded.
The system's `tree` executable was unavailable, so Python generated this listing.

```text
ShadowWatch/
├── .agents/
├── .codex/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cases.py
│   │   │   │   ├── entities.py
│   │   │   │   ├── findings.py
│   │   │   │   ├── risk.py
│   │   │   │   ├── system.py
│   │   │   │   └── telemetry.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── risk_config.py
│   │   ├── services/
│   │   │   ├── analytics/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── behaviour_analytics.py
│   │   │   │   ├── behaviour_finding_service.py
│   │   │   │   ├── contradiction_engine.py
│   │   │   │   ├── findings_service.py
│   │   │   │   ├── negative_space_engine.py
│   │   │   │   ├── rule_engine.py
│   │   │   │   └── workflow_auditor.py
│   │   │   ├── ingestion/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data_ingestion.py
│   │   │   │   ├── dataset_validation.py
│   │   │   │   └── importer.py
│   │   │   ├── risk/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── benchmark_engine.py
│   │   │   │   ├── explainability.py
│   │   │   │   ├── finding_aggregator.py
│   │   │   │   ├── prioritization.py
│   │   │   │   ├── risk_engine.py
│   │   │   │   └── risk_service.py
│   │   │   ├── __init__.py
│   │   │   ├── case_service.py
│   │   │   ├── entity_service.py
│   │   │   ├── system_service.py
│   │   │   └── telemetry_service.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── scripts/
│   │   ├── legacy/
│   │   │   ├── __init__.py
│   │   │   ├── inspect_r007.py
│   │   │   ├── inspect_r007_cases.py
│   │   │   ├── validate_alpha_data.py
│   │   │   └── validate_ground_truth.py
│   │   ├── maintenance/
│   │   │   ├── __init__.py
│   │   │   ├── generate_powergrid_data.py
│   │   │   ├── inject_powergrid_scenarios.py
│   │   │   └── repair_organization_datasets.py
│   │   ├── __init__.py
│   │   ├── check_behaviour_edge_cases.py
│   │   ├── import_all_entities.py
│   │   ├── import_alpha_bank.py
│   │   ├── import_data.py
│   │   ├── import_metro_telecom.py
│   │   ├── report_behaviour.py
│   │   ├── report_contradictions.py
│   │   ├── report_negative_space.py
│   │   ├── report_peers.py
│   │   ├── report_r007.py
│   │   ├── report_r008.py
│   │   ├── report_r009.py
│   │   ├── report_risk.py
│   │   ├── report_rules.py
│   │   ├── report_workflow.py
│   │   ├── validate_all_datasets.py
│   │   ├── validate_behaviour_ground_truth.py
│   │   ├── validate_negative_space.py
│   │   ├── validate_r007_ground_truth.py
│   │   ├── validate_r008_ground_truth.py
│   │   ├── verify_database.py
│   │   └── verify_system.py
│   ├── tests/
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── test_analytics_live.py
│   │   │   ├── test_backend_api.py
│   │   │   ├── test_backend_live.py
│   │   │   ├── test_ingestion.py
│   │   │   ├── test_risk_api.py
│   │   │   └── test_risk_live.py
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_behaviour_analytics.py
│   │   │   ├── test_configuration.py
│   │   │   ├── test_contradiction_engine.py
│   │   │   ├── test_negative_space.py
│   │   │   ├── test_risk_engine.py
│   │   │   └── test_workflow_auditor.py
│   │   └── __init__.py
│   ├── .env
│   ├── .env.example
│   ├── pyproject.toml
│   └── requirements.txt
├── data/
│   ├── alpha_bank/
│   │   ├── alerts.csv
│   │   ├── assets.csv
│   │   ├── cases.csv
│   │   ├── entities.csv
│   │   ├── escalations.csv
│   │   ├── ground_truth.csv
│   │   ├── investigations.csv
│   │   └── telemetry.csv
│   ├── beta_bank/
│   │   ├── alerts.csv
│   │   ├── assets.csv
│   │   ├── cases.csv
│   │   ├── entities.csv
│   │   ├── escalations.csv
│   │   ├── ground_truth.csv
│   │   ├── investigations.csv
│   │   └── telemetry.csv
│   ├── gamma_bank/
│   │   ├── alerts.csv
│   │   ├── assets.csv
│   │   ├── cases.csv
│   │   ├── entities.csv
│   │   ├── escalations.csv
│   │   ├── ground_truth.csv
│   │   ├── investigations.csv
│   │   └── telemetry.csv
│   ├── metro_telecom/
│   │   ├── alerts.csv
│   │   ├── assets.csv
│   │   ├── cases.csv
│   │   ├── entities.csv
│   │   ├── escalations.csv
│   │   ├── ground_truth.csv
│   │   ├── investigations.csv
│   │   └── telemetry.csv
│   └── powergrid_utility/
│       ├── alerts.csv
│       ├── assets.csv
│       ├── cases.csv
│       ├── entities.csv
│       ├── escalations.csv
│       ├── ground_truth.csv
│       ├── investigations.csv
│       └── telemetry.csv
├── database/
│   └── schema.sql
├── docs/
│   ├── backend_api.md
│   ├── behaviour_analytics.md
│   ├── behaviour_analytics_original_handoff.md
│   ├── contradiction_engine.md
│   ├── dataset_repairs.json
│   ├── deepa_backend_verification.md
│   ├── devenanda_behaviour_verification.md
│   ├── multi_entity_import.md
│   ├── project_structure.md
│   ├── refactor_manifest.json
│   ├── refactor_verification.md
│   ├── risk_intelligence.md
│   ├── risk_results.json
│   ├── risk_verification.md
│   └── workflow_auditor.md
├── frontend/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── src/
│   │   ├── assets/
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .gitignore
│   ├── README.md
│   ├── eslint.config.js
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   └── vite.config.js
├── work/
│   ├── dataset_backups/
│   │   └── before_gamma_powergrid_repair/
│   │       ├── gamma_bank/
│   │       │   ├── alerts.csv
│   │       │   ├── assets.csv
│   │       │   ├── cases.csv
│   │       │   ├── entities.csv
│   │       │   ├── escalations.csv
│   │       │   ├── ground_truth.csv
│   │       │   ├── investigations.csv
│   │       │   └── telemetry.csv
│   │       └── powergrid_utility/
│   │           ├── alerts.csv
│   │           ├── assets.csv
│   │           ├── cases.csv
│   │           ├── entities.csv
│   │           ├── escalations.csv
│   │           ├── ground_truth.csv
│   │           ├── investigations.csv
│   │           └── telemetry.csv
│   ├── source_archives/
│   │   └── E005_powergrid_datasets.zip
│   ├── w1.txt
│   ├── w2.txt
│   ├── w3.txt
│   ├── w4.txt
│   ├── w5.txt
│   └── w6.txt
├── .gitignore
└── README.md
```

## Complete move/rename manifest

Tracked files were moved with `git mv`; previously untracked risk files were
renamed without changing their ownership or losing edits. All old locations
below are absent. Basename changes distinguish reports from tests. No old source
copies or compatibility implementation duplicates were left behind.

| Previous path | Current path |
| --- | --- |
| `BEHAVIOUR_ANALYTICS_HANDOFF.md` | `docs/behaviour_analytics_original_handoff.md` |
| `E005_powergrid_datasets.zip` | `work/source_archives/E005_powergrid_datasets.zip` |
| `backend/config/risk_config.py` | `backend/app/core/risk_config.py` |
| `backend/database.py` | `backend/app/core/database.py` |
| `backend/import_all_entities.py` | `backend/scripts/import_all_entities.py` |
| `backend/import_alpha_bank.py` | `backend/scripts/import_alpha_bank.py` |
| `backend/import_data.py` | `backend/scripts/import_data.py` |
| `backend/import_metro_telecom.py` | `backend/scripts/import_metro_telecom.py` |
| `backend/inspect_r007.py` | `backend/scripts/legacy/inspect_r007.py` |
| `backend/inspect_r007_cases.py` | `backend/scripts/legacy/inspect_r007_cases.py` |
| `backend/main.py` | `backend/app/main.py` |
| `backend/models.py` | `backend/app/models.py` |
| `backend/routes/cases.py` | `backend/app/api/routes/cases.py` |
| `backend/routes/entities.py` | `backend/app/api/routes/entities.py` |
| `backend/routes/findings.py` | `backend/app/api/routes/findings.py` |
| `backend/routes/risk.py` | `backend/app/api/routes/risk.py` |
| `backend/routes/system.py` | `backend/app/api/routes/system.py` |
| `backend/routes/telemetry.py` | `backend/app/api/routes/telemetry.py` |
| `backend/schemas.py` | `backend/app/schemas.py` |
| `backend/services/behaviour_analytics.py` | `backend/app/services/analytics/behaviour_analytics.py` |
| `backend/services/behaviour_finding_service.py` | `backend/app/services/analytics/behaviour_finding_service.py` |
| `backend/services/benchmark_engine.py` | `backend/app/services/risk/benchmark_engine.py` |
| `backend/services/case_service.py` | `backend/app/services/case_service.py` |
| `backend/services/contradiction_engine.py` | `backend/app/services/analytics/contradiction_engine.py` |
| `backend/services/data_ingestion.py` | `backend/app/services/ingestion/data_ingestion.py` |
| `backend/services/dataset_validation.py` | `backend/app/services/ingestion/dataset_validation.py` |
| `backend/services/entity_service.py` | `backend/app/services/entity_service.py` |
| `backend/services/explainability.py` | `backend/app/services/risk/explainability.py` |
| `backend/services/finding_aggregator.py` | `backend/app/services/risk/finding_aggregator.py` |
| `backend/services/findings_service.py` | `backend/app/services/analytics/findings_service.py` |
| `backend/services/negative_space_engine.py` | `backend/app/services/analytics/negative_space_engine.py` |
| `backend/services/prioritization.py` | `backend/app/services/risk/prioritization.py` |
| `backend/services/risk_engine.py` | `backend/app/services/risk/risk_engine.py` |
| `backend/services/risk_service.py` | `backend/app/services/risk/risk_service.py` |
| `backend/services/rule_engine.py` | `backend/app/services/analytics/rule_engine.py` |
| `backend/services/system_service.py` | `backend/app/services/system_service.py` |
| `backend/services/telemetry_service.py` | `backend/app/services/telemetry_service.py` |
| `backend/services/workflow_auditor.py` | `backend/app/services/analytics/workflow_auditor.py` |
| `backend/test_backend_api_unit.py` | `backend/tests/integration/test_backend_api.py` |
| `backend/test_backend_integration.py` | `backend/tests/integration/test_backend_live.py` |
| `backend/test_behaviour_analytics.py` | `backend/scripts/report_behaviour.py` |
| `backend/test_behaviour_edge_cases.py` | `backend/scripts/check_behaviour_edge_cases.py` |
| `backend/test_behaviour_unit.py` | `backend/tests/unit/test_behaviour_analytics.py` |
| `backend/test_contradiction_engine.py` | `backend/scripts/report_contradictions.py` |
| `backend/test_contradiction_engine_unit.py` | `backend/tests/unit/test_contradiction_engine.py` |
| `backend/test_multi_entity_analytics.py` | `backend/tests/integration/test_analytics_live.py` |
| `backend/test_multi_entity_unit.py` | `backend/tests/integration/test_ingestion.py` |
| `backend/test_negative_space.py` | `backend/scripts/report_negative_space.py` |
| `backend/test_negative_space_unit.py` | `backend/tests/unit/test_negative_space.py` |
| `backend/test_peer_benchmark.py` | `backend/scripts/report_peers.py` |
| `backend/test_r007.py` | `backend/scripts/report_r007.py` |
| `backend/test_r008.py` | `backend/scripts/report_r008.py` |
| `backend/test_r009.py` | `backend/scripts/report_r009.py` |
| `backend/test_risk_api_unit.py` | `backend/tests/integration/test_risk_api.py` |
| `backend/test_risk_engine.py` | `backend/scripts/report_risk.py` |
| `backend/test_risk_integration.py` | `backend/tests/integration/test_risk_live.py` |
| `backend/test_risk_unit.py` | `backend/tests/unit/test_risk_engine.py` |
| `backend/test_rule_engine.py` | `backend/scripts/report_rules.py` |
| `backend/test_workflow_auditor.py` | `backend/scripts/report_workflow.py` |
| `backend/test_workflow_auditor_unit.py` | `backend/tests/unit/test_workflow_auditor.py` |
| `backend/validate_behaviour_ground_truth.py` | `backend/scripts/validate_behaviour_ground_truth.py` |
| `backend/validate_ground_truth.py` | `backend/scripts/legacy/validate_ground_truth.py` |
| `backend/validate_negative_space.py` | `backend/scripts/validate_negative_space.py` |
| `backend/validate_r007_ground_truth.py` | `backend/scripts/validate_r007_ground_truth.py` |
| `backend/validate_r008_ground_truth.py` | `backend/scripts/validate_r008_ground_truth.py` |
| `backend/verify_multi_entity_db.py` | `backend/scripts/verify_database.py` |
| `generate_data.py` | `backend/scripts/maintenance/generate_powergrid_data.py` |
| `inject_scenarios.py` | `backend/scripts/maintenance/inject_powergrid_scenarios.py` |
| `requirements.txt` | `backend/requirements.txt` |
| `tests/repair_organization_datasets.py` | `backend/scripts/maintenance/repair_organization_datasets.py` |
| `tests/tests/validate_alpha_data.py` | `backend/scripts/legacy/validate_alpha_data.py` |
| `tests/validate_all_datasets.py` | `backend/scripts/validate_all_datasets.py` |

## Additional changes

- Added package `__init__.py` markers, `backend/pyproject.toml`, centralized
  `backend/app/core/config.py`, the master `backend/scripts/verify_system.py`,
  configuration tests and this migration/verification documentation.
- Extracted transactional import helpers into
  `app/services/ingestion/importer.py`; the CLI imports these helpers. Application
  ingestion no longer depends on a runnable script.
- Changed imports and mock patch targets to `app.*`, `scripts.*` and `tests.*`.
  Removed both `sys.path.insert` workarounds and centralized all repository paths.
- Kept `backend/.env` and `backend/.env.example` at their existing locations.
  Environment variables override the explicitly resolved local `.env`.
- Preserved all old assertion bodies/expected values. Three existing standalone
  PostgreSQL regression runners are now discoverable unittest cases, gated by
  `SHADOWWATCH_RUN_POSTGRES_TESTS=1`. Report-only programs are named `report_*`.
- Protected historical report/authoring scripts with explicit main entry points;
  importing packages no longer runs reports or writes source CSVs.
- Updated maintained documentation commands, README and ignore rules. The original
  behaviour handoff is retained with an explicit historical-document banner.
- Deleted only 44 generated `.pyc` files in retired directories and the resulting
  empty folders, including the unused root `analytics/` placeholder. No source, test, dataset, repair backup or source archive was
  deleted. The ZIP is retained under `work/source_archives/`.

The JSON [manifest](refactor_manifest.json) lists every moved path and removed
bytecode file. [Verification](refactor_verification.md) records results and exact
commands. `git mv` staged the tracked renames; subsequent content edits may be
unstaged. No commit or push was made.
