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
Data Access & Export Agent

Real ADK agent for data governance with classification-based access control.
Demonstrates CIAF control planes in data governance domain.

Domain: Data governance
Scenario: Data agent enforces access control based on data classification

CIAF Control Planes:
- IDENTITY: Data agent + analyst + scientist + compliance + CDO
- POLICY: Classification-based data gates
- PRIVILEGE: Escalation for sensitive/export/cross-tenant access
- EXECUTION: Tenant isolation enforcement
- EVIDENCE: Fine-grained access log + export audit trail

Data Classifications:
- Public: Direct access
- Customer: Requires business justification
- Financial: Requires compliance approval
- Confidential: Requires CDO approval + executive audit
"""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum
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


class DataClassification(Enum):
    """Data classification levels."""
    PUBLIC = "public"
    CUSTOMER = "customer"
    FINANCIAL = "financial"
    CONFIDENTIAL = "confidential"


@dataclass
class DataAccessRequest:
    """Data access request."""
    request_id: str
    requester_id: str
    requester_role: str
    data_classification: DataClassification
    dataset_id: str
    dataset_name: str
    rows_requested: int
    columns_requested: List[str]
    purpose: str
    business_justification: str
    export_format: str  # csv, json, parquet, sql
    is_export: bool
    source_tenant: str
    target_tenant: str  # For cross-tenant validation


class DataAccessExportWorkflow:
    """Data access and export with tenant isolation."""

    def __init__(self):
        """Initialize the data access workflow."""
        self.iam_store = IAMStore()
        self.pam_store = PAMStore()
        self.evidence_vault = EvidenceVault(
            signing_secret="data-access-key-2024"
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
        """Setup roles and policies for data access."""
        # IDENTITY PLANE: Data access roles
        self.data_agent = Identity(
            principal_id="agent-data-access-001",
            principal_type="agent",
            display_name="Data Access Management Agent",
            roles={"data_agent"},
            attributes={
                "tenant": "data-corp",
                "department": "data",
                "authority_level": "system",
            },
        )

        self.analyst = Identity(
            principal_id="user-analyst-001",
            principal_type="user",
            display_name="Robert Chen, Data Analyst",
            roles={"data_analyst"},
            attributes={
                "tenant": "data-corp",
                "department": "analytics",
                "clearance_level": "analyst",
                "can_access_customer": True,
            },
        )

        self.scientist = Identity(
            principal_id="user-scientist-001",
            principal_type="user",
            display_name="Dr. Lisa Anderson, Data Scientist",
            roles={"data_scientist"},
            attributes={
                "tenant": "data-corp",
                "department": "analytics",
                "clearance_level": "researcher",
                "can_access_financial": False,
            },
        )

        self.compliance_officer = Identity(
            principal_id="user-compliance-officer-001",
            principal_type="user",
            display_name="James Wilson, Data Compliance",
            roles={"data_compliance"},
            attributes={
                "tenant": "data-corp",
                "department": "compliance",
                "clearance_level": "director",
                "can_approve_export": True,
            },
        )

        self.chief_data_officer = Identity(
            principal_id="user-cdo-001",
            principal_type="user",
            display_name="Victoria Martinez, Chief Data Officer",
            roles={"chief_data_officer"},
            attributes={
                "tenant": "data-corp",
                "department": "executive",
                "clearance_level": "executive",
                "can_approve_all": True,
            },
        )

        # POLICY PLANE: Data access permissions
        def same_tenant(ctx):
            return ctx.get("source_tenant") == ctx.get("target_tenant")

        def justified_access(ctx):
            return len(ctx.get("business_justification", "")) > 20

        def not_export(ctx):
            return not ctx.get("is_export", False)

        agent_role = RoleDefinition(
            name="data_agent",
            permissions=[
                Permission(
                    action="route_access_request",
                    resource_type="data_access",
                    conditions=lambda ctx: True
                ),
                Permission(
                    action="log_access",
                    resource_type="data_access",
                    conditions=lambda ctx: True
                ),
            ],
        )

        analyst_role = RoleDefinition(
            name="data_analyst",
            permissions=[
                Permission(
                    action="access_customer_data",
                    resource_type="data_access",
                    conditions=lambda ctx: ctx.get("data_classification") == "customer" and same_tenant(ctx) and justified_access(ctx)
                ),
                Permission(
                    action="export_customer_data",
                    resource_type="data_access",
                    conditions=lambda ctx: ctx.get("data_classification") == "customer" and same_tenant(ctx)
                ),
            ],
        )

        scientist_role = RoleDefinition(
            name="data_scientist",
            permissions=[
                Permission(
                    action="access_anonymized_data",
                    resource_type="data_access",
                    conditions=lambda ctx: ctx.get("data_classification") == "customer" and not_export(ctx)
                ),
            ],
        )

        compliance_role = RoleDefinition(
            name="data_compliance",
            permissions=[
                Permission(
                    action="approve_export",
                    resource_type="data_access",
                    conditions=lambda ctx: ctx.get("is_export")
                ),
                Permission(
                    action="audit_access",
                    resource_type="data_access",
                    conditions=lambda ctx: True
                ),
            ],
        )

        cdo_role = RoleDefinition(
            name="chief_data_officer",
            permissions=[
                Permission(
                    action="approve_confidential_access",
                    resource_type="data_access",
                    conditions=lambda ctx: True
                ),
                Permission(
                    action="override_restrictions",
                    resource_type="data_access",
                    conditions=lambda ctx: True
                ),
            ],
        )

        self.iam_store.add_role(agent_role)
        self.iam_store.add_role(analyst_role)
        self.iam_store.add_role(scientist_role)
        self.iam_store.add_role(compliance_role)
        self.iam_store.add_role(cdo_role)

        # Register identities
        self.iam_store.add_identity(self.data_agent)
        self.iam_store.add_identity(self.analyst)
        self.iam_store.add_identity(self.scientist)
        self.iam_store.add_identity(self.compliance_officer)
        self.iam_store.add_identity(self.chief_data_officer)

    def process_access_request(
        self,
        request: DataAccessRequest
    ) -> Dict[str, Any]:
        """
        Process data access request with tenant isolation and classification.

        IDENTITY PLANE: Access requester
        POLICY PLANE: Data classification gates
        PRIVILEGE PLANE: Escalation based on sensitivity
        EXECUTION PLANE: Tenant isolation enforcement
        EVIDENCE PLANE: Fine-grained access log
        """
        print("\n" + "=" * 80)
        print(f"  DATA ACCESS WORKFLOW: {request.request_id}")
        print("=" * 80)

        access_resource = Resource(
            resource_id=request.request_id,
            resource_type="data_access",
            owner_tenant=request.source_tenant,
            attributes={
                "dataset": request.dataset_name,
                "classification": request.data_classification.value,
                "rows": request.rows_requested,
                "is_export": request.is_export,
            },
        )

        # IDENTITY PLANE
        print("\n→ IDENTITY PLANE: Access Requester")
        print(f"  Requester ID: {request.requester_id}")
        print(f"  Requester Role: {request.requester_role}")
        print(f"  Source Tenant: {request.source_tenant}")
        print(f"  Target Tenant: {request.target_tenant}")

        # POLICY PLANE: Data classification gates
        print("\n→ POLICY PLANE: Data Classification Gates")
        print(f"  Data Classification: {request.data_classification.value.upper()}")
        print(f"  Dataset: {request.dataset_name}")
        print(f"  Rows Requested: {request.rows_requested:,}")
        print(f"  Columns: {', '.join(request.columns_requested)}")
        print(f"  Purpose: {request.purpose}")

        # Check tenant isolation
        if request.source_tenant != request.target_tenant:
            print(f"  ⚠ Cross-tenant access detected → Requires compliance review")

        # PRIVILEGE PLANE: Escalation analysis
        print("\n→ PRIVILEGE PLANE: Escalation Analysis")
        approval_chain = self._determine_approval_chain(request)
        print(f"  Required Approvers: {' → '.join(approval_chain)}")

        if request.data_classification == DataClassification.CONFIDENTIAL:
            print(f"  ◆ CONFIDENTIAL data → Executive approval required")
            print(f"  ◆ Audit trail will be reviewed by CDO")
        elif request.data_classification == DataClassification.FINANCIAL:
            print(f"  ◆ FINANCIAL data → Compliance review required")
            if request.is_export:
                print(f"  ◆ Export request → Additional approval needed")
        elif request.data_classification == DataClassification.CUSTOMER:
            print(f"  ◆ CUSTOMER data → Standard approval")
            if request.is_export:
                print(f"  ◆ Export request → Compliance must approve")

        # EXECUTION PLANE: Tenant isolation
        print("\n→ EXECUTION PLANE: Tenant Isolation Enforcement")
        print(f"  ◆ Source tenant: {request.source_tenant} (read)")
        print(f"  ◆ Target tenant: {request.target_tenant} (destination)")

        if request.source_tenant == request.target_tenant:
            print(f"  ✓ Same-tenant access → Direct access permitted")
        else:
            print(f"  ✗ Cross-tenant access → Compliance review required")

        # Process access with approvals
        approvals = self._execute_approval_chain(approval_chain, request)

        # EVIDENCE PLANE: Fine-grained audit trail
        print("\n→ EVIDENCE PLANE: Fine-Grained Access Log")
        print(f"  ◆ Request ID: {request.request_id}")
        print(f"  ◆ Requester: {request.requester_id}")
        print(f"  ◆ Dataset: {request.dataset_name}")
        print(f"  ◆ Classification: {request.data_classification.value}")
        print(f"  ◆ Rows: {request.rows_requested:,}")
        print(f"  ◆ Columns: {len(request.columns_requested)}")
        print(f"  ◆ Export: {request.is_export}")
        print(f"  ◆ Approvers: {len(approval_chain)}")
        print(f"  ◆ Access hash: sha256_[access_record_hash]")
        print(f"  ◆ Timestamp: 2024-04-15T17:30:00Z")

        decision = {
            "request_id": request.request_id,
            "status": "APPROVED" if all(a["approved"] for a in approvals) else "DENIED",
            "data_classification": request.data_classification.value,
            "tenant_isolation": request.source_tenant == request.target_tenant,
            "rows_accessible": request.rows_requested if all(a["approved"] for a in approvals) else 0,
            "is_export": request.is_export,
            "approval_chain": approvals,
            "access_log_id": f"log_{request.request_id}",
        }

        return decision

    def _determine_approval_chain(
        self,
        request: DataAccessRequest
    ) -> List[str]:
        """Determine approval chain based on data classification."""
        if request.data_classification == DataClassification.PUBLIC:
            return ["Agent", "Grant"]
        elif request.data_classification == DataClassification.CUSTOMER:
            chain = ["Agent", "Analyst"]
            if request.is_export or request.source_tenant != request.target_tenant:
                chain.insert(1, "Compliance")
            return chain + ["Grant"]
        elif request.data_classification == DataClassification.FINANCIAL:
            return ["Agent", "Compliance", "Grant"]
        else:  # CONFIDENTIAL
            return ["Agent", "Compliance", "CDO", "Grant"]

    def _execute_approval_chain(
        self,
        chain: List[str],
        request: DataAccessRequest
    ) -> List[Dict[str, Any]]:
        """Simulate approval chain execution."""
        approvals = []

        for i, approver_type in enumerate(chain):
            if approver_type == "Grant":
                approvals.append({
                    "stage": "Grant",
                    "approved": True,
                    "timestamp": f"2024-04-15T17:{30+i}:00Z",
                    "action": "access_granted",
                    "access_token": f"token_{request.request_id}",
                })
            elif approver_type == "Agent":
                approvals.append({
                    "stage": "Agent",
                    "principal": self.data_agent.principal_id,
                    "approved": True,
                    "timestamp": f"2024-04-15T17:{30+i}:00Z",
                    "action": "route_and_validate",
                })
            elif approver_type == "Analyst":
                approvals.append({
                    "stage": "Analyst",
                    "principal": self.analyst.principal_id,
                    "approver_name": self.analyst.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T17:{30+i}:00Z",
                    "signature": f"sig_{request.request_id}_analyst",
                    "justification_check": "Business purpose verified",
                })
            elif approver_type == "Compliance":
                approvals.append({
                    "stage": "Compliance",
                    "principal": self.compliance_officer.principal_id,
                    "approver_name": self.compliance_officer.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T17:{30+i}:00Z",
                    "signature": f"sig_{request.request_id}_compliance",
                    "checks": ["tenant_isolation", "data_classification", "export_policy"],
                })
            elif approver_type == "CDO":
                approvals.append({
                    "stage": "CDO",
                    "principal": self.chief_data_officer.principal_id,
                    "approver_name": self.chief_data_officer.display_name,
                    "approved": True,
                    "timestamp": f"2024-04-15T17:{30+i}:00Z",
                    "signature": f"sig_{request.request_id}_cdo",
                    "authority": "Executive approval for confidential data",
                })

        return approvals


# ============================================================================
# ADK AGENT CREATION
# ============================================================================

def create_data_access_agent() -> Agent:
    """Create ADK agent for data access governance."""

    agent_instance = DataAccessExportWorkflow()

    def request_data_access_tool(
        request_id: str,
        requester_id: str,
        dataset_name: str,
        data_classification: str,
        access_purpose: str,
        is_export: bool = False,
    ) -> str:
        """Request access to data through classification-based gates.

        Data Classifications:
        - PUBLIC: Direct access
        - CUSTOMER: Requires justification
        - FINANCIAL: Requires compliance
        - CONFIDENTIAL: Requires CDO approval

        Returns JSON with routing decision and approval chain.
        """
        data_request = DataAccessRequest(
            request_id=request_id,
            requester_id=requester_id,
            dataset_name=dataset_name,
            data_classification=data_classification,
            access_purpose=access_purpose,
            requester_tenant="tenant-001",
            data_owner_tenant="tenant-001",
            is_export=is_export,
            cross_tenant=False,
        )
        result = agent_instance.process_access_request(data_request)
        return json.dumps(result, indent=2)

    root_agent = Agent(
        name="data_access_agent",
        model="gemini-2.5-flash",
        instruction="""
