import os
import csv
import json
import jwt
import logging
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
from io import StringIO
from app import app, db
from models import Player, Source, Rumour, Score, Settings, ClubNeeds, UserRating
from forms import RumourForm, CSVUploadForm, AdminForm, WeightsForm, SourceReputationForm, UserRatingForm
from scoring import calculate_rumour_scores

# Import news ingestion services
from services.ingest.bbc_rss import fetch_bbc_rss
from services.ingest.guardian import fetch_guardian_transfers
from services.ingest.dedupe import deduplicate_rumours
from services.images.wikimedia import get_player_image, get_publisher_image

# Configure logging
logger = logging.getLogger(__name__)

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Landing page with latest transfer news and quick access to leaderboard"""
    # Get latest 6 rumours for news section
    latest_rumours = Rumour.query.order_by(Rumour.created_at.desc()).limit(6).all()
    
    # Check if live sources are active
    live_sources_active = has_recent_ingest(24)
    
    return render_template('landing.html', 
                         latest_rumours=latest_rumours,
                         live_sources_active=live_sources_active,
                         page_title="TransferRank - Football Transfer Rumour Analysis")

@app.route('/leaderboard')
def leaderboard():
    """Main leaderboard page"""
    # Get filter parameters
    search = request.args.get('search', '')
    league = request.args.get('league', '')
    position = request.args.get('position', '')
    source_type = request.args.get('source_type', '')
    min_fee = request.args.get('min_fee', type=float)
    max_fee = request.args.get('max_fee', type=float)
    sort_by = request.args.get('sort_by', 'overall')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = db.session.query(Rumour).join(Player).join(Source).join(Score)
    
    # Apply filters
    if search:
        query = query.filter(
            (Player.name.contains(search)) |
            (Rumour.from_club.contains(search)) |
            (Rumour.to_club.contains(search))
        )
    
    if league:
        query = query.filter(Rumour.league == league)
    
    if position:
        query = query.filter(Rumour.position == position)
    
    if source_type:
        query = query.filter(Source.type == source_type)
    
    if min_fee is not None:
        query = query.filter(Rumour.reported_fee >= min_fee)
    
    if max_fee is not None:
        query = query.filter(Rumour.reported_fee <= max_fee)
    
    # Check if live sources are active
    live_sources_active = has_recent_ingest(24)
    
    # Apply sorting
    if sort_by == 'overall':
        sort_column = Score.overall
    elif sort_by == 'credibility':
        sort_column = Score.credibility
    elif sort_by == 'fit':
        sort_column = Score.fit
    elif sort_by == 'value':
        sort_column = Score.value
    elif sort_by == 'momentum':
        sort_column = Score.momentum
    elif sort_by == 'fee':
        sort_column = Rumour.reported_fee
    elif sort_by == 'date':
        sort_column = Rumour.first_seen_date
    else:
        sort_column = Score.overall
    
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Paginate
    rumours = query.paginate(page=page, per_page=20, error_out=False, max_per_page=100)
    
    # Get unique values for filters
    leagues = db.session.query(Rumour.league).distinct().all()
    positions = db.session.query(Rumour.position).distinct().all()
    source_types = db.session.query(Source.type).distinct().all()
    
    return render_template('leaderboard.html', 
                         rumours=rumours,
                         leagues=[l[0] for l in leagues],
                         positions=[p[0] for p in positions],
                         source_types=[s[0] for s in source_types],
                         current_filters={
                             'search': search,
                             'league': league,
                             'position': position,
                             'source_type': source_type,
                             'min_fee': min_fee,
                             'max_fee': max_fee,
                             'sort_by': sort_by,
                             'order': order
                         })

@app.route('/rumour/<int:id>')
def rumour_detail(id):
    """Rumour detail page with score breakdown"""
    rumour = Rumour.query.get_or_404(id)
    latest_score = Score.query.filter_by(rumour_id=id).order_by(Score.calculated_at.desc()).first()
    
    return render_template('rumour_detail.html', 
                         rumour=rumour, 
                         score=latest_score)

@app.route('/player/<int:id>')
def player_detail(id):
    """Player detail page with all rumours"""
    player = Player.query.get_or_404(id)
    rumours = Rumour.query.filter_by(player_id=id).join(Score).order_by(Score.overall.desc()).all()
    
    return render_template('player_detail.html', 
                         player=player, 
                         rumours=rumours)

@app.route('/sources')
def source_rankings():
    """Source rankings page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query sources with their rumour counts and average scores
    sources_query = db.session.query(
        Source,
        db.func.count(Rumour.id).label('rumour_count'),
        db.func.avg(Score.overall).label('avg_score'),
        db.func.avg(Score.credibility).label('avg_credibility')
    ).outerjoin(Rumour).outerjoin(Score).group_by(Source.id)
    
    # Order by reputation and then by average score
    sources_query = sources_query.order_by(
        Source.reputation_tag.desc(),
        db.func.avg(Score.overall).desc()
    )
    
    sources = sources_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('source_rankings.html', 
                         sources=sources,
                         page_title="Source Rankings - TransferRank")

