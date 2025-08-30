from datetime import datetime, timedelta
from app import db
import json

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)  # Player's current age
    current_club = db.Column(db.String(50), nullable=False)
    nationality = db.Column(db.String(30), nullable=False)
    image_url = db.Column(db.String(500))  # URL to player image
    image_filename = db.Column(db.String(255))  # Local filename if uploaded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rumours = db.relationship('Rumour', backref='player', lazy=True)

class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200))
    type = db.Column(db.String(30), nullable=False)  # journalist, club, outlet, aggregator
    reputation_tag = db.Column(db.String(20), default='neutral')  # trusted, neutral, unreliable
    avg_credibility = db.Column(db.Float, default=50.0)
    hit_rate = db.Column(db.Float, default=0.0)
    logo_url = db.Column(db.String(500))  # URL to source logo/avatar
    logo_filename = db.Column(db.String(255))  # Local filename if uploaded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rumours = db.relationship('Rumour', backref='source', lazy=True)

class Rumour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    from_club = db.Column(db.String(50), nullable=False)
    to_club = db.Column(db.String(50), nullable=False)
    league = db.Column(db.String(30), nullable=False)
    position = db.Column(db.String(20), nullable=False)
    reported_fee = db.Column(db.Float)  # in millions
    wage_estimate = db.Column(db.Float)  # weekly wage in thousands
    contract_years_left = db.Column(db.Float)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=False)
    source_claim = db.Column(db.Text)
    source_url = db.Column(db.String(500))
    article_links = db.Column(db.Text)  # JSON array of additional article links
    first_seen_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen_date = db.Column(db.DateTime, default=datetime.utcnow)
    sightings_count = db.Column(db.Integer, default=1)
    distinct_sources_7d = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User ratings
    total_user_rating = db.Column(db.Float, default=0.0)
    user_rating_count = db.Column(db.Integer, default=0)
    
    # Relationships
    scores = db.relationship('Score', backref='rumour', lazy=True)
    user_ratings = db.relationship('UserRating', backref='rumour', lazy=True)
    
    @property
    def average_user_rating(self):
        if self.user_rating_count == 0:
            return 0.0
        return self.total_user_rating / self.user_rating_count
    
    @property
    def article_links_list(self):
        if not self.article_links:
            return []
        try:
            return json.loads(self.article_links)
        except:
            return []

class UserRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rumour_id = db.Column(db.Integer, db.ForeignKey('rumour.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 support
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('rumour_id', 'ip_address', name='_rumour_ip_rating'),)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rumour_id = db.Column(db.Integer, db.ForeignKey('rumour.id'), nullable=False)
    credibility = db.Column(db.Float, nullable=False)
    fit = db.Column(db.Float, nullable=False)
    value = db.Column(db.Float, nullable=False)
    momentum = db.Column(db.Float, nullable=False)
    overall = db.Column(db.Float, nullable=False)
    weights_json = db.Column(db.Text, nullable=False)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    weights_json = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def get_current_weights():
        settings = Settings.query.order_by(Settings.updated_at.desc()).first()
        if settings:
            try:
                return json.loads(settings.weights_json)
            except:
                pass
        # Default weights
        return {
            'credibility': 0.4,
            'fit': 0.3,
            'value': 0.2,
            'momentum': 0.1
        }

class ClubNeeds(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_name = db.Column(db.String(50), nullable=False, unique=True)
    position_needs = db.Column(db.Text)  # JSON array of positions needed
    style_tags = db.Column(db.Text)  # JSON array of playing style preferences
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
