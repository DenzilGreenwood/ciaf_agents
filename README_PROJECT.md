# CIAF-LCM Agentic Execution Boundaries

Python implementation of Identity and Access Management (IAM) and Privileged Access Management (PAM) controls for autonomous AI agents, aligned with Continuous Intelligence, Assurance, and Forensics - Lifecycle Management (CIAF-LCM) principles.

## Overview

This implementation provides:

- **Identity Plane**: Unique agent identities with role-based and attribute-based access control
- **Policy Plane**: Runtime boundary enforcement with contextual conditions
- **Privilege Plane**: Just-in-time elevation grants for sensitive actions
- **Execution Plane**: Mediated tool invocation with interruptibility controls
- **Evidence Plane**: Cryptographically signed, chained audit receipts

## Quick Start

```bash
# Navigate to the ciaf_agents directory
cd ciaf_agents

# Install the package
pip install -e .

# Run tests to verify installation
pytest tests/ -v

# Run the demo
python examples/demo.py
```

## Project Structure

```
ciaf_agents/
├── src/                          # Core implementation
│   ├── core/                     # Core types and data structures
│   ├── iam/                      # Identity and Access Management
│   ├── pam/                      # Privileged Access Management
│   ├── policy/                   # Policy evaluation engine
│   ├── evidence/                 # Evidence vault and receipts
│   ├── execution/                # Tool executor with mediation
│   └── utils/                    # Utilities and helpers
├── examples/                     # Example usage and scenarios
│   ├── demo.py                   # Main demo script
│   └── scenarios/                # Real-world use cases
├── tests/                        # Unit tests
├── config/                       # Configuration files
│   └── policies/                 # Policy definitions
└── docs/                         # Documentation
```

## Documentation

- [Agentic AI README](ciaf_agents/README.md) - Detailed module documentation
- [Whitepaper](ciaf_agents/docs/whitepaper_agentic_execution_boundaries.md) - Comprehensive theory and rationale
- [Architecture](ciaf_agents/docs/architecture.md) - Technical architecture details
- [Implementation Guide](ciaf_agents/docs/implementation_guide.md) - Step-by-step implementation
- **[API Reference](ciaf_agents/docs/API_REFERENCE.md)** - Complete API documentation
- **[Troubleshooting](ciaf_agents/docs/TROUBLESHOOTING.md)** - Common issues and solutions
- [Contributing](../CONTRIBUTING.md) - Contribution guidelines
- [Changelog](../CHANGELOG.md) - Version history

## Example Scenarios

Explore real-world implementations:

- **Healthcare Claims**: HIPAA-compliant claims processing with department isolation
- **Financial Approvals**: SOX-compliant payment workflows with dual control
- **Infrastructure Changes**: Production changes with change management integration

Run scenarios:

```bash
python examples/scenarios/healthcare_claims.py
python examples/scenarios/financial_approvals.py
python examples/scenarios/production_changes.py
```

## Core Concepts

### Agent Identity

Every agent is a first-class principal with:
- Unique identifier
- Role assignments
- Contextual attributes (tenant, department, environment)
- Lifecycle management

### Action Boundaries

Actions are controlled through:
- **IAM Permissions**: Standing permissions via roles
- **Boundary Policies**: Runtime constraints (tenant isolation, allowlists)
- **PAM Elevation**: Temporary privilege grants for sensitive actions
- **Evidence Recording**: Immutable audit trail

### Evidence Chain

Every action creates a cryptographically signed receipt:
- Chained via hash linking
- Includes full context (who, what, when, why)
- Tamper-evident
- Verifiable independently

## License

Business Source License 1.1 (BUSL-1.1) - See [LICENSE.md](LICENSE.md)

## Contributing

This project is part of the CIAF-LCM initiative. For questions or contributions, please refer to the project documentation.

---

**Version**: 1.0.0  
**Date**: March 2026  
**Project**: CIAF-LCM Agentic AI
