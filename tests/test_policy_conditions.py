"""
Comprehensive tests for policy conditions.
"""

import pytest

from ciaf_agents.core import Identity, Resource
from ciaf_agents.policy.conditions import (
    any_condition,
    same_tenant_only,
    same_department_only,
    production_environment_only,
    non_production_only,
)


def test_any_condition_always_true():
    """Test that any_condition always returns True."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    assert any_condition(identity, resource, {}) == True


def test_same_tenant_only_matching():
    """Test same_tenant_only with matching tenants."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"tenant": "tenant-a"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    assert same_tenant_only(identity, resource, {}) == True


def test_same_tenant_only_not_matching():
    """Test same_tenant_only with different tenants."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"tenant": "tenant-a"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="document",
        owner_tenant="tenant-b",
        attributes={}
    )
    
    assert same_tenant_only(identity, resource, {}) == False


def test_same_tenant_only_missing_tenant():
    """Test same_tenant_only when identity has no tenant attribute."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    assert same_tenant_only(identity, resource, {}) == False


def test_same_department_only_matching():
    """Test same_department_only with matching departments."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"department": "engineering"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={"department": "engineering"}
    )
    
    assert same_department_only(identity, resource, {}) == True


def test_same_department_only_not_matching():
    """Test same_department_only with different departments."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"department": "engineering"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="document",
        owner_tenant="tenant-a",
        attributes={"department": "finance"}
    )
    
    assert same_department_only(identity, resource, {}) == False


def test_production_environment_only_true():
    """Test production_environment_only for production identity."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"environment": "production"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="server",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    assert production_environment_only(identity, resource, {}) == True


def test_production_environment_only_false():
    """Test production_environment_only for non-production identity."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"environment": "staging"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="server",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    assert production_environment_only(identity, resource, {}) == False


def test_non_production_only_true():
    """Test non_production_only for staging identity."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"environment": "staging"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="server",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    assert non_production_only(identity, resource, {}) == True


def test_non_production_only_false():
    """Test non_production_only for production identity."""
    identity = Identity(
        principal_id="test-001",
        principal_type="agent",
        display_name="Test",
        roles=set(),
        attributes={"environment": "production"}
    )
    
    resource = Resource(
        resource_id="res-1",
        resource_type="server",
        owner_tenant="tenant-a",
        attributes={}
    )
    
    assert non_production_only(identity, resource, {}) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
