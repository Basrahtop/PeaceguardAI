from typing import List, Dict, Any, Optional
from backend.app.schemas.ews_schemas import EWSAlert, EWSInput
from backend.app.schemas.text_analysis_schemas import PeaceGuardRiskOutput # For type hinting
from backend.app.core.notification_client import notification_client # Import the instance

# --- Define Historical Conflict Precursor Patterns ---
# These patterns would ideally be more complex and potentially loaded from a config/database
# For MVP, we define them here. Each pattern needs:
# - id: A unique identifier
# - name: Human-readable name
# - conditions_to_check: A function that takes EWSInput and returns True if pattern matches
# - severity: e.g., "Medium", "High", "Critical"
# - description_template: A template for the alert description
# - recommended_action_template: Template for actions
# - sms_template: Template for the SMS message

# Helper to check for keywords (case-insensitive)
def check_keywords_in_text(text_lower: str, keywords: List[str]) -> List[str]:
    found = []
    for kw in keywords:
        if kw.lower() in text_lower:
            found.append(kw)
    return found

# --- PATTERN DEFINITIONS ---
# These would be more sophisticated, possibly involving combinations of framings, categories, sentiment thresholds, etc.

EWS_PATTERNS = [
    {
        "id": "EWS_PAT_001",
        "name": "Targeted Group Incitement Pattern",
        "severity": "Critical",
        "description_template": "Detected a pattern of high-risk rhetoric, including divisive 'Us vs. Them' framing and strong negative sentiment, potentially targeting groups. This aligns with historical precursors to inter-group tension.",
        "recommended_action_template": "Monitor related online/offline conversations closely. Engage community leaders for de-escalation. Prepare counter-narratives focused on unity and verified facts.",
        "target_audience_suggestion": "CSOs, Peace Committees, Security Agencies, Community Leaders",
        "sms_template": "EWS Critical: Divisive rhetoric pattern detected targeting groups. Potential incitement. Monitor closely. #PeaceGuardAI",
        "conditions_to_check": lambda data: (
            data.peaceguard_risk.score >= 0.7 and # High or Critical PeaceGuard score
            "Us vs. Them Divisive Framing" in data.peaceguard_risk.detected_framings and
            data.gcp_sentiment is not None and data.gcp_sentiment.sentiment_score < -0.6 # Strongly negative
        ),
        "confidence_logic": lambda data: data.peaceguard_risk.score * 0.8 # Example confidence
    },
    {
        "id": "EWS_PAT_002",
        "name": "Election Integrity Destabilization Pattern",
        "severity": "High",
        "description_template": "Observing narratives attacking election integrity using alarmist framing and specific keywords related to electoral malpractice. This historically correlates with attempts to delegitimize elections and incite pre/post-election unrest.",
        "recommended_action_template": "Amplify verified information from electoral bodies. Promote civic education on identifying election misinformation. Alert election monitors.",
        "target_audience_suggestion": "Electoral Bodies, CSOs, Media, Fact-Checkers",
        "sms_template": "EWS High: Election integrity narratives with alarmist framing detected. Potential for unrest. Promote verified info. #PeaceGuardAI",
        "conditions_to_check": lambda data: (
            (
                len(check_keywords_in_text(data.original_text.lower(), ["rigged election", "stolen mandate", "election violence", "inec corrupt", "no election"])) > 0 or
                len(check_keywords_in_text(data.original_text.lower(), ["stolen mandate 2027"])) > 0 # Example contextual
            ) and
            "Alarmist Claim Framing" in data.peaceguard_risk.detected_framings and
            data.gcp_sentiment is not None and data.gcp_sentiment.sentiment_score < -0.5
        ),
        "confidence_logic": lambda data: (data.peaceguard_risk.score * 0.5 + 0.2 if "Alarmist Claim Framing" in data.peaceguard_risk.detected_framings else 0.0)
    },
    {
        "id": "EWS_PAT_003",
        "name": "Escalating Unrest Rumor Pattern",
        "severity": "High",
        "description_template": "Detection of widespread rumors and alarmist claims suggesting imminent large-scale unrest or breakdown of order, combined with a high general risk score. This pattern has been observed prior to significant public disturbances.",
        "recommended_action_template": "Urgently verify circulating rumors. Disseminate factual information through trusted channels. Prepare contingency plans with local authorities.",
        "target_audience_suggestion": "Security Agencies, Local Government, Community Leaders, Media",
        "sms_template": "EWS High: Rumors of escalating unrest with alarmist framing. Verify all info. Potential for disturbances. #PeaceGuardAI",
        "conditions_to_check": lambda data: (
            len(check_keywords_in_text(data.original_text.lower(), ["uprising", "riot imminent", "total shutdown", "youth restiveness propaganda", "nationwide strike"])) > 0 and
            "Alarmist Claim Framing" in data.peaceguard_risk.detected_framings and
            data.peaceguard_risk.score >= 0.6 # High PeaceGuard score
        ),
        "confidence_logic": lambda data: data.peaceguard_risk.score * 0.7
    },
    # Add more patterns here based on research (e.g., related to specific Nigerian conflicts, Gaddafi, DRC examples)
]

