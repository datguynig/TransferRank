"""Guardian Open Platform API integration for football transfer news."""

import os
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

# Import player extraction utilities from BBC module
from .bbc_rss import extract_player_from_title, extract_clubs_from_text, infer_league_from_clubs

def fetch_guardian_transfers() -> List[Dict]:
    """
    Fetch transfer news from Guardian Open Platform API.
    Returns list of normalised rumour data.
    """
    api_key = os.environ.get('GUARDIAN_API_KEY')
    if not api_key:
        logger.warning("No Guardian API key provided, skipping Guardian ingest")
        return []
    
    # Guardian API endpoint
    base_url = "https://content.guardianapis.com/search"
    
    params = {
        'api-key': api_key,
        'section': 'football',
        'q': 'transfer OR signing OR fee',
        'show-fields': 'trailText,headline,byline',
        'page-size': 20,
        'order-by': 'newest',
        'format': 'json'
    }
    
    try:
        logger.info("Fetching transfer news from Guardian API")
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['response']['status'] != 'ok':
            logger.error(f"Guardian API error: {data['response']['status']}")
            return []
        
        articles = data['response']['results']
        rumours = []
        
        for article in articles:
            # Extract basic information
            title = article.get('webTitle', '')
            trail_text = article.get('fields', {}).get('trailText', '')
            url = article.get('webUrl', '')
            pub_date_str = article.get('webPublicationDate', '')
            
            # Parse publication date
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            except:
                pub_date = datetime.utcnow()
            
            # Extract player name
            player_name = extract_player_from_title(title, trail_text)
            
            # Extract clubs
            clubs = extract_clubs_from_text(f"{title} {trail_text}")
            
            # Skip if no meaningful transfer information
            if not clubs["from_club"] and not clubs["to_club"] and not player_name:
                continue
            
            # Infer league
            league = infer_league_from_clubs(clubs["from_club"] or "", clubs["to_club"] or "")
            
            rumour_data = {
                "player_name": player_name,
                "from_club": clubs["from_club"] or "Unknown",
                "to_club": clubs["to_club"] or "Unknown",
                "league": league,
                "position": None,
                "reported_fee": None,
                "wage_estimate": None,
                "contract_years_left": None,
                "source_name": "The Guardian",
                "source_url": url,
                "source_type": "outlet",
                "source_claim": f"{title}. {trail_text}",
                "first_seen_date": pub_date,
                "last_seen_date": pub_date,
                "sightings_count": 1,
                "distinct_sources_7d": 1
            }
            
            rumours.append(rumour_data)
            logger.debug(f"Parsed Guardian rumour: {player_name or 'Unknown player'} -> {clubs['to_club']}")
        
        logger.info(f"Successfully parsed {len(rumours)} rumours from Guardian API")
        return rumours
        
    except requests.RequestException as e:
        logger.error(f"Error fetching from Guardian API: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in Guardian fetch: {str(e)}")
        return []