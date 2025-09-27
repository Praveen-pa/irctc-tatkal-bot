"""
IRCTC Tatkal Automation Bot - Core Automation Logic
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import ntplib
from utils.logging import setup_logger
from utils.encryption import CredentialManager
from config import Config

class IRCTCBot:
    """Main IRCTC automation bot class"""
    
    def __init__(self, config, socketio=None, websocket_handler=None):
        self.config = config
        self.socketio = socketio
        self.websocket_handler = websocket_handler
        self.logger = setup_logger('irctc_bot')
        
        # Browser components
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # State management
        self.is_running = False
        self.current_step = "idle"
        self.booking_result = None
        
        # User input handling
        self.captcha_response = None
        self.otp_response = None
        self.waiting_for_input = False
        
        # Configuration
        self.app_config = Config()
        
    def start_booking(self):
        """Main booking execution flow"""
        try:
            self.is_running = True
            self._emit_status("🚀 Starting IRCTC Tatkal booking process...", "info")
            
            # Initialize browser
            self._init_browser()
            
            # Execute booking steps
            self._login()
            self._search_trains()
            self._select_train()
            self._fill_passenger_details()
            self._handle_payment()
            self._confirm_booking()
            
        except Exception as e:
            self.logger.error(f"Booking failed with error: {str(e)}")
            self._emit_status(f"❌ Booking failed: {str(e)}", "error")
            self._save_booking_result("failed", str(e))
        finally:
            self._cleanup()
            
    def stop_booking(self):
        """Stop the current booking process"""
        self.is_running = False
        self._emit_status("🛑 Booking process stopped by user", "warning")
        self._cleanup()
        
    def get_status(self):
        """Get current booking status"""
        return {
            "is_running": self.is_running,
            "current_step": self.current_step,
            "waiting_for_input": self.waiting_for_input,
            "timestamp": datetime.now().isoformat()
        }
        
    def submit_captcha(self, captcha_text):
        """Submit captcha response from user"""
        self.captcha_response = captcha_text
        self.waiting_for_input = False
        self._emit_status("✅ Captcha received, continuing...", "success")
        
    def submit_otp(self, otp):
        """Submit OTP response from user"""
        self.otp_response = otp
        self.waiting_for_input = False
        self._emit_status("✅ OTP received, continuing...", "success")
        
    def _init_browser(self):
        """Initialize Playwright browser"""
        self._emit_status("🌐 Initializing browser...", "info")
        self.current_step = "browser_init"
        
        self.playwright = sync_playwright().start()
        
        # Browser launch options
        browser_options = {
            "headless": self.app_config.PLAYWRIGHT_HEADLESS,
            "slow_mo": self.app_config.PLAYWRIGHT_SLOW_MO,
            "args": [
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-gpu",
                "--no-first-run",
                "--disable-extensions",
                "--disable-default-apps"
            ]
        }
        
        self.browser = self.playwright.chromium.launch(**browser_options)
        
        # Create context with mobile user agent for better performance
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = self.context.new_page()
        
        # Set timeouts
        self.page.set_default_timeout(self.app_config.PAGE_LOAD_TIMEOUT * 1000)
        
    def _login(self):
        """Login to IRCTC"""
        self._emit_status("🔐 Logging into IRCTC...", "info")
        self.current_step = "login"
        
        # Navigate to IRCTC
        self.page.goto(self.app_config.IRCTC_LOGIN_URL)
        
        # Wait for page load
        self.page.wait_for_selector("text=LOGIN", timeout=30000)
        
        # Click login button
        self.page.click("text=LOGIN")
        
        # Wait for login form
        self.page.wait_for_selector("#userId", timeout=10000)
        
        # Decrypt and fill credentials
        credential_manager = CredentialManager(self.app_config.ENCRYPTION_KEY)
        credentials = credential_manager.decrypt_credentials(self.config['credentials'])
        
        self.page.fill("#userId", credentials['username'])
        self.page.fill("#pwd", credentials['password'])
        
        # Handle login captcha
        self._handle_login_captcha()
        
        # Click sign in
        self.page.click("#loginBtnId")
        
        # Handle OTP if required
        self._handle_otp()
        
        # Wait for successful login
        try:
            self.page.wait_for_selector("text=logout", timeout=30000)
            self._emit_status("✅ Login successful", "success")
        except PlaywrightTimeoutError:
            raise Exception("Login failed - timeout waiting for success confirmation")
            
    def _handle_login_captcha(self):
        """Handle login captcha"""
        try:
            captcha_image = self.page.locator("#captcha")
            if captcha_image.is_visible():
                self._emit_status("🔍 Captcha detected, please solve...", "warning")
                
                # Take screenshot of captcha
                captcha_path = f"{self.app_config.TEMP_DIR}/login_captcha_{int(time.time())}.png"
                captcha_image.screenshot(path=captcha_path)
                
                # Request captcha input from user
                self.waiting_for_input = True
                self.captcha_response = None
                
                if self.websocket_handler:
                    self.websocket_handler.request_captcha_input(captcha_path)
                
                # Wait for user response
                self._wait_for_captcha_response()
                
                # Fill captcha
                self.page.fill("#captcha", self.captcha_response)
                
        except Exception as e:
            self.logger.warning(f"Captcha handling issue: {str(e)}")
            
    def _handle_otp(self):
        """Handle OTP verification"""
        try:
            # Check if OTP page appears
            if self.page.is_visible("#otpModal", timeout=5000):
                self._emit_status("📱 OTP required, please enter...", "warning")
                
                # Request OTP from user
                self.waiting_for_input = True
                self.otp_response = None
                
                if self.websocket_handler:
                    self.websocket_handler.request_otp_input()
                
                # Wait for user response
                self._wait_for_otp_response()
                
                # Fill OTP
                self.page.fill("#otpLoginId", self.otp_response)
                self.page.click("#continueBtn")
                
        except Exception as e:
            self.logger.warning(f"OTP handling issue: {str(e)}")
            
    def _search_trains(self):
        """Search for trains"""
        self._emit_status("🚂 Searching for trains...", "info")
        self.current_step = "train_search"
        
        # Navigate to booking page
        self.page.goto(f"{self.app_config.IRCTC_BASE_URL}/nget/train-search")
        
        # Fill journey details
        self.page.click("#origin")
        self.page.fill("#origin", self.config['from_station'])
        self.page.press("#origin", "ArrowDown")
        self.page.press("#origin", "Enter")
        
        self.page.click("#destination")
        self.page.fill("#destination", self.config['to_station'])
        self.page.press("#destination", "ArrowDown")
        self.page.press("#destination", "Enter")
        
        # Set journey date
        self._set_journey_date()
        
        # Select class
        self.page.select_option("#journeyClass", self.config['travel_class'])
        
        # Set quota to Tatkal
        self.page.select_option("#journeyQuota", "TQ")
        
        # Search trains
        self.page.click("#searchBtn")
        
        # Wait for results
        self.page.wait_for_selector(".train-list", timeout=30000)
        self._emit_status("✅ Train search completed", "success")
        
    def _select_train(self):
        """Select and book the preferred train"""
        self._emit_status("🎯 Selecting train...", "info")
        self.current_step = "train_selection"
        
        # Find the preferred train
        train_number = self.config.get('train_number')
        if train_number:
            train_selector = f"text={train_number}"
            try:
                self.page.click(train_selector, timeout=10000)
            except PlaywrightTimeoutError:
                # Fallback to first available train
                self._emit_status("⚠️ Preferred train not found, selecting first available", "warning")
                self.page.click(".train-list .book-now-btn", timeout=10000)
        else:
            # Select first available train
            self.page.click(".train-list .book-now-btn", timeout=10000)
        
        self._emit_status("✅ Train selected", "success")
        
    def _fill_passenger_details(self):
        """Fill passenger details"""
        self._emit_status("👥 Filling passenger details...", "info")
        self.current_step = "passenger_details"
        
        # Wait for passenger form
        self.page.wait_for_selector("#passenger-details", timeout=15000)
        
        # Fill passenger information
        passengers = self.config['passengers']
        for i, passenger in enumerate(passengers):
            # Name
            name_selector = f"#passengerName_{i}"
            self.page.fill(name_selector, passenger['name'])
            
            # Age
            age_selector = f"#passengerAge_{i}"
            self.page.fill(age_selector, str(passenger['age']))
            
            # Gender
            gender_selector = f"#passengerGender_{i}"
            self.page.select_option(gender_selector, passenger['gender'])
            
            # Berth preference
            if 'berth_preference' in passenger:
                berth_selector = f"#passengerBerth_{i}"
                self.page.select_option(berth_selector, passenger['berth_preference'])
        
        # Handle additional options
        if self.config.get('auto_upgrade', False):
            self.page.check("#autoUpgradation")
            
        if self.config.get('travel_insurance', False):
            self.page.check("#travelInsurance")
            
        # Handle booking captcha
        self._handle_booking_captcha()
        
        # Proceed to payment
        self.page.click("#reviewBooking")
        self._emit_status("✅ Passenger details filled", "success")
        
    def _handle_booking_captcha(self):
        """Handle booking page captcha"""
        try:
            captcha_selector = "#captcha-img"
            if self.page.is_visible(captcha_selector, timeout=2000):
                self._emit_status("🔍 Booking captcha detected...", "warning")
                
                # Screenshot captcha
                captcha_path = f"{self.app_config.TEMP_DIR}/booking_captcha_{int(time.time())}.png"
                self.page.locator(captcha_selector).screenshot(path=captcha_path)
                
                # Request captcha from user
                self.waiting_for_input = True
                self.captcha_response = None
                
                if self.websocket_handler:
                    self.websocket_handler.request_captcha_input(captcha_path)
                    
                # Wait for response
                self._wait_for_captcha_response()
                
                # Fill captcha
                self.page.fill("#captcha-input", self.captcha_response)
                
        except Exception as e:
            self.logger.warning(f"Booking captcha handling: {str(e)}")
            
    def _handle_payment(self):
        """Handle payment process"""
        self._emit_status("💳 Processing payment...", "info")
        self.current_step = "payment"
        
        # Wait for payment page
        self.page.wait_for_selector("#payment-options", timeout=15000)
        
        # Select UPI payment
        self.page.click("input[value='UP']")  # UPI option
        
        # Select gateway if specified
        if self.config.get('upi_gateway'):
            gateway = self.config['upi_gateway']
            self.page.click(f"input[value='{gateway}']")
        
        # Fill UPI ID if provided
        if self.config.get('upi_id'):
            self.page.fill("#upiId", self.config['upi_id'])
            
        # Proceed to payment
        self.page.click("#makePayment")
        
        self._emit_status("🔄 Redirected to payment gateway - Please complete payment", "warning")
        
        # Wait for payment completion (or timeout)
        self._wait_for_payment_completion()
        
    def _wait_for_payment_completion(self):
        """Wait for payment to complete"""
        try:
            # Wait for return to IRCTC (successful payment)
            self.page.wait_for_url("**/booking/confirmation**", timeout=180000)  # 3 minutes
            self._emit_status("✅ Payment completed successfully", "success")
        except PlaywrightTimeoutError:
            self._emit_status("⚠️ Payment timeout - Please check manually", "warning")
            
    def _confirm_booking(self):
        """Confirm booking and extract PNR"""
        self._emit_status("📋 Confirming booking...", "info")
        self.current_step = "confirmation"
        
        try:
            # Wait for confirmation page
            self.page.wait_for_selector("#pnr-details", timeout=30000)
            
            # Extract PNR
            pnr_element = self.page.locator("#pnr-number")
            if pnr_element.is_visible():
                pnr = pnr_element.text_content().strip()
                self._emit_status(f"🎉 Booking successful! PNR: {pnr}", "success")
                self._save_booking_result("success", pnr=pnr)
            else:
                # Check for failure message
                error_element = self.page.locator(".booking-failed")
                if error_element.is_visible():
                    error_msg = error_element.text_content().strip()
                    self._emit_status(f"❌ Booking failed: {error_msg}", "error")
                    self._save_booking_result("failed", error_msg)
                else:
                    self._emit_status("⚠️ Unknown booking status", "warning")
                    self._save_booking_result("unknown", "Unable to determine status")
                    
        except Exception as e:
            self.logger.error(f"Confirmation error: {str(e)}")
            # Take screenshot for manual verification
            screenshot_path = f"{self.app_config.LOGS_DIR}/booking_result_{int(time.time())}.png"
            self.page.screenshot(path=screenshot_path)
            self._emit_status(f"⚠️ Confirmation error - Screenshot saved: {screenshot_path}", "warning")
            
    def _set_journey_date(self):
        """Set journey date in the calendar"""
        journey_date = datetime.strptime(self.config['journey_date'], '%Y-%m-%d')
        
        # Click date picker
        self.page.click("#jDate")
        
        # Navigate to correct month/year if needed
        self._navigate_calendar_to_date(journey_date)
        
        # Click the specific date
        date_selector = f"text={journey_date.day}"
        self.page.click(date_selector)
        
    def _navigate_calendar_to_date(self, target_date):
        """Navigate calendar to the target date"""
        # This is a simplified version - actual implementation would depend on IRCTC's calendar UI
        # For now, assume the date is in the current view
        pass
        
    def _wait_for_captcha_response(self, timeout=300):
        """Wait for user to provide captcha response"""
        start_time = time.time()
        while self.waiting_for_input and self.captcha_response is None:
            if time.time() - start_time > timeout:
                raise Exception("Timeout waiting for captcha response")
            time.sleep(0.5)
            
    def _wait_for_otp_response(self, timeout=300):
        """Wait for user to provide OTP response"""
        start_time = time.time()
        while self.waiting_for_input and self.otp_response is None:
            if time.time() - start_time > timeout:
                raise Exception("Timeout waiting for OTP response")
            time.sleep(0.5)
            
    def _emit_status(self, message, status_type="info"):
        """Emit status update to UI"""
        status_data = {
            "message": message,
            "type": status_type,
            "step": self.current_step,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.websocket_handler:
            self.websocket_handler.emit_status(status_data)
            
        # Log the message
        if status_type == "error":
            self.logger.error(message)
        elif status_type == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
            
    def _save_booking_result(self, status, details=None, pnr=None):
        """Save booking result to file"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "pnr": pnr,
            "details": details,
            "config": {
                "from_station": self.config['from_station'],
                "to_station": self.config['to_station'],
                "journey_date": self.config['journey_date'],
                "travel_class": self.config['travel_class'],
                "passenger_count": len(self.config['passengers'])
            }
        }
        
        self.booking_result = result
        
        # Save to file
        result_file = f"{self.app_config.LOGS_DIR}/booking_results.json"
        with open(result_file, "a") as f:
            f.write(json.dumps(result) + "\n")
            
    def _cleanup(self):
        """Clean up resources"""
        self.is_running = False
        
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
            
        self._emit_status("🧹 Cleanup completed", "info")