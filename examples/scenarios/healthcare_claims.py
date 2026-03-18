"""
Healthcare Claims Processing Scenario.

Demonstrates CIAF-LCM controls for HIPAA-regulated healthcare workflows.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ciaf_agents.core import Identity, Resource, ActionRequest, Permission, RoleDefinition
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine, same_department_only
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


def setup_healthcare_scenario():
    """
    Set up a healthcare claims processing scenario with HIPAA compliance controls.
    
    Key controls:
    - Department-based isolation (claims processors can't access billing data)
    - Sensitive actions require PAM elevation
    - All PHI access is recorded in evidence vault
    """
    iam = IAMStore()
    pam = PAMStore()
    vault = EvidenceVault(signing_secret="healthcare-demo-secret")
    policy = PolicyEngine(iam, pam)
    executor = ToolExecutor(policy, vault, pam)

    # Define roles
    claims_processor_role = RoleDefinition(
        name="claims_processor",
        permissions=[
            Permission("read_claim", "claim", same_department_only),
            Permission("update_claim_status", "claim", same_department_only),
            Permission("send_claim_notification", "email", same_department_only),
        ]
    )

    medical_coder_role = RoleDefinition(
        name="medical_coder",
        permissions=[
            Permission("read_patient_record", "patient_record", same_department_only),
            Permission("read_claim", "claim", same_department_only),
            Permission("assign_diagnosis_codes", "claim", same_department_only),
        ]
    )

    iam.add_role(claims_processor_role)
    iam.add_role(medical_coder_role)

    # Create agent identities
    claims_agent = Identity(
        principal_id="agent-claims-processor-001",
        principal_type="agent",
        display_name="Claims Processing Agent",
        roles={"claims_processor"},
        attributes={
            "tenant": "midwest-health",
            "department": "claims",
            "hipaa_trained": True,
        }
    )

    coding_agent = Identity(
        principal_id="agent-medical-coder-001",
        principal_type="agent",
        display_name="Medical Coding Agent",
        roles={"medical_coder"},
        attributes={
            "tenant": "midwest-health",
            "department": "coding",
            "hipaa_trained": True,
        }
    )

    iam.add_identity(claims_agent)
    iam.add_identity(coding_agent)

    return iam, pam, vault, executor


def run_healthcare_scenario():
    """Run the healthcare scenario."""
    print("Healthcare Claims Processing Scenario")
    print("=" * 80)
    
    iam, pam, vault, executor = setup_healthcare_scenario()
    
    claims_agent = iam.identities["agent-claims-processor-001"]
    
    # Example: Process a claim
    claim_resource = Resource(
        resource_id="claim-2026-1234",
        resource_type="claim",
        owner_tenant="midwest-health",
        attributes={"department": "claims", "patient_id": "P-98765"}
    )
    
    request = ActionRequest(
        action="update_claim_status",
        resource=claim_resource,
        params={"new_status": "approved", "amount": 1250.00},
        justification="Claim meets approval criteria per policy HC-2026-03",
        requested_by=claims_agent
    )
    
    result = executor.execute(request)
    print(f"Result: {result['status']}")
    print(f"Receipt ID: {result['receipt']['receipt_id']}")
    print()
    print("Evidence chain valid:", vault.verify_chain())


if __name__ == "__main__":
    run_healthcare_scenario()
