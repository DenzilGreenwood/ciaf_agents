#!/usr/bin/env python3
"""
Verify CIAF-LCM Agentic AI Installation

Run this script to verify that all components are properly installed and working.
"""

import sys
from pathlib import Path


def check_imports():
    """Check that all modules can be imported."""
    print("Testing imports...")
    errors = []
    
    try:
        from ciaf_agents.core import (
            Identity, Resource, ActionRequest, Permission, RoleDefinition,
            ElevationGrant, PolicyDecision, EvidenceReceipt
        )
        print("  ✓ Core types")
    except ImportError as e:
        errors.append(f"  ✗ Core types: {e}")
    
    try:
        from ciaf_agents.iam import IAMStore
        print("  ✓ IAM Store")
    except ImportError as e:
        errors.append(f"  ✗ IAM Store: {e}")
    
    try:
        from ciaf_agents.pam import PAMStore
        print("  ✓ PAM Store")
    except ImportError as e:
        errors.append(f"  ✗ PAM Store: {e}")
    
    try:
        from ciaf_agents.policy import PolicyEngine
        print("  ✓ Policy Engine")
    except ImportError as e:
        errors.append(f"  ✗ Policy Engine: {e}")
    
    try:
        from ciaf_agents.evidence import EvidenceVault
        print("  ✓ Evidence Vault")
    except ImportError as e:
        errors.append(f"  ✗ Evidence Vault: {e}")
    
    try:
        from ciaf_agents.execution import ToolExecutor
        print("  ✓ Tool Executor")
    except ImportError as e:
        errors.append(f"  ✗ Tool Executor: {e}")
    
    try:
        from ciaf_agents.utils.helpers import utc_now, canonical_json, sha256_hex
        print("  ✓ Utilities")
    except ImportError as e:
        errors.append(f"  ✗ Utilities: {e}")
    
    return errors


def check_functionality():
    """Basic functional test."""
    print("\nTesting basic functionality...")
    errors = []
    
    try:
        from ciaf_agents.core import Identity, Resource, ActionRequest, Permission, RoleDefinition
        from ciaf_agents.iam import IAMStore
        from ciaf_agents.pam import PAMStore
        from ciaf_agents.policy import PolicyEngine, same_tenant_only
        from ciaf_agents.evidence import EvidenceVault
        from ciaf_agents.execution import ToolExecutor
        
        # Create system
        iam = IAMStore()
        pam = PAMStore()
        vault = EvidenceVault(signing_secret="test-secret")
        policy = PolicyEngine(iam, pam)
        executor = ToolExecutor(policy, vault, pam)
        
        # Create role
        role = RoleDefinition(
            name="test_role",
            permissions=[Permission("test_action", "test_resource", same_tenant_only)]
        )
        iam.add_role(role)
        
        # Create identity
        identity = Identity(
            principal_id="test-agent",
            principal_type="agent",
            display_name="Test Agent",
            roles={"test_role"},
            attributes={"tenant": "test-tenant"}
        )
        iam.add_identity(identity)
        
        # Create request
        resource = Resource(
            resource_id="test-123",
            resource_type="test_resource",
            owner_tenant="test-tenant",
            attributes={}
        )
        
        request = ActionRequest(
            action="test_action",
            resource=resource,
            params={},
            justification="Test verification",
            requested_by=identity
        )
        
        # Test policy evaluation
        decision = policy.evaluate(request)
        if not decision.allowed:
            errors.append(f"  ✗ Policy evaluation failed: {decision.reason}")
        else:
            print("  ✓ Policy evaluation")
        
        # Test evidence recording
        receipt = vault.append(request, decision, None)
        if not vault.verify_chain():
            errors.append("  ✗ Evidence chain verification failed")
        else:
            print("  ✓ Evidence recording")
        
        # Test PAM
        grant = pam.issue_grant(
            principal_id=identity.principal_id,
            allowed_actions={"test_action"},
            resource_types={"test_resource"},
            reason="Test grant",
            approved_by="test-approver",
            duration_minutes=15,
            ticket_id="TEST-001"
        )
        if not grant.is_active():
            errors.append("  ✗ PAM grant not active")
        else:
            print("  ✓ PAM grants")
        
    except Exception as e:
        errors.append(f"  ✗ Functional test failed: {e}")
    
    return errors


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("CIAF-LCM Agentic AI Installation Verification")
    print("=" * 70)
    print()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 9):
        print("⚠ WARNING: Python 3.9 or later is recommended")
    print()
    
    # Run checks
    import_errors = check_imports()
    functional_errors = check_functionality()
    
    # Summary
    print()
    print("=" * 70)
    if not import_errors and not functional_errors:
        print("✅ ALL CHECKS PASSED")
        print()
        print("Installation verified successfully!")
        print()
        print("Next steps:")
        print("  1. Read the documentation: docs/")
        print("  2. Run the demo: python examples/demo.py")
        print("  3. Run tests: pytest tests/ -v")
        print("  4. Explore examples: examples/scenarios/")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        if import_errors:
            print("Import errors:")
            for error in import_errors:
                print(error)
        if functional_errors:
            print("\nFunctional errors:")
            for error in functional_errors:
                print(error)
        print()
        print("Installation incomplete. Please:")
        print("  1. Ensure you're in the ciaf_agents directory")
        print("  2. Run: pip install -e .")
        print("  3. Check TROUBLESHOOTING.md for help")
        return 1


if __name__ == "__main__":
    sys.exit(main())