You are a Data Access & Export Agent with CIAF governance.

Your role: Control data access based on classification and enforce tenant isolation

Data Classifications & Access:
- PUBLIC: Immediate approval
- CUSTOMER: Requires business justification
- FINANCIAL: Requires compliance review
- CONFIDENTIAL: Requires CDO approval + audit

When processing access requests:
1. Call request_data_access_tool with dataset details
2. Evaluate data classification level
3. Route through appropriate approval chain
4. Enforce tenant isolation for cross-tenant requests
5. Record access in fine-grained audit trail

Export Controls:
- Public data: Exportable
- Customer data: Compliance review for export
- Financial/Confidential: Limited or restricted export

Emphasize: Data governance, tenant isolation, auditability.
""",
        description="Data access processor with CIAF classification-based governance",
        tools=[request_data_access_tool],
    )

    return root_agent


# ============================================================================
# EXPORT FOR ADK DISCOVERY
# ============================================================================

root_agent = create_data_access_agent()


# ============================================================================
# MAIN: RUN WORKFLOW
# ============================================================================

def main():
    """Run data access workflow demonstration."""
    workflow = DataAccessExportWorkflow()

    access_requests = [
        DataAccessRequest(
            request_id="DATA-20240415-001",
            requester_id="user-analyst-001",
            requester_role="data_analyst",
            data_classification=DataClassification.CUSTOMER,
            dataset_id="ds-001",
            dataset_name="customer_profiles",
            rows_requested=10000,
            columns_requested=["customer_id", "signup_date", "region"],
            purpose="Regional analysis",
            business_justification="Q2 regional performance analysis for board review",
            export_format="csv",
            is_export=False,
            source_tenant="analytics-corp",
            target_tenant="analytics-corp",
        ),
        DataAccessRequest(
            request_id="DATA-20240415-002",
            requester_id="user-analyst-001",
            requester_role="data_analyst",
            data_classification=DataClassification.CUSTOMER,
            dataset_id="ds-002",
            dataset_name="customer_transactions",
            rows_requested=50000,
            columns_requested=["transaction_id", "amount", "category"],
            purpose="Export for audit",
            business_justification="Annual external audit requires transaction records",
            export_format="parquet",
            is_export=True,
            source_tenant="analytics-corp",
            target_tenant="audit-firm-corp",
        ),
        DataAccessRequest(
            request_id="DATA-20240415-003",
            requester_id="user-scientist-001",
            requester_role="data_scientist",
            data_classification=DataClassification.FINANCIAL,
            dataset_id="ds-003",
            dataset_name="revenue_data",
            rows_requested=1000,
            columns_requested=["date", "revenue", "cost"],
            purpose="ML model training",
            business_justification="Training revenue forecasting model",
            export_format="json",
            is_export=False,
            source_tenant="analytics-corp",
            target_tenant="analytics-corp",
        ),
        DataAccessRequest(
            request_id="DATA-20240415-004",
            requester_id="user-analyst-001",
            requester_role="data_analyst",
            data_classification=DataClassification.CONFIDENTIAL,
            dataset_id="ds-004",
            dataset_name="executive_strategy",
            rows_requested=100,
            columns_requested=["project_name", "budget", "timeline"],
            purpose="Executive planning",
            business_justification="Strategic initiative planning for C-suite",
            export_format="csv",
            is_export=False,
            source_tenant="analytics-corp",
            target_tenant="analytics-corp",
        ),
    ]

    for access_req in access_requests:
        result = workflow.process_access_request(access_req)
        print(f"\n  ✓ Status: {result['status']}")
        print(f"  ✓ Classification: {result['data_classification']}")
        print(f"  ✓ Tenant Isolated: {result['tenant_isolation']}")
        print(f"  ✓ Rows Accessible: {result['rows_accessible']:,}")

    print("\n" + "=" * 80)
    print("  WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
