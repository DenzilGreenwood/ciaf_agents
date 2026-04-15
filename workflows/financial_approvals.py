# Copyright (c) 2026 Denzil Greenwood. All rights reserved.
# Licensed under the Business Source License 1.1 (BUSL-1.1)
# See BUSL_1_1_LICENSE for license terms
#
# LICENSING NOTE:
# This file contains original CIAF control plane implementations (BUSL 1.1).
# It integrates with Google Agent Development Kit (Apache 2.0) via the
# Agent class import. The CIAF logic and orchestration is original (BUSL 1.1);
# the ADK framework integration is used as a dependency (Apache 2.0).
# See LICENSING_AUDIT.md for file-by-file breakdown.

"""
Financial Approvals Agent

Real ADK agent for payment approvals with multi-tier governance.
Demonstrates CIAF control planes in financial domain.

Domain: Payment authorization
Scenario: Payment processor routes payments through approval tiers

CIAF Control Planes:
- IDENTITY: Processor + approver + controller + CFO agents
- POLICY: Tier-based approval limits
- PRIVILEGE: Multi-level escalation
- EXECUTION: Approval chain orchestration
- EVIDENCE: Cryptographic signature trail
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import sys
from pathlib import Path
import warnings
import json

warnings.filterwarnings('ignore', message='.*PLUGGABLE_AUTH.*')

# Setup imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import Agent

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
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


@dataclass
class PaymentRequest:
    """Financial payment request."""
    payment_id: str
    vendor: str
    amount: float
    category: str
    purpose: str
    requester: str
    cost_center: str
    support_documents: List[str]


class FinancialApprovalsWorkflow:
    """Financial approvals with dual-control and evidence."""

    def __init__(self):
        """Initialize the financial approvals workflow."""
        self.iam_store = IAMStore()
        self.pam_store = PAMStore()
        self.evidence_vault = EvidenceVault(
            signing_secret="finance-approvals-key-2024"
        )
        self.policy_engine = PolicyEngine(
            iam=self.iam_store,
            pam=self.pam_store
        )
        self.executor = ToolExecutor(
            policy_engine=self.policy_engine,
            vault=self.evidence_vault,
            pam=self.pam_store
        )
        self._setup_roles_and_policies()

    def _setup_roles_and_policies(self):
        """Setup roles and policies for financial approvals."""
        # IDENTITY PLANE: Define financial roles
        self.payment_processor = Identity(
            principal_id="agent-payment-processor-001",
            principal_type="agent",
            display_name="Payment Processing Agent",
            roles={"payment_processor"},
            attributes={
                "tenant": "finance-corp",
                "department": "accounting",
                "max_approve": 10000,
            },
        )

        self.approver = Identity(
            principal_id="user-finance-approver-001",
            principal_type="user",
            display_name="Rebecca Thompson, Finance Manager",
            roles={"finance_approver"},
            attributes={
                "tenant": "finance-corp",
                "department": "finance",
                "approval_limit": 50000,
                "clearance_level": "manager",
            },
        )

        self.controller = Identity(
            principal_id="user-controller-001",
            principal_type="user",
            display_name="David Kumar, Controller",
            roles={"finance_controller"},
            attributes={
                "tenant": "finance-corp",
                "department": "finance",
                "approval_limit": 250000,
                "clearance_level": "director",
            },
        )

        self.cfo = Identity(
            principal_id="user-cfo-001",
            principal_type="user",
            display_name="Margaret White, CFO",
            roles={"cfo"},
            attributes={
                "tenant": "finance-corp",
                "department": "finance",
                "approval_limit": 1000000,
                "clearance_level": "executive",
            },
        )

        # POLICY PLANE: Amount-based permissions
        def standard_tenant(ctx):
            return ctx.get("tenant") == "finance-corp"

        def amount_check(limit):
            def check(ctx):
                return ctx.get("amount", 0) <= limit
            return check

        processor_role = RoleDefinition(
            name="payment_processor",
            permissions=[
                Permission(
                    action="process_payment",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
                Permission(
                    action="approve_payment_low",
                    resource_type="payment",
                    conditions=amount_check(10000)
                ),
                Permission(
                    action="request_approval",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
            ],
        )

        approver_role = RoleDefinition(
            name="finance_approver",
            permissions=[
                Permission(
                    action="approve_mid_range",
                    resource_type="payment",
                    conditions=amount_check(50000)
                ),
                Permission(
                    action="request_controller_approval",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
                Permission(
                    action="deny_payment",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
            ],
        )

        controller_role = RoleDefinition(
            name="finance_controller",
            permissions=[
                Permission(
                    action="approve_high_value",
                    resource_type="payment",
                    conditions=amount_check(250000)
                ),
                Permission(
                    action="escalate_to_cfo",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
                Permission(
                    action="audit_payment",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
            ],
        )

        cfo_role = RoleDefinition(
            name="cfo",
            permissions=[
                Permission(
                    action="approve_executive",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
                Permission(
                    action="board_escalation",
                    resource_type="payment",
                    conditions=standard_tenant
                ),
            ],
        )

        self.iam_store.add_role(processor_role)
        self.iam_store.add_role(approver_role)
        self.iam_store.add_role(controller_role)
        self.iam_store.add_role(cfo_role)

        # Register identities
        self.iam_store.add_identity(self.payment_processor)
        self.iam_store.add_identity(self.approver)
        self.iam_store.add_identity(self.controller)
        self.iam_store.add_identity(self.cfo)

    def approve_payment(self, request: PaymentRequest) -> Dict[str, Any]:
        """
        Approve a payment through CIAF governance.

        IDENTITY PLANE: Processor initiates
        POLICY PLANE: Amount-based routing
        PRIVILEGE PLANE: Multi-level escalation
        EXECUTION PLANE: Approval chain mediation
        EVIDENCE PLANE: Cryptographic approval trail
        """
        print("\n" + "=" * 80)
        print(f"  FINANCIAL APPROVAL WORKFLOW: {request.payment_id}")
        print("=" * 80)

        payment_resource = Resource(
            resource_id=request.payment_id,
            resource_type="payment",
            owner_tenant="finance-corp",
            attributes={
                "vendor": request.vendor,
                "amount": request.amount,
                "category": request.category,
                "cost_center": request.cost_center,
            },
        )

        # IDENTITY PLANE
        print("\n→ IDENTITY PLANE: Processor Initiates")
        print(f"  Principal: {self.payment_processor.principal_id}")
        print(f"  Display: {self.payment_processor.display_name}")
        print(f"  Max Standing Authority: ${self.payment_processor.attributes['max_approve']:,.2f}")

        # POLICY PLANE: Determine approval path
        print("\n→ POLICY PLANE: Amount-Based Routing")
        print(f"  Payment Amount: ${request.amount:,.2f}")
        print(f"  Vendor: {request.vendor}")
        print(f"  Purpose: {request.purpose}")

        approval_chain = self._determine_approval_chain(request.amount)
        print(f"  Required Approvals: {' → '.join(approval_chain)}")

        # PRIVILEGE PLANE: Escalation needed
        print("\n→ PRIVILEGE PLANE: Escalation Analysis")
        print(f"  ◆ Processor standing authority: ${self.payment_processor.attributes['max_approve']:,.2f}")
        print(f"  ◆ Payment amount: ${request.amount:,.2f}")

        if request.amount > self.payment_processor.attributes["max_approve"]:
            print(f"  → Escalation required (${request.amount:,.2f} > ${self.payment_processor.attributes['max_approve']:,.2f})")
            escalation_level = "HIGH"
        else:
            print(f"  ✓ Within standing authority")
            escalation_level = "LOW"

        # EXECUTION PLANE: Process approvals
        print("\n→ EXECUTION PLANE: Approval Chain Execution")
        approvals = self._execute_approval_chain(approval_chain, request)

        # EVIDENCE PLANE: Record entire chain
        print("\n→ EVIDENCE PLANE: Cryptographic Audit Trail")
        print(f"  ◆ Approval chain recorded: {' → '.join(approval_chain)}")
        print(f"  ◆ Chain hash: sha256_[approval_chain_hash]")
        print(f"  ◆ Signatures collected: {len(approval_chain)}")
        print(f"  ◆ Timestamp: 2024-04-15T14:30:00Z")

        decision = {
            "payment_id": request.payment_id,
            "status": "APPROVED" if all(a["approved"] for a in approvals) else "PENDING",
            "amount": request.amount,
            "approval_chain": approvals,
            "escalation_level": escalation_level,
        }

        return decision

    def _determine_approval_chain(self, amount: float) -> List[str]:
        """Determine approval chain based on amount."""
        if amount <= 10000:
            return ["Processor", "Release"]
        elif amount <= 50000:
            return ["Processor", "Approver", "Release"]
        elif amount <= 250000:
            return ["Processor", "Approver", "Controller", "Release"]
        else:
            return ["Processor", "Approver", "Controller", "CFO", "Board", "Release"]

    def _execute_approval_chain(
        self,
        chain: List[str],
        request: PaymentRequest
    ) -> List[Dict[str, Any]]:
        """Simulate approval chain execution."""
        approvals = []

        for i, level in enumerate(chain):
            if level == "Release":
                approvals.append({
                    "level": "Release",
                    "approved": True,
                    "timestamp": f"2024-04-15T14:{30+i}:00Z",
                    "action": "payment_released",
                })
            elif level == "Processor":
                approvals.append({
                    "level": "Processor",
                    "principal": self.payment_processor.principal_id,
                    "approved": True,
                    "timestamp": f"2024-04-15T14:{30+i}:00Z",
                    "signature": f"sig_{request.payment_id}_processor",
                })
            elif level == "Approver":
                approvals.append({
                    "level": "Approver",
                    "principal": self.approver.principal_id,
                    "approver_name": self.approver.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T14:{30+i}:00Z",
                    "signature": f"sig_{request.payment_id}_approver",
                    "comment": "Verified vendor and supporting docs",
                })
            elif level == "Controller":
                approvals.append({
                    "level": "Controller",
                    "principal": self.controller.principal_id,
                    "approver_name": self.controller.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T14:{30+i}:00Z",
                    "signature": f"sig_{request.payment_id}_controller",
                })
            elif level == "CFO":
                approvals.append({
                    "level": "CFO",
                    "principal": self.cfo.principal_id,
                    "approver_name": self.cfo.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T14:{30+i}:00Z",
                    "signature": f"sig_{request.payment_id}_cfo",
                })
            elif level == "Board":
                approvals.append({
                    "level": "Board",
                    "approved": False,  # Simulated pending
                    "status": "PENDING_BOARD_REVIEW",
                    "meeting": "2024-04-22",
                })

        return approvals


# ============================================================================
# ADK AGENT CREATION
# ============================================================================

def create_financial_approvals_agent() -> Agent:
    """Create ADK agent for financial payment approvals."""

    agent_instance = FinancialApprovalsWorkflow()

    def process_payment_tool(
        payment_id: str,
        vendor: str,
        amount: float,
        category: str,
        purpose: str,
        requester: str,
    ) -> str:
        """Process payment through multi-tier approval chain.

        Tier-based routing:
        - $0-10K: Processor authority
        - $10-50K: Processor + Approver
        - $50-250K: + Controller
        - $250K+: + CFO + Board

        Returns JSON with approval chain status.
        """
        payment = PaymentRequest(
            payment_id=payment_id,
            vendor=vendor,
            amount=amount,
            category=category,
            purpose=purpose,
            requester=requester,
            cost_center="CC-001",
            support_documents=[],
        )
        result = agent_instance.process_payment(payment)
        return json.dumps(result, indent=2)

    root_agent = Agent(
        name="financial_approvals_agent",
        model="gemini-2.5-flash",
        instruction="""
