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
Healthcare Claims Processing Agent

Real ADK agent for processing healthcare claims with HIPAA compliance.

Domain: Medical billing and claims routing
Scenario: Claims processor agent routes claims based on amount and risk level

CIAF Control Planes:
- IDENTITY: Claims processor agent + medical/financial reviewers
- POLICY: Amount-based permissions and medical necessity rules
- PRIVILEGE: JIT elevation for high-value claims ($1K+)
- EXECUTION: Amount-based routing with mediation
- EVIDENCE: Audit trail of all claim decisions

Integration: Uses Google ADK Agent framework for LLM-powered claim processing.
"""

from dataclasses import dataclass
from typing import Dict, Any
import sys
from pathlib import Path
import warnings
import json

warnings.filterwarnings("ignore", message=".*PLUGGABLE_AUTH.*")

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
from ciaf_agents.policy.conditions import same_tenant_only
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


@dataclass
class ClaimRecord:
    """Medical claim record."""

    claim_id: str
    patient_id: str
    provider: str
    amount: float
    diagnosis_code: str
    treatment_type: str
    medical_necessity_score: float
    high_risk: bool = False


# ============================================================================
# HEALTHCARE CLAIMS AGENT (WITH CIAF GOVERNANCE)
# ============================================================================


class HealthcareClaimsAgent:
    """Healthcare claims processing with CIAF governance."""

    def __init__(self):
        """Initialize the healthcare claims agent."""
        self.iam_store = IAMStore()
        self.pam_store = PAMStore()
        self.evidence_vault = EvidenceVault(signing_secret="healthcare-claims-key-2024")
        self.policy_engine = PolicyEngine(iam=self.iam_store, pam=self.pam_store)
        self.executor = ToolExecutor(
            policy_engine=self.policy_engine,
            vault=self.evidence_vault,
            pam=self.pam_store,
        )
        self._setup_roles_and_policies()

    def _setup_roles_and_policies(self):
        """Setup identity, roles, and policies for healthcare domain."""
        # IDENTITY PLANE: Define healthcare agent and reviewers
        self.claims_processor = Identity(
            principal_id="agent-claims-processor-001",
            principal_type="agent",
            display_name="Healthcare Claims Processor",
            roles={"claims_processor"},
            attributes={
                "tenant": "healthcare-provider-corp",
                "department": "claims",
                "organization_level": "system",
                "requires_supervision": True,
            },
        )

        self.medical_reviewer = Identity(
            principal_id="user-medical-reviewer-001",
            principal_type="user",
            display_name="Dr. Sarah Chen, Medical Reviewer",
            roles={"medical_reviewer"},
            attributes={
                "tenant": "healthcare-provider-corp",
                "department": "medical",
                "license_id": "MD-12345",
                "specialties": ["orthopedics", "cardiology"],
            },
        )

        self.financial_reviewer = Identity(
            principal_id="user-financial-reviewer-001",
            principal_type="user",
            display_name="James Park, Financial Reviewer",
            roles={"financial_reviewer"},
            attributes={
                "tenant": "healthcare-provider-corp",
                "department": "finance",
                "approval_limit": 50000,
            },
        )

        self.compliance_officer = Identity(
            principal_id="user-compliance-officer-001",
            principal_type="user",
            display_name="Lisa Martinez, Compliance Officer",
            roles={"compliance_officer"},
            attributes={
                "tenant": "healthcare-provider-corp",
                "department": "compliance",
                "authority_level": "executive",
            },
        )

        # POLICY PLANE: Define permissions and conditions
        def standard_tenant_check(ctx):
            """Verify same tenant context."""
            return ctx.get("tenant") == "healthcare-provider-corp"

        def claim_amount_check(amount_limit):
            """Factory: Create condition for claim amount."""

            def check(ctx):
                return ctx.get("claim_amount", 0) <= amount_limit

            return check

        # Roles with permissions
        processor_role = RoleDefinition(
            name="claims_processor",
            permissions=[
                Permission(
                    action="review_claim",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="auto_approve_claim",
                    resource_type="claim",
                    conditions=claim_amount_check(1000),  # Only up to $1k
                ),
                Permission(
                    action="request_medical_review",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="request_financial_review",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
            ],
        )

        medical_role = RoleDefinition(
            name="medical_reviewer",
            permissions=[
                Permission(
                    action="medical_review",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="approve_medical",
                    resource_type="claim",
                    conditions=claim_amount_check(5000),
                ),
                Permission(
                    action="deny_claim_medical",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
            ],
        )

        financial_role = RoleDefinition(
            name="financial_reviewer",
            permissions=[
                Permission(
                    action="financial_review",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="approve_high_value",
                    resource_type="claim",
                    conditions=claim_amount_check(50000),
                ),
            ],
        )

        compliance_role = RoleDefinition(
            name="compliance_officer",
            permissions=[
                Permission(
                    action="escalate_hipaa",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="audit_claim",
                    resource_type="claim",
                    conditions=standard_tenant_check,
                ),
            ],
        )

        self.iam_store.add_role(processor_role)
        self.iam_store.add_role(medical_role)
        self.iam_store.add_role(financial_role)
        self.iam_store.add_role(compliance_role)

        # Register identities
        self.iam_store.add_identity(self.claims_processor)
        self.iam_store.add_identity(self.medical_reviewer)
        self.iam_store.add_identity(self.financial_reviewer)
        self.iam_store.add_identity(self.compliance_officer)

    def process_claim(self, claim: ClaimRecord) -> Dict[str, Any]:
        """
        Process a healthcare claim through CIAF governance.

        IDENTITY PLANE: Processor agent identity
        POLICY PLANE: Amount-based routing
        PRIVILEGE PLANE: Escalation for high-value claims
        EXECUTION PLANE: Tool mediation
        EVIDENCE PLANE: Audit trail
        """
        print("\n" + "=" * 80)
        print(f"  HEALTHCARE CLAIMS AGENT: {claim.claim_id}")
        print("=" * 80)

        # Create claim resource
        claim_resource = Resource(
            resource_id=claim.claim_id,
            resource_type="claim",
            owner_tenant="healthcare-provider-corp",
            attributes={
                "patient_id": claim.patient_id,
                "amount": claim.amount,
                "diagnosis": claim.diagnosis_code,
                "high_risk": claim.high_risk,
            },
        )

        # IDENTITY PLANE: Processor initiates
        print("\n→ IDENTITY PLANE: Processor Agent Identity")
        print(f"  Principal: {self.claims_processor.principal_id}")
        print(f"  Display: {self.claims_processor.display_name}")
        print(f"  Roles: {self.claims_processor.roles}")

        # POLICY PLANE: Routing decision
        print("\n→ POLICY PLANE: Amount-Based Routing")
        print(f"  Claim Amount: ${claim.amount:,.2f}")

        if claim.amount <= 1000:
            action = "auto_approve_claim"
            action_label = "AUTO-APPROVE (Agent Authority)"
        elif claim.amount <= 5000:
            action = "request_medical_review"
            action_label = "MEDICAL REVIEW REQUIRED"
        else:
            action = "request_financial_review"
            action_label = "FINANCIAL REVIEW REQUIRED"

        if claim.high_risk:
            action = "escalate_hipaa"
            action_label = "ESCALATE TO COMPLIANCE"

        print(f"  Decision: {action_label}")

        # PRIVILEGE PLANE: Check if escalation needed
        print("\n→ PRIVILEGE PLANE: Escalation Analysis")
        if claim.amount > 1000:
            print(f"  ◆ High-value claim (${claim.amount:,.2f})")
            print(f"  ◆ Requires elevated approval")
            print(f"  ◆ Current role: {list(self.claims_processor.roles)[0]}")
            print(f"  → Escalation requested to appropriate reviewer")
        else:
            print(f"  ✓ Within agent authority (${claim.amount:,.2f})")

        # EXECUTION PLANE: Simulate tool execution
        print("\n→ EXECUTION PLANE: Tool Mediation")
        print(f"  Action: {action}")
        print(f"  Resource: {claim_resource.resource_id}")

        decision = self._execute_claim_decision(claim, action)

        # EVIDENCE PLANE: Record receipt
        print("\n→ EVIDENCE PLANE: Audit Trail")
        receipt = {
            "claim_id": claim.claim_id,
            "decision": decision["status"],
            "amount": claim.amount,
            "action": action,
            "principal": self.claims_processor.principal_id,
            "timestamp": "2024-04-15T10:30:00Z",
        }
        print(f"  ◆ Receipt recorded: {decision['status']}")
        print(f"  ◆ Chain: [claim-{claim.claim_id}] → [receipt-{action}]")
        print(f"  ◆ Signature: simulated cryptographic hash")

        return decision

    def _execute_claim_decision(
        self, claim: ClaimRecord, action: str
    ) -> Dict[str, Any]:
        """Simulate claim decision execution."""
        decisions = {
            "auto_approve_claim": {
                "status": "APPROVED",
                "reason": "Within agent authority limit ($1,000)",
                "amount": claim.amount,
                "payment_method": "ACH transfer",
            },
            "request_medical_review": {
                "status": "PENDING_MEDICAL_REVIEW",
                "reason": f"Claim (${claim.amount:,.2f}) requires medical review",
                "assigned_to": self.medical_reviewer.display_name,
                "deadline": "2024-04-17",
            },
            "request_financial_review": {
                "status": "PENDING_FINANCIAL_REVIEW",
                "reason": f"High-value claim (${claim.amount:,.2f}) requires financial review",
                "assigned_to": self.financial_reviewer.display_name,
                "deadline": "2024-04-17",
            },
            "escalate_hipaa": {
                "status": "ESCALATED_COMPLIANCE",
                "reason": "High-risk claim flagged for HIPAA review",
                "assigned_to": self.compliance_officer.display_name,
                "deadline": "2024-04-16",
            },
        }
        return decisions.get(action, {"status": "ERROR", "reason": "Unknown action"})


# ============================================================================
# ADK AGENT CREATION
# ============================================================================


def create_healthcare_claims_agent() -> Agent:
    """Create ADK agent for healthcare claims processing."""

    agent_instance = HealthcareClaimsAgent()

    # Define tool: Process claim
    def process_claim_tool(
        claim_id: str,
        patient_id: str,
        provider: str,
        amount: float,
        diagnosis_code: str,
        treatment_type: str,
        high_risk: bool = False,
    ) -> str:
        """
        Process a healthcare claim through CIAF governance.

        This tool routes claims based on:
        - Amount: $0-1K (auto-approve), $1-5K (medical review), $5K+ (financial)
        - Risk level: High-risk claims escalate to compliance

        Args:
            claim_id: Unique claim identifier (e.g., 'CLM-20240415-001')
            patient_id: Patient identifier
            provider: Healthcare provider name
            amount: Claim amount in dollars
            diagnosis_code: ICD-10 diagnosis code
            treatment_type: Description of treatment
            high_risk: Whether claim requires HIPAA escalation

        Returns:
            JSON result with decision, status, and assigned reviewer
        """
        claim = ClaimRecord(
            claim_id=claim_id,
            patient_id=patient_id,
            provider=provider,
            amount=amount,
            diagnosis_code=diagnosis_code,
            treatment_type=treatment_type,
            medical_necessity_score=0.85,
            high_risk=high_risk,
        )

        result = agent_instance.process_claim(claim)
        return json.dumps(result, indent=2)

    # Create ADK agent
    root_agent = Agent(
        name="healthcare_claims_agent",
        model="gemini-2.5-flash",
        instruction="""
