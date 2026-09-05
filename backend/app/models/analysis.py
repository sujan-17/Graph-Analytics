import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)
    question = Column(Text, nullable=False)
    intent_json = Column(Text, nullable=True)
    plan_json = Column(Text, nullable=True)
    generated_code = Column(Text, nullable=True)
    execution_status = Column(String(50), default="SUCCESS")  # SUCCESS, FAILED, CLARIFICATION_NEEDED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="analyses")
    dataset = relationship("Dataset", back_populates="analyses")
    conversation = relationship("Conversation", back_populates="analyses")
    result = relationship("AnalysisResult", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    saved_insights = relationship("SavedInsight", back_populates="analysis")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False, unique=True)
    result_json = Column(Text, nullable=True)  # DataFrame summary/table as JSON
    chart_json = Column(Text, nullable=True)   # Plotly specification as JSON
    insights = Column(Text, nullable=True)     # Business explanation & recommendations as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="result")
