# backend/app/schemas/__init__.py

# Import all your Pydantic models from their respective files
# This order can matter if models depend on others already being defined before rebuild
from .text_analysis_schemas import TextAnalysisRequest, KeywordMatch, GCPSentimentOutput, GCPCategoryMatch, GCPRiskAssessmentOutput, PeaceGuardRiskOutput, TextAnalysisResponse
from .ews_schemas import EWSInput, EWSAlert, EWSCheckResponse # EWSAlert defined here
from .audio_analysis_schemas import EmbeddedTextAnalysisResult, AudioAnalysisResponse


# List of all models that use forward references OR ARE REFERENCED by forward references.
# It's often easier to just rebuild all primary models in your schemas.
# Pydantic V2 uses model_rebuild()
models_to_rebuild = [
    TextAnalysisResponse,       # Uses 'EWSAlert'
    EWSInput,                   # Uses 'PeaceGuardRiskOutput', 'GCPSentimentOutput', etc.
    EmbeddedTextAnalysisResult, # Uses 'EWSAlert'
    AudioAnalysisResponse,      # Contains EmbeddedTextAnalysisResult
    
    # Also good to rebuild the models that were referenced by strings,
    # although it's mainly the models *containing* the string hints that need it.
    # Rebuilding all of them is generally safe and ensures all relationships are resolved.
    PeaceGuardRiskOutput,
    GCPSentimentOutput,
    GCPRiskAssessmentOutput,
    KeywordMatch,
    EWSAlert,
    EWSCheckResponse,
    TextAnalysisRequest
]

for model_cls in models_to_rebuild:
    if hasattr(model_cls, 'model_rebuild'): # Check if it's a Pydantic model (Pydantic V2+)
        model_cls.model_rebuild(force=True) # Rebuild to resolve forward references
    elif hasattr(model_cls, 'update_forward_refs'): # For older Pydantic V1
        model_cls.update_forward_refs()


print("INFO:     Pydantic schemas processed and forward references updated.")