"""
Encryption utilities for secure credential storage
"""
from cryptography.fernet import Fernet
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Generate a key for development (in production, use AWS KMS or similar)
def get_or_create_key():
    """Get or create encryption key"""
    key_file = ".encryption_key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        # Add to .gitignore
        with open("../.gitignore", "a") as f:
            f.write("\n.encryption_key\n")
        return key

ENCRYPTION_KEY = get_or_create_key()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Encrypt AWS credentials for storage"""
    json_str = json.dumps(credentials)
    encrypted = cipher.encrypt(json_str.encode())
    return encrypted.decode()

def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
    """Decrypt AWS credentials for use"""
    decrypted = cipher.decrypt(encrypted.encode())
    return json.loads(decrypted.decode())

def test_encryption():
    """Test encryption/decryption"""
    test_creds = {
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    }
    
    encrypted = encrypt_credentials(test_creds)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = decrypt_credentials(encrypted)
    assert decrypted == test_creds
    print("✓ Encryption working correctly")

if __name__ == "__main__":
    test_encryption()
