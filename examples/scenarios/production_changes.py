"""
Production Infrastructure Changes Scenario.

Demonstrates CIAF-LCM controls for production system modifications with change management.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ciaf_agents.core import Identity, Resource, ActionRequest, Permission, RoleDefinition
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine, production_environment_only, any_condition
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


def setup_infrastructure_scenario():
    """
    Set up infrastructure operations with change management controls.
    
    Key controls:
    - Production changes require PAM elevation
    - Change ticket validation
    - Separation of read vs write permissions
    - Complete audit trail for incident investigation
    """
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="infrastructure-demo-secret")
    policy = PolicyEngine(
        iam, pam,
        sensitive_actions={
            "modify_prod_config",
            "restart_service",
            "deploy_code",
            "modify_firewall_rule"
        }
    )
    executor = ToolExecutor(policy, vault, pam)

    # Define roles
    sre_readonly_role = RoleDefinition(
        name="sre_readonly",
        permissions=[
            Permission("read_config", "config", any_condition),
            Permission("read_logs", "logs", any_condition),
            Permission("read_metrics", "metrics", any_condition),
        ]
    )

    sre_operator_role = RoleDefinition(
        name="sre_operator",
        permissions=[
            Permission("read_config", "config", any_condition),
            Permission("read_logs", "logs", any_condition),
            Permission("modify_prod_config", "config", production_environment_only),
            Permission("restart_service", "service", production_environment_only),
        ]
    )

    iam.add_role(sre_readonly_role)
    iam.add_role(sre_operator_role)

    # Create agent identities
    monitoring_agent = Identity(
        principal_id="agent-monitoring-001",
        principal_type="agent",
        display_name="Infrastructure Monitoring Agent",
        roles={"sre_readonly"},
        attributes={
            "tenant": "platform-ops",
            "department": "sre",
            "environment": "production",
        }
    )

    ops_agent = Identity(
        principal_id="agent-ops-automation-001",
        principal_type="agent",
        display_name="Operations Automation Agent",
        roles={"sre_operator"},
        attributes={
            "tenant": "platform-ops",
            "department": "sre",
            "environment": "production",
        }
    )

    iam.add_identity(monitoring_agent)
    iam.add_identity(ops_agent)

    return iam, pam, vault, executor


def run_infrastructure_scenario():
    """Run the infrastructure operations scenario."""
    print("Production Infrastructure Changes Scenario")
    print("=" * 80)
    
    iam, pam, vault, executor = setup_infrastructure_scenario()
    
    ops_agent = iam.identities["agent-ops-automation-001"]
    monitoring_agent = iam.identities["agent-monitoring-001"]
    
    # Scenario 1: Monitoring agent reads (allowed)
    print("Scenario 1: Monitoring agent reads metrics")
    metrics_resource = Resource(
        resource_id="metrics-db-cpu",
        resource_type="metrics",
        owner_tenant="platform-ops",
        attributes={"service": "database"}
    )
    
    request1 = ActionRequest(
        action="read_metrics",
        resource=metrics_resource,
        params={"time_range": "1h"},
        justification="Routine monitoring check",
        requested_by=monitoring_agent
    )
    
    result1 = executor.execute(request1)
    print(f"Result: {result1['status']}")
    print()
    
    # Scenario 2: Operations agent modifies config (requires elevation)
    print("Scenario 2: Operations agent modifies production config")
    config_resource = Resource(
        resource_id="config-api-gateway",
        resource_type="config",
        owner_tenant="platform-ops",
        attributes={"service": "api-gateway", "environment": "production"}
    )
    
    request2 = ActionRequest(
        action="modify_prod_config",
        resource=config_resource,
        params={"setting": "max_connections", "value": 1000},
        justification="Increase connection limit per capacity planning",
        requested_by=ops_agent
    )
    
    # First attempt: blocked, needs elevation
    result2 = executor.execute(request2)
    print(f"Result: {result2['status']}")
    print(f"Requires elevation: {result2.get('requires_elevation')}")
    print()
    
    # Issue change-managed grant
    print("Issuing PAM grant with change ticket...")
    grant = pam.issue_grant(
        principal_id=ops_agent.principal_id,
        allowed_actions={"modify_prod_config"},
        resource_types={"config"},
        reason="Approved change per capacity planning review",
        approved_by="sre-lead@platform-ops.com",
        duration_minutes=30,
        ticket_id="CHG-2026-00456"
    )
    print(f"Grant issued: {grant.grant_id}")
    print(f"Change ticket: {grant.ticket_id}")
    print()
    
    # Retry with grant
    result2_retry = executor.execute(request2)
    print(f"Retry result: {result2_retry['status']}")
    print()
    
    print("=" * 80)
    print("Audit Summary:")
    print("-" * 80)
    elevated = vault.get_elevated_receipts()
    print(f"Elevated actions: {len(elevated)}")
    for receipt in elevated:
        print(f"  - {receipt.action} on {receipt.resource_id}")
        print(f"    Approved by: {receipt.approved_by}")
        print(f"    Grant: {receipt.elevation_grant_id}")
    print()
    print("Evidence chain valid:", vault.verify_chain())


if __name__ == "__main__":
    run_infrastructure_scenario()
