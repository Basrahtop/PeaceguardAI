from backend.app.schemas.text_analysis_schemas import (
    TextAnalysisRequest, 
    TextAnalysisResponse, 
    KeywordMatch,
    GCPSentimentOutput,
    GCPCategoryMatch,
    GCPRiskAssessmentOutput,
    PeaceGuardRiskOutput
)
from backend.app.schemas.ews_schemas import EWSInput, EWSAlert # NEW: Import EWS schemas
from backend.app.core import nlp_utils
from backend.app.services import early_warning_service # NEW: Import EWS service
from typing import List, Tuple, Optional

# --- PeaceGuard AI Risk Scoring Parameters (Tuning Section) ---
DANGEROUS_KEYWORD_MULTIPLIER = 0.3
SENSITIVE_KEYWORD_MULTIPLIER = 0.1
CATEGORY_RISK_WEIGHTS = {
    "/Sensitive Subjects/War & Conflict": 0.4,
    "/Sensitive Subjects/Terrorism": 0.6,
    "Hate Speech": 0.7,
    "Violent Crime": 0.5,
    "/Sensitive Subjects/Firearms & Weapons": 0.3,
    "/Adult": 0.1, 
    "Cyberbullying": 0.7,
    "/Finance/Scams & Frauds": 0.5,
}
CATEGORY_CONFIDENCE_THRESHOLD = 0.3
STRONG_NEGATIVE_SENTIMENT_THRESHOLD = -0.5
VERY_STRONG_NEGATIVE_SENTIMENT_THRESHOLD = -0.75
VERY_STRONG_NEGATIVE_MAGNITUDE_THRESHOLD = 0.7
BASE_SENTIMENT_RISK_ADDITION = 0.15
SENTIMENT_AMPLIFICATION_BOOST = 0.2
SENTIMENT_AMPLIFICATION_MIN_RISK_THRESHOLD = 0.05
RISK_LABEL_MEDIUM_THRESHOLD = 0.3
RISK_LABEL_HIGH_THRESHOLD = 0.6
RISK_LABEL_CRITICAL_THRESHOLD = 0.85

CONTEXTUAL_CONCERN_KEYWORDS_LIST = [
    "foreign invaders", "land grabbers", "secret cabal", "deep state nigeria", 
    "stolen mandate", "ungoverned terror spaces", "youth uprising imminent",
] # Ensure lowercase
CONTEXTUAL_CONCERN_KEYWORD_MULTIPLIER = 0.4

US_VS_THEM_PATTERNS = [
    "they are all", "those people are", "real patriots vs them", 
    "the true [x] against the corrupt [y]", "us vs them", "we the people versus", 
    "enemies of the state", "traitors among us", "our people vs their kind"
] # Ensure lowercase
ALARMIST_CLAIM_PATTERNS = [
    "urgent warning", "everyone must know this", "secret plot exposed", 
    "they are hiding the truth from you", "imminent total danger", 
    "complete collapse is coming", "government is lying about the [x]", "share before they delete this"
] # Ensure lowercase
FRAMING_TYPE_US_VS_THEM = "Us vs. Them Divisive Framing"
FRAMING_TYPE_ALARMIST = "Alarmist Claim Framing"
FRAMING_PATTERN_MULTIPLIER = 0.25

# NEW: Threshold for auto-triggering EWS check
EWS_AUTO_TRIGGER_RISK_SCORE_THRESHOLD = RISK_LABEL_MEDIUM_THRESHOLD # e.g., 0.3
# --- End of Tuning Section ---

DANGEROUS_KEYWORDS = ["kill", "attack", "bomb", "riot", "false flag", "massacre", "genocide", "execute", "executed", "assassinate"]
SENSITIVE_KEYWORDS = [
    "protest", "election", "government", "crisis", "rumor", "unrest", "corruption", 
    "exploit", "exploitation", "extort", "slavery", "colonialism", 
    "foreign interference", "uprising", "masters"
]

