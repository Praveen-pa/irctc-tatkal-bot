"""
IRCTC Tatkal Automation Bot - WebSocket Handler
"""

from flask_socketio import SocketIO, emit, disconnect
from datetime import datetime
import logging
import json
import threading
import time
from bot.irctc_automation import IRCTCBot
from utils.logging import setup_logger

class WebSocketHandler:
    """Handles WebSocket communication for real-time updates"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.logger = setup_logger('websocket_handler')
        self.connected_clients = set()
        self.active_bot = None
        
        # Register event handlers
        self.register_handlers()
        
    def register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.connected_clients.add(request.sid)
            self.logger.info(f"Client connected: {request.sid}")
            
            emit('connected', {
                'message': 'Connected to IRCTC Tatkal Bot',
                'timestamp': datetime.now().isoformat(),
                'client_id': request.sid
            })
            
            # Send current status if available
            if self.active_bot:
                emit('booking_status', self.active_bot.get_status())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            if request.sid in self.connected_clients:
                self.connected_clients.remove(request.sid)
            self.logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('captcha_response')
        def handle_captcha_response(data):
            """Handle captcha input from user"""
            self.logger.info("Received captcha response from client")
            
            captcha_text = data.get('captcha_text', '').strip()
            
            if not captcha_text:
                emit('error', {'message': 'Invalid captcha input'})
                return
            
            if self.active_bot:
                self.active_bot.submit_captcha(captcha_text)
                emit('captcha_submitted', {
                    'message': 'Captcha submitted successfully',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                emit('error', {'message': 'No active booking to submit captcha'})
        
        @self.socketio.on('otp_response')
        def handle_otp_response(data):
            """Handle OTP input from user"""
            self.logger.info("Received OTP response from client")
            
            otp = data.get('otp', '').strip()
            
            if not otp or len(otp) != 6 or not otp.isdigit():
                emit('error', {'message': 'Invalid OTP format. Must be 6 digits.'})
                return
            
            if self.active_bot:
                self.active_bot.submit_otp(otp)
                emit('otp_submitted', {
                    'message': 'OTP submitted successfully',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                emit('error', {'message': 'No active booking to submit OTP'})
        
        @self.socketio.on('start_booking')
        def handle_start_booking(data):
            """Handle immediate booking request"""
            if self.active_bot and self.active_bot.is_running:
                emit('error', {'message': 'Another booking is already in progress'})
                return
            
            try:
                # Create and start bot
                self.active_bot = IRCTCBot(
                    config=data,
                    socketio=self.socketio,
                    websocket_handler=self
                )
                
                # Start booking in background thread
                booking_thread = threading.Thread(
                    target=self.active_bot.start_booking,
                    daemon=True
                )
                booking_thread.start()
                
                emit('booking_started', {
                    'message': 'Booking process started',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error starting booking: {str(e)}")
                emit('error', {'message': f'Failed to start booking: {str(e)}'})
        
        @self.socketio.on('stop_booking')
        def handle_stop_booking():
            """Handle booking stop request"""
            if not self.active_bot:
                emit('error', {'message': 'No active booking to stop'})
                return
            
            try:
                self.active_bot.stop_booking()
                self.active_bot = None
                
                emit('booking_stopped', {
                    'message': 'Booking process stopped',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error stopping booking: {str(e)}")
                emit('error', {'message': f'Failed to stop booking: {str(e)}'})
        
        @self.socketio.on('get_status')
        def handle_get_status():
            """Handle status request"""
            if self.active_bot:
                emit('booking_status', self.active_bot.get_status())
            else:
                emit('booking_status', {
                    'is_running': False,
                    'current_step': 'idle',
                    'waiting_for_input': False,
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('ping')
        def handle_ping(data):
            """Handle ping for connection testing"""
            emit('pong', {
                'timestamp': datetime.now().isoformat(),
                'received_data': data
            })
    
    def emit_status(self, status_data):
        """Emit status update to all connected clients"""
        try:
            self.socketio.emit('booking_status', status_data, broadcast=True)
            self.logger.debug(f"Status emitted to {len(self.connected_clients)} clients")
            
        except Exception as e:
            self.logger.error(f"Error emitting status: {str(e)}")
    
    def request_captcha_input(self, captcha_image_path):
        """Request captcha input from user"""
        try:
            self.socketio.emit('captcha_required', {
                'image_path': captcha_image_path,
                'message': 'Please solve the captcha',
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
            self.logger.info(f"Captcha input requested: {captcha_image_path}")
            
        except Exception as e:
            self.logger.error(f"Error requesting captcha input: {str(e)}")
    
    def request_otp_input(self):
        """Request OTP input from user"""
        try:
            self.socketio.emit('otp_required', {
                'message': 'Please enter the OTP sent to your mobile',
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
            self.logger.info("OTP input requested")
            
        except Exception as e:
            self.logger.error(f"Error requesting OTP input: {str(e)}")
    
    def emit_live_update(self, update_data):
        """Emit live update to all connected clients"""
        try:
            self.socketio.emit('live_update', {
                **update_data,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
        except Exception as e:
            self.logger.error(f"Error emitting live update: {str(e)}")
    
    def emit_system_status(self, status_data):
        """Emit system status update"""
        try:
            self.socketio.emit('system_status', status_data, broadcast=True)
            
        except Exception as e:
            self.logger.error(f"Error emitting system status: {str(e)}")
    
    def emit_booking_complete(self, result_data):
        """Emit booking completion notification"""
        try:
            self.socketio.emit('booking_complete', {
                **result_data,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
            # Reset active bot
            self.active_bot = None
            
            self.logger.info("Booking completion notification sent")
            
        except Exception as e:
            self.logger.error(f"Error emitting booking complete: {str(e)}")
    
    def emit_error(self, error_message, error_type='general'):
        """Emit error message to clients"""
        try:
            self.socketio.emit('error', {
                'message': error_message,
                'type': error_type,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
        except Exception as e:
            self.logger.error(f"Error emitting error message: {str(e)}")
    
    def emit_notification(self, notification_data):
        """Emit notification to clients"""
        try:
            self.socketio.emit('notification', {
                **notification_data,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
        except Exception as e:
            self.logger.error(f"Error emitting notification: {str(e)}")
    
    def get_connected_clients_count(self):
        """Get number of connected clients"""
        return len(self.connected_clients)
    
    def broadcast_message(self, event_name, data):
        """Broadcast custom message to all clients"""
        try:
            self.socketio.emit(event_name, {
                **data,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {str(e)}")

class BookingNotificationManager:
    """Manages booking notifications and alerts"""
    
    def __init__(self, websocket_handler):
        self.websocket_handler = websocket_handler
        self.logger = setup_logger('notification_manager')
        
    def notify_booking_started(self, booking_config):
        """Notify that booking has started"""
        self.websocket_handler.emit_notification({
            'type': 'booking_started',
            'title': 'Booking Started',
            'message': f'Tatkal booking started for {booking_config["from_station"]} to {booking_config["to_station"]}',
            'icon': 'fa-rocket',
            'level': 'info'
        })
    
    def notify_captcha_required(self):
        """Notify that captcha input is required"""
        self.websocket_handler.emit_notification({
            'type': 'captcha_required',
            'title': 'Captcha Required',
            'message': 'Please solve the captcha to continue booking',
            'icon': 'fa-eye',
            'level': 'warning'
        })
    
    def notify_otp_required(self):
        """Notify that OTP input is required"""
        self.websocket_handler.emit_notification({
            'type': 'otp_required',
            'title': 'OTP Required',
            'message': 'Please enter the OTP sent to your mobile',
            'icon': 'fa-mobile-alt',
            'level': 'warning'
        })
    
    def notify_payment_redirect(self, gateway):
        """Notify about payment gateway redirect"""
        self.websocket_handler.emit_notification({
            'type': 'payment_redirect',
            'title': 'Payment Required',
            'message': f'Redirected to {gateway}. Please complete payment on your mobile',
            'icon': 'fa-credit-card',
            'level': 'info'
        })
    
    def notify_booking_success(self, pnr):
        """Notify successful booking"""
        self.websocket_handler.emit_notification({
            'type': 'booking_success',
            'title': 'Booking Successful!',
            'message': f'Your ticket has been booked successfully. PNR: {pnr}',
            'icon': 'fa-check-circle',
            'level': 'success'
        })
    
    def notify_booking_failed(self, reason):
        """Notify failed booking"""
        self.websocket_handler.emit_notification({
            'type': 'booking_failed',
            'title': 'Booking Failed',
            'message': f'Booking could not be completed: {reason}',
            'icon': 'fa-exclamation-triangle',
            'level': 'error'
        })
    
    def notify_system_error(self, error_message):
        """Notify system error"""
        self.websocket_handler.emit_notification({
            'type': 'system_error',
            'title': 'System Error',
            'message': f'A system error occurred: {error_message}',
            'icon': 'fa-bug',
            'level': 'error'
        })

# Periodic status updater
class StatusUpdater:
    """Periodically updates system status"""
    
    def __init__(self, websocket_handler, interval=30):
        self.websocket_handler = websocket_handler
        self.interval = interval
        self.logger = setup_logger('status_updater')
        self.running = False
        
    def start(self):
        """Start periodic status updates"""
        if not self.running:
            self.running = True
            update_thread = threading.Thread(target=self._update_loop, daemon=True)
            update_thread.start()
            self.logger.info("Status updater started")
    
    def stop(self):
        """Stop periodic status updates"""
        self.running = False
        self.logger.info("Status updater stopped")
    
    def _update_loop(self):
        """Main update loop"""
        while self.running:
            try:
                # Get system status
                status = self._get_system_status()
                
                # Emit to clients
                self.websocket_handler.emit_system_status(status)
                
                # Wait for next update
                time.sleep(self.interval)
                
            except Exception as e:
                self.logger.error(f"Error in status update loop: {str(e)}")
                time.sleep(self.interval)
    
    def _get_system_status(self):
        """Get current system status"""
        try:
            import psutil
            
            return {
                'server': 'healthy',
                'irctc': self._check_irctc_status(),
                'bot': 'idle',  # This would be updated based on active bot status
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'connected_clients': self.websocket_handler.get_connected_clients_count()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {str(e)}")
            return {
                'server': 'error',
                'error': str(e)
            }
    
    def _check_irctc_status(self):
        """Check IRCTC website accessibility"""
        try:
            import requests
            response = requests.get('https://www.irctc.co.in', timeout=5)
            return 'healthy' if response.status_code == 200 else 'degraded'
        except:
            return 'unhealthy'