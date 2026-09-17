"""Offline R006–R009 prototypes. No ground truth, closure phrases or cloud calls."""
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Prototype defaults: calibrate against reviewed peer data, not injected labels.
SIMILARITY_THRESHOLD = 0.90
MIN_NOTE_WORDS = 6
MIN_REPEATED_CASES = 3
MIN_BASELINE_CASES = 5
SHORT_DURATION_RATIO = 0.25
LONG_DURATION_RATIO = 4.0
RECURRENCE_WINDOW_DAYS = 10
MIN_INCIDENTS = 4
MIN_COMBINED_RULES = 2

def _require(df, columns):
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f'Missing required columns: {missing}')

def _unique(df, key):
    _require(df, [key])
    frame = df.drop_duplicates().copy()
    if frame[key].isna().any() or frame[key].duplicated().any():
        raise ValueError(f'Missing/conflicting duplicate {key}')
    return frame

def _investigations(investigations, cases=None):
    _require(investigations, ['investigation_id', 'case_id'])
    result = _unique(investigations, 'investigation_id')
    if cases is not None:
        _require(cases, ['case_id', 'entity_id'])
        parents = _unique(cases, 'case_id')[['case_id', 'entity_id']]
        if 'entity_id' in result:
            result = result.merge(parents, on=['case_id', 'entity_id'], how='inner', validate='many_to_one')
        else:
            result = result.merge(parents, on='case_id', how='inner', validate='many_to_one')
    _require(result, ['entity_id'])
    return result.dropna(subset=['entity_id', 'case_id'])

def has_internal_repetition(note):
    if not isinstance(note, str):
        return False
    sentences = [re.sub(r'\s+', ' ', s.strip().lower()) for s in re.split(r'[.!?]+', note) if s.strip()]
    return len(sentences) != len(set(sentences))

def detect_repetitive_investigations(investigations_df, similarity_threshold=SIMILARITY_THRESHOLD,
                                      cases_df=None, minimum_cases=MIN_REPEATED_CASES,
                                      minimum_words=MIN_NOTE_WORDS):
    """One finding per note with sufficiently similar notes in distinct cases.

    Supply cases_df when investigation rows lack entity_id (as in the DB schema).
    Internal repetition is not required. Boilerplate similarity is a review cue,
    not proof of superficial investigation.
    """
    if not 0 < similarity_threshold <= 1 or minimum_cases < 2 or minimum_words < 1:
        raise ValueError('Invalid repetition thresholds')
    _require(investigations_df, ['analyst_notes'])
    df = _investigations(investigations_df, cases_df)
    if df.empty:
        return pd.DataFrame()
    df['normalized_note'] = df['analyst_notes'].fillna('').astype(str).map(
        lambda s: re.sub(r'\s+', ' ', s.lower()).strip())
    df = df[df['normalized_note'].map(lambda s: len(re.findall(r'\b\w+\b', s)) >= minimum_words)]
    findings = []
    for entity, group in df.groupby('entity_id', sort=True):
        group = group.sort_values(['case_id','investigation_id']).reset_index(drop=True)
        if group['case_id'].nunique() < minimum_cases:
            continue
        try:
            vectors = TfidfVectorizer(lowercase=True, stop_words='english').fit_transform(group['normalized_note'])
        except ValueError as exc:
            if 'empty vocabulary' in str(exc):
                continue
            raise
        similarities = cosine_similarity(vectors)
        case_ids = group['case_id'].to_numpy()
        for i, row in group.iterrows():
            matches = ((case_ids != row['case_id']) &
                       (similarities[i] >= similarity_threshold)).nonzero()[0].tolist()
            related = sorted(set(group.iloc[matches]['case_id']))
            if len(related) + 1 < minimum_cases:
                continue
            score = float(min(similarities[i,j] for j in matches))
            findings.append(dict(rule_id='R006', finding_type='REPETITIVE_INVESTIGATION', entity_id=entity,
                case_id=row['case_id'], investigation_id=row['investigation_id'],
                case_ids=', '.join(sorted([row['case_id'], *related])),
                investigation_ids=', '.join(sorted([row['investigation_id'], *group.iloc[matches]['investigation_id'].tolist()])),
                similarity_score=score, repetition_count=len(related)+1,
                note_excerpt=row['analyst_notes'][:300], similarity_threshold=similarity_threshold,
                reason=f"Investigation {row['investigation_id']} has at least {score:.1%} TF-IDF cosine similarity "
                       f"to notes in {len(related)} other cases in entity {entity}. Review reuse of investigation text."))
    return pd.DataFrame(findings)

