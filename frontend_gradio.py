import gradio as gr
import requests
import json
import numpy as np
import io
import time
import os
from scipy.io.wavfile import write as write_wav # For processing audio chunks

# Load Backend URL from an environment variable for flexibility in deployment
# Fallback to localhost for local development if the env var is not set.
BACKEND_URL = os.getenv("PEACEGUARD_BACKEND_URL", "http://localhost:8000/api/v1")

# --- Helper function to format keyword results for DataFrame ---
def format_keywords_for_display(flagged_keywords_list):
    if flagged_keywords_list and isinstance(flagged_keywords_list, list):
        return [[kw.get('keyword', 'N/A') if isinstance(kw, dict) else 'Invalid_KW_Format', 
                 kw.get('count', 0) if isinstance(kw, dict) else 0] 
                for kw in flagged_keywords_list]
    return []

def format_ews_alerts_for_display(ews_alerts_list):
    if not ews_alerts_list: # Could be None or empty list
        return "No specific Early Warning System alerts triggered by this content."
    
    alerts_md_parts = ["**🔥 Early Warning System Alerts Triggered:**"]
    for alert in ews_alerts_list:
        alerts_md_parts.append(
            f"<hr style='border:1px solid #ddd'/>" 
            f"<h4>Pattern: {alert.get('pattern_name', 'N/A')} (Severity: {alert.get('severity', 'N/A')})</h4>"
            f"<strong>Description:</strong> {alert.get('description', 'N/A')}<br>"
            f"<strong>Recommendation:</strong> {alert.get('recommended_action', 'N/A')}<br>"
            f"<strong>Suggested SMS:</strong> <code style='background-color:#f0f0f0; padding: 2px 4px; border-radius:3px;'>{alert.get('generated_sms_message', 'N/A')}</code><br>"
            f"<strong>Confidence:</strong> {alert.get('confidence_score', 0.0):.2f}"
        )
    return "\n".join(alerts_md_parts)

# --- Functions to interact with the backend services ---

def analyze_text_interface(text_input: str, language_hint: str):
    if not text_input.strip():
        return "Low Risk (0.0)", "Input text is empty.", [], "No EWS alerts.", {"status": "Input text is empty."}
    
    endpoint = f"{BACKEND_URL}/misinformation/analyze-text"
    payload = {"text": text_input, "language": language_hint if language_hint.strip() else None}
    
    risk_display_label = "Error"
    explanation_text = "An error occurred."
    keywords_df_data = []
    ews_alerts_display = "EWS check not performed or no alerts."
    full_json_output = {"error": "Initialization error"}

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status() 
        data = response.json()
        full_json_output = data
        
        explanation_text = data.get("overall_explanation", "No explanation provided.")
        
        if data.get("peaceguard_risk"):
            risk_label_val = data["peaceguard_risk"].get("label", "Error")
            risk_score_val = data["peaceguard_risk"].get("score", 0.0)
            risk_display_label = f"{risk_label_val} (Score: {risk_score_val:.3f})"
        else:
            risk_display_label = "Analysis Incomplete"

        keywords_list = data.get("flagged_keywords", [])
        keywords_df_data = format_keywords_for_display(keywords_list)
        
        ews_alerts_list = data.get("ews_alerts")
        ews_alerts_display = format_ews_alerts_for_display(ews_alerts_list)
        
    except requests.exceptions.HTTPError as http_err:
        error_detail = f"HTTP error: {http_err}"
        try: error_detail = f"HTTP error: {http_err} - Response: {response.json().get('detail', response.text)}"
        except: pass
        explanation_text = error_detail
        full_json_output = {"error": error_detail, "status_code": response.status_code if 'response' in locals() else None}
    except Exception as e:
        explanation_text = f"An unexpected error occurred: {str(e)}"
        full_json_output = {"error": explanation_text}

    return risk_display_label, explanation_text, keywords_df_data, ews_alerts_display, full_json_output


