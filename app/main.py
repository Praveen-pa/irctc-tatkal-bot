"""
IRCTC Tatkal Automation Bot - Main Flask Application
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import os
import json
import threading
from datetime import datetime, timedelta
import logging
from config import Config
from utils.logging import setup_logger
from utils.encryption import CredentialManager
from bot.irctc_automation import IRCTCBot
from bot.scheduler import TatkalScheduler
from web.routes import register_routes
from web.websocket_handler import WebSocketHandler

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    config = Config()
    app.config.from_object(config)
    
    # Initialize extensions
    socketio.init_app(app)
    
    # Setup logging
    logger = setup_logger('main_app')
    
    # Global variables
    bot_instance = None
    scheduler = TatkalScheduler()
    websocket_handler = WebSocketHandler(socketio)
    
    # Register routes
    register_routes(app, scheduler, websocket_handler)
    
    @app.route('/')
    def index():
        """Main booking interface"""
        return render_template('index.html')
    
    @app.route('/status')
    def status_page():
        """Real-time status monitoring page"""
        return render_template('status.html')
    
    @app.route('/config')
    def config_page():
        """Configuration and settings page"""
        return render_template('config.html')
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/api/schedule_booking', methods=['POST'])
    def schedule_booking():
        """Schedule a Tatkal booking"""
        try:
            booking_data = request.json
            
            # Validate booking data
            if not _validate_booking_data(booking_data):
                return jsonify({'error': 'Invalid booking data'}), 400
            
            # Calculate Tatkal timing
            booking_time = _calculate_tatkal_time(
                booking_data['journey_date'], 
                booking_data['travel_class']
            )
            
            # Schedule the booking
            job_id = scheduler.schedule_booking(booking_data, booking_time)
            
            logger.info(f"Booking scheduled with job ID: {job_id}")
            
            return jsonify({
                'status': 'scheduled',
                'job_id': job_id,
                'booking_time': booking_time.isoformat(),
                'message': 'Booking scheduled successfully'
            })
            
        except Exception as e:
            logger.error(f"Error scheduling booking: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/start_booking', methods=['POST'])
    def start_booking():
        """Start immediate booking"""
        nonlocal bot_instance
        
        try:
            booking_data = request.json
            
            if not _validate_booking_data(booking_data):
                return jsonify({'error': 'Invalid booking data'}), 400
            
            # Create bot instance
            bot_instance = IRCTCBot(
                config=booking_data,
                socketio=socketio,
                websocket_handler=websocket_handler
            )
            
            # Start booking in background thread
            booking_thread = threading.Thread(
                target=bot_instance.start_booking,
                daemon=True
            )
            booking_thread.start()
            
            logger.info("Booking started immediately")
            
            return jsonify({'status': 'booking_started'})
            
        except Exception as e:
            logger.error(f"Error starting booking: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stop_booking', methods=['POST'])
    def stop_booking():
        """Stop current booking process"""
        nonlocal bot_instance
        
        try:
            if bot_instance:
                bot_instance.stop_booking()
                bot_instance = None
                logger.info("Booking stopped by user request")
                return jsonify({'status': 'booking_stopped'})
            else:
                return jsonify({'error': 'No active booking to stop'}), 400
                
        except Exception as e:
            logger.error(f"Error stopping booking: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/get_booking_status')
    def get_booking_status():
        """Get current booking status"""
        try:
            if bot_instance:
                status = bot_instance.get_status()
            else:
                status = {'status': 'idle', 'message': 'No active booking'}
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting booking status: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to IRCTC Tatkal Bot'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('captcha_response')
    def handle_captcha_response(data):
        """Handle captcha input from user"""
        if bot_instance:
            bot_instance.submit_captcha(data['captcha_text'])
            logger.info("Captcha response received from user")
    
    @socketio.on('otp_response')
    def handle_otp_response(data):
        """Handle OTP input from user"""
        if bot_instance:
            bot_instance.submit_otp(data['otp'])
            logger.info("OTP response received from user")
    
    def _validate_booking_data(data):
        """Validate booking data"""
        required_fields = [
            'from_station', 'to_station', 'journey_date',
            'travel_class', 'passengers', 'credentials'
        ]
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate passengers
        if not data['passengers'] or len(data['passengers']) == 0:
            logger.error("No passengers provided")
            return False
        
        return True
    
    def _calculate_tatkal_time(journey_date, travel_class):
        """Calculate Tatkal booking time"""
        journey_dt = datetime.strptime(journey_date, '%Y-%m-%d')
        
        # Tatkal booking opens 1 day before journey
        booking_date = journey_dt - timedelta(days=1)
        
        # AC classes: 10:00 AM, Non-AC classes: 11:00 AM
        if travel_class in ['1A', '2A', '3A', 'CC', 'EC']:
            booking_time = booking_date.replace(hour=10, minute=0, second=0, microsecond=0)
        else:
            booking_time = booking_date.replace(hour=11, minute=0, second=0, microsecond=0)
        
        return booking_time
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error="Page not found"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error="Internal server error"), 500
    
    return app