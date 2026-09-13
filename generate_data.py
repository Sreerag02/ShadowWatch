import pandas as pd
import random
from datetime import datetime, timedelta
import os

OUT_DIR = "data/member_5"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Entities
ENTITY = {"entity_id": "E005", "entity_name": "PowerGrid Utility", "sector": "Energy", "peer_group": "Energy", "country": "India"}
pd.DataFrame([ENTITY]).to_csv(f"{OUT_DIR}/entities.csv", index=False)

# 2. Assets (20-40 assets)
asset_types = ["SCADA-Control-Server", "Substation-Firewall", "Smart-Grid-Gateway", "ICS-Endpoint"]
assets = [{"asset_id": f"E005-AS{str(i).zfill(3)}", "entity_id": "E005", "asset_name": f"{random.choice(asset_types)}-{i}", "asset_type": "SERVER", "criticality": random.choice(["HIGH", "CRITICAL"]), "business_function": "Grid Operations", "monitoring_expected": True} for i in range(1, 31)]
pd.DataFrame(assets).to_csv(f"{OUT_DIR}/assets.csv", index=False)

# 3, 4, 5, 6. Alerts, Cases, Investigations, Escalations
alerts, cases, investigations, escalations = [], [], [], []
start_time = datetime(2026, 8, 1, 8, 0)
investigation_notes = [
    "Reviewed SCADA traffic logs. No anomalies detected.",
    "Analyzed firewall denied connections. Routine port scanning dropped.",
    "Inspected ICS endpoint baseline. Process execution authorized.",
    "Verified authentication logs. Legitimate admin login confirmed."
]

for i in range(1, 201):
    a_id = f"E005-A{str(i).zfill(4)}"
    asset = random.choice(assets)["asset_id"]
    a_time = start_time + timedelta(hours=i*2, minutes=random.randint(1, 45))
    alerts.append({"alert_id": a_id, "entity_id": "E005", "asset_id": asset, "timestamp": a_time.strftime("%Y-%m-%d %H:%M:%S"), "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]), "category": "MALWARE", "source": "SIEM", "confidence": round(random.uniform(0.6, 0.99), 2), "status": "CLOSED", "description": "Suspicious network activity"})
    
    if i <= 100: # ~100 cases
        c_id = f"E005-C{str(i).zfill(4)}"
        c_open = a_time + timedelta(minutes=random.randint(1, 15))
        c_close = c_open + timedelta(minutes=random.randint(45, 180))
        cases.append({"case_id": c_id, "alert_id": a_id, "entity_id": "E005", "analyst_id": "AN01", "opened_at": c_open.strftime("%Y-%m-%d %H:%M:%S"), "closed_at": c_close.strftime("%Y-%m-%d %H:%M:%S"), "status": "CLOSED", "resolution": "TRUE_POSITIVE", "closure_reason": "Threat mitigated"})
        
        # ~100 Investigations
        inv_start = c_open + timedelta(minutes=random.randint(1, 20))
        investigations.append({"investigation_id": f"E005-INV{str(i).zfill(4)}", "case_id": c_id, "started_at": inv_start.strftime("%Y-%m-%d %H:%M:%S"), "completed_at": (c_close - timedelta(minutes=random.randint(5, 15))).strftime("%Y-%m-%d %H:%M:%S"), "analyst_id": "AN01", "analyst_notes": random.choice(investigation_notes), "evidence_present": True, "evidence_count": random.randint(1, 5), "root_cause_identified": True})
        
        # 50-80 Escalations
        if i <= 60:
            escalations.append({"escalation_id": f"E005-ESC{str(i).zfill(4)}", "case_id": c_id, "escalated": True, "escalation_level": "L2", "escalated_at": (c_open + timedelta(minutes=random.randint(5, 30))).strftime("%Y-%m-%d %H:%M:%S"), "escalated_to": "SOC_L2", "reason": "Further analysis required"})

pd.DataFrame(alerts).to_csv(f"{OUT_DIR}/alerts.csv", index=False)
pd.DataFrame(cases).to_csv(f"{OUT_DIR}/cases.csv", index=False)
pd.DataFrame(investigations).to_csv(f"{OUT_DIR}/investigations.csv", index=False)
pd.DataFrame(escalations).to_csv(f"{OUT_DIR}/escalations.csv", index=False)

# 7. Telemetry (Hourly events for 30 assets over 48 hours = 1440 records)
telemetry = []
for idx, asset in enumerate(assets):
    for h in range(48):
        t_time = start_time + timedelta(hours=h)
        telemetry.append({"telemetry_id": f"E005-T{str((idx*48)+h+1).zfill(6)}", "entity_id": "E005", "asset_id": asset["asset_id"], "timestamp": t_time.strftime("%Y-%m-%d %H:%M:%S"), "source_type": "EDR", "event_count": random.randint(900, 1100), "expected_event_count": 1000, "status": "ACTIVE"})
pd.DataFrame(telemetry).to_csv(f"{OUT_DIR}/telemetry.csv", index=False)

print(f"Data generation complete. 7 files created in {OUT_DIR}/")