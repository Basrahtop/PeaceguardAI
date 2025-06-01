from fastapi import APIRouter, HTTPException, Body
from typing import List
from backend.app.schemas.ews_schemas import EWSInput, EWSCheckResponse, EWSAlert
from backend.app.schemas.text_analysis_schemas import TextAnalysisResponse # To potentially receive this as input
from backend.app.services import early_warning_service

router = APIRouter()

@router.post("/check-content", response_model=EWSCheckResponse)
async def check_content_for_ews_alerts(
    # Instead of full TextAnalysisResponse, use EWSInput for cleaner contract
    ews_input_data: EWSInput = Body(...)
):
    """
    Receives detailed analysis results of a piece of content (text/transcript)
    and evaluates it against predefined Early Warning System patterns.
    """
    if not ews_input_data.original_text:
        raise HTTPException(status_code=400, detail="Original text/transcript is required in input.")
    if not ews_input_data.peaceguard_risk: # PeaceGuardRiskOutput is crucial
        raise HTTPException(status_code=400, detail="PeaceGuard risk assessment data is required in input.")

    try:
        print(f"Received EWS check request for text: {ews_input_data.original_text[:100]}...")
        triggered_alerts = early_warning_service.evaluate_content_for_ews(ews_input_data)
        
        status_msg = "EWS evaluation complete."
        if triggered_alerts:
            status_msg += f" {len(triggered_alerts)} potential EWS alert(s) triggered."
            # Example: If a critical alert is found, immediately try to send a mock SMS
            # This is just for demonstration; real dissemination logic would be more complex.
            # for alert in triggered_alerts:
            #     if alert.severity == "Critical":
            #         early_warning_service.disseminate_ews_alert_sms(alert, ["+1234567890"]) # Mock phone number
        else:
            status_msg += " No specific EWS patterns matched with high confidence."
            
        return EWSCheckResponse(
            input_text_snippet=ews_input_data.original_text[:200] + "...",
            triggered_alerts=triggered_alerts,
            status_message=status_msg
        )
    except Exception as e:
        print(f"Error in EWS endpoint: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"An error occurred during EWS evaluation: {str(e)}")

# Example endpoint to test SMS sending (mocked)
@router.post("/test-sms", summary="Test Mock SMS Sending")
async def test_sms_sending(phone_number: str = Body(..., embed=True), message: str = Body(..., embed=True)):
    if not phone_number or not message:
        raise HTTPException(status_code=400, detail="Phone number and message are required.")
    result = early_warning_service.notification_client.send_sms_alert(phone_number, message)
    return result