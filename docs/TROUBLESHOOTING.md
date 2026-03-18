# Troubleshooting Guide

Common issues and solutions for CIAF-LCM Agentic Execution Boundaries.

## Installation Issues

### Import Error: "No module named 'ciaf_agents'"

**Problem:**
```python
ModuleNotFoundError: No module named 'ciaf_agents'
```

**Solutions:**

1. **Install the package** (recommended):
   ```bash
   cd ciaf_agents
   pip install -e .
   ```

2. **Add to Python path** (temporary):
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   ```

3. **Set PYTHONPATH** environment variable:
   ```bash
   # Windows PowerShell
   $env:PYTHONPATH = "D:\Github\CIAF_LMC_Agentic_AI"
   
   # Windows CMD
   set PYTHONPATH=D:\Github\CIAF_LMC_Agentic_AI
   
   # Linux/Mac
   export PYTHONPATH=/path/to/CIAF_LMC_Agentic_AI
   ```

### Import Error: Wrong path from examples/

**Problem:**
Running examples fails with import errors.

**Solution:**
Examples use relative paths. Run from the examples directory:
```bash
cd ciaf_agents/examples
python demo.py

# Or run from ciaf_agents root:
cd ciaf_agents
python examples/demo.py
```

---

## Policy Decision Issues

### Action Always Denied: "No matching permission"

**Problem:**
```
PolicyDecision(allowed=False, reason="Denied by IAM: no matching permission.")
```

**Debugging Steps:**

1. **Check role assignment**:
   ```python
   identity = iam.get_identity("agent-001")
   print(f"Roles: {identity.roles}")
   ```

2. **Check role exists**:
   ```python
   print(f"Available roles: {iam.role_definitions.keys()}")
   ```

3. **Check permissions in role**:
   ```python
   role = iam.role_definitions.get("your_role_name")
   if role:
       for perm in role.permissions:
           print(f"Action: {perm.action}, Type: {perm.resource_type}")
   ```

4. **Check action name matches exactly**:
   ```python
   # These are different!
   request.action = "read_record"    # ✓
   request.action = "read-record"    # ✗
   request.action = "readRecord"     # ✗
   ```

5. **Check resource type matches**:
   ```python
   # Permission expects "claim", but resource is "patient_claim"
   Permission("read_claim", "claim", ...)
   Resource(resource_id="123", resource_type="patient_claim", ...)  # ✗
   
   # Use wildcard or match exactly
   Permission("read_claim", "*", ...)  # ✓ Matches all types
   ```

### Cross-Tenant Access Denied

**Problem:**
```
PolicyDecision(allowed=False, reason="Denied by policy: cross-tenant access not allowed.")
```

**Cause:**
Identity tenant doesn't match resource owner tenant.

**Solution:**

1. **Check tenant attributes**:
   ```python
   print(f"Identity tenant: {identity.attributes.get('tenant')}")
   print(f"Resource tenant: {resource.owner_tenant}")
   ```

2. **If cross-tenant access is needed**, use a permission condition that allows it:
   ```python
   from ciaf_agents.policy.conditions import any_condition
   
   Permission("read_data", "database", any_condition)
   ```

3. **Or create custom condition**:
   ```python
   def allow_partner_tenants(identity, resource, params):
       identity_tenant = identity.attributes.get("tenant")
       partner_tenants = identity.attributes.get("partner_tenants", [])
       return resource.owner_tenant in [identity_tenant] + partner_tenants
   
   Permission("read_shared_data", "database", allow_partner_tenants)
   ```

### Permission Condition Returns False

**Problem:**
Permission exists but condition logic blocks access.

**Debugging:**

1. **Test condition in isolation**:
   ```python
   from ciaf_agents.policy.conditions import same_department_only
   
   result = same_department_only(identity, resource, {})
   print(f"Condition result: {result}")
   print(f"Identity dept: {identity.attributes.get('department')}")
   print(f"Resource dept: {resource.attributes.get('department')}")
   ```

2. **Common condition failures**:
   - `same_tenant_only`: Missing tenant attribute
   - `same_department_only`: Department attribute missing or mismatched
   - `production_environment_only`: Environment not set to "production"

---

## PAM Elevation Issues

### Action Requires Elevation

**Problem:**
```
PolicyDecision(allowed=False, requires_elevation=True, 
               reason="PAM elevation required for sensitive action.")
```

**Solution:**

1. **Issue a PAM grant**:
   ```python
   grant = pam.issue_grant(
       principal_id="agent-001",
       allowed_actions={"approve_payment"},
       resource_types={"payment"},
       reason="Approved batch payment processing",
       approved_by="manager@example.com",
       duration_minutes=30,
       ticket_id="TASK-456"
   )
   ```

2. **Retry the action** - the grant is now active:
   ```python
   result = executor.execute(request)  # Should succeed now
   ```

### Grant Already Expired

**Problem:**
Grant expired between issuance and use.

**Check:**
```python
grant = pam.find_active_grant("agent-001", "approve_payment", "payment")
if grant:
    print(f"Grant expires at: {grant.expires_at}")
    print(f"Is active: {grant.is_active()}")
