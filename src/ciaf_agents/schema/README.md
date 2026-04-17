# CIAF Schema Documentation

This directory contains JSON Schema definitions for all core CIAF (Cognitive Insight Agentic Framework) data structures, policies, and configurations.

## Overview

The CIAF schema suite provides comprehensive validation for:
- **Agent definitions and capabilities**
- **Action requests and execution results**
- **IAM/PAM policies and decisions**
- **Identities, roles, and permissions**
- **Resources and access controls**
- **Cryptographic evidence receipts**
- **Policy engine configuration**

All schemas follow JSON Schema Draft 7 specification and are designed for:
- Type safety and validation
- Documentation and discoverability
- Governance and compliance
- Audit trail integration

---

## Schema Files

### Core Agent Schema

#### `agent.schema.json`
Defines complete agent specification with capabilities, boundaries, and governance controls.

**Key components:**
- Agent identity (ID, name, version, status)
- Capabilities (actions agent can perform)
- Execution boundaries (tenant isolation, rate limits, resource allowlists)
- Role assignments
- Audit requirements

**Use case:** Registering agents, enforcing agent execution boundaries, documenting agent capabilities.

**Example:**
```json
{
  "agent_id": "agent-001",
  "name": "Data Processor Agent",
  "agent_type": "task_specific",
  "status": "active",
  "capabilities": [
    {
      "name": "read_records",
      "action": "read",
      "resource_types": ["record"],
      "requires_elevation": false
    }
  ],
  "boundaries": {
    "tenant_isolation": true,
    "rate_limit_requests_per_min": 1000,
    "max_parallel_executions": 5
  }
}
```

---

### Request/Response Schemas

#### `action_request.schema.json`
Represents requests to perform actions submitted by agents or users.

**Key components:**
- Correlation ID for request tracking
- Identity of requester
- Target resource
- Action and parameters
- Justification and context

**Use case:** Validating incoming action requests before policy evaluation.

**Example:**
```json
{
  "correlation_id": "req-12345",
  "action": "read_record",
  "resource": {
    "resource_id": "rec-789",
    "resource_type": "record",
    "owner_tenant": "org-1"
  },
  "requested_by": {
    "principal_id": "agent-001",
    "principal_type": "agent",
    "display_name": "Data Processor"
  },
  "justification": "Daily batch processing"
}
```

---

#### `execution_result.schema.json`
Represents results from action execution including outcome and evidence receipt.

**Key components:**
- Execution status (ok, blocked, error, timeout, pending_approval)
- Result data or error details
- Execution timing and duration
- Evidence receipt for audit trail
- Obligations fulfilled

**Use case:** Returning execution results to callers with cryptographic proof.

**Example:**
```json
{
  "result_id": "res-456",
  "correlation_id": "req-12345",
  "status": "ok",
  "action": "read_record",
  "result": {
    "data": {...},
    "timestamp": "2026-04-17T15:30:00Z"
  },
  "receipt": {
    "receipt_id": "rcpt-789",
    "decision": "allow",
    "signature": "..."
  }
}
```

---

### Policy & Decision Schemas

#### `policy_decision.schema.json`
Result of policy engine evaluation for an action request.

**Key components:**
- Decision (allowed/denied)
- Reason for decision
- Matched role or policy basis
- Required obligations
- Evaluated policies and denial reasons
- Risk level assessment

**Use case:** Recording policy evaluation results for audit trail.

**Example:**
```json
{
  "decision_id": "dec-123",
  "correlation_id": "req-12345",
  "allowed": true,
  "requires_elevation": false,
  "reason": "Matches read_records permission in data_analyst role",
  "matched_role": "data_analyst",
  "decision_basis": "rbac",
  "risk_level": "low"
}
```

---

### Access Control Schemas

#### `identity.schema.json`
Represents principals: agents, users, services, or systems.

**Key components:**
- Principal identity and type
- Display name and email
- Assigned roles
- Contextual attributes (tenant, department, risk score)
- Agent-specific metadata if applicable

**Use case:** Looking up principal information for policy decisions.

**Example:**
```json
{
  "principal_id": "agent-001",
  "principal_type": "agent",
  "display_name": "Data Processor Agent",
  "roles": ["data_analyst", "report_generator"],
  "agent_info": {
    "agent_id": "agent-001",
    "model_id": "gpt-4",
    "capabilities": ["read_records", "generate_reports"]
  }
}
```

