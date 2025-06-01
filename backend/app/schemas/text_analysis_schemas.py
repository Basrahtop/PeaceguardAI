from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING # Import TYPE_CHECKING

# Use TYPE_CHECKING to allow type hints for linters/IDEs without runtime import errors
if TYPE_CHECKING:
    from .ews_schemas import EWSAlert 

class TextAnalysisRequest(BaseModel):
    text: str
    language_hint: Optional[str] = Field(None, alias="language")

class KeywordMatch(BaseModel):
    keyword: str
    count: int

class GCPSentimentOutput(BaseModel):
    sentiment_label: str
    sentiment_score: float
    magnitude: float
    detected_language_by_nlp_api: Optional[str] = None
    details: Optional[str] = None

class GCPCategoryMatch(BaseModel):
    category: str
    confidence: float

class GCPRiskAssessmentOutput(BaseModel):
    risk_categories: List[GCPCategoryMatch] = Field(default_factory=list)
    explanation: Optional[str] = None

class PeaceGuardRiskOutput(BaseModel):
    score: float = Field(..., description="Overall PeaceGuard AI risk score (0.0 to 1.0+).")
    label: str = Field(..., description="Qualitative risk label (Low, Medium, High, Critical).")
    contributing_factors: List[str] = Field(default_factory=list, description="List of factors that contributed to the score.")
    detected_framings: List[str] = Field(default_factory=list, description="Detected manipulative framing techniques.")

class TextAnalysisResponse(BaseModel):
    original_text: str
    detected_language_by_translate_api: Optional[str] = Field(None, alias="detected_language")
    gcp_sentiment: Optional[GCPSentimentOutput] = None
    gcp_risk_assessment: Optional[GCPRiskAssessmentOutput] = None
    keyword_analysis_score: float = 0.0
    flagged_keywords: List[KeywordMatch] = Field(default_factory=list)
    peaceguard_risk: Optional[PeaceGuardRiskOutput] = None
    ews_alerts: Optional[List['EWSAlert']] = None # MODIFIED: Use string literal 'EWSAlert'
    overall_explanation: Optional[str] = "Analysis completed."

# update_forward_refs() or model_rebuild() will be called later, typically in __init__.py or main.py