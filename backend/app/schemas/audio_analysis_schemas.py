from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING # Import TYPE_CHECKING

from .text_analysis_schemas import ( # These are direct dependencies, not circular with EWSAlert here
    GCPSentimentOutput, 
    GCPRiskAssessmentOutput,
    KeywordMatch, 
    PeaceGuardRiskOutput
)

# Import EWSAlert under TYPE_CHECKING if it's hinted here
if TYPE_CHECKING:
    from .ews_schemas import EWSAlert 

class EmbeddedTextAnalysisResult(BaseModel):
    detected_language_by_translate_api: Optional[str] = Field(None, alias="text_detected_language")
    gcp_sentiment: Optional[GCPSentimentOutput] = None
    gcp_risk_assessment: Optional[GCPRiskAssessmentOutput] = None
    keyword_analysis_score: float = 0.0
    flagged_keywords: List[KeywordMatch] = Field(default_factory=list)
    peaceguard_risk: Optional[PeaceGuardRiskOutput] = None
    ews_alerts: Optional[List['EWSAlert']] = None # MODIFIED: Use string literal 'EWSAlert'
    overall_explanation: Optional[str] = None

class AudioAnalysisResponse(BaseModel):
    original_transcript: Optional[str] = None
    stt_confidence: Optional[float] = None
    stt_error: Optional[str] = None
    stt_detected_language_code: Optional[str] = None
    text_analysis_results: Optional[EmbeddedTextAnalysisResult] = None
    overall_process_error: Optional[str] = None