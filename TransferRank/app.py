import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///transferrank.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Add custom template filters
import json
from datetime import datetime

@app.template_filter('from_json')
def from_json(value):
    """Convert JSON string to Python object"""
    if not value:
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}

@app.template_filter('avg')
def avg_filter(values):
    """Calculate average of a list of numbers."""
    if not values:
        return 0
    valid_values = [v for v in values if v is not None]
    return sum(valid_values) / len(valid_values) if valid_values else 0

@app.template_global()
def moment():
    """Get current datetime for templates"""
    class MomentProxy:
        def format(self, fmt):
            return datetime.utcnow().strftime(fmt.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d').replace('HH', '%H').replace('mm', '%M').replace('ss', '%S'))
    return MomentProxy()

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Import routes
    from routes import *
    
    # Seed data if database is empty
    from seed_data import seed_database_if_empty
    seed_database_if_empty()
