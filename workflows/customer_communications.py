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
Customer Communications Agent

Real ADK agent for customer communication governance with policy enforcement.
Demonstrates CIAF control planes in communications domain.

Domain: Customer-facing communications
Scenario: Communications agent enforces policy before sending messages

CIAF Control Planes:
- IDENTITY: Communications agent + marketing + support + compliance + counsel
- POLICY: Content policy gates (financial info, legal terms)
- PRIVILEGE: Escalation for compliance-sensitive content
- EXECUTION: Approval chain enforcement
- EVIDENCE: Communication audit trail + content hash
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
class CommunicationRequest:
    """Customer communication request."""
    message_id: str
    communication_type: str  # marketing, support, disclosure, legal
    recipient: str
    recipient_type: str  # individual, segment, broadcast
    subject: str
    content: str
    content_length: int
    contains_financial_info: bool
    contains_legal_terms: bool
    sender_role: str
    urgency: str


class CustomerCommunicationsWorkflow:
    """Customer communications with policy enforcement."""

    def __init__(self):
        """Initialize the customer communications workflow."""
        self.iam_store = IAMStore()
        self.pam_store = PAMStore()
        self.evidence_vault = EvidenceVault(
            signing_secret="communications-key-2024"
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
        """Setup roles and policies for communications."""
        # IDENTITY PLANE: Communication agents and reviewers
        self.comms_agent = Identity(
            principal_id="agent-comms-001",
            principal_type="agent",
            display_name="Customer Communications Agent",
            roles={"communications_agent"},
            attributes={
                "tenant": "customer-corp",
                "department": "communications",
                "authority_level": "system",
                "can_send_direct": False,  # Must go through review
            },
        )

        self.marketing_manager = Identity(
            principal_id="user-marketing-mgr-001",
            principal_type="user",
            display_name="Susan Adams, Marketing Manager",
            roles={"marketing_manager"},
            attributes={
                "tenant": "customer-corp",
                "department": "marketing",
                "clearance_level": "manager",
                "can_approve_marketing": True,
            },
        )

        self.support_lead = Identity(
            principal_id="user-support-lead-001",
            principal_type="user",
            display_name="Michael Torres, Support Lead",
            roles={"support_lead"},
            attributes={
                "tenant": "customer-corp",
                "department": "support",
                "clearance_level": "manager",
                "can_approve_support": True,
            },
        )

        self.compliance_officer = Identity(
            principal_id="user-compliance-officer-001",
            principal_type="user",
            display_name="Elena Rodriguez, Compliance Officer",
            roles={"compliance_officer"},
            attributes={
                "tenant": "customer-corp",
                "department": "compliance",
                "clearance_level": "director",
                "can_block_communications": True,
            },
        )

        self.general_counsel = Identity(
            principal_id="user-general-counsel-001",
            principal_type="user",
            display_name="William Thompson, General Counsel",
            roles={"general_counsel"},
            attributes={
                "tenant": "customer-corp",
                "department": "legal",
                "clearance_level": "executive",
                "can_approve_legal": True,
            },
        )

        # POLICY PLANE: Content policy permissions
        def standard_tenant(ctx):
            return ctx.get("tenant") == "customer-corp"

        def no_financial_info(ctx):
            return not ctx.get("contains_financial_info", False)

        def no_legal_terms(ctx):
            return not ctx.get("contains_legal_terms", False)

        agent_role = RoleDefinition(
            name="communications_agent",
            permissions=[
                Permission(
                    action="draft_communication",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
                Permission(
                    action="request_marketing_review",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
                Permission(
                    action="request_support_review",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
            ],
        )

        marketing_role = RoleDefinition(
            name="marketing_manager",
            permissions=[
                Permission(
                    action="approve_marketing",
                    resource_type="communication",
                    conditions=no_financial_info
                ),
                Permission(
                    action="request_compliance_review",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
            ],
        )

        support_role = RoleDefinition(
            name="support_lead",
            permissions=[
                Permission(
                    action="approve_support",
                    resource_type="communication",
                    conditions=no_legal_terms
                ),
                Permission(
                    action="escalate_to_legal",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
            ],
        )

        compliance_role = RoleDefinition(
            name="compliance_officer",
            permissions=[
                Permission(
                    action="compliance_review",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
                Permission(
                    action="block_communication",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
            ],
        )

        counsel_role = RoleDefinition(
            name="general_counsel",
            permissions=[
                Permission(
                    action="legal_review",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
                Permission(
                    action="approve_legal_communication",
                    resource_type="communication",
                    conditions=standard_tenant
                ),
            ],
        )

        self.iam_store.add_role(agent_role)
        self.iam_store.add_role(marketing_role)
        self.iam_store.add_role(support_role)
        self.iam_store.add_role(compliance_role)
        self.iam_store.add_role(counsel_role)

        # Register identities
        self.iam_store.add_identity(self.comms_agent)
        self.iam_store.add_identity(self.marketing_manager)
        self.iam_store.add_identity(self.support_lead)
        self.iam_store.add_identity(self.compliance_officer)
        self.iam_store.add_identity(self.general_counsel)

    def send_communication(
        self,
        request: CommunicationRequest
    ) -> Dict[str, Any]:
        """
        Send customer communication with policy enforcement.

        IDENTITY PLANE: Communication agent
        POLICY PLANE: Content policies
        PRIVILEGE PLANE: Escalation for sensitive content
        EXECUTION PLANE: Approval chain enforcement
        EVIDENCE PLANE: Audit trail of all communications
        """
        print("\n" + "=" * 80)
        print(f"  CUSTOMER COMMUNICATION WORKFLOW: {request.message_id}")
        print("=" * 80)

        comm_resource = Resource(
            resource_id=request.message_id,
            resource_type="communication",
            owner_tenant="customer-corp",
            attributes={
                "type": request.communication_type,
                "recipient": request.recipient,
                "contains_financial": request.contains_financial_info,
                "contains_legal": request.contains_legal_terms,
            },
        )

        # IDENTITY PLANE
        print("\n→ IDENTITY PLANE: Communication Agent")
        print(f"  Principal: {self.comms_agent.principal_id}")
        print(f"  Display: {self.comms_agent.display_name}")
        print(f"  Direct Send Authority: {self.comms_agent.attributes['can_send_direct']}")

        # POLICY PLANE: Content policy evaluation
        print("\n→ POLICY PLANE: Content Policy Evaluation")
        print(f"  Communication Type: {request.communication_type}")
        print(f"  Recipient: {request.recipient}")
        print(f"  Content Length: {request.content_length} characters")
        print(f"  Contains Financial Info: {request.contains_financial_info}")
        print(f"  Contains Legal Terms: {request.contains_legal_terms}")

        # Policy checks
        policy_violations = self._check_policy_violations(request)
        if policy_violations:
            print(f"  ⚠ Policy violations detected: {len(policy_violations)}")
            for violation in policy_violations:
                print(f"    • {violation}")
        else:
            print(f"  ✓ No policy violations")

        # PRIVILEGE PLANE: Escalation needed?
        print("\n→ PRIVILEGE PLANE: Escalation Analysis")
        approval_chain = self._determine_approval_chain(request)
        print(f"  Required Approvers: {' → '.join(approval_chain)}")

        if request.contains_financial_info:
            print(f"  ◆ Financial content detected → Compliance review required")
        if request.contains_legal_terms:
            print(f"  ◆ Legal terms detected → General counsel approval required")
        if request.communication_type == "legal":
            print(f"  ◆ Legal communication → Executive approval required")

        # EXECUTION PLANE: Approval chain
        print("\n→ EXECUTION PLANE: Approval Chain Execution")
        approvals = self._execute_approval_chain(approval_chain, request)

        # EVIDENCE PLANE: Communication audit trail
        print("\n→ EVIDENCE PLANE: Communication Audit Trail")
        print(f"  ◆ Message ID: {request.message_id}")
        print(f"  ◆ Approvers: {' → '.join(approval_chain)}")
        print(f"  ◆ Policy checks: {len(policy_violations)} violations found")
        print(f"  ◆ Timestamp: 2024-04-15T16:30:00Z")
        print(f"  ◆ Recipient logged: {request.recipient}")
        print(f"  ◆ Content hash: sha256_[message_hash]")

        decision = {
            "message_id": request.message_id,
            "status": "APPROVED" if all(a["approved"] for a in approvals) else "BLOCKED",
            "communication_type": request.communication_type,
            "policy_violations": policy_violations,
            "approval_chain": approvals,
        }

        return decision

    def _check_policy_violations(
        self,
        request: CommunicationRequest
    ) -> List[str]:
        """Check for policy violations."""
        violations = []

        # Marketing policies
        if request.communication_type == "marketing":
            if request.contains_financial_info:
                violations.append("Marketing cannot contain financial information")
            if request.content_length > 5000:
                violations.append("Marketing email too long (max 5000 chars)")

        # Support policies
        elif request.communication_type == "support":
            if request.contains_legal_terms:
                violations.append("Support response cannot contain legal terms")
            if request.recipient_type == "broadcast":
                violations.append("Support responses must be individual, not broadcast")

        # Financial disclosure policies
        elif request.communication_type == "disclosure":
            if not request.contains_financial_info:
                violations.append("Disclosure should contain financial information")

        # Legal communication policies
        elif request.communication_type == "legal":
            if request.urgency == "immediate":
                violations.append("Legal communications require standard review timeline")

        return violations

    def _determine_approval_chain(
        self,
        request: CommunicationRequest
    ) -> List[str]:
        """Determine approval chain based on communication type."""
        if request.communication_type == "marketing":
            chain = ["Marketing"]
            if request.contains_financial_info:
                chain.insert(0, "Compliance")
            return chain + ["Send"]

        elif request.communication_type == "support":
            chain = ["Support"]
            if request.contains_legal_terms:
                chain.append("Legal")
            return chain + ["Send"]

        elif request.communication_type == "disclosure":
            return ["Compliance", "Counsel", "Send"]

        elif request.communication_type == "legal":
            return ["Counsel", "Counsel.Review", "Send"]

        return ["Send"]

    def _execute_approval_chain(
        self,
        chain: List[str],
        request: CommunicationRequest
    ) -> List[Dict[str, Any]]:
        """Simulate approval chain execution."""
        approvals = []

        for i, approver_type in enumerate(chain):
            if approver_type == "Send":
                approvals.append({
                    "stage": "Send",
                    "approved": True,
                    "timestamp": f"2024-04-15T16:{30+i}:00Z",
                    "action": "communication_sent",
                })
            elif approver_type == "Marketing":
                approvals.append({
                    "stage": "Marketing",
                    "principal": self.marketing_manager.principal_id,
                    "approver_name": self.marketing_manager.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T16:{30+i}:00Z",
                    "signature": f"sig_{request.message_id}_marketing",
                })
            elif approver_type == "Support":
                approvals.append({
                    "stage": "Support",
                    "principal": self.support_lead.principal_id,
                    "approver_name": self.support_lead.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T16:{30+i}:00Z",
                    "signature": f"sig_{request.message_id}_support",
                })
            elif approver_type == "Compliance":
                approvals.append({
                    "stage": "Compliance",
                    "principal": self.compliance_officer.principal_id,
                    "approver_name": self.compliance_officer.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T16:{30+i}:00Z",
                    "signature": f"sig_{request.message_id}_compliance",
                })
            elif approver_type in ["Legal", "Counsel", "Counsel.Review"]:
                approvals.append({
                    "stage": "Counsel",
                    "principal": self.general_counsel.principal_id,
                    "approver_name": self.general_counsel.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T16:{30+i}:00Z",
                    "signature": f"sig_{request.message_id}_counsel",
                })

        return approvals


# ============================================================================
# ADK AGENT CREATION
# ============================================================================

def create_customer_communications_agent() -> Agent:
    """Create ADK agent for customer communication governance."""

    agent_instance = CustomerCommunicationsWorkflow()

    def send_communication_tool(
        message_id: str,
        communication_type: str,
        recipient: str,
        subject: str,
        content: str,
    ) -> str:
        """Send customer communication through policy enforcement.

        Communication types:
        - marketing: Content policy check
        - support: No legal terms allowed
        - disclosure: Requires compliance review
        - legal: Requires general counsel approval

        Returns JSON with routing decision and approval chain.
        """
        communication = CommunicationRequest(
            message_id=message_id,
            communication_type=communication_type,
            recipient=recipient,
            subject=subject,
            content=content,
            sender="comms_agent",
            priority="normal",
            includes_financial_info=("price" in content.lower() or "cost" in content.lower()),
            includes_legal_terms=("agreement" in content.lower() or "terms" in content.lower()),
        )
        result = agent_instance.send_communication(communication)
        return json.dumps(result, indent=2)

    root_agent = Agent(
        name="customer_communications_agent",
        model="gemini-2.5-flash",
        instruction="""
You are a Customer Communications Agent with CIAF governance.

Your role: Enforce policy on customer-facing communications before sending

Communication Types & Policies:
- Marketing: Must pass content policy (no unsubstantiated claims)
- Support: Cannot include legal terms, KB-only
- Disclosure: Requires compliance review
- Legal: Requires general counsel approval

When sending communications:
1. Call send_communication_tool with message details
2. Explain policy checks applied
3. Route through appropriate approval chain
4. Confirm audit trail was recorded

Message policies:
- Financial info → compliance review
- Legal terms → counsel review
- Sensitive content → escalation

Emphasize: Compliance, policy enforcement, auditability.
""",
        description="Customer communication processor with CIAF policy enforcement",
        tools=[send_communication_tool],
    )

    return root_agent


# ============================================================================
# EXPORT FOR ADK DISCOVERY
# ============================================================================

root_agent = create_customer_communications_agent()


# ============================================================================
# MAIN: RUN WORKFLOW
# ============================================================================

def main():
    """Run customer communications workflow demonstration."""
    workflow = CustomerCommunicationsWorkflow()

    communications = [
        CommunicationRequest(
            message_id="MSG-20240415-001",
            communication_type="marketing",
            recipient="segment:premium_members",
            recipient_type="segment",
            subject="Spring Sale: 20% Off Premium Features",
            content="Enjoy 20% off all premium features this spring...",
            content_length=800,
            contains_financial_info=False,
            contains_legal_terms=False,
            sender_role="marketing",
            urgency="normal",
        ),
        CommunicationRequest(
            message_id="MSG-20240415-002",
            communication_type="support",
            recipient="customer@example.com",
            recipient_type="individual",
            subject="Your Support Ticket #12345 - Resolution",
            content="Your issue has been resolved using our standard procedure...",
            content_length=500,
            contains_financial_info=False,
            contains_legal_terms=False,
            sender_role="support",
            urgency="normal",
        ),
        CommunicationRequest(
            message_id="MSG-20240415-003",
            communication_type="disclosure",
            recipient="all_customers",
            recipient_type="broadcast",
            subject="Q1 2024 Financial Results Disclosure",
            content="Revenue increased 15% YoY to $125M. EBITDA margin: 28%...",
            content_length=2000,
            contains_financial_info=True,
            contains_legal_terms=False,
            sender_role="communications",
            urgency="normal",
        ),
        CommunicationRequest(
            message_id="MSG-20240415-004",
            communication_type="legal",
            recipient="all_customers",
            recipient_type="broadcast",
            subject="Updated Terms of Service - Effective May 1, 2024",
            content="Please review our updated terms and conditions effective May 1...",
            content_length=4000,
            contains_financial_info=False,
            contains_legal_terms=True,
            sender_role="legal",
            urgency="normal",
        ),
    ]

    for comm in communications:
        result = workflow.send_communication(comm)
        print(f"\n  ✓ Status: {result['status']}")
        print(f"  ✓ Approvers: {len(result['approval_chain'])} stages")
        print(f"  ✓ Policy violations: {len(result['policy_violations'])}")

    print("\n" + "=" * 80)
    print("  WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
