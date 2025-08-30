from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange, URL
from wtforms.widgets import TextArea

class RumourForm(FlaskForm):
    player_name = StringField('Player Name', validators=[DataRequired()])
    position = SelectField('Position', choices=[
        ('GK', 'Goalkeeper'),
        ('CB', 'Centre-Back'),
        ('LB', 'Left-Back'),
        ('RB', 'Right-Back'),
        ('DM', 'Defensive Midfielder'),
        ('CM', 'Central Midfielder'),
        ('AM', 'Attacking Midfielder'),
        ('LW', 'Left Winger'),
        ('RW', 'Right Winger'),
        ('ST', 'Striker')
    ], validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=16, max=45, message='Age must be between 16 and 45')])
    nationality = StringField('Nationality', validators=[DataRequired()])
    current_club = StringField('Current Club', validators=[DataRequired()])
    target_club = StringField('Target Club', validators=[DataRequired()])
    league = SelectField('League', choices=[
        ('Premier League', 'Premier League'),
        ('La Liga', 'La Liga'),
        ('Serie A', 'Serie A'),
        ('Bundesliga', 'Bundesliga'),
        ('Ligue 1', 'Ligue 1'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    reported_fee = FloatField('Reported Fee (€M)', validators=[Optional(), NumberRange(min=0)])
    wage_estimate = FloatField('Weekly Wage Estimate (€K)', validators=[Optional(), NumberRange(min=0)])
    contract_years_left = FloatField('Contract Years Left', validators=[Optional(), NumberRange(min=0)])
    source_name = StringField('Source Name', validators=[DataRequired()])
    source_type = SelectField('Source Type', choices=[
        ('journalist', 'Journalist'),
        ('club', 'Official Club'),
        ('outlet', 'News Outlet'),
        ('aggregator', 'Aggregator')
    ], validators=[DataRequired()])
    source_url = StringField('Source URL', validators=[Optional(), URL()])
    source_claim = TextAreaField('Source Claim', widget=TextArea())
    article_links = TextAreaField('Additional Article Links (one per line)', widget=TextArea())

class CSVUploadForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[
        DataRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])

class AdminForm(FlaskForm):
    admin_password = StringField('Admin Password', validators=[DataRequired()])

class WeightsForm(FlaskForm):
    credibility = FloatField('Credibility Weight', validators=[DataRequired(), NumberRange(min=0, max=1)])
    fit = FloatField('Club Fit Weight', validators=[DataRequired(), NumberRange(min=0, max=1)])
    value = FloatField('Value Weight', validators=[DataRequired(), NumberRange(min=0, max=1)])
    momentum = FloatField('Momentum Weight', validators=[DataRequired(), NumberRange(min=0, max=1)])

class SourceReputationForm(FlaskForm):
    source_id = HiddenField('Source ID', validators=[DataRequired()])
    reputation_tag = SelectField('Reputation', choices=[
        ('trusted', 'Trusted'),
        ('neutral', 'Neutral'),
        ('unreliable', 'Unreliable')
    ], validators=[DataRequired()])

class UserRatingForm(FlaskForm):
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