---

#### `resource.schema.json`
Represents resources that agents can act upon.

**Key components:**
- Resource identity and type
- Owner and tenant
- Classification and sensitivity level
- Access controls and allowlists/denylists
- Audit requirements
- Risk assessment

**Use case:** Validating resource access and enforcing resource-level policies.

**Example:**
```json
{
  "resource_id": "rec-789",
  "resource_type": "record",
  "resource_name": "Customer Profile #12345",
  "owner_tenant": "org-1",
  "classification": "confidential",
  "sensitivity": "high",
  "access_control": {
    "allowed_roles": ["data_analyst", "admin"],
    "requires_mfa": true
  }
}
```

---

#### `permission.schema.json`
Defines permissions with optional contextual conditions (RBAC/ABAC rules).

**Key components:**
- Action and resource type
- Effect (allow/deny)
- Contextual conditions
- Constraints (time-based, location-based, rate limits)

**Use case:** Defining granular permissions for role-based access control.

**Example:**
```json
{
  "permission_id": "perm-001",
  "action": "read_record",
  "resource_type": "record",
  "effect": "allow",
  "constraints": {
    "time_based": {
      "allowed_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "start_time": "09:00",
      "end_time": "17:00"
    },
    "rate_limit": {
      "max_per_hour": 10000
    }
  }
}
```

---

#### `role.schema.json`
Defines named roles with permission sets and role assignments.

**Key components:**
- Role identity and type (system, organization, team, custom)
- Permissions granted
- Implied roles (role hierarchy)
- Elevation requirements
- Assignment tracking

**Use case:** Managing RBAC policies and assigning roles to principals.

**Example:**
```json
{
  "role_id": "role-analyst",
  "name": "data_analyst",
  "role_type": "organization",
  "permissions": [
    {
      "permission_id": "perm-001",
      "action": "read_record",
      "resource_type": "record"
    }
  ],
  "implied_roles": ["basic_user"],
  "requires_elevation": false
}
```

---

### Privileged Access Management (PAM)

#### `elevation_grant.schema.json`
Time-bound privilege elevation grants for sensitive actions.

**Key components:**
- Grant ID and ticket reference
- Principal and approver information
- Duration and expiration
- Allowed actions and resource types
- Usage limits and status
- Conditions (MFA, IP whitelist, session requirements)
- Revocation tracking
- Audit trail

**Use case:** Managing temporary privilege escalation with full audit trail.

**Example:**
```json
{
  "grant_id": "grant-789",
  "ticket_id": "TICKET-5678",
  "principal_id": "agent-001",
  "approved_by": "admin-user-1",
  "issued_at": "2026-04-17T15:00:00Z",
  "expires_at": "2026-04-17T23:00:00Z",
  "duration_minutes": 480,
  "reason": "Emergency incident response",
  "allowed_actions": ["delete_record", "modify_config"],
  "resource_types": ["record", "config"],
  "max_uses": 50,
  "status": "active"
}
```

---

### Evidence & Audit

#### `evidence_receipt.schema.json`
Cryptographically signed, chained receipts for the Evidence Vault.

**Key components:**
- Receipt and correlation IDs
- Principal, action, resource information
- Policy decision (allow/deny) and reason
- Parameter hash and prior receipt hash
- Cryptographic signature
- Blockchain-style chaining via prior_receipt_hash
- Metadata (environment, IP, execution time)

**Use case:** Creating tamper-evident audit trail records.

**Features:**
- **Hash chaining:** Each receipt references the previous receipt's hash
- **Tamper detection:** HMAC signature prevents tampering
- **Integrity verification:** Parameter hash detects modified params
- **Full provenance:** Complete record of who did what when

**Example:**
```json
{
  "receipt_id": "rcpt-001",
  "timestamp": "2026-04-17T15:30:00Z",
  "correlation_id": "req-12345",
  "principal_id": "agent-001",
  "principal_type": "agent",
  "action": "read_record",
  "resource_id": "rec-789",
  "resource_type": "record",
  "decision": "allow",
  "reason": "Matched data_analyst role permission",
  "params_hash": "abc123...",
  "prior_receipt_hash": "xyz789...",
  "receipt_hash": "def456...",
  "signature": "hmac_signature...",
  "metadata": {
    "environment": "production",
    "execution_time_ms": 45.2,
    "tenant_id": "org-1"
  }
}
```

