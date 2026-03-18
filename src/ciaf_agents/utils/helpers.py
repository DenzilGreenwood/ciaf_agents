"""
Utility functions for cryptographic operations and helpers.
"""

from datetime import datetime, timezone
from typing import Any, Dict
import hashlib
import hmac
import json


def utc_now() -> datetime:
    """Get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


def canonical_json(data: Dict[str, Any]) -> str:
    """
    Convert data to canonical JSON representation.
    
    Ensures consistent serialization for hashing and signing.
    
    Args:
        data: Dictionary to serialize
        
    Returns:
        Canonical JSON string
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def sha256_hex(text: str) -> str:
    """
    Compute SHA-256 hash of text.
    
    Args:
        text: Input text to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sign_receipt(payload: Dict[str, Any], secret_key: str) -> str:
    """
    Create HMAC-SHA256 signature for a payload.
    
    Args:
        payload: Data to sign
        secret_key: Signing secret
        
    Returns:
        Hexadecimal signature string
    """
    message = canonical_json(payload).encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()
