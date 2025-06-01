from backend.app.core import stt_client
from backend.app.services.text_misinfo_analyzer import analyze_text_content as analyze_text_for_misinfo
from backend.app.schemas.text_analysis_schemas import TextAnalysisRequest
from backend.app.schemas.audio_analysis_schemas import AudioAnalysisResponse, EmbeddedTextAnalysisResult
from typing import Optional

async def analyze_audio_segment(
    audio_bytes: bytes, 
    language_code_stt_hint: str = "en-US",
    sample_rate_hertz: Optional[int] = None
) -> AudioAnalysisResponse:
    """
    Analyzes a short audio segment (e.g., 5-10 seconds) by transcribing it, 
    performing misinformation analysis, and auto-triggering EWS.
    Uses synchronous STT for low latency on short chunks.
    """
    if not audio_bytes:
        return AudioAnalysisResponse(overall_process_error="No audio content provided for segment analysis.")

    # Using synchronous STT is more efficient for short, frequent chunks
    stt_result = stt_client.transcribe_audio_gcp_sync(
        audio_content=audio_bytes, 
        language_code=language_code_stt_hint,
        sample_rate_hertz=sample_rate_hertz
    )

    transcript = stt_result.get("transcript")
    stt_confidence = stt_result.get("confidence")
    stt_error_message = stt_result.get("error")
    stt_detected_lang = stt_result.get("detected_language_code", language_code_stt_hint)

    if stt_error_message or not transcript:
        return AudioAnalysisResponse(
            original_transcript=transcript,
            stt_confidence=stt_confidence,
            stt_error=f"STT Error: {stt_error_message or 'No transcript returned for segment.'}",
            stt_detected_language_code=stt_detected_lang,
            overall_process_error="Failed to obtain a usable transcript from STT for the audio segment."
        )
    
    # Determine language hint for text analysis
    lang_hint_for_text_analysis = stt_detected_lang if stt_detected_lang and "error" not in stt_detected_lang else None
    if not lang_hint_for_text_analysis and "error" not in language_code_stt_hint:
        lang_hint_for_text_analysis = language_code_stt_hint

    text_analysis_request = TextAnalysisRequest(
        text=transcript, 
        language=lang_hint_for_text_analysis
    )
    
    # This call includes the auto-EWS trigger
    text_analysis_output_obj = analyze_text_for_misinfo(text_analysis_request)

    embedded_text_results = EmbeddedTextAnalysisResult(
        text_detected_language=text_analysis_output_obj.detected_language_by_translate_api,
        gcp_sentiment=text_analysis_output_obj.gcp_sentiment,
        gcp_risk_assessment=text_analysis_output_obj.gcp_risk_assessment,
        keyword_analysis_score=text_analysis_output_obj.keyword_analysis_score,
        flagged_keywords=text_analysis_output_obj.flagged_keywords,
        peaceguard_risk=text_analysis_output_obj.peaceguard_risk,
        ews_alerts=text_analysis_output_obj.ews_alerts,
        overall_explanation=text_analysis_output_obj.overall_explanation
    )
    
    return AudioAnalysisResponse(
        original_transcript=transcript,
        stt_confidence=stt_confidence,
        stt_detected_language_code=stt_detected_lang,
        text_analysis_results=embedded_text_results
    )