---

### Configuration

#### `policy_configuration.schema.json`
Complete CIAF policy engine configuration combining all subsystems.

**Key configuration sections:**

1. **IAM Configuration**
   - Mode (RBAC, ABAC, or hybrid)
   - Role definitions
   - Default deny policy

2. **PAM Configuration**
   - Sensitive/privileged actions requiring elevation
   - Approval requirements and timeout
   - Auto-revocation on expiry

3. **Boundary Policies**
   - Tenant isolation
   - Rate limiting
   - Resource allowlists/denylists
   - Time-based restrictions

4. **Evidence Configuration**
   - Vault backend (memory, SQLite, PostgreSQL, MongoDB)
   - Receipt signing secret
   - Retention policy
   - Receipt chaining

5. **Logging & Monitoring**
   - Log levels and alert thresholds
   - Denied action logging
   - Elevated action logging
   - Metrics collection

6. **Enforcement**
   - Mode (report_only, soft_enforce, hard_enforce)
   - Rate limiting configuration
   - Concurrent execution limits

7. **Compliance**
   - Enabled frameworks (SOC2, HIPAA, PCI-DSS)
   - Encryption requirements
   - PII protection settings

**Use case:** Configuring and deploying CIAF policy engines across environments.

---

## Schema Relationships

```
┌─────────────────────────────────────────────────┐
│     CIAF Agent Request Execution Flow            │
└─────────────────────────────────────────────────┘

1. Agent submits action_request.schema.json
        ↓
2. Policy engine evaluates using policy_configuration.schema.json
        ↓
3. Consults identity.schema.json and resource.schema.json
        ↓
4. Matches against role.schema.json and permission.schema.json
        ↓
5. Checks elevation_grant.schema.json if required
        ↓
6. Returns policy_decision.schema.json
        ↓
7. Records evidence_receipt.schema.json in vault
        ↓
8. Returns execution_result.schema.json to caller
```

---

## Validation Usage

### Python (jsonschema)
```python
import json
import jsonschema

with open('agent.schema.json') as schema_file:
    agent_schema = json.load(schema_file)

with open('agent_config.json') as config_file:
    agent_config = json.load(config_file)

jsonschema.validate(instance=agent_config, schema=agent_schema)
print("Agent configuration is valid!")
```

### JavaScript/Node.js (ajv)
```javascript
const Ajv = require('ajv');
const agentSchema = require('./agent.schema.json');
const agentConfig = require('./agent_config.json');

const ajv = new Ajv();
const validate = ajv.compile(agentSchema);

if (validate(agentConfig)) {
    console.log("Agent configuration is valid!");
} else {
    console.log("Validation errors:", validate.errors);
}
```

---

## Compliance & Governance

All schemas support:

- **Audit trail requirements** - evidence_receipt.schema.json provides cryptographic proof
- **Data classification** - resource.schema.json includes classification levels
- **Access control** - permission.schema.json and role.schema.json define controls
- **Compliance frameworks** - policy_configuration.schema.json lists enabled frameworks
- **Encryption requirements** - resource and evidence schemas support encryption metadata
- **Retention policies** - policy_configuration.schema.json defines retention rules

---

## Versioning

Each schema includes:
- `$schema`: JSON Schema Draft 7
- `version`: Semantic versioning (major.minor.patch)
- `$id`: Unique URI for schema identification

When schemas change:
1. Update version number
2. Update `$id` URI if breaking changes
3. Document changes in schema `description`
4. Maintain backward compatibility when possible

---

## References

- [JSON Schema Draft 7 Specification](https://json-schema.org/draft-07/)
- [CIAF Whitepaper: Agentic Execution Boundaries](../docs/whitepaper_agentic_execution_boundaries.md)
- [CIAF Architecture Documentation](../docs/architecture.md)
- [CIAF API Reference](../docs/API_REFERENCE.md)

---

## Support

For questions or issues with schemas:
1. Review schema documentation strings
2. Check examples in `examples/` directory
3. Refer to CIAF architecture documentation
4. Open an issue on GitHub with `[schema]` tag