def _linked(cases, alerts):
    _require(cases, ['case_id', 'alert_id', 'entity_id'])
    _require(alerts, ['alert_id', 'entity_id', 'severity', 'category'])
    cases, alerts = _unique(cases, 'case_id'), _unique(alerts, 'alert_id')
    return cases[['case_id','alert_id','entity_id']].merge(alerts, on=['alert_id','entity_id'], how='inner', validate='many_to_one')

def detect_duration_anomalies(investigations_df, cases_df, alerts_df,
                              minimum_deviation_ratio=SHORT_DURATION_RATIO,
                              maximum_deviation_ratio=LONG_DURATION_RATIO,
                              minimum_baseline_cases=MIN_BASELINE_CASES):
    """Compare investigation duration to other cases of same entity/severity/category.

    Baseline uses one median per other case; the candidate's case never enters its
    own baseline. Invalid/missing timestamps and sparse/zero baselines are skipped.
    """
    if not 0 < minimum_deviation_ratio < 1 or maximum_deviation_ratio <= 1 or minimum_baseline_cases < 2:
        raise ValueError('Invalid duration thresholds')
    _require(investigations_df, ['started_at','completed_at'])
    inv = _investigations(investigations_df, cases_df)
    joined = inv.merge(_linked(cases_df, alerts_df)[['case_id','entity_id','alert_id','severity','category']],
                       on=['case_id','entity_id'], how='inner', validate='many_to_one')
    start = pd.to_datetime(joined['started_at'], errors='coerce', format='mixed', utc=True)
    end = pd.to_datetime(joined['completed_at'], errors='coerce', format='mixed', utc=True)
    joined['duration_minutes'] = (end-start).dt.total_seconds()/60
    joined = joined[joined['duration_minutes'].notna() & (joined['duration_minutes'] >= 0)]
    findings = []
    for _, group in joined.groupby(['entity_id','severity','category'], sort=True):
        for _, row in group.sort_values('investigation_id').iterrows():
            peers = group[group['case_id'] != row['case_id']].groupby('case_id')['duration_minutes'].median()
            if len(peers) < minimum_baseline_cases:
                continue
            baseline = float(peers.median())
            if baseline <= 0:
                continue
            duration = float(row['duration_minutes'])
            ratio = duration / baseline
            if minimum_deviation_ratio <= ratio <= maximum_deviation_ratio:
                continue
            direction = 'SHORT' if ratio < minimum_deviation_ratio else 'LONG'
            findings.append(dict(rule_id='R007', finding_type='INVESTIGATION_DURATION_ANOMALY',
                entity_id=row['entity_id'], case_id=row['case_id'], investigation_id=row['investigation_id'],
                alert_id=row['alert_id'], severity=row['severity'], category=row['category'],
                duration_minutes=duration, baseline_duration_minutes=baseline, duration_ratio=ratio,
                baseline_case_count=len(peers), direction=direction,
                reason=f"Investigation {row['investigation_id']} took {duration:.2f} minutes ({direction.lower()}), "
                       f"versus a median of {baseline:.2f} across {len(peers)} other cases with the same "
                       f"entity, severity and category; ratio {ratio:.3f}."))
    return pd.DataFrame(findings)

