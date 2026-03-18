# API Reference

Complete reference for CIAF-LCM Agentic Execution Boundaries.

## Installation

```bash
# Install from local directory
cd ciaf_agents
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install with cloud storage backends
pip install -e ".[aws]"     # For S3 evidence storage
pip install -e ".[azure]"   # For Azure Blob storage
pip install -e ".[gcp]"     # For GCS storage
```

**Import Pattern**: After installation, use `from ciaf_agents.MODULE import CLASS` for imports.

## Core Types

### Identity

Represents a unique digital principal (agent, user, or service).

```python
from ciaf_agents.core import Identity

identity = Identity(
    principal_id="agent-001",           # Unique identifier
    principal_type="agent",             # "agent", "user", or "service"
    display_name="Claims Agent",        # Human-readable name
    roles={"claims_processor"},         # Set of assigned role names
    attributes={                        # Contextual attributes
        "tenant": "acme-health",
        "department": "claims",
        "environment": "production"
    }
)
```

**Attributes:**
- `principal_id` (str): Unique identifier for the principal
- `principal_type` (str): Classification - "agent", "user", or "service"
- `display_name` (str): Human-readable name
- `roles` (Set[str]): Assigned role names
- `attributes` (Dict[str, Any]): Context like tenant, department, environment

**Immutable**: Identity objects are frozen dataclasses and cannot be modified after creation.

---

### Resource

Represents a target resource for an action.

```python
from ciaf_agents.core import Resource

resource = Resource(
    resource_id="claim-12345",          # Unique resource identifier
    resource_type="claim",              # Type classification
    owner_tenant="acme-health",         # Owning tenant/organization
    attributes={                        # Resource-specific metadata
        "department": "claims",
        "data_classification": "phi"
    }
)
```

**Attributes:**
- `resource_id` (str): Unique identifier
- `resource_type` (str): Type like "email", "payment", "claim", "database"
- `owner_tenant` (str): Owning tenant/organization
- `attributes` (Dict[str, Any]): Resource-specific metadata

---

### ActionRequest

Represents a request to perform an action.

```python
from ciaf_agents.core import ActionRequest, Identity, Resource

request = ActionRequest(
    action="update_claim_status",       # Action to perform
    resource=resource,                  # Target resource
    params={                            # Action-specific parameters
        "status": "approved",
        "reason": "All criteria met"
    },
    justification="Patient meets all criteria per policy",
    requested_by=identity,              # Requesting identity
    correlation_id="optional-trace-id"  # Optional tracking ID
)
```

**Attributes:**
- `action` (str): Action to perform (e.g., "read_record", "approve_payment")
- `resource` (Resource): Target resource
- `params` (Dict[str, Any]): Action-specific parameters
- `justification` (str): Business justification
- `requested_by` (Identity): Requesting identity
- `correlation_id` (str): Optional tracking ID (auto-generated if not provided)

---

### Permission

Defines a permission with optional conditions.

```python
from ciaf_agents.core import Permission
from ciaf_agents.policy.conditions import same_tenant_only

permission = Permission(
    action="read_claim",                # Action this permission allows
    resource_type="claim",              # Resource type ("*" for all)
    conditions=same_tenant_only         # Optional condition function
)

# Permission without conditions
unrestricted_perm = Permission(
    action="read_public_data",
    resource_type="public_data",
    conditions=None                     # No additional conditions
)
```

**Attributes:**
- `action` (str): Action this permission allows
- `resource_type` (str): Resource type ("*" for all types)
- `conditions` (Optional[Callable]): Function to evaluate contextual conditions

**Methods:**
- `matches(identity, resource, params) -> bool`: Check if permission applies

---

### RoleDefinition

Named collection of permissions.

```python
from ciaf_agents.core import RoleDefinition, Permission
from ciaf_agents.policy.conditions import same_department_only, any_condition

role = RoleDefinition(
    name="claims_processor",
    permissions=[
        Permission("read_claim", "claim", same_department_only),
        Permission("update_claim_status", "claim", same_department_only),
        Permission("send_notification", "email", any_condition)
    ]
)
```

**Attributes:**
- `name` (str): Unique role name
- `permissions` (List[Permission]): List of permissions granted by this role

---

### ElevationGrant

Time-bound privilege grant for sensitive actions.

