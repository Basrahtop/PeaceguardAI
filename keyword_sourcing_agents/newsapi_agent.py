import os
from newsapi import NewsApiClient # type: ignore  (newsapi-python might not have type stubs)
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .nlp_extractor_utils import extract_candidate_keywords # Relative import

# Load NewsAPI key from environment variables
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

newsapi_client: Optional[NewsApiClient] = None
if NEWSAPI_KEY:
    try:
        newsapi_client = NewsApiClient(api_key=NEWSAPI_KEY)
        print("INFO:     NewsAPI client initialized.")
    except Exception as e:
        print(f"ERROR:    Failed to initialize NewsAPI client: {e}. Ensure NEWSAPI_KEY is set.")
else:
    print("WARNING:  NEWSAPI_KEY not found in environment. NewsAPI agent will not run.")


def fetch_from_newsapi(
    query: Optional[str] = None, 
    sources: Optional[str] = None, # Comma-separated string of source IDs
    category: Optional[str] = None, # e.g., business, entertainment, general, health, science, sports, technology
    language: str = 'en', 
    country: Optional[str] = None, # e.g., ng, za, ke, cd, bf
    page_size: int = 20 # Max 100 for free tier usually
) -> List[Dict[str, Any]]:
    """Fetches articles from NewsAPI.org and extracts candidate keywords."""
    if not newsapi_client:
        print("NewsAPI client not available.")
        return []

    print(f"Fetching from NewsAPI: query='{query}', country='{country}', language='{language}', sources='{sources}', category='{category}'")
    
    # Get yesterday's date for 'from_param' to ensure recent news
    # NewsAPI on free tier often restricts 'from' to not too far in the past
    from_param = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')

    all_candidates: List[Dict[str, Any]] = []
    try:
        # Use get_everything for more flexibility, or get_top_headlines
        if query or sources: # Query or specific sources require get_everything
             all_articles = newsapi_client.get_everything(
                q=query,
                sources=sources,
                language=language,
                sort_by='relevancy', # or 'publishedAt', 'popularity'
                page_size=page_size,
                from_param=from_param # Restrict to recent articles
            )
        elif country or category: # Top headlines by country/category
            all_articles = newsapi_client.get_top_headlines(
                q=query, # Can also add a general query here
                category=category,
                language=language,
                country=country,
                page_size=page_size
            )
        else:
            print("NewsAPI: Must provide query, sources, country, or category.")
            return []

        if all_articles['status'] == 'ok':
            for article in all_articles['articles'][:page_size]: # Process received articles
                title = article.get('title', "")
                description = article.get('description', "")
                content = article.get('content', "") # Often truncated on free tier
                url = article.get('url', "")
                source_name = article.get('source', {}).get('name', 'NewsAPI')

                # Combine available text fields for keyword extraction
                text_content = f"{title}. {description}. {content if content else ''}"
                
                if text_content.strip() and text_content != ". .":
                    candidates_from_article = extract_candidate_keywords(
                        text_content, 
                        source_url=url, 
                        source_api=f"NewsAPI: {source_name}"
                    )
                    all_candidates.extend(candidates_from_article)
            print(f"Found {len(all_candidates)} candidate terms from NewsAPI for query/params.")
        else:
            print(f"ERROR: NewsAPI request failed: {all_articles.get('message')}")
            
    except Exception as e:
        print(f"ERROR: Exception during NewsAPI fetch: {e}")
        
    return all_candidates

def run_newsapi_keyword_sourcing() -> List[Dict[str, Any]]:
    """Runs keyword sourcing from NewsAPI for predefined queries/countries."""
    if not newsapi_client:
        return []
        
    master_candidate_list: List[Dict[str, Any]] = []
    
    # Example queries - these should be tailored to your monitoring needs
    # Consider regions like Nigeria (ng), Burkina Faso (bf), DRC (cd)
    # You can get source IDs from NewsAPI documentation if you want to target specific outlets.
    
    # General news from Nigeria
    master_candidate_list.extend(fetch_from_newsapi(country='ng', language='en', page_size=10))
    # General news from DRC
    master_candidate_list.extend(fetch_from_newsapi(country='cd', language='fr', page_size=5)) # French for DRC
    master_candidate_list.extend(fetch_from_newsapi(country='cd', language='en', page_size=5)) # English for DRC if available
    # General news from Burkina Faso
    master_candidate_list.extend(fetch_from_newsapi(country='bf', language='fr', page_size=5)) # French for BF
    
    # Specific query example
    master_candidate_list.extend(fetch_from_newsapi(query='Sahel security OR Boko Haram OR ISWAP', language='en', page_size=10))
    master_candidate_list.extend(fetch_from_newsapi(query='corruption africa OR élection afrique', language='en', page_size=10)) # Mixed lang query example

    print(f"Total candidate terms (including duplicates) from NewsAPI: {len(master_candidate_list)}")
    return master_candidate_list

if __name__ == '__main__':
    # Example of running this agent directly
    if not NEWSAPI_KEY:
        print("Skipping NewsAPI example run as NEWSAPI_KEY is not set.")
    else:
        newsapi_candidates = run_newsapi_keyword_sourcing()
        if newsapi_candidates:
            print("\n--- Sample NewsAPI Candidates ---")
            for i, candidate in enumerate(newsapi_candidates[:5]):
                print(f"{i+1}. Term: '{candidate['term']}', Freq: {candidate['frequency']}, Source: {candidate['source_api']}")
            # with open("candidate_keywords_newsapi.json", "w", encoding="utf-8") as f:
            #     json.dump(newsapi_candidates, f, indent=2, ensure_ascii=False)
            # print("Saved NewsAPI candidates to candidate_keywords_newsapi.json")