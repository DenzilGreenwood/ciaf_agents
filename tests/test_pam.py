"""
Tests for PAM module.
"""

import pytest
from datetime import timedelta

from ciaf_agents.pam import PAMStore
from ciaf_agents.utils.helpers import utc_now


def test_pam_store_initialization():
    """Test PAM store can be initialized."""
    pam = PAMStore()
    assert len(pam.grants) == 0


def test_issue_grant():
    """Test issuing an elevation grant."""
    pam = PAMStore()
    grant = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Test approval",
        approved_by="manager@example.com",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    assert grant.principal_id == "test-agent-001"
    assert "approve_payment" in grant.allowed_actions
    assert grant.is_active()


def test_find_active_grant():
    """Test finding an active grant."""
    pam = PAMStore()
    grant = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Test approval",
        approved_by="manager@example.com",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    found = pam.find_active_grant("test-agent-001", "approve_payment", "payment")
    assert found is not None
    assert found.grant_id == grant.grant_id


def test_find_active_grant_not_found():
    """Test finding a grant that doesn't exist."""
    pam = PAMStore()
    found = pam.find_active_grant("test-agent-001", "approve_payment", "payment")
    assert found is None


def test_revoke_grant():
    """Test revoking a grant."""
    pam = PAMStore()
    grant = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Test approval",
        approved_by="manager@example.com",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    result = pam.revoke_grant(grant.grant_id)
    assert result is True
    assert grant.grant_id not in pam.grants


def test_revoke_all_grants_for_principal():
    """Test revoking all grants for a principal."""
    pam = PAMStore()
    
    # Issue multiple grants
    pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Test 1",
        approved_by="manager@example.com",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"delete_record"},
        resource_types={"document"},
        reason="Test 2",
        approved_by="manager@example.com",
        duration_minutes=15,
        ticket_id="TEST-002"
    )
    
    count = pam.revoke_all_grants_for_principal("test-agent-001")
    assert count == 2
    assert len(pam.grants) == 0


def test_extend_grant():
    """Test extending a grant's expiration."""
    pam = PAMStore()
    grant = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Test approval",
        approved_by="manager@example.com",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    original_expiry = grant.expires_at
    result = pam.extend_grant(grant.grant_id, 10)
    
    assert result is True
    extended_grant = pam.grants[grant.grant_id]
    assert extended_grant.expires_at > original_expiry


def test_cleanup_expired_grants():
    """Test cleaning up expired grants."""
    pam = PAMStore()
    
    # Issue a grant with 0 duration (immediately expired)
    grant1 = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"action1"},
        resource_types={"resource1"},
        reason="Test",
        approved_by="manager",
        duration_minutes=0,
        ticket_id="TEST-001"
    )
    
    # Issue a normal grant
    grant2 = pam.issue_grant(
        principal_id="test-agent-002",
        allowed_actions={"action2"},
        resource_types={"resource2"},
        reason="Test",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="TEST-002"
    )
    
    # Cleanup should remove expired grant
    removed_count = pam.cleanup_expired_grants()
    assert removed_count == 1
    assert grant1.grant_id not in pam.grants
    assert grant2.grant_id in pam.grants


def test_get_active_grants_for_principal():
    """Test getting all active grants for a principal."""
    pam = PAMStore()
    
    # Issue multiple grants for same principal
    grant1 = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"action1"},
        resource_types={"resource1"},
        reason="Test 1",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    grant2 = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"action2"},
        resource_types={"resource2"},
        reason="Test 2",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="TEST-002"
    )
    
    # Issue grant for different principal
    grant3 = pam.issue_grant(
        principal_id="test-agent-002",
        allowed_actions={"action3"},
        resource_types={"resource3"},
        reason="Test 3",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="TEST-003"
    )
    
    # Get grants for test-agent-001
    grants = pam.get_active_grants_for_principal("test-agent-001")
    assert len(grants) == 2
    assert all(g.principal_id == "test-agent-001" for g in grants)


def test_revoke_nonexistent_grant():
    """Test revoking a grant that doesn't exist."""
    pam = PAMStore()
    result = pam.revoke_grant("nonexistent-grant-id")
    assert result is False


def test_extend_nonexistent_grant():
    """Test extending a grant that doesn't exist."""
    pam = PAMStore()
    result = pam.extend_grant("nonexistent-grant-id", 10)
    assert result is False


def test_find_grant_wrong_action():
    """Test finding a grant with wrong action."""
    pam = PAMStore()
    grant = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"action1"},
        resource_types={"resource1"},
        reason="Test",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    # Try to find with different action
    found = pam.find_active_grant("test-agent-001", "action2", "resource1")
    assert found is None


def test_find_grant_wrong_resource_type():
    """Test finding a grant with wrong resource type."""
    pam = PAMStore()
    grant = pam.issue_grant(
        principal_id="test-agent-001",
        allowed_actions={"action1"},
        resource_types={"resource1"},
        reason="Test",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    # Try to find with different resource type
    found = pam.find_active_grant("test-agent-001", "action1", "resource2")
    assert found is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
