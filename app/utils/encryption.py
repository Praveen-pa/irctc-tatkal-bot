"""
IRCTC Tatkal Automation Bot - Encryption Utilities
"""

from cryptography.fernet import Fernet
import base64
import json
import os
from pathlib import Path
import hashlib
from utils.logging import setup_logger

class CredentialManager:
    """Secure credential storage and management"""
    
    def __init__(self, encryption_key=None):
        self.logger = setup_logger('credential_manager')
        
        if encryption_key:
            # Use provided key
            self.key = encryption_key.encode()[:32].ljust(32, b'0')  # Ensure 32 bytes
            self.cipher_suite = Fernet(base64.urlsafe_b64encode(self.key))
        else:
            # Generate new key
            self.key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.key)
    
    def encrypt_credentials(self, credentials):
        """
        Encrypt user credentials
        
        Args:
            credentials (dict): Dictionary containing username, password, etc.
            
        Returns:
            str: Encrypted credentials string
        """
        try:
            # Convert credentials to JSON string
            creds_json = json.dumps(credentials)
            
            # Encrypt the JSON string
            encrypted_data = self.cipher_suite.encrypt(creds_json.encode())
            
            # Return base64 encoded string for storage
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            self.logger.error(f"Error encrypting credentials: {str(e)}")
            raise
    
    def decrypt_credentials(self, encrypted_credentials):
        """
        Decrypt user credentials
        
        Args:
            encrypted_credentials (str): Encrypted credentials string
            
        Returns:
            dict: Decrypted credentials dictionary
        """
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_credentials.encode())
            
            # Decrypt the data
            decrypted_json = self.cipher_suite.decrypt(encrypted_data)
            
            # Parse JSON and return
            return json.loads(decrypted_json.decode())
            
        except Exception as e:
            self.logger.error(f"Error decrypting credentials: {str(e)}")
            raise
    
    def save_encrypted_credentials(self, credentials, filepath):
        """
        Save encrypted credentials to file
        
        Args:
            credentials (dict): Credentials to encrypt and save
            filepath (str): Path to save the encrypted file
        """
        try:
            # Encrypt credentials
            encrypted_data = self.encrypt_credentials(credentials)
            
            # Save to file
            with open(filepath, 'w') as f:
                f.write(encrypted_data)
                
            self.logger.info(f"Credentials saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving credentials: {str(e)}")
            raise
    
    def load_encrypted_credentials(self, filepath):
        """
        Load and decrypt credentials from file
        
        Args:
            filepath (str): Path to the encrypted credentials file
            
        Returns:
            dict: Decrypted credentials
        """
        try:
            # Load encrypted data from file
            with open(filepath, 'r') as f:
                encrypted_data = f.read().strip()
            
            # Decrypt and return
            return self.decrypt_credentials(encrypted_data)
            
        except FileNotFoundError:
            self.logger.error(f"Credentials file not found: {filepath}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            raise
    
    def get_key_string(self):
        """Get the encryption key as a string (for storage in environment variables)"""
        return base64.b64encode(self.key).decode()

class SecureStorage:
    """Secure storage for sensitive application data"""
    
    def __init__(self, storage_dir="config", encryption_key=None):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.credential_manager = CredentialManager(encryption_key)
        self.logger = setup_logger('secure_storage')
    
    def save_user_data(self, user_id, data):
        """
        Save encrypted user data
        
        Args:
            user_id (str): Unique user identifier
            data (dict): User data to encrypt and save
        """
        try:
            # Create user-specific filename
            filename = self._get_user_filename(user_id)
            filepath = self.storage_dir / filename
            
            # Encrypt and save
            self.credential_manager.save_encrypted_credentials(data, filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving user data: {str(e)}")
            raise
    
    def load_user_data(self, user_id):
        """
        Load and decrypt user data
        
        Args:
            user_id (str): Unique user identifier
            
        Returns:
            dict: Decrypted user data
        """
        try:
            # Create user-specific filename
            filename = self._get_user_filename(user_id)
            filepath = self.storage_dir / filename
            
            # Load and decrypt
            return self.credential_manager.load_encrypted_credentials(filepath)
            
        except Exception as e:
            self.logger.error(f"Error loading user data: {str(e)}")
            raise
    
    def user_data_exists(self, user_id):
        """Check if user data file exists"""
        filename = self._get_user_filename(user_id)
        filepath = self.storage_dir / filename
        return filepath.exists()
    
    def delete_user_data(self, user_id):
        """Delete user data file"""
        try:
            filename = self._get_user_filename(user_id)
            filepath = self.storage_dir / filename
            
            if filepath.exists():
                filepath.unlink()
                self.logger.info(f"User data deleted for: {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error deleting user data: {str(e)}")
            raise
    
    def _get_user_filename(self, user_id):
        """Generate secure filename for user data"""
        # Hash the user ID for security
        hash_object = hashlib.sha256(user_id.encode())
        return f"user_{hash_object.hexdigest()[:16]}.enc"

def generate_encryption_key():
    """Generate a new encryption key"""
    key = Fernet.generate_key()
    return base64.b64encode(key).decode()

def validate_credentials(credentials):
    """
    Validate credential format and requirements
    
    Args:
        credentials (dict): Credentials to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['username', 'password']
    
    # Check required fields
    for field in required_fields:
        if field not in credentials:
            return False, f"Missing required field: {field}"
        
        if not credentials[field] or not credentials[field].strip():
            return False, f"Empty value for field: {field}"
    
    # Validate username format (IRCTC usernames)
    username = credentials['username'].strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    # Validate password strength
    password = credentials['password']
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    return True, "Valid credentials"

# Example usage and testing functions
def test_encryption():
    """Test encryption functionality"""
    print("Testing encryption functionality...")
    
    # Create credential manager
    cm = CredentialManager()
    
    # Test credentials
    test_creds = {
        "username": "test_user",
        "password": "test_password_123",
        "upi_id": "test@upi"
    }
    
    try:
        # Encrypt
        encrypted = cm.encrypt_credentials(test_creds)
        print(f"Encrypted: {encrypted[:50]}...")
        
        # Decrypt
        decrypted = cm.decrypt_credentials(encrypted)
        print(f"Decrypted: {decrypted}")
        
        # Verify
        assert decrypted == test_creds
        print("✅ Encryption test passed!")
        
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")

if __name__ == "__main__":
    test_encryption()