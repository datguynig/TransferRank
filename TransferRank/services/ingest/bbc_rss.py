"""BBC Sport Football RSS feed parser and normaliser."""

import os
import re
import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

# Common football player names for fuzzy matching
# This would normally be populated from the database
KNOWN_PLAYERS = [
    "Harry Kane", "Erling Haaland", "Kylian Mbappe", "Vinicius Junior", 
    "Jude Bellingham", "Pedri", "Gavi", "Jamal Musiala", "Bukayo Saka",
    "Phil Foden", "Mason Mount", "Declan Rice", "Moises Caicedo",
    "Enzo Fernandez", "Christopher Nkunku", "Victor Osimhen",
    "Rafael Leao", "Khvicha Kvaratskhelia", "Martin Odegaard",
    "Alexander Isak", "Nick Woltemade", "Darwin Nunez", "Cody Gakpo",
    "Mohamed Salah", "Kevin De Bruyne", "Marcus Rashford", "Bruno Fernandes"
]

# Transfer-related keywords to filter relevant articles
TRANSFER_KEYWORDS = [
    "transfer", "signing", "sign", "move", "joins", "join", "agreement", 
    "deal", "fee", "contract", "target", "interest", "bid", "offer",
    "swap", "loan", "permanent", "clause", "release"
]

def extract_player_from_title(title: str, description: str = "") -> Optional[str]:
    """
    Extract player name from RSS title using fuzzy matching.
    Returns best match if confidence > 80, otherwise None.
    """
    text = f"{title} {description}".lower()
    
    best_match = None
    best_score = 0
    
    for player in KNOWN_PLAYERS:
        # Try exact name match
        if player.lower() in text:
            return player
            
        # Try surname match
        surname = player.split()[-1].lower()
        if surname in text and len(surname) > 3:  # Avoid short surnames
            score = fuzz.partial_ratio(player.lower(), text)
            if score > best_score and score > 80:
                best_score = score
                best_match = player
    
    return best_match

def extract_clubs_from_text(text: str) -> Dict[str, Optional[str]]:
    """
    Extract from_club and to_club from text using common patterns.
    """
    text_lower = text.lower()
    
    # Common club patterns
    club_patterns = [
        r'(\w+(?:\s+\w+)*)\s+to\s+(\w+(?:\s+\w+)*)',
        r'from\s+(\w+(?:\s+\w+)*)\s+to\s+(\w+(?:\s+\w+)*)',
        r'leaving\s+(\w+(?:\s+\w+)*)\s+for\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+sign\s+.*from\s+(\w+(?:\s+\w+)*)',
    ]
    
    for pattern in club_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if 'to' in pattern or 'for' in pattern:
                return {"from_club": match.group(1).title(), "to_club": match.group(2).title()}
            elif 'from' in pattern:
                return {"from_club": match.group(2).title(), "to_club": match.group(1).title()}
    
    # Default to unknown clubs if no pattern matches
    return {"from_club": None, "to_club": None}

def infer_league_from_clubs(from_club: str, to_club: str) -> str:
    """
    Infer league from club names using simple heuristics.
    """
    premier_clubs = ["arsenal", "chelsea", "liverpool", "manchester", "tottenham", "city", "united"]
    la_liga_clubs = ["barcelona", "madrid", "atletico", "sevilla", "valencia"]
    serie_a_clubs = ["juventus", "milan", "inter", "napoli", "roma", "lazio"]
    
    clubs_text = f"{from_club or ''} {to_club or ''}".lower()
    
    for club in premier_clubs:
        if club in clubs_text:
            return "Premier League"
    
    for club in la_liga_clubs:
        if club in clubs_text:
            return "La Liga"
    
    for club in serie_a_clubs:
        if club in clubs_text:
            return "Serie A"
    
    return "Unknown"

def fetch_bbc_rss() -> List[Dict]:
    """
    Fetch and parse BBC Sport Football RSS feed.
    Returns list of normalised rumour data.
    """
    feed_url = os.environ.get('FEEDS_BBC_FOOTBALL', 'https://feeds.bbci.co.uk/sport/football/rss.xml')
    
    try:
        logger.info(f"Fetching BBC RSS from {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            logger.warning(f"RSS feed parse warning: {feed.bozo_exception}")
        
        rumours = []
        
        for entry in feed.entries[:20]:  # Limit to most recent 20 items
            # Extract basic information
            title = entry.get('title', '')
            description = entry.get('description', '') or entry.get('summary', '')
            link = entry.get('link', '')
            pub_date = entry.get('published_parsed')
            
            # Check if this is transfer-related content
            full_text = f"{title} {description}".lower()
            has_transfer_keywords = any(keyword in full_text for keyword in TRANSFER_KEYWORDS)
            
            if not has_transfer_keywords:
                logger.debug(f"Skipping non-transfer article: {title}")
                continue
            
            # Convert publication date
            if pub_date:
                first_seen = datetime(*pub_date[:6])
            else:
                first_seen = datetime.utcnow()
            
            # Extract player name
            player_name = extract_player_from_title(title, description)
            
            # Extract clubs
            clubs = extract_clubs_from_text(f"{title} {description}")
            
            # Skip if no meaningful transfer information
            if not clubs["from_club"] and not clubs["to_club"] and not player_name:
                logger.debug(f"No transfer info found in: {title}")
                continue
            
            # Infer league
            league = infer_league_from_clubs(clubs["from_club"] or "", clubs["to_club"] or "")
            
            rumour_data = {
                "player_name": player_name,
                "from_club": clubs["from_club"] or "Unknown",
                "to_club": clubs["to_club"] or "Unknown", 
                "league": league,
                "position": None,  # Cannot reliably extract from RSS
                "reported_fee": None,  # Would need more sophisticated extraction
                "wage_estimate": None,
                "contract_years_left": None,
                "source_name": "BBC Sport",
                "source_url": link,
                "source_type": "outlet",
                "source_claim": f"{title}. {description}",
                "first_seen_date": first_seen,
                "last_seen_date": first_seen,
                "sightings_count": 1,
                "distinct_sources_7d": 1
            }
            
            rumours.append(rumour_data)
            logger.debug(f"Parsed rumour: {player_name or 'Unknown player'} -> {clubs['to_club']}")
        
        logger.info(f"Successfully parsed {len(rumours)} rumours from BBC RSS")
        return rumours
        
    except Exception as e:
        logger.error(f"Error fetching BBC RSS: {str(e)}")
        return []