import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_SECRET'] = os.environ.get('SESSION_SECRET', 'session-secret-key')
    
    # Database configuration for Railway PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        # Railway provides postgres:// URLs, but SQLAlchemy expects postgresql://
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to SQLite for development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///codetrack_pro.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Production optimizations for Railway
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 10,
            'max_overflow': 20
        }
    else:
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Configure logging for Railway
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logging.basicConfig(level=logging.WARNING)
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)
    elif not app.debug:
        logging.basicConfig(level=logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    else:
        logging.basicConfig(level=logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        app.logger.addHandler(handler)
    
    # Register blueprints
    from routes import main_bp, auth_bp, dashboard_bp, ai_bp, contest_bp, forum_bp, study_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(contest_bp, url_prefix='/contest')
    app.register_blueprint(forum_bp, url_prefix='/forum')
    app.register_blueprint(study_bp, url_prefix='/study')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Template context processors
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            from models import Notification
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, 
                is_read=False
            ).count()
            return dict(unread_notifications=unread_count)
        return dict(unread_notifications=0)
    
    # Database initialization
    with app.app_context():
        try:
            # Import models to register them
            from models import (
                User, PlatformStats, DailyCodingHours, Problem, ProblemsSolved,
                Flashcard, StudySession, AIRecommendation, StudyGroup, StudyGroupMember,
                GroupChatMessage, ForumPost, ForumAnswer, ForumPostVote, ForumAnswerVote,
                QuestionDiscussion, Contest, ContestProblem, ContestTestCase,
                ContestSubmission, ContestTestResult, ContestParticipant, Notification
            )
            
            # Create tables
            db.create_all()
            
            # Create default admin user if none exists
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                admin = User(
                    username='admin',
                    email='admin@codetrackpro.com',
                    role='admin',
                    first_name='Admin',
                    last_name='User'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                app.logger.info("Default admin user created (username: admin, password: admin123)")
            
            app.logger.info("Database initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    return app

def init_database():
    """Initialize database connection and create tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Import all models
            from models import (
                User, PlatformStats, DailyCodingHours, Problem, ProblemsSolved,
                Flashcard, StudySession, AIRecommendation, StudyGroup, StudyGroupMember,
                GroupChatMessage, ForumPost, ForumAnswer, ForumPostVote, ForumAnswerVote,
                QuestionDiscussion, Contest, ContestProblem, ContestTestCase,
                ContestSubmission, ContestTestResult, ContestParticipant, Notification
            )
            
            # Create all tables
            db.create_all()
            
            # Create indexes for better performance
            try:
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);')
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);')
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_platform_stats_user_platform ON platform_stats(user_id, platform);')
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_daily_coding_hours_user_date ON daily_coding_hours(user_id, date);')
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_forum_posts_created_at ON forum_posts(created_at);')
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_contest_start_date ON contests(start_date);')
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);')
            except Exception as e:
                print(f"Warning: Could not create indexes: {e}")
            
            print("Database initialized successfully!")
            
        except Exception as e:
            print(f"Database initialization failed: {str(e)}")
            raise

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
