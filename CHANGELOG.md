# Changelog

All notable changes to CIAF-LCM Agentic AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Future enhancements and improvements

## [1.1.0] - 2026-04-15

### Added

**Web Search Workflow Agent**
- New 6th workflow agent demonstrating CIAF governance in information retrieval domain
- Internet search with content governance and policy enforcement
- Search categories: PUBLIC, GENERAL, ACADEMIC, RESTRICTED, SENSITIVE
- All 5 CIAF control planes demonstrated (Identity, Policy, Privilege, Execution, Evidence)
- Safe search filtering and adult content blocking
- Escalation routing for restricted/sensitive searches
- Cryptographically signed search audit trail
- Tool function: `search_the_web_tool` with LLM integration

**ADK Agent Discovery & Integration**
- Fixed agent discovery issues in ADK web UI
- Created proper `workflows/agent.py` with Router Agent pattern
- Router agent guides users between all 6 workflows
- Added App pattern with ContextFilterPlugin for session management
- Proper `__init__.py` structure for ADK compliance
- Added `.env` file to workflows folder for API credentials

**Workflow Agent Improvements**
- All 6 workflows now fully ADK-discoverable and loadable
- Workflows folder now exports 7 agents (6 workflows + 1 router)
- Each workflow verified with proper `root_agent` export
- Healthcare and Financial Approvals workflows tested and verified working
- Complete integration with `adk web`, `adk run`, `adk api_server` commands

**Documentation Updates**
- Updated workflows/README.md with complete ADK integration guide
- Added Web Search workflow documentation with tool signatures and examples
- Added integration section showing how to use agents with ADK CLI and programmatically
- Updated __init__.py files to match ADK discovery patterns

### Fixed
- Agent discovery in ADK web UI (proper folder structure)
- Method naming bug in financial_approvals workflow (process_payment → approve_payment)
- Missing `.env` file in workflows folder

### Verified
- Healthcare Claims Agent: All 5 control planes working, 4 claims processed correctly
- Financial Approvals Agent: Multi-tier approval chains, 3 payments routed correctly
- Web Search Agent: 5 search queries with proper escalation and categorization
- ADK web UI discovery: Both `my_agent/` and `workflows/` folders properly discoverable

### Technical Details
- 6 complete workflow agents across different domains
- 7 total agents (6 workflows + 1 router)
- ~450 lines of code for Web Search workflow
- Full CIAF governance with all 5 control planes
- Dual-license compliance (BUSL-1.1 for CIAF logic + Apache 2.0 for ADK framework)
- 2,500+ lines of governance logic across all workflows

### Breaking Changes
None - This is a backward-compatible minor version release.

### Migration Steps
1. Update to version 1.1.0
2. Run `adk web` from ciaf_agents root directory to discover both agent folders
3. New Web Search workflow available in workflows folder
4. All existing workflows continue to work as before

## [1.0.0] - 2026-03-18

### Added

**Core Framework**
- Five-plane control architecture (Identity, Policy, Privilege, Execution, Evidence)
- Identity and Access Management (IAM) store with RBAC/ABAC support
- Privileged Access Management (PAM) store with time-bound elevation grants
- Policy evaluation engine with multi-layered decision logic
- Evidence vault with cryptographically signed, chained audit receipts
- Mediated tool executor with runtime controls

**Identity Plane**
- `Identity` dataclass for unique agent principals
- `IAMStore` for identity and role management
- Role-based access control (RBAC)
- Attribute-based access control (ABAC)
- Tenant and department isolation
- Identity lifecycle management (provision, revoke, update)

**Policy Plane**
- `PolicyEngine` for decision evaluation
- `Permission` with optional condition functions
- `RoleDefinition` for named permission collections
- Pre-built condition functions (same_tenant_only, same_department_only, etc.)
- Runtime constraint evaluation (thresholds, allowlists, business rules)
- Boundary policy enforcement

