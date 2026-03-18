"""
Privileged Access Management (PAM) Store.

Manages time-bound privilege elevation grants for sensitive actions.
"""

from datetime import timedelta
from typing import Dict, Optional, Set
import uuid

from ciaf_agents.core.types import ElevationGrant
from ciaf_agents.utils.helpers import utc_now


class PAMStore:
    """
    Repository for privilege elevation grants.
    
    The PAM Store is responsible for:
    - Issuing time-bound elevation grants
    - Validating active grants
    - Expiring and revoking grants
    - Tracking approval workflows
    """
    
    def __init__(self) -> None:
        """Initialize empty PAM store."""
        self.grants: Dict[str, ElevationGrant] = {}

    def issue_grant(
        self,
        principal_id: str,
        allowed_actions: Set[str],
        resource_types: Set[str],
        reason: str,
        approved_by: str,
        duration_minutes: int,
        ticket_id: str,
    ) -> ElevationGrant:
        """
        Issue a new time-bound privilege elevation grant.
        
        Args:
            principal_id: ID of the principal receiving elevation
            allowed_actions: Set of actions permitted under this grant
            resource_types: Set of resource types this applies to
            reason: Business justification for elevation
            approved_by: Identity of the approver
            duration_minutes: How long the grant is valid
            ticket_id: Reference to approval ticket/case
            
        Returns:
            The created elevation grant
        """
        grant = ElevationGrant(
            grant_id=str(uuid.uuid4()),
            principal_id=principal_id,
            allowed_actions=allowed_actions,
            resource_types=resource_types,
            reason=reason,
            approved_by=approved_by,
            expires_at=utc_now() + timedelta(minutes=duration_minutes),
            ticket_id=ticket_id,
        )
        self.grants[grant.grant_id] = grant
        return grant

    def find_active_grant(
        self,
        principal_id: str,
        action: str,
        resource_type: str,
    ) -> Optional[ElevationGrant]:
        """
        Find an active grant that permits the specified action.
        
        Args:
            principal_id: ID of the principal
            action: Action being attempted
            resource_type: Type of resource being accessed
            
        Returns:
            Active grant if found, None otherwise
        """
        for grant in self.grants.values():
            if (
                grant.principal_id == principal_id
                and grant.is_active()
                and action in grant.allowed_actions
                and resource_type in grant.resource_types
            ):
                return grant
        return None

    def revoke_grant(self, grant_id: str) -> bool:
        """
        Revoke a grant immediately (emergency revocation).
        
        Args:
            grant_id: ID of grant to revoke
            
        Returns:
            True if grant was found and revoked, False otherwise
        """
        if grant_id in self.grants:
            del self.grants[grant_id]
            return True
        return False

    def revoke_all_grants_for_principal(self, principal_id: str) -> int:
        """
        Revoke all grants for a specific principal (kill switch).
        
        Args:
            principal_id: ID of principal whose grants should be revoked
            
        Returns:
            Number of grants revoked
        """
        grants_to_remove = [
            grant_id for grant_id, grant in self.grants.items()
            if grant.principal_id == principal_id
        ]
        for grant_id in grants_to_remove:
            del self.grants[grant_id]
        return len(grants_to_remove)

    def cleanup_expired_grants(self) -> int:
        """
        Remove expired grants from storage.
        
        Returns:
            Number of grants removed
        """
        expired_grant_ids = [
            grant_id for grant_id, grant in self.grants.items()
            if not grant.is_active()
        ]
        for grant_id in expired_grant_ids:
            del self.grants[grant_id]
        return len(expired_grant_ids)

    def get_active_grants_for_principal(self, principal_id: str) -> list:
        """
        Get all active grants for a principal.
        
        Args:
            principal_id: ID of the principal
            
        Returns:
            List of active grants
        """
        return [
            grant for grant in self.grants.values()
            if grant.principal_id == principal_id and grant.is_active()
        ]

    def extend_grant(self, grant_id: str, additional_minutes: int) -> bool:
        """
        Extend the expiration time of a grant.
        
        Note: This should typically require additional approval.
        
        Args:
            grant_id: ID of grant to extend
            additional_minutes: Additional time to add
            
        Returns:
            True if grant was found and extended, False otherwise
        """
        if grant_id in self.grants:
            grant = self.grants[grant_id]
            # Create new grant with extended time
            extended_grant = ElevationGrant(
                grant_id=grant.grant_id,
                principal_id=grant.principal_id,
                allowed_actions=grant.allowed_actions,
                resource_types=grant.resource_types,
                reason=grant.reason + f" [Extended by {additional_minutes}m]",
                approved_by=grant.approved_by,
                expires_at=grant.expires_at + timedelta(minutes=additional_minutes),
                ticket_id=grant.ticket_id,
            )
            self.grants[grant_id] = extended_grant
            return True
        return False
