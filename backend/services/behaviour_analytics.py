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