@app.route('/contributors')
def contributor_rankings():
    """User contributor rankings page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query contributors based on rumour submissions
    # Since we don't have a user system, we'll group by source names as contributors
    contributors_query = db.session.query(
        Source.name,
        Source.type,
        db.func.count(Rumour.id).label('rumours_added'),
        db.func.avg(Score.overall).label('avg_quality'),
        db.func.max(Rumour.created_at).label('last_contribution')
    ).join(Rumour).join(Score).group_by(Source.name, Source.type)
    
    # Order by number of contributions and then by quality
    contributors_query = contributors_query.order_by(
        db.func.count(Rumour.id).desc(),
        db.func.avg(Score.overall).desc()
    )
    
    contributors = contributors_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('contributor_rankings.html', 
                         contributors=contributors,
                         page_title="Contributor Rankings - TransferRank")

@app.route('/source/<int:id>')
def source_detail(id):
    """Source detail page with reputation and history"""
    source = Source.query.get_or_404(id)
    rumours = Rumour.query.filter_by(source_id=id).join(Score).order_by(Rumour.first_seen_date.desc()).all()
    
    # Calculate recent performance metrics
    recent_rumours = Rumour.query.filter_by(source_id=id).filter(
        Rumour.first_seen_date >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    return render_template('source_detail.html', 
                         source=source, 
                         rumours=rumours,
                         recent_rumours=recent_rumours)

@app.route('/add_rumour', methods=['GET', 'POST'])
def add_rumour():
    """Add a new rumour manually"""
    form = RumourForm()
    
    if form.validate_on_submit():
        # Find or create player
        player = Player.query.filter_by(
            name=form.player_name.data,
            current_club=form.current_club.data
        ).first()
        
        if not player:
            player = Player()
            player.name = form.player_name.data
            player.position = form.position.data
            player.age = form.age.data
            player.current_club = form.current_club.data
            player.nationality = form.nationality.data
            db.session.add(player)
            db.session.flush()
        
        # Find or create source
        source = Source.query.filter_by(name=form.source_name.data).first()
        if not source:
            source = Source()
            source.name = form.source_name.data
            source.type = form.source_type.data
            source.url = form.source_url.data or ''
            source.reputation_tag = 'neutral'
            db.session.add(source)
            db.session.flush()
        
        # Process article links
        article_links = []
        if form.article_links.data:
            links = [link.strip() for link in form.article_links.data.split('\n') if link.strip()]
            article_links = links
        
        # Create rumour
        rumour = Rumour()
        rumour.player_id = player.id
        rumour.from_club = form.current_club.data
        rumour.to_club = form.target_club.data
        rumour.league = form.league.data
        rumour.position = form.position.data
        rumour.reported_fee = form.reported_fee.data
        rumour.wage_estimate = form.wage_estimate.data
        rumour.contract_years_left = form.contract_years_left.data
        rumour.source_id = source.id
        rumour.source_claim = form.source_claim.data
        rumour.source_url = form.source_url.data
        rumour.article_links = json.dumps(article_links) if article_links else None
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
        
        flash('Rumour added successfully!', 'success')
        return redirect(url_for('rumour_detail', id=rumour.id))
    
    return render_template('add_rumour.html', form=form)

@app.route('/upload_csv', methods=['GET', 'POST'])
def upload_csv():
    """Upload CSV file with multiple rumours"""
    form = CSVUploadForm()
    errors = []
    success_count = 0
    
    if form.validate_on_submit():
        try:
            file_content = form.csv_file.data.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(file_content))
            
            required_fields = ['player_name', 'position', 'age_band', 'nationality', 
                             'current_club', 'target_club', 'league', 'source_name', 'source_type']
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Validate required fields
                    missing_fields = [field for field in required_fields if not row.get(field)]
                    if missing_fields:
                        errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                        continue
                    
                    # Find or create player
                    player = Player.query.filter_by(
                        name=row['player_name'],
                        current_club=row['current_club']
                    ).first()
                    
                    if not player:
                        player = Player()
                        player.name = row['player_name']
                        player.position = row['position']
                        player.age = int(row['age'])
                        player.current_club = row['current_club']
                        player.nationality = row['nationality']
                        db.session.add(player)
                        db.session.flush()
                    
                    # Find or create source
                    source = Source.query.filter_by(name=row['source_name']).first()
                    if not source:
                        source = Source()
                        source.name = row['source_name']
                        source.type = row['source_type']
                        source.url = row.get('source_url', '')
                        source.reputation_tag = 'neutral'
                        db.session.add(source)
                        db.session.flush()
                    
                    # Create rumour
                    rumour = Rumour()
                    rumour.player_id = player.id
                    rumour.from_club = row['current_club']
                    rumour.to_club = row['target_club']
                    rumour.league = row['league']
                    rumour.position = row['position']
                    rumour.reported_fee = float(row['reported_fee']) if row.get('reported_fee') else None
                    rumour.wage_estimate = float(row['wage_estimate']) if row.get('wage_estimate') else None
                    rumour.contract_years_left = float(row['contract_years_left']) if row.get('contract_years_left') else None
                    rumour.source_id = source.id
                    rumour.source_claim = row.get('source_claim', '')
                    rumour.source_url = row.get('source_url', '')
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
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            db.session.commit()
            flash(f'Successfully imported {success_count} rumours!', 'success')
            if errors:
                flash(f'{len(errors)} rows had errors.', 'warning')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'error')
    
    return render_template('upload_csv.html', form=form, errors=errors)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Admin panel with authentication"""
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
    
    # Check if already authenticated
    if session.get('admin_authenticated'):
        # Handle weight updates
        weights_form = WeightsForm()
        reputation_form = SourceReputationForm()
        
        if request.method == 'POST':
            if 'update_weights' in request.form and weights_form.validate():
                # Validate weights sum to 1.0
                credibility = weights_form.credibility.data or 0.0
                fit = weights_form.fit.data or 0.0
                value = weights_form.value.data or 0.0
                momentum = weights_form.momentum.data or 0.0
                total_weight = credibility + fit + value + momentum
                
                if abs(total_weight - 1.0) > 0.01:
                    flash('Weights must sum to 1.0', 'error')
                else:
                    weights = {
                        'credibility': weights_form.credibility.data,
                        'fit': weights_form.fit.data,
                        'value': weights_form.value.data,
                        'momentum': weights_form.momentum.data
                    }
                    
                    settings = Settings()
                    settings.weights_json = json.dumps(weights)
                    db.session.add(settings)
                    db.session.commit()
                    flash('Weights updated successfully!', 'success')
            
            elif 'update_reputation' in request.form and reputation_form.validate():
                source = Source.query.get(reputation_form.source_id.data)
                if source:
                    source.reputation_tag = reputation_form.reputation_tag.data
                    db.session.commit()
                    flash(f'Updated reputation for {source.name}', 'success')
            
            elif 'recompute_scores' in request.form:
                # Recompute all scores
                rumours = Rumour.query.all()
                for rumour in rumours:
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
                flash('All scores recomputed successfully!', 'success')
        
        # Load current weights
        current_weights = Settings.get_current_weights()
        weights_form.credibility.data = current_weights['credibility']
        weights_form.fit.data = current_weights['fit']
        weights_form.value.data = current_weights['value']
        weights_form.momentum.data = current_weights['momentum']
        
        # Get all sources for reputation management
        sources = Source.query.all()
        
        return render_template('admin.html', 
                             weights_form=weights_form,
                             reputation_form=reputation_form,
                             sources=sources,
                             using_default_password=(admin_password == 'admin'))
    
    # Authentication required
    auth_form = AdminForm()
    if auth_form.validate_on_submit():
        if auth_form.admin_password.data == admin_password:
            session['admin_authenticated'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid admin password', 'error')
    
    return render_template('admin.html', auth_form=auth_form)

@app.route('/admin/logout')
def admin_logout():
    """Logout from admin panel"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('index'))

@app.route('/api/rate_rumour', methods=['POST'])
def rate_rumour():
    """API endpoint for user ratings"""
    data = request.get_json()
    rumour_id = data.get('rumour_id')
    rating = data.get('rating')
    
    if not rumour_id or not rating or rating not in [1, 2, 3, 4, 5]:
        return jsonify({'error': 'Invalid data'}), 400
    
    rumour = Rumour.query.get(rumour_id)
    if not rumour:
        return jsonify({'error': 'Rumour not found'}), 404
    
    # Use IP address to prevent duplicate ratings
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
    
    # Check if user already rated this rumour
    existing_rating = UserRating.query.filter_by(
        rumour_id=rumour_id,
        ip_address=ip_address
    ).first()
    
    if existing_rating:
        # Update existing rating
        old_rating = existing_rating.rating
        existing_rating.rating = rating
        rumour.total_user_rating = rumour.total_user_rating - old_rating + rating
    else:
        # Create new rating
        user_rating = UserRating()
        user_rating.rumour_id = rumour_id
        user_rating.ip_address = ip_address
        user_rating.rating = rating
        db.session.add(user_rating)
        rumour.total_user_rating += rating
        rumour.user_rating_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'average_rating': rumour.average_user_rating,
        'rating_count': rumour.user_rating_count
    })

@app.route('/api/momentum_data/<int:rumour_id>')
def momentum_data(rumour_id):
    """API endpoint for momentum sparkline data"""
    # Generate sample momentum data for the last 30 days
    # In a real implementation, this would track actual momentum over time
    rumour = Rumour.query.get_or_404(rumour_id)
    latest_score = Score.query.filter_by(rumour_id=rumour_id).order_by(Score.calculated_at.desc()).first()
    
    if not latest_score:
        return jsonify([])
    
    # Generate sample data points (in real app, store historical momentum)
    import random
    base_momentum = latest_score.momentum
    data_points = []
    
    for i in range(30):
        # Add some variation to create a trend
        variation = random.randint(-10, 10)
        momentum_value = max(0, min(100, base_momentum + variation))
        data_points.append({
            'date': (datetime.utcnow() - timedelta(days=29-i)).strftime('%Y-%m-%d'),
            'momentum': momentum_value
        })
    
    return jsonify(data_points)

@app.route('/embed/top10')
def embed_top10():
    """Embeddable widget showing top 10 rumours"""
    top_rumours = db.session.query(Rumour).join(Score).order_by(Score.overall.desc()).limit(10).all()
    return render_template('embed_top10.html', rumours=top_rumours)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route("/upload_image/<string:model_type>/<int:model_id>", methods=["GET", "POST"])
def upload_image(model_type, model_id):
    """Upload image for player or source"""
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)
        
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Get the model instance
            if model_type == "player":
                model_instance = Player.query.get_or_404(model_id)
                folder = "players"
            elif model_type == "source":
                model_instance = Source.query.get_or_404(model_id)
                folder = "sources"
            else:
                flash("Invalid model type", "error")
                return redirect(url_for("leaderboard"))
            
            # Create filename
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{model_type}_{model_id}_{timestamp}_{filename}"
            
            # Ensure upload directory exists
            upload_path = os.path.join("static/images", folder)
            os.makedirs(upload_path, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            # Update database
            image_url = f"/static/images/{folder}/{filename}"
            if model_type == "player":
                model_instance.image_url = image_url
                model_instance.image_filename = filename
            elif model_type == "source":
                model_instance.logo_url = image_url
                model_instance.logo_filename = filename
            
            db.session.commit()
            flash(f"Image uploaded successfully for {model_instance.name}", "success")
            return redirect(url_for("leaderboard"))
        else:
            flash("Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP files.", "error")
    
    # GET request - show upload form
    if model_type == "player":
        model_instance = Player.query.get_or_404(model_id)
    elif model_type == "source":
        model_instance = Source.query.get_or_404(model_id)
    else:
        flash("Invalid model type", "error")
        return redirect(url_for("leaderboard"))
    
    return render_template("upload_image.html", 
                         model_instance=model_instance,
                         model_type=model_type,
                         page_title=f"Upload Image - {model_instance.name}")

@app.route("/api/media/favicon")
def favicon_proxy():
    """Proxy route to fetch website favicons with CORS handling"""
    url = request.args.get("url")
    if not url:
        return "", 204
    
    try:
        # Try to fetch favicon with short timeout
        response = requests.get(f"{url}/favicon.ico", timeout=3, 
                              headers={"User-Agent": "TransferRank/1.0"})
        if response.status_code == 200:
            return response.content, 200, {"Content-Type": "image/x-icon"}
    except:
        pass
    
    # Return 204 No Content if favicon fetch fails
    return "", 204
import jwt
from functools import wraps

# JWT authentication for admin routes
@app.route("/api/auth/login", methods=["POST"])
def admin_login():
    """Admin login endpoint with JWT"""
    data = request.get_json() or {}
    password = data.get("password", "")
    
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin")
    
    if password == admin_password:
        # Create JWT token
        payload = {
            "admin": True,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        
        auth_secret = os.environ.get("AUTH_SECRET", "devsecret")
        token = jwt.encode(payload, auth_secret, algorithm="HS256")
        
        return jsonify({
            "success": True, 
            "token": token,
            "is_default_password": admin_password == "admin"
        })
    
    return jsonify({"success": False, "error": "Invalid password"}), 401

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                pass
        
        if not token:
            return jsonify({"error": "Token missing"}), 401
        
        try:
            auth_secret = os.environ.get("AUTH_SECRET", "devsecret")
            payload = jwt.decode(token, auth_secret, algorithms=["HS256"])
            
            if not payload.get("admin"):
                return jsonify({"error": "Invalid token"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route("/admin/login")
def admin_login_page():
    """Admin login page"""
    return render_template("admin_login.html", page_title="Admin Login")

@app.route("/pricing")
def pricing():
    """Pricing page"""
    return render_template("pricing.html", page_title="Pricing")

# ===== NEWS INGESTION ROUTES =====

@app.route("/api/ingest/bbc", methods=["POST"])
@require_admin_auth
def ingest_bbc():
    """Manual trigger for BBC RSS ingest"""
    try:
        # Fetch BBC rumours
        bbc_rumours = fetch_bbc_rss()
        
        if not bbc_rumours:
            return jsonify({
                "success": True,
                "added": 0,
                "skipped": 0,
                "note": "No rumours found in BBC RSS"
            })
        
        # Deduplicate
        unique_rumours = deduplicate_rumours(bbc_rumours)
        
        # Create rumours in database
        added_count = 0
        for rumour_data in unique_rumours:
            try:
                added_count += create_rumour_from_data(rumour_data)
            except Exception as e:
                logger.error(f"Error creating rumour: {str(e)}")
                continue
        
        skipped_count = len(bbc_rumours) - added_count
        
        # Update last ingest time
        update_last_ingest_time("bbc")
        
        return jsonify({
            "success": True,
            "added": added_count,
            "skipped": skipped_count,
            "source": "BBC Sport"
        })
        
    except Exception as e:
        logger.error(f"BBC ingest error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/ingest/guardian", methods=["POST"])
@require_admin_auth
def ingest_guardian():
    """Manual trigger for Guardian API ingest"""
    try:
        # Check if API key is available
        if not os.environ.get('GUARDIAN_API_KEY'):
            return jsonify({
                "success": True,
                "added": 0,
                "skipped": 0,
                "note": "Guardian API key not configured"
            })
        
        # Fetch Guardian rumours
        guardian_rumours = fetch_guardian_transfers()
        
        if not guardian_rumours:
            return jsonify({
                "success": True,
                "added": 0,
                "skipped": 0,
                "note": "No rumours found from Guardian API"
            })
        
        # Deduplicate
        unique_rumours = deduplicate_rumours(guardian_rumours)
        
        # Create rumours in database
        added_count = 0
        for rumour_data in unique_rumours:
            try:
                added_count += create_rumour_from_data(rumour_data)
            except Exception as e:
                logger.error(f"Error creating rumour: {str(e)}")
                continue
        
        skipped_count = len(guardian_rumours) - added_count
        
        # Update last ingest time
        update_last_ingest_time("guardian")
        
        return jsonify({
            "success": True,
            "added": added_count,
            "skipped": skipped_count,
            "source": "The Guardian"
        })
        
    except Exception as e:
        logger.error(f"Guardian ingest error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/ingest/run-all", methods=["POST"])
@require_admin_auth
def ingest_all():
    """Run both BBC and Guardian ingest in sequence"""
    try:
        total_added = 0
        total_skipped = 0
        results = []
        
        # BBC ingest
        try:
            bbc_rumours = fetch_bbc_rss()
            if bbc_rumours:
                unique_bbc = deduplicate_rumours(bbc_rumours)
                bbc_added = sum(create_rumour_from_data(r) for r in unique_bbc)
                total_added += bbc_added
                total_skipped += len(bbc_rumours) - bbc_added
                results.append(f"BBC: {bbc_added} added")
                update_last_ingest_time("bbc")
            else:
                results.append("BBC: No rumours found")
        except Exception as e:
            logger.error(f"BBC ingest failed: {str(e)}")
            results.append(f"BBC: Failed ({str(e)})")
        
        # Guardian ingest
        if os.environ.get('GUARDIAN_API_KEY'):
            try:
                guardian_rumours = fetch_guardian_transfers()
                if guardian_rumours:
                    unique_guardian = deduplicate_rumours(guardian_rumours)
                    guardian_added = sum(create_rumour_from_data(r) for r in unique_guardian)
                    total_added += guardian_added
                    total_skipped += len(guardian_rumours) - guardian_added
                    results.append(f"Guardian: {guardian_added} added")
                    update_last_ingest_time("guardian")
                else:
                    results.append("Guardian: No rumours found")
            except Exception as e:
                logger.error(f"Guardian ingest failed: {str(e)}")
                results.append(f"Guardian: Failed ({str(e)})")
        else:
            results.append("Guardian: API key not configured")
        
        return jsonify({
            "success": True,
            "added": total_added,
            "skipped": total_skipped,
            "details": results
        })
        
    except Exception as e:
        logger.error(f"Full ingest error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== IMAGE API ROUTES =====

@app.route("/api/images/player")
def get_player_image_api():
    """Get player image from Wikimedia with attribution"""
    player_name = request.args.get('name')
    if not player_name:
        return jsonify({"error": "Player name required"}), 400
    
    try:
        image_data = get_player_image(player_name)
        
        if image_data:
            return jsonify({
                "success": True,
                "image": image_data
            })
        else:
            return jsonify({
                "success": False,
                "message": "No image found"
            })
    
    except Exception as e:
        logger.error(f"Error fetching player image: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/images/publisher")
def get_publisher_image_api():
    """Get publisher logo from Wikimedia with attribution"""
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain required"}), 400
    
    try:
        image_data = get_publisher_image(domain)
        
        if image_data:
            return jsonify({
                "success": True,
                "image": image_data
            })
        else:
            return jsonify({
                "success": False,
                "message": "No image found"
            })
    
    except Exception as e:
        logger.error(f"Error fetching publisher image: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== HELPER FUNCTIONS =====

def create_rumour_from_data(rumour_data: dict) -> int:
    """
    Create a rumour from parsed news data.
    Returns 1 if created, 0 if skipped.
    """
    try:
        # Get or create player
        player = None
        if rumour_data.get('player_name'):
            player = Player.query.filter_by(name=rumour_data['player_name']).first()
        
        if not player and rumour_data.get('player_name'):
            # Create new player with minimal data
            player = Player(
                name=rumour_data['player_name'],
                position=rumour_data.get('position') or 'Unknown',
                age=25,  # Default age
                current_club=rumour_data.get('from_club') or 'Unknown',
                nationality='Unknown'
            )
            db.session.add(player)
            db.session.flush()  # Get player ID
        
        if not player:
            logger.warning(f"Cannot create rumour without player: {rumour_data}")
            return 0
        
        # Get or create source
        source = Source.query.filter_by(name=rumour_data['source_name']).first()
        if not source:
            source = Source(
                name=rumour_data['source_name'],
                url=rumour_data.get('source_url', ''),
                type=rumour_data.get('source_type', 'outlet'),
                reputation_tag='neutral'
            )
            db.session.add(source)
            db.session.flush()
        
        # Create rumour
        rumour = Rumour(
            player_id=player.id,
            from_club=rumour_data.get('from_club') or 'Unknown',
            to_club=rumour_data.get('to_club') or 'Unknown',
            league=rumour_data.get('league') or 'Unknown',
            position=rumour_data.get('position') or player.position,
            reported_fee=rumour_data.get('reported_fee'),
            wage_estimate=rumour_data.get('wage_estimate'),
            contract_years_left=rumour_data.get('contract_years_left'),
            source_id=source.id,
            source_claim=rumour_data.get('source_claim', ''),
            source_url=rumour_data.get('source_url', ''),
            first_seen_date=rumour_data.get('first_seen_date', datetime.utcnow()),
            last_seen_date=rumour_data.get('last_seen_date', datetime.utcnow()),
            sightings_count=rumour_data.get('sightings_count', 1),
            distinct_sources_7d=rumour_data.get('distinct_sources_7d', 1)
        )
        
        db.session.add(rumour)
        db.session.flush()
        
        # Calculate scores
        calculate_rumour_scores(rumour)
        
        db.session.commit()
        logger.info(f"Created rumour: {player.name} to {rumour.to_club}")
        return 1
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating rumour from data: {str(e)}")
        raise

def update_last_ingest_time(source_name: str):
    """Update the last ingest time for a source in settings"""
    try:
        setting_key = f"last_ingest_{source_name}"
        setting = Settings.query.filter_by(key=setting_key).first()
        
        if setting:
            setting.value = datetime.utcnow().isoformat()
        else:
            setting = Settings(
                key=setting_key,
                value=datetime.utcnow().isoformat(),
                description=f"Last successful ingest from {source_name}"
            )
            db.session.add(setting)
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error updating last ingest time: {str(e)}")
        db.session.rollback()

def get_last_ingest_time(source_name: str) -> datetime:
    """Get the last ingest time for a source"""
    try:
        setting_key = f"last_ingest_{source_name}"
        setting = Settings.query.filter_by(key=setting_key).first()
        
        if setting and setting.value:
            return datetime.fromisoformat(setting.value)
        
        return datetime.min
        
    except Exception as e:
        logger.error(f"Error getting last ingest time: {str(e)}")
        return datetime.min

def has_recent_ingest(hours: int = 24) -> bool:
    """Check if any source has been ingested in the last N hours"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    bbc_last = get_last_ingest_time("bbc")
    guardian_last = get_last_ingest_time("guardian")
    
    return bbc_last > cutoff or guardian_last > cutoff
