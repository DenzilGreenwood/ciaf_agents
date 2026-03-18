"""
Core type definitions for CIAF-LCM Agentic Execution Boundaries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable


class RiskLevel(str, Enum):
    """Risk classification for actions and resources."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Identity:
    """
    Represents a unique digital principal (agent, user, or service).
    
    Attributes:
        principal_id: Unique identifier for the principal
        principal_type: Type classification ("agent", "user", "service")
        display_name: Human-readable name
        roles: Set of assigned role names
        attributes: Contextual attributes (tenant, department, etc.)
    """
    principal_id: str
    principal_type: str
    display_name: str
    roles: Set[str]
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Resource:
    """
    Represents a target resource for an action.
    
    Attributes:
        resource_id: Unique identifier for the resource
        resource_type: Type classification (e.g., "email", "payment", "record")
        owner_tenant: Owning tenant/organization
        attributes: Resource-specific attributes
    """
    resource_id: str
    resource_type: str
    owner_tenant: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionRequest:
    """
    Represents a request to perform an action on a resource.
    
    Attributes:
        action: The action to perform (e.g., "read_record", "approve_payment")
        resource: Target resource
        params: Action-specific parameters
        justification: Business justification for the action
        requested_by: Identity making the request
        correlation_id: Unique ID for tracking related requests
    """
    action: str
    resource: Resource
    params: Dict[str, Any]
    justification: str
    requested_by: Identity
    correlation_id: str = field(default_factory=lambda: __import__('uuid').uuid4().hex)


@dataclass
class Permission:
    """
    Defines a permission with optional contextual conditions.
    
    Attributes:
        action: The action this permission allows
        resource_type: The resource type this applies to ("*" for all)
        conditions: Optional callable to evaluate contextual conditions
    """
    action: str
    resource_type: str
    conditions: Optional[Callable[[Identity, Resource, Dict[str, Any]], bool]] = None

    def matches(self, identity: Identity, resource: Resource, params: Dict[str, Any]) -> bool:
        """
        Check if this permission matches the given context.
        
        Args:
            identity: The requesting identity
            resource: The target resource
            params: Action parameters
            
        Returns:
            True if permission applies, False otherwise
        """
        if self.resource_type != "*" and self.resource_type != resource.resource_type:
            return False
        if self.conditions is None:
            return True
        return self.conditions(identity, resource, params)


@dataclass
class RoleDefinition:
    """
    Defines a named role with a set of permissions.
    
    Attributes:
        name: Unique role name
        permissions: List of permissions granted by this role
    """
    name: str
    permissions: List[Permission]


@dataclass
class ElevationGrant:
    """
    Represents a time-bound privilege elevation grant.
    
    Attributes:
        grant_id: Unique identifier for this grant
        principal_id: Who received the elevation
        allowed_actions: Set of actions permitted under this grant
        resource_types: Set of resource types this grant applies to
        reason: Business justification for the elevation
        approved_by: Who approved the elevation
        expires_at: When the grant expires
        ticket_id: Reference to approval ticket/case
    """
    grant_id: str
    principal_id: str
    allowed_actions: Set[str]
    resource_types: Set[str]
    reason: str
    approved_by: str
    expires_at: datetime
    ticket_id: str

    def is_active(self) -> bool:
        """Check if this grant is still valid."""
        from ciaf_agents.utils.helpers import utc_now
        return utc_now() < self.expires_at


@dataclass
class PolicyDecision:
    """
    Result of a policy evaluation.
    
    Attributes:
        allowed: Whether the action is permitted
        requires_elevation: Whether PAM elevation is required
        reason: Explanation for the decision
        matched_role: Role that provided the permission (if any)
        obligations: Additional requirements or constraints
    """
    allowed: bool
    requires_elevation: bool
    reason: str
    matched_role: Optional[str] = None
    obligations: List[str] = field(default_factory=list)


@dataclass
class EvidenceReceipt:
    """
    Tamper-evident receipt for an action or decision.
    
    Attributes:
        receipt_id: Unique identifier for this receipt
        timestamp: When the event occurred
        principal_id: Who initiated the action
        principal_type: Type of principal
        action: What action was requested
        resource_id: Target resource ID
        resource_type: Target resource type
        correlation_id: Request correlation ID
        decision: Outcome (e.g., "allow", "deny")
        reason: Explanation for the decision
        elevation_grant_id: Associated grant ID (if elevated)
        approved_by: Approver identity (if applicable)
        params_hash: Hash of action parameters
        policy_obligations: Policy-mandated requirements
        prior_receipt_hash: Hash of previous receipt (for chaining)
        receipt_hash: Hash of this receipt's content
        signature: Cryptographic signature
    """
    receipt_id: str
    timestamp: datetime
    principal_id: str
    principal_type: str
    action: str
    resource_id: str
    resource_type: str
    correlation_id: str
    decision: str
    reason: str
    elevation_grant_id: Optional[str]
    approved_by: Optional[str]
    params_hash: str
    policy_obligations: List[str]
    prior_receipt_hash: Optional[str]
    receipt_hash: str
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary for serialization."""
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp.isoformat(),
            "principal_id": self.principal_id,
            "principal_type": self.principal_type,
            "action": self.action,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "correlation_id": self.correlation_id,
            "decision": self.decision,
            "reason": self.reason,
            "elevation_grant_id": self.elevation_grant_id,
            "approved_by": self.approved_by,
            "params_hash": self.params_hash,
            "policy_obligations": self.policy_obligations,
            "prior_receipt_hash": self.prior_receipt_hash,
            "receipt_hash": self.receipt_hash,
            "signature": self.signature,
        }
