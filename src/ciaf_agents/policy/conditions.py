"""
Common policy condition functions.

These are reusable conditions for permission evaluation.
"""

from typing import Any, Dict

from ciaf_agents.core.types import Identity, Resource


def any_condition(identity: Identity, resource: Resource, params: Dict[str, Any]) -> bool:
    """
    Always returns True - permissive condition.
    
    Args:
        identity: Requesting identity
        resource: Target resource
        params: Action parameters
        
    Returns:
        Always True
    """
    return True


def same_tenant_only(identity: Identity, resource: Resource, params: Dict[str, Any]) -> bool:
    """
    Only allow access if identity and resource are in the same tenant.
    
    Args:
        identity: Requesting identity
        resource: Target resource
        params: Action parameters
        
    Returns:
        True if tenants match
    """
    identity_tenant = identity.attributes.get("tenant")
    if not identity_tenant:
        return False
    return identity_tenant == resource.owner_tenant


def same_department_only(identity: Identity, resource: Resource, params: Dict[str, Any]) -> bool:
    """
    Only allow access if identity and resource are in the same department.
    
    Args:
        identity: Requesting identity
        resource: Target resource
        params: Action parameters
        
    Returns:
        True if departments match
    """
    return identity.attributes.get("department") == resource.attributes.get("department")


def production_environment_only(identity: Identity, resource: Resource, params: Dict[str, Any]) -> bool:
    """
    Only allow if identity is in production environment.
    
    Args:
        identity: Requesting identity
        resource: Target resource
        params: Action parameters
        
    Returns:
        True if identity is in production
    """
    return identity.attributes.get("environment") == "production"


def non_production_only(identity: Identity, resource: Resource, params: Dict[str, Any]) -> bool:
    """
    Only allow if identity is NOT in production environment.
    
    Args:
        identity: Requesting identity
        resource: Target resource
        params: Action parameters
        
    Returns:
        True if identity is not in production
    """
    return identity.attributes.get("environment") != "production"
