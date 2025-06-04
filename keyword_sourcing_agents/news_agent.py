import os
from newsapi import NewsApiClient # type: ignore
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .nlp_extractor_utils import extract_candidate_keywords

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY") # Loaded by load_dotenv() in main script

newsapi_client: Optional[NewsApiClient] = None
if NEWSAPI_KEY:
    try:
        newsapi_client = NewsApiClient(api_key=NEWSAPI_KEY)
        print("INFO:     NewsAPI client initialized.")
    except Exception as e:
        print(f"ERROR:    NewsAPI: Failed to initialize client: {e}. Ensure NEWSAPI_KEY is correct.")
else:
    print("WARNING:  NewsAPI: NEWSAPI_KEY not found. NewsAPI agent will be skipped.")


def fetch_from_newsapi(
    query: Optional[str] = None, 
    sources: Optional[str] = None, 
    category: Optional[str] = None,
    language: str = 'en', 
    country: Optional[str] = None,
    page_size: int = 20 
) -> List[Dict[str, Any]]:
    if not newsapi_client:
        print("WARNING:  NewsAPI: Client not available. Skipping fetch.")
        return []

    print(f"INFO:     NewsAPI: Fetching: query='{query}', country='{country}', lang='{language}', cat='{category}'")
    
    from_param = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d') # Last 2 days, free tier limitation

    all_candidates: List[Dict[str, Any]] = []
    try:
        if query or sources:
             all_articles = newsapi_client.get_everything(
                q=query, sources=sources, language=language, sort_by='relevancy',
                page_size=page_size, from_param=from_param
            )
        elif country or category:
            all_articles = newsapi_client.get_top_headlines(
                q=query, category=category, language=language, country=country, page_size=page_size
            )
        else:
            print("WARNING:  NewsAPI: Must provide query, sources, country, or category.")
            return []

        if all_articles['status'] == 'ok':
            print(f"INFO:     NewsAPI: Retrieved {all_articles['totalResults']} total articles, processing up to {page_size}.")
            for article in all_articles['articles']:
                title = article.get('title', "")
                description = article.get('description', "")
                content = article.get('content', "") 
                url = article.get('url', "")
                source_name = article.get('source', {}).get('name', 'NewsAPI')

                text_content = f"{title}. {description if description else ''}. {content if content else ''}"
                
                if text_content.strip() and text_content != ". .":
                    candidates_from_article = extract_candidate_keywords(
                        text_content, source_url=url, source_api=f"NewsAPI: {source_name}", language=language
                    )
                    all_candidates.extend(candidates_from_article)
            print(f"INFO:     NewsAPI: Found {len(all_candidates)} candidate terms from this query.")
        else:
            print(f"ERROR:    NewsAPI: Request failed: {all_articles.get('code')} - {all_articles.get('message')}")
            
    except Exception as e:
        print(f"ERROR:    NewsAPI: Exception during fetch: {e}")
        
    return all_candidates

def run_newsapi_keyword_sourcing() -> List[Dict[str, Any]]:
    if not newsapi_client:
        return []
        
    master_candidate_list: List[Dict[str, Any]] = []
    
    # Example queries relevant to context
    # Nigeria
    master_candidate_list.extend(fetch_from_newsapi(country='ng', language='en', page_size=15, category='general'))
    master_candidate_list.extend(fetch_from_newsapi(query='Nigeria security OR politics OR election', language='en', page_size=10))
    
    # Burkina Faso (primarily French news)
    master_candidate_list.extend(fetch_from_newsapi(country='bf', language='fr', page_size=10, category='general'))
    master_candidate_list.extend(fetch_from_newsapi(query='Burkina Faso sécurité OR politique', language='fr', page_size=5))
    
    # DRC (primarily French news)
    master_candidate_list.extend(fetch_from_newsapi(country='cd', language='fr', page_size=10, category='general'))
    master_candidate_list.extend(fetch_from_newsapi(query='RDC conflit OR Kivu OR élection', language='fr', page_size=5))

    print(f"INFO:     NewsAPI: Total candidate terms from NewsAPI: {len(master_candidate_list)}")
    return master_candidate_list

if __name__ == '__main__':
    if not NEWSAPI_KEY:
        print("Skipping NewsAPI example run as NEWSAPI_KEY is not set in .env or environment.")
    else:
        newsapi_candidates = run_newsapi_keyword_sourcing()
        if newsapi_candidates:
            print("\n--- Sample NewsAPI Candidates (First 5) ---")
            for i, candidate in enumerate(newsapi_candidates[:5]):
                print(f"{i+1}. Term: '{candidate['term']}', Freq: {candidate['frequency']}, Lang: {candidate['language_code']}, Source: {candidate['source_api']}")