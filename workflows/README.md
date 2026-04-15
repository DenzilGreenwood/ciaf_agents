# CIAF Workflows: Real-World Governance Demonstrations

This directory contains 6 production-adjacent workflow implementations demonstrating CIAF governance across different domains.

Each workflow is **100% original CIAF implementation** and is **BUSL 1.1 licensed**. See [../LICENSING_AUDIT.md](../LICENSING_AUDIT.md) for details.

---

## Quick Start: Run Workflows

Each workflow is a standalone Python script demonstrating all 5 CIAF control planes:

```bash
# Run any workflow
python workflows/healthcare_claims.py
python workflows/financial_approvals.py
python workflows/production_changes.py
python workflows/customer_communications.py
python workflows/data_access_export.py
python workflows/web_search.py

# Or run all workflows in sequence
for workflow in healthcare_claims financial_approvals production_changes customer_communications data_access_export web_search; do
    echo ">>> Running $workflow"
    python workflows/${workflow}.py
    echo ""
done
```

---

## Six Workflows

### 1. Healthcare Claims Processing (`healthcare_claims.py`)

**Agent Name:** `healthcare_claims_agent`  
**Tool:** `process_claim_tool`

**Domain:** Medical billing with HIPAA compliance  
**Five Control Planes Demonstrated:**

- **Identity Plane:** Claims processor agent + medical/financial reviewers
- **Policy Plane:** RBAC with amount-based permissions + medical necessity
- **Privilege Plane:** JIT elevation for claims over $1,000
- **Execution Plane:** Amount-based routing with mediation
- **Evidence Plane:** Audit trail of all claim decisions

**Key Feature:** Risk-level escalation
- $0-$1K → Auto-approved by processor
- $1K-$5K → Requires medical reviewer
- $5K+ → Requires medical + financial approval
- High-risk → Escalates to compliance

**How to run this workflow:**

```bash
python workflows/healthcare_claims.py
```

**Or use programmatically:**

```python
from workflows.healthcare_claims import HealthcareClaimsAgent, ClaimRecord

agent = HealthcareClaimsAgent()
claim = ClaimRecord(
    claim_id="CLM-001",
    patient_id="PAT-001",
    provider="Hospital Name",
    amount=2500.00,
    diagnosis_code="M79.3",
    treatment_type="Physical Therapy",
    medical_necessity_score=0.95
)
result = agent.process_claim(claim)
print(result)
```

**Tool parameters:**
```
process_claim_tool(
    claim_id: str,
    patient_id: str,
    provider: str,
    amount: float,
    diagnosis_code: str,
    treatment_type: str,
    high_risk: bool = False
) -> str (JSON result)
```

**Runs:** 4 test claims with different amounts and risk levels

---

### 2. Financial Approvals (`financial_approvals.py`)

**Agent Name:** `financial_approvals_agent`  
**Tool:** `process_payment_tool`

**Domain:** Payment authorization with dual-control

**Five Control Planes Demonstrated:**

- **Identity Plane:** Payment processor + approver + controller + CFO
- **Policy Plane:** Approval limits tied to role and amount
- **Privilege Plane:** Multi-tier escalation for high-value payments
- **Execution Plane:** Approval chain mediation
- **Evidence Plane:** Cryptographic approval trail with signatures

**Key Feature:** Dual-control and multi-level approval
- $0-$10K → Processor authority
- $10K-$50K → Processor + Approver
- $50K-$250K → Processor + Approver + Controller
- $250K+ → Processor + Approver + Controller + CFO + Board

**How to run this workflow:**

```bash
python workflows/financial_approvals.py
```

**Or use programmatically:**

```python
from workflows.financial_approvals import FinancialApprovalsAgent, PaymentRequest

agent = FinancialApprovalsAgent()
payment = PaymentRequest(
    payment_id="PAY-001",
    vendor="Acme Corp",
    amount=25000.00,
    category="supplies",
    purpose="Office equipment",
    requester="manager-001"
)
result = agent.approve_payment(payment)
print(result)
```

**Tool parameters:**
```
process_payment_tool(
    payment_id: str,
    vendor: str,
    amount: float,
    category: str,
    purpose: str,
    requester: str
) -> str (JSON result)
```