def calculate_peaceguard_risk(
    text_lower: str, 
    gcp_sentiment: Optional[GCPSentimentOutput],
    gcp_risk_assessment: Optional[GCPRiskAssessmentOutput],
    flagged_keywords: List[KeywordMatch] 
) -> PeaceGuardRiskOutput:
    current_risk_score = 0.0
    contributing_factors: List[str] = []
    detected_framings_list: List[str] = []
    
    found_dangerous_keywords_actual: List[str] = []
    found_sensitive_keywords_actual: List[str] = []

    # 1. GCP Content Categories
    if gcp_risk_assessment and gcp_risk_assessment.risk_categories:
        for cat_match in gcp_risk_assessment.risk_categories:
            if cat_match.confidence >= CATEGORY_CONFIDENCE_THRESHOLD:
                for defined_risky_cat_keyword, weight in CATEGORY_RISK_WEIGHTS.items():
                    if defined_risky_cat_keyword.lower() in cat_match.category.lower():
                        score_add = weight * cat_match.confidence
                        current_risk_score += score_add
                        contributing_factors.append(
                            f"Content classified by GCP as potentially related to '{cat_match.category}' (confidence: {cat_match.confidence*100:.1f}%)."
                        )
                        break 
    
    # 2. Standard Keywords
    raw_keyword_score_contribution = 0.0
    dangerous_hits_count = 0
    sensitive_hits_count = 0
    if flagged_keywords:
        for kw_match in flagged_keywords:
            if kw_match.keyword in DANGEROUS_KEYWORDS:
                raw_keyword_score_contribution += DANGEROUS_KEYWORD_MULTIPLIER * kw_match.count
                if kw_match.keyword not in found_dangerous_keywords_actual: found_dangerous_keywords_actual.append(kw_match.keyword)
                dangerous_hits_count += kw_match.count
            elif kw_match.keyword in SENSITIVE_KEYWORDS:
                raw_keyword_score_contribution += SENSITIVE_KEYWORD_MULTIPLIER * kw_match.count
                if kw_match.keyword not in found_sensitive_keywords_actual: found_sensitive_keywords_actual.append(kw_match.keyword)
                sensitive_hits_count += kw_match.count
        current_risk_score += raw_keyword_score_contribution

        if found_dangerous_keywords_actual:
            contributing_factors.append(f"Presence of {dangerous_hits_count} high-risk keyword instance(s) like: '{', '.join(sorted(found_dangerous_keywords_actual)[:2])}{'...' if len(found_dangerous_keywords_actual)>2 else ''}'.")
        elif found_sensitive_keywords_actual:
            contributing_factors.append(f"Presence of {sensitive_hits_count} sensitive keyword instance(s) like: '{', '.join(sorted(found_sensitive_keywords_actual)[:2])}{'...' if len(found_sensitive_keywords_actual)>2 else ''}'.")

    # 3. Contextual Concern Keywords
    found_contextual_concerns_actual = []
    contextual_concern_score_contribution = 0.0
    for concern_keyword in CONTEXTUAL_CONCERN_KEYWORDS_LIST:
        if concern_keyword in text_lower: # Assumes concern_keywords are lowercase
            occurrences = text_lower.count(concern_keyword)
            contextual_concern_score_contribution += (CONTEXTUAL_CONCERN_KEYWORD_MULTIPLIER * occurrences)
            if concern_keyword not in found_contextual_concerns_actual:
                 found_contextual_concerns_actual.append(concern_keyword)
    if found_contextual_concerns_actual:
        current_risk_score += contextual_concern_score_contribution
        contributing_factors.append(
            f"Detected highly sensitive contextual terms: '{', '.join(sorted(found_contextual_concerns_actual))}'.")

    # 4. Manipulative Framing Detection
    us_vs_them_detected = False
    for pattern in US_VS_THEM_PATTERNS: # Assumes patterns are lowercase
        if pattern in text_lower:
            us_vs_them_detected = True
            break
    if us_vs_them_detected:
        current_risk_score += FRAMING_PATTERN_MULTIPLIER
        if FRAMING_TYPE_US_VS_THEM not in detected_framings_list:
             detected_framings_list.append(FRAMING_TYPE_US_VS_THEM)
        contributing_factors.append(f"Detected '{FRAMING_TYPE_US_VS_THEM}'.")

    alarmist_claim_detected = False
    for pattern in ALARMIST_CLAIM_PATTERNS: # Assumes patterns are lowercase
        if pattern in text_lower:
            alarmist_claim_detected = True
            break
    if alarmist_claim_detected:
        current_risk_score += FRAMING_PATTERN_MULTIPLIER
        if FRAMING_TYPE_ALARMIST not in detected_framings_list:
            detected_framings_list.append(FRAMING_TYPE_ALARMIST)
        contributing_factors.append(f"Detected '{FRAMING_TYPE_ALARMIST}'.")
    
    # 5. Sentiment Contribution
    if gcp_sentiment and gcp_sentiment.sentiment_score is not None:
        sentiment_desc = f"score: {gcp_sentiment.sentiment_score:.2f}, magnitude: {gcp_sentiment.magnitude:.2f}"
        if gcp_sentiment.sentiment_score < VERY_STRONG_NEGATIVE_SENTIMENT_THRESHOLD and \
           (gcp_sentiment.magnitude is None or gcp_sentiment.magnitude > VERY_STRONG_NEGATIVE_MAGNITUDE_THRESHOLD):
            current_risk_score += BASE_SENTIMENT_RISK_ADDITION
            contributing_factors.append(
                f"Text exhibits very strong negative sentiment ({sentiment_desc}), increasing assessed risk."
            )
        elif gcp_sentiment.sentiment_score < STRONG_NEGATIVE_SENTIMENT_THRESHOLD:
            if current_risk_score > SENTIMENT_AMPLIFICATION_MIN_RISK_THRESHOLD:
                current_risk_score += SENTIMENT_AMPLIFICATION_BOOST
                contributing_factors.append(
                    f"Strongly negative sentiment ({sentiment_desc}) amplified risk from other factors."
                )
            else:
                contributing_factors.append(
                    f"Detected strongly negative sentiment ({sentiment_desc})." # Removed: ", though other primary risk factors were minimal to amplify."
                )
        elif gcp_sentiment.sentiment_label not in ["neutral", "unavailable"] and "error" not in gcp_sentiment.sentiment_label:
             contributing_factors.append(
                f"The text carries a {gcp_sentiment.sentiment_label} sentiment ({sentiment_desc})."
            )

    final_score = round(max(0.0, current_risk_score), 3)

    risk_label = "Low"
    if final_score >= RISK_LABEL_CRITICAL_THRESHOLD: risk_label = "Critical"
    elif final_score >= RISK_LABEL_HIGH_THRESHOLD: risk_label = "High"
    elif final_score >= RISK_LABEL_MEDIUM_THRESHOLD: risk_label = "Medium"

    if not contributing_factors and final_score < 0.1:
        contributing_factors.append("No significant risk indicators found based on current rules.")

    return PeaceGuardRiskOutput(
        score=final_score, 
        label=risk_label, 
        contributing_factors=sorted(list(set(contributing_factors))),
        detected_framings=sorted(list(set(detected_framings_list)))
    )

