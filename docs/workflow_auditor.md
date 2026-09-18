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
`confirmed_rules`, `data_issues`, `assessment_complete`,
`closure_minutes`, `closure_policy`, `assessment`, source `records`,
`limitations`, and a human-readable `explanation`.

`None` in `expected` means no policy is defined. `None` in `observed` means
unknown or mixed evidence. Multiple investigation/escalation records are
preserved, and repeated findings from joined rows are deduplicated. Existing
rules still evaluate individual records; a satisfactory record does not erase
a gap in another record. R002 retains its existing behavior for NULL evidence
counts in `triggered_rules`. The auditor excludes a NULL-only R002 trigger from
confirmed `gaps` and lists it under `data_issues`. An explicit false evidence
flag or zero count still establishes an evidence gap. Rule-engine behavior
itself is unchanged.

Assessment values:

- `EXECUTION_GAP`: at least one confirmed gap; additional unknowns are retained.
- `INSUFFICIENT_DATA`: no confirmed gap, but a required check cannot be resolved.
- `NO_GAP`: no gap or unresolved required check within the prototype policy.
- `NOT_ASSESSED`: severity is outside HIGH/CRITICAL scope.

`assessment_complete` is false for insufficient data, mixed confirmed gaps and
unknowns, or out-of-scope cases. It is scoped to the prototype checks, not all
possible SOC obligations. Unknown escalation flags affect CRITICAL assessments;
HIGH has no escalation requirement. Open cases have no mandatory closure deadline
and are not incomplete solely because they lack a closure timestamp. Closed cases
with missing duration data, or negative durations, cannot establish a valid
closure assessment. Negative-duration R004 triggers remain visible but are not
confirmed fast-closure gaps. No assessment certifies compliance.

For Gamma, HIGH cases with NULL evidence counts now report INSUFFICIENT_DATA.
CRITICAL cases with NULL counts retain raw R002 triggers; confirmed missing
escalations or valid fast closures still produce EXECUTION_GAP alongside the
evidence uncertainty. Source IDs identify records needing review.
The available data does not establish evidence quality, a mandatory closure
deadline, a complete stage-order policy, or alert-to-case creation requirements.
The auditor starts from cases, so it cannot identify alerts without cases.

Run from the repository root with the existing local PostgreSQL configuration:

```bash
cd backend
source venv/bin/activate
python3 -m scripts.report_workflow
python3 -m scripts.report_workflow --case E001-C0081
python3 -m scripts.report_workflow --entity E001
python3 -m unittest tests.unit.test_workflow_auditor tests.unit.test_negative_space
python3 -m scripts.report_rules
python3 -m scripts.validate_negative_space
```

The default report shows E001-C0081: investigation present, evidence absent,
escalation absent, closure in 1.3 minutes, R002/R003/R004, EXECUTION_GAP.
Unit tests run without PostgreSQL or environment configuration.