```python
from ciaf_agents.core import ElevationGrant

# Grants are typically created via PAMStore.issue_grant()
# This shows the structure
grant = ElevationGrant(
    grant_id="grant-abc123",
    principal_id="agent-001",
    allowed_actions={"approve_payment", "delete_record"},
    resource_types={"payment", "claim"},
    reason="Approved cleanup per TASK-456",
    approved_by="manager@example.com",
    issued_at=datetime.utcnow(),
    expires_at=datetime.utcnow() + timedelta(minutes=30),
    ticket_id="TASK-456",
    metadata={"priority": "high"}
)
```

**Attributes:**
- `grant_id` (str): Unique grant identifier
- `principal_id` (str): Who is elevated
- `allowed_actions` (Set[str]): Permitted actions
- `resource_types` (Set[str]): Allowed resource types
- `reason` (str): Business justification
- `approved_by` (str): Approving authority
- `issued_at` (datetime): When grant was issued
- `expires_at` (datetime): Expiration timestamp
- `ticket_id` (str): Reference to approval ticket
- `metadata` (Dict[str, Any]): Additional metadata

**Methods:**
- `is_active() -> bool`: Check if grant is currently valid (not expired)

---

### PolicyDecision

Result of policy evaluation.

```python
from ciaf_agents.core import PolicyDecision

decision = PolicyDecision(
    allowed=True,                       # Whether action is allowed
    requires_elevation=False,           # Whether PAM grant is needed
    reason="Approved by IAM policy",    # Explanation
    matched_role="claims_processor",    # Role that granted permission
    obligations=["log_access"]          # Additional requirements
)
```

**Attributes:**
- `allowed` (bool): Whether action is allowed
- `requires_elevation` (bool): Whether PAM elevation is needed
- `reason` (str): Human-readable explanation
- `matched_role` (Optional[str]): Role that provided permission
- `obligations` (List[str]): Additional requirements (e.g., "heightened_logging")

---

### EvidenceReceipt

Cryptographically signed audit record.

```python
from ciaf_agents.core import EvidenceReceipt

# Receipts are created by EvidenceVault.append()
# This shows the structure
receipt = EvidenceReceipt(
    receipt_id="receipt-xyz789",
    timestamp=datetime.utcnow(),
    principal_id="agent-001",
    principal_type="agent",
    action="approve_payment",
    resource_id="payment-456",
    resource_type="payment",
    correlation_id="trace-123",
    decision="allow",
    reason="Approved with active PAM grant",
    elevation_grant_id="grant-abc123",
    approved_by="manager@example.com",
    params_hash="sha256_hash_of_params",
    policy_obligations=["heightened_logging"],
    prior_receipt_hash="hash_of_previous_receipt",
    receipt_hash="sha256_hash_of_this_receipt",
    signature="hmac_signature"
)
```

**Methods:**
- `to_dict() -> Dict[str, Any]`: Convert to dictionary for export

---

## IAM Store

Identity and Access Management store.

```python
from ciaf_agents.iam import IAMStore
from ciaf_agents.core import Identity, RoleDefinition, Permission

iam = IAMStore()

# Add role
role = RoleDefinition(
    name="data_reader",
    permissions=[Permission("read_data", "database")]
)
iam.add_role(role)

# Add identity
identity = Identity(
    principal_id="agent-001",
    principal_type="agent",
    display_name="Analytics Agent",
    roles={"data_reader"},
    attributes={"tenant": "acme"}
)
iam.add_identity(identity)

# Get identity
agent = iam.get_identity("agent-001")

# Get permissions
permissions = iam.get_identity_permissions(identity)
# Returns: [(role_name, Permission), ...]

# Update roles
iam.update_identity_roles("agent-001", {"data_reader", "report_generator"})

# Revoke identity
iam.revoke_identity("agent-001")

# List by role
agents = iam.list_identities_by_role("data_reader")
```

**Methods:**
- `add_role(role: RoleDefinition)`: Register a role definition
- `add_identity(identity: Identity)`: Register an identity
- `get_identity(principal_id: str) -> Identity`: Retrieve identity by ID
- `get_identity_permissions(identity: Identity) -> List[Tuple[str, Permission]]`: Get all permissions
- `update_identity_roles(principal_id: str, roles: Set[str])`: Update role assignments
- `revoke_identity(principal_id: str)`: Remove an identity (emergency kill switch)
- `list_identities_by_role(role_name: str) -> List[Identity]`: Find identities with role

---

## PAM Store

Privileged Access Management store.

