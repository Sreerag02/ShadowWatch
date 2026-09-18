"""Historical PowerGrid dataset authoring tool; explicitly running this modifies CSVs."""

def main():
    import pandas as pd
    import random
    from datetime import datetime, timedelta
    import os

    from app.core.config import DATA_DIR
    OUT_DIR = DATA_DIR / "powergrid_utility"
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Entities
    ENTITY = {"entity_id": "E005", "entity_name": "PowerGrid Utility", "sector": "Energy", "peer_group": "Energy", "country": "India"}
    pd.DataFrame([ENTITY]).to_csv(f"{OUT_DIR}/entities.csv", index=False)

    # 2. Assets
    asset_types = ["SCADA-Control-Server", "Substation-Firewall", "Smart-Grid-Gateway", "ICS-Endpoint"]
    assets = [{"asset_id": f"E005-AS{str(i).zfill(3)}", "entity_id": "E005", "asset_name": f"{random.choice(asset_types)}-{i}", "asset_type": "SERVER", "criticality": random.choice(["HIGH", "CRITICAL"]), "business_function": "Grid Operations", "monitoring_expected": True} for i in range(1, 31)]
    pd.DataFrame(assets).to_csv(f"{OUT_DIR}/assets.csv", index=False)

    # Variance Pools
    categories = ["MALWARE", "RANSOMWARE", "PHISHING", "BRUTE_FORCE", "SUSPICIOUS_LOGIN", "PRIVILEGE_ESCALATION", "DATA_EXFILTRATION"]
    sources = ["SIEM", "EDR", "IDS", "FIREWALL", "IAM", "EMAIL_SECURITY"]
    desc_map = {"MALWARE": "Potential malicious executable", "RANSOMWARE": "Ransomware activity", "PHISHING": "Phishing email delivered", "BRUTE_FORCE": "Repeated failed logins", "SUSPICIOUS_LOGIN": "Multiple suspicious logins", "PRIVILEGE_ESCALATION": "Unusual privilege escalation", "DATA_EXFILTRATION": "Unusual outbound data transfer"}
    analysts = ["AN01", "AN02", "AN03", "AN04", "AN05"]
    resolutions = ["TRUE_POSITIVE", "FALSE_POSITIVE", "BENIGN"]
    closure_reasons = ["Threat mitigated and isolated", "Confirmed false alarm", "Authorized system activity"]
    investigation_notes = ["Reviewed SCADA traffic logs. No anomalies detected.", "Analyzed firewall denied connections.", "Inspected ICS endpoint baseline.", "Verified authentication logs. Legitimate admin login confirmed.", "Isolated host and dumped memory for analysis.", "Reviewed EDR telemetry, process execution blocked."]

    # 3, 4, 5, 6. Alerts, Cases, Investigations, Escalations
    alerts, cases, investigations, escalations = [], [], [], []
    start_time = datetime(2026, 8, 1, 8, 0)

    for i in range(1, 201):
        a_id = f"E005-A{str(i).zfill(4)}"
        asset = random.choice(assets)["asset_id"]
        a_time = start_time + timedelta(hours=i*2, minutes=random.randint(1, 45))
        category = random.choice(categories)
    
        alerts.append({"alert_id": a_id, "entity_id": "E005", "asset_id": asset, "timestamp": a_time.strftime("%Y-%m-%d %H:%M:%S"), "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]), "category": category, "source": random.choice(sources), "confidence": round(random.uniform(0.45, 0.99), 2), "status": "CLOSED", "description": desc_map[category]})
    
        if i <= 100:
            c_id = f"E005-C{str(i).zfill(4)}"
            c_open = a_time + timedelta(minutes=random.randint(1, 15))
            c_close = c_open + timedelta(minutes=random.randint(45, 180))
            cases.append({"case_id": c_id, "alert_id": a_id, "entity_id": "E005", "analyst_id": random.choice(analysts), "opened_at": c_open.strftime("%Y-%m-%d %H:%M:%S"), "closed_at": c_close.strftime("%Y-%m-%d %H:%M:%S"), "status": "CLOSED", "resolution": random.choice(resolutions), "closure_reason": random.choice(closure_reasons)})
        
            inv_start = c_open + timedelta(minutes=random.randint(1, 20))
            investigations.append({"investigation_id": f"E005-INV{str(i).zfill(4)}", "case_id": c_id, "started_at": inv_start.strftime("%Y-%m-%d %H:%M:%S"), "completed_at": (c_close - timedelta(minutes=random.randint(5, 15))).strftime("%Y-%m-%d %H:%M:%S"), "analyst_id": random.choice(analysts), "analyst_notes": random.choice(investigation_notes), "evidence_present": True, "evidence_count": random.randint(1, 12), "root_cause_identified": random.choice([True, False])})
        
            if i <= 60:
                level = random.choice(["L2", "L3"])
                escalations.append({"escalation_id": f"E005-ESC{str(i).zfill(4)}", "case_id": c_id, "escalated": True, "escalation_level": level, "escalated_at": (c_open + timedelta(minutes=random.randint(5, 30))).strftime("%Y-%m-%d %H:%M:%S"), "escalated_to": f"SOC_{level}", "reason": random.choice(["Requires deeper forensic analysis", "Critical asset involved", "Cross-team verification needed"])})

    pd.DataFrame(alerts).to_csv(f"{OUT_DIR}/alerts.csv", index=False)
    pd.DataFrame(cases).to_csv(f"{OUT_DIR}/cases.csv", index=False)
    pd.DataFrame(investigations).to_csv(f"{OUT_DIR}/investigations.csv", index=False)
    pd.DataFrame(escalations).to_csv(f"{OUT_DIR}/escalations.csv", index=False)

    # 7. Telemetry
    telemetry = []
    for idx, asset in enumerate(assets):
        for h in range(48):
            t_time = start_time + timedelta(hours=h)
            telemetry.append({"telemetry_id": f"E005-T{str((idx*48)+h+1).zfill(6)}", "entity_id": "E005", "asset_id": asset["asset_id"], "timestamp": t_time.strftime("%Y-%m-%d %H:%M:%S"), "source_type": random.choice(sources), "event_count": random.randint(850, 1150), "expected_event_count": 1000, "status": "ACTIVE"})
    pd.DataFrame(telemetry).to_csv(f"{OUT_DIR}/telemetry.csv", index=False)

    print(f"Randomized base data generated in {OUT_DIR}/")

if __name__ == "__main__":
    main()
