"""Preserved historical report; execute explicitly as a module."""

def main():
    import pandas as pd

    from app.services.analytics.rule_engine import analyze_critical_cases


    from app.core.config import DATA_DIR
    GROUND_TRUTH_PATH = DATA_DIR / "alpha_bank/ground_truth.csv"


    RULE_TO_PROBLEM = {
        "R001": "MISSING_INVESTIGATION",
        "R002": "MISSING_EVIDENCE",
        "R003": "MISSING_ESCALATION",
        "R004": "FAST_CRITICAL_CLOSURE",
    }


    print("\n======================================")
    print(" SHADOWWATCH GROUND TRUTH VALIDATION")
    print("======================================\n")


    # --------------------------------------
    # Load injected ground truth
    # --------------------------------------

    ground_truth = pd.read_csv(GROUND_TRUTH_PATH)

    ground_truth = ground_truth[
        ground_truth["expected_detection"] == True
    ]


    # --------------------------------------
    # Get ShadowWatch detections
    # --------------------------------------

    findings = analyze_critical_cases()


    detected = set()

    for finding in findings:

        case_id = finding["case_id"]

        for rule in finding["rules"]:

            if rule in RULE_TO_PROBLEM:

                problem_type = RULE_TO_PROBLEM[rule]

                detected.add(
                    (case_id, problem_type)
                )


    # --------------------------------------
    # Convert ground truth to same format
    # --------------------------------------

    expected = set()

    for _, row in ground_truth.iterrows():

        case_id = row["case_id"]
        problem_type = row["problem_type"]

        if pd.notna(case_id):

            expected.add(
                (case_id, problem_type)
            )


    # --------------------------------------
    # Compare
    # --------------------------------------

    true_positives = expected & detected

    false_positives = detected - expected

    false_negatives = expected - detected


    TP = len(true_positives)
    FP = len(false_positives)
    FN = len(false_negatives)


    # --------------------------------------
    # Metrics
    # --------------------------------------

    precision = (
        TP / (TP + FP)
        if (TP + FP) > 0
        else 0
    )

    recall = (
        TP / (TP + FN)
        if (TP + FN) > 0
        else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )


    # --------------------------------------
    # Results
    # --------------------------------------

    print("Expected scenarios:", len(expected))
    print("Detected scenarios:", len(detected))

    print("\nTrue Positives:", TP)
    print("False Positives:", FP)
    print("False Negatives:", FN)

    print("\nPrecision:", f"{precision * 100:.2f}%")
    print("Recall:", f"{recall * 100:.2f}%")
    print("F1 Score:", f"{f1 * 100:.2f}%")


    print("\n--------------------------------------")
    print("TRUE POSITIVES")
    print("--------------------------------------")

    for item in sorted(true_positives):
        print(item)


    print("\n--------------------------------------")
    print("FALSE POSITIVES")
    print("--------------------------------------")

    for item in sorted(false_positives):
        print(item)


    print("\n--------------------------------------")
    print("FALSE NEGATIVES")
    print("--------------------------------------")

    for item in sorted(false_negatives):
        print(item)


    print("\n======================================")
    print(" VALIDATION COMPLETE")
    print("======================================")

if __name__ == "__main__":
    main()
