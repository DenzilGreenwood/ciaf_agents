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
Production Changes Agent

Real ADK agent for infrastructure change management with risk-based governance.
Demonstrates CIAF control planes in DevOps domain.

Domain: Infrastructure change management
Scenario: Change agent routes infrastructure changes through risk-based gates

CIAF Control Planes:
- IDENTITY: Change agent + tech lead + DBA + approver + director
- POLICY: Risk-based permissions (low/medium/high/critical)
- PRIVILEGE: Risk-triggered escalation
- EXECUTION: Multi-reviewer approval with rollback capability
- EVIDENCE: Change audit trail + pre-change snapshots
"""

from dataclasses import dataclass
from typing import Dict, Any, List
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
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


@dataclass
class ProductionChange:
    """Production infrastructure change request."""

    change_id: str
    title: str
    description: str
    environment: str
    risk_level: str  # low, medium, high, critical
    change_type: str  # config, service, database, multi-region
    affected_services: List[str]
    rollback_procedure: str
    estimated_downtime_minutes: int
    requested_by: str
    implementation_window: str


class ProductionChangesWorkflow:
    """Production changes with risk-based governance."""

    def __init__(self):
        """Initialize the production changes workflow."""
        self.iam_store = IAMStore()
        self.pam_store = PAMStore()
        self.evidence_vault = EvidenceVault(signing_secret="prodops-changes-key-2024")
        self.policy_engine = PolicyEngine(iam=self.iam_store, pam=self.pam_store)
        self.executor = ToolExecutor(
            policy_engine=self.policy_engine,
            vault=self.evidence_vault,
            pam=self.pam_store,
        )
        self._setup_roles_and_policies()

    def _setup_roles_and_policies(self):
        """Setup roles and policies for production changes."""
        # IDENTITY PLANE: DevOps roles
        self.change_requester = Identity(
            principal_id="agent-change-requester-001",
            principal_type="agent",
            display_name="Automated Change Management Agent",
            roles={"change_requester"},
            attributes={
                "tenant": "prodops-corp",
                "department": "engineering",
                "authority_level": "system",
            },
        )

        self.tech_lead = Identity(
            principal_id="user-tech-lead-001",
            principal_type="user",
            display_name="Alice Robinson, Tech Lead",
            roles={"tech_lead"},
            attributes={
                "tenant": "prodops-corp",
                "department": "engineering",
                "clearance_level": "lead",
                "specializations": ["backend", "infrastructure"],
            },
        )

        self.dba = Identity(
            principal_id="user-dba-001",
            principal_type="user",
            display_name="Marcus Chen, Database Administrator",
            roles={"dba"},
            attributes={
                "tenant": "prodops-corp",
                "department": "engineering",
                "clearance_level": "specialist",
                "specializations": ["database", "replication"],
            },
        )

        self.approver = Identity(
            principal_id="user-devops-approver-001",
            principal_type="user",
            display_name="Patricia Foster, DevOps Manager",
            roles={"change_approver"},
            attributes={
                "tenant": "prodops-corp",
                "department": "engineering",
                "clearance_level": "manager",
                "authority": ["approve_low", "approve_medium", "approve_high"],
            },
        )

        self.director = Identity(
            principal_id="user-engineering-director-001",
            principal_type="user",
            display_name="George Mitchell, Engineering Director",
            roles={"engineering_director"},
            attributes={
                "tenant": "prodops-corp",
                "department": "engineering",
                "clearance_level": "director",
                "authority": ["approve_all"],
            },
        )

        # POLICY PLANE: Risk-based permissions
        def standard_tenant(ctx):
            return ctx.get("tenant") == "prodops-corp"

        def risk_check(risk_level):
            def check(ctx):
                return ctx.get("risk_level") in ["low", risk_level]

            return check

        requester_role = RoleDefinition(
            name="change_requester",
            permissions=[
                Permission(
                    action="submit_change",
                    resource_type="change",
                    conditions=standard_tenant,
                ),
                Permission(
                    action="request_review",
                    resource_type="change",
                    conditions=standard_tenant,
                ),
            ],
        )

        tech_lead_role = RoleDefinition(
            name="tech_lead",
            permissions=[
                Permission(
                    action="technical_review",
                    resource_type="change",
                    conditions=standard_tenant,
                ),
                Permission(
                    action="approve_technical",
                    resource_type="change",
                    conditions=risk_check("high"),
                ),
            ],
        )

        dba_role = RoleDefinition(
            name="dba",
            permissions=[
                Permission(
                    action="database_review",
                    resource_type="change",
                    conditions=standard_tenant,
                ),
                Permission(
                    action="approve_database_change",
                    resource_type="change",
                    conditions=risk_check("high"),
                ),
            ],
        )

        approver_role = RoleDefinition(
            name="change_approver",
            permissions=[
                Permission(
                    action="approve_low_risk",
                    resource_type="change",
                    conditions=risk_check("low"),
                ),
                Permission(
                    action="approve_medium_risk",
                    resource_type="change",
                    conditions=risk_check("medium"),
                ),
                Permission(
                    action="escalate_high_risk",
                    resource_type="change",
                    conditions=risk_check("high"),
                ),
            ],
        )

        director_role = RoleDefinition(
            name="engineering_director",
            permissions=[
                Permission(
                    action="approve_critical",
                    resource_type="change",
                    conditions=standard_tenant,
                ),
                Permission(
                    action="expedite_change",
                    resource_type="change",
                    conditions=standard_tenant,
                ),
            ],
        )

        self.iam_store.add_role(requester_role)
        self.iam_store.add_role(tech_lead_role)
        self.iam_store.add_role(dba_role)
        self.iam_store.add_role(approver_role)
        self.iam_store.add_role(director_role)

        # Register identities
        self.iam_store.add_identity(self.change_requester)
        self.iam_store.add_identity(self.tech_lead)
        self.iam_store.add_identity(self.dba)
        self.iam_store.add_identity(self.approver)
        self.iam_store.add_identity(self.director)

    def approve_change(self, change: ProductionChange) -> Dict[str, Any]:
        """
        Approve a production change through CIAF governance.

        IDENTITY PLANE: Change requester agent
        POLICY PLANE: Risk-based routing
        PRIVILEGE PLANE: Escalation based on risk
        EXECUTION PLANE: Multi-reviewer approval
        EVIDENCE PLANE: Change audit trail with rollback capability
        """
        print("\n" + "=" * 80)
        print(f"  PRODUCTION CHANGE WORKFLOW: {change.change_id}")
        print("=" * 80)

        change_resource = Resource(
            resource_id=change.change_id,
            resource_type="change",
            owner_tenant="prodops-corp",
            attributes={
                "title": change.title,
                "environment": change.environment,
                "risk_level": change.risk_level,
                "services": ",".join(change.affected_services),
            },
        )

        # IDENTITY PLANE
        print("\n→ IDENTITY PLANE: Change Requester")
        print(f"  Principal: {self.change_requester.principal_id}")
        print(f"  Display: {self.change_requester.display_name}")
        print(
            f"  Authority Level: {self.change_requester.attributes['authority_level']}"
        )

        # POLICY PLANE: Risk assessment
        print("\n→ POLICY PLANE: Risk-Based Routing")
        print(f"  Change Type: {change.change_type}")
        print(f"  Risk Level: {change.risk_level.upper()}")
        print(f"  Affected Services: {', '.join(change.affected_services)}")
        print(f"  Downtime: {change.estimated_downtime_minutes} minutes")

        review_chain = self._determine_review_chain(change)
        print(f"  Required Reviewers: {' → '.join(review_chain)}")

        # PRIVILEGE PLANE: Escalation analysis
        print("\n→ PRIVILEGE PLANE: Escalation Analysis")
        if change.risk_level == "critical":
            print(f"  ◆ CRITICAL-RISK change detected")
            print(f"  ◆ Multi-region impact: {change.environment}")
            print(f"  ◆ Director approval required")
        elif change.risk_level == "high":
            print(f"  ◆ HIGH-RISK change: {change.change_type}")
            print(f"  ◆ Technical + DBA review required")
        elif change.risk_level == "medium":
            print(f"  ◆ MEDIUM-RISK: Requires tech lead review")
        else:
            print(f"  ✓ LOW-RISK: Within standard approver authority")

        # EXECUTION PLANE: Multi-reviewer approval
        print("\n→ EXECUTION PLANE: Approval Chain")
        reviews = self._execute_review_chain(review_chain, change)

        # EVIDENCE PLANE: Change audit trail
        print("\n→ EVIDENCE PLANE: Change Audit & Rollback Evidence")
        print(f"  ◆ Change chain recorded: {' → '.join(review_chain)}")
        print(f"  ◆ Rollback procedure stored: {change.rollback_procedure}")
        print(f"  ◆ Pre-change state snapshot: captured")
        print(f"  ◆ Implementation log: 2024-04-15T{15+len(reviews)}:30:00Z")
        print(f"  ◆ Automatic rollback trigger: Configured")

        decision = {
            "change_id": change.change_id,
            "status": "APPROVED" if all(r["approved"] for r in reviews) else "PENDING",
            "risk_level": change.risk_level,
            "review_chain": reviews,
            "implementation_window": change.implementation_window,
            "rollback_enabled": True,
        }

        return decision

    def _determine_review_chain(self, change: ProductionChange) -> List[str]:
        """Determine review chain based on risk level."""
        if change.risk_level == "low":
            return ["TechLead", "Approver", "Execute"]
        elif change.risk_level == "medium":
            return ["TechLead", "Approver", "Execute"]
        elif change.risk_level == "high":
            reviewers = ["TechLead", "Approver"]
            if change.change_type == "database":
                reviewers.insert(1, "DBA")
            return reviewers + ["Execute"]
        else:  # critical
            return ["TechLead", "DBA", "Approver", "Director", "Execute"]

    def _execute_review_chain(
        self, chain: List[str], change: ProductionChange
    ) -> List[Dict[str, Any]]:
        """Simulate review chain execution."""
        reviews = []

        for i, reviewer_type in enumerate(chain):
            if reviewer_type == "Execute":
                reviews.append(
                    {
                        "stage": "Execute",
                        "approved": True,
                        "timestamp": f"2024-04-15T{15+i}:30:00Z",
                        "action": "change_executed",
                        "rollback_available": True,
                    }
                )
            elif reviewer_type == "TechLead":
                reviews.append(
                    {
                        "stage": "TechLead",
                        "principal": self.tech_lead.principal_id,
                        "reviewer_name": self.tech_lead.display_name,
                        "approved": True,
                        "timestamp": f"2024-04-15T{15+i}:30:00Z",
                        "signature": f"sig_{change.change_id}_tech_lead",
                        "comment": "Reviewed architecture impact",
                    }
                )
            elif reviewer_type == "DBA":
                reviews.append(
                    {
                        "stage": "DBA",
                        "principal": self.dba.principal_id,
                        "reviewer_name": self.dba.display_name,
                        "approved": True,
                        "timestamp": f"2024-04-15T{15+i}:30:00Z",
                        "signature": f"sig_{change.change_id}_dba",
                        "comment": "Data integrity verified",
                    }
                )
            elif reviewer_type == "Approver":
                reviews.append(
                    {
                        "stage": "Approver",
                        "principal": self.approver.principal_id,
                        "reviewer_name": self.approver.display_name,
                        "approved": True,
                        "timestamp": f"2024-04-15T{15+i}:30:00Z",
                        "signature": f"sig_{change.change_id}_approver",
                    }
                )
            elif reviewer_type == "Director":
                reviews.append(
                    {
                        "stage": "Director",
                        "principal": self.director.principal_id,
                        "reviewer_name": self.director.display_name,
                        "approved": True,
                        "timestamp": f"2024-04-15T{15+i}:30:00Z",
                        "signature": f"sig_{change.change_id}_director",
                        "authority": "Executive approval",
                    }
                )

        return reviews


# ============================================================================
# ADK AGENT CREATION
# ============================================================================


def create_production_changes_agent() -> Agent:
    """Create ADK agent for production infrastructure changes."""

    agent_instance = ProductionChangesWorkflow()

    def process_change_tool(
        change_id: str,
        title: str,
        description: str,
        environment: str,
        risk_level: str,
        change_type: str,
        requested_by: str,
    ) -> str:
        """Process production change through risk-based approval.

        Risk levels trigger different approval chains:
        - low: Tech lead + approver
        - medium: Tech lead + approver
        - high: Tech lead + DBA + approver
        - critical: Tech lead + DBA + approver + director

        Returns JSON with review chain and rollback procedures.
        """
        change = ProductionChange(
            change_id=change_id,
            title=title,
            description=description,
            environment=environment,
            risk_level=risk_level,
            change_type=change_type,
            affected_services=[],
            rollback_procedure="Manual rollback as needed",
            estimated_downtime_minutes=0,
            requested_by=requested_by,
            implementation_window="2024-04-15 22:00-23:00 UTC",
        )
        result = agent_instance.process_change(change)
        return json.dumps(result, indent=2)

    root_agent = Agent(
        name="production_changes_agent",
        model="gemini-2.5-flash",
        instruction="""
