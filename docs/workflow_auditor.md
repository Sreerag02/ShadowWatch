# Workflow Auditor

The auditor compares operational case records with prototype expectations.
It reads existing alerts, cases, investigations, and escalations; it does not
read ground truth or write to the database.

- `audit_case_workflow(case_id)` returns a JSON-serializable dictionary, or
  `None` for an unknown case.
- `audit_entity_workflows(entity_id)` returns HIGH/CRITICAL case assessments,
  sorted by case ID, or an empty list for an entity without matching cases.
- `assess_case_workflow(rows)` evaluates joined database-shaped rows without
  a database connection, for tests and future integrations.

CRITICAL expectations reuse the existing R001–R004 evaluator. Investigation,
supporting evidence, and escalation are expected. Closure below the configurable
10-minute prototype threshold triggers R004. HIGH cases expect investigation
and evidence under explicit auditor prototype policy; their gaps have no R rule
ID. No HIGH escalation policy or closure timing threshold is inferred.

The response contains `expected`, `observed`, `gaps`, `triggered_rules`,
`closure_minutes`, `closure_policy`, `assessment`, source `records`,
`limitations`, and a human-readable `explanation`.

`None` in `expected` means no policy is defined. `None` in `observed` means
unknown or mixed evidence. Multiple investigation/escalation records are
preserved, and repeated findings from joined rows are deduplicated. Existing
rules still evaluate individual records; a satisfactory record does not erase
a gap in another record. R002 retains its existing behavior for NULL evidence
counts, with an explicit limitation explaining the uncertainty.

`EXECUTION_GAP` means an evaluated expectation has a recorded gap. `NO_GAP`
means no evaluated gap was found, not certified compliance. Check limitations
and `assessment_in_scope`, especially for nullable fields and other severities.
The available data does not establish evidence quality, a mandatory closure
deadline, a complete stage-order policy, or alert-to-case creation requirements.
The auditor starts from cases, so it cannot identify alerts without cases.

Run from the repository root with the existing local PostgreSQL configuration:

```bash
cd backend
source venv/bin/activate
python3 test_workflow_auditor.py
python3 test_workflow_auditor.py --case E001-C0081
python3 test_workflow_auditor.py --entity E001
python3 -m unittest test_workflow_auditor_unit test_negative_space_unit
python3 test_rule_engine.py
python3 validate_negative_space.py
```

The default report shows E001-C0081: investigation present, evidence absent,
escalation absent, closure in 1.3 minutes, R002/R003/R004, EXECUTION_GAP.
Unit tests run without PostgreSQL or environment configuration.
