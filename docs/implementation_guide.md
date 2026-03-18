# Implementation Guide

## Getting Started

This guide walks through implementing CIAF-LCM Agentic Execution Boundaries for your AI agents.

## Prerequisites

- Python 3.9 or later
- Understanding of IAM/RBAC concepts
- Inventory of AI agents and their tool access patterns
- Classification of actions by risk level

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/CIAF_LMC_Agentic_AI.git
cd CIAF_LMC_Agentic_AI/ciaf_agents

# Install dependencies
pip install -r requirements.txt

# Run tests to verify installation
pytest tests/
```

## Implementation Steps

### Step 1: Inventory and Classification

Before implementing controls, document your current state:

```python
# inventory.py
agents_inventory = {
    "agent-claims-001": {
        "purpose": "Process healthcare claims",
        "current_access": ["claims_db", "email_system", "crm"],
        "risk_level": "medium",
        "owner": "claims-team@example.com"
    },
    "agent-finance-001": {
        "purpose": "Approve payment workflows",
        "current_access": ["payment_system", "approval_system"],
        "risk_level": "high",
        "owner": "finance-ops@example.com"
    }
}

# Classify actions by sensitivity
action_classification = {
    "read_record": "routine",
    "update_status": "routine",
    "send_internal_email": "routine",
    "send_external_email": "sensitive",
    "approve_payment": "privileged",
    "delete_record": "privileged",
    "export_patient_data": "privileged",
    "modify_prod_config": "privileged"
}
```

### Step 2: Define Roles and Permissions

Create role definitions based on job functions:

```python
from ciaf_agents.iam import RoleDefinition, Permission
from ciaf_agents.policy import any_condition, same_tenant_only

# Example: Healthcare Claims Agent Role
claims_agent_role = RoleDefinition(
    name="claims_processor",
    permissions=[
        Permission(
            action="read_record",
            resource_type="claim",
            conditions=same_tenant_only
        ),
        Permission(
            action="update_claim_status",
            resource_type="claim",
            conditions=same_tenant_only
        ),
        Permission(
            action="send_internal_email",
            resource_type="email",
            conditions=any_condition
        )
    ]
)

# Example: Finance Agent Role
finance_agent_role = RoleDefinition(
    name="payment_reviewer",
    permissions=[
        Permission(
            action="read_payment",
            resource_type="payment",
            conditions=same_tenant_only
        ),
        Permission(
            action="approve_payment",
            resource_type="payment",
            conditions=same_tenant_only
        )
    ]
)
```

### Step 3: Provision Agent Identities

Create unique identities for each agent:

```python
from ciaf_agents.core import Identity

claims_agent = Identity(
    principal_id="agent-claims-001",
    principal_type="agent",
    display_name="Healthcare Claims Processor",
    roles={"claims_processor"},
    attributes={
        "tenant": "acme-health",
        "department": "claims",
        "environment": "production",
        "owner": "claims-team@example.com",
        "allowed_email_domains": ["acme-health.com", "partners.com"]
    }
)

finance_agent = Identity(
    principal_id="agent-finance-001",
    principal_type="agent",
    display_name="Payment Approval Agent",
    roles={"payment_reviewer"},
    attributes={
        "tenant": "acme-health",
        "department": "finance",
        "environment": "production",
        "owner": "finance-ops@example.com"
    }
)
```

### Step 4: Initialize the Control System

Set up the IAM, PAM, Policy, and Evidence components:

```python
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor

# Initialize stores
iam_store = IAMStore()
pam_store = PAMStore()

# Register roles
iam_store.add_role(claims_agent_role)
iam_store.add_role(finance_agent_role)

# Register identities
iam_store.add_identity(claims_agent)
iam_store.add_identity(finance_agent)

# Initialize policy engine
policy_engine = PolicyEngine(
    iam=iam_store,
    pam=pam_store,
    sensitive_actions={
        "send_external_email",
        "export_data",
        "delete_record"
    },
    privileged_actions={
        "approve_payment",
        "modify_prod_config",
        "export_patient_data"
    }
)

# Initialize evidence vault with signing secret
# NOTE: In production, use a secure key management system
evidence_vault = EvidenceVault(
    signing_secret=os.environ["CIAF_SIGNING_SECRET"]
)

