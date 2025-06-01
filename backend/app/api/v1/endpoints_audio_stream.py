from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
# Import the new response model
from backend.app.schemas.audio_analysis_schemas import AudioAnalysisResponse 
from backend.app.services import audio_stream_analyzer

router = APIRouter()

# Update the endpoint name to reflect broader analysis
@router.post("/analyze-audio", response_model=AudioAnalysisResponse) 
async def analyze_audio_endpoint( # Renamed function for clarity
    audio_file: UploadFile = File(..., description="Audio file to analyze (e.g., WAV, FLAC, MP3)."),
    language_code: Optional[str] = Form("en-US", description="BCP-47 language hint for STT (e.g., 'en-US', 'ha-NG').")
    # sample_rate_hertz: Optional[int] = Form(None, description="Sample rate (Hz). Important for raw audio, often inferred for WAV/MP3.")
    # We are not explicitly passing sample_rate_hertz to analyze_audio_content for now
):
    """
    Receives an audio file, transcribes it, performs misinformation analysis on the transcript,
    and returns the combined results.
    """
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file provided.")

    try:
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        # Call the updated service function
        # analyze_audio_content will handle both STT and text analysis
        analysis_result = await audio_stream_analyzer.analyze_audio_content(
            audio_bytes=audio_bytes,
            language_code_stt_hint=language_code,
            # sample_rate_hertz can be passed if extracted or provided by user
        )
        
        if analysis_result.overall_process_error:
            # Log the full error for debugging on the server
            print(f"Audio analysis processing error for file {audio_file.filename}: {analysis_result.overall_process_error}")
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {analysis_result.overall_process_error}")
        
        if analysis_result.stt_error and not analysis_result.original_transcript: # If STT failed critically
            print(f"Critical STT error for file {audio_file.filename}: {analysis_result.stt_error}")
            raise HTTPException(status_code=500, detail=f"STT failed: {analysis_result.stt_error}")

        return analysis_result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error processing audio file {audio_file.filename}: {e}") # Log full error
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during audio processing: {str(e)}")
    finally:
        if audio_file: # Ensure file is closed if it was opened
            await audio_file.close()