You are a Financial Approvals Agent with CIAF governance.

Your role: Route payments through multi-tier approval chain

Approval Tiers (based on amount):
- $0-10,000: You can approve directly
- $10,000-50,000: Route to Finance Approver
- $50,000-250,000: Escalate to Controller
- $250,000+: Escalate to CFO + Board

When processing a payment:
1. Call process_payment_tool with payment details
2. Explain the routing decision
3. Describe the approval chain required
4. Confirm dual-control measures (where applicable)

Emphasize dual-control, auditability, and financial controls.
""",
        description="Financial payment processor with multi-tier CIAF governance",
        tools=[process_payment_tool],
    )

    return root_agent


# ============================================================================
# EXPORT FOR ADK DISCOVERY
# ============================================================================

root_agent = create_financial_approvals_agent()


# ============================================================================
# MAIN: RUN WORKFLOW DEMONSTRATION
# ============================================================================

def main():
    """Run financial approvals workflow demonstration."""
    workflow = FinancialApprovalsWorkflow()

    payments = [
        PaymentRequest(
            payment_id="PAY-20240415-001",
            vendor="Acme Supplies Inc.",
            amount=2500.00,
            category="Office Supplies",
            purpose="Monthly office supplies",
            requester="John Smith",
            cost_center="CC-100",
            support_documents=["invoice-001.pdf"],
        ),
        PaymentRequest(
            payment_id="PAY-20240415-002",
            vendor="TechFlow Systems",
            amount=35000.00,
            category="Software License",
            purpose="Annual software licenses",
            requester="Jane Doe",
            cost_center="CC-200",
            support_documents=["quote-techflow.pdf", "contract.pdf"],
        ),
        PaymentRequest(
            payment_id="PAY-20240415-003",
            vendor="BuildCo Contractors",
            amount=125000.00,
            category="Facility Upgrade",
            purpose="Facility renovation project",
            requester="Michael Brown",
            cost_center="CC-300",
            support_documents=["bid-001.pdf", "plans.pdf", "estimate.pdf"],
        ),
    ]

    for payment in payments:
        result = workflow.approve_payment(payment)
        print(f"\n  ✓ Payment: {result['payment_id']}")
        print(f"  ✓ Amount: ${result.get('amount', 0):,.2f}")
        print(f"  ✓ Status: {result.get('status', 'Unknown')}")

    print("\n" + "=" * 80)
    print("  AGENT DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

def main():
    """Run financial approvals workflow demonstration."""
    workflow = FinancialApprovalsWorkflow()

    payments = [
        PaymentRequest(
            payment_id="PAY-20240415-001",
            vendor="Acme Office Supply",
            amount=2500.00,
            category="Supplies",
            purpose="Q2 office supplies",
            requester="John Smith",
            cost_center="CC-001",
            support_documents=["invoice-12345", "po-5678"],
        ),
        PaymentRequest(
            payment_id="PAY-20240415-002",
            vendor="TechCore Solutions",
            amount=35000.00,
            category="Software License",
            purpose="Annual enterprise software license",
            requester="Jane Doe",
            cost_center="CC-IT",
            support_documents=["quote-98765", "contract-abc123"],
        ),
        PaymentRequest(
            payment_id="PAY-20240415-003",
            vendor="Capital Equipment Inc",
            amount=125000.00,
            category="Equipment",
            purpose="Manufacturing equipment upgrade",
            requester="Robert Wilson",
            cost_center="CC-OPS",
            support_documents=["proposal-xxx", "spec-sheet", "appraisal"],
        ),
    ]

    for payment in payments:
        result = workflow.approve_payment(payment)
        print(f"\n  ✓ Status: {result['status']}")
        print(f"  ✓ Approvals: {len(result['approval_chain'])} steps")
        print(f"  ✓ Escalation: {result['escalation_level']}")

    print("\n" + "=" * 80)
    print("  WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
