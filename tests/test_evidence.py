"""
Tests for Evidence Vault.
"""

import pytest

from ciaf_agents.core import Identity, Resource, ActionRequest, PolicyDecision
from ciaf_agents.evidence import EvidenceVault


def test_evidence_vault_initialization():
    """Test evidence vault can be initialized."""
    vault = EvidenceVault(signing_secret="test-secret")
    assert len(vault.receipts) == 0


def test_append_receipt():
    """Test appending a receipt to the vault."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = PolicyDecision(
        allowed=True,
        requires_elevation=False,
        reason="Test decision"
    )
    
    receipt = vault.append(request, decision, None)
    
    assert receipt is not None
    assert receipt.principal_id == "test-agent-001"
    assert receipt.action == "read_document"
    assert receipt.decision == "allow"
    assert len(vault.receipts) == 1


def test_verify_chain():
    """Test verifying the receipt chain."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    # Add multiple receipts
    for i in range(3):
        resource = Resource(
            resource_id=f"doc-{i}",
            resource_type="document",
            owner_tenant="test",
            attributes={}
        )
        
        request = ActionRequest(
            action="read_document",
            resource=resource,
            params={},
            justification="Test",
            requested_by=identity
        )
        
        decision = PolicyDecision(
            allowed=True,
            requires_elevation=False,
            reason="Test"
        )
        
        vault.append(request, decision, None)
    
    # Verify chain
    assert vault.verify_chain() is True


def test_get_receipts_by_principal():
    """Test getting receipts by principal ID."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity1 = Identity(
        principal_id="agent-001",
        principal_type="agent",
        display_name="Agent 1",
        roles=set(),
        attributes={}
    )
    
    identity2 = Identity(
        principal_id="agent-002",
        principal_type="agent",
        display_name="Agent 2",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    # Add receipts for different agents
    for identity in [identity1, identity2, identity1]:
        request = ActionRequest(
            action="read_document",
            resource=resource,
            params={},
            justification="Test",
            requested_by=identity
        )
        
        decision = PolicyDecision(
            allowed=True,
            requires_elevation=False,
            reason="Test"
        )
        
        vault.append(request, decision, None)
    
    agent1_receipts = vault.get_receipts_by_principal("agent-001")
    assert len(agent1_receipts) == 2
    
    agent2_receipts = vault.get_receipts_by_principal("agent-002")
    assert len(agent2_receipts) == 1


def test_get_denied_receipts():
    """Test getting denied receipts."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    # Add allowed and denied receipts
    for allowed in [True, False, True]:
        request = ActionRequest(
            action="read_document",
            resource=resource,
            params={},
            justification="Test",
            requested_by=identity
        )
        
        decision = PolicyDecision(
            allowed=allowed,
            requires_elevation=False,
            reason="Test"
        )
        
        vault.append(request, decision, None)
    
    denied = vault.get_denied_receipts()
    assert len(denied) == 1


def test_verify_receipt():
    """Test verifying a single receipt."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = PolicyDecision(
        allowed=True,
        requires_elevation=False,
        reason="Test"
    )
    
    receipt = vault.append(request, decision, None)
    
    assert vault.verify_receipt(receipt) is True


def test_get_receipts_by_action():
    """Test getting receipts by action."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    # Add receipts with different actions
    for action in ["read", "write", "read"]:
        resource = Resource(
            resource_id="doc-123",
            resource_type="document",
            owner_tenant="test",
            attributes={}
        )
        
        request = ActionRequest(
            action=action,
            resource=resource,
            params={},
            justification="Test",
            requested_by=identity
        )
        
        decision = PolicyDecision(
            allowed=True,
            requires_elevation=False,
            reason="Test"
        )
        
        vault.append(request, decision, None)
    
    read_receipts = vault.get_receipts_by_action("read")
    assert len(read_receipts) == 2
    
    write_receipts = vault.get_receipts_by_action("write")
    assert len(write_receipts) == 1


def test_get_elevated_receipts():
    """Test getting receipts that used privilege elevation."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    from ciaf_agents.pam import PAMStore
    pam = PAMStore()
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    # Add receipts with and without grants
    for i, has_grant in enumerate([True, False, True]):
        request = ActionRequest(
            action="read",
            resource=resource,
            params={},
            justification="Test",
            requested_by=identity
        )
        
        decision = PolicyDecision(
            allowed=True,
            requires_elevation=False,
            reason="Test"
        )
        
        grant = None
        if has_grant:
            grant = pam.issue_grant(
                principal_id=identity.principal_id,
                allowed_actions={"read"},
                resource_types={"document"},
                reason="Test",
                approved_by="manager",
                duration_minutes=15,
                ticket_id=f"TEST-{i}"
            )
        
        vault.append(request, decision, grant)
    
    elevated = vault.get_elevated_receipts()
    assert len(elevated) == 2


def test_export_receipts():
    """Test exporting receipts as dictionaries."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    # Add a few receipts
    for i in range(3):
        request = ActionRequest(
            action="read",
            resource=resource,
            params={"index": i},
            justification="Test",
            requested_by=identity
        )
        
        decision = PolicyDecision(
            allowed=True,
            requires_elevation=False,
            reason="Test"
        )
        
        vault.append(request, decision, None)
    
    exported = vault.export_receipts()
    
    assert len(exported) == 3
    assert all(isinstance(r, dict) for r in exported)
    assert all("receipt_id" in r for r in exported)
    assert all("signature" in r for r in exported)


def test_receipt_to_dict():
    """Test converting receipt to dictionary."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={"field": "value"},
        justification="Test",
        requested_by=identity
    )
    
    decision = PolicyDecision(
        allowed=True,
        requires_elevation=False,
        reason="Test decision",
        matched_role="reader",
        obligations=["log_action"]
    )
    
    receipt = vault.append(request, decision, None)
    receipt_dict = receipt.to_dict()
    
    assert isinstance(receipt_dict, dict)
    assert receipt_dict["receipt_id"] == receipt.receipt_id
    assert receipt_dict["principal_id"] == "test-agent-001"
    assert receipt_dict["action"] == "read_document"
    assert receipt_dict["decision"] == "allow"
    assert receipt_dict["policy_obligations"] == ["log_action"]


def test_verify_chain_with_invalid_hash():
    """Test chain verification fails with tampered hash."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = PolicyDecision(
        allowed=True,
        requires_elevation=False,
        reason="Test"
    )
    
    receipt = vault.append(request, decision, None)
    
    # Tamper with the receipt hash
    receipt.receipt_hash = "tampered_hash"
    
    # Verification should fail
    assert vault.verify_chain() is False


def test_verify_chain_with_invalid_signature():
    """Test chain verification fails with tampered signature."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = PolicyDecision(
        allowed=True,
        requires_elevation=False,
        reason="Test"
    )
    
    receipt = vault.append(request, decision, None)
    
    # Tamper with the signature
    receipt.signature = "tampered_signature"
    
    # Verification should fail
    assert vault.verify_chain() is False


def test_verify_chain_with_broken_link():
    """Test chain verification fails with broken chain link."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    # Add two receipts
    for i in range(2):
        request = ActionRequest(
            action="read_document",
            resource=resource,
            params={},
            justification="Test",
            requested_by=identity
        )
        
        decision = PolicyDecision(
            allowed=True,
            requires_elevation=False,
            reason="Test"
        )
        
        vault.append(request, decision, None)
    
    # Break the chain link
    vault.receipts[1].prior_receipt_hash = "broken_link"
    
    # Verification should fail
    assert vault.verify_chain() is False


def test_verify_receipt_with_invalid_hash():
    """Test single receipt verification fails with invalid hash."""
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision = PolicyDecision(
        allowed=True,
        requires_elevation=False,
        reason="Test"
    )
    
    receipt = vault.append(request, decision, None)
    
    # Tamper with the receipt hash
    receipt.receipt_hash = "tampered"
    
    # Single receipt verification should fail
    assert vault.verify_receipt(receipt) is False


def test_verify_chain_with_valid_hash_invalid_prior_link():
    """Test chain verification fails when prior_receipt_hash is wrong but hash is valid."""
    from ciaf_agents.utils.helpers import sha256_hex, canonical_json, sign_receipt, utc_now
    from ciaf_agents.core.types import EvidenceReceipt
    from datetime import datetime
    
    vault = EvidenceVault(signing_secret="test-secret")
    
    identity = Identity(
        principal_id="test-agent-001",
        principal_type="agent",
        display_name="Test Agent",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="doc-123",
        resource_type="document",
        owner_tenant="test",
        attributes={}
    )
    
    # Add first receipt
    request1 = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=identity
    )
    
    decision1 = PolicyDecision(
        allowed=True,
        requires_elevation=False,
        reason="Test"
    )
    
    receipt1 = vault.append(request1, decision1, None)
    
    # Manually create a second receipt with wrong prior_receipt_hash
    # but valid hash and signature for that wrong prior value
    wrong_prior = "wrong_prior_hash"
    
    payload2 = {
        "receipt_id": "receipt-2",
        "timestamp": utc_now().isoformat(),
        "principal_id": identity.principal_id,
        "principal_type": identity.principal_type,
        "action": "read_document",
        "resource_id": resource.resource_id,
        "resource_type": resource.resource_type,
        "correlation_id": "corr-2",
        "decision": "allow",
        "reason": "Test",
        "elevation_grant_id": None,
        "approved_by": None,
        "params_hash": sha256_hex(canonical_json({})),
        "policy_obligations": [],
        "prior_receipt_hash": wrong_prior,  # Wrong prior hash!
    }
    
    # Create valid hash and signature for this wrong payload
    receipt_hash2 = sha256_hex(canonical_json(payload2))
    signature2 = sign_receipt(
        {**payload2, "receipt_hash": receipt_hash2},
        "test-secret"
    )
    
    receipt2 = EvidenceReceipt(
        receipt_id="receipt-2",
        timestamp=datetime.fromisoformat(payload2["timestamp"]),
        principal_id=identity.principal_id,
        principal_type=identity.principal_type,
        action="read_document",
        resource_id=resource.resource_id,
        resource_type=resource.resource_type,
        correlation_id="corr-2",
        decision="allow",
        reason="Test",
        elevation_grant_id=None,
        approved_by=None,
        params_hash=payload2["params_hash"],
        policy_obligations=[],
        prior_receipt_hash=wrong_prior,
        receipt_hash=receipt_hash2,
        signature=signature2
    )
    
    vault.receipts.append(receipt2)
    
    # Chain verification should fail at the chain link check
    assert vault.verify_chain() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
