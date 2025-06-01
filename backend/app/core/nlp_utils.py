from google.cloud import language_v2
from google.cloud import translate_v2 as translate
import json
import os
from google.oauth2 import service_account # Added for loading creds from env var

# --- Modified Google Cloud Client Initialization ---
gcp_sa_key_content = os.getenv("GCP_SA_KEY_JSON_CONTENT")
gcp_credentials = None

if gcp_sa_key_content:
    try:
        credentials_info = json.loads(gcp_sa_key_content)
        gcp_credentials = service_account.Credentials.from_service_account_info(credentials_info)
        print("INFO:     NLP Utils: Loaded GCP credentials from GCP_SA_KEY_JSON_CONTENT env var.")
    except Exception as e:
        print(f"ERROR:    NLP Utils: Failed to load GCP credentials from ENV content: {e}. Falling back to default.")
# If gcp_credentials is None, the libraries will try Application Default Credentials (ADC)
# which includes GOOGLE_APPLICATION_CREDENTIALS file path for local dev.

try:
    language_client = language_v2.LanguageServiceClient(credentials=gcp_credentials) if gcp_credentials else language_v2.LanguageServiceClient()
    translate_client = translate.Client(credentials=gcp_credentials) if gcp_credentials else translate.Client()
    if not gcp_credentials and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("WARNING:  NLP Utils: Neither GCP_SA_KEY_JSON_CONTENT nor GOOGLE_APPLICATION_CREDENTIALS seem to be set for default client init.")
    print("INFO:     NLP Utils: Google Cloud Language and Translate clients initialized.")
except Exception as e:
    print(f"ERROR:    NLP Utils: Failed to initialize Google Cloud clients: {e}.")
    language_client = None
    translate_client = None
# --- End of Modified Initialization ---

def detect_language_gcp_sync(text: str) -> str | None:
    if not translate_client:
        print("ERROR:    NLP Utils: Google Translate client not initialized.")
        return "error_client_init"
    if not text:
        return None
    try:
        result = translate_client.detect_language(text)
        return result['language'] if result and 'language' in result else None
    except Exception as e:
        print(f"ERROR:    NLP Utils: Google Cloud language detection error: {e}")
        return "error_detection"

def get_sentiment_gcp_sync(text: str, language_code: str = None) -> dict:
    if not language_client:
        print("ERROR:    NLP Utils: Google Natural Language client not initialized.")
        return {"sentiment_label": "unavailable", "sentiment_score": 0.0, "magnitude": 0.0, "error": "Language client not initialized."}
    if not text:
        return {"sentiment_label": "neutral", "sentiment_score": 0.0, "magnitude": 0.0, "error": "Input text is empty."}

    doc_type = language_v2.types.Document.Type.PLAIN_TEXT
    effective_language_code = language_code if language_code and "error" not in language_code else None
    document = language_v2.types.Document(
        content=text, type_=doc_type, language_code=effective_language_code
    )
    try:
        response = language_client.analyze_sentiment(document=document)
        sentiment = response.document_sentiment
        sentiment_label = "neutral"
        if sentiment.score > 0.25: sentiment_label = "positive"
        elif sentiment.score < -0.25: sentiment_label = "negative"
        detected_lang_from_sentiment = response.language_code if response.language_code else None
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": round(sentiment.score, 4),
            "magnitude": round(sentiment.magnitude, 4),
            "detected_language_by_nlp_api": detected_lang_from_sentiment
        }
    except Exception as e:
        print(f"ERROR:    NLP Utils: Google Cloud sentiment analysis error: {e}")
        return {"sentiment_label": "error", "sentiment_score": 0.0, "magnitude": 0.0, "details": str(e)}

def get_content_categories_gcp_sync(text: str, language_code: str = None) -> dict:
    if not language_client:
        print("ERROR:    NLP Utils: Google Natural Language client not initialized.")
        return {"risk_categories": [], "explanation": "Language client not initialized."}
    if not text:
         return {"risk_categories": [], "explanation": "Input text is empty."}

    effective_language_code = language_code if language_code and "error" not in language_code else None
    document = language_v2.types.Document(
        content=text, type_=language_v2.types.Document.Type.PLAIN_TEXT, language_code=effective_language_code
    )
    found_risk_categories = []
    explanation_parts = []
    try:
        response = language_client.classify_text(document=document)
        if not response.categories:
            explanation_parts.append("No content categories returned by the API.")
        for category_proto in response.categories:
            category_name = category_proto.name
            confidence = round(category_proto.confidence, 4)
            risky_keywords_in_category_path = ["/Sensitive Subjects", "/Adult", "/Violence", "/Hate Speech", "/Profanity", "/Derogatory", "/War & Conflict", "/Terrorism"]
            is_risky = any(keyword.lower() in category_name.lower() for keyword in risky_keywords_in_category_path) # case-insensitive check
            if is_risky and confidence > 0.3:
                found_risk_categories.append({"category": category_name, "confidence": confidence})
                explanation_parts.append(f"Identified '{category_name}' (conf: {confidence*100:.1f}%)")
        if not found_risk_categories and not explanation_parts:
             explanation_parts.append("No predefined high-risk categories detected with sufficient confidence.")
        return {
            "risk_categories": found_risk_categories, 
            "explanation": ". ".join(explanation_parts) if explanation_parts else "Content classification performed."
        }
    except Exception as e:
        print(f"ERROR:    NLP Utils: Google Cloud content categorization error: {e}")
        if "Unsupported language" in str(e) or "Invalid language code" in str(e):
             return {"risk_categories": [{"category": "error_unsupported_language", "confidence": 0.0}], "explanation": f"Content classification not supported: {str(e)}"}
        return {"risk_categories": [{"category": "error_classification", "confidence": 0.0}], "explanation": str(e)}