def analyze_audio_interface(audio_filepath: str, language_code_stt: str):
    if audio_filepath is None:
        return "N/A", "Low Risk (0.0)", "Please upload an audio file.", [], "No EWS alerts.", {"status": "No audio file uploaded."}

    endpoint = f"{BACKEND_URL}/audio/analyze-audio"
    
    transcript_text, risk_display_label, explanation_text, keywords_df_data, ews_alerts_display, full_json_output = \
        "Error in transcription.", "Error", "Error during processing.", [], "EWS not performed.", {"error": "Init error"}
    try:
        with open(audio_filepath, 'rb') as afp: # Ensure file is properly closed
            files = {'audio_file': (os.path.basename(audio_filepath), afp, 'audio/wav')} # Suggest MIME type
            payload = {'language_code': language_code_stt if language_code_stt.strip() else "en-US"}
            
            response = requests.post(endpoint, files=files, data=payload)
            response.raise_for_status()
            data = response.json()
            full_json_output = data

            transcript_text = data.get("original_transcript", "No transcript available.")
            stt_error, overall_error = data.get("stt_error"), data.get("overall_process_error")

            if overall_error: 
                explanation_text, risk_display_label = f"Processing Error: {overall_error}", "Error processing"
            elif stt_error: 
                explanation_text, risk_display_label = f"STT Error: {stt_error}", "STT Error"
            
            text_analysis_results = data.get("text_analysis_results")
            if text_analysis_results:
                if text_analysis_results.get("peaceguard_risk"):
                    risk_data = text_analysis_results["peaceguard_risk"]
                    risk_label_val, risk_score_val = risk_data.get("label", "Error"), risk_data.get("score", 0.0)
                    risk_display_label = f"{risk_label_val} (Score: {risk_score_val:.3f})"
                
                explanation_text = text_analysis_results.get("overall_explanation", explanation_text)
                keywords_df_data = format_keywords_for_display(text_analysis_results.get("flagged_keywords", []))
                ews_alerts_display = format_ews_alerts_for_display(text_analysis_results.get("ews_alerts"))
            elif not overall_error and not stt_error:
                explanation_text, risk_display_label = "Transcription ok, text analysis missing/incomplete.", "Analysis Incomplete"
                
    except requests.exceptions.HTTPError as http_err:
        error_detail = f"HTTP error: {http_err}"
        try: error_detail = f"HTTP error: {http_err} - Response: {response.json().get('detail', response.text)}"
        except: pass
        transcript_text, explanation_text = "Error", error_detail
        full_json_output = {"error": error_detail, "status_code": response.status_code if 'response' in locals() else None}
    except FileNotFoundError:
        transcript_text, explanation_text = "Error", "Audio file not found. Please check path."
        full_json_output = {"error": explanation_text}
    except Exception as e:
        transcript_text, explanation_text = "Error", f"Unexpected error: {str(e)}"
        full_json_output = {"error": explanation_text}
    
    if not isinstance(transcript_text, str): transcript_text = str(transcript_text)

    return transcript_text, risk_display_label, explanation_text, keywords_df_data, ews_alerts_display, full_json_output

