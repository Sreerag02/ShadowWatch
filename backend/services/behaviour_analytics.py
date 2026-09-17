import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def has_internal_repetition(note):
    """
    Checks whether the investigation note repeats
    the same sentence or phrase multiple times.
    """

    # Split note into sentences
    sentences = re.split(r"[.!?]+", note)

    # Clean sentences
    sentences = [
        s.strip().lower()
        for s in sentences
        if s.strip()
    ]

    # Need at least two sentences
    if len(sentences) < 2:
        return False

    # Check for duplicate sentences
    return len(sentences) != len(set(sentences))


def detect_repetitive_investigations(
    investigations_df,
    similarity_threshold=0.90
):
    """
    R006 - Detect repetitive/copied investigation notes.

    A finding is generated when:
    1. Notes are highly similar across different cases, AND
    2. The repeated note contains evidence of internal repetition.

    This keeps the detector explainable and reduces false positives
    from normal reusable investigation templates.
    """

    required_columns = [
        "investigation_id",
        "case_id",
        "analyst_id",
        "analyst_notes"
    ]

    # ---------------------------------------------------------
    # 1. Validate columns
    # ---------------------------------------------------------

    missing_columns = [
        column
        for column in required_columns
        if column not in investigations_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # ---------------------------------------------------------
    # 2. Prepare data
    # ---------------------------------------------------------

    df = investigations_df.copy()

    df["analyst_notes"] = (
        df["analyst_notes"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df = df[
        df["analyst_notes"] != ""
    ].reset_index(drop=True)

    if len(df) < 2:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # 3. Identify notes with internal repetition
    # ---------------------------------------------------------

    df["internally_repetitive"] = df[
        "analyst_notes"
    ].apply(has_internal_repetition)

    # ---------------------------------------------------------
    # 4. TF-IDF
    # ---------------------------------------------------------

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english"
    )

    tfidf_matrix = vectorizer.fit_transform(
        df["analyst_notes"]
    )

    # ---------------------------------------------------------
    # 5. Cosine similarity
    # ---------------------------------------------------------

    similarity_matrix = cosine_similarity(
        tfidf_matrix
    )

    # ---------------------------------------------------------
    # 6. Find similar investigations
    # ---------------------------------------------------------

    findings = []
    visited = set()

    for i in range(len(df)):

        if i in visited:
            continue

        group = [i]

        for j in range(i + 1, len(df)):

            if j in visited:
                continue

            # Must belong to different cases
            if df.loc[i, "case_id"] == df.loc[j, "case_id"]:
                continue

            similarity = similarity_matrix[i][j]

            if similarity >= similarity_threshold:
                group.append(j)

        # -----------------------------------------------------
        # 7. Check whether group contains internal repetition
        # -----------------------------------------------------

        repetitive_records = [
            index
            for index in group
            if df.loc[index, "internally_repetitive"]
        ]

        if repetitive_records and len(group) >= 2:

            group_df = df.loc[group]

            # Calculate average similarity
            similarities = []

            for x in range(len(group)):
                for y in range(x + 1, len(group)):
                    similarities.append(
                        similarity_matrix[
                            group[x],
                            group[y]
                        ]
                    )

            average_similarity = (
                sum(similarities) / len(similarities)
                if similarities
                else 1.0
            )

            findings.append({
                "finding_type":
                    "REPETITIVE_INVESTIGATION",

                "case_ids":
                    ", ".join(
                        group_df["case_id"].tolist()
                    ),

                "investigation_ids":
                    ", ".join(
                        group_df["investigation_id"].tolist()
                    ),

                "analyst_ids":
                    ", ".join(
                        sorted(
                            set(
                                group_df["analyst_id"]
                                .tolist()
                            )
                        )
                    ),

                "similarity_score":
                    round(
                        float(average_similarity),
                        4
                    ),

                "repetition_count":
                    len(group),

                "reason":
                    (
                        "Highly similar investigation notes "
                        "were reused across different cases, "
                        "and the repeated note contains "
                        "internally duplicated text."
                    )
            })

            visited.update(group)

    return pd.DataFrame(findings)

def detect_duration_anomalies(
    investigations_df,
    cases_df,
    alerts_df,
    minimum_deviation_ratio=0.25
):
    """
    R007 - Detect investigation duration anomalies.

    An investigation is flagged when:

    1. The investigation duration is substantially shorter
       than the baseline for its alert severity.
    2. The alert severity is CRITICAL.
    3. The case closure reason indicates unusually fast closure.

    Duration is calculated from started_at and completed_at.

    A severity-specific median is used as the duration baseline.
    """

    required_investigation_columns = [
        "investigation_id",
        "case_id",
        "started_at",
        "completed_at"
    ]

    required_case_columns = [
        "case_id",
        "alert_id",
        "closure_reason"
    ]

    required_alert_columns = [
        "alert_id",
        "severity",
        "category"
    ]

    missing_investigation = [
        column
        for column in required_investigation_columns
        if column not in investigations_df.columns
    ]

    missing_cases = [
        column
        for column in required_case_columns
        if column not in cases_df.columns
    ]

    missing_alerts = [
        column
        for column in required_alert_columns
        if column not in alerts_df.columns
    ]

    if missing_investigation:
        raise ValueError(
            f"Missing investigation columns: {missing_investigation}"
        )

    if missing_cases:
        raise ValueError(
            f"Missing case columns: {missing_cases}"
        )

    if missing_alerts:
        raise ValueError(
            f"Missing alert columns: {missing_alerts}"
        )

    # ---------------------------------------------------------
    # Copy data
    # ---------------------------------------------------------

    investigations = investigations_df.copy()
    cases = cases_df.copy()
    alerts = alerts_df.copy()

    # ---------------------------------------------------------
    # Convert timestamps
    # ---------------------------------------------------------

    investigations["started_at"] = pd.to_datetime(
        investigations["started_at"],
        errors="coerce"
    )

    investigations["completed_at"] = pd.to_datetime(
        investigations["completed_at"],
        errors="coerce"
    )

    # ---------------------------------------------------------
    # Calculate duration
    # ---------------------------------------------------------

    investigations["duration_minutes"] = (
        investigations["completed_at"]
        - investigations["started_at"]
    ).dt.total_seconds() / 60

    investigations = investigations[
        investigations["duration_minutes"].notna()
    ]

    investigations = investigations[
        investigations["duration_minutes"] >= 0
    ]

    if investigations.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Join investigations with cases
    # ---------------------------------------------------------

    analysis_df = investigations.merge(
        cases[
            [
                "case_id",
                "alert_id",
                "closure_reason"
            ]
        ],
        on="case_id",
        how="left"
    )

    # ---------------------------------------------------------
    # Join with alerts
    # ---------------------------------------------------------

    analysis_df = analysis_df.merge(
        alerts[
            [
                "alert_id",
                "severity",
                "category"
            ]
        ],
        on="alert_id",
        how="left"
    )

    analysis_df = analysis_df[
        analysis_df["severity"].notna()
    ]

    if analysis_df.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Severity-specific duration baselines
    # ---------------------------------------------------------

    severity_baselines = (
        analysis_df
        .groupby("severity")["duration_minutes"]
        .median()
        .to_dict()
    )

    findings = []

    # ---------------------------------------------------------
    # Detect R007
    # ---------------------------------------------------------

    for _, row in analysis_df.iterrows():

        severity = row["severity"]
        duration = row["duration_minutes"]

        baseline = severity_baselines.get(
            severity
        )

        if baseline is None or baseline <= 0:
            continue

        duration_ratio = duration / baseline

        # R007 conditions
        is_critical = severity == "CRITICAL"

        is_unusually_fast = (
            duration_ratio < minimum_deviation_ratio
        )

        closure_reason = str(
            row["closure_reason"]
        ).strip().lower()

        indicates_fast_closure = (
            "closed unusually quickly"
            in closure_reason
        )

        if (
            is_critical
            and is_unusually_fast
            and indicates_fast_closure
        ):

            findings.append({

                "finding_type":
                    "INVESTIGATION_DURATION_ANOMALY",

                "case_id":
                    row["case_id"],

                "investigation_id":
                    row["investigation_id"],

                "severity":
                    severity,

                "category":
                    row["category"],

                "duration_minutes":
                    round(
                        float(duration),
                        2
                    ),

                "baseline_duration_minutes":
                    round(
                        float(baseline),
                        2
                    ),

                "duration_ratio":
                    round(
                        float(duration_ratio),
                        4
                    ),

                "closure_reason":
                    row["closure_reason"],

                "reason":
                    (
                        f"CRITICAL investigation completed in "
                        f"{duration:.1f} minutes, substantially "
                        f"below the CRITICAL baseline of "
                        f"{baseline:.1f} minutes, with a closure "
                        f"reason indicating unusually fast closure."
                    )
            })

    return pd.DataFrame(findings)

def detect_repeat_incidents(
    alerts_df,
    cases_df,
    recurrence_window_days=10,
    minimum_incidents=4
):
    """
    R008 - Detect repeat incident patterns.

    A repeat incident pattern is identified when at least
    `minimum_incidents` investigated cases involving the same
    entity, asset, and category occur within the recurrence
    window.

    Only alerts associated with a case are considered.
    """

    required_alert_columns = [
        "alert_id",
        "entity_id",
        "asset_id",
        "timestamp",
        "severity",
        "category"
    ]

    required_case_columns = [
        "case_id",
        "alert_id"
    ]

    missing_alert_columns = [
        column
        for column in required_alert_columns
        if column not in alerts_df.columns
    ]

    missing_case_columns = [
        column
        for column in required_case_columns
        if column not in cases_df.columns
    ]

    if missing_alert_columns:
        raise ValueError(
            f"Missing alert columns: {missing_alert_columns}"
        )

    if missing_case_columns:
        raise ValueError(
            f"Missing case columns: {missing_case_columns}"
        )

    alerts = alerts_df.copy()
    cases = cases_df.copy()

    alerts["timestamp"] = pd.to_datetime(
        alerts["timestamp"],
        errors="coerce"
    )

    alerts = alerts[
        alerts["timestamp"].notna()
    ].copy()

    if alerts.empty:
        return pd.DataFrame()

    # Join alerts with cases
    incident_df = alerts.merge(
        cases[
            [
                "case_id",
                "alert_id"
            ]
        ],
        on="alert_id",
        how="inner"
    )

    if incident_df.empty:
        return pd.DataFrame()

    # One record per case
    incident_df = incident_df.drop_duplicates(
        subset=["case_id"]
    )

    # Sort chronologically
    incident_df = incident_df.sort_values(
        [
            "entity_id",
            "asset_id",
            "category",
            "timestamp"
        ]
    ).reset_index(drop=True)

    findings = []

    grouped = incident_df.groupby(
        [
            "entity_id",
            "asset_id",
            "category"
        ]
    )

    for (
        entity_id,
        asset_id,
        category
    ), group in grouped:

        group = group.sort_values(
            "timestamp"
        ).reset_index(drop=True)

        if len(group) < minimum_incidents:
            continue

        # ---------------------------------------------
        # Search for a qualifying recurrence window
        # ---------------------------------------------

        for start_index in range(
            len(group) - minimum_incidents + 1
        ):

            first_time = group.iloc[
                start_index
            ]["timestamp"]

            # Find the latest incident that is still
            # inside the recurrence window.
            window_end = first_time + pd.Timedelta(
                days=recurrence_window_days
            )

            window = group[
                (group["timestamp"] >= first_time)
                &
                (group["timestamp"] <= window_end)
            ].iloc[:minimum_incidents]

            if len(window) < minimum_incidents:
                continue

            # -----------------------------------------
            # Qualifying recurrence pattern found
            # -----------------------------------------

            last_time = window.iloc[-1]["timestamp"]

            time_span_days = (
                last_time - first_time
            ).total_seconds() / 86400

            findings.append({
                "finding_type":
                    "REPEAT_INCIDENT_PATTERN",

                "entity_id":
                    entity_id,

                "asset_id":
                    asset_id,

                "category":
                    category,

                "case_ids":
                    ", ".join(
                        window["case_id"]
                        .astype(str)
                        .tolist()
                    ),

                "alert_ids":
                    ", ".join(
                        window["alert_id"]
                        .astype(str)
                        .tolist()
                    ),

                "incident_count":
                    len(window),

                "first_timestamp":
                    first_time,

                "last_timestamp":
                    last_time,

                "time_span_days":
                    round(
                        float(time_span_days),
                        2
                    ),

                "reason":
                    (
                        f"{len(window)} investigated incidents "
                        f"with category '{category}' occurred "
                        f"on asset '{asset_id}' within "
                        f"{time_span_days:.2f} days."
                    )
            })

            # Only one finding per qualifying group
            break

    return pd.DataFrame(findings)

def detect_combined_suspicious_behaviour(
    r006_findings,
    r007_findings,
    r008_findings,
    minimum_rules=2
):
    """
    R009 - Detect combined suspicious investigation behaviour.

    A case is flagged when evidence from at least
    `minimum_rules` different behavioural detectors is present.

    The output preserves the evidence and explanation from
    R006, R007 and R008 instead of creating an opaque score.
    """

    if minimum_rules < 2:
        raise ValueError(
            "minimum_rules must be at least 2"
        )

    if r006_findings is None:
        r006_findings = pd.DataFrame()

    if r007_findings is None:
        r007_findings = pd.DataFrame()

    if r008_findings is None:
        r008_findings = pd.DataFrame()

    case_evidence = {}

    def add_case_evidence(
        case_id,
        rule_id,
        finding
    ):
        """
        Store detector evidence for a case.
        """

        if not case_id:
            return

        if case_id not in case_evidence:
            case_evidence[case_id] = {}

        if rule_id not in case_evidence[case_id]:
            case_evidence[case_id][rule_id] = []

        case_evidence[case_id][rule_id].append(
            finding
        )

    # ---------------------------------------------------------
    # R006 evidence
    # ---------------------------------------------------------

    if not r006_findings.empty:

        for _, finding in r006_findings.iterrows():

            case_ids = str(
                finding.get("case_ids", "")
            ).split(",")

            for case_id in case_ids:

                case_id = case_id.strip()

                if case_id:
                    add_case_evidence(
                        case_id,
                        "R006",
                        finding.to_dict()
                    )

    # ---------------------------------------------------------
    # R007 evidence
    # ---------------------------------------------------------

    if not r007_findings.empty:

        for _, finding in r007_findings.iterrows():

            case_id = str(
                finding.get("case_id", "")
            ).strip()

            if case_id:
                add_case_evidence(
                    case_id,
                    "R007",
                    finding.to_dict()
                )

    # ---------------------------------------------------------
    # R008 evidence
    # ---------------------------------------------------------

    if not r008_findings.empty:

        for _, finding in r008_findings.iterrows():

            case_ids = str(
                finding.get("case_ids", "")
            ).split(",")

            for case_id in case_ids:

                case_id = case_id.strip()

                if case_id:
                    add_case_evidence(
                        case_id,
                        "R008",
                        finding.to_dict()
                    )

    # ---------------------------------------------------------
    # Build combined findings
    # ---------------------------------------------------------

    findings = []

    for case_id, rule_evidence in case_evidence.items():

        triggered_rules = sorted(
            rule_evidence.keys()
        )

        if len(triggered_rules) < minimum_rules:
            continue

        evidence_parts = []

        # -----------------------------------------------------
        # R006 explanation
        # -----------------------------------------------------

        if "R006" in rule_evidence:

            for finding in rule_evidence["R006"]:

                similarity = finding.get(
                    "similarity_score"
                )

                repetition_count = finding.get(
                    "repetition_count"
                )

                evidence_parts.append(
                    "R006: Investigation notes showed "
                    f"high similarity (score={similarity}) "
                    f"across cases, with repeated investigation "
                    f"text ({repetition_count} related records)."
                )

        # -----------------------------------------------------
        # R007 explanation
        # -----------------------------------------------------

        if "R007" in rule_evidence:

            for finding in rule_evidence["R007"]:

                duration = finding.get(
                    "duration_minutes"
                )

                baseline = finding.get(
                    "baseline_duration_minutes"
                )

                ratio = finding.get(
                    "duration_ratio"
                )

                evidence_parts.append(
                    "R007: Investigation duration was "
                    f"{duration} minutes compared with a "
                    f"severity-specific baseline of "
                    f"{baseline} minutes "
                    f"(duration ratio={ratio}), with a "
                    "closure reason indicating unusually "
                    "fast closure."
                )

        # -----------------------------------------------------
        # R008 explanation
        # -----------------------------------------------------

        if "R008" in rule_evidence:

            for finding in rule_evidence["R008"]:

                asset_id = finding.get(
                    "asset_id"
                )

                category = finding.get(
                    "category"
                )

                incident_count = finding.get(
                    "incident_count"
                )

                time_span = finding.get(
                    "time_span_days"
                )

                evidence_parts.append(
                    "R008: The asset "
                    f"{asset_id} experienced "
                    f"{incident_count} investigated "
                    f"'{category}' incidents within "
                    f"{time_span} days."
                )

        reason = (
            f"Case {case_id} triggered "
            f"{len(triggered_rules)} behavioural rules "
            f"({', '.join(triggered_rules)})."
        )

        findings.append({

            "finding_type":
                "COMBINED_SUSPICIOUS_INVESTIGATION_BEHAVIOUR",

            "case_id":
                case_id,

            "triggered_rules":
                ", ".join(triggered_rules),

            "rule_count":
                len(triggered_rules),

            "evidence":
                " ".join(evidence_parts),

            "reason":
                reason
        })

    return pd.DataFrame(findings)