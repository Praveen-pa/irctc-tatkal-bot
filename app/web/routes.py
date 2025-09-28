"""
IRCTC Tatkal Automation Bot - Web Routes
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import emit
from datetime import datetime, timedelta
import json
import logging
from utils.validation import BookingValidator, ValidationError
from utils.encryption import CredentialManager
from bot.scheduler import TatkalScheduler
from bot.irctc_automation import IRCTCBot
from config import Config

# Create blueprint
web_bp = Blueprint('web', __name__)

# Initialize components
config = Config()
validator = BookingValidator()
credential_manager = CredentialManager(config.ENCRYPTION_KEY)
scheduler = TatkalScheduler()

# Global variables for active bookings
active_bookings = {}
logger = logging.getLogger(__name__)

@web_bp.route('/')
def index():
    """Main booking interface"""
    return render_template('index.html')

@web_bp.route('/status')
def status_page():
    """Real-time status monitoring page"""
    return render_template('status.html')

@web_bp.route('/config')
def config_page():
    """Configuration and settings page"""
    return render_template('config.html')

@web_bp.route('/api/health')
def health_check():
    """Application health check"""
    try:
        # Check database connection
        db_status = "healthy"
        
        # Check scheduler
        scheduler_status = "healthy" if scheduler.is_running else "unhealthy"
        
        # Check IRCTC accessibility
        import requests
        try:
            response = requests.get(config.IRCTC_BASE_URL, timeout=5)
            irctc_status = "healthy" if response.status_code == 200 else "degraded"
        except:
            irctc_status = "unhealthy"
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'services': {
                'database': db_status,
                'scheduler': scheduler_status,
                'irctc': irctc_status
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@web_bp.route('/api/validate_booking', methods=['POST'])
def validate_booking():
    """Validate booking configuration"""
    try:
        booking_data = request.get_json(force=True)
        
        if not booking_data:
            return jsonify({'error': 'No booking data provided'}), 400
        
        # Sanitize input
        sanitized_data = validator.sanitize_input(booking_data)
        
        # Validate
        is_valid, errors = validator.validate_booking_data(sanitized_data)
        
        if is_valid:
            return jsonify({
                'valid': True,
                'message': 'Booking data is valid',
                'data': sanitized_data
            })
        else:
            return jsonify({
                'valid': False,
                'errors': errors
            }), 400
            
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500

@web_bp.route('/api/schedule_booking', methods=['POST'])
def schedule_booking():
    """Schedule a Tatkal booking"""
    try:
        booking_data = request.get_json(force=True)
        
        # Validate booking data
        is_valid, errors = validator.validate_booking_data(booking_data)
        if not is_valid:
            return jsonify({'error': 'Invalid booking data', 'details': errors}), 400
        
        # Calculate Tatkal timing
        booking_time = scheduler.calculate_tatkal_time(
            booking_data['journey_date'],
            booking_data['travel_class']
        )
        
        # Check if Tatkal time has already passed
        if scheduler.is_tatkal_time_passed(booking_data['journey_date'], booking_data['travel_class']):
            return jsonify({
                'error': 'Tatkal booking time has already passed for this date and class'
            }), 400
        
        # Encrypt credentials
        encrypted_credentials = credential_manager.encrypt_credentials({
            'username': booking_data['username'],
            'password': booking_data['password']
        })
        
        # Prepare booking config
        booking_config = {
            **booking_data,
            'credentials': encrypted_credentials
        }
        
        # Schedule the booking
        job_id = scheduler.schedule_booking(booking_config, booking_time)
        
        return jsonify({
            'status': 'scheduled',
            'job_id': job_id,
            'booking_time': booking_time.isoformat(),
            'message': f'Booking scheduled for {booking_time.strftime("%Y-%m-%d at %H:%M:%S")}'
        })
        
    except Exception as e:
        logger.error(f"Error scheduling booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/start_booking', methods=['POST'])
def start_booking():
    """Start immediate booking"""
    try:
        booking_data = request.get_json(force=True)
        
        # Validate booking data
        is_valid, errors = validator.validate_booking_data(booking_data)
        if not is_valid:
            return jsonify({'error': 'Invalid booking data', 'details': errors}), 400
        
        # Check if there's already an active booking
        if active_bookings:
            return jsonify({
                'error': 'Another booking is already in progress'
            }), 409
        
        # Create unique booking ID
        booking_id = f"immediate_{int(datetime.now().timestamp())}"
        
        # Encrypt credentials
        encrypted_credentials = credential_manager.encrypt_credentials({
            'username': booking_data['username'],
            'password': booking_data['password']
        })
        
        # Prepare booking config
        booking_config = {
            **booking_data,
            'credentials': encrypted_credentials,
            'booking_id': booking_id
        }
        
        # Store active booking
        active_bookings[booking_id] = {
            'config': booking_config,
            'status': 'starting',
            'started_at': datetime.now()
        }
        
        # Start booking immediately
        # This would typically be handled by the websocket handler
        return jsonify({
            'status': 'booking_started',
            'booking_id': booking_id,
            'message': 'Booking started immediately'
        })
        
    except Exception as e:
        logger.error(f"Error starting booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/stop_booking', methods=['POST'])
def stop_booking():
    """Stop current booking process"""
    try:
        data = request.get_json() or {}
        booking_id = data.get('booking_id')
        
        if not booking_id and active_bookings:
            # Stop the first active booking if no ID provided
            booking_id = list(active_bookings.keys())[0]
        
        if booking_id in active_bookings:
            # Update status
            active_bookings[booking_id]['status'] = 'stopped'
            active_bookings[booking_id]['stopped_at'] = datetime.now()
            
            # Remove from active bookings
            del active_bookings[booking_id]
            
            return jsonify({
                'status': 'booking_stopped',
                'booking_id': booking_id,
                'message': 'Booking process stopped'
            })
        else:
            return jsonify({
                'error': 'No active booking found to stop'
            }), 404
            
    except Exception as e:
        logger.error(f"Error stopping booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/booking_status')
def get_booking_status():
    """Get current booking status"""
    try:
        booking_id = request.args.get('booking_id')
        
        if booking_id and booking_id in active_bookings:
            booking = active_bookings[booking_id]
            return jsonify({
                'booking_id': booking_id,
                'status': booking['status'],
                'started_at': booking['started_at'].isoformat(),
                'current_step': booking.get('current_step', 'unknown'),
                'progress': booking.get('progress', 0)
            })
        elif active_bookings:
            # Return first active booking status
            booking_id = list(active_bookings.keys())[0]
            booking = active_bookings[booking_id]
            return jsonify({
                'booking_id': booking_id,
                'status': booking['status'],
                'started_at': booking['started_at'].isoformat(),
                'current_step': booking.get('current_step', 'unknown'),
                'progress': booking.get('progress', 0)
            })
        else:
            return jsonify({
                'status': 'idle',
                'message': 'No active booking'
            })
            
    except Exception as e:
        logger.error(f"Error getting booking status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/scheduled_bookings')
def get_scheduled_bookings():
    """Get list of scheduled bookings"""
    try:
        bookings = scheduler.get_scheduled_bookings()
        return jsonify({
            'scheduled_bookings': bookings,
            'total': len(bookings)
        })
        
    except Exception as e:
        logger.error(f"Error getting scheduled bookings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/cancel_scheduled_booking', methods=['POST'])
def cancel_scheduled_booking():
    """Cancel a scheduled booking"""
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        
        if not job_id:
            return jsonify({'error': 'Job ID required'}), 400
        
        success = scheduler.cancel_booking(job_id)
        
        if success:
            return jsonify({
                'status': 'cancelled',
                'job_id': job_id,
                'message': 'Scheduled booking cancelled'
            })
        else:
            return jsonify({
                'error': 'Failed to cancel booking or booking not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error cancelling booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/save_passenger_config', methods=['POST'])
def save_passenger_config():
    """Save passenger configuration"""
    try:
        data = request.get_json()
        passengers = data.get('passengers', [])
        
        # Validate passengers
        passenger_errors = validator.validate_passengers(passengers)
        if passenger_errors:
            return jsonify({
                'error': 'Invalid passenger data',
                'details': passenger_errors
            }), 400
        
        # Save to session or file
        session['saved_passengers'] = passengers
        
        # Optionally save to file
        import os
        import json
        
        config_dir = config.CONFIG_DIR
        os.makedirs(config_dir, exist_ok=True)
        
        with open(f"{config_dir}/passengers.json", 'w') as f:
            json.dump({
                'passengers': passengers,
                'saved_at': datetime.now().isoformat()
            }, f, indent=2)
        
        return jsonify({
            'status': 'saved',
            'message': 'Passenger configuration saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving passenger config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/load_passenger_config')
def load_passenger_config():
    """Load saved passenger configuration"""
    try:
        # Try to load from session first
        passengers = session.get('saved_passengers')
        
        if not passengers:
            # Try to load from file
            import os
            import json
            
            config_file = f"{config.CONFIG_DIR}/passengers.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    passengers = data.get('passengers', [])
        
        return jsonify({
            'passengers': passengers or [],
            'message': 'Passenger configuration loaded'
        })
        
    except Exception as e:
        logger.error(f"Error loading passenger config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/stations')
def get_stations():
    """Get list of common railway stations"""
    stations = [
        {"code": "NDLS", "name": "NEW DELHI", "display": "NEW DELHI - NDLS"},
        {"code": "BCT", "name": "MUMBAI CENTRAL", "display": "MUMBAI CENTRAL - BCT"},
        {"code": "MAS", "name": "CHENNAI CENTRAL", "display": "CHENNAI CENTRAL - MAS"},
        {"code": "KOAA", "name": "KOLKATA", "display": "KOLKATA - KOAA"},
        {"code": "SBC", "name": "BANGALORE CITY", "display": "BANGALORE CITY - SBC"},
        {"code": "HYB", "name": "HYDERABAD DECAN", "display": "HYDERABAD DECAN - HYB"},
        {"code": "ADI", "name": "AHMEDABAD JN", "display": "AHMEDABAD JN - ADI"},
        {"code": "PUNE", "name": "PUNE JN", "display": "PUNE JN - PUNE"},
        {"code": "LKO", "name": "LUCKNOW", "display": "LUCKNOW - LKO"},
        {"code": "PNBE", "name": "PATNA JN", "display": "PATNA JN - PNBE"},
        {"code": "JAT", "name": "JAMMU TAWI", "display": "JAMMU TAWI - JAT"},
        {"code": "TVC", "name": "TRIVANDRUM CENTRAL", "display": "TRIVANDRUM CENTRAL - TVC"},
        {"code": "ERS", "name": "ERNAKULAM JN", "display": "ERNAKULAM JN - ERS"},
        {"code": "BBS", "name": "BHUBANESWAR", "display": "BHUBANESWAR - BBS"},
        {"code": "VSKP", "name": "VISAKHAPATNAM", "display": "VISAKHAPATNAM - VSKP"}
    ]
    
    return jsonify({'stations': stations})

@web_bp.route('/api/system_info')
def get_system_info():
    """Get system information and metrics"""
    try:
        import psutil
        import platform
        
        # System info
        system_info = {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'free': psutil.disk_usage('/').free,
                'total': psutil.disk_usage('/').total,
                'percent': psutil.disk_usage('/').percent
            },
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        # Application info
        app_info = {
            'version': '1.0.0',
            'environment': config.ENVIRONMENT,
            'debug_mode': config.DEBUG,
            'active_bookings': len(active_bookings),
            'scheduled_bookings': len(scheduler.get_scheduled_bookings())
        }
        
        return jsonify({
            'system': system_info,
            'application': app_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@web_bp.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    return render_template('error.html', error="Page not found"), 404

@web_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error="Internal server error"), 500

def register_routes(app, scheduler_instance, websocket_handler):
    """Register routes with the Flask application"""
    global scheduler
    scheduler = scheduler_instance
    
    app.register_blueprint(web_bp)