# Initialize tool executor
executor = ToolExecutor(
    policy_engine=policy_engine,
    vault=evidence_vault,
    pam=pam_store
)
```

### Step 5: Configure Sensitive Actions

Define which actions require PAM elevation:

```python
# policy_config.py
SENSITIVE_ACTION_CONFIG = {
    "approve_payment": {
        "threshold_amount": 10000,  # Require elevation above this
        "requires_dual_approval": True,
        "max_grant_duration_minutes": 15,
        "allowed_approvers": ["cfo@example.com", "finance-director@example.com"]
    },
    "export_patient_data": {
        "requires_dual_approval": True,
        "max_grant_duration_minutes": 30,
        "allowed_approvers": ["compliance-officer@example.com"],
        "post_export_review": True
    },
    "modify_prod_config": {
        "requires_change_ticket": True,
        "max_grant_duration_minutes": 60,
        "allowed_approvers": ["platform-lead@example.com"]
    }
}
```

### Step 6: Implement Action Execution

Wrap all agent tool calls through the executor:

```python
from ciaf_agents.core import ActionRequest, Resource

def agent_execute_action(
    agent_id: str,
    action: str,
    resource_id: str,
    resource_type: str,
    params: dict,
    justification: str
) -> dict:
    """
    Execute an agent action with full IAM/PAM/Evidence controls.
    """
    # Resolve agent identity
    identity = iam_store.identities.get(agent_id)
    if not identity:
        return {"status": "error", "reason": "Unknown agent identity"}
    
    # Create resource reference
    resource = Resource(
        resource_id=resource_id,
        resource_type=resource_type,
        owner_tenant=identity.attributes.get("tenant"),
        attributes={}  # Add resource-specific attributes
    )
    
    # Create action request
    request = ActionRequest(
        action=action,
        resource=resource,
        params=params,
        justification=justification,
        requested_by=identity
    )
    
    # Execute through controlled path
    result = executor.execute(request)
    
    return result

# Example usage
result = agent_execute_action(
    agent_id="agent-claims-001",
    action="read_record",
    resource_id="claim-12345",
    resource_type="claim",
    params={"fields": ["status", "amount"]},
    justification="Review pending claim for processing"
)

print(result)
```

### Step 7: Implement Elevation Grant Workflow

Create a workflow for handling elevation requests:

```python
def request_elevation(
    agent_id: str,
    action: str,
    resource_type: str,
    reason: str,
    ticket_id: str
) -> dict:
    """
    Request privilege elevation for a sensitive action.
    In production, this would integrate with your approval system.
    """
    # Validate request
    agent = iam_store.identities.get(agent_id)
    if not agent:
        return {"status": "error", "reason": "Unknown agent"}
    
    # In production: Send to approval system, wait for human decision
    # For demo: Auto-approve with logging
    print(f"Elevation requested: {agent_id} for {action} on {resource_type}")
    print(f"Reason: {reason}")
    print(f"Ticket: {ticket_id}")
    
    # Issue grant (in production, only after approval)
    grant = pam_store.issue_grant(
        principal_id=agent_id,
        allowed_actions={action},
        resource_types={resource_type},
        reason=reason,
        approved_by="system-approval@example.com",  # In prod: actual approver
        duration_minutes=15,
        ticket_id=ticket_id
    )
    
    return {
        "status": "granted",
        "grant_id": grant.grant_id,
        "expires_at": grant.expires_at.isoformat()
    }

# Example: Request elevation for payment approval
elevation_result = request_elevation(
    agent_id="agent-finance-001",
    action="approve_payment",
    resource_type="payment",
    reason="Supervisor approved high-value vendor payment",
    ticket_id="CHG-2026-00123"
)

# Now the agent can execute the privileged action
if elevation_result["status"] == "granted":
    result = agent_execute_action(
        agent_id="agent-finance-001",
        action="approve_payment",
        resource_id="payment-98765",
        resource_type="payment",
        params={"amount": 25000, "currency": "USD"},
        justification="Execute approved payment per ticket CHG-2026-00123"
    )
```

### Step 8: Implement Evidence Review

Create tools to review the evidence chain:

```python
def audit_agent_actions(agent_id: str, hours: int = 24) -> list:
    """
    Review all actions by an agent in the last N hours.
    """
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    agent_receipts = [
        receipt for receipt in evidence_vault.receipts
        if receipt.principal_id == agent_id and receipt.timestamp >= cutoff
    ]
    
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "action": r.action,
            "resource": f"{r.resource_type}/{r.resource_id}",
            "decision": r.decision,
            "reason": r.reason,
            "grant_id": r.elevation_grant_id
        }
        for r in agent_receipts
    ]

def verify_evidence_integrity() -> bool:
    """
    Verify the cryptographic integrity of the evidence chain.
    """
    return evidence_vault.verify_chain()

# Example usage
print("Agent audit trail:")
print(json.dumps(audit_agent_actions("agent-finance-001"), indent=2))

