"""Offline dataset validation and an explicit, opt-in Gamma source adapter."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ('entities', 'assets', 'alerts', 'cases', 'investigations', 'escalations', 'telemetry')
HEADERS = {
    'entities': 'entity_id entity_name sector peer_group country',
    'assets': 'asset_id entity_id asset_name asset_type criticality business_function monitoring_expected',
    'alerts': 'alert_id entity_id asset_id timestamp severity category source confidence status description',
    'cases': 'case_id alert_id entity_id analyst_id opened_at closed_at status resolution closure_reason',
    'investigations': 'investigation_id case_id started_at completed_at analyst_id analyst_notes evidence_present evidence_count root_cause_identified',
    'escalations': 'escalation_id case_id escalated escalation_level escalated_at escalated_to reason',
    'telemetry': 'telemetry_id entity_id asset_id timestamp source_type event_count expected_event_count status',
    'ground_truth': 'scenario_id entity_id case_id asset_id problem_type expected_detection',
}
HEADERS = {key: value.split() for key, value in HEADERS.items()}
GAMMA_HEADERS = {
    'entities': 'Member,Organization,Entity ID,Sector'.split(','),
    'assets': 'asset_id entity_id asset_name asset_type criticality'.split(),
    'alerts': 'alert_id entity_id asset_id severity alert_type timestamp'.split(),
    'cases': 'case_id entity_id alert_id severity opened_at closed_at status'.split(),
    'investigations': 'investigation_id entity_id case_id analyst investigation_notes evidence_status duration_minutes'.split(),
    'escalations': 'escalation_id entity_id case_id escalation_level escalated_at reason'.split(),
    'telemetry': 'telemetry_id entity_id asset_id event_type event_status timestamp event_count'.split(),
    'ground_truth': 'scenario_id scenario_type case_id expected_rule'.split(),
}
BOOLS = {'monitoring_expected', 'evidence_present', 'root_cause_identified', 'escalated', 'expected_detection'}
DATES = {'timestamp', 'opened_at', 'closed_at', 'started_at', 'completed_at', 'escalated_at'}
INTS = {'event_count', 'expected_event_count', 'evidence_count'}
RULE_TYPES = dict(R001='MISSING_INVESTIGATION', R002='MISSING_EVIDENCE',
                  R003='MISSING_ESCALATION', R004='FAST_CRITICAL_CLOSURE', NONE='NORMAL_WORKFLOW')
CONTRADICTIONS = dict(C001='CASE_CLOSED_BEFORE_INVESTIGATION_COMPLETED',
                     C002='INVESTIGATION_BEFORE_CASE_OPENED',
                     C003='ESCALATION_AFTER_CASE_CLOSED', C004='ALERT_AFTER_CASE_OPENED')


def adapt_gamma(table, source):
    """Never edit source files or fabricate timestamps/counts from durations."""
    row = {key: source.get(key) for key in HEADERS[table]}
    if table == 'entities':
        row.update(entity_id=source['Entity ID'], entity_name=source['Organization'], sector=source['Sector'])
    if table == 'alerts':
        row['category'] = source['alert_type']
    if table == 'investigations':
        status = source['evidence_status']
        if status not in ('Complete evidence package', 'Missing evidence'):
            raise ValueError(f'Unknown Gamma evidence_status: {status}')
        row.update(analyst_id=source['analyst'], analyst_notes=source['investigation_notes'],
                   evidence_present='true' if status == 'Complete evidence package' else 'false')
    # No escalated boolean, evidence counts, investigation timestamps or source
    # type can be copied from Gamma. Explicit NULL prevents database defaults
    # from inventing false evidence/monitoring assertions.
    if table == 'ground_truth':
        rule = source['expected_rule']
        if rule not in RULE_TYPES:
            raise ValueError(f'Unknown Gamma expected_rule: {rule}')
        row.update(entity_id='E003', problem_type=RULE_TYPES[rule],
                   expected_detection='false' if rule == 'NONE' else 'true')
    for key in ('severity', 'criticality', 'status'):
        if row.get(key):
            row[key] = row[key].upper()
    return row


def convert(row):
    result = {}
    for key, value in row.items():
        value = value.strip() if isinstance(value, str) else value
        if value in ('', None):
            result[key] = None
        elif key in BOOLS:
            if value.lower() not in ('true', 'false'):
                raise ValueError(f'{key}: invalid boolean {value!r}')
            result[key] = value.lower() == 'true'
        elif key in DATES:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is not None:
                raise ValueError(f'{key}: timezone not supported by TIMESTAMP schema')
            result[key] = parsed
        elif key in INTS:
            result[key] = int(value)
            if result[key] < 0:
                raise ValueError(f'{key}: negative count')
        elif key == 'confidence':
            result[key] = Decimal(value)
            if not result[key].is_finite() or not 0 <= result[key] <= 1:
                raise ValueError('confidence must be between 0 and 1')
        else:
            result[key] = value
    return result


def validate_folder(folder, gamma_adapter=False, allow_chronology=(), allow_source_conflicts=(),
                    allow_ground_truth_duplicates=()):
    report = dict(folder=folder.name, tables={}, errors=[], warnings=[], intentional=[])
    errors, warnings = report['errors'], report['warnings']
    gamma = folder.name == 'gamma_bank' and gamma_adapter
    raw = {}
    for table, headers in HEADERS.items():
        path = folder / f'{table}.csv'
        try:
            with path.open(newline='', encoding='utf-8-sig') as handle:
                reader = csv.DictReader(handle)
                expected = GAMMA_HEADERS[table] if gamma else headers
                if reader.fieldnames is None or len(reader.fieldnames) != len(expected) or set(reader.fieldnames) != set(expected):
                    errors.append(f'{path.name}: headers {reader.fieldnames} do not match {expected}')
                    continue
                raw[table] = list(reader)
        except (OSError, csv.Error, UnicodeError) as exc:
            errors.append(f'{path.name}: {exc}')
            continue
        result = []
        for index, source in enumerate(raw[table], 2):
            try:
                if None in source or any(v is None for v in source.values()):
                    raise ValueError('incorrect CSV field count')
                result.append(convert(adapt_gamma(table, source) if gamma else source))
            except (ValueError, InvalidOperation) as exc:
                errors.append(f'{path.name} row {index}: {exc}')
        report['tables'][table] = result
    if len(report['tables']) != len(HEADERS) or errors:
        return report
    tables = report['tables']
    indexes = {}
    for table, rows in tables.items():
        key = HEADERS[table][0]
        indexes[table] = {}
        for line, row in enumerate(rows, 2):
            identity = row[key]
            if not identity or identity in indexes[table]:
                target = warnings if (identity and table == 'ground_truth' and
                                      row.get('entity_id') in allow_ground_truth_duplicates) else errors
                target.append(f'{table}.csv row {line}: missing/duplicate {key} {identity}')
            indexes[table][identity] = row
    if len(tables['entities']) != 1:
        errors.append('entities.csv: require exactly one organization per folder')
    entities = indexes['entities']
    entity_id = next(iter(entities), None)
    report['entity_id'] = entity_id
    if gamma:
        warnings.append('Explicit Gamma adapter: renamed fields/normalized enums; absent fields remain NULL; original CSVs retained.')
        warnings.append('Gamma investigation timestamps/counts, escalation flags, and telemetry source/status are unavailable; relevant checks are unassessable. R002 flags NULL evidence counts.')
        # Alternate child entity columns must be checked before they are omitted.
        for table in ('investigations', 'escalations'):
            for row in raw[table]:
                if row['entity_id'] != entity_id:
                    errors.append(f'{table}.csv {row[HEADERS[table][0]]}: cross-entity child record')
        for row in raw['cases']:
            alert = indexes['alerts'].get(row['alert_id'])
            if alert and row['severity'].upper() != alert['severity']:
                target = warnings if entity_id in allow_source_conflicts else errors
                target.append(f"cases.csv {row['case_id']}: severity conflicts with alert; database retains alert severity")

    def error(table, row, message):
        errors.append(f'{table}.csv {row[HEADERS[table][0]]}: {message}')

    def reference(table, row, key, target, optional=False):
        value = row.get(key)
        if value is None and optional:
            return None
        parent = indexes[target].get(value)
        if parent is None:
            error(table, row, f'{key} {value!r} does not reference {target}')
        elif row.get('entity_id') and parent.get('entity_id') != row['entity_id']:
            error(table, row, f'{key} crosses entity boundary')
        return parent

    for table, rows in tables.items():
        for row in rows:
            if 'entity_id' in row and row['entity_id'] not in entities:
                error(table, row, 'invalid entity_id')
            if table in ('alerts', 'telemetry'):
                reference(table, row, 'asset_id', 'assets', optional=table == 'alerts')
            if table == 'cases':
                reference(table, row, 'alert_id', 'alerts')
            if table in ('investigations', 'escalations'):
                reference(table, row, 'case_id', 'cases')
            if table == 'ground_truth':
                reference(table, row, 'case_id', 'cases', optional=True)
                reference(table, row, 'asset_id', 'assets', optional=True)
            if table == 'alerts' and row['severity'] not in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'):
                error(table, row, f"unsupported severity {row['severity']!r}")
            if table == 'cases' and row['status'] not in ('OPEN', 'IN_PROGRESS', 'CLOSED'):
                error(table, row, f"unsupported case status {row['status']!r}")
            if table in ('alerts', 'telemetry') and row['timestamp'] is None:
                error(table, row, 'required timestamp is NULL')
            if table == 'entities' and not row['entity_name']:
                error(table, row, 'required entity_name is NULL')
            if table == 'assets' and not row['asset_name']:
                error(table, row, 'required asset_name is NULL')

    labels = {(r['case_id'], r['problem_type']) for r in tables['ground_truth'] if r['expected_detection'] is True}

    def chronology(table, row, left, right, message, rule=None):
        if left is None or right is None:
            return
        if left <= right:
            return
        detail = f'{table}.csv {row[HEADERS[table][0]]}: {message} ({left} > {right})'
        if rule and ((row['case_id'], CONTRADICTIONS[rule]) in labels or
                     (row['case_id'], rule) in labels):
            report['intentional'].append(detail)
        elif entity_id in allow_chronology:
            warnings.append('EXPLICITLY ACCEPTED chronology: ' + detail)
        else:
            errors.append(detail)

    for row in tables['cases']:
        alert = indexes['alerts'].get(row['alert_id'], {})
        chronology('cases', row, alert.get('timestamp'), row['opened_at'], 'alert after opening', 'C004')
        chronology('cases', row, row['opened_at'], row['closed_at'], 'opening after closure')
    for row in tables['investigations']:
        case = indexes['cases'].get(row['case_id'], {})
        chronology('investigations', row, case.get('opened_at'), row['started_at'], 'start before case opening', 'C002')
        chronology('investigations', row, row['started_at'], row['completed_at'], 'completion before start')
        chronology('investigations', row, row['completed_at'], case.get('closed_at'), 'completion after closure', 'C001')
    for row in tables['escalations']:
        if row['escalated'] is True or gamma:
            case = indexes['cases'].get(row['case_id'], {})
            chronology('escalations', row, case.get('opened_at'), row['escalated_at'], 'escalation before opening')
            chronology('escalations', row, row['escalated_at'], case.get('closed_at'), 'escalation after closure', 'C003')
    return report


def validate_all(data_dir=None, gamma_adapter=False, allow_chronology=(),
                 allow_source_conflicts=(), allow_ground_truth_duplicates=()):
    folders = sorted(p for p in Path(data_dir or ROOT / 'data').iterdir() if p.is_dir())
    reports = [validate_folder(p, gamma_adapter, allow_chronology, allow_source_conflicts,
                               allow_ground_truth_duplicates) for p in folders]
    seen = {}
    for report in reports:
        for table, rows in report['tables'].items():
            key = HEADERS[table][0]
            for row in rows:
                identity = (table, row[key])
                if identity in seen and seen[identity] != report['folder']:
                    report['errors'].append(f'{table}.csv {row[key]}: ID also exists in {seen[identity]}')
                    for other in reports:
                        if other['folder'] == seen[identity]:
                            other['errors'].append(f'{table}.csv {row[key]}: ID also exists in {report["folder"]}')
                seen[identity] = report['folder']
    return reports


def add_validation_arguments(parser):
    parser.add_argument('--gamma-adapter', action='store_true', help='Explicit Gamma alternate-schema mapping')
    parser.add_argument('--allow-chronology', nargs='*', default=[], metavar='ENTITY_ID')
    parser.add_argument('--allow-source-conflicts', nargs='*', default=[], metavar='ENTITY_ID')
    parser.add_argument('--allow-ground-truth-duplicates', nargs='*', default=[], metavar='ENTITY_ID')


def validation_options(args):
    return {key: getattr(args, key) for key in ('gamma_adapter', 'allow_chronology',
                                               'allow_source_conflicts', 'allow_ground_truth_duplicates')}


def print_reports(reports):
    print('SHADOWWATCH MULTI-DATASET VALIDATION')
    for report in reports:
        print(f"\n{report['folder']} / {report.get('entity_id', 'unknown')}")
        for table, rows in report['tables'].items():
            print(f'  {table}: {len(rows)}')
        for kind in ('errors', 'warnings', 'intentional'):
            for message in report[kind]:
                print(f'  {kind.upper()}: {message}')
        print('  RESULT:', 'FAIL' if report['errors'] else 'PASS WITH WARNINGS' if report['warnings'] else 'PASS')
    failed = any(r['errors'] for r in reports) or not reports
    print(f'\nOrganizations: {len(reports)}')
    complete = all(len(r['tables']) == len(HEADERS) for r in reports)
    duplicate = any('also exists' in e for r in reports for e in r['errors'])
    contamination = any('cross' in e or 'entity_id' in e for r in reports for e in r['errors'])
    print('Cross-organization ID uniqueness:', 'FAIL' if duplicate else 'PASS' if complete else 'NOT FULLY ASSESSED')
    print('Cross-entity contamination:', 'FAIL' if contamination else 'PASS' if complete else 'NOT FULLY ASSESSED')
    print('FINAL RESULT:', 'FAIL' if failed else 'PASS WITH WARNINGS' if any(r['warnings'] for r in reports) else 'PASS')
    return not failed
