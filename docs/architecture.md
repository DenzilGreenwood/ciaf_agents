# Architecture Details

## System Overview

The CIAF-LCM Agentic Execution Boundaries implementation provides a complete control stack for governing AI agent actions through five integrated planes.

## Control Planes

### 1. Identity Plane

**Purpose**: Establish unique, traceable identity for each agent

**Components**:
- `IAMStore`: Central repository for identities and role definitions
- `Identity`: Immutable principal record with roles and attributes
- `RoleDefinition`: Named collection of permissions

**Design Principles**:
- Each agent is a first-class principal
- No shared or anonymous agents in production
- Workload identity credentials (certificates, tokens)
- Tenant and environment binding
- Lifecycle management (provision, attest, revoke)

**Identity Structure**:
```python
@dataclass(frozen=True)
class Identity:
    principal_id: str            # Unique identifier
    principal_type: str          # "agent", "user", "service"
    display_name: str            # Human-readable name
    roles: Set[str]              # Assigned roles
    attributes: Dict[str, Any]   # Contextual attributes (tenant, dept, etc.)
```

### 2. Policy Plane

**Purpose**: Evaluate standing permissions and contextual constraints

**Components**:
- `PolicyEngine`: Core decision engine
- `Permission`: Declarative permission with conditions
- `PolicyDecision`: Structured allow/deny/elevate result

**Decision Logic**:
```
1. Resolve identity from request
2. Match action against role permissions
3. Evaluate ABAC conditions (tenant, environment, data class)
4. Check for sensitive action patterns
5. Determine elevation requirements
6. Apply runtime constraints (allowlists, thresholds)
7. Return structured decision with obligations
```

**Policy Types**:
- **Role-Based (RBAC)**: Static permission assignments
- **Attribute-Based (ABAC)**: Contextual evaluation
- **Boundary Rules**: Cross-cutting constraints (tenant isolation, domain allowlists)
- **Sensitivity Detection**: Automatic elevation triggers

### 3. Privilege Plane

**Purpose**: Manage temporary elevation for high-risk actions

**Components**:
- `PAMStore`: Elevation grant registry
- `ElevationGrant`: Time-bound privilege record
- Grant lifecycle (issue, validate, expire, revoke)

**Grant Structure**:
```python
@dataclass
class ElevationGrant:
    grant_id: str                 # Unique grant identifier
    principal_id: str             # Who is elevated
    allowed_actions: Set[str]     # What actions are permitted
    resource_types: Set[str]      # What resource types are allowed
    reason: str                   # Business justification
    approved_by: str              # Approving authority
    expires_at: datetime          # Expiration timestamp
    ticket_id: str                # Reference to approval ticket
```

**Grant Workflow**:
1. Agent requests sensitive action
2. System detects elevation requirement
3. Request denied with elevation signal
4. Human/automated approver issues grant
5. Agent retries with active grant
6. Grant expires automatically
7. Evidence captured at each step

### 4. Execution Plane

**Purpose**: Mediate tool invocations with runtime controls

**Components**:
- `ToolExecutor`: Guarded execution wrapper
- `ActionRequest`: Structured request envelope
- Mediation hooks and interceptors

**Execution Flow**:
```
ActionRequest → Identity Resolution → Policy Evaluation → 
Privilege Check → Mediated Tool Call → Result Capture → 
Evidence Recording → Response
```

**Mediation Capabilities**:
- Schema validation
- Parameter sanitization
- Output filtering
- Interruptibility (kill switch)
- Timeout enforcement
- Destination allowlists
- Sandboxing integration points

### 5. Evidence Plane

**Purpose**: Create tamper-evident audit trail

**Components**:
- `EvidenceVault`: Receipt storage and chain management
- `EvidenceReceipt`: Signed, chained record
- Cryptographic utilities (hash, sign, verify)