**Runs:** 3 payments showing low, mid-range, and high-value approval chains

---

### 3. Production Changes (`production_changes.py`)

**Agent Name:** `production_changes_agent`  
**Tool:** `process_change_tool`

**Domain:** Infrastructure change management with rollback controls

**Five Control Planes Demonstrated:**

- **Identity Plane:** Change agent + tech lead + DBA + approver + director
- **Policy Plane:** Risk-based permissions (low/medium/high/critical)
- **Privilege Plane:** Escalation based on change risk level
- **Execution Plane:** Multi-reviewer approval with rollback capability
- **Evidence Plane:** Change audit trail with pre-change state snapshot

**Key Feature:** Risk-based change governance with rollback evidence
- Low-risk → Tech lead + approver
- Medium-risk → Tech lead + approver
- High-risk → Tech lead + DBA + approver
- Critical-risk → Tech lead + DBA + approver + director

**How to run this workflow:**

```bash
python workflows/production_changes.py
```

**Or use programmatically:**

```python
from workflows.production_changes import ProductionChangesAgent, ChangeRequest

agent = ProductionChangesAgent()
change = ChangeRequest(
    change_id="CHG-001",
    title="Database Migration",
    description="Migrate from v11 to v12",
    environment="production",
    risk_level="high",
    change_type="database",
    requested_by="engineer-001"
)
result = agent.process_change(change)
print(result)
```

**Tool parameters:**
```
process_change_tool(
    change_id: str,
    title: str,
    description: str,
    environment: str,
    risk_level: str,  # 'low', 'medium', 'high', 'critical'
    change_type: str,
    requested_by: str
) -> str (JSON result)
```

**Runs:** 4 changes from low-risk config updates to critical multi-region failover

---

### 4. Customer Communications (`customer_communications.py`)

**Agent Name:** `customer_communications_agent`  
**Tool:** `send_communication_tool`

**Domain:** Customer-facing message governance with policy enforcement

**Five Control Planes Demonstrated:**

- **Identity Plane:** Communications agent + marketing/support + compliance + counsel
- **Policy Plane:** Content policy gates (financial info, legal terms)
- **Privilege Plane:** Escalation for compliance-sensitive content
- **Execution Plane:** Approval chain enforcement before sending
- **Evidence Plane:** Audit trail of all customer communications

**Key Feature:** Content policy validation + multi-reviewer approval
- **Marketing:** No financial info; policy check first
- **Support:** No legal terms; reply restriction
- **Disclosure:** Must contain financial info; compliance review
- **Legal:** Requires general counsel approval

**How to run this workflow:**

```bash
python workflows/customer_communications.py
```

**Or use programmatically:**

```python
from workflows.customer_communications import CustomerCommunicationsAgent, CommunicationRequest

agent = CustomerCommunicationsAgent()
message = CommunicationRequest(
    message_id="MSG-001",
    communication_type="marketing",
    recipient="customer@example.com",
    subject="Special Offer",
    content="We have a new offer for you..."
)
result = agent.send_communication(message)
print(result)
```

**Tool parameters:**
```
send_communication_tool(
    message_id: str,
    communication_type: str,  # 'marketing', 'support', 'disclosure', 'legal'
    recipient: str,
    subject: str,
    content: str
) -> str (JSON result)
```

**Runs:** 4 communications (marketing, support, financial disclosure, legal notice)

---

### 5. Data Access & Export (`data_access_export.py`)

**Agent Name:** `data_access_agent`  
**Tool:** `request_data_access_tool`

**Domain:** Data governance with tenant isolation and classification

**Five Control Planes Demonstrated:**

- **Identity Plane:** Data agent + analyst + scientist + compliance + CDO
- **Policy Plane:** Classification-based data gates (public/customer/financial/confidential)
- **Privilege Plane:** Escalation for sensitive data (export, cross-tenant)
- **Execution Plane:** Tenant isolation enforcement
- **Evidence Plane:** Fine-grained access logging + export audit trail

**Key Feature:** Data classification + tenant isolation
- **Public:** Direct access
- **Customer:** Requires business justification; export needs compliance
- **Financial:** Compliance review mandatory
- **Confidential:** CDO approval + executive audit

