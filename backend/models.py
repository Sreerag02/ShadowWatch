from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Entity(Base):
    __tablename__ = "entities"
    entity_id = Column(String(20), primary_key=True)
    entity_name = Column(String(150), nullable=False)
    sector = Column(String(100))
    peer_group = Column(String(100))
    country = Column(String(100))
    created_at = Column(DateTime)
    
    assets = relationship("Asset", back_populates="entity")
    cases = relationship("Case", back_populates="entity")

class Asset(Base):
    __tablename__ = "assets"
    asset_id = Column(String(20), primary_key=True)
    entity_id = Column(String(20), ForeignKey("entities.entity_id"), nullable=False)
    asset_name = Column(String(150), nullable=False)
    asset_type = Column(String(100))
    criticality = Column(String(20))
    business_function = Column(String(150))
    monitoring_expected = Column(Boolean, default=True)
    
    entity = relationship("Entity", back_populates="assets")
    telemetry = relationship("Telemetry", back_populates="asset")

class Alert(Base):
    __tablename__ = "alerts"
    alert_id = Column(String(30), primary_key=True)
    entity_id = Column(String(20), ForeignKey("entities.entity_id"), nullable=False)
    asset_id = Column(String(20), ForeignKey("assets.asset_id"))
    timestamp = Column(DateTime, nullable=False)
    severity = Column(String(20))
    category = Column(String(100))
    source = Column(String(100))
    confidence = Column(Numeric(5, 4))
    status = Column(String(30))
    description = Column(Text)
    
    case = relationship("Case", back_populates="alert", uselist=False)

class Case(Base):
    __tablename__ = "cases"
    case_id = Column(String(30), primary_key=True)
    alert_id = Column(String(30), ForeignKey("alerts.alert_id"), nullable=False)
    entity_id = Column(String(20), ForeignKey("entities.entity_id"), nullable=False)
    analyst_id = Column(String(30))
    opened_at = Column(DateTime)
    closed_at = Column(DateTime)
    status = Column(String(30))
    resolution = Column(String(100))
    closure_reason = Column(Text)
    
    entity = relationship("Entity", back_populates="cases")
    alert = relationship("Alert", back_populates="case")
    investigation = relationship("Investigation", back_populates="case", uselist=False)
    escalation = relationship("Escalation", back_populates="case", uselist=False)

class Investigation(Base):
    __tablename__ = "investigations"
    investigation_id = Column(String(30), primary_key=True)
    case_id = Column(String(30), ForeignKey("cases.case_id"), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    analyst_id = Column(String(30))
    analyst_notes = Column(Text)
    evidence_present = Column(Boolean, default=False)
    evidence_count = Column(Integer, default=0)
    root_cause_identified = Column(Boolean, default=False)
    
    case = relationship("Case", back_populates="investigation")

class Escalation(Base):
    __tablename__ = "escalations"
    escalation_id = Column(String(30), primary_key=True)
    case_id = Column(String(30), ForeignKey("cases.case_id"), nullable=False)
    escalated = Column(Boolean, default=False)
    escalation_level = Column(String(50))
    escalated_at = Column(DateTime)
    escalated_to = Column(String(100))
    reason = Column(Text)
    
    case = relationship("Case", back_populates="escalation")

class Telemetry(Base):
    __tablename__ = "telemetry"
    telemetry_id = Column(String(30), primary_key=True)
    entity_id = Column(String(20), ForeignKey("entities.entity_id"), nullable=False)
    asset_id = Column(String(20), ForeignKey("assets.asset_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    source_type = Column(String(100))
    event_count = Column(Integer)
    expected_event_count = Column(Integer)
    status = Column(String(30))
    
    asset = relationship("Asset", back_populates="telemetry")