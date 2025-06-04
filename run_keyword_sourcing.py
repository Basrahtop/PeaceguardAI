from dotenv import load_dotenv
load_dotenv() # Loads variables from .env into environment for os.getenv()

import json
from keyword_sourcing_agents import rss_agent, newsapi_agent
from datetime import datetime
import os # For checking NEWSAPI_KEY after load_dotenv

def run_all_sourcing_agents():
    print("Starting keyword sourcing from all agents...")
    all_candidate_keywords = []

    # Run RSS Agent
    print("\n--- Running RSS Agent ---")
    try:
        rss_candidates = rss_agent.run_rss_keyword_sourcing()
        all_candidate_keywords.extend(rss_candidates)
    except Exception as e:
        print(f"ERROR:    MainSourcing: Failed running RSS agent: {e}")

    # Run NewsAPI Agent
    print("\n--- Running NewsAPI Agent ---")
    try:
        # newsapi_agent module now initializes client based on os.getenv at its import time
        # We can check its global `newsapi_client` to see if it initialized
        if newsapi_agent.newsapi_client: 
            newsapi_candidates = newsapi_agent.run_newsapi_keyword_sourcing()
            all_candidate_keywords.extend(newsapi_candidates)
        else:
            print("INFO:     MainSourcing: Skipping NewsAPI agent as its client was not initialized (check NEWSAPI_KEY).")
    except Exception as e:
        print(f"ERROR:    MainSourcing: Failed running NewsAPI agent: {e}")
        
    # --- Add calls to other agents here as you implement them ---

    print(f"\n--- Keyword Sourcing Complete ---")
    print(f"Total candidate keywords gathered: {len(all_candidate_keywords)}")

    if all_candidate_keywords:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"candidate_keywords_master_{timestamp}.json"
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(all_candidate_keywords, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved all candidate keywords to: {output_filename}")
            print("Next step: VET these candidates and update your 'dynamic_keywords.json' or 'observed_hot_terms.json'.")
        except Exception as e:
            print(f"ERROR:    MainSourcing: Failed saving candidate keywords to file: {e}")
    else:
        print("No candidate keywords were gathered from any source.")

if __name__ == '__main__':
    # Reminder for NLTK data if user sees warnings from nlp_extractor_utils
    print("Reminder: If you see NLTK download warnings, run the following in a Python interpreter:")
    print(">>> import nltk")
    print(">>> nltk.download('stopwords')")
    print(">>> nltk.download('punkt')")
    print("-" * 30)
    
    run_all_sourcing_agents()