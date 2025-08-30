# TransferRank - Football Transfer Rumour Analysis

## Overview

TransferRank is a web application that aggregates, scores, and ranks football transfer rumours. The platform provides a comprehensive leaderboard system that evaluates transfer rumours based on four key metrics: credibility, club fit, value, and momentum. Users can submit rumours manually, upload CSV files for bulk import, and explore detailed analytics through an intuitive web interface.

The application serves football fans, creators, and analysts who want transparent, data-driven insights into transfer rumour reliability and likelihood.

## User Preferences

Preferred communication style: Simple, everyday language.
Copy tone: Warm, confident, helpful. British English with no hyphens in UI text.
Design: Clean, modern UI with calm color palette and consistent spacing.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM for database operations
- **Database**: SQLite for development with configurable database URI for production deployments
- **Models**: Core entities include Player, Source, Rumour, Score, Settings, ClubNeeds, and UserRating with proper foreign key relationships
- **Scoring Engine**: Custom scoring algorithm that calculates credibility, fit, value, and momentum scores with configurable weights

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Bootstrap for responsive UI components
- **Styling**: Bootstrap with custom CSS for score badges, source reputation indicators, and visual consistency
- **JavaScript**: Vanilla JavaScript for interactive features including chart rendering and user rating systems
- **Charts**: Chart.js integration for data visualization and sparkline momentum indicators

### Authentication & Security
- **Admin Access**: Simple password-based authentication using environment variables
- **Session Management**: Flask sessions for admin state persistence
- **Form Validation**: WTForms integration with CSRF protection and input validation
- **File Upload**: Secure CSV upload functionality with file type and size restrictions

### Data Management
- **Manual Entry**: Web forms for individual rumour submission with comprehensive field validation
- **Bulk Import**: CSV upload system with template validation and error reporting
- **Seeding**: Automated database seeding with realistic transfer rumour data for development

### Scoring System
- **Multi-factor Analysis**: Combines credibility (source reputation), fit (positional needs), value (fee assessment), and momentum (recent activity)
- **Configurable Weights**: Admin-adjustable scoring weights stored in database settings
- **Source Reputation**: Three-tier system (trusted, neutral, unreliable) with historical accuracy tracking
- **Club Needs Mapping**: Position-based fit scoring using club-specific requirement data

### API Design
- **RESTful Routes**: Clean URL structure for players, rumours, sources, and administrative functions
- **Error Handling**: Custom 404 and 500 error pages with helpful navigation
- **Pagination**: Built-in pagination for large dataset handling
- **Filtering**: Advanced search and filter capabilities across multiple dimensions

## External Dependencies

### Core Framework Dependencies
- **Flask**: Primary web framework for application routing and request handling
- **SQLAlchemy**: ORM for database operations and model relationships
- **WTForms**: Form handling and validation with Flask-WTF integration

### Frontend Libraries
- **Bootstrap**: UI framework with Replit dark theme integration
- **Font Awesome**: Icon library for consistent visual elements
- **Chart.js**: JavaScript charting library for data visualization

### Development Tools
- **Werkzeug**: WSGI utilities including ProxyFix for deployment environments
- **Python Logging**: Built-in logging configuration for debugging and monitoring

### Optional Integrations
- **RSS Feeds**: Planned integration for automated rumour ingestion (graceful fallback if unavailable)
- **External APIs**: Placeholder support for player statistics and club data (mock data fallback)

### Environment Configuration
- **DATABASE_URL**: Configurable database connection string
- **SESSION_SECRET**: Secure session key for production deployment
- **ADMIN_PASSWORD**: Administrative access credentials