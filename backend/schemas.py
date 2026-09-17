"""API contracts preserve SQL NULLs and all linked evidence records."""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class EntityResponse(ORMResponse):
    entity_id: str
    entity_name: str
    sector: str | None = None
    peer_group: str | None = None
    country: str | None = None

class EntitySummaryResponse(EntityResponse):
    asset_count: int
    alert_count: int
    case_count: int
    finding_count: int

class AssetResponse(ORMResponse):
    asset_id: str
    entity_id: str
    asset_name: str
    asset_type: str | None = None
    criticality: str | None = None
    business_function: str | None = None
    monitoring_expected: bool | None = None

class TelemetryResponse(ORMResponse):
    telemetry_id: str
    entity_id: str
    asset_id: str
    timestamp: datetime
    source_type: str | None = None
    event_count: int | None = None
    expected_event_count: int | None = None
    status: str | None = None

class AlertResponse(ORMResponse):
    alert_id: str
    entity_id: str
    asset_id: str | None = None
    timestamp: datetime
    severity: str | None = None
    category: str | None = None
    source: str | None = None
    confidence: float | None = None
    status: str | None = None
    description: str | None = None

class InvestigationResponse(ORMResponse):
    investigation_id: str
    case_id: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    analyst_id: str | None = None
    analyst_notes: str | None = None
    evidence_present: bool | None = None
    evidence_count: int | None = None
    root_cause_identified: bool | None = None

class EscalationResponse(ORMResponse):
    escalation_id: str
    case_id: str
    escalated: bool | None = None
    escalation_level: str | None = None
    escalated_at: datetime | None = None
    escalated_to: str | None = None
    reason: str | None = None

class FindingResponse(BaseModel):
    finding_id: str
    rule_id: str
    problem_type: str
    entity_id: str
    case_id: str | None = None
    alert_id: str | None = None
    asset_id: str | None = None
    severity: str
    source: str
    assessment: Literal['CONFIRMED_GAP', 'INSUFFICIENT_DATA', 'REVIEW_REQUIRED']
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)

class CaseSummaryResponse(ORMResponse):
    case_id: str
    entity_id: str
    alert_id: str
    analyst_id: str | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    status: str | None = None
    resolution: str | None = None
    closure_reason: str | None = None

class CaseResponse(CaseSummaryResponse):
    alert: AlertResponse | None = None
    investigations: list[InvestigationResponse] = Field(default_factory=list)
    escalations: list[EscalationResponse] = Field(default_factory=list)
    # Compatibility views: only populated when exactly one record exists.
    investigation: InvestigationResponse | None = None
    escalation: EscalationResponse | None = None
    findings: list[FindingResponse] = Field(default_factory=list)
    workflow: dict[str, Any] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str
    database: str

class AnalyticsSummaryResponse(BaseModel):
    entity_count: int
    asset_count: int
    alert_count: int
    case_count: int
    investigation_count: int
    escalation_count: int
    telemetry_count: int
    finding_count: int
    findings_by_rule: dict[str, int]
    findings_by_assessment: dict[str, int]
