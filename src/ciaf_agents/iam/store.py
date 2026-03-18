"""
Identity and Access Management (IAM) Store.

Manages agent identities, role definitions, and permission resolution.
"""

from typing import Dict, List, Tuple

from ciaf_agents.core.types import Identity, RoleDefinition, Permission


class IAMStore:
    """
    Central repository for identity and role management.
    
    The IAM Store is responsible for:
    - Storing role definitions with their permissions
    - Managing agent identities with role assignments
    - Resolving effective permissions for identities
    """
    
    def __init__(self) -> None:
        """Initialize empty IAM store."""
        self.role_definitions: Dict[str, RoleDefinition] = {}
        self.identities: Dict[str, Identity] = {}

    def add_role(self, role: RoleDefinition) -> None:
        """
        Register a role definition.
        
        Args:
            role: Role definition to add
        """
        self.role_definitions[role.name] = role

    def add_identity(self, identity: Identity) -> None:
        """
        Register an identity (agent, user, or service).
        
        Args:
            identity: Identity to register
        """
        self.identities[identity.principal_id] = identity

    def get_identity(self, principal_id: str) -> Identity:
        """
        Retrieve an identity by ID.
        
        Args:
            principal_id: Unique identifier for the principal
            
        Returns:
            Identity object
            
        Raises:
            KeyError: If identity not found
        """
        return self.identities[principal_id]

    def get_identity_permissions(self, identity: Identity) -> List[Tuple[str, Permission]]:
        """
        Resolve all permissions for an identity based on assigned roles.
        
        Args:
            identity: The identity to resolve permissions for
            
        Returns:
            List of (role_name, permission) tuples
        """
        results: List[Tuple[str, Permission]] = []
        for role_name in identity.roles:
            role = self.role_definitions.get(role_name)
            if role:
                for perm in role.permissions:
                    results.append((role_name, perm))
        return results

    def revoke_identity(self, principal_id: str) -> None:
        """
        Revoke an identity (emergency kill switch).
        
        Args:
            principal_id: ID of identity to revoke
        """
        if principal_id in self.identities:
            del self.identities[principal_id]

    def list_identities_by_role(self, role_name: str) -> List[Identity]:
        """
        Find all identities with a specific role.
        
        Args:
            role_name: Name of the role to search for
            
        Returns:
            List of identities with that role
        """
        return [
            identity for identity in self.identities.values()
            if role_name in identity.roles
        ]

    def update_identity_roles(self, principal_id: str, new_roles: set) -> None:
        """
        Update the roles assigned to an identity.
        
        Note: Since Identity is frozen, this creates a new Identity object.
        
        Args:
            principal_id: ID of identity to update
            new_roles: New set of role names
            
        Raises:
            KeyError: If identity not found
        """
        old_identity = self.identities[principal_id]
        updated_identity = Identity(
            principal_id=old_identity.principal_id,
            principal_type=old_identity.principal_type,
            display_name=old_identity.display_name,
            roles=new_roles,
            attributes=old_identity.attributes
        )
        self.identities[principal_id] = updated_identity
