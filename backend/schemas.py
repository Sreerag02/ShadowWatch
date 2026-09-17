from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ==========================================
# Base & Common Schemas
# ==========================================
class EntityBase(BaseModel):
    entity_id: str
    entity_name: str
    sector: Optional[str] = None
    peer_group: Optional[str] = None
    country: Optional[str] = None

class EntityResponse(EntityBase):
    class Config:
        from_attributes = True

class AssetBase(BaseModel):
    asset_id: str
    entity_id: str
    asset_name: str
    asset_type: Optional[str] = None
    criticality: Optional[str] = None
    monitoring_expected: bool

class TelemetryResponse(BaseModel):
    telemetry_id: str
    asset_id: str
    timestamp: datetime
    event_count: Optional[int] = None
    expected_event_count: Optional[int] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

# ==========================================
# Nested Case Response Components
# ==========================================
class CaseAlertSummary(BaseModel):
    severity: Optional[str] = None
    category: Optional[str] = None
    
    class Config:
        from_attributes = True

class CaseInvestigationSummary(BaseModel):
    evidence_present: bool
    evidence_count: int
    
    class Config:
        from_attributes = True

class CaseEscalationSummary(BaseModel):
    escalated: bool
    
    class Config:
        from_attributes = True

class FindingSummary(BaseModel):
    rule_id: str
    problem_type: str
    severity: str
    reason: Optional[str] = None
    evidence: Optional[str] = None

# ==========================================
# Main Case Response
# ==========================================
class CaseResponse(BaseModel):
    case_id: str
    entity_id: str
    alert: Optional[CaseAlertSummary] = None
    investigation: Optional[CaseInvestigationSummary] = None
    escalation: Optional[CaseEscalationSummary] = None
    findings: List[FindingSummary] = [] # To be populated by engine integration

    class Config:
        from_attributes = True
# appended by Deepa
class EntitySummaryResponse(EntityBase):
    asset_count: int
    alert_count: int
    case_count: int
    
    class Config:
        from_attributes = True