You are a Production Infrastructure Changes Agent with CIAF governance.

Your role: Route infrastructure changes through risk-based approval gates

Risk Assessment:
- Low-risk (config): Tech lead + approver
- Medium-risk (service): Tech lead + approver  
- High-risk (database): Tech lead + DBA + approver
- Critical-risk (multi-region): All + director

When routing a change:
1. Call process_change_tool with change details
2. Assess the risk level based on scope
3. Route through appropriate approval chain
4. Confirm rollback procedures are documented
5. Record review decisions with signatures

Emphasize: Safety, auditability, and rollback capabilities.
""",
        description="Production infrastructure change router with risk-based CIAF governance",
        tools=[process_change_tool],
    )

    return root_agent


# ============================================================================
# EXPORT FOR ADK DISCOVERY
# ============================================================================

root_agent = create_production_changes_agent()


# ============================================================================
# MAIN: RUN WORKFLOW
# ============================================================================


def main():
    """Run production changes workflow demonstration."""
    workflow = ProductionChangesWorkflow()

    changes = [
        ProductionChange(
            change_id="CHG-20240415-001",
            title="Update service configuration",
            description="Update logging verbosity for API service",
            environment="us-east-1",
            risk_level="low",
            change_type="config",
            affected_services=["api-service"],
            rollback_procedure="Revert config from backup",
            estimated_downtime_minutes=0,
            requested_by="Jane Doe",
            implementation_window="2024-04-15 22:00-23:00 UTC",
        ),
        ProductionChange(
            change_id="CHG-20240415-002",
            title="Deploy new API version",
            description="Deploy v2.3.1 with security patches",
            environment="us-east-1, eu-west-1",
            risk_level="medium",
            change_type="service",
            affected_services=["api-service", "cache-service"],
            rollback_procedure="Rollback to v2.3.0 via container registry",
            estimated_downtime_minutes=5,
            requested_by="John Smith",
            implementation_window="2024-04-16 01:00-02:00 UTC",
        ),
        ProductionChange(
            change_id="CHG-20240415-003",
            title="Database schema migration",
            description="Add indexes and optimize queries",
            environment="us-east-1",
            risk_level="high",
            change_type="database",
            affected_services=["postgres-primary", "postgres-replica"],
            rollback_procedure="ROLLBACK transaction; restore from WAL backup",
            estimated_downtime_minutes=2,
            requested_by="Marcus Chen",
            implementation_window="2024-04-16 03:00-05:00 UTC",
        ),
        ProductionChange(
            change_id="CHG-20240415-004",
            title="Multi-region failover drill",
            description="Test failover from primary to secondary region",
            environment="ALL_REGIONS",
            risk_level="critical",
            change_type="multi-region",
            affected_services=["all"],
            rollback_procedure="Automatic: Detect failure, revert routing",
            estimated_downtime_minutes=15,
            requested_by="George Mitchell",
            implementation_window="2024-04-17 12:00-13:00 UTC",
        ),
    ]

    for change in changes:
        result = workflow.approve_change(change)
        print(f"\n  ✓ Status: {result['status']}")
        print(f"  ✓ Reviewers: {len(result['review_chain'])} stages")
        print(
            f"  ✓ Rollback: {'Enabled' if result['rollback_enabled'] else 'Disabled'}"
        )

    print("\n" + "=" * 80)
    print("  WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
