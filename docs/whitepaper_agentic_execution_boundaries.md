# Agentic Execution Boundaries
## Definition and Implementation of IAM and PAM for AI Agents

**A CIAF-LCM-aligned architecture for identity, privilege, mediation, and evidence**

---

**Positioning**: AI agents should be treated as digital principals with defined identity, scoped permissions, privileged elevation controls, runtime policy mediation, and tamper-evident receipts for every consequential action.

**Prepared for**: Strategic, architectural, and governance use  
**Authoring basis**: CIAF-LCM / AI Evidence Vault concepts  
**License**: Business Source License 1.1 (BUSL-1.1), consistent with CIAF-LCM  
**Date**: March 17, 2026

---

## Executive Summary

The rise of agentic AI changes the security and governance problem from model oversight alone to **action oversight**. Once an AI system can call tools, request data, modify records, approve workflows, send communications, or initiate external transactions, the core question becomes: **under what identity, under what policy, with what privilege, and with what evidence did the action occur?**

This whitepaper defines **agentic execution boundaries** as the combined technical and governance controls that determine what an AI agent may access, what it may do, when it must defer, when it may elevate authority, how it is mediated, and how those events are recorded. In enterprise terms, this is the extension of Identity and Access Management (IAM) and Privileged Access Management (PAM) principles from human and service accounts to autonomous or semi-autonomous AI actors.

The implementation model presented here is intentionally aligned to CIAF-LCM. IAM establishes the base identity, role, entitlement, and scope of an agent. PAM governs temporary or sensitive privilege elevation for consequential actions. A runtime policy gate mediates execution. An evidence layer records the who, what, when, why, policy basis, approval basis, and cryptographic proof of each decision and action.

### Core Outcomes of the Model

| Outcome | Definition | Why it matters |
|---------|------------|----------------|
| Identity-bound agency | Each agent acts as a defined principal, not an anonymous automation. | Makes accountability, scoping, and revocation possible. |
| Least-privilege execution | Agents receive only the minimum standing authority required for routine work. | Reduces blast radius and accidental overreach. |
| Privileged elevation on demand | High-risk actions require time-bound, purpose-bound elevation. | Prevents standing privileged agents. |
| Runtime mediation | Every significant action is evaluated before execution. | Allows policy enforcement in real time. |
| Evidence-grade auditability | Every allow, deny, defer, and elevate decision is captured as a receipt. | Supports assurance, audits, incident reconstruction, and governance. |

---

## Definition of Agentic Execution Boundaries

**Agentic execution boundaries** are the technical, identity, policy, and evidence controls that define the permitted execution space of an AI agent. They determine the scope of accessible resources, callable tools, permitted actions, escalation pathways, interruptibility, and required records for each action or attempted action.

An implementation-grade definition is as follows:

```
Agent Boundary = Identity + Authorization + Context + Elevation Control + Mediation + Auditability
```

This definition intentionally bridges classical IAM and PAM with AI runtime governance. It treats an agent as a digital actor that must be authenticated, scoped, mediated, and monitored in the same way an enterprise would govern a human operator or service identity, while also recognizing the unique need to constrain goals, plans, tool chains, and autonomous decision pathways.

The boundary is therefore not just an access boundary. It is also a **behavioral and operational boundary**. It governs not only whether an agent can reach a system, but whether it can execute a workflow, under what level of confidence, with what approval requirements, and with what recovery or interruption mechanisms.

### Boundary Layers

| Layer | Purpose | Typical control | Evidence |
|-------|---------|----------------|----------|
| Identity boundary | Establishes which agent is acting. | Workload identity, certificates, federation, service account, signed token | Agent ID, issuer, tenant, role set |
| Authorization boundary | Defines standing permissions and resource scope. | RBAC, ABAC, allowlists, tenant scoping | Entitlements, policy version, scope hash |
| Privilege boundary | Controls entry into elevated or sensitive actions. | JIT elevation, approval ticket, dual control, session brokering | Grant ID, approver, expiry, purpose |
| Execution boundary | Mediates each tool invocation or external action. | Policy gate, tool wrapper, sandbox, schema validation | Allow/deny/defer receipt, request hash, outcome |
| Evidence boundary | Ensures actions are reconstructable and tamper-evident. | Cryptographic receipt, chained log, Merkle batch, WORM retention | Signature, chain link, retention class, verification proof |

---

## Mapping the Concept to IAM and PAM