print("\nEvidence chain integrity:", verify_evidence_integrity())
```

### Step 9: Add Custom Policy Conditions

Implement business-specific policy logic:

```python
def payment_amount_check(identity: Identity, resource: Resource, params: dict) -> bool:
    """
    Custom condition: Agent can only approve payments under their limit.
    """
    agent_limit = identity.attributes.get("payment_limit", 0)
    payment_amount = float(params.get("amount", 0))
    return payment_amount <= agent_limit

def business_hours_only(identity: Identity, resource: Resource, params: dict) -> bool:
    """
    Custom condition: Action only allowed during business hours.
    """
    from datetime import datetime
    now = datetime.now()
    return 9 <= now.hour < 17 and now.weekday() < 5  # Mon-Fri, 9am-5pm

def data_classification_check(identity: Identity, resource: Resource, params: dict) -> bool:
    """
    Custom condition: Agent clearance must match data classification.
    """
    agent_clearance = identity.attributes.get("data_clearance", 0)
    data_classification = resource.attributes.get("classification", 0)
    return agent_clearance >= data_classification

# Use in permission definitions
restricted_permission = Permission(
    action="approve_payment",
    resource_type="payment",
    conditions=lambda i, r, p: (
        same_tenant_only(i, r, p) and
        payment_amount_check(i, r, p) and
        business_hours_only(i, r, p)
    )
)
```

### Step 10: Integrate with Existing Systems

#### Integration with SIEM

```python
def export_receipts_to_siem(siem_endpoint: str, batch_size: int = 100):
    """
    Export evidence receipts to SIEM for correlation and alerting.
    """
    import requests
    
    for i in range(0, len(evidence_vault.receipts), batch_size):
        batch = evidence_vault.receipts[i:i+batch_size]
        
        events = [
            {
                "timestamp": r.timestamp.isoformat(),
                "event_type": "agent_action",
                "agent_id": r.principal_id,
                "action": r.action,
                "resource": r.resource_id,
                "decision": r.decision,
                "elevation": r.elevation_grant_id is not None,
                "receipt_id": r.receipt_id,
                "correlation_id": r.correlation_id
            }
            for r in batch
        ]
        
        requests.post(siem_endpoint, json={"events": events})
```

#### Integration with Change Management

```python
def validate_change_ticket(ticket_id: str) -> bool:
    """
    Validate that a change ticket exists and is approved.
    Integrate with ServiceNow, Jira, etc.
    """
    # Example: Call change management API
    # response = requests.get(f"https://changem.example.com/api/tickets/{ticket_id}")
    # return response.json().get("status") == "approved"
    
    # For demo: Simple validation
    return ticket_id.startswith("CHG-") and len(ticket_id) > 8
```

## Testing

### Unit Tests

```python
# tests/test_policy.py
def test_policy_denies_cross_tenant_access():
    """Test that agents cannot access resources in other tenants."""
    # Setup
    iam = IAMStore()
    pam = PAMStore()
    policy = PolicyEngine(iam, pam)
    
    agent = Identity(
        principal_id="test-agent",
        principal_type="agent",
        display_name="Test Agent",
        roles={"reader"},
        attributes={"tenant": "tenant-a"}
    )
    
    resource = Resource(
        resource_id="resource-123",
        resource_type="document",
        owner_tenant="tenant-b",  # Different tenant!
        attributes={}
    )
    
    request = ActionRequest(
        action="read_document",
        resource=resource,
        params={},
        justification="Test",
        requested_by=agent
    )
    
    # Execute
    decision = policy.evaluate(request)
    
    # Assert
    assert not decision.allowed
    assert "cross-tenant" in decision.reason.lower()
```

### Integration Tests

```python
# tests/test_integration.py
def test_full_elevation_workflow():
    """Test complete PAM elevation workflow."""
    iam, pam, vault, executor = build_demo_system()
    
    agent = iam.identities["agent-finance-001"]
    resource = Resource(
        resource_id="payment-999",
        resource_type="payment",
        owner_tenant="acme-health",
        attributes={}
    )
    
    # First attempt should be blocked
    request = ActionRequest(
        action="approve_payment",
        resource=resource,
        params={"amount": 50000},
        justification="Large payment",
        requested_by=agent
    )
    
    result1 = executor.execute(request)
    assert result1["status"] == "blocked"
    assert result1["requires_elevation"] == True
    
    # Issue elevation grant
    grant = pam.issue_grant(
        principal_id=agent.principal_id,
        allowed_actions={"approve_payment"},
        resource_types={"payment"},
        reason="CFO approved",
        approved_by="cfo@example.com",
        duration_minutes=15,
        ticket_id="CHG-TEST-001"
    )
    
    # Retry should succeed
    result2 = executor.execute(request)
    assert result2["status"] == "ok"
    assert "receipt" in result2
