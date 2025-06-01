from google.cloud import speech
from typing import Optional, List
import time # Kept if any timing/polling logic remains, but not essential for current sync version
import os # For os.getenv
import json # For parsing JSON string
from google.oauth2 import service_account # Added for loading creds from env var

# --- Modified Google Cloud Client Initialization ---
gcp_sa_key_content_stt = os.getenv("GCP_SA_KEY_JSON_CONTENT")
gcp_credentials_stt = None

if gcp_sa_key_content_stt:
    try:
        credentials_info_stt = json.loads(gcp_sa_key_content_stt)
        gcp_credentials_stt = service_account.Credentials.from_service_account_info(credentials_info_stt)
        print("INFO:     STT Client: Loaded GCP credentials from GCP_SA_KEY_JSON_CONTENT env var.")
    except Exception as e:
        print(f"ERROR:    STT Client: Failed to load GCP credentials from ENV content: {e}. Falling back to default.")

try:
    speech_client = speech.SpeechClient(credentials=gcp_credentials_stt) if gcp_credentials_stt else speech.SpeechClient()
    if not gcp_credentials_stt and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("WARNING:  STT Client: Neither GCP_SA_KEY_JSON_CONTENT nor GOOGLE_APPLICATION_CREDENTIALS seem to be set for default client init.")
    print("INFO:     STT Client: Google Cloud Speech client initialized.")
except Exception as e:
    print(f"ERROR:    STT Client: Failed to initialize Google Cloud Speech client: {e}.")
    speech_client = None
# --- End of Modified Initialization ---


def transcribe_audio_gcp_long_running(
    audio_content: bytes, 
    language_code: str = "en-US", 
    sample_rate_hertz: Optional[int] = None,
    audio_channel_count: int = 1,
    operation_timeout_seconds: int = 360
) -> dict:
    if not speech_client:
        print("ERROR:    STT Client: Speech client not initialized for long_running.")
        return {"transcript": None, "confidence": 0.0, "error": "Speech client not initialized."}
    if not audio_content:
        return {"transcript": None, "confidence": 0.0, "error": "Audio content is empty."}

    audio = speech.RecognitionAudio(content=audio_content)
    config_params = {
        "language_code": language_code,
        "enable_automatic_punctuation": True,
        "audio_channel_count": audio_channel_count,
    }
    if sample_rate_hertz: config_params["sample_rate_hertz"] = sample_rate_hertz
    else: print("WARNING:  STT Client: sample_rate_hertz not provided for long_running STT.")
    config = speech.RecognitionConfig(**config_params)

    try:
        print(f"INFO:     STT Client: Sending audio to GCP STT (long_running) with config: {config_params}")
        operation = speech_client.long_running_recognize(config=config, audio=audio)
        print(f"INFO:     STT Client: Waiting for STT operation (up to {operation_timeout_seconds}s): {operation.operation.name}")
        response = operation.result(timeout=operation_timeout_seconds)
        print("INFO:     STT Client: Long-running STT Operation completed.")

        all_transcripts: List[str] = []
        total_confidence = 0.0
        num_segments_for_confidence = 0
        stt_detected_lang = language_code # Default

        if response.results:
            for result_idx, result in enumerate(response.results):
                if result.alternatives:
                    alternative = result.alternatives[0]
                    all_transcripts.append(alternative.transcript)
                    if alternative.confidence > 0:
                        total_confidence += alternative.confidence
                        num_segments_for_confidence += 1
                    # Check for language code in results (can be in beta features or specific models)
                    if hasattr(result, 'language_code') and result.language_code and result_idx == 0: # Take from first result
                        stt_detected_lang = result.language_code
            
            final_transcript = " ".join(all_transcripts).strip()
            average_confidence = (total_confidence / num_segments_for_confidence) if num_segments_for_confidence > 0 else 0.0
            return {"transcript": final_transcript if final_transcript else None, "confidence": round(average_confidence, 4), "error": None, "detected_language_code": stt_detected_lang}
        else:
            return {"transcript": None, "confidence": 0.0, "error": "No transcription results in long-running operation.", "detected_language_code": language_code}
    except TimeoutError:
        print(f"ERROR:    STT Client: STT (long_running) timed out after {operation_timeout_seconds} seconds.")
        return {"transcript": None, "confidence": 0.0, "error": f"Transcription timed out after {operation_timeout_seconds}s."}
    except Exception as e:
        print(f"ERROR:    STT Client: STT (long_running) error: {e}")
        return {"transcript": None, "confidence": 0.0, "error": str(e)}

def transcribe_audio_gcp_sync(audio_content: bytes, language_code: str = "en-US", sample_rate_hertz: Optional[int] = None) -> dict:
    if not speech_client:
        print("ERROR:    STT Client: Speech client not initialized for sync.")
        return {"transcript": None, "confidence": 0.0, "error": "Speech client not initialized."}
    if not audio_content:
        return {"transcript": None, "confidence": 0.0, "error": "Audio content is empty."}

    audio = speech.RecognitionAudio(content=audio_content)
    config_params = { "language_code": language_code, "enable_automatic_punctuation": True }
    if sample_rate_hertz: config_params["sample_rate_hertz"] = sample_rate_hertz
    else: print("WARNING:  STT Client: sample_rate_hertz not provided for sync STT.")
    config = speech.RecognitionConfig(**config_params)

    try:
        print(f"INFO:     STT Client: Sending audio to GCP STT (sync) with config: {config_params}")
        response = speech_client.recognize(config=config, audio=audio)
        result_language_code = language_code 
        if response.results and response.results[0].alternatives:
            alt = response.results[0].alternatives[0]
            # For RecognizeResponse, language_code is not typically on results[0] but on RecognizeResponse if auto-detected
            # For simplicity, if language_code was passed, we assume it's that.
            # If auto-detection was forced by not passing language_code to config, then check response.results[0].language_code (if available)
            # For now, we'll assume `result_language_code` remains the input `language_code`
            # as the main `recognize` response object doesn't have a top-level one easily.
            if hasattr(response, 'results') and len(response.results) > 0 and hasattr(response.results[0], 'language_code') and response.results[0].language_code:
                 result_language_code = response.results[0].language_code # More robust if available

            return {"transcript": alt.transcript, "confidence": round(alt.confidence, 4) if alt.confidence else 0.0, "detected_language_code": result_language_code, "error": None}
        else:
            return {"transcript": None, "confidence": 0.0, "error": "No transcription result (sync).", "detected_language_code": language_code}
    except Exception as e:
        print(f"ERROR:    STT Client: STT (sync) error: {e}")
        return {"transcript": None, "confidence": 0.0, "error": str(e)}