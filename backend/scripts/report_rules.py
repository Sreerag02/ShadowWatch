"""Preserved historical report; execute explicitly as a module."""

def main():
    from app.services.analytics.rule_engine import analyze_critical_cases


    print("\n======================================")
    print(" SHADOWWATCH RULE ENGINE V1")
    print("======================================\n")


    findings = analyze_critical_cases()


    print("Total suspicious critical cases:", len(findings))


    for finding in findings:

        print("\n--------------------------------------")

        print("Case:", finding["case_id"])
        print("Entity:", finding["entity_id"])
        print("Alert:", finding["alert_id"])
        print("Asset:", finding["asset_id"])
        print("Severity:", finding["severity"])
        print("Category:", finding["category"])

        print("\nTriggered Rules:")

        for rule in finding["rules"]:
            print(" -", rule)

        print("\nReasons:")

        for reason in finding["reasons"]:
            print(" -", reason)


    print("\n======================================")
    print(" ANALYSIS COMPLETE")
    print("======================================")

if __name__ == "__main__":
    main()
