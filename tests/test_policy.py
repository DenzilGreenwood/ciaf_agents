"""
Tests for Policy Engine.
"""

import pytest

from ciaf_agents.core import Identity, Resource, ActionRequest, Permission, RoleDefinition
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine, same_tenant_only, any_condition


def setup_basic_system():
    """Setup a basic IAM/PAM/Policy system for testing."""
    iam = IAMStore()
    pam = PAMStore()
    policy = PolicyEngine(iam, pam)
    
    # Add role
    role = RoleDefinition(
        name="reader",
        permissions=[
            Permission("read_document", "document", same_tenant_only)
        ]
    )
    iam.add_role(role)
    
    # Add identity
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles={"reader"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    return iam, pam, policy


def test_policy_allows_valid_request():
    """Test that policy allows a valid request."""
    iam, pam, policy = setup_basic_system()
    
    identity = iam.identities["test-agent-001"]
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test read",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is True


def test_policy_denies_cross_tenant_access():
    """Test that policy denies cross-tenant access."""
    iam, pam, policy = setup_basic_system()
    
    identity = iam.identities["test-agent-001"]
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="tenant-b",  # Different tenant!
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test read",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is False
    # Permission with same_tenant_only condition doesn't match, so IAM denies
    assert "no matching permission" in decision.reason.lower()


def test_policy_requires_elevation_for_sensitive_action():
    """Test that sensitive actions require PAM elevation."""
    iam, pam, policy = setup_basic_system()
    
    # Add permission for sensitive action
    sensitive_role = RoleDefinition(
        name="payment_processor",
        permissions=[
            Permission("approve_payment", "payment", any_condition)
        ]
    )
    iam.add_role(sensitive_role)
    
    identity = Identity(
        principal_id="test-agent-002",
        principal_type="agent",
        display_name="Payment Agent",
        roles={"payment_processor"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    resource = Resource(
        resource_id="payment-123",
        resource_type="payment",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        action="approve_payment",
        resource=resource,
        params={"amount": 5000},
        justification="Process payment",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is False
    assert decision.requires_elevation is True


def test_policy_allows_with_active_grant():
    """Test that policy allows sensitive action with active PAM grant."""
    iam, pam, policy = setup_basic_system()
    
    # Add permission for sensitive action
    sensitive_role = RoleDefinition(
        name="payment_processor",
        permissions=[
            Permission("approve_payment", "payment", any_condition)
        ]
    )
    iam.add_role(sensitive_role)
    
    identity = Identity(
        principal_id="test-agent-002",
        principal_type="agent",
        display_name="Payment Agent",
        roles={"payment_processor"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    # Issue grant
    pam.issue_grant(
        principal_id="test-agent-002",
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Approved for payment processing",
        approved_by="manager@example.com",
        duration_minutes=15,
        ticket_id="TEST-001"
    )
    
    resource = Resource(
        resource_id="payment-123",
        resource_type="payment",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        action="approve_payment",
        resource=resource,
        params={"amount": 5000},
        justification="Process payment",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is True


def test_policy_denies_without_permission():
    """Test that policy denies actions without permission."""
    iam, pam, policy = setup_basic_system()
    
    identity = iam.identities["test-agent-001"]
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    # Try an action not in the role
    request = ActionRequest(
        action="delete_document",
        resource=resource,
        params={},
        justification="Delete document",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is False
    assert "no matching permission" in decision.reason.lower()


def test_policy_email_domain_allowlist():
    """Test email domain allowlist enforcement."""
    iam,pam, policy = setup_basic_system()
    
    # Add email permission
    email_role = RoleDefinition(
        name="emailer",
        permissions=[
            Permission("send_external_email", "email", any_condition)
        ]
    )
    iam.add_role(email_role)
    
    identity = Identity(
        principal_id="test-agent-email",
        principal_type="agent",
        display_name="Email Agent",
        roles={"emailer"},
        attributes={
            "tenant": "tenant-a",
            "allowed_email_domains": ["example.com", "test.com"]
        }
    )
    iam.add_identity(identity)
    
    # Mark as sensitive
    policy.add_sensitive_action("send_external_email")
    
    resource = Resource(
        resource_id="email-1",
        resource_type="email",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    # Test with allowed domain
    request1 = ActionRequest(
        action="send_external_email",
        resource=resource,
        params={"to": "user@example.com"},
        justification="Send email",
        requested_by=identity
    )
    
    # Issue grant first
    grant = pam.issue_grant(
        principal_id=identity.principal_id,
        allowed_actions={"send_external_email"},
        resource_types={"email"},
        reason="Email batch",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="EMAIL-001"
    )
    
    decision1 = policy.evaluate(request1)
    assert decision1.allowed is True
    
    # Test with disallowed domain
    request2 = ActionRequest(
        action="send_external_email",
        resource=resource,
        params={"to": "user@blocked.com"},
        justification="Send email",
        requested_by=identity
    )
    
    decision2 = policy.evaluate(request2)
    assert decision2.allowed is False
    assert "domain outside allowlist" in decision2.reason.lower()


def test_policy_payment_threshold():
    """Test payment amount threshold enforcement."""
    iam, pam, policy = setup_basic_system()
    
    # Add payment role
    payment_role = RoleDefinition(
        name="payment_approver",
        permissions=[
            Permission("approve_payment", "payment", any_condition)
        ]
    )
    iam.add_role(payment_role)
    
    identity = Identity(
        principal_id="test-payment-agent",
        principal_type="agent",
        display_name="Payment Agent",
        roles={"payment_approver"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    # Mark as sensitive
    policy.add_sensitive_action("approve_payment")
    
    resource = Resource(
        resource_id="payment-1",
        resource_type="payment",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    # Issue grant for sensitive action
    grant = pam.issue_grant(
        principal_id=identity.principal_id,
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Payment approval",
        approved_by="manager",
        duration_minutes=15,
        ticket_id="PAY-001"
    )
    
    # Test small payment (should work with grant)
    request1 = ActionRequest(
        action="approve_payment",
        resource=resource,
        params={"amount": 5000},
        justification="Small payment",
        requested_by=identity
    )
    
    decision1 = policy.evaluate(request1)
    assert decision1.allowed is True
    
    # Test large payment over threshold (needs additional elevation)
    request2 = ActionRequest(
        action="approve_payment",
        resource=resource,
        params={"amount": 15000},
        justification="Large payment",
        requested_by=identity
    )
    
    decision2 = policy.evaluate(request2)
    # Current grant covers it, but adds obligation
    assert decision2.allowed is True
    assert "two_person_review_verified" in decision2.obligations


def test_policy_sensitive_action_management():
    """Test adding and removing sensitive actions."""
    iam, pam, policy = setup_basic_system()
    
    # Add sensitive action
    policy.add_sensitive_action("custom_action")
    assert policy.is_sensitive_action("custom_action")
    
    # Remove sensitive action
    policy.remove_sensitive_action("custom_action")
    assert not policy.is_sensitive_action("custom_action")


def test_policy_with_no_roles():
    """Test policy evaluation with identity that has no roles."""
    iam, pam, policy = setup_basic_system()
    
    identity = Identity(
        principal_id="no-role-agent",
        principal_type="agent",
        display_name="No Role Agent",
        roles=set(),  # No roles
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is False
    assert decision.matched_role is None


def test_default_sensitive_actions():
    """Test that PolicyEngine has default sensitive actions when none provided."""
    iam = IAMStore()
    pam = PAMStore()
    
    # Create without specifying any sensitive actions
    engine = PolicyEngine(iam=iam, pam=pam)
    
    # Should have defaults
    assert "delete_record" in engine.sensitive_actions
    assert "approve_payment" in engine.sensitive_actions
    assert len(engine.sensitive_actions) > 0


def test_policy_with_privileged_actions():
    """Test PolicyEngine with privileged_actions parameter."""
    iam = IAMStore()
    pam = PAMStore()
    
    # Create with privileged_actions
    engine = PolicyEngine(
        iam=iam, 
        pam=pam,
        privileged_actions={"privileged_action_1", "privileged_action_2"}
    )
    
    # Should include privileged actions
    assert "privileged_action_1" in engine.sensitive_actions
    assert "privileged_action_2" in engine.sensitive_actions


def test_permission_condition_returns_false():
    """Test permission with a condition that returns False."""
    iam, pam, policy = setup_basic_system()
    
    # Create identity without 'department' attribute
    identity = Identity(
        principal_id="test_user",
        principal_type="user",
        display_name="Test User",
        roles={"finance_viewer"},  # Add role immediately
        attributes={}  # No department attribute
    )
    iam.add_identity(identity)
    
    # Add role with condition that checks for department
    def requires_department(identity, resource, params):
        return identity.attributes.get("department") == "finance"
    
    permission = Permission(
        action="view_record",
        resource_type="record",
        conditions=requires_department
    )
    
    finance_role = RoleDefinition(
        name="finance_viewer",
        permissions=[permission]
    )
    iam.add_role(finance_role)
    
    resource = Resource(
        resource_id="rec-123",
        resource_type="record",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        action="view_record",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert not decision.allowed
    assert "no matching permission" in decision.reason.lower()


def test_high_value_payment_without_elevation():
    """Test high-value payment requiring elevation when no grant exists."""
    iam, pam, policy = setup_basic_system()
    
    # Add payment role
    payment_role = RoleDefinition(
        name="payment_processor",
        permissions=[
            Permission("approve_payment", "payment", any_condition)
        ]
    )
    iam.add_role(payment_role)
    
    identity = Identity(
        principal_id="test-payment-agent",
        principal_type="agent",
        display_name="Payment Agent",
        roles={"payment_processor"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    # Remove approve_payment from sensitive actions temporarily
    # so we can test the threshold-specific logic
    policy.remove_sensitive_action("approve_payment")
    
    # Create a payment resource
    payment_resource = Resource(
        resource_id="payment_9999",
        resource_type="payment",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        requested_by=identity,
        action="approve_payment",
        resource=payment_resource,
        params={"amount": "15000"},  # Above 10000 threshold
        justification="High value payment"
    )
    
    decision = policy.evaluate(request)
    assert not decision.allowed
    assert decision.requires_elevation
    assert "threshold" in decision.reason.lower()


def test_permission_without_conditions():
    """Test permission with no conditions (conditions=None)."""
    iam, pam, policy = setup_basic_system()
    
    # Create a permission without conditions (not using any_condition)
    permission = Permission(
        action="unrestricted_action",
        resource_type="document",
        conditions=None  # No conditions
    )
    
    role = RoleDefinition(
        name="unrestricted_role",
        permissions=[permission]
    )
    iam.add_role(role)
    
    identity = Identity(
        principal_id="unrestricted_agent",
        principal_type="agent",
        display_name="Unrestricted Agent",
        roles={"unrestricted_role"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        action="unrestricted_action",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is True


def test_policy_cross_tenant_boundary():
    """Test that policy-level cross-tenant boundary is enforced."""
    iam, pam, policy = setup_basic_system()
    
    # Create a permission with any_condition (no IAM-level tenant check)
    role = RoleDefinition(
        name="cross_tenant_reader",
        permissions=[
            Permission("read_data", "data", any_condition)
        ]
    )
    iam.add_role(role)
    
    # Identity with tenant-a
    identity = Identity(
        principal_id="agent-tenant-a",
        principal_type="agent",
        display_name="Agent A",
        roles={"cross_tenant_reader"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    # Resource owned by tenant-b
    resource = Resource(
        resource_id="data-123",
        resource_type="data",
        owner_tenant="tenant-b",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_data",
        resource=resource,
        params={},
        justification="Cross-tenant read",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is False
    assert "cross-tenant" in decision.reason.lower()


def test_permission_resource_type_mismatch():
    """Test permission doesn't match when resource type differs."""
    iam, pam, policy = setup_basic_system()
    
    # Create a permission for "document" resource type
    permission = Permission(
        action="read_data",
        resource_type="document",  # Specific type
        conditions=None
    )
    
    role = RoleDefinition(
        name="doc_reader",
        permissions=[permission]
    )
    iam.add_role(role)
    
    identity = Identity(
        principal_id="reader_agent",
        principal_type="agent",
        display_name="Reader",
        roles={"doc_reader"},
        attributes={"tenant": "tenant-a"}
    )
    iam.add_identity(identity)
    
    # Resource with different type
    resource = Resource(
        resource_id="data-123",
        resource_type="database",  # Different type!
        owner_tenant="tenant-a",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_data",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = policy.evaluate(request)
    assert decision.allowed is False
    assert "no matching permission" in decision.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