**Receipt Structure**:
```python
@dataclass
class EvidenceReceipt:
    receipt_id: str                     # Unique receipt ID
    timestamp: datetime                 # When it occurred
    principal_id: str                   # Who initiated
    action: str                         # What was requested
    resource_id: str                    # Target resource
    decision: str                       # Allow/deny outcome
    elevation_grant_id: Optional[str]   # Grant reference (if elevated)
    approved_by: Optional[str]          # Approver (if applicable)
    params_hash: str                    # Hash of parameters
    prior_receipt_hash: Optional[str]   # Chain link
    receipt_hash: str                   # Self hash
    signature: str                      # HMAC signature
```

**Chain Properties**:
- Each receipt links to previous receipt hash
- Cryptographic signatures prevent tampering
- Batch verification possible
- Append-only (WORM storage recommended)
- Independent verification supported

## Data Flow

### Allowed Action Sequence

```
┌──────────────┐
│ Agent        │
│ Requests     │
│ Action       │
└──────┬───────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Identity Plane                          │
│ • Authenticate agent                    │
│ • Load roles: ["agent_reader"]          │
│ • Load attributes: {tenant: "acme"}     │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Policy Plane                            │
│ • Match permission: read_record ✓       │
│ • Check tenant: acme == acme ✓          │
│ • Sensitive action: No                  │
│ • Decision: ALLOW                       │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Execution Plane                         │
│ • Validate schema ✓                     │
│ • Invoke tool wrapper                   │
│ • Capture result                        │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Evidence Plane                          │
│ • Create receipt                        │
│ • Link to prior receipt                 │
│ • Sign and store                        │
└──────┬──────────────────────────────────┘
       │
       ↓
┌──────────────┐
│ Success      │
│ Response     │
│ + Receipt    │
└──────────────┘
```

### Denied Action with Elevation Required

```
┌──────────────┐
│ Agent        │
│ Requests     │
│ Sensitive    │
│ Action       │
└──────┬───────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Policy Plane                            │
│ • Match permission: approve_payment ✓   │
│ • Sensitive action: YES                 │
│ • Check elevation grant: NOT FOUND      │
│ • Decision: DENY + ELEVATION REQUIRED   │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Evidence Plane                          │
│ • Create DENY receipt                   │
│ • Record elevation requirement          │
└──────┬──────────────────────────────────┘
       │
       ↓
┌──────────────┐
│ Blocked      │
│ Response     │
│ + Elevation  │
│ Signal       │
└──────┬───────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Privilege Plane (Human Workflow)       │
│ • Review request                        │
│ • Approve via ticket: CHG-2026-123      │
│ • Issue JIT grant                       │
│ • Grant expires in 15 minutes           │
└──────┬──────────────────────────────────┘
       │
       ↓
┌──────────────┐
│ Agent        │
│ Retries      │
│ with Grant   │
└──────────────┘
```

## Security Architecture

### Defense in Depth

1. **Authentication Layer**: Verify agent identity
2. **Authorization Layer**: Check standing permissions
3. **Policy Layer**: Enforce runtime constraints
4. **Privilege Layer**: Require approval for sensitive actions
5. **Execution Layer**: Mediate all tool calls
6. **Evidence Layer**: Record all decisions

### Threat Model Coverage

| Threat | Mitigation |
|--------|-----------|
| Anonymous agent | Mandatory unique identity |
| Over-privileged agent | Least-privilege by default + JIT elevation |
| Privilege escalation | Policy engine blocks unauthorized elevation |
| Cross-tenant access | ABAC tenant matching |
| Unauthorized tool use | Explicit tool registration + mediation |
| Action repudiation | Cryptographic receipts with chain |
| Evidence tampering | Signed receipts with hash chain |
| Standing privilege | Time-bound grants with auto-expiry |
| Approval bypass | Privilege plane enforcement |
| Audit log deletion | WORM storage + external anchoring |

## Integration Patterns

### Pattern 1: Sidecar Model

Agent runtime integrates IAM/PAM/Evidence as a sidecar service.

