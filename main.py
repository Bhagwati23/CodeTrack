#!/usr/bin/env python3
"""
CodeTrack Pro - Main Application Entry Point
Comprehensive coding learning platform with AI tutoring, contests, and collaboration
"""

import os
import sys
import logging
import signal
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Configure application logging"""
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'False').lower() == 'true' else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('codetrack_pro.log')
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def start_notification_scheduler():
    """Start the background notification scheduler"""
    try:
        from services.notification_scheduler import NotificationScheduler
        
        scheduler = NotificationScheduler()
        scheduler.start()
        
        logging.info("Notification scheduler started successfully")
        return scheduler
        
    except Exception as e:
        logging.error(f"Failed to start notification scheduler: {e}")
        return None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    
    # Stop notification scheduler if running
    if hasattr(signal_handler, 'scheduler') and signal_handler.scheduler:
        signal_handler.scheduler.stop()
    
    sys.exit(0)

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("CodeTrack Pro - Starting Application")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Create Flask application
        from app import create_app, init_database
        
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialization completed")
        
        # Create Flask app
        logger.info("Creating Flask application...")
        app = create_app()
        logger.info("Flask application created successfully")
        
        # Start notification scheduler in background
        logger.info("Starting notification scheduler...")
        scheduler = start_notification_scheduler()
        signal_handler.scheduler = scheduler  # Store reference for cleanup
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Get server configuration
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info("=" * 60)
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Disable reloader to prevent scheduler conflicts
        )
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if hasattr(signal_handler, 'scheduler') and signal_handler.scheduler:
            signal_handler.scheduler.stop()
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    main()
