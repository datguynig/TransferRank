import json
from datetime import datetime, timedelta
from app import db
from models import Player, Source, Rumour, Score, Settings, ClubNeeds
from scoring import calculate_rumour_scores

def seed_database_if_empty():
    """Seed the database with realistic transfer rumour data if it's empty"""
    if Player.query.count() > 0:
        return  # Database already has data
    
    print("Seeding database with initial data...")
    
    # Create settings with default weights
    default_weights = {
        'credibility': 0.4,
        'fit': 0.3,
        'value': 0.2,
        'momentum': 0.1
    }
    settings = Settings()
    settings.weights_json = json.dumps(default_weights)
    db.session.add(settings)
    
    # Create club needs data
    club_needs_data = [
        {
            'club_name': 'Manchester United',
            'position_needs': ['CB', 'DM', 'ST'],
            'style_tags': ['attacking', 'pace']
        },
        {
            'club_name': 'Arsenal',
            'position_needs': ['DM', 'ST'],
            'style_tags': ['technical', 'attacking']
        },
        {
            'club_name': 'Chelsea',
            'position_needs': ['CB', 'LB', 'ST'],
            'style_tags': ['defensive', 'physical']
        },
        {
            'club_name': 'Liverpool',
            'position_needs': ['CB', 'DM'],
            'style_tags': ['pressing', 'pace']
        },
        {
            'club_name': 'Manchester City',
            'position_needs': ['LB', 'DM'],
            'style_tags': ['technical', 'possession']
        },
        {
            'club_name': 'Real Madrid',
            'position_needs': ['CB', 'DM', 'RW'],
            'style_tags': ['technical', 'experience']
        },
        {
            'club_name': 'Barcelona',
            'position_needs': ['CB', 'RB', 'DM'],
            'style_tags': ['technical', 'possession']
        },
        {
            'club_name': 'Bayern Munich',
            'position_needs': ['CB', 'RB', 'CM'],
            'style_tags': ['physical', 'pressing']
        },
        {
            'club_name': 'Paris Saint-Germain',
            'position_needs': ['CB', 'DM', 'RW'],
            'style_tags': ['pace', 'attacking']
        },
        {
            'club_name': 'Juventus',
            'position_needs': ['CB', 'CM', 'LW'],
            'style_tags': ['defensive', 'experience']
        }
    ]
    
    for club_data in club_needs_data:
        club_needs = ClubNeeds()
        club_needs.club_name = club_data['club_name']
        club_needs.position_needs = json.dumps(club_data['position_needs'])
        club_needs.style_tags = json.dumps(club_data['style_tags'])
        db.session.add(club_needs)
    
    # Create realistic sources based on actual football journalists
    sources_data = [
        {'name': 'David Ornstein', 'type': 'journalist', 'reputation_tag': 'trusted', 'url': 'https://theathletic.com', 'avg_credibility': 92.0, 'hit_rate': 0.89},
        {'name': 'Fabrizio Romano', 'type': 'journalist', 'reputation_tag': 'trusted', 'url': 'https://twitter.com/FabrizioRomano', 'avg_credibility': 88.0, 'hit_rate': 0.85},
        {'name': 'Paul Joyce', 'type': 'journalist', 'reputation_tag': 'trusted', 'url': 'https://thetimes.co.uk', 'avg_credibility': 85.0, 'hit_rate': 0.82},
        {'name': 'James Ducker', 'type': 'journalist', 'reputation_tag': 'trusted', 'url': 'https://telegraph.co.uk', 'avg_credibility': 83.0, 'hit_rate': 0.80},
        {'name': 'Simon Stone', 'type': 'journalist', 'reputation_tag': 'trusted', 'url': 'https://bbc.co.uk/sport', 'avg_credibility': 87.0, 'hit_rate': 0.84},
        {'name': 'Gianluca Di Marzio', 'type': 'journalist', 'reputation_tag': 'neutral', 'url': 'https://gianlucadimarzio.com', 'avg_credibility': 75.0, 'hit_rate': 0.72},
        {'name': 'Sky Sports News', 'type': 'outlet', 'reputation_tag': 'neutral', 'url': 'https://skysports.com', 'avg_credibility': 68.0, 'hit_rate': 0.65},
        {'name': 'ESPN FC', 'type': 'outlet', 'reputation_tag': 'neutral', 'url': 'https://espn.com', 'avg_credibility': 65.0, 'hit_rate': 0.62},
        {'name': 'The Sun', 'type': 'outlet', 'reputation_tag': 'unreliable', 'url': 'https://thesun.co.uk', 'avg_credibility': 35.0, 'hit_rate': 0.28},
        {'name': 'Mirror Football', 'type': 'outlet', 'reputation_tag': 'unreliable', 'url': 'https://mirror.co.uk', 'avg_credibility': 38.0, 'hit_rate': 0.31},
        {'name': 'Transfer Aggregator', 'type': 'aggregator', 'reputation_tag': 'unreliable', 'url': 'https://example.com', 'avg_credibility': 25.0, 'hit_rate': 0.15},
        {'name': 'Manchester United Official', 'type': 'club', 'reputation_tag': 'trusted', 'url': 'https://manutd.com', 'avg_credibility': 98.0, 'hit_rate': 0.95},
        {'name': 'Real Madrid Official', 'type': 'club', 'reputation_tag': 'trusted', 'url': 'https://realmadrid.com', 'avg_credibility': 98.0, 'hit_rate': 0.95},
        {'name': 'Barcelona Official', 'type': 'club', 'reputation_tag': 'trusted', 'url': 'https://fcbarcelona.com', 'avg_credibility': 98.0, 'hit_rate': 0.95}
    ]
    
    sources = []
    for source_data in sources_data:
        source = Source()
        source.name = source_data['name']
        source.type = source_data['type']
        source.reputation_tag = source_data['reputation_tag']
        source.url = source_data['url']
        source.avg_credibility = source_data['avg_credibility']
        source.hit_rate = source_data['hit_rate']
        sources.append(source)
        db.session.add(source)
    
    db.session.flush()  # Get IDs for sources
    
    # Create realistic players
    players_data = [
        {'name': 'Kylian Mbappé', 'position': 'LW', 'age': 26, 'current_club': 'Paris Saint-Germain', 'nationality': 'France'},
        {'name': 'Erling Haaland', 'position': 'ST', 'age': 23, 'current_club': 'Manchester City', 'nationality': 'Norway'},
        {'name': 'Jude Bellingham', 'position': 'CM', 'age': 21, 'current_club': 'Real Madrid', 'nationality': 'England'},
        {'name': 'Pedri González', 'position': 'AM', 'age': 22, 'current_club': 'Barcelona', 'nationality': 'Spain'},
        {'name': 'Vinícius Júnior', 'position': 'LW', 'age': 24, 'current_club': 'Real Madrid', 'nationality': 'Brazil'},
        {'name': 'João Félix', 'position': 'AM', 'age': 24, 'current_club': 'Atlético Madrid', 'nationality': 'Portugal'},
        {'name': 'Mason Mount', 'position': 'AM', 'age': 26, 'current_club': 'Chelsea', 'nationality': 'England'},
        {'name': 'Declan Rice', 'position': 'DM', 'age': 25, 'current_club': 'West Ham United', 'nationality': 'England'},
        {'name': 'Victor Osimhen', 'position': 'ST', 'age': 25, 'current_club': 'Napoli', 'nationality': 'Nigeria'},
        {'name': 'Gavi', 'position': 'CM', 'age': 19, 'current_club': 'Barcelona', 'nationality': 'Spain'},
        {'name': 'Rafael Leão', 'position': 'LW', 'age': 24, 'current_club': 'AC Milan', 'nationality': 'Portugal'},
        {'name': 'Enzo Fernández', 'position': 'CM', 'age': 23, 'current_club': 'Chelsea', 'nationality': 'Argentina'},
        {'name': 'Khvicha Kvaratskhelia', 'position': 'LW', 'age': 23, 'current_club': 'Napoli', 'nationality': 'Georgia'},
        {'name': 'Bukayo Saka', 'position': 'RW', 'age': 22, 'current_club': 'Arsenal', 'nationality': 'England'},
        {'name': 'Martin Ødegaard', 'position': 'AM', 'age': 25, 'current_club': 'Arsenal', 'nationality': 'Norway'},
        {'name': 'Bruno Fernandes', 'position': 'AM', 'age': 30, 'current_club': 'Manchester United', 'nationality': 'Portugal'},
        {'name': 'Virgil van Dijk', 'position': 'CB', 'age': 32, 'current_club': 'Liverpool', 'nationality': 'Netherlands'},
        {'name': 'Rúben Dias', 'position': 'CB', 'age': 27, 'current_club': 'Manchester City', 'nationality': 'Portugal'},
        {'name': 'Alessandro Bastoni', 'position': 'CB', 'age': 24, 'current_club': 'Inter Milan', 'nationality': 'Italy'},
        {'name': 'Aurélien Tchouaméni', 'position': 'DM', 'age': 24, 'current_club': 'Real Madrid', 'nationality': 'France'},
        {'name': 'Jamal Musiala', 'position': 'AM', 'age': 21, 'current_club': 'Bayern Munich', 'nationality': 'Germany'},
        {'name': 'Florian Wirtz', 'position': 'AM', 'age': 21, 'current_club': 'Bayer Leverkusen', 'nationality': 'Germany'},
        {'name': 'Youssoufa Moukoko', 'position': 'ST', 'age': 19, 'current_club': 'Borussia Dortmund', 'nationality': 'Germany'},
        {'name': 'Eduardo Camavinga', 'position': 'CM', 'age': 22, 'current_club': 'Real Madrid', 'nationality': 'France'},
        {'name': 'Dusan Vlahovic', 'position': 'ST', 'age': 24, 'current_club': 'Juventus', 'nationality': 'Serbia'},
        {'name': 'Christopher Nkunku', 'position': 'AM', 'age': 27, 'current_club': 'Chelsea', 'nationality': 'France'},
        {'name': 'Nicolo Barella', 'position': 'CM', 'age': 27, 'current_club': 'Inter Milan', 'nationality': 'Italy'},
        {'name': 'Federico Chiesa', 'position': 'RW', 'age': 27, 'current_club': 'Juventus', 'nationality': 'Italy'},
        {'name': 'Gianluigi Donnarumma', 'position': 'GK', 'age': 25, 'current_club': 'Paris Saint-Germain', 'nationality': 'Italy'},
        {'name': 'Thibaut Courtois', 'position': 'GK', 'age': 32, 'current_club': 'Real Madrid', 'nationality': 'Belgium'}
    ]
    
    players = []
    for player_data in players_data:
        player = Player()
        player.name = player_data['name']
        player.position = player_data['position']
        player.age = player_data['age']
        player.current_club = player_data['current_club']
        player.nationality = player_data['nationality']
        players.append(player)
        db.session.add(player)
    
    db.session.flush()  # Get IDs for players
    
    # Create realistic transfer rumours
    rumours_data = [
        {
            'player': 'Kylian Mbappé', 'from_club': 'Paris Saint-Germain', 'to_club': 'Real Madrid',
            'league': 'La Liga', 'reported_fee': 180.0, 'wage_estimate': 800.0, 'contract_years_left': 0.5,
            'source': 'Fabrizio Romano', 'claim': 'Real Madrid confident of signing Mbappé as free agent next summer',
            'source_url': 'https://twitter.com/FabrizioRomano/status/example1',
            'article_links': ['https://theathletic.com/mbappe-real-madrid', 'https://marca.com/mbappe-decision']
        },
        {
            'player': 'Jude Bellingham', 'from_club': 'Real Madrid', 'to_club': 'Manchester City',
            'league': 'Premier League', 'reported_fee': 120.0, 'wage_estimate': 300.0, 'contract_years_left': 4.5,
            'source': 'The Sun', 'claim': 'City plotting shock move for Bellingham',
            'source_url': 'https://thesun.co.uk/sport/example2',
            'article_links': ['https://manchestereveningnews.co.uk/bellingham-city']
        },
        {
            'player': 'Victor Osimhen', 'from_club': 'Napoli', 'to_club': 'Manchester United',
            'league': 'Premier League', 'reported_fee': 100.0, 'wage_estimate': 250.0, 'contract_years_left': 2.0,
            'source': 'David Ornstein', 'claim': 'United monitoring Osimhen situation at Napoli',
            'source_url': 'https://theathletic.com/osimhen-united',
            'article_links': ['https://manutd.com/news/osimhen-links', 'https://skysports.com/osimhen-united']
        },
        {
            'player': 'Declan Rice', 'from_club': 'West Ham United', 'to_club': 'Arsenal',
            'league': 'Premier League', 'reported_fee': 90.0, 'wage_estimate': 200.0, 'contract_years_left': 1.0,
            'source': 'Paul Joyce', 'claim': 'Arsenal prepare £90m bid for Rice',
            'source_url': 'https://thetimes.co.uk/rice-arsenal',
            'article_links': ['https://arsenal.com/news/rice-transfer', 'https://bbc.com/sport/rice-arsenal']
        },
        {
            'player': 'João Félix', 'from_club': 'Atlético Madrid', 'to_club': 'Chelsea',
            'league': 'Premier League', 'reported_fee': 80.0, 'wage_estimate': 180.0, 'contract_years_left': 3.0,
            'source': 'Gianluca Di Marzio', 'claim': 'Chelsea in advanced talks for João Félix',
            'source_url': 'https://gianlucadimarzio.com/felix-chelsea',
            'article_links': ['https://chelseafc.com/news/felix-talks']
        },
        {
            'player': 'Mason Mount', 'from_club': 'Chelsea', 'to_club': 'Liverpool',
            'league': 'Premier League', 'reported_fee': 60.0, 'wage_estimate': 150.0, 'contract_years_left': 1.0,
            'source': 'James Ducker', 'claim': 'Liverpool interested in Mount as contract talks stall',
            'source_url': 'https://telegraph.co.uk/mount-liverpool',
            'article_links': ['https://liverpoolfc.com/news/mount-interest']
        },
        {
            'player': 'Rafael Leão', 'from_club': 'AC Milan', 'to_club': 'Paris Saint-Germain',
            'league': 'Ligue 1', 'reported_fee': 85.0, 'wage_estimate': 220.0, 'contract_years_left': 2.5,
            'source': 'Sky Sports News', 'claim': 'PSG weighing up move for Milan winger Leão',
            'source_url': 'https://skysports.com/leao-psg',
            'article_links': ['https://psg.fr/news/leao-transfer']
        },
        {
            'player': 'Bukayo Saka', 'from_club': 'Arsenal', 'to_club': 'Manchester City',
            'league': 'Premier League', 'reported_fee': 120.0, 'wage_estimate': 280.0, 'contract_years_left': 3.0,
            'source': 'Mirror Football', 'claim': 'City ready to break bank for Saka',
            'source_url': 'https://mirror.co.uk/saka-city',
            'article_links': ['https://mcfc.com/news/saka-links']
        },
        {
            'player': 'Khvicha Kvaratskhelia', 'from_club': 'Napoli', 'to_club': 'Barcelona',
            'league': 'La Liga', 'reported_fee': 75.0, 'wage_estimate': 160.0, 'contract_years_left': 3.5,
            'source': 'ESPN FC', 'claim': 'Barcelona tracking Napoli star Kvaratskhelia',
            'source_url': 'https://espn.com/kvaratskhelia-barca',
            'article_links': ['https://fcbarcelona.com/news/kvara-interest']
        },
        {
            'player': 'Enzo Fernández', 'from_club': 'Chelsea', 'to_club': 'Real Madrid',
            'league': 'La Liga', 'reported_fee': 110.0, 'wage_estimate': 240.0, 'contract_years_left': 6.0,
            'source': 'Transfer Aggregator', 'claim': 'Madrid plotting summer move for Enzo',
            'source_url': 'https://example.com/enzo-madrid',
            'article_links': []
        },
        {
            'player': 'Alessandro Bastoni', 'from_club': 'Inter Milan', 'to_club': 'Manchester United',
            'league': 'Premier League', 'reported_fee': 70.0, 'wage_estimate': 140.0, 'contract_years_left': 2.0,
            'source': 'Simon Stone', 'claim': 'United consider Bastoni as defensive reinforcement',
            'source_url': 'https://bbc.com/sport/bastoni-united',
            'article_links': ['https://manutd.com/news/bastoni-target']
        },
        {
            'player': 'Jamal Musiala', 'from_club': 'Bayern Munich', 'to_club': 'Liverpool',
            'league': 'Premier League', 'reported_fee': 90.0, 'wage_estimate': 200.0, 'contract_years_left': 2.5,
            'source': 'David Ornstein', 'claim': 'Liverpool monitoring Musiala contract situation',
            'source_url': 'https://theathletic.com/musiala-liverpool',
            'article_links': ['https://liverpoolfc.com/news/musiala-watch']
        },
        {
            'player': 'Florian Wirtz', 'from_club': 'Bayer Leverkusen', 'to_club': 'Bayern Munich',
            'league': 'Bundesliga', 'reported_fee': 85.0, 'wage_estimate': 180.0, 'contract_years_left': 2.0,
            'source': 'Fabrizio Romano', 'claim': 'Bayern prioritize Wirtz for summer window',
            'source_url': 'https://twitter.com/FabrizioRomano/status/example3',
            'article_links': ['https://fcbayern.com/news/wirtz-target']
        },
        {
            'player': 'Dusan Vlahovic', 'from_club': 'Juventus', 'to_club': 'Arsenal',
            'league': 'Premier League', 'reported_fee': 95.0, 'wage_estimate': 220.0, 'contract_years_left': 3.0,
            'source': 'Paul Joyce', 'claim': 'Arsenal revive interest in Juventus striker',
            'source_url': 'https://thetimes.co.uk/vlahovic-arsenal',
            'article_links': ['https://arsenal.com/news/vlahovic-links']
        },
        {
            'player': 'Christopher Nkunku', 'from_club': 'Chelsea', 'to_club': 'Paris Saint-Germain',
            'league': 'Ligue 1', 'reported_fee': 70.0, 'wage_estimate': 150.0, 'contract_years_left': 4.0,
            'source': 'Gianluca Di Marzio', 'claim': 'PSG consider bringing Nkunku back to France',
            'source_url': 'https://gianlucadimarzio.com/nkunku-psg',
            'article_links': ['https://psg.fr/news/nkunku-return']
        },
        {
            'player': 'Federico Chiesa', 'from_club': 'Juventus', 'to_club': 'Manchester United',
            'league': 'Premier League', 'reported_fee': 60.0, 'wage_estimate': 130.0, 'contract_years_left': 1.5,
            'source': 'James Ducker', 'claim': 'United eye Chiesa as wing reinforcement',
            'source_url': 'https://telegraph.co.uk/chiesa-united',
            'article_links': ['https://manutd.com/news/chiesa-interest']
        },
        {
            'player': 'Nicolo Barella', 'from_club': 'Inter Milan', 'to_club': 'Liverpool',
            'league': 'Premier League', 'reported_fee': 80.0, 'wage_estimate': 170.0, 'contract_years_left': 2.5,
            'source': 'Sky Sports News', 'claim': 'Liverpool scout Barella for midfield rebuild',
            'source_url': 'https://skysports.com/barella-liverpool',
            'article_links': ['https://liverpoolfc.com/news/barella-target']
        },
        {
            'player': 'Gavi', 'from_club': 'Barcelona', 'to_club': 'Manchester City',
            'league': 'Premier League', 'reported_fee': 100.0, 'wage_estimate': 180.0, 'contract_years_left': 5.0,
            'source': 'The Sun', 'claim': 'City ready to trigger Gavi release clause',
            'source_url': 'https://thesun.co.uk/sport/gavi-city',
            'article_links': []
        },
        {
            'player': 'Youssoufa Moukoko', 'from_club': 'Borussia Dortmund', 'to_club': 'Chelsea',
            'league': 'Premier League', 'reported_fee': 40.0, 'wage_estimate': 100.0, 'contract_years_left': 0.5,
            'source': 'ESPN FC', 'claim': 'Chelsea target Moukoko as contract expires',
            'source_url': 'https://espn.com/moukoko-chelsea',
            'article_links': ['https://chelseafc.com/news/moukoko-talks']
        },
        {
            'player': 'Eduardo Camavinga', 'from_club': 'Real Madrid', 'to_club': 'Liverpool',
            'league': 'Premier League', 'reported_fee': 75.0, 'wage_estimate': 160.0, 'contract_years_left': 4.0,
            'source': 'Mirror Football', 'claim': 'Liverpool plot raid for Madrid midfielder',
            'source_url': 'https://mirror.co.uk/camavinga-liverpool',
            'article_links': ['https://liverpoolfc.com/news/camavinga-links']
        }
    ]
    
    # Create rumours with realistic variation in dates
    base_date = datetime.utcnow() - timedelta(days=30)
    for i, rumour_data in enumerate(rumours_data):
        # Find player and source
        player = next(p for p in players if p.name == rumour_data['player'])
        source = next(s for s in sources if s.name == rumour_data['source'])
        
        # Vary the first seen date
        first_seen = base_date + timedelta(days=i)
        last_seen = first_seen + timedelta(days=min(i % 7, 5))
        
        # Vary sightings and sources
        sightings = max(1, min(i % 10 + 1, 8))
        distinct_sources = max(1, min(i % 5 + 1, 4))
        
        rumour = Rumour()
        rumour.player_id = player.id
        rumour.from_club = rumour_data['from_club']
        rumour.to_club = rumour_data['to_club']
        rumour.league = rumour_data['league']
        rumour.position = player.position
        rumour.reported_fee = rumour_data.get('reported_fee')
        rumour.wage_estimate = rumour_data.get('wage_estimate')
        rumour.contract_years_left = rumour_data.get('contract_years_left')
        rumour.source_id = source.id
        rumour.source_claim = rumour_data['claim']
        rumour.source_url = rumour_data['source_url']
        rumour.article_links = json.dumps(rumour_data.get('article_links', []))
        rumour.first_seen_date = first_seen
        rumour.last_seen_date = last_seen
        rumour.sightings_count = sightings
        rumour.distinct_sources_7d = distinct_sources
        db.session.add(rumour)
        db.session.flush()
        
        # Calculate and save scores
        scores_data = calculate_rumour_scores(rumour)
        score = Score()
        score.rumour_id = rumour.id
        score.credibility = scores_data['credibility']
        score.fit = scores_data['fit']
        score.value = scores_data['value']
        score.momentum = scores_data['momentum']
        score.overall = scores_data['overall']
        score.weights_json = json.dumps(scores_data['weights'])
        db.session.add(score)
    
    db.session.commit()
    print("Database seeded successfully!")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_database_if_empty()