The mapping to **IAM** is strong because IAM already answers the foundational questions of identity, authentication, authorization, and scope. An agent needs a distinct identity, role binding, contextual attributes, and resource entitlements. Those are classical IAM concerns.

The mapping to **PAM** is strongest where an agent may initiate sensitive, irreversible, regulated, or financially consequential actions. Privileged elevation should never be the agent's default posture. Instead, elevation should be temporary, purpose-bound, approval-aware, and fully recorded. That is a PAM pattern applied to AI agents.

### Mapping Table

| Agentic concern | IAM / PAM mapping | Implementation note |
|-----------------|-------------------|---------------------|
| Agent identity | IAM workload identity | Treat the agent as a principal with unique credentials and lifecycle controls. |
| Allowed tools | IAM application and entitlement scope | Allow only explicitly registered tools or APIs. |
| Data access scope | IAM RBAC/ABAC policy | Bind tenant, data class, record type, and contextual conditions. |
| Approval gate | PAM or step-up approval workflow | Require a human or policy authority before high-risk execution. |
| Temporary elevation | PAM JIT privilege grant | Grant only the minimum elevated capability and expire it quickly. |
| Privileged execution path | PAM brokered or wrapped session | Route consequential actions through a controlled mediator. |
| Kill switch / stop | Administrative revoke / disable control | Support immediate interruption and revocation. |
| Action traceability | IAM/PAM logs extended with CIAF receipts | Capture decision basis, approval basis, and action proof. |

---

## Reference Architecture

A practical enterprise architecture for agent IAM and PAM has five planes: **identity**, **policy**, **privilege**, **execution**, and **evidence**. These planes can be implemented as distinct services or integrated into a shared control platform, but they should remain conceptually separate so that standing identity, elevated authority, runtime mediation, and evidence are not conflated.

### Architecture Planes

| Plane | Responsibilities |
|-------|------------------|
| **Identity** | Provision agent identities, credentials, attestation status, tenant binding, and role assignments. |
| **Policy** | Evaluate standing entitlements plus contextual controls such as environment, sensitivity, destination, amount thresholds, and human-approval requirements. |
| **Privilege** | Issue, validate, expire, and revoke elevated grants for sensitive actions. Bind each grant to purpose, duration, approver, and allowed action scope. |
| **Execution** | Route actions through guarded tool adapters, schema validation, output filtering, and interruptibility controls before any side effect occurs. |
| **Evidence** | Write signed, chained, and ideally batch-verifiable receipts for every action request, decision, approval, elevation, execution result, and exception. |

---

## Implementation Model

The implementation below is intentionally technology-neutral while still being concrete enough to build. It assumes agents interact with enterprise tools through a mediation layer rather than making direct calls to systems of record.

### 1. Identity Model

Each agent should be provisioned as a **first-class principal** with a unique identifier, credential material, lifecycle state, owner, tenant binding, environment binding, and approved role set. Shared agent accounts should be avoided where accountability matters.

The minimum agent identity record should include:
- Principal ID
- Principal type
- Display name
- Owner or sponsoring team
- Tenant
- Environment
- Role assignments
- Allowed tool catalog
- Credential issuer
- Issuance date
- Revocation status
- Provenance references to model or workflow versions where appropriate

### 2. Authorization Model

Standing permissions should be narrow and composable. In most cases, an agent should hold only routine read or low-risk workflow permissions by default. Authorization should be evaluated against resource type, data classification, tenant, context, and action semantics, not just a static role name.

### 3. Privilege Elevation Model

Sensitive operations should transition from standing authority to temporary authority. A privileged grant should state:
- Requesting principal
- Allowed action or action family
- Allowed resource types
- Reason
- Ticket or case reference
- Approving authority
- Issuance time
- Expiration time
- Any post-execution review obligations

Examples of actions that commonly require PAM-style treatment include:
- Payment approvals
- Production configuration changes
- Deletion of regulated records
- External data exports
- Identity impersonation
- Mass notifications
- Irreversible state changes

### 4. Runtime Policy Mediation

The execution path should enforce a decision sequence:
1. Identify the principal
2. Resolve the requested action
3. Validate the target resource
4. Evaluate standing authorization
5. Determine whether the action is sensitive
6. Check for any required elevation
7. Enforce allowlists or data policy constraints
8. Log the decision
9. Execute the side effect (only after all checks pass)

### 5. Evidence and Receipts