def analyze_text_content(request: TextAnalysisRequest) -> TextAnalysisResponse:
    text_to_analyze = request.text
    user_language_hint = request.language_hint
    text_lower = text_to_analyze.lower()

    lang_detected_by_translate = nlp_utils.detect_language_gcp_sync(text_to_analyze)
    
    lang_for_nlu_api = None
    if user_language_hint and "error" not in str(user_language_hint):
        lang_for_nlu_api = user_language_hint
    elif lang_detected_by_translate and "error" not in str(lang_detected_by_translate):
        lang_for_nlu_api = lang_detected_by_translate

    found_keywords: List[KeywordMatch] = []
    keyword_score_contribution_for_display = 0.0
    
    current_lang_for_keywords_check = lang_for_nlu_api or lang_detected_by_translate
    run_keyword_analysis = False
    if current_lang_for_keywords_check is None or \
       (isinstance(current_lang_for_keywords_check, str) and "error" in current_lang_for_keywords_check) or \
       (isinstance(current_lang_for_keywords_check, str) and current_lang_for_keywords_check.startswith('en')):
        run_keyword_analysis = True
        
    if run_keyword_analysis:
        # Combine all keyword lists for comprehensive flagging for display
        # Ensure all keywords in lists are lowercase for matching with text_lower
        all_display_keywords = set(
            [k.lower() for k in DANGEROUS_KEYWORDS] + 
            [k.lower() for k in SENSITIVE_KEYWORDS] + 
            [k.lower() for k in CONTEXTUAL_CONCERN_KEYWORDS_LIST]
        )
        for keyword in all_display_keywords:
            count = text_lower.count(keyword)
            if count > 0:
                found_keywords.append(KeywordMatch(keyword=keyword, count=count))
                # This score is just for the keyword_analysis_score field (capped 0-1)
                # The main PeaceGuard score calculates keyword impact differently
                if keyword in DANGEROUS_KEYWORDS:
                    keyword_score_contribution_for_display += (DANGEROUS_KEYWORD_MULTIPLIER * count)
                elif keyword in SENSITIVE_KEYWORDS: # Contextual not added to this specific score
                    keyword_score_contribution_for_display += (SENSITIVE_KEYWORD_MULTIPLIER * count)
    
    keyword_analysis_final_score = min(keyword_score_contribution_for_display, 1.0)

    gcp_sentiment_raw = nlp_utils.get_sentiment_gcp_sync(text_to_analyze, language_code=lang_for_nlu_api)
    gcp_sentiment_data = GCPSentimentOutput(**gcp_sentiment_raw)

    gcp_risk_assessment_raw = nlp_utils.get_content_categories_gcp_sync(text_to_analyze, language_code=lang_for_nlu_api)
    gcp_risk_data = GCPRiskAssessmentOutput(
        risk_categories=[GCPCategoryMatch(**cat) for cat in gcp_risk_assessment_raw.get("risk_categories", [])],
        explanation=gcp_risk_assessment_raw.get("explanation")
    )

    peaceguard_risk_data = calculate_peaceguard_risk(
        text_lower=text_lower,
        gcp_sentiment=gcp_sentiment_data,
        gcp_risk_assessment=gcp_risk_data,
        flagged_keywords=found_keywords 
    )

    triggered_ews_alerts: Optional[List[EWSAlert]] = None
    if peaceguard_risk_data and peaceguard_risk_data.score >= EWS_AUTO_TRIGGER_RISK_SCORE_THRESHOLD:
        print(f"PeaceGuard AI risk score ({peaceguard_risk_data.score:.3f}) met threshold ({EWS_AUTO_TRIGGER_RISK_SCORE_THRESHOLD}). Auto-triggering EWS check.")
        ews_input_data = EWSInput(
            original_text=text_to_analyze,
            detected_language=lang_detected_by_translate,
            peaceguard_risk=peaceguard_risk_data,
            gcp_sentiment=gcp_sentiment_data,
            gcp_risk_assessment=gcp_risk_data,
            flagged_keywords=found_keywords
        )
        triggered_ews_alerts = early_warning_service.evaluate_content_for_ews(ews_input_data)
        if triggered_ews_alerts:
            print(f"EWS triggered {len(triggered_ews_alerts)} alert(s).")
        else:
            print("EWS check completed, no specific EWS patterns matched by this input.")
    
    narrative_parts = []
    if peaceguard_risk_data:
        narrative_parts.append(
            f"PeaceGuard AI assessment: '{peaceguard_risk_data.label}' risk (Score: {peaceguard_risk_data.score:.3f})."
        )
    
    final_detected_lang_display = lang_detected_by_translate
    if "error" in (final_detected_lang_display or ""): final_detected_lang_display = f"Detection Error"
    elif final_detected_lang_display is None: final_detected_lang_display = "Undetermined"
    narrative_parts.append(f"Language: '{final_detected_lang_display}'.")
    
    if gcp_sentiment_data and "error" not in gcp_sentiment_data.sentiment_label and "unavailable" not in gcp_sentiment_data.sentiment_label:
        narrative_parts.append(
            f"Sentiment: '{gcp_sentiment_data.sentiment_label}' (Score: {gcp_sentiment_data.sentiment_score:.3f}, Intensity: {gcp_sentiment_data.magnitude:.3f})."
        )
    
    if found_keywords:
        kw_summary = [f"'{kw.keyword}' ({kw.count}x)" for kw in found_keywords[:3]]
        narrative_parts.append(f"Flagged keywords: {', '.join(kw_summary)}{' and others.' if len(found_keywords) > 3 else '.'}")
    else:
        narrative_parts.append("No predefined keywords detected.")

    if peaceguard_risk_data and peaceguard_risk_data.detected_framings:
        narrative_parts.append(f"Potential manipulative framing: {', '.join(peaceguard_risk_data.detected_framings)}.")

    if gcp_risk_data and gcp_risk_data.risk_categories:
        cat_names = [f"'{cat.category}' ({cat.confidence*100:.1f}%)" for cat in gcp_risk_data.risk_categories[:2]]
        narrative_parts.append(f"GCP noted sensitive categories: {', '.join(cat_names)}{'...' if len(gcp_risk_data.risk_categories) > 2 else '.'}")
    
    if triggered_ews_alerts:
        narrative_parts.append(f"EWS Analysis: {len(triggered_ews_alerts)} high-level warning pattern(s) matched. See 'ews_alerts' for details.")
    elif peaceguard_risk_data and peaceguard_risk_data.score >= EWS_AUTO_TRIGGER_RISK_SCORE_THRESHOLD:
         narrative_parts.append("EWS Analysis: Initial risk met threshold for EWS check, but no specific historical patterns were matched by this input.")


    final_overall_explanation = " ".join(narrative_parts)
    
    return TextAnalysisResponse(
        original_text=text_to_analyze,
        detected_language=final_detected_lang_display,
        gcp_sentiment=gcp_sentiment_data,
        gcp_risk_assessment=gcp_risk_data,
        keyword_analysis_score=keyword_analysis_final_score,
        flagged_keywords=found_keywords,
        peaceguard_risk=peaceguard_risk_data,
        ews_alerts=triggered_ews_alerts,
        overall_explanation=final_overall_explanation
    )