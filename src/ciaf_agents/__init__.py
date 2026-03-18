"""
CIAF-LCM Agentic Execution Boundaries

Core implementation of IAM and PAM controls for autonomous AI agents.
"""

__version__ = "1.0.0"
__author__ = "CIAF-LCM Project Contributors"
__license__ = "BUSL-1.1"

from ciaf_agents.core.types import (
    RiskLevel,
    Identity,
    Resource,
    ActionRequest,
    Permission,
    RoleDefinition,
    ElevationGrant,
    PolicyDecision,
    EvidenceReceipt,
)

from ciaf_agents.iam.store import IAMStore
from ciaf_agents.pam.store import PAMStore
from ciaf_agents.policy.engine import PolicyEngine
from ciaf_agents.evidence.vault import EvidenceVault
from ciaf_agents.execution.executor import ToolExecutor

__all__ = [
    "RiskLevel",
    "Identity",
    "Resource",
    "ActionRequest",
    "Permission",
    "RoleDefinition",
    "ElevationGrant",
    "PolicyDecision",
    "EvidenceReceipt",
    "IAMStore",
    "PAMStore",
    "PolicyEngine",
    "EvidenceVault",
    "ToolExecutor",
]
