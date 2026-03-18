"""
Comprehensive tests for the Execution module.
"""

import pytest

from ciaf_agents.core import Identity, Resource, ActionRequest, Permission, RoleDefinition, PolicyDecision
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine, any_condition
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor, ToolRegistry


def test_tool_executor_execute_allowed_action():
    """Test executing an allowed action."""
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="test-secret")
    policy = PolicyEngine(iam, pam)
    executor = ToolExecutor(policy, vault, pam)
    
    # Setup role and identity
    role = RoleDefinition(
        name="reader",
        permissions=[Permission("read", "document", any_condition)]
    )
    iam.add_role(role)
    
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles={"reader"},
        attributes={"tenant": "test"}
    )
    iam.add_identity(identity)
    
    # Create request
    resource = Resource(
        resource_id="doc-1",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read",
        resource=resource,
        params={"field": "value"},
        justification="Test",
        requested_by=identity
    )
    
    result = executor.execute(request)
    
    assert result["status"] == "ok"
    assert "result" in result
    assert "receipt" in result
    assert result["result"]["action"] == "read"


def test_tool_executor_execute_denied_action():
    """Test executing a denied action."""
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="test-secret")
    policy = PolicyEngine(iam, pam)
    executor = ToolExecutor(policy, vault, pam)
    
    # Setup identity without permissions
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={}
    )
    iam.add_identity(identity)
    
    # Create request
    resource = Resource(
        resource_id="doc-1",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="delete",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    result = executor.execute(request)
    
    assert result["status"] == "blocked"
    assert "reason" in result
    assert "receipt" in result
    assert result["requires_elevation"] == False


def test_tool_executor_execute_sensitive_action_without_grant():
    """Test executing sensitive action without PAM grant."""
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="test-secret")
    policy = PolicyEngine(iam, pam, sensitive_actions={"delete_record"})
    executor = ToolExecutor(policy, vault, pam)
    
    # Setup role and identity
    role = RoleDefinition(
        name="deleter",
        permissions=[Permission("delete_record", "document", any_condition)]
    )
    iam.add_role(role)
    
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles={"deleter"},
        attributes={"tenant": "test"}
    )
    iam.add_identity(identity)
    
    # Create request
    resource = Resource(
        resource_id="doc-1",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="delete_record",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    result = executor.execute(request)
    
    assert result["status"] == "blocked"
    assert result["requires_elevation"] == True


def test_tool_executor_execute_batch():
    """Test batch execution."""
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="test-secret")
    policy = PolicyEngine(iam, pam)
    executor = ToolExecutor(policy, vault, pam)
    
    # Setup
    role = RoleDefinition(
        name="reader",
        permissions=[Permission("read", "document", any_condition)]
    )
    iam.add_role(role)
    
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles={"reader"},
        attributes={"tenant": "test"}
    )
    iam.add_identity(identity)
    
    # Create multiple requests
    requests = []
    for i in range(3):
        resource = Resource(
            resource_id=f"doc-{i}",
            resource_type="document",
            owner_tenant="test",
            attributes={}
        )
        
        request = ActionRequest(
            action="read",
            resource=resource,
            params={},
            justification="Batch test",
            requested_by=identity
        )
        requests.append(request)
    
    results = executor.execute_batch(requests)
    
    assert len(results) == 3
    assert all(r["status"] == "ok" for r in results)


def test_tool_executor_dry_run():
    """Test dry run without execution."""
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="test-secret")
    policy = PolicyEngine(iam, pam)
    executor = ToolExecutor(policy, vault, pam)
    
    # Setup
    role = RoleDefinition(
        name="reader",
        permissions=[Permission("read", "document", any_condition)]
    )
    iam.add_role(role)
    
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles={"reader"},
        attributes={"tenant": "test"}
    )
    iam.add_identity(identity)
    
    resource = Resource(
        resource_id="doc-1",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    # Dry run should not create receipts
    initial_receipt_count = len(vault.receipts)
    result = executor.dry_run(request)
    
    assert result["would_allow"] == True
    assert result["requires_elevation"] == False
    assert "reason" in result
    assert "matched_role" in result
    assert len(vault.receipts) == initial_receipt_count  # No new receipts


def test_tool_executor_dry_run_denied():
    """Test dry run for denied action."""
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="test-secret")
    policy = PolicyEngine(iam, pam)
    executor = ToolExecutor(policy, vault, pam)
    
    # Setup identity without permissions
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={}
    )
    iam.add_identity(identity)
    
    resource = Resource(
        resource_id="doc-1",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="delete",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    result = executor.dry_run(request)
    
    assert result["would_allow"] == False
    assert result["requires_elevation"] == False


def test_tool_registry_register_and_get():
    """Test tool registry operations."""
    registry = ToolRegistry()
    
    def mock_handler():
        return "executed"
    
    registry.register_tool("test_action", mock_handler)
    
    handler = registry.get_tool("test_action")
    assert handler is not None
    assert handler() == "executed"


def test_tool_registry_get_nonexistent():
    """Test getting a non-existent tool."""
    registry = ToolRegistry()
    
    handler = registry.get_tool("nonexistent")
    assert handler is None


def test_tool_registry_list_tools():
    """Test listing registered tools."""
    registry = ToolRegistry()
    
    registry.register_tool("action1", lambda: None)
    registry.register_tool("action2", lambda: None)
    registry.register_tool("action3", lambda: None)
    
    tools = registry.list_tools()
    assert len(tools) == 3
    assert "action1" in tools
    assert "action2" in tools
    assert "action3" in tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
