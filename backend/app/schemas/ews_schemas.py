from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING # Import TYPE_CHECKING

# Use TYPE_CHECKING to allow type hints for linters/IDEs without runtime import errors
if TYPE_CHECKING:
    # These types are defined in text_analysis_schemas.py
    from .text_analysis_schemas import PeaceGuardRiskOutput, GCPSentimentOutput, GCPRiskAssessmentOutput, KeywordMatch

class EWSInput(BaseModel):
    original_text: str
    detected_language: Optional[str] = None
    # MODIFIED: Use string literals for forward references
    peaceguard_risk: 'PeaceGuardRiskOutput' 
    gcp_sentiment: Optional['GCPSentimentOutput'] = None
    gcp_risk_assessment: Optional['GCPRiskAssessmentOutput'] = None
    flagged_keywords: List['KeywordMatch'] = Field(default_factory=list)

class EWSAlert(BaseModel):
    alert_id: str = Field(..., description="Unique ID for the alert pattern triggered.")
    pattern_name: str = Field(..., description="Name of the historical/precursor pattern matched.")
    severity: str = Field(..., description="Severity of the alert (e.g., 'High', 'Critical').")
    description: str = Field(..., description="Description of the detected pattern and potential risk.")
    recommended_action: Optional[str] = None
    implicated_keywords: List[str] = Field(default_factory=list)
    implicated_framings: List[str] = Field(default_factory=list)
    target_audience_suggestion: Optional[str] = "General Public, CSOs, Security Agencies"
    confidence_score: Optional[float] = Field(None, description="Confidence in this specific EWS alert (0.0-1.0)")
    generated_sms_message: Optional[str] = None

class EWSCheckResponse(BaseModel):
    input_text_snippet: str
    triggered_alerts: List[EWSAlert] = Field(default_factory=list)
    status_message: str

# update_forward_refs() or model_rebuild() will be called later