def evaluate_content_for_ews(ews_input: EWSInput) -> List[EWSAlert]:
    """
    Evaluates a given EWSInput (derived from TextAnalysisResponse) against predefined EWS patterns.
    """
    triggered_alerts: List[EWSAlert] = []
    text_lower = ews_input.original_text.lower() # For keyword checks within patterns

    print(f"EWS Input PeaceGuard Risk Score: {ews_input.peaceguard_risk.score}, Label: {ews_input.peaceguard_risk.label}")
    print(f"EWS Input Detected Framings: {ews_input.peaceguard_risk.detected_framings}")
    print(f"EWS Input Sentiment Score: {ews_input.gcp_sentiment.sentiment_score if ews_input.gcp_sentiment else 'N/A'}")


    for pattern in EWS_PATTERNS:
        try:
            # Pass the full ews_input to the condition checker
            if pattern["conditions_to_check"](ews_input):
                # Extract implicated keywords and framings for this specific alert
                implicated_kws = []
                if "keywords" in pattern: # If pattern definition has specific keywords
                    implicated_kws = check_keywords_in_text(text_lower, pattern["keywords"])
                else: # Fallback to general flagged keywords if pattern doesn't specify its own
                    implicated_kws = [kw.keyword for kw in ews_input.flagged_keywords]

                implicated_fr = ews_input.peaceguard_risk.detected_framings # All framings detected by text_analyzer

                # Generate SMS message (can be more dynamic based on pattern details)
                # For now, using the template. Could replace placeholders like [Area] if data available.
                sms_message = pattern["sms_template"]

                alert = EWSAlert(
                    alert_id=pattern["id"],
                    pattern_name=pattern["name"],
                    severity=pattern["severity"],
                    description=pattern["description_template"], # Could format this with specific findings
                    recommended_action=pattern["recommended_action_template"],
                    implicated_keywords=list(set(implicated_kws))[:5], # Show some unique keywords
                    implicated_framings=list(set(implicated_fr)),
                    target_audience_suggestion=pattern.get("target_audience_suggestion"),
                    confidence_score=round(min(pattern["confidence_logic"](ews_input), 1.0), 3) if "confidence_logic" in pattern else 0.75, # Example default
                    generated_sms_message=sms_message
                )
                triggered_alerts.append(alert)
        except Exception as e:
            print(f"Error checking EWS pattern {pattern['id']}: {e}")
            # Optionally add a system error alert or log this more formally
            
    return triggered_alerts

# Example of how to use the notification client (can be called from an endpoint)
def disseminate_ews_alert_sms(alert: EWSAlert, phone_numbers: List[str]):
    if not alert.generated_sms_message:
        print(f"No SMS message generated for alert {alert.alert_id}. Skipping dissemination.")
        return {"status": "skipped", "reason": "No SMS message in alert."}
        
    print(f"Attempting to disseminate EWS Alert '{alert.pattern_name}' via SMS.")
    # In a real app, phone_numbers would come from a subscriber list or be determined by alert context
    if not phone_numbers:
        print("No phone numbers provided for SMS dissemination.")
        return {"status": "skipped", "reason": "No phone numbers provided."}
        
    return notification_client.send_bulk_sms_alerts(phone_numbers, alert.generated_sms_message)