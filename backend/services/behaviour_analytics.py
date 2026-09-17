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