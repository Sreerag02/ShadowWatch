import pandas as pd

from services.behaviour_analytics import (
    detect_repetitive_investigations,
    detect_duration_anomalies,
    detect_repeat_incidents,
)


print("\n======================================")
print(" SHADOWWATCH BEHAVIOUR EDGE CASE TEST")
print("======================================\n")


# -------------------------------------------------
# TEST 1: Missing / Empty Investigation Notes
# -------------------------------------------------

print("TEST 1: Missing / Empty Notes")

investigations = pd.DataFrame([
    {
        "investigation_id": "INV001",
        "case_id": "C001",
        "analyst_id": "A001",
        "analyst_notes": None
    },
    {
        "investigation_id": "INV002",
        "case_id": "C002",
        "analyst_id": "A002",
        "analyst_notes": ""
    }
])

try:
    result = detect_repetitive_investigations(investigations)

    if result.empty:
        print("PASS: Empty/missing notes handled safely.")
    else:
        print("PASS: Detector completed without crashing.")

except Exception as e:
    print("FAIL:", e)


# -------------------------------------------------
# TEST 2: Identical Notes
# -------------------------------------------------

print("\nTEST 2: Identical Notes")

investigations = pd.DataFrame([
    {
        "investigation_id": "INV001",
        "case_id": "C001",
        "analyst_id": "A001",
        "analyst_notes": (
            "Checked logs. No suspicious activity. "
            "Checked logs. No suspicious activity."
        )
    },
    {
        "investigation_id": "INV002",
        "case_id": "C002",
        "analyst_id": "A002",
        "analyst_notes": (
            "Checked logs. No suspicious activity. "
            "Checked logs. No suspicious activity."
        )
    }
])

try:
    result = detect_repetitive_investigations(
        investigations,
        similarity_threshold=0.90
    )

    if not result.empty:
        print("PASS: Highly similar notes detected.")
        print(result.to_string(index=False))
    else:
        print("WARNING: Identical notes were not flagged.")

except Exception as e:
    print("FAIL:", e)


# -------------------------------------------------
# TEST 3: Clearly Different Notes
# -------------------------------------------------

print("\nTEST 3: Clearly Different Notes")

investigations = pd.DataFrame([
    {
        "investigation_id": "INV003",
        "case_id": "C003",
        "analyst_id": "A003",
        "analyst_notes": "Firewall blocked suspicious external connection."
    },
    {
        "investigation_id": "INV004",
        "case_id": "C004",
        "analyst_id": "A004",
        "analyst_notes": "Database performance issue investigated and resolved."
    }
])

try:
    result = detect_repetitive_investigations(
        investigations,
        similarity_threshold=0.90
    )

    if result.empty:
        print("PASS: Clearly different notes were not flagged.")
    else:
        print("FAIL: Different notes were incorrectly flagged.")
        print(result.to_string(index=False))

except Exception as e:
    print("FAIL:", e)


# -------------------------------------------------
# TEST 4: Missing Timestamps
# -------------------------------------------------

print("\nTEST 4: Missing Timestamps")

investigations = pd.DataFrame([
    {
        "investigation_id": "INV005",
        "case_id": "C005",
        "analyst_id": "A005",
        "started_at": None,
        "completed_at": None,
        "analyst_notes": "Investigation completed."
    }
])

cases = pd.DataFrame([
    {
        "case_id": "C005",
        "alert_id": "AL005",
        "closure_reason": "TEST"
    }
])

alerts = pd.DataFrame([
    {
        "alert_id": "AL005",
        "severity": "HIGH",
        "category": "MALWARE"
    }
])

try:
    result = detect_duration_anomalies(
        investigations,
        cases,
        alerts
    )

    print("PASS: Missing timestamps handled safely.")
    print("Findings:", len(result))

except Exception as e:
    print("FAIL:", e)


# -------------------------------------------------
# TEST 5: Negative Duration
# -------------------------------------------------

print("\nTEST 5: Negative Duration")

investigations = pd.DataFrame([
    {
        "investigation_id": "INV006",
        "case_id": "C006",
        "analyst_id": "A006",
        "started_at": "2026-01-01 12:00:00",
        "completed_at": "2026-01-01 11:00:00",
        "analyst_notes": "Invalid timestamp test."
    }
])

cases = pd.DataFrame([
    {
        "case_id": "C006",
        "alert_id": "AL006",
        "closure_reason": "TEST"
    }
])

alerts = pd.DataFrame([
    {
        "alert_id": "AL006",
        "severity": "HIGH",
        "category": "MALWARE"
    }
])

try:
    result = detect_duration_anomalies(
        investigations,
        cases,
        alerts
    )

    print("PASS: Negative duration handled without crashing.")
    print("Findings:", len(result))

except Exception as e:
    print("FAIL:", e)


# -------------------------------------------------
# TEST 6: Repeat Incident Pattern
# -------------------------------------------------

print("\nTEST 6: Repeat Incident Pattern")

alerts = pd.DataFrame([
    {
        "alert_id": "AL001",
        "entity_id": "E001",
        "asset_id": "AS001",
        "timestamp": "2026-01-01",
        "severity": "HIGH",
        "category": "BRUTE_FORCE"
    },
    {
        "alert_id": "AL002",
        "entity_id": "E001",
        "asset_id": "AS001",
        "timestamp": "2026-01-03",
        "severity": "HIGH",
        "category": "BRUTE_FORCE"
    },
    {
        "alert_id": "AL003",
        "entity_id": "E001",
        "asset_id": "AS001",
        "timestamp": "2026-01-05",
        "severity": "HIGH",
        "category": "BRUTE_FORCE"
    },
    {
        "alert_id": "AL004",
        "entity_id": "E001",
        "asset_id": "AS001",
        "timestamp": "2026-01-07",
        "severity": "HIGH",
        "category": "BRUTE_FORCE"
    }
])

cases = pd.DataFrame([
    {"case_id": "C001", "alert_id": "AL001"},
    {"case_id": "C002", "alert_id": "AL002"},
    {"case_id": "C003", "alert_id": "AL003"},
    {"case_id": "C004", "alert_id": "AL004"}
])

try:
    result = detect_repeat_incidents(
        alerts,
        cases,
        recurrence_window_days=10,
        minimum_incidents=4
    )

    if not result.empty:
        print("PASS: Repeat incident pattern detected.")
        print(result.to_string(index=False))
    else:
        print("FAIL: Repeat incident pattern not detected.")

except Exception as e:
    print("FAIL:", e)


# -------------------------------------------------
# TEST 7: Isolated Incident
# -------------------------------------------------

print("\nTEST 7: Single Isolated Incident")

alerts = pd.DataFrame([
    {
        "alert_id": "AL010",
        "entity_id": "E001",
        "asset_id": "AS002",
        "timestamp": "2026-01-01",
        "severity": "HIGH",
        "category": "PHISHING"
    }
])

cases = pd.DataFrame([
    {
        "case_id": "C010",
        "alert_id": "AL010"
    }
])

try:
    result = detect_repeat_incidents(
        alerts,
        cases,
        recurrence_window_days=10,
        minimum_incidents=4
    )

    if result.empty:
        print("PASS: Isolated incident was not classified as a repeat.")
    else:
        print("FAIL: Isolated incident incorrectly flagged.")

except Exception as e:
    print("FAIL:", e)


print("\n======================================")
print(" EDGE CASE TEST COMPLETE")
print("======================================")