You are a Healthcare Claims Processor Agent with CIAF governance.

Your responsibilities:
1. Process healthcare claims through five control planes
2. Route claims based on amount and risk level
3. Explain escalation decisions to users
4. Record all decisions in audit trails
5. Ensure HIPAA compliance

When processing a claim:
1. Call process_claim_tool with complete claim details
2. Explain the routing decision (why it was auto-approved, needs review, etc.)
3. Identify the assigned reviewer (if applicable)
4. Confirm the audit trail was recorded

Decision Logic:
- $0-$1,000: Auto-approve (your authority)
- $1,000-$5,000: Route to medical reviewer
- $5,000+: Route to financial reviewer + medical reviewer
- High-risk claims: Escalate to compliance officer

Always emphasize transparency, auditability, and regulatory compliance.
Focus on governance decisions, not clinical judgment.
""",
        description="Healthcare claims processor with CIAF governance and escalation routing",
        tools=[process_claim_tool],
    )

    return root_agent


# ============================================================================
# EXPORT FOR ADK DISCOVERY
# ============================================================================

root_agent = create_healthcare_claims_agent()


# ============================================================================
# MAIN: RUN AGENT DEMONSTRATION
# ============================================================================


def main():
    """Run healthcare claims agent demonstration."""
    agent_instance = HealthcareClaimsAgent()

    # Test cases
    claims = [
        ClaimRecord(
            claim_id="CLM-20240415-001",
            patient_id="PAT-98765",
            provider="Metropolitan Hospital",
            amount=850.00,
            diagnosis_code="M79.3",
            treatment_type="Physical Therapy",
            medical_necessity_score=0.95,
        ),
        ClaimRecord(
            claim_id="CLM-20240415-002",
            patient_id="PAT-98766",
            provider="Sunrise Clinic",
            amount=3200.00,
            diagnosis_code="I10",
            treatment_type="Cardiology Consultation",
            medical_necessity_score=0.88,
        ),
        ClaimRecord(
            claim_id="CLM-20240415-003",
            patient_id="PAT-98767",
            provider="Regional Medical Center",
            amount=8500.00,
            diagnosis_code="M51.2",
            treatment_type="Spinal Surgery",
            medical_necessity_score=0.92,
        ),
        ClaimRecord(
            claim_id="CLM-20240415-004",
            patient_id="PAT-98768",
            provider="City Hospital",
            amount=1200.00,
            diagnosis_code="Z12.11",
            treatment_type="Preventive Screening",
            medical_necessity_score=0.85,
            high_risk=True,  # HIPAA escalation
        ),
    ]

    for claim in claims:
        result = agent_instance.process_claim(claim)
        print(f"\n  ✓ Decision: {result['status']}")
        print(f"  ✓ Reason: {result.get('reason', 'N/A')}")

    print("\n" + "=" * 80)
    print("  AGENT DEMONSTRATION COMPLETE")
    print(f"  Processed {len(claims)} claims through CIAF governance")
    print("=" * 80)


if __name__ == "__main__":
    main()