**How to run this workflow:**

```bash
python workflows/data_access_export.py
```

**Or use programmatically:**

```python
from workflows.data_access_export import DataAccessAgent, AccessRequest

agent = DataAccessAgent()
request = AccessRequest(
    request_id="REQ-001",
    requester_id="analyst-001",
    dataset_name="customer_data",
    data_classification="CUSTOMER",
    access_purpose="Analytics",
    is_export=False
)
result = agent.request_access(request)
print(result)
```

**Tool parameters:**
```
request_data_access_tool(
    request_id: str,
    requester_id: str,
    dataset_name: str,
    data_classification: str,  # 'PUBLIC', 'CUSTOMER', 'FINANCIAL', 'CONFIDENTIAL'
    access_purpose: str,
    is_export: bool = False
) -> str (JSON result)
```

**Runs:** 4 access requests showing same-tenant, cross-tenant, export, and confidential cases

---

### 6. Web Search (`web_search.py`)

**Agent Name:** `web_search_agent`  
**Tool:** `search_the_web_tool`

**Domain:** Internet search with content governance

**Five Control Planes Demonstrated:**

- **Identity Plane:** Search agent + content reviewer + compliance officer
- **Policy Plane:** RBAC with content category-based permissions
- **Privilege Plane:** Escalation for restricted/sensitive searches
- **Execution Plane:** Search mediation with content filtering
- **Evidence Plane:** Search audit trail and result logging

**Key Feature:** Content category-based search governance
- **PUBLIC:** Unrestricted searches (1000+ results)
- **GENERAL:** Standard safe search applied (500 results)
- **ACADEMIC:** Research-focused searches (250 results)
- **RESTRICTED:** Requires content reviewer approval
- **SENSITIVE:** Requires compliance officer oversight

**How to run this workflow:**

```bash
python workflows/web_search.py
```

**Or use programmatically:**

```python
from workflows.web_search import WebSearchAgent, SearchQuery
from workflows.web_search import SearchCategory

agent = WebSearchAgent()
query = SearchQuery(
    query_id="Q-001",
    search_term="Python programming best practices",
    category=SearchCategory.ACADEMIC,
    requester_id="user-001",
    requester_tenant="search-corp",
    search_scope="academic",
    safe_search=True
)
result = agent.perform_search(query)
print(result)
```

**Tool parameters:**
```
search_the_web_tool(
    query_id: str,
    search_term: str,
    category: str,              # 'PUBLIC', 'GENERAL', 'ACADEMIC', 'RESTRICTED', 'SENSITIVE'
    search_scope: str = "web",  # 'web', 'news', 'academic', 'images'
    safe_search: bool = True,
    max_results: int = 10
) -> str (JSON result)
```

**Runs:** 5 search queries demonstrating different categories (academic, general, public, restricted, sensitive)

---

## Workflow Architecture

```
ClassName:
  __init__() → Setup IAM, PAM, Evidence Vault
  _setup_roles_and_policies() → Define CIAF control planes
  [operation]() → IDENTITY → POLICY → PRIVILEGE → EXECUTION → EVIDENCE
  main() → Run test cases

Output:
  ◆ DEMONSTRATED: Shows control plane logic explicitly
  ◇ SIMULATED: Shows design without full integration
  ✓ Status: Final decision with evidence trail
```

---

## Key Features Across All Workflows

### Identity Plane
✅ Agent and user identities with roles and attributes  
✅ Credential and lifecycle management simulation  
✅ Role-based access control foundation  

### Policy Plane
✅ RBAC with conditional permissions  
✅ Condition evaluation (amount, tenant, content policy, etc.)  
✅ Standing authority vs. escalation  

### Privilege Plane
✅ JIT privilege elevation requests  
✅ Amount/risk-based escalation triggers  
✅ Multi-level approval workflows  

### Execution Plane
✅ Tool mediation with schema validation  
✅ Decision routing based on policies  
✅ Approval chain orchestration  

### Evidence Plane
✅ Cryptographic receipt simulation  
✅ Audit trail recording (timestamps, signatures)  
✅ Chain linkage and verification design  

---

## Running All Workflows