```

## Production Deployment

### Configuration Management

Create environment-specific configurations:

```yaml
# config/production.yaml
environment: production

iam:
  identity_provider: "oauth2"
  credential_rotation_days: 90
  
pam:
  default_grant_duration_minutes: 15
  max_grant_duration_minutes: 120
  require_approval_for_extensions: true
  
policy:
  default_deny: true
  cache_ttl_seconds: 300
  
evidence:
  signing_algorithm: "hmac-sha256"
  storage_backend: "s3"
  storage_config:
    bucket: "ciaf-evidence-prod"
    region: "us-east-1"
    encryption: "AES256"
  retention_days: 2555  # 7 years
  
monitoring:
  siem_export_enabled: true
  siem_endpoint: "https://siem.example.com/api/events"
  metrics_endpoint: "https://metrics.example.com/api/v1/push"
```

### Security Hardening

```python
# Secure credential management
import boto3
from botocore.exceptions import ClientError

def get_signing_secret() -> str:
    """
    Retrieve signing secret from AWS Secrets Manager.
    """
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    
    try:
        response = client.get_secret_value(SecretId='ciaf-lmc-signing-key')
        return response['SecretString']
    except ClientError as e:
        raise Exception(f"Failed to retrieve signing secret: {e}")

# Use in production
vault = EvidenceVault(signing_secret=get_signing_secret())
```

### Monitoring and Alerting

```python
# monitoring.py
from dataclasses import dataclass
from typing import List
import time

@dataclass
class Alert:
    severity: str
    message: str
    agent_id: str
    timestamp: float

def detect_anomalies(vault: EvidenceVault) -> List[Alert]:
    """
    Analyze evidence for suspicious patterns.
    """
    alerts = []
    now = time.time()
    last_hour = now - 3600
    
    # Check for excessive denials
    recent_receipts = [
        r for r in vault.receipts
        if r.timestamp.timestamp() >= last_hour
    ]
    
    denials_by_agent = {}
    for receipt in recent_receipts:
        if receipt.decision == "deny":
            denials_by_agent[receipt.principal_id] = \
                denials_by_agent.get(receipt.principal_id, 0) + 1
    
    for agent_id, denial_count in denials_by_agent.items():
        if denial_count > 10:  # Threshold
            alerts.append(Alert(
                severity="high",
                message=f"Excessive denials: {denial_count} in 1 hour",
                agent_id=agent_id,
                timestamp=now
            ))
    
    return alerts
```

## Best Practices

1. **Never hardcode credentials** - Use environment variables or secret management
2. **Rotate signing keys regularly** - Implement key rotation with overlap period
3. **Monitor denial patterns** - High denial rates indicate misconfiguration or attack
4. **Set aggressive grant expiry** - Start with 15 minutes, only extend if needed
5. **Require justifications** - Every action should have business context
6. **Audit regularly** - Review receipts and grants on a schedule
7. **Test elevation workflows** - Ensure approval processes work under load
8. **Backup evidence vault** - Receipt loss breaks accountability
9. **Version policies** - Track policy changes with receipts
10. **Document exceptions** - Break-glass access should be pre-authorized and logged

## Troubleshooting

### Common Issues

**Problem**: Agent actions always denied

```python
# Check identity exists and roles are assigned
identity = iam_store.identities.get("agent-id")
print(f"Roles: {identity.roles}")

# Check role has required permission
for role_name in identity.roles:
    role = iam_store.role_definitions.get(role_name)
    print(f"Role {role_name} permissions: {role.permissions}")
```

**Problem**: Elevation grants not found

```python
# Check grant was issued and hasn't expired
grant = pam_store.find_active_grant(
    principal_id="agent-id",
    action="approve_payment",
    resource_type="payment"
)
if not grant:
    print("No active grant found")
else:
    print(f"Grant expires: {grant.expires_at}")
```

**Problem**: Chain verification fails

```python
# Identify which receipt broke the chain
for i, receipt in enumerate(evidence_vault.receipts):
    # Check hash
    # Check signature
    # Check prior link
    # Print results
    pass
```

## Next Steps

1. Review the [Architecture](architecture.md) document for deeper understanding
2. Explore [Example Scenarios](../examples/scenarios/) for real-world patterns
3. Read the [Whitepaper](whitepaper_agentic_execution_boundaries.md) for governance context
4. Join the community discussions and share your implementation

---

For questions or support, contact: ciaf-lmc-support@example.com
