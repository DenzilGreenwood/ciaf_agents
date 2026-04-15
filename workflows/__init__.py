# Copyright (c) 2026 Denzil Greenwood. All rights reserved.
# Licensed under the Business Source License 1.1 (BUSL-1.1)
# See BUSL_1_1_LICENSE for license terms
#
# LICENSING NOTE:
# This package contains original CIAF workflow implementations demonstrating
# the five control planes (Identity, Policy, Privilege, Execution, Evidence)
# across real-world use cases. All workflows are BUSL 1.1 licensed.

"""
CIAF-LCM Workflow Implementations

Real-world demonstrations of the five control planes applied to:
1. Healthcare Claims Processing
2. Financial Approvals
3. Production Infrastructure Changes
4. Customer Communications
5. Data Access and Export
6. Web Search

Each workflow shows:
- Identity Plane: Agent and user roles
- Policy Plane: RBAC with contextual conditions
- Privilege Plane: JIT elevation for sensitive actions
- Execution Plane: Mediated tool execution
- Evidence Plane: Audit trail and receipts

All workflows include ADK Agent integration for LLM-powered execution.
"""

from . import agent