```python
from ciaf_agents.pam import PAMStore

pam = PAMStore()

# Issue a grant
grant = pam.issue_grant(
    principal_id="agent-001",
    allowed_actions={"approve_payment", "delete_record"},
    resource_types={"payment", "claim"},
    reason="Approved data cleanup per TASK-123",
    approved_by="manager@example.com",
    duration_minutes=30,
    ticket_id="TASK-123",
    metadata={"priority": "high"}
)

# Find active grant
active_grant = pam.find_active_grant(
    principal_id="agent-001",
    action="approve_payment",
    resource_type="payment"
)

# Get all active grants for a principal
grants = pam.get_active_grants_for_principal("agent-001")

# Extend grant
pam.extend_grant(grant.grant_id, additional_minutes=15)

# Revoke grant
pam.revoke_grant(grant.grant_id)

# Revoke all grants for a principal
pam.revoke_all_grants_for_principal("agent-001")

# Cleanup expired grants
pam.cleanup_expired_grants()
```

**Methods:**
- `issue_grant(...)`: Create a new elevation grant
- `find_active_grant(principal_id, action, resource_type) -> Optional[ElevationGrant]`: Find matching grant
- `get_active_grants_for_principal(principal_id) -> List[ElevationGrant]`: Get all active grants
- `extend_grant(grant_id, additional_minutes)`: Extend grant duration
- `revoke_grant(grant_id)`: Revoke a specific grant
- `revoke_all_grants_for_principal(principal_id)`: Revoke all grants for principal
- `cleanup_expired_grants()`: Remove expired grants from memory

---

## Policy Engine

Policy evaluation engine.

```python
from ciaf_agents.policy import PolicyEngine
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore

iam = IAMStore()
pam = PAMStore()

# Create policy engine with sensitive actions
policy = PolicyEngine(
    iam=iam,
    pam=pam,
    sensitive_actions={"approve_payment", "delete_record", "export_data"}
)

# Evaluate a request
decision = policy.evaluate(request)

if decision.allowed:
    # Execute action
    print("Action allowed:", decision.reason)
elif decision.requires_elevation:
    # Need PAM grant
    print("Elevation required:", decision.reason)
else:
    # Denied
    print("Action denied:", decision.reason)

# Manage sensitive actions
policy.add_sensitive_action("new_sensitive_action")
policy.remove_sensitive_action("no_longer_sensitive")
is_sensitive = policy.is_sensitive_action("approve_payment")
```

**Methods:**
- `evaluate(request: ActionRequest) -> PolicyDecision`: Evaluate action request
- `add_sensitive_action(action: str)`: Mark action as sensitive
- `remove_sensitive_action(action: str)`: Remove from sensitive list
- `is_sensitive_action(action: str) -> bool`: Check if action is sensitive

**Decision Flow:**
1. Check IAM permissions (RBAC/ABAC)
2. Enforce boundary policies (tenant isolation)
3. Check for sensitive actions requiring PAM
4. Apply runtime constraints (thresholds, allowlists)

---

## Evidence Vault

Tamper-evident audit trail.

```python
from ciaf_agents.evidence import EvidenceVault

vault = EvidenceVault(signing_secret="your-secure-secret-key")

# Append a receipt
receipt = vault.append(
    request=action_request,
    decision=policy_decision,
    grant=elevation_grant  # Optional, if elevated
)

# Verify chain integrity
is_valid = vault.verify_chain()

# Verify single receipt
is_valid = vault.verify_receipt(receipt)

# Query receipts
receipts_by_principal = vault.get_receipts_by_principal("agent-001")
denied_receipts = vault.get_denied_receipts()
elevated_receipts = vault.get_elevated_receipts()
receipts_by_action = vault.get_receipts_by_action("approve_payment")

# Export receipts
json_data = vault.export_receipts(format="json")
jsonl_data = vault.export_receipts(format="jsonl")
```

**Methods:**
- `append(request, decision, grant) -> EvidenceReceipt`: Create and append receipt
- `verify_chain() -> bool`: Verify entire receipt chain integrity
- `verify_receipt(receipt) -> bool`: Verify single receipt
- `get_receipts_by_principal(principal_id) -> List[EvidenceReceipt]`: Find by principal
- `get_denied_receipts() -> List[EvidenceReceipt]`: Find denied actions
- `get_elevated_receipts() -> List[EvidenceReceipt]`: Find elevated actions
- `get_receipts_by_action(action) -> List[EvidenceReceipt]`: Find by action
- `export_receipts(format) -> str`: Export in JSON or JSONL format

---

## Tool Executor