```bash
# Run all 6 workflows in sequence
for workflow in healthcare_claims financial_approvals production_changes customer_communications data_access_export web_search; do
    echo ">>> Running $workflow"
    python workflows/${workflow}.py
    echo ""
done
```

---

## Learning Path

**Start here:**
1. `healthcare_claims.py` — Simplest: Amount-based routing
2. `financial_approvals.py` — Multi-tier approvals
3. `production_changes.py` — Risk-based escalation + rollback
4. `customer_communications.py` — Policy enforcement
5. `data_access_export.py` — Classification + tenant isolation
6. `web_search.py` — Content governance

Each builds on CIAF concepts from the previous one.

---

## Expected Output

Each workflow prints:

```
════════════════════════════════════════════════════════════════════════════════
  [WORKFLOW NAME]: [Test Case ID]
════════════════════════════════════════════════════════════════════════════════

→ IDENTITY PLANE: [Agent/Principal Details]
  Principal: [ID]
  Display: [Name]
  Roles: [List]

→ POLICY PLANE: [Routing Decision]
  [Decision Logic with Context]
  Decision: [Action]

→ PRIVILEGE PLANE: [Escalation Analysis]
  ◆ [Escalation Trigger]
  → [Escalation Required/Within Authority]

→ EXECUTION PLANE: [Approval Chain]
  [Approval Stage Details]

→ EVIDENCE PLANE: [Audit Trail]
  ◆ [Recorded Evidence]
  ◆ [Signatures/Hashes]
  ◆ [Timestamps]

  ✓ Status: [Decision]
  ✓ [Additional Result Details]
```

---

## Licensing

All workflows are **Business Source License 1.1 (BUSL-1.1)** licensed.

**Why BUSL-1.1:**
- Original implementations developed from first principles
- Demonstrate all five CIAF control planes
- Not derived from external templates or samples
- Represent core CIAF governance architecture

**What this means:**
- ✓ Non-production use: Permitted (evaluation, learning)
- ✗ Production use: Requires commercial license
- ✓ Google ADK integration: Apache 2.0 (see [../LICENSING_AUDIT.md](../LICENSING_AUDIT.md))

For commercial licensing or production deployment, contact:  
**Denzil Greenwood**  
GitHub: [@DenzilGreenwood](https://github.com/DenzilGreenwood)  
Repository: [ciaf_agents](https://github.com/DenzilGreenwood/ciaf_agents)

---

## Architecture Notes

### Design Philosophy
- Each workflow is a **self-contained demonstration** (can run independently)
- Focuses on **policy logic** not LLM interaction
- Shows **decision pathways** at each control plane
- Emphasizes **evidence recording** and audit trails

### What's Demonstrated vs. Simulated

| Aspect | Demonstrated | Simulated |
|--------|--------------|-----------|
| Identity & roles | ✅ Real objects | - |
| Policy evaluation | ✅ Real conditions | - |
| Permission checking | ✅ Real RBAC logic | - |
| Approval routing | ✅ Real chains | - |
| Evidence recording | ✅ Struct generation | ◇ Cryptographic hashing |
| Tool execution | ◇ Decision logic | ◇ Actual tool runs |
| LLM integration | ◇ Not included | ◇ Use my_agent/ for LLM demo |

### Integration with my_agent/

These workflows can be integrated into `my_agent/agent.py`:

```python
from workflows import HealthcareClaimsWorkflow, FinancialApprovalsWorkflow, ...

workflow = HealthcareClaimsWorkflow()
result = workflow.process_claim(claim_record)
```

See [../my_agent/INTEGRATION_GUIDE.md](../my_agent/INTEGRATION_GUIDE.md) for details.

---

## Extensibility

Each workflow can be extended:

```python
class CustomWorkflow(HealthcareClaimsWorkflow):
    def _setup_roles_and_policies(self):
        # Add new roles
        super()._setup_roles_and_policies()
        # Your custom permissions
        
    def process_custom_case(self, case):
        # Your custom logic
        pass
```

---

## Questions?

See the main [../README.md](../README.md) or [../LICENSING_AUDIT.md](../LICENSING_AUDIT.md) for details about the CIAF architecture and licensing.