else:
    print("No active grant found")
```

**Solution:**
Issue a new grant with longer duration:
```python
grant = pam.issue_grant(
    principal_id="agent-001",
    allowed_actions={"approve_payment"},
    resource_types={"payment"},
    reason="Extended processing time needed",
    approved_by="manager@example.com",
    duration_minutes=60,  # Longer duration
    ticket_id="TASK-456"
)
```

### Grant Doesn't Cover Action

**Problem:**
Grant exists but doesn't cover the specific action or resource type.

**Check:**
```python
grant = pam.find_active_grant("agent-001", "delete_record", "claim")
if grant:
    print(f"Allowed actions: {grant.allowed_actions}")
    print(f"Resource types: {grant.resource_types}")
```

**Solution:**
Issue grant covering the needed action:
```python
grant = pam.issue_grant(
    principal_id="agent-001",
    allowed_actions={"delete_record"},  # Add the action
    resource_types={"claim"},           # Add the resource type
    reason="...",
    approved_by="...",
    duration_minutes=30,
    ticket_id="..."
)
```

---

## Evidence Vault Issues

### Chain Verification Fails

**Problem:**
```python
vault.verify_chain()  # Returns False
```

**Causes:**
1. Receipt hash tampered
2. Signature invalid
3. Chain link broken

**Debug:**
```python
for i, receipt in enumerate(vault.receipts):
    is_valid = vault.verify_receipt(receipt)
    print(f"Receipt {i} ({receipt.receipt_id}): {'✓' if is_valid else '✗'}")
    
    if i > 0:
        prev_hash = vault.receipts[i-1].receipt_hash
        if receipt.prior_receipt_hash != prev_hash:
            print(f"  ⚠ Chain break: expected {prev_hash}, got {receipt.prior_receipt_hash}")
```

**Prevention:**
- Use WORM (write-once-read-many) storage
- Don't modify receipts after creation
- Rotate signing secrets carefully (keep old secrets for verification)

### Signing Secret Mismatch

**Problem:**
Old receipts can't be verified after changing secret.

**Solution:**
Keep a history of signing secrets:
```python
class EvidenceVaultWithRotation(EvidenceVault):
    def __init__(self, current_secret: str, historical_secrets: List[str] = None):
        super().__init__(signing_secret=current_secret)
        self.historical_secrets = historical_secrets or []
    
    def verify_receipt(self, receipt):
        # Try current secret
        if super().verify_receipt(receipt):
            return True
        
        # Try historical secrets
        for old_secret in self.historical_secrets:
            original_secret = self.signing_secret
            self.signing_secret = old_secret
            if super().verify_receipt(receipt):
                self.signing_secret = original_secret
                return True
            self.signing_secret = original_secret
        
        return False
```

---

## Tool Execution Issues

### Tool Not Found

**Problem:**
```
ValueError: Tool 'send_email' not found in registry
```

**Solution:**
Register the tool before executing:
```python
def send_email_handler(to, subject, body):
    # Implementation
    return {"status": "sent"}

