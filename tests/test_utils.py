"""
Tests for utility functions.
"""

import pytest
from datetime import datetime, timezone

from ciaf_agents.utils.helpers import (
    utc_now,
    canonical_json,
    sha256_hex,
    sign_receipt,
)


def test_utc_now():
    """Test getting current UTC time."""
    now = utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc


def test_canonical_json():
    """Test canonical JSON serialization."""
    data = {
        "z_key": "value1",
        "a_key": "value2",
        "m_key": 123,
    }
    
    result = canonical_json(data)
    
    # Should be sorted keys, no spaces
    assert result == '{"a_key":"value2","m_key":123,"z_key":"value1"}'


def test_canonical_json_with_datetime():
    """Test canonical JSON with datetime."""
    data = {
        "timestamp": datetime(2026, 3, 18, 12, 0, 0, tzinfo=timezone.utc),
        "value": 42,
    }
    
    result = canonical_json(data)
    
    assert "timestamp" in result
    assert "value" in result
    assert "42" in result


def test_sha256_hex():
    """Test SHA-256 hashing."""
    text = "test string"
    hash1 = sha256_hex(text)
    hash2 = sha256_hex(text)
    
    # Same input should produce same hash
    assert hash1 == hash2
    
    # Should be hex string of appropriate length (64 chars for SHA-256)
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)
    
    # Different input should produce different hash
    hash3 = sha256_hex("different string")
    assert hash1 != hash3


def test_sign_receipt():
    """Test HMAC signing of receipt."""
    payload = {
        "action": "test",
        "principal": "agent-001",
        "timestamp": "2026-03-18T12:00:00Z",
    }
    
    secret = "test-secret-key"
    
    signature1 = sign_receipt(payload, secret)
    signature2 = sign_receipt(payload, secret)
    
    # Same payload and secret should produce same signature
    assert signature1 == signature2
    
    # Should be hex string of appropriate length (64 chars for HMAC-SHA256)
    assert len(signature1) == 64
    assert all(c in "0123456789abcdef" for c in signature1)
    
    # Different payload should produce different signature
    different_payload = {**payload, "action": "different"}
    signature3 = sign_receipt(different_payload, secret)
    assert signature1 != signature3
    
    # Different secret should produce different signature
    signature4 = sign_receipt(payload, "different-secret")
    assert signature1 != signature4


def test_canonical_json_deterministic():
    """Test that canonical JSON is deterministic for same data."""
    data = {
        "nested": {"z": 3, "a": 1, "m": 2},
        "list": [3, 2, 1],
        "string": "value",
    }
    
    result1 = canonical_json(data)
    result2 = canonical_json(data)
    
    assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
