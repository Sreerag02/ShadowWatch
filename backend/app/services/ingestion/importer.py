"""Transactional import of already-validated operational data."""
from sqlalchemy import MetaData, select
from app.services.ingestion.dataset_validation import TABLES


def import_organization(engine, report):
    with engine.begin() as connection:
        return import_validated_connection(connection, report)


def import_validated_connection(connection, report):
    if report['errors']:
        return 'BLOCKED - validation failed'
    entity = report['tables']['entities'][0]
    entity_id = entity['entity_id']
    metadata = MetaData()
    metadata.reflect(bind=connection, only=list(TABLES))
    entities = metadata.tables['entities']
    if connection.execute(select(entities.c.entity_id).where(entities.c.entity_id == entity_id)).first():
        return f'SKIPPED {entity_id} - entity already exists'
    for name in TABLES:
        table = metadata.tables[name]
        rows = report['tables'][name]
        for offset in range(0, len(rows), 500):
            connection.execute(table.insert(), rows[offset:offset + 500])
    # Verify every supplied value before committing, not merely total counts.
    for name in TABLES:
        table = metadata.tables[name]
        key = next(iter(table.primary_key.columns)).name
        expected = {row[key]: row for row in report['tables'][name]}
        for offset in range(0, len(expected), 500):
            ids = list(expected)[offset:offset + 500]
            actual = list(connection.execute(select(table).where(table.c[key].in_(ids))).mappings())
            if len(actual) != len(ids):
                raise ValueError(f'{name}: post-import count mismatch')
            for row in actual:
                if any(row[column] != value for column, value in expected[row[key]].items()):
                    raise ValueError(f'{name} {row[key]}: post-import value mismatch')
    return f'IMPORT SUCCESS {entity_id}'


