"""
IRCTC Tatkal Automation Bot - Input Validation and Sanitization
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json
import logging
from utils.logging import setup_logger

class ValidationError(Exception):
    """Custom validation error exception"""
    pass

class BookingValidator:
    """Validator for booking form data"""
    
    def __init__(self):
        self.logger = setup_logger('validator')
        
        # Station code patterns
        self.station_pattern = re.compile(r'^[A-Z\s]+ - [A-Z]{2,5}$')
        
        # Train number pattern
        self.train_number_pattern = re.compile(r'^\d{5}$')
        
        # UPI ID pattern
        self.upi_pattern = re.compile(r'^[\w\.-]+@[\w-]+$')
        
        # Valid travel classes
        self.valid_classes = ['1A', '2A', '3A', 'SL', 'CC', '2S', 'EC']
        
        # Valid genders
        self.valid_genders = ['M', 'F', 'T']
        
        # Valid berth preferences
        self.valid_berths = ['LB', 'MB', 'UB', 'SU', 'SL', '']
        
        # Valid UPI gateways
        self.valid_gateways = ['GOOGLEPAY', 'PHONEPE', 'PAYTM', 'BHIM', '']
        
    def validate_booking_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete booking data
        
        Args:
            data: Dictionary containing all booking information
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validate journey details
            journey_errors = self.validate_journey_details(data)
            errors.extend(journey_errors)
            
            # Validate passengers
            passenger_errors = self.validate_passengers(data.get('passengers', []))
            errors.extend(passenger_errors)
            
            # Validate credentials
            credential_errors = self.validate_credentials(data.get('credentials', {}))
            errors.extend(credential_errors)
            
            # Validate payment details
            payment_errors = self.validate_payment_details(data)
            errors.extend(payment_errors)
            
            is_valid = len(errors) == 0
            
            if is_valid:
                self.logger.info("Booking data validation passed")
            else:
                self.logger.warning(f"Booking data validation failed: {errors}")
                
            return is_valid, errors
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False, [f"Validation system error: {str(e)}"]
            
    def validate_journey_details(self, data: Dict[str, Any]) -> List[str]:
        """Validate journey-related fields"""
        errors = []
        
        # From Station
        from_station = data.get('from_station', '').strip()
        if not from_station:
            errors.append("From station is required")
        elif not self.is_valid_station_format(from_station):
            errors.append("Invalid from station format. Use: CITY NAME - CODE")
            
        # To Station
        to_station = data.get('to_station', '').strip()
        if not to_station:
            errors.append("To station is required")
        elif not self.is_valid_station_format(to_station):
            errors.append("Invalid to station format. Use: CITY NAME - CODE")
        elif from_station == to_station:
            errors.append("From and to stations cannot be the same")
            
        # Journey Date
        journey_date = data.get('journey_date', '')
        if not journey_date:
            errors.append("Journey date is required")
        else:
            date_error = self.validate_journey_date(journey_date)
            if date_error:
                errors.append(date_error)
                
        # Travel Class
        travel_class = data.get('travel_class', '')
        if not travel_class:
            errors.append("Travel class is required")
        elif travel_class not in self.valid_classes:
            errors.append(f"Invalid travel class. Valid options: {', '.join(self.valid_classes)}")
            
        # Train Number (Optional)
        train_number = data.get('train_number', '').strip()
        if train_number and not self.train_number_pattern.match(train_number):
            errors.append("Invalid train number format. Must be 5 digits")
            
        return errors
        
    def validate_passengers(self, passengers: List[Dict[str, Any]]) -> List[str]:
        """Validate passenger details"""
        errors = []
        
        if not passengers:
            errors.append("At least one passenger is required")
            return errors
            
        if len(passengers) > 6:
            errors.append("Maximum 6 passengers allowed per booking")
            
        for i, passenger in enumerate(passengers, 1):
            passenger_errors = self.validate_single_passenger(passenger, i)
            errors.extend(passenger_errors)
            
        return errors
        
    def validate_single_passenger(self, passenger: Dict[str, Any], passenger_num: int) -> List[str]:
        """Validate single passenger data"""
        errors = []
        prefix = f"Passenger {passenger_num}: "
        
        # Name
        name = passenger.get('name', '').strip()
        if not name:
            errors.append(f"{prefix}Name is required")
        elif len(name) < 2:
            errors.append(f"{prefix}Name must be at least 2 characters")
        elif len(name) > 50:
            errors.append(f"{prefix}Name must be less than 50 characters")
        elif not re.match(r'^[A-Za-z\s\.]+$', name):
            errors.append(f"{prefix}Name can only contain letters, spaces, and dots")
            
        # Age
        age = passenger.get('age')
        if not age:
            errors.append(f"{prefix}Age is required")
        else:
            try:
                age_int = int(age)
                if age_int < 1 or age_int > 120:
                    errors.append(f"{prefix}Age must be between 1 and 120")
            except (ValueError, TypeError):
                errors.append(f"{prefix}Invalid age format")
                
        # Gender
        gender = passenger.get('gender', '')
        if not gender:
            errors.append(f"{prefix}Gender is required")
        elif gender not in self.valid_genders:
            errors.append(f"{prefix}Invalid gender. Valid options: M, F, T")
            
        # Berth Preference (Optional)
        berth = passenger.get('berth_preference', '')
        if berth and berth not in self.valid_berths:
            errors.append(f"{prefix}Invalid berth preference")
            
        return errors
        
    def validate_credentials(self, credentials: Dict[str, Any]) -> List[str]:
        """Validate IRCTC login credentials"""
        errors = []
        
        # Username
        username = credentials.get('username', '').strip()
        if not username:
            errors.append("IRCTC username is required")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters")
            
        # Password
        password = credentials.get('password', '')
        if not password:
            errors.append("IRCTC password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters")
            
        return errors
        
    def validate_payment_details(self, data: Dict[str, Any]) -> List[str]:
        """Validate payment-related fields"""
        errors = []
        
        # UPI ID (Optional)
        upi_id = data.get('upi_id', '').strip()
        if upi_id and not self.upi_pattern.match(upi_id):
            errors.append("Invalid UPI ID format")
            
        # UPI Gateway (Optional)
        gateway = data.get('upi_gateway', '')
        if gateway and gateway not in self.valid_gateways:
            errors.append("Invalid UPI gateway selection")
            
        return errors
        
    def validate_journey_date(self, date_str: str) -> str:
        """Validate journey date"""
        try:
            # Parse date
            journey_date = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now().date()
            
            # Check if date is in the past
            if journey_date.date() <= today:
                return "Journey date must be in the future"
                
            # Check if date is too far in future (IRCTC allows booking up to 120 days)
            max_date = today + timedelta(days=120)
            if journey_date.date() > max_date:
                return "Journey date cannot be more than 120 days from today"
                
            # Check if it's a valid Tatkal booking date (at least tomorrow)
            tomorrow = today + timedelta(days=1)
            if journey_date.date() < tomorrow:
                return "Tatkal booking is only available from tomorrow onwards"
                
            return ""  # No error
            
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD"
            
    def is_valid_station_format(self, station: str) -> bool:
        """Check if station string matches expected format"""
        return bool(self.station_pattern.match(station.strip().upper()))
        
    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data to prevent injection attacks"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = re.sub(r'[<>"\';\\]', '', value.strip())
                sanitized[key] = sanitized_value
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    self.sanitize_input(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self.sanitize_input(value)
            else:
                sanitized[key] = value
                
        return sanitized
        
    def validate_file_upload(self, file_data: bytes, allowed_types: List[str] = None) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if allowed_types is None:
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if len(file_data) > max_size:
            return False, "File size exceeds 5MB limit"
            
        # Check file type by magic numbers
        if file_data.startswith(b'\xff\xd8\xff'):
            file_type = 'image/jpeg'
        elif file_data.startswith(b'\x89PNG\r\n\x1a\n'):
            file_type = 'image/png'
        elif file_data.startswith(b'GIF87a') or file_data.startswith(b'GIF89a'):
            file_type = 'image/gif'
        else:
            return False, "Unsupported file type"
            
        if file_type not in allowed_types:
            return False, f"File type not allowed. Supported types: {', '.join(allowed_types)}"
            
        return True, "File validation passed"

class ConfigValidator:
    """Validator for configuration files"""
    
    def __init__(self):
        self.logger = setup_logger('config_validator')
        
    def validate_passenger_config(self, config_path: str) -> Tuple[bool, List[str]]:
        """Validate passenger configuration file"""
        errors = []
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                errors.append("Configuration must be a JSON object")
                return False, errors
                
            # Validate structure
            if 'passengers' not in data:
                errors.append("Missing 'passengers' section")
                
            if 'default_preferences' not in data:
                errors.append("Missing 'default_preferences' section")
                
            # Validate passengers
            validator = BookingValidator()
            if 'passengers' in data:
                passenger_errors = validator.validate_passengers(data['passengers'])
                errors.extend(passenger_errors)
                
            return len(errors) == 0, errors
            
        except FileNotFoundError:
            return False, [f"Configuration file not found: {config_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON format: {str(e)}"]
        except Exception as e:
            return False, [f"Configuration validation error: {str(e)}"]
            
    def validate_app_config(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate application configuration"""
        errors = []
        
        required_fields = [
            'SECRET_KEY', 'HOST', 'PORT', 'IRCTC_BASE_URL',
            'PLAYWRIGHT_HEADLESS', 'LOG_LEVEL'
        ]
        
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required configuration: {field}")
                
        # Validate port
        if 'PORT' in config_data:
            try:
                port = int(config_data['PORT'])
                if port < 1 or port > 65535:
                    errors.append("PORT must be between 1 and 65535")
            except ValueError:
                errors.append("PORT must be a valid integer")
                
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if 'LOG_LEVEL' in config_data:
            if config_data['LOG_LEVEL'] not in valid_log_levels:
                errors.append(f"Invalid LOG_LEVEL. Valid options: {', '.join(valid_log_levels)}")
                
        return len(errors) == 0, errors