Every significant event should create a **receipt**. At a minimum, receipts should capture:
- Timestamp
- Principal
- Action
- Resource
- Request hash
- Policy decision
- Policy version
- Elevation grant reference (when present)
- Approver (when present)
- Result status
- Prior-receipt link
- Receipt hash
- Signature

For higher-assurance systems, receipts should be batch-anchored or Merkle-linked and retained in immutable storage.

### 6. Operational Controls

| Control family | Minimum control | Recommended enhancement |
|----------------|-----------------|------------------------|
| Provisioning | Documented owner and purpose for each agent identity | Automated approval workflow plus attested deployment metadata |
| Entitlements | Role-based standing permissions | Attribute-based policies with environment and data-class conditions |
| Elevation | Manual approval with time-bound grant | Dual approval, reason codes, and automated expiry with revalidation |
| Execution | Tool mediation layer | Sandboxing, schema enforcement, and destination allowlists |
| Logging | Action and decision logs | Signed receipts, Merkle batches, WORM retention, and independent verification |
| Response | Manual revoke or disable | Immediate kill switch, session purge, and break-glass logging |

---

## Implementation Sequence

1. **Inventory** agents, workflows, callable tools, and systems of record.
2. **Classify** actions into routine, sensitive, and privileged categories.
3. **Provision** agent identities and remove anonymous or shared automation identities where feasible.
4. **Define** standing entitlements for routine actions only.
5. **Define** privileged action families and JIT grant requirements.
6. **Place** all externalized actions behind a mediation layer or brokered tool wrapper.
7. **Emit** cryptographic receipts for allow, deny, elevate, execute, and interrupt events.
8. **Add** review dashboards and exception workflows for denied, deferred, or over-scope requests.
9. **Verify** grants, roles, and receipt integrity through independent checks periodically.

---

## Illustrative Control Flow

The following pseudocode expresses the intended control path. It is not the only implementation pattern, but it captures the architecture described in this paper.

```python
request = ActionRequest(agent_id, action, resource, params, justification)

identity = iam.resolve(agent_id)
decision = policy.evaluate(identity, action, resource, params)

if decision.requires_elevation:
    grant = pam.find_active_grant(agent_id, action, resource.type)
    if not grant:
        return deny_with_receipt()

result = mediated_tool_executor.execute(request)
receipt = evidence_vault.write(identity, decision, result, grant)
```

---

## CIAF-LCM Alignment

CIAF-LCM provides the evidence-oriented extension of this architecture. IAM and PAM establish identity and authority boundaries, but CIAF-LCM records the proof that those boundaries were enforced. In a CIAF-aligned deployment, every decision point can emit a signed receipt linked to policy state, privileged approval state, execution result, and later audit-pack generation.

This is strategically important because agent governance is not merely about restricting behavior; it is about **proving how the system was governed**. The more agentic a system becomes, the more valuable the evidence layer becomes.

---

## Governance and Risk Considerations

- An agent IAM and PAM program should assign clear ownership across platform engineering, security, risk, compliance, and business operations.
- No agent should exist without a sponsoring owner, an allowed purpose, and a review cadence.
- Privilege should be treated as an **event, not a state**. Sensitive authority should be exceptional, brief, reviewable, and attributable.
- Evidence should be written for denied and interrupted actions as well as successful ones. Denials and interruptions often carry the strongest governance signal.

---

## Conclusion

Agentic execution boundaries can and should be mapped to IAM and PAM. IAM provides the standing identity and authorization model. PAM provides the controlled elevation model for high-risk actions. A runtime policy gate mediates execution. A CIAF-LCM-aligned evidence layer provides durable proof. Together, these create a practical governance stack for AI agents that is legible to security teams, risk teams, auditors, and enterprise architecture leaders.

---

## Appendix A: License

This whitepaper is intended to use the same licensing posture as the CIAF-LCM process: **Business Source License 1.1 (BUSL-1.1)**. Any operational use, redistribution, or derivative implementation should follow the governing terms you use for CIAF-LCM, including any change date or conversion terms defined in your primary licensing materials.

Because this document is derivative positioning and architecture content rather than the source code implementation itself, you may also choose to include an explicit notice in your repository or distribution package clarifying whether the whitepaper is covered directly by BUSL-1.1 or distributed as accompanying documentation under a separate compatible documentation license. The title page and this appendix currently assume the same BUSL-1.1 posture for consistency.
