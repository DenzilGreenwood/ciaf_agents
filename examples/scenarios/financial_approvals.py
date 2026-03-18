"""
Financial Payment Approvals Scenario.

Demonstrates CIAF-LCM controls for financial transactions with dual-control requirements.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ciaf_agents.core import Identity, Resource, ActionRequest, Permission, RoleDefinition
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine, same_tenant_only
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


def setup_financial_scenario():
    """
    Set up financial payment approvals with SOX compliance controls.
    
    Key controls:
    - Payments over threshold require PAM elevation
    - Dual-control for high-value transactions
    - Complete audit trail for regulatory compliance
    """
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="finance-demo-secret")
    policy = PolicyEngine(iam, pam, sensitive_actions={"approve_payment", "initiate_wire_transfer"})
    executor = ToolExecutor(policy, vault, pam)

    # Define roles
    payment_reviewer_role = RoleDefinition(
        name="payment_reviewer",
        permissions=[
            Permission("read_payment", "payment", same_tenant_only),
            Permission("approve_payment", "payment", same_tenant_only),
        ]
    )

    treasury_role = RoleDefinition(
        name="treasury_agent",
        permissions=[
            Permission("read_payment", "payment", same_tenant_only),
            Permission("approve_payment", "payment", same_tenant_only),
            Permission("initiate_wire_transfer", "wire_transfer", same_tenant_only),
        ]
    )

    iam.add_role(payment_reviewer_role)
    iam.add_role(treasury_role)

    # Create agent identities
    payment_agent = Identity(
        principal_id="agent-payment-reviewer-001",
        principal_type="agent",
        display_name="Payment Review Agent",
        roles={"payment_reviewer"},
        attributes={
            "tenant": "acme-corp",
            "department": "finance",
            "payment_limit": 5000,  # Can approve up to $5K without elevation
        }
    )

    treasury_agent = Identity(
        principal_id="agent-treasury-001",
        principal_type="agent",
        display_name="Treasury Operations Agent",
        roles={"treasury_agent"},
        attributes={
            "tenant": "acme-corp",
            "department": "treasury",
        }
    )

    iam.add_identity(payment_agent)
    iam.add_identity(treasury_agent)

    return iam, pam, vault, executor


def run_financial_scenario():
    """Run the financial payment scenario."""
    print("Financial Payment Approvals Scenario")
    print("=" * 80)
    
    iam, pam, vault, executor = setup_financial_scenario()
    
    payment_agent = iam.identities["agent-payment-reviewer-001"]
    
    # Scenario 1: Small payment (allowed)
    print("Scenario 1: Small payment approval")
    small_payment = Resource(
        resource_id="payment-2026-5432",
        resource_type="payment",
        owner_tenant="acme-corp",
        attributes={"vendor": "Office Supplies Inc"}
    )
    
    request1 = ActionRequest(
        action="approve_payment",
        resource=small_payment,
        params={"amount": 2500, "currency": "USD"},
        justification="Office supplies - approved per budget",
        requested_by=payment_agent
    )
    
    # This will be blocked because approve_payment is sensitive
    result1 = executor.execute(request1)
    print(f"Result: {result1['status']}")
    print(f"Requires elevation: {result1.get('requires_elevation')}")
    print()
    
    # Issue elevation grant
    print("Issuing PAM grant for payment approval...")
    grant = pam.issue_grant(
        principal_id=payment_agent.principal_id,
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="Daily payment processing session",
        approved_by="finance-manager@acme-corp.com",
        duration_minutes=60,
        ticket_id="SOP-DAILY-PAYMENTS"
    )
    print(f"Grant issued: {grant.grant_id}")
    print()
    
    # Retry with grant
    result1_retry = executor.execute(request1)
    print(f"Retry result: {result1_retry['status']}")
    print()
    
    # Scenario 2: Large payment (requires additional approval)
    print("Scenario 2: Large payment approval")
    large_payment = Resource(
        resource_id="payment-2026-9999",
        resource_type="payment",
        owner_tenant="acme-corp",
        attributes={"vendor": "Enterprise Software Corp"}
    )
    
    request2 = ActionRequest(
        action="approve_payment",
        resource=large_payment,
        params={"amount": 50000, "currency": "USD"},
        justification="Annual software license renewal",
        requested_by=payment_agent
    )
    
    # Even with existing grant, this will be blocked due to threshold
    result2 = executor.execute(request2)
    print(f"Result: {result2['status']}")
    print(f"Reason: {result2.get('reason')}")
    print()
    
    print("Evidence chain valid:", vault.verify_chain())
    print(f"Total receipts: {len(vault.receipts)}")


if __name__ == "__main__":
    run_financial_scenario()
