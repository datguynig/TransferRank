import json
import math
from datetime import datetime, timedelta
from models import Settings, ClubNeeds, Source, Rumour

def calculate_credibility_score(source, distinct_sources_7d=1):
    """Calculate credibility score based on source reputation and corroboration"""
    # Base score from reputation tag
    reputation_scores = {
        'trusted': 85,
        'neutral': 50,
        'unreliable': 15
    }
    
    base_score = reputation_scores.get(source.reputation_tag, 50)
    
    # Boost for multiple independent sources (diminishing returns)
    if distinct_sources_7d > 1:
        corroboration_boost = min(20, 5 * math.log(distinct_sources_7d))
        base_score += corroboration_boost
    
    # Factor in source's historical accuracy
    if source.hit_rate > 0:
        accuracy_factor = (source.hit_rate - 0.5) * 20  # Range: -10 to +10
        base_score += accuracy_factor
    
    return max(0, min(100, base_score))

def calculate_fit_score(player_position, from_club, to_club):
    """Calculate how well the player fits the target club's needs"""
    club_needs = ClubNeeds.query.filter_by(club_name=to_club).first()
    
    if not club_needs:
        return 50.0  # Neutral baseline if no data
    
    try:
        needed_positions = json.loads(club_needs.position_needs or "[]")
        style_preferences = json.loads(club_needs.style_tags or "[]")
    except:
        return 50.0
    
    fit_score = 50.0  # Start with baseline
    
    # Position need boost
    if player_position in needed_positions:
        fit_score += 25
    
    # Style match (simplified - would need player style data)
    # For now, add some variance based on position type
    position_style_bonuses = {
        'GK': 0,
        'CB': 10 if 'defensive' in style_preferences else 0,
        'LB': 15 if 'attacking' in style_preferences else 5,
        'RB': 15 if 'attacking' in style_preferences else 5,
        'DM': 10 if 'defensive' in style_preferences else 0,
        'CM': 10,  # Versatile position
        'AM': 15 if 'attacking' in style_preferences else 5,
        'LW': 20 if 'attacking' in style_preferences else 0,
        'RW': 20 if 'attacking' in style_preferences else 0,
        'ST': 25 if 'attacking' in style_preferences else 5
    }
    
    fit_score += position_style_bonuses.get(player_position, 0)
    
    return max(0, min(100, fit_score))