def detect_repeat_incidents(alerts_df, cases_df, recurrence_window_days=RECURRENCE_WINDOW_DAYS,
                            minimum_incidents=MIN_INCIDENTS):
    """Maximal qualifying windows, counting distinct alerts (not duplicate cases)."""
    if recurrence_window_days <= 0 or minimum_incidents < 2:
        raise ValueError('Invalid recurrence thresholds')
    _require(alerts_df, ['asset_id','timestamp'])
    data = _linked(cases_df, alerts_df)
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce', format='mixed', utc=True)
    data = data.dropna(subset=['asset_id','category','timestamp'])
    findings = []
    for (entity, asset, category), group in data.groupby(['entity_id','asset_id','category'], sort=True):
        times = group[['alert_id','timestamp']].drop_duplicates().sort_values(['timestamp','alert_id'])
        candidates = []
        for first in times['timestamp'].drop_duplicates():
            window = times[(times['timestamp'] >= first) & (times['timestamp'] <= first + pd.Timedelta(days=recurrence_window_days))]
            ids = frozenset(window['alert_id'])
            if len(ids) >= minimum_incidents and not any(ids <= previous for previous in candidates):
                candidates.append(ids)
        for ids in candidates:
            records = group[group['alert_id'].isin(ids)]
            first, last = records['timestamp'].min(), records['timestamp'].max()
            cases = sorted(set(records['case_id']))
            span = (last-first).total_seconds()/86400
            findings.append(dict(rule_id='R008', finding_type='REPEAT_INCIDENT_PATTERN',
                entity_id=entity, asset_id=asset, category=category, case_ids=', '.join(cases),
                alert_ids=', '.join(sorted(ids)), incident_count=len(ids), first_timestamp=first.isoformat(),
                last_timestamp=last.isoformat(), time_span_days=span,
                reason=f"{len(ids)} distinct alerts linked to {len(cases)} cases for {category} on asset "
                       f"{asset} occurred within {span:.2f} days. Review recurring incident handling."))
    return pd.DataFrame(findings)

def detect_combined_suspicious_behaviour(r006_findings, r007_findings, r008_findings, minimum_rules=MIN_COMBINED_RULES):
    if not 2 <= minimum_rules <= 3:
        raise ValueError('minimum_rules must be between 2 and 3')
    combined = {}
    for rule, frame in [('R006',r006_findings),('R007',r007_findings),('R008',r008_findings)]:
        if frame is None or frame.empty:
            continue
        for finding in frame.to_dict('records'):
            entity = finding.get('entity_id')
            if not entity:
                raise ValueError('Behaviour findings require entity_id')
            cases = [finding['case_id']] if finding.get('case_id') else finding['case_ids'].split(', ')
            for case in cases:
                combined.setdefault((entity,case),{}).setdefault(rule,[]).append(finding)
    findings=[]
    for (entity,case), evidence in sorted(combined.items()):
        if len(evidence) >= minimum_rules:
            rules=sorted(evidence)
            findings.append(dict(rule_id='R009',finding_type='COMBINED_SUSPICIOUS_INVESTIGATION_BEHAVIOUR',
                entity_id=entity,case_id=case,triggered_rules=', '.join(rules),rule_count=len(rules),evidence=evidence,
                reason=f"Case {case} has {len(rules)} independent behavioural indicators: " +
                       ' '.join(f"{rule}: {evidence[rule][0]['reason']}" for rule in rules)))
    return pd.DataFrame(findings)

def analyze_behaviour(investigations, cases, alerts):
    r006 = detect_repetitive_investigations(investigations, cases_df=cases)
    r007 = detect_duration_anomalies(investigations,cases,alerts)
    r008 = detect_repeat_incidents(alerts,cases)
    return {'R006':r006,'R007':r007,'R008':r008,
            'R009':detect_combined_suspicious_behaviour(r006,r007,r008)}