executor.registry.register(
    name="send_email",
    handler=send_email_handler,
    description="Send email"
)
```

### Tool Execution Fails

**Problem:**
Tool raises exception during execution.

**Debug:**
1. **Test tool directly**:
   ```python
   handler = executor.registry.get("send_email")
   result = handler(**request.params)
   ```

2. **Check parameters**:
   ```python
   print(f"Request params: {request.params}")
   ```

3. **Use try-except in tool**:
   ```python
   def safe_tool(param1, param2):
       try:
           # Tool logic
           return {"status": "success", "data": result}
       except Exception as e:
           return {"status": "error", "error": str(e)}
   ```

---

## Performance Issues

### Slow Policy Evaluation

**Cause:**
Complex condition functions or large role sets.

**Solutions:**

1. **Cache identity permissions**:
   ```python
   class CachedIAMStore(IAMStore):
       def __init__(self):
           super().__init__()
           self._perm_cache = {}
       
       def get_identity_permissions(self, identity):
           cache_key = identity.principal_id
           if cache_key not in self._perm_cache:
               self._perm_cache[cache_key] = super().get_identity_permissions(identity)
           return self._perm_cache[cache_key]
   ```

2. **Simplify conditions**:
   ```python
   # Slow - database lookup
   def requires_db_check(identity, resource, params):
       return check_database(identity.principal_id)
   
   # Fast - attribute check
   def requires_attribute_check(identity, resource, params):
       return identity.attributes.get("clearance") == "high"
   ```

3. **Reduce role count** per identity.

### Large Evidence Vault

**Cause:**
Vault growing too large in memory.

**Solutions:**

1. **Export and archive regularly**:
   ```python
   # Export receipts
   export_data = vault.export_receipts(format="jsonl")
   
   # Write to storage
   with open(f"receipts_{date}.jsonl", "w") as f:
       f.write(export_data)
   
   # Clear old receipts (only if archived safely!)
   # vault.receipts = vault.receipts[-1000:]  # Keep last 1000
   ```

2. **Use external storage** (S3, Azure Blob, database):
   ```python
   class PersistentEvidenceVault(EvidenceVault):
       def append(self, request, decision, grant):
           receipt = super().append(request, decision, grant)
           # Write to database/storage immediately
           self.save_to_storage(receipt)
           return receipt
   ```

---

## Configuration Issues

### YAML Configuration Not Loading

**Problem:**
Configuration file not being read.

**Solution:**

1. **Install PyYAML**:
   ```bash
   pip install pyyaml
   ```

2. **Check file path**:
   ```python
   from pathlib import Path
   config_path = Path("config/example_config.yaml")
   print(f"Exists: {config_path.exists()}")
   print(f"Absolute: {config_path.absolute()}")
   ```

3. **Parse YAML**:
   ```python
   import yaml
   
   with open("config/example_config.yaml") as f:
       config = yaml.safe_load(f)
   
   # Use config values
   signing_secret = config["evidence"]["signing_algorithm"]
   ```

---

## Testing Issues

### Tests Fail with Import Errors

**Problem:**
Tests can't import modules.

**Solution:**

Use `conftest.py` to set up paths:
```python
# tests/conftest.py
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

### Coverage Report Shows Low Coverage

**Problem:**
Coverage doesn't match expectations.

**Debug:**
```bash
# Run with verbose output
pytest tests/ --cov=src --cov-report=term-missing -v

# Generate HTML report for detailed view
pytest tests/ --cov=src --cov-report=html

# Open htmlcov/index.html in browser
```

---

## Common Patterns & Solutions

### Question: How do I handle agent authentication?

**Answer:**
CIAF-LCM focuses on authorization after authentication. Implement authentication separately:

```python
# Example integration with JWT
import jwt

def authenticate_agent(token: str) -> Identity:
    """Authenticate and return identity."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    
    return iam.get_identity(payload["principal_id"])

# Then use in request
identity = authenticate_agent(request_token)
request = ActionRequest(
    action="...",
    resource=...,
    requested_by=identity,
    ...
)
```

### Question: How do I integrate with existing approval systems?

**Answer:**
Implement custom grant issuance workflow:

```python
class ApprovalIntegration:
    def __init__(self, pam_store, approval_api):
        self.pam = pam_store
        self.approval_api = approval_api
    
    def request_elevation(self, principal_id, action, reason):
        # Create approval ticket
        ticket = self.approval_api.create_ticket(
            requester=principal_id,
            action=action,
            justification=reason
        )
        
        # Wait for approval (async or webhook)
        return ticket.id
    
    def approve_elevation(self, ticket_id, approved_by):
        # Get ticket details
        ticket = self.approval_api.get_ticket(ticket_id)
        
        # Issue PAM grant
        grant = self.pam.issue_grant(
            principal_id=ticket.requester,
            allowed_actions={ticket.action},
            resource_types={"*"},
            reason=ticket.justification,
            approved_by=approved_by,
            duration_minutes=30,
            ticket_id=ticket_id
        )
        
        return grant
```

### Question: How do I set up monitoring and alerts?

**Answer:**
Monitor evidence vault and policy decisions:

```python
class MonitoredExecutor(ToolExecutor):
    def execute(self, request):
        result = super().execute(request)
        
        # Send metrics
        if result["status"] == "denied":
            self.alert_system.send_alert(
                severity="warning",
                message=f"Denied action: {request.action} by {request.requested_by.principal_id}",
                details=result
            )
        
        # Log to SIEM
        self.siem.log_event({
            "event_type": "agent_action",
            "principal": request.requested_by.principal_id,
            "action": request.action,
            "resource": request.resource.resource_id,
            "decision": result["decision"],
            "timestamp": result["receipt"]["timestamp"]
        })
        
        return result
```

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs** - enable detailed logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Review the examples** - see [examples/](../examples/) for working code

3. **Read the documentation**:
   - [Architecture](architecture.md)
   - [Implementation Guide](implementation_guide.md)
   - [API Reference](API_REFERENCE.md)

4. **File an issue** with:
   - Python version
   - Operating system
   - Full error message and stack trace
   - Minimal reproducible example