# Utility functions
def clean_station_name(station_input: str) -> str:
    """Clean and format station input"""
    # Remove extra spaces and convert to uppercase
    cleaned = ' '.join(station_input.strip().upper().split())
    
    # Ensure proper format (CITY - CODE)
    if ' - ' not in cleaned:
        # Try to add separator if missing
        parts = cleaned.split()
        if len(parts) >= 2:
            # Assume last part is code
            code = parts[-1]
            city = ' '.join(parts[:-1])
            cleaned = f"{city} - {code}"
            
    return cleaned

def format_passenger_name(name: str) -> str:
    """Format passenger name properly"""
    # Convert to title case and clean
    formatted = ' '.join(name.strip().title().split())
    
    # Remove multiple dots
    formatted = re.sub(r'\.{2,}', '.', formatted)
    
    return formatted

def validate_captcha_input(captcha_text: str) -> bool:
    """Basic captcha input validation"""
    if not captcha_text or len(captcha_text.strip()) < 4:
        return False
        
    # Remove spaces and check if alphanumeric
    cleaned = captcha_text.replace(' ', '')
    return cleaned.isalnum()

def validate_otp_input(otp: str) -> bool:
    """Validate OTP input"""
    return bool(otp and len(otp.strip()) == 6 and otp.strip().isdigit())