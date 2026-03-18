"""
Tool execution layer with mediation controls.

Provides guarded execution of agent actions with full IAM/PAM/Evidence integration.
"""

from typing import Any, Dict

from ciaf_agents.core.types import ActionRequest
from ciaf_agents.evidence.vault import EvidenceVault
from ciaf_agents.pam.store import PAMStore
from ciaf_agents.policy.engine import PolicyEngine


class ToolExecutor:
    """
    Mediated execution wrapper for agent actions.
    
    The Tool Executor:
    - Evaluates policy before execution
    - Checks for required PAM elevation
    - Records evidence for all decisions
    - Provides structured execution results
    - Supports interruptibility and kill switches
    """
    
    def __init__(
        self,
        policy_engine: PolicyEngine,
        vault: EvidenceVault,
        pam: PAMStore
    ) -> None:
        """
        Initialize tool executor.
        
        Args:
            policy_engine: Policy evaluation engine
            vault: Evidence vault for receipt storage
            pam: PAM store for grant lookups
        """
        self.policy_engine = policy_engine
        self.vault = vault
        self.pam = pam

    def execute(self, request: ActionRequest) -> Dict[str, Any]:
        """
        Execute an action request with full controls.
        
        Execution flow:
        1. Evaluate policy
        2. Check for active PAM grant if needed
        3. Record evidence
        4. Execute action (if allowed)
        5. Return result with receipt
        
        Args:
            request: The action request to execute
            
        Returns:
            Dictionary with status, result, and receipt
        """
        # Step 1: Evaluate policy
        decision = self.policy_engine.evaluate(request)
        
        # Step 2: Find elevation grant if required
        grant = None
        if decision.allowed or decision.requires_elevation:
            grant = self.pam.find_active_grant(
                principal_id=request.requested_by.principal_id,
                action=request.action,
                resource_type=request.resource.resource_type,
            )

        # Step 3: Record evidence
        receipt = self.vault.append(request, decision, grant)

        # Step 4: Handle denial
        if not decision.allowed:
            return {
                "status": "blocked",
                "reason": decision.reason,
                "requires_elevation": decision.requires_elevation,
                "receipt": receipt.to_dict(),
            }

        # Step 5: Execute action
        # In a real system, this would dispatch to actual tool implementations
        # For now, we return a simulated success result
        result = self._dispatch_to_tool(request)

        return {
            "status": "ok",
            "result": result,
            "receipt": receipt.to_dict(),
        }

    def _dispatch_to_tool(self, request: ActionRequest) -> Dict[str, Any]:
        """
        Dispatch to actual tool implementation.
        
        In a production system, this would:
        - Call registered tool handlers
        - Apply schema validation
        - Enforce timeouts
        - Filter outputs
        - Support interruption
        
        Args:
            request: The action request
            
        Returns:
            Tool execution result
        """
        # Simulated execution result
        return {
            "status": "executed",
            "action": request.action,
            "resource_id": request.resource.resource_id,
            "correlation_id": request.correlation_id,
            "message": f"Successfully executed {request.action} on {request.resource.resource_type}",
        }

    def execute_batch(self, requests: list) -> list:
        """
        Execute multiple requests in sequence.
        
        Args:
            requests: List of action requests
            
        Returns:
            List of results
        """
        return [self.execute(req) for req in requests]

    def dry_run(self, request: ActionRequest) -> Dict[str, Any]:
        """
        Evaluate a request without executing or recording evidence.
        
        Useful for testing policies and permissions.
        
        Args:
            request: The action request to evaluate
            
        Returns:
            Policy decision without execution
        """
        decision = self.policy_engine.evaluate(request)
        
        grant = self.pam.find_active_grant(
            principal_id=request.requested_by.principal_id,
            action=request.action,
            resource_type=request.resource.resource_type,
        )

        return {
            "would_allow": decision.allowed,
            "requires_elevation": decision.requires_elevation,
            "reason": decision.reason,
            "matched_role": decision.matched_role,
            "obligations": decision.obligations,
            "has_active_grant": grant is not None,
        }


class ToolRegistry:
    """
    Registry for tool implementations.
    
    In a production system, this would manage:
    - Tool registration and discovery
    - Schema validation
    - Tool versioning
    - Capability declaration
    """
    
    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self.tools: Dict[str, Any] = {}

    def register_tool(self, action: str, handler: Any) -> None:
        """
        Register a tool handler for an action.
        
        Args:
            action: Action name
            handler: Callable that implements the tool
        """
        self.tools[action] = handler

    def get_tool(self, action: str) -> Any:
        """
        Get tool handler for an action.
        
        Args:
            action: Action name
            
        Returns:
            Tool handler or None
        """
        return self.tools.get(action)

    def list_tools(self) -> list:
        """
        Get list of registered tools.
        
        Returns:
            List of action names
        """
        return list(self.tools.keys())
