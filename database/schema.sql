CREATE TABLE entities (
    entity_id VARCHAR(20) PRIMARY KEY,
    entity_name VARCHAR(150) NOT NULL,
    sector VARCHAR(100),
    peer_group VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assets (
    asset_id VARCHAR(20) PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL,
    asset_name VARCHAR(150) NOT NULL,
    asset_type VARCHAR(100),
    criticality VARCHAR(20),
    business_function VARCHAR(150),
    monitoring_expected BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE alerts (
    alert_id VARCHAR(30) PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL,
    asset_id VARCHAR(20),
    timestamp TIMESTAMP NOT NULL,
    severity VARCHAR(20),
    category VARCHAR(100),
    source VARCHAR(100),
    confidence DECIMAL(5,4),
    status VARCHAR(30),
    description TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

CREATE TABLE cases (
    case_id VARCHAR(30) PRIMARY KEY,
    alert_id VARCHAR(30) NOT NULL,
    entity_id VARCHAR(20) NOT NULL,
    analyst_id VARCHAR(30),
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    status VARCHAR(30),
    resolution VARCHAR(100),
    closure_reason TEXT,
    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE investigations (
    investigation_id VARCHAR(30) PRIMARY KEY,
    case_id VARCHAR(30) NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    analyst_id VARCHAR(30),
    analyst_notes TEXT,
    evidence_present BOOLEAN DEFAULT FALSE,
    evidence_count INTEGER DEFAULT 0,
    root_cause_identified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE escalations (
    escalation_id VARCHAR(30) PRIMARY KEY,
    case_id VARCHAR(30) NOT NULL,
    escalated BOOLEAN DEFAULT FALSE,
    escalation_level VARCHAR(50),
    escalated_at TIMESTAMP,
    escalated_to VARCHAR(100),
    reason TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE telemetry (
    telemetry_id VARCHAR(30) PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL,
    asset_id VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    source_type VARCHAR(100),
    event_count INTEGER,
    expected_event_count INTEGER,
    status VARCHAR(30),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);