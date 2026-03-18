"""
Tests for IAM module.
"""

import pytest

from ciaf_agents.core import Identity, Permission, RoleDefinition
from ciaf_agents.iam import IAMStore
from ciaf_agents.policy.conditions import any_condition


def test_iam_store_initialization():
    """Test IAM store can be initialized."""
    iam = IAMStore()
    assert len(iam.identities) == 0
    assert len(iam.role_definitions) == 0


def test_add_role():
    """Test adding a role definition."""
    iam = IAMStore()
    role = RoleDefinition(
        name="test_role",
        permissions=[
            Permission("read", "document", any_condition)
        ]
    )
    iam.add_role(role)
    assert "test_role" in iam.role_definitions


def test_add_identity():
    """Test adding an identity."""
    iam = IAMStore()
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles={"reader"},
        attributes={"tenant": "test"}
    )
    iam.add_identity(identity)
    assert "test-agent-001" in iam.identities


def test_get_identity_permissions():
    """Test retrieving permissions for an identity."""
    iam = IAMStore()
    
    # Create role
    role = RoleDefinition(
        name="reader",
        permissions=[
            Permission("read", "document", any_condition),
            Permission("list", "document", any_condition),
        ]
    )
    iam.add_role(role)
    
    # Create identity
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles={"reader"},
        attributes={}
    )
    iam.add_identity(identity)
    
    # Get permissions
    permissions = iam.get_identity_permissions(identity)
    assert len(permissions) == 2
    assert all(role_name == "reader" for role_name, _ in permissions)


def test_revoke_identity():
    """Test revoking an identity."""
    iam = IAMStore()
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    iam.add_identity(identity)
    assert "test-agent-001" in iam.identities
    
    iam.revoke_identity("test-agent-001")
    assert "test-agent-001" not in iam.identities


def test_update_identity_roles():
    """Test updating an identity's roles."""
    iam = IAMStore()
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles={"reader"},
        attributes={}
    )
    iam.add_identity(identity)
    
    iam.update_identity_roles("test-agent-001", {"reader", "writer"})
    updated = iam.identities["test-agent-001"]
    assert updated.roles == {"reader", "writer"}


def test_get_identity():
    """Test getting an identity by ID."""
    iam = IAMStore()
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles={"reader"},
        attributes={}
    )
    iam.add_identity(identity)
    
    retrieved = iam.get_identity("test-agent-001")
    assert retrieved.principal_id == "test-agent-001"
    assert retrieved.display_name == "Test Agent"


def test_get_identity_not_found():
    """Test getting a non-existent identity."""
    iam = IAMStore()
    
    with pytest.raises(KeyError):
        iam.get_identity("nonexistent-agent")


def test_list_identities_by_role():
    """Test listing identities by role."""
    iam = IAMStore()
    
    # Add multiple identities with different roles
    identity1 = Identity(
        principal_id="agent-001",
        principal_type="agent",
        display_name="Agent 1",
        roles={"reader", "writer"},
        attributes={}
    )
    
    identity2 = Identity(
        principal_id="agent-002",
        principal_type="agent",
        display_name="Agent 2",
        roles={"reader"},
        attributes={}
    )
    
    identity3 = Identity(
        principal_id="agent-003",
        principal_type="agent",
        display_name="Agent 3",
        roles={"admin"},
        attributes={}
    )
    
    iam.add_identity(identity1)
    iam.add_identity(identity2)
    iam.add_identity(identity3)
    
    # Get identities with 'reader' role
    readers = iam.list_identities_by_role("reader")
    assert len(readers) == 2
    assert all("reader" in i.roles for i in readers)
    
    # Get identities with 'admin' role
    admins = iam.list_identities_by_role("admin")
    assert len(admins) == 1
    assert admins[0].principal_id == "agent-003"


def test_get_identity_permissions_with_no_roles():
    """Test getting permissions for identity with no matching roles."""
    iam = IAMStore()
    
    # Add identity with role that doesn't exist
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles={"nonexistent_role"},
        attributes={}
    )
    iam.add_identity(identity)
    
    permissions = iam.get_identity_permissions(identity)
    assert len(permissions) == 0


def test_update_identity_roles_nonexistent():
    """Test updating roles for nonexistent identity."""
    iam = IAMStore()
    
    with pytest.raises(KeyError):
        iam.update_identity_roles("nonexistent-agent", {"new_role"})


def test_revoke_nonexistent_identity():
    """Test revoking an identity that doesn't exist."""
    iam = IAMStore()
    
    # Should not raise error, just do nothing
    iam.revoke_identity("nonexistent-agent")
    assert "nonexistent-agent" not in iam.identities


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
