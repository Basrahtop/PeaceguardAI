from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from backend.app.schemas.audio_analysis_schemas import AudioAnalysisResponse # Reusing this response schema
from backend.app.services import live_conversation_service 
# import soundfile as sf # soundfile was removed in a previous simplification for this endpoint
# import io # io was used with soundfile

router = APIRouter()

@router.post("/analyze-segment", response_model=AudioAnalysisResponse)
async def analyze_audio_segment_endpoint(
    audio_segment: UploadFile = File(..., description="A short audio segment (e.g., 5-10 seconds) from a live stream or microphone."),
    language_code: Optional[str] = Form("en-US", description="BCP-47 language hint for STT."),
    sample_rate: Optional[int] = Form(None, description="Sample rate of the audio segment (e.g., 16000). This is crucial.")
):
    """
    Receives a single audio segment, transcribes it, performs analysis, and checks EWS patterns.
    Designed for frequent calls from a streaming client.
    """
    if not audio_segment:
        raise HTTPException(status_code=400, detail="No audio segment provided.")
    if not sample_rate: # Make sample_rate mandatory from client for these chunks
        raise HTTPException(status_code=400, detail="Sample rate must be provided by the client for audio segment analysis.")

    try:
        audio_bytes = await audio_segment.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio segment is empty.")

        print(f"Backend: Received audio segment. Size: {len(audio_bytes)}, Client Sample Rate: {sample_rate}, Lang: {language_code}")

        # We trust the sample_rate from the client (Gradio microphone) for these chunks.
        # Assume mono audio (1 channel) from microphone for simplicity in this STT call.
        analysis_result = await live_conversation_service.analyze_audio_segment(
            audio_bytes=audio_bytes,
            language_code_stt_hint=language_code,
            sample_rate_hertz=sample_rate
            # audio_channel_count is defaulted to 1 in live_conversation_service STT config
        )
        
        # Check for critical errors from the service layer
        # If an error occurred in the service, it will be in analysis_result.overall_process_error or analysis_result.stt_error
        if analysis_result.overall_process_error or (analysis_result.stt_error and not analysis_result.original_transcript):
            error_detail = analysis_result.overall_process_error or analysis_result.stt_error
            print(f"Backend: Service layer error for segment: {error_detail}")
            # Return the AudioAnalysisResponse object containing the error details.
            # The Gradio client will interpret this.
            return analysis_result

        return analysis_result
    
    except HTTPException as e:
        # Re-raise HTTPExceptions directly if they are intentionally thrown (e.g., 400 errors)
        raise e
    except Exception as e:
        print(f"Backend: Unexpected error processing audio segment in endpoint: {e}")
        # For truly unexpected server errors, return a consistent error structure if possible,
        # or let FastAPI's default 500 handler take over.
        # Returning our defined response model with an error message is often cleaner for the client.
        return AudioAnalysisResponse(overall_process_error=f"Unexpected server error: {str(e)}")
    finally:
        # Correctly close the UploadFile object using the correct variable name
        if audio_segment and hasattr(audio_segment, 'close'): 
            await audio_segment.close()