**Privilege Plane**
- `PAMStore` for elevation grant management
- `ElevationGrant` with time-bound, purpose-bound privileges
- JIT (just-in-time) privilege elevation
- Grant lifecycle (issue, validate, extend, revoke, cleanup)
- Dual-approval support for high-risk actions
- Approval workflow integration points

**Execution Plane**
- `ToolExecutor` for mediated action execution
- `ToolRegistry` for tool management
- Dry-run capability (policy check without execution)
- Batch execution support
- Full IAM/PAM/Evidence integration

**Evidence Plane**
- `EvidenceVault` for tamper-evident audit trail
- `EvidenceReceipt` with HMAC-SHA256 signatures
- Hash-chained receipts for integrity
- Chain verification (batch and individual)
- Receipt query capabilities (by principal, action, elevation status)
- Export functionality (JSON, JSONL formats)

**Documentation**
- Comprehensive whitepaper on Agentic Execution Boundaries
- Architecture documentation with detailed design
- Implementation guide with step-by-step instructions
- Getting started guide
- API reference documentation
- Troubleshooting guide
- Three complete READMEs (root, ciaf_agents, project)

**Examples**
- Main demonstration script with multiple scenarios
- Healthcare claims processing example (HIPAA compliance)
- Financial payment approvals example (SOX compliance)
- Production infrastructure changes example (change management)

**Configuration**
- Example configuration file (YAML)
- Default policy definitions
- Sensitive actions configuration
- Modular configuration structure

**Testing**
- 81 comprehensive tests across all modules
- 100% code coverage (353 statements)
- Unit tests for IAM, PAM, Policy, Evidence, Execution, Utilities
- Edge case testing (tampering, expiry, boundaries, conditions)
- Integration test scenarios

**Development Tools**
- setup.py for pip installation
- Requirements file with optional dependencies
- pytest configuration
- Code coverage reporting (terminal and HTML)
- Contributing guidelines
- Changelog tracking

### Security Features
- Cryptographic signing with HMAC-SHA256
- Hash chaining for tamper detection
- Least-privilege execution model
- Time-bound privilege elevation
- Cross-tenant access prevention
- Evidence-grade auditability

### Performance
- In-memory storage for low-latency decisions
- Efficient permission resolution
- Minimal external dependencies
- Batch operation support

## [0.9.0] - 2026-03-15 (Beta)

### Added
- Initial beta implementation
- Core IAM and PAM functionality
- Basic policy evaluation
- Evidence recording
- Demo scenarios

### Known Issues
- Import path workarounds in examples (fixed in 1.0.0)
- No package installation (fixed in 1.0.0)

---

## Version History

- **1.0.0** (2026-03-18): First production release with complete documentation
- **0.9.0** (2026-03-15): Beta release for testing

## Upgrade Guide

### From 0.9.0 to 1.0.0

**Breaking Changes:**
None - This is the first production release.

**New Features:**
- Proper pip installation via setup.py
- Complete API reference documentation
- Troubleshooting guide

**Migration Steps:**
1. Install via pip: `pip install -e .`
2. Update imports to use installed package instead of path hacks
3. Review new documentation for best practices

---

## Future Roadmap

### Planned for 1.1.0
- Persistent storage backends (database, S3, Azure Blob)
- Policy decision caching for performance
- GraphQL API for evidence queries
- Real-time monitoring and alerting integration
- Approval workflow automation
- Webhook support for grant issuance

### Planned for 1.2.0
- Multi-signature approval support
- Time-of-day and day-of-week constraints
- Geolocation-based access controls
- API rate limiting integration
- Break-glass emergency access
- Automated policy testing framework

### Planned for 2.0.0
- Distributed evidence vault with consensus
- Zero-knowledge proof integration
- Blockchain evidence anchoring (optional)
- Machine learning for anomaly detection
- Natural language policy definitions
- Visual policy builder UI

---

[Unreleased]: https://github.com/your-org/CIAF_LMC_Agentic_AI/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/CIAF_LMC_Agentic_AI/releases/tag/v1.0.0
[0.9.0]: https://github.com/your-org/CIAF_LMC_Agentic_AI/releases/tag/v0.9.0
