"""R005: historical telemetry drops, independent of ground-truth labels."""

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from math import isfinite
from statistics import mean, median


# Prototype thresholds for hourly synthetic telemetry. Calibrate against
# entity/peer history before applying to other environments or cadences.
MIN_BASELINE_POINTS = 6
BASELINE_WINDOW = 24
MIN_BASELINE_ACTIVITY = 10
LOW_ACTIVITY_RATIO = 0.10
CONSECUTIVE_LOW_POINTS = 3
EXPECTED_INTERVAL = timedelta(hours=1)


def _observations(rows):
    """Normalize CSV/SQL rows; ambiguous duplicate intervals become unknown.

    Identical duplicate counts collapse to one observation. Conflicting counts
    (including multiple sources) are not summed: the schema has no contract
    saying they are disjoint. NULL/invalid counts interrupt persistence.
    """
    groups = defaultdict(lambda: defaultdict(set))
    for row in rows:
        entity, asset = row['entity_id'], row['asset_id']
        if not entity or not asset or not row['timestamp']:
            continue
        try:
            timestamp = row['timestamp']
            if not isinstance(timestamp, datetime):
                timestamp = datetime.fromisoformat(timestamp)
            if timestamp.tzinfo is not None:
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
        except (ValueError, TypeError):
            continue
        try:
            count = float(row['event_count'])
            if not isfinite(count) or count < 0 or not count.is_integer():
                count = None
        except (ValueError, TypeError):
            count = None
        groups[(entity, asset)][timestamp].add(count)
    return groups


def _finding(entity, asset, run, baseline):
    observed = mean(count for _, count in run)
    return {
        'rule_id': 'R005',
        'problem_type': 'TELEMETRY_BLIND_SPOT',
        'entity_id': entity,
        'asset_id': asset,
        'start_time': run[0][0].isoformat(sep=' '),
        'end_time': run[-1][0].isoformat(sep=' '),
        'baseline_activity': baseline,
        'observed_activity': observed,
        'drop_percentage': 100 * (1 - observed / baseline),
        'consecutive_low_points': len(run),
        'reason': (
            f'Asset {asset} normally generated approximately {baseline:.1f} '
            f'events per hourly observation (prior historical median), but '
            f'activity averaged {observed:.1f} events for {len(run)} consecutive '
            f'observations, each below {LOW_ACTIVITY_RATIO:.0%} of that baseline. '
            'This indicates a possible monitoring blind spot.'
        ),
    }


def detect_telemetry_blind_spots(rows=None):
    """Return one finding per sustained low episode for each entity/asset.

    With no rows supplied, read operational telemetry using the project's DB
    engine. Explicit rows allow offline CSV evaluation and isolated tests.
    Missing rows are unknown, not zero: gaps reset history and persistence.
    The baseline freezes at episode onset to avoid learning an ongoing outage
    as normal. End time denotes the last observed low timestamp, not recovery.
    """
    if rows is None:
        from sqlalchemy import text
        from app.core.database import engine

        with engine.connect() as connection:
            rows = list(connection.execute(text(
                'SELECT entity_id, asset_id, timestamp, event_count FROM telemetry'
            )).mappings())

    findings = []
    for (entity, asset), observations in sorted(_observations(rows).items()):
        history = deque(maxlen=BASELINE_WINDOW)
        run = []
        baseline = None
        previous = None

        def finish_run():
            if len(run) >= CONSECUTIVE_LOW_POINTS:
                findings.append(_finding(entity, asset, run, baseline))

        for timestamp, counts in sorted(observations.items()):
            count = next(iter(counts)) if len(counts) == 1 else None
            if previous is not None and timestamp - previous != EXPECTED_INTERVAL:
                finish_run()
                run = []
                history.clear()
            previous = timestamp
            if count is None:
                finish_run()
                run = []
                history.clear()
                continue
            if not run:
                baseline = median(history) if len(history) >= MIN_BASELINE_POINTS else None
            low = (baseline is not None and baseline >= MIN_BASELINE_ACTIVITY
                   and count < baseline * LOW_ACTIVITY_RATIO)
            if low:
                run.append((timestamp, count))
            else:
                finish_run()
                # Short dips are ordinary historical observations; confirmed
                # outages are excluded from the normal-activity baseline.
                if len(run) < CONSECUTIVE_LOW_POINTS:
                    history.extend(value for _, value in run)
                run = []
                history.append(count)
        finish_run()
    return findings
