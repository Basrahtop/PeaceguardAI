from fastapi import APIRouter, HTTPException
from backend.app.schemas.text_analysis_schemas import TextAnalysisRequest, TextAnalysisResponse
from backend.app.services import text_misinfo_analyzer

router = APIRouter()

@router.post("/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text_endpoint(request: TextAnalysisRequest):
    """
    Receives text input and returns a misinformation analysis.
    - **text**: The text content to analyze.
    - **language** (optional): A hint for the language of the text.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty.")
    
    try:
        analysis_result = text_misinfo_analyzer.analyze_text_content(request)
        return analysis_result
    except Exception as e:
        # TODO: Proper logging
        print(f"Error during analysis: {e}") # Temporary
        raise HTTPException(status_code=500, detail="An error occurred during analysis.")