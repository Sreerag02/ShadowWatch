"""Validation and transactional import tests; uses isolated in-memory SQLite."""
import copy
import csv
from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from sqlalchemy import create_engine, event, text

from import_all_entities import import_organization
from verify_multi_entity_db import verify_database
from services.dataset_validation import HEADERS, ROOT, convert, validate_all, validate_folder


def fixture():
    tables = {name: [] for name in HEADERS}
    def add(table, **values):
        row = dict.fromkeys(HEADERS[table])
        row.update(values)
        tables[table].append(row)
    add('entities', entity_id='E9', entity_name='Test Entity')
    add('assets', asset_id='AS9', entity_id='E9', asset_name='Test asset')
    add('alerts', alert_id='A9', entity_id='E9', asset_id='AS9', severity='HIGH', timestamp=datetime(2026, 1, 1))
    add('cases', case_id='C9', entity_id='E9', alert_id='A9', status='CLOSED',
        opened_at=datetime(2026, 1, 1), closed_at=datetime(2026, 1, 2))
    add('investigations', investigation_id='I9', case_id='C9')
    add('escalations', escalation_id='S9', case_id='C9')
    add('telemetry', telemetry_id='T9', entity_id='E9', asset_id='AS9', timestamp=datetime(2026, 1, 1), event_count=5)
    add('ground_truth', scenario_id='GT9', entity_id='E9', case_id='C9', expected_detection=True, problem_type='TEST')
    return dict(folder='test_entity', entity_id='E9', tables=tables, errors=[], warnings=[], intentional=[])


def write_fixture(folder, report):
    folder.mkdir(parents=True, exist_ok=True)
    for table, rows in report['tables'].items():
        with (folder / f'{table}.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADERS[table])
            writer.writeheader()
            writer.writerows(rows)


class MultiEntityTests(unittest.TestCase):
    def setUp(self):
        self.db = create_engine('sqlite:///:memory:')
        @event.listens_for(self.db, 'connect')
        def foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
        with self.db.begin() as connection:
            for statement in (ROOT / 'database/schema.sql').read_text().split(';'):
                if statement.strip():
                    connection.exec_driver_sql(statement)

    def tearDown(self):
        self.db.dispose()

    def test_import_skip_verify_and_no_ground_truth(self):
        report = fixture()
        self.assertIn('SUCCESS', import_organization(self.db, report))
        altered = copy.deepcopy(report)
        altered['tables']['entities'][0]['entity_name'] = 'Do not overwrite'
        self.assertIn('SKIPPED', import_organization(self.db, altered))
        summary, errors = verify_database(self.db, [report])
        self.assertEqual(errors, [])
        self.assertEqual(summary[0]['entity_name'], 'Test Entity')
        with self.db.connect() as connection:
            names = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars().all()
        self.assertNotIn('ground_truth', names)

    def test_late_failure_rolls_back_entire_organization(self):
        report = fixture()
        report['tables']['telemetry'][0]['asset_id'] = 'missing'
        with self.assertRaises(Exception):
            import_organization(self.db, report)
        with self.db.connect() as connection:
            self.assertEqual(connection.execute(text('SELECT count(*) FROM entities')).scalar(), 0)

    def test_validation_blocks_writes(self):
        report = fixture()
        report['errors'] = ['bad source']
        self.assertIn('BLOCKED', import_organization(self.db, report))

    def test_validator_relationships_headers_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'one'
            report = fixture()
            write_fixture(folder, report)
            self.assertFalse(validate_folder(folder)['errors'])
            report['tables']['alerts'][0]['asset_id'] = 'foreign'
            report['tables']['cases'][0]['status'] = 'unsupported'
            report['tables']['assets'].append(report['tables']['assets'][0].copy())
            write_fixture(folder, report)
            errors = '\n'.join(validate_folder(folder)['errors'])
            self.assertIn('does not reference assets', errors)
            self.assertIn('duplicate asset_id', errors)
            self.assertIn('unsupported case status', errors)
            (folder / 'entities.csv').write_text('Unnamed: 0\n1\n')
            self.assertTrue(validate_folder(folder)['errors'])

    def test_cross_organization_ids_fail_both_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ('one', 'two'):
                write_fixture(Path(directory) / name, fixture())
            reports = validate_all(directory)
            self.assertTrue(all(any('also exists' in e for e in r['errors']) for r in reports))

    def test_chronology_requires_specific_label_or_explicit_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            report = fixture()
            report['tables']['investigations'][0]['completed_at'] = datetime(2026, 1, 3)
            write_fixture(folder, report)
            self.assertTrue(validate_folder(folder)['errors'])
            report['tables']['ground_truth'][0]['problem_type'] = 'CASE_CLOSED_BEFORE_INVESTIGATION_COMPLETED'
            write_fixture(folder, report)
            checked = validate_folder(folder)
            self.assertFalse(checked['errors'])
            self.assertEqual(len(checked['intentional']), 1)

    def test_invalid_scalar_values(self):
        for row in ({'confidence': '1.1'}, {'confidence': 'NaN'}, {'evidence_present': 'maybe'},
                    {'timestamp': 'broken'}, {'event_count': '-1'}):
            with self.subTest(row=row), self.assertRaises(ValueError):
                convert(row)

    def test_gamma_adapter_does_not_fabricate_missing_fields(self):
        report = validate_folder(ROOT / 'data/gamma_bank', gamma_adapter=True,
                                 allow_chronology=['E003'], allow_source_conflicts=['E003'])
        self.assertFalse(report['errors'])
        investigation = report['tables']['investigations'][0]
        self.assertIsNone(investigation['started_at'])
        self.assertIsNone(investigation['completed_at'])
        self.assertIsNone(investigation['evidence_count'])
        self.assertTrue(investigation['evidence_present'])
        self.assertIsNone(report['tables']['escalations'][0]['escalated'])

    def test_verifier_detects_wrong_child_link(self):
        report = fixture()
        import_organization(self.db, report)
        with self.db.begin() as connection:
            connection.execute(text("INSERT INTO cases (case_id, entity_id, alert_id) VALUES ('C10', 'E9', 'A9')"))
            connection.execute(text("UPDATE investigations SET case_id='C10'"))
        _, errors = verify_database(self.db, [report])
        self.assertTrue(any('investigations I9' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
