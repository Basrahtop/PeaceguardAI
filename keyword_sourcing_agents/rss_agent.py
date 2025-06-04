import feedparser
from typing import List, Dict, Any
from .nlp_extractor_utils import extract_candidate_keywords

AFRICA_RSS_FEEDS = {
    "Premium Times Nigeria": "https://www.premiumtimesng.com/feed",
    "The Nation Nigeria": "https://thenationonlineng.net/feed/",
    "Sahara Reporters": "http://saharareporters.com/feed", # Check if still active, sometimes http
    "Al Jazeera Africa": "https://www.aljazeera.com/xml/rss/africa.xml",
    "BBC News Africa": "http://feeds.bbci.co.uk/news/world/africa/rss.xml",
    "Reuters Africa": "https://www.reutersagency.com/feed/?best-topics=africa&post_type=best", # Example, actual might differ
    # Add more feeds relevant to Nigeria, Burkina Faso, DRC
    "LeFaso.net (Burkina Faso)": "https://lefaso.net/spip.php?page=backend",
    "Actualite.cd (DRC)": "https://actualite.cd/feed",
    # "Radio Okapi (DRC)": "https://www.radiookapi.net/feed" # Check actual feed URL
}

def fetch_from_rss(feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
    print(f"INFO:     RSS Agent: Fetching from {feed_name} ({feed_url})")
    parsed_feed = feedparser.parse(feed_url)
    all_candidates: List[Dict[str, Any]] = []

    if parsed_feed.bozo:
        print(f"WARNING:  RSS Agent: Error parsing feed {feed_name}: {parsed_feed.get('bozo_exception', 'Unknown parsing error')}")

    for entry in parsed_feed.entries[:5]: # Limit to first 5 entries per feed for this MVP
        title = entry.title if hasattr(entry, 'title') else ""
        summary = entry.summary if hasattr(entry, 'summary') else ""
        link = entry.link if hasattr(entry, 'link') else feed_url
        
        # Attempt to determine language from feed or entry if available
        language = entry.get('language', parsed_feed.feed.get('language', 'en')).split('-')[0] # Default to 'en'

        text_content = f"{title}. {summary}"
        
        if text_content.strip() and text_content != ". .":
            candidates_from_entry = extract_candidate_keywords(
                text_content, 
                source_url=link, 
                source_api=f"RSS: {feed_name}",
                language=language
            )
            all_candidates.extend(candidates_from_entry)
        
    print(f"INFO:     RSS Agent: Found {len(all_candidates)} candidate terms from {feed_name}.")
    return all_candidates

def run_rss_keyword_sourcing() -> List[Dict[str, Any]]:
    master_candidate_list: List[Dict[str, Any]] = []
    for name, url in AFRICA_RSS_FEEDS.items():
        try:
            master_candidate_list.extend(fetch_from_rss(url, name))
        except Exception as e:
            print(f"ERROR:    RSS Agent: Failed to process feed {name} at {url}: {e}")
    
    print(f"INFO:     RSS Agent: Total candidate terms from RSS: {len(master_candidate_list)}")
    return master_candidate_list

if __name__ == '__main__':
    rss_candidates = run_rss_keyword_sourcing()
    if rss_candidates:
        print("\n--- Sample RSS Candidates (First 5) ---")
        for i, candidate in enumerate(rss_candidates[:5]):
            print(f"{i+1}. Term: '{candidate['term']}', Freq: {candidate['frequency']}, Lang: {candidate['language_code']}, Source: {candidate['source_api']}")