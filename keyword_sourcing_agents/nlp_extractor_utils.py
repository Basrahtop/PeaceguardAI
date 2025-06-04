import re
from typing import List, Dict, Any, Optional # Ensured List is imported
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
from collections import Counter
import string

# Ensure NLTK data is available (user should download these once via Python interpreter)
# Example: import nltk; nltk.download('stopwords'); nltk.download('punkt')
try:
    stop_words_english = set(stopwords.words('english'))
    # Add stopwords for other languages if you plan to process them:
    # stop_words_french = set(stopwords.words('french'))
except LookupError:
    print("WARNING: NLTK 'stopwords' not found. Keyword extraction quality will be affected. "
          "Please download them: In Python, run: import nltk; nltk.download('stopwords')")
    stop_words_english = set()

try:
    # Test if 'punkt' is available by trying to use it.
    sent_tokenize("Test sentence. Another test sentence.")
    print("INFO:     NLTK 'punkt' tokenizer found.")
except LookupError:
    print("WARNING: NLTK 'punkt' tokenizer models not found. Keyword extraction quality will be affected. "
          "Please download them: In Python, run: import nltk; nltk.download('punkt')")


def preprocess_text(text: str) -> List[str]:
    """Lowercase, remove punctuation, tokenize, and remove stopwords."""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r'\d+', '', text) # Remove numbers
    text = text.translate(str.maketrans('', '', string.punctuation)) # Remove punctuation
    
    try:
        tokens = word_tokenize(text)
    except Exception as e:
        # Fallback if word_tokenize fails (e.g., if punkt is still missing despite checks)
        print(f"WARNING: word_tokenize failed: {e}. Falling back to simple split().")
        tokens = text.split()
        
    custom_stopwords = stop_words_english.union({'rt', 'via', 'also', 'could', 'would', 'may', 'might', 'must', 'shall', 'will', 'says', 'said', 'like', 'get', 'us'})
    filtered_tokens = [word for word in tokens if word.isalpha() and word not in custom_stopwords and len(word) > 2]
    return filtered_tokens

def extract_frequent_terms(text: str, top_n: int = 10) -> List[tuple[str, int]]:
    """Extracts most frequent single terms."""
    tokens = preprocess_text(text)
    if not tokens:
        return []
    return Counter(tokens).most_common(top_n)

def extract_frequent_ngrams(text: str, n: int = 2, top_n: int = 10) -> List[tuple[str, int]]:
    """Extracts most frequent n-grams (phrases)."""
    tokens = preprocess_text(text)
    if not tokens or len(tokens) < n:
        return []
    
    try:
        n_grams_list = ngrams(tokens, n)
        n_grams_strings = [" ".join(grams) for grams in n_grams_list]
        return Counter(n_grams_strings).most_common(top_n)
    except Exception as e:
        print(f"WARNING: N-gram extraction failed (n={n}): {e}")
        return []

def extract_candidate_keywords(text_content: str, source_url: Optional[str] = None, source_api: Optional[str] = None, language: Optional[str] = 'en') -> List[Dict[str, Any]]:
    """
    Extracts candidate keywords (single terms, bi-grams, tri-grams) from text.
    Returns a list of dictionaries, each representing a candidate keyword.
    """
    if not text_content:
        return []

    candidates: List[Dict[str, Any]] = []
    
    single_terms = extract_frequent_terms(text_content, top_n=10)
    for term, freq in single_terms:
        candidates.append({
            "term": term,
            "frequency": freq,
            "type_suggestion": "SINGLE_TERM",
            "language_code": language,
            "source_api": source_api,
            "source_url": source_url,
            "context_snippet": text_content[:250] + "..."
        })
        
    bigrams = extract_frequent_ngrams(text_content, n=2, top_n=7)
    for bigram, freq in bigrams:
        candidates.append({
            "term": bigram,
            "frequency": freq,
            "type_suggestion": "BIGRAM_PHRASE",
            "language_code": language,
            "source_api": source_api,
            "source_url": source_url,
            "context_snippet": text_content[:250] + "..."
        })
        
    trigrams = extract_frequent_ngrams(text_content, n=3, top_n=5)
    for trigram, freq in trigrams:
        candidates.append({
            "term": trigram,
            "frequency": freq,
            "type_suggestion": "TRIGRAM_PHRASE",
            "language_code": language,
            "source_api": source_api,
            "source_url": source_url,
            "context_snippet": text_content[:250] + "..."
        })
            
    return candidates