```
┌─────────────────────────────────┐
│ Agent Process                   │
│                                 │
│  ┌──────────────────────────┐  │
│  │ Agent Core               │  │
│  └────────┬─────────────────┘  │
│           │                     │
│           ↓                     │
│  ┌──────────────────────────┐  │
│  │ CIAF-LCM Client Library  │  │
│  └────────┬─────────────────┘  │
└───────────┼─────────────────────┘
            │
            ↓ (gRPC/REST)
┌─────────────────────────────────┐
│ CIAF-LCM Control Plane         │
│ • IAM Store                     │
│ • PAM Store                     │
│ • Policy Engine                 │
│ • Evidence Vault                │
└─────────────────────────────────┘
```

### Pattern 2: Gateway Model

Central gateway mediates all agent tool calls.

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Agent 1  │    │ Agent 2  │    │ Agent 3  │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     └───────────────┼───────────────┘
                     ↓
         ┌────────────────────────┐
         │ CIAF-LCM Gateway       │
         │ • Identity Resolution  │
         │ • Policy Evaluation    │
         │ • Privilege Check      │
         │ • Tool Mediation       │
         │ • Evidence Recording   │
         └────────┬───────────────┘
                  │
      ┌───────────┼───────────┐
      ↓           ↓           ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Tool A   │ │ Tool B   │ │ Tool C   │
└──────────┘ └──────────┘ └──────────┘
```

### Pattern 3: Embedded Model

IAM/PAM/Evidence logic directly embedded in agent runtime.

```
┌─────────────────────────────────────┐
│ Agent Runtime                       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Agent Decision Loop          │   │
│  └─────────────┬────────────────┘   │
│                ↓                     │
│  ┌─────────────────────────────┐   │
│  │ Embedded CIAF-LCM           │   │
│  │ • Local IAM Cache           │   │
│  │ • Policy Evaluator          │   │
│  │ • PAM Grant Validator       │   │
│  │ • Evidence Emitter          │   │
│  └─────────────┬────────────────┘   │
└────────────────┼────────────────────┘
                 │
                 ↓ (Async sync)
   ┌──────────────────────────────┐
   │ Central Evidence Collector   │
   └──────────────────────────────┘
```

## Scalability Considerations

### Performance

- **Identity Resolution**: Cache identity records locally with TTL
- **Policy Evaluation**: Pre-compile permission rules
- **Grant Lookup**: Index grants by principal + action + resource type
- **Receipt Writing**: Batch receipts before signing/storage
- **Chain Verification**: Verify incrementally, not full chain each time

### High Availability

- **IAM Store**: Replicated identity database
- **PAM Store**: Distributed grant cache with expiry
- **Policy Engine**: Stateless, horizontally scalable
- **Evidence Vault**: Append-only distributed log (e.g., Kafka, S3)

## Compliance Mapping

| Regulation | CIAF-LCM Control | Evidence |
|------------|------------------|----------|
| SOC 2 (CC6.1) | Logical access controls | Identity assignments, role definitions |
| SOC 2 (CC6.2) | Privileged access | Elevation grants, approval records |
| SOC 2 (CC7.2) | System monitoring | Receipt chain, deny events |
| HIPAA (164.308) | Access management | Identity + permissions + receipts |
| HIPAA (164.312) | Audit controls | Evidence vault, chain verification |
| PCI DSS (7.1) | Least privilege | IAM roles, PAM grants |
| PCI DSS (10.2) | Audit trail | All receipts with action detail |
| GDPR (32) | Access control | Identity plane, policy enforcement |
| ISO 27001 (A.9) | Access control | Complete IAM/PAM implementation |

## Deployment Recommendations

### Phase 1: Identity Foundation
- Provision unique identities for all agents
- Eliminate shared credentials
- Implement basic RBAC

### Phase 2: Policy Enforcement
- Deploy policy engine
- Implement ABAC conditions
- Add boundary rules (tenant, allowlists)

### Phase 3: Privilege Management
- Classify sensitive actions
- Implement PAM grant workflow
- Add approval integration

### Phase 4: Evidence & Assurance
- Enable evidence vault
- Implement receipt signing
- Add chain verification
- Integrate with SIEM/audit tools

### Phase 5: Advanced Controls
- Implement mediation wrappers for all tools
- Add sandboxing and output filtering
- Deploy kill switch capabilities
- Enable anomaly detection