Mediated tool execution with full IAM/PAM/Evidence controls.

```python
from ciaf_agents.execution import ToolExecutor, ToolRegistry

# Create executor
executor = ToolExecutor(
    policy_engine=policy,
    vault=vault,
    pam=pam
)

# Register a tool
def send_email(to: str, subject: str, body: str) -> dict:
    # Implementation
    return {"status": "sent", "message_id": "msg-123"}

executor.registry.register(
    name="send_email",
    handler=send_email,
    description="Send an email message"
)

# Execute with full controls
result = executor.execute(action_request)

# Dry run (policy check only, no execution)
result = executor.dry_run(action_request)

# Batch execution
results = executor.execute_batch([request1, request2, request3])

# Access registry
tool = executor.registry.get("send_email")
all_tools = executor.registry.list_tools()
```

**Methods:**
- `execute(request: ActionRequest) -> dict`: Execute with full controls
- `dry_run(request: ActionRequest) -> dict`: Policy check only
- `execute_batch(requests: List[ActionRequest]) -> List[dict]`: Execute multiple requests

**Tool Registry Methods:**
- `register(name, handler, description)`: Register a tool
- `get(name) -> Optional[Callable]`: Get tool handler
- `list_tools() -> List[str]`: List registered tools

---

## Policy Conditions

Pre-built condition functions for ABAC.

```python
from ciaf_agents.policy.conditions import (
    any_condition,
    same_tenant_only,
    same_department_only,
    production_environment_only,
    non_production_only
)

# Use in permissions
Permission("read_data", "database", same_tenant_only)
Permission("deploy_code", "service", production_environment_only)
Permission("test_feature", "service", non_production_only)
```

**Available Conditions:**
- `any_condition`: Always returns True (no restrictions)
- `same_tenant_only`: Requires identity.tenant == resource.owner_tenant
- `same_department_only`: Requires matching department attribute
- `production_environment_only`: Requires environment="production"
- `non_production_only`: Requires environment != "production"

**Custom Conditions:**
```python
def custom_condition(identity: Identity, resource: Resource, params: dict) -> bool:
    """Your custom logic here."""
    return identity.attributes.get("clearance_level", 0) >= 3

permission = Permission("read_classified", "document", custom_condition)
```

---

## Utilities

Helper functions for cryptography and data handling.

```python
from ciaf_agents.utils.helpers import (
    utc_now,
    canonical_json,
    sha256_hex,
    sign_receipt
)

# Get current UTC time
timestamp = utc_now()

# Create deterministic JSON
json_str = canonical_json({"key": "value"})

# Hash data
hash_value = sha256_hex(json_str)

# Sign data
signature = sign_receipt(data_dict, secret_key)
```

**Functions:**
- `utc_now() -> datetime`: Get current UTC time
- `canonical_json(obj) -> str`: Deterministic JSON serialization
- `sha256_hex(text: str) -> str`: SHA-256 hash as hex string
- `sign_receipt(data: dict, secret: str) -> str`: HMAC-SHA256 signature

---

## Complete Example

```python
from ciaf_agents.core import Identity, Resource, ActionRequest, Permission, RoleDefinition
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine, same_tenant_only
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor

# 1. Initialize system
iam = IAMStore()
pam = PAMStore()
vault = EvidenceVault(signing_secret="your-secret")
policy = PolicyEngine(iam, pam)
executor = ToolExecutor(policy, vault, pam)

# 2. Define roles
role = RoleDefinition(
    name="data_analyst",
    permissions=[
        Permission("read_data", "database", same_tenant_only),
        Permission("export_report", "report", same_tenant_only)
    ]
)
iam.add_role(role)

# 3. Create identity
agent = Identity(
    principal_id="agent-analytics-001",
    principal_type="agent",
    display_name="Analytics Agent",
    roles={"data_analyst"},
    attributes={"tenant": "acme", "department": "analytics"}
)
iam.add_identity(agent)

# 4. Execute action
resource = Resource(
    resource_id="customer_db",
    resource_type="database",
    owner_tenant="acme",
    attributes={}
)

request = ActionRequest(
    action="read_data",
    resource=resource,
    params={"query": "SELECT * FROM customers LIMIT 100"},
    justification="Weekly analytics report",
    requested_by=agent
)

result = executor.execute(request)
print(result)

# 5. Verify evidence
print(f"Chain valid: {vault.verify_chain()}")
print(f"Total receipts: {len(vault.receipts)}")
```
