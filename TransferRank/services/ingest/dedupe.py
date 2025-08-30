"""Deduplication logic for incoming news rumours."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from app import db
from models import Rumour, Source, Player

logger = logging.getLogger(__name__)

def deduplicate_rumours(incoming_rumours: List[Dict]) -> List[Dict]:
    """
    Remove duplicates from incoming rumours based on:
    1. Same source_url already exists
    2. Same (player, to_club) within 48 hours from more credible source
    
    Returns filtered list of unique rumours to create.
    """
    unique_rumours = []
    
    for rumour_data in incoming_rumours:
        source_url = rumour_data.get('source_url')
        player_name = rumour_data.get('player_name')
        to_club = rumour_data.get('to_club')
        source_name = rumour_data.get('source_name')
        first_seen = rumour_data.get('first_seen_date', datetime.utcnow())
        
        # Skip if no essential data
        if not source_url:
            logger.warning("Skipping rumour with no source URL")
            continue
        
        # Check 1: URL already exists
        existing_by_url = Rumour.query.filter_by(source_url=source_url).first()
        if existing_by_url:
            logger.debug(f"Skipping duplicate URL: {source_url}")
            continue
        
        # Check 2: Same player + club within 48 hours
        if player_name and to_club:
            # Find player in database
            player = Player.query.filter_by(name=player_name).first()
            if player:
                # Look for similar rumours in last 48 hours
                cutoff_date = first_seen - timedelta(hours=48)
                
                similar_rumours = db.session.query(Rumour).join(Player).filter(
                    Player.id == player.id,
                    Rumour.to_club == to_club,
                    Rumour.first_seen_date >= cutoff_date
                ).all()
                
                if similar_rumours:
                    # Check source credibility - prefer more trusted sources
                    source_credibility = get_source_credibility(source_name)
                    
                    skip_rumour = False
                    for existing in similar_rumours:
                        existing_credibility = get_source_credibility(existing.source.name)
                        
                        # Skip if existing source is more credible
                        if existing_credibility > source_credibility:
                            logger.debug(f"Skipping {source_name} rumour, {existing.source.name} more credible")
                            skip_rumour = True
                            break
                    
                    if skip_rumour:
                        continue
        
        # If we get here, rumour is unique enough to include
        unique_rumours.append(rumour_data)
        logger.debug(f"Accepted unique rumour: {player_name or 'Unknown'} -> {to_club}")
    
    logger.info(f"Deduplicated {len(incoming_rumours)} -> {len(unique_rumours)} rumours")
    return unique_rumours

def get_source_credibility(source_name: str) -> int:
    """
    Get credibility score for source name.
    Returns 1-5 scale where 5 is most credible.
    """
    # Check if source exists in database
    source = Source.query.filter_by(name=source_name).first()
    if source:
        # Convert reputation tag to numeric score
        reputation_scores = {
            'trusted': 5,
            'neutral': 3,
            'unreliable': 1
        }
        return reputation_scores.get(source.reputation_tag, 3)
    
    # Default credibility for known outlets
    known_credible = {
        'BBC Sport': 5,
        'The Guardian': 4,
        'Sky Sports': 4,
        'ESPN': 3,
        'Goal.com': 2,
        'The Sun': 1,
        'Daily Mail': 1
    }
    
    return known_credible.get(source_name, 3)  # Default neutral