# --- Gradio interface function for REAL-TIME streaming analysis ---
def live_conversation_streaming_interface(
    microphone_stream_chunk,
    language_code_stt: str,
    full_transcript_state: str, 
    audio_buffer_state 
):
    if audio_buffer_state is None:
        audio_buffer_state = b''
    
    if microphone_stream_chunk is None: 
        final_status = "Live stream ended. Full transcript above. Analysis was periodic."
        yield full_transcript_state, gr.Markdown("Stream ended."), final_status, gr.JSON(None), full_transcript_state, audio_buffer_state
        return

    sample_rate, audio_chunk_data = microphone_stream_chunk
    audio_chunk_bytes = audio_chunk_data.astype(np.int16).tobytes()
    audio_buffer_state += audio_chunk_bytes
    
    CHUNK_DURATION_SECONDS = 5 
    BYTES_PER_CHUNK_THRESHOLD = sample_rate * 2 * 1 * CHUNK_DURATION_SECONDS
    
    if len(audio_buffer_state) < BYTES_PER_CHUNK_THRESHOLD:
        status_update = f"Recording... buffer: {len(audio_buffer_state)}/{BYTES_PER_CHUNK_THRESHOLD} bytes"
        yield full_transcript_state, gr.Markdown("Accumulating audio..."), status_update, gr.JSON(None), full_transcript_state, audio_buffer_state
        return

    print(f"Buffer full ({len(audio_buffer_state)} bytes). Sending for analysis...")
    current_chunk_to_send = audio_buffer_state
    audio_buffer_state = b'' 
    
    wav_buffer_obj = io.BytesIO()
    write_wav(wav_buffer_obj, sample_rate, np.frombuffer(current_chunk_to_send, dtype=np.int16))
    wav_buffer_obj.seek(0)
    
    endpoint = f"{BACKEND_URL}/live/analyze-segment"
    files = {'audio_segment': ('live_segment.wav', wav_buffer_obj, 'audio/wav')}
    payload = {'language_code': language_code_stt, 'sample_rate': sample_rate}
    
    latest_segment_analysis_md = "Error processing segment."
    latest_chunk_status = "Processing segment..."
    latest_chunk_json = {}

    try:
        response = requests.post(endpoint, files=files, data=payload)
        response.raise_for_status()
        data = response.json()
        latest_chunk_json = data

        new_transcript_segment = data.get("original_transcript", "")
        if new_transcript_segment:
            full_transcript_state = (full_transcript_state + " " + new_transcript_segment).strip()
        
        segment_summary_parts = [f"**Analysis of Last ~{CHUNK_DURATION_SECONDS}s Segment (Transcript: *'{new_transcript_segment}'*):**"]
        text_analysis = data.get("text_analysis_results")
        if text_analysis:
            risk = text_analysis.get("peaceguard_risk", {})
            segment_summary_parts.append(f"- **PeaceGuard Risk:** {risk.get('label', 'N/A')} (Score: {risk.get('score', 0.0):.3f})")
            if risk.get("detected_framings"):
                segment_summary_parts.append(f"  - *Detected Framings:* {', '.join(risk.get('detected_framings'))}")
            # Optionally add more details from contributing_factors for the segment if desired
            # if risk.get("contributing_factors"):
            #     segment_summary_parts.append(f"  - *Key Segment Risk Factors:* {'; '.join(risk.get('contributing_factors',[]))}")
            sentiment = text_analysis.get("gcp_sentiment", {})
            if sentiment:
                 segment_summary_parts.append(f"- **Sentiment:** {sentiment.get('sentiment_label','N/A')} (Score: {sentiment.get('sentiment_score',0.0):.2f})")
            keywords = text_analysis.get("flagged_keywords", [])
            if keywords:
                kw_strings = [f"'{k.get('keyword')}'({k.get('count')})" for k in keywords[:2]] # Show first 2
                segment_summary_parts.append(f"- **Keywords:** {', '.join(kw_strings)}{'...' if len(keywords)>2 else ''}")
            ews_alerts = text_analysis.get("ews_alerts")
            if ews_alerts:
                segment_summary_parts.append(f"- **🔥 EWS ALERTS ON SEGMENT:**")
                for alert_idx, alert in enumerate(ews_alerts[:1]): # Show first EWS alert for segment brevity
                    segment_summary_parts.append(f"  - *Pattern:* {alert.get('pattern_name')} (Severity: {alert.get('severity')})")
        else:
             segment_summary_parts.append("- *Full text analysis not available for this segment.*")
        latest_segment_analysis_md = "\n".join(segment_summary_parts)
        latest_chunk_status = f"Analyzed segment at {time.strftime('%H:%M:%S')}. Listening..."
        
    except Exception as e:
        latest_chunk_status = f"Error analyzing segment: {str(e)}"
        print(f"Error during live_conversation_streaming_interface HTTP call: {e}")
        latest_segment_analysis_md = f"Error processing segment: {str(e)}"

    return full_transcript_state, latest_segment_analysis_md, latest_chunk_status, latest_chunk_json, full_transcript_state, audio_buffer_state

# Placeholder functions
def test_sms_gradio_interface(phone_number: str, message: str):
    if not phone_number.strip() or not message.strip(): return "Phone number and message are required."
    endpoint = f"{BACKEND_URL}/ews/test-sms" 
    payload = {"phone_number": phone_number, "message": message}
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return f"SMS Test Response: {json.dumps(response.json(), indent=2)}"
    except Exception as e: return f"SMS Test Error: {str(e)}"

def specialized_stt_placeholder(audio_filepath):
    if audio_filepath is None: return "Please upload an audio file."
    filename = os.path.basename(audio_filepath.name) if hasattr(audio_filepath, 'name') and audio_filepath.name else 'uploaded file'
    return f"Service for 'Specialized STT' (for file: '{filename}') is under development."

def contextual_verification_placeholder(claim_or_url: str):
    if not claim_or_url.strip(): return "Please enter a claim or URL."
    return f"Service for 'Contextual Verification Support' (for input: '{claim_or_url[:50]}...') is under development."

# --- Build the Gradio UI with Tabs ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange"), title="PeaceGuard AI") as peaceguard_ai_ui:
    gr.Markdown("# 🕊️ PeaceGuard AI: Information Integrity Framework")
    gr.Markdown("AI-powered tools to analyze content, detect risks, and promote peace. Ensure your FastAPI backend is running.")

    with gr.Tabs():
        with gr.TabItem("💬 Text Analysis"):
            gr.Markdown("## Analyze Text for Misinformation & Risk Indicators")
            with gr.Row():
                with gr.Column(scale=3):
                    text_input_service1 = gr.Textbox(lines=10, placeholder="Paste text here to analyze...", label="Text Input")
                    lang_hint_service1 = gr.Textbox(label="Language Hint (e.g., en, ha, yo, ig)", placeholder="Optional, e.g., 'en' for English")
                    analyze_text_button = gr.Button("Analyze Text", variant="primary") # Icon removed
                with gr.Column(scale=2):
                    risk_label_output_service1 = gr.Label(label="PeaceGuard AI Risk Assessment")
                    explanation_output_service1 = gr.Textbox(label="Detailed Explanation", lines=7, interactive=False)
                    keywords_output_service1 = gr.DataFrame(
                        label="Flagged Keywords", 
                        headers=["Keyword", "Count"], 
                        datatype=["str", "number"],
                        col_count=(2,"fixed")
                    )
                    ews_alerts_output_service1 = gr.Markdown(label="Early Warning Alerts (if any)")
            with gr.Accordion("Full JSON Response (Backend Output)", open=False):
                json_output_service1 = gr.JSON(label="Backend JSON Response")
            
            analyze_text_button.click(
                fn=analyze_text_interface,
                inputs=[text_input_service1, lang_hint_service1],
                outputs=[risk_label_output_service1, explanation_output_service1, keywords_output_service1, ews_alerts_output_service1, json_output_service1]
            )

        with gr.TabItem("🎙️ Audio File Analysis"):
            gr.Markdown("## Transcribe Audio File & Analyze for Misinformation Indicators")
            with gr.Row():
                with gr.Column(scale=3):
                    audio_input_service2 = gr.Audio(sources=["upload"], type="filepath", label="Upload Audio File (WAV, MP3 recommended)")
                    lang_code_stt_service2 = gr.Textbox(label="Language Code for STT (e.g., en-US, ha-NG)", value="en-US")
                    analyze_audio_button = gr.Button("Analyze Audio File", variant="primary") # Icon removed
                with gr.Column(scale=2):
                    transcript_output_service2 = gr.Textbox(label="Transcript", lines=3, interactive=False)
                    risk_label_output_service2 = gr.Label(label="PeaceGuard AI Risk (on transcript)")
                    explanation_output_service2 = gr.Textbox(label="Detailed Explanation (on transcript)", lines=5, interactive=False)
                    keywords_output_service2 = gr.DataFrame(
                        label="Flagged Keywords (on transcript)", 
                        headers=["Keyword", "Count"],
                        datatype=["str", "number"],
                        col_count=(2,"fixed")
                    )
                    ews_alerts_output_service2 = gr.Markdown(label="Early Warning Alerts (if any)")
            with gr.Accordion("Full JSON Response (Backend Output)", open=False):
                json_output_service2 = gr.JSON(label="Backend JSON Response")
            analyze_audio_button.click(
                fn=analyze_audio_interface,
                inputs=[audio_input_service2, lang_code_stt_service2],
                outputs=[transcript_output_service2, risk_label_output_service2, explanation_output_service2, keywords_output_service2, ews_alerts_output_service2, json_output_service2]
            )
        
        with gr.TabItem("🔴 Live Conversation Analysis"): # REINSTATED THIS TAB
            gr.Markdown("## Analyze Spoken Conversations Periodically (Near Real-Time)")
            gr.Markdown(
                "Click 'Record from microphone', speak. Analysis updates for ~5s segments. Click 'Stop recording' when done.\n"
                "**Note:** Browser will request microphone permission. Ensure backend is running."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    live_mic_input = gr.Microphone(
                        label="Live Microphone Feed", 
                        type="numpy", 
                        streaming=True,
                    )
                    live_lang_code_stt_stream = gr.Textbox(label="Language Code for STT", value="en-US")
                with gr.Column(scale=2):
                    live_full_transcript_output = gr.Textbox(label="Full Conversation Transcript", lines=6, interactive=False)
                    live_latest_segment_analysis_output = gr.Markdown(label="Latest Segment Analysis")
                    live_status_output = gr.Textbox(label="Live Status", interactive=False)

            with gr.Accordion("Full JSON Response (Latest Segment)", open=False):
                live_json_output_stream = gr.JSON()

            full_transcript_state = gr.State("") 
            audio_buffer_state = gr.State(None)

            live_mic_input.stream(
                fn=live_conversation_streaming_interface,
                inputs=[live_mic_input, live_lang_code_stt_stream, full_transcript_state, audio_buffer_state],
                outputs=[live_full_transcript_output, live_latest_segment_analysis_output, live_status_output, live_json_output_stream, full_transcript_state, audio_buffer_state]
            )
            live_mic_input.clear( # Reset states and relevant outputs when microphone interaction stops/clears
                lambda: ("", None, "Stream cleared. Ready for new recording.", "", gr.JSON(None)), 
                outputs=[full_transcript_state, audio_buffer_state, live_status_output, live_latest_segment_analysis_output, live_json_output_stream]
            )

        with gr.TabItem("⚠️ EWS Utilities"): 
            gr.Markdown("## Early Warning System Utilities")
            gr.Markdown(
                "EWS is auto-triggered by Text/Audio/Live analysis if risk is high. Alerts are shown in those tabs. This section is for auxiliary EWS utilities like testing mock SMS."
            )
            gr.Markdown("---")
            gr.Markdown("### Test Mock SMS Alert Dissemination")
            with gr.Row():
                with gr.Column(scale=1):
                    test_sms_phone_ews_tab = gr.Textbox(label="Recipient Phone Number", placeholder="+234XXXXXXXXXX")
                with gr.Column(scale=2):
                    test_sms_message_ews_tab = gr.Textbox(label="Custom SMS Message Content", placeholder="Enter test alert message")
            test_sms_button_ews_tab = gr.Button("Send Test SMS (Mock)") # Icon removed
            test_sms_output_ews_tab = gr.Textbox(label="SMS Send Status", interactive=False)
            test_sms_button_ews_tab.click(
                fn=test_sms_gradio_interface,
                inputs=[test_sms_phone_ews_tab, test_sms_message_ews_tab],
                outputs=test_sms_output_ews_tab
            )
            gr.Markdown("*Note: SMS sending is currently mocked and will print to the backend console via the `/ews/test-sms` endpoint.*")

        with gr.TabItem("🗣️ Specialized STT (Dev)"):
            gr.Markdown("## Transcribe Challenging Audio with Enhanced STT (Under Development)")
            with gr.Row():
                with gr.Column():
                    audio_input_service4 = gr.Audio(sources=["upload"], type="filepath", label="Upload Challenging Audio File")
                    transcribe_special_button = gr.Button("Transcribe (Specialized)", variant="secondary", interactive=False)
                with gr.Column():
                    special_stt_output_service4 = gr.Textbox(label="Specialized Transcription", lines=10, interactive=False, value="This service is under development.")

        with gr.TabItem("🔗 Contextual Verification (Dev)"):
            gr.Markdown("## Get Contextual Insights for Claims/URLs (Under Development)")
            with gr.Row():
                with gr.Column():
                    claim_input_service5 = gr.Textbox(label="Enter Claim, Statement, or URL", placeholder="e.g., 'A new cure for malaria has been suppressed...' or a news article URL", lines=5)
                    get_context_button = gr.Button("Get Contextual Report", variant="secondary", interactive=False)
                with gr.Column():
                    context_output_service5 = gr.Textbox(label="Contextual Verification Report", lines=10, interactive=False, value="This service is under development.")

if __name__ == "__main__":
    print("Launching PeaceGuard AI Gradio UI...")
    print(f"Attempting to connect to Backend at: {BACKEND_URL}")
    server_port = int(os.getenv("PORT", 7860)) # For Render deployment
    print(f"Gradio will attempt to listen on 0.0.0.0:{server_port}")
    # Set share=False for deployment, True for temporary public link during local dev if needed.
    peaceguard_ai_ui.launch(server_name="0.0.0.0", server_port=server_port, share=False)