def calculate_value_score(position, age, reported_fee, contract_years_left=None, wage_estimate=None):
    """Calculate value score based on estimated fair value vs reported fee"""
    if not reported_fee:
        return 50.0  # Neutral if no fee reported
    
    # Base fair value estimates by position and age (in millions €)
    def get_position_value(position, age):
        # Value curves by position type - peak values and age curves
        position_configs = {
            'GK': {'peak_age': 30, 'peak_value': 35, 'youth_multiplier': 0.4, 'decline_start': 32},
            'CB': {'peak_age': 28, 'peak_value': 50, 'youth_multiplier': 0.4, 'decline_start': 30},
            'LB': {'peak_age': 27, 'peak_value': 45, 'youth_multiplier': 0.4, 'decline_start': 29},
            'RB': {'peak_age': 27, 'peak_value': 45, 'youth_multiplier': 0.4, 'decline_start': 29},
            'DM': {'peak_age': 28, 'peak_value': 55, 'youth_multiplier': 0.45, 'decline_start': 30},
            'CM': {'peak_age': 27, 'peak_value': 65, 'youth_multiplier': 0.45, 'decline_start': 29},
            'AM': {'peak_age': 26, 'peak_value': 75, 'youth_multiplier': 0.5, 'decline_start': 28},
            'LW': {'peak_age': 26, 'peak_value': 85, 'youth_multiplier': 0.5, 'decline_start': 28},
            'RW': {'peak_age': 26, 'peak_value': 85, 'youth_multiplier': 0.5, 'decline_start': 28},
            'ST': {'peak_age': 27, 'peak_value': 100, 'youth_multiplier': 0.5, 'decline_start': 29}
        }
        
        config = position_configs.get(position, position_configs['CM'])  # Default to CM
        peak_age = config['peak_age']
        peak_value = config['peak_value']
        youth_multiplier = config['youth_multiplier']
        decline_start = config['decline_start']
        
        if age <= 19:
            # Young players - exponential growth curve
            age_factor = youth_multiplier * (1 + (age - 16) * 0.2)
        elif age <= peak_age:
            # Rising to peak - linear growth
            age_factor = youth_multiplier + (1 - youth_multiplier) * ((age - 20) / (peak_age - 20))
        elif age <= decline_start:
            # At peak
            age_factor = 1.0
        elif age <= 35:
            # Decline phase
            decline_years = age - decline_start
            age_factor = 1.0 - (decline_years * 0.15)  # 15% per year decline
        else:
            # Veteran phase
            age_factor = 0.2
        
        return max(5, peak_value * age_factor)
    
    estimated_value = get_position_value(position, age)
    
    # Adjust for contract situation
    if contract_years_left is not None:
        if contract_years_left < 0.5:  # Less than 6 months
            estimated_value *= 0.3  # Significant discount
        elif contract_years_left < 1.0:  # Less than 1 year
            estimated_value *= 0.6
        elif contract_years_left > 3.0:  # Long contract
            estimated_value *= 1.2
    
    # Calculate value score (inverse relationship with overpay)
    value_ratio = estimated_value / reported_fee
    if value_ratio >= 1.5:  # Great value
        return 90
    elif value_ratio >= 1.2:  # Good value
        return 75
    elif value_ratio >= 0.8:  # Fair value
        return 60
    elif value_ratio >= 0.6:  # Slight overpay
        return 40
    elif value_ratio >= 0.4:  # Significant overpay
        return 25
    else:  # Major overpay
        return 10

def calculate_momentum_score(sightings_count, distinct_sources_7d, days_since_first_seen):
    """Calculate momentum based on recent activity"""
    base_momentum = 30.0
    
    # Boost for multiple sightings
    sighting_boost = min(30, sightings_count * 5)
    
    # Boost for multiple sources
    source_boost = min(25, distinct_sources_7d * 8)
    
    # Decay factor based on time since first seen
    if days_since_first_seen > 14:
        time_decay = max(0.3, 1.0 - (days_since_first_seen - 14) * 0.05)
    else:
        time_decay = 1.0
    
    momentum = (base_momentum + sighting_boost + source_boost) * time_decay
    
    return max(0, min(100, momentum))

def calculate_overall_score(credibility, fit, value, momentum, weights=None):
    """Calculate weighted overall score"""
    if not weights:
        weights = Settings.get_current_weights()
    
    overall = (
        credibility * weights['credibility'] +
        fit * weights['fit'] +
        value * weights['value'] +
        momentum * weights['momentum']
    )
    
    return round(overall, 1)

def calculate_rumour_scores(rumour):
    """Calculate all scores for a rumour"""
    # Calculate days since first seen
    days_since = (datetime.utcnow() - rumour.first_seen_date).days
    
    # Calculate individual scores
    credibility = calculate_credibility_score(rumour.source, rumour.distinct_sources_7d)
    fit = calculate_fit_score(rumour.position, rumour.from_club, rumour.to_club)
    value = calculate_value_score(
        rumour.position, 
        rumour.player.age_band, 
        rumour.reported_fee,
        rumour.contract_years_left,
        rumour.wage_estimate
    )
    momentum = calculate_momentum_score(
        rumour.sightings_count,
        rumour.distinct_sources_7d,
        days_since
    )
    
    # Get current weights
    weights = Settings.get_current_weights()
    
    # Calculate overall score
    overall = calculate_overall_score(credibility, fit, value, momentum, weights)
    
    return {
        'credibility': round(credibility, 1),
        'fit': round(fit, 1),
        'value': round(value, 1),
        'momentum': round(momentum, 1),
        'overall': overall,
        'weights': weights
    }
