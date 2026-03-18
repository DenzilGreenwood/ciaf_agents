"""
Demo of CIAF-LCM Agentic Execution Boundaries.

This demonstrates the complete IAM/PAM/Evidence workflow with example agents and scenarios.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from dataclasses import asdict

from ciaf_agents.core import (
    Identity,
    Resource,
    ActionRequest,
    Permission,
    RoleDefinition,
)
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine
from ciaf_agents.policy.conditions import same_department_only, any_condition
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


def build_demo_system():
    """
    Build a complete demo system with IAM, PAM, Policy, Evidence, and Execution.
    
    Returns:
        Tuple of (iam_store, pam_store, evidence_vault, tool_executor)
    """
    # Initialize stores
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="super-secret-signing-key")
    policy_engine = PolicyEngine(iam=iam, pam=pam)
    executor = ToolExecutor(policy_engine=policy_engine, vault=vault, pam=pam)

    # Define roles
    agent_reader_role = RoleDefinition(
        name="agent_reader",
        permissions=[
            Permission(
                action="read_record",
                resource_type="patient_record",
                conditions=same_department_only
            ),
            Permission(
                action="send_external_email",
                resource_type="email",
                conditions=any_condition
            ),
        ],
    )

    finance_agent_role = RoleDefinition(
        name="finance_agent",
        permissions=[
            Permission(
                action="approve_payment",
                resource_type="payment",
                conditions=any_condition
            ),
        ],
    )

    ops_agent_role = RoleDefinition(
        name="ops_agent",
        permissions=[
            Permission(
                action="modify_prod_config",
                resource_type="config",
                conditions=any_condition
            ),
        ],
    )

    # Register roles
    iam.add_role(agent_reader_role)
    iam.add_role(finance_agent_role)
    iam.add_role(ops_agent_role)

    # Create agent identities
    claims_agent = Identity(
        principal_id="agent-claims-001",
        principal_type="agent",
        display_name="Claims Review Agent",
        roles={"agent_reader"},
        attributes={
            "tenant": "acme-health",
            "department": "claims",
            "allowed_email_domains": ["acme-health.com"],
        },
    )

    finance_agent = Identity(
        principal_id="agent-finance-001",
        principal_type="agent",
        display_name="Finance Approval Agent",
        roles={"finance_agent"},
        attributes={
            "tenant": "acme-health",
            "department": "finance",
        },
    )

    # Register identities
    iam.add_identity(claims_agent)
    iam.add_identity(finance_agent)

    return iam, pam, vault, executor


def run_demo():
    """Run the complete demo with various scenarios."""
    print("=" * 80)
    print("CIAF-LCM Agentic Execution Boundaries - Demo")
    print("=" * 80)
    print()

    # Build the system
    iam, pam, vault, executor = build_demo_system()

    # Get agent identities
    claims_agent = iam.identities["agent-claims-001"]
    finance_agent = iam.identities["agent-finance-001"]

    # Define resources
    patient_record = Resource(
        resource_id="patient-123",
        resource_type="patient_record",
        owner_tenant="acme-health",
        attributes={"department": "claims"},
    )

    email_resource = Resource(
        resource_id="email-outbound-001",
        resource_type="email",
        owner_tenant="acme-health",
        attributes={},
    )

    payment_resource = Resource(
        resource_id="payment-789",
        resource_type="payment",
        owner_tenant="acme-health",
        attributes={},
    )

    # Scenario 1: Allowed by IAM + policy
    print("Scenario 1: Routine action (read patient record)")
    print("-" * 80)
    req1 = ActionRequest(
        action="read_record",
        resource=patient_record,
        params={"fields": ["claim_id", "status"]},
        justification="Review open claim",
        requested_by=claims_agent,
    )
    result1 = executor.execute(req1)
    print(f"Status: {result1['status']}")
    print(f"Result: {result1.get('result', {}).get('message', result1.get('reason'))}")
    print()

    # Scenario 2: Blocked by boundary policy (domain not allowlisted)
    print("Scenario 2: Blocked by email domain policy")
    print("-" * 80)
    req2 = ActionRequest(
        action="send_external_email",
        resource=email_resource,
        params={"to": "person@gmail.com", "subject": "Claim update"},
        justification="Notify claimant",
        requested_by=claims_agent,
    )
    result2 = executor.execute(req2)
    print(f"Status: {result2['status']}")
    print(f"Reason: {result2['reason']}")
    print()

    # Scenario 3: Blocked because PAM elevation required
    print("Scenario 3: Sensitive action requires PAM elevation")
    print("-" * 80)
    req3 = ActionRequest(
        action="approve_payment",
        resource=payment_resource,
        params={"amount": 25000, "currency": "USD"},
        justification="Approve payout",
        requested_by=finance_agent,
    )
    result3 = executor.execute(req3)
    print(f"Status: {result3['status']}")
    print(f"Reason: {result3['reason']}")
    print(f"Requires Elevation: {result3['requires_elevation']}")
    print()

    # Scenario 4: Issue JIT elevation, then retry
    print("Scenario 4: Issue PAM grant and retry")
    print("-" * 80)
    grant = pam.issue_grant(
        principal_id=finance_agent.principal_id,
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Supervisor approved one-time high-value payment",
        approved_by="user-cfo-001",
        duration_minutes=15,
        ticket_id="CHG-2026-00091",
    )
    print(f"Issued Grant: {grant.grant_id}")
    print(f"Expires: {grant.expires_at}")
    print(f"Approved By: {grant.approved_by}")
    print()

    req4 = ActionRequest(
        action="approve_payment",
        resource=payment_resource,
        params={"amount": 25000, "currency": "USD"},
        justification="Approve payout after CFO approval",
        requested_by=finance_agent,
    )
    result4 = executor.execute(req4)
    print(f"Status: {result4['status']}")
    print(f"Result: {result4.get('result', {}).get('message')}")
    print()

    # Evidence chain verification
    print("=" * 80)
    print("Evidence Chain Verification")
    print("=" * 80)
    chain_valid = vault.verify_chain()
    print(f"Chain Valid: {chain_valid}")
    print(f"Total Receipts: {len(vault.receipts)}")
    print()

    # Show receipt details
    print("Receipt Summary:")
    print("-" * 80)
    for i, receipt in enumerate(vault.receipts, 1):
        print(f"{i}. {receipt.timestamp.isoformat()} | "
              f"{receipt.principal_id} | "
              f"{receipt.action} | "
              f"Decision: {receipt.decision} | "
              f"Grant: {receipt.elevation_grant_id or 'N/A'}")
    print()

    # Audit queries
    print("=" * 80)
    print("Audit Queries")
    print("=" * 80)
    
    denied_receipts = vault.get_denied_receipts()
    print(f"Denied Actions: {len(denied_receipts)}")
    for receipt in denied_receipts:
        print(f"  - {receipt.action} by {receipt.principal_id}: {receipt.reason}")
    print()

    elevated_receipts = vault.get_elevated_receipts()
    print(f"Elevated Actions: {len(elevated_receipts)}")
    for receipt in elevated_receipts:
        print(f"  - {receipt.action} by {receipt.principal_id} "
              f"(Grant: {receipt.elevation_grant_id}, Approver: {receipt.approved_by})")
    print()

    print("=" * 80)
    print("Demo Complete")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
