"""
Policy evaluation engine.

Implements the core decision logic for IAM, PAM, and runtime boundary enforcement.
"""

from typing import List, Optional, Set

from ciaf_agents.core.types import ActionRequest, Identity, PolicyDecision, Resource
from ciaf_agents.iam.store import IAMStore
from ciaf_agents.pam.store import PAMStore


class PolicyEngine:
    """
    Central policy evaluation engine.
    
    The Policy Engine implements multi-layered decision logic:
    1. IAM permission checking (RBAC/ABAC)
    2. Boundary policy enforcement (tenant isolation, allowlists)
    3. Sensitivity detection (requires PAM elevation)
    4. Runtime constraint evaluation
    """
    
    def __init__(
        self,
        iam: IAMStore,
        pam: PAMStore,
        sensitive_actions: Optional[Set[str]] = None,
        privileged_actions: Optional[Set[str]] = None
    ) -> None:
        """
        Initialize policy engine.
        
        Args:
            iam: IAM store for identity and permission resolution
            pam: PAM store for elevation grant lookup
            sensitive_actions: Actions that require PAM elevation
            privileged_actions: Alias for sensitive_actions
        """
        self.iam = iam
        self.pam = pam
        
        # Combine sensitive and privileged actions
        self.sensitive_actions: Set[str] = set()
        if sensitive_actions:
            self.sensitive_actions.update(sensitive_actions)
        if privileged_actions:
            self.sensitive_actions.update(privileged_actions)
        
        # Default sensitive actions if none specified
        if not self.sensitive_actions:
            self.sensitive_actions = {
                "delete_record",
                "send_external_email",
                "approve_payment",
                "export_patient_data",
                "export_data",
                "modify_prod_config",
            }

    def evaluate(self, request: ActionRequest) -> PolicyDecision:
        """
        Evaluate whether an action request should be allowed.
        
        Decision flow:
        1. Check IAM permissions (RBAC/ABAC)
        2. Enforce boundary policies (tenant, allowlists)
        3. Check for sensitive actions requiring PAM
        4. Apply runtime constraints (thresholds, business hours)
        
        Args:
            request: The action request to evaluate
            
        Returns:
            Policy decision with allow/deny and any obligations
        """
        identity = request.requested_by
        resource = request.resource
        params = request.params

        # Step 1: IAM permission check
        matched_role = None
        has_base_permission = False

        for role_name, permission in self.iam.get_identity_permissions(identity):
            if permission.action == request.action and permission.matches(identity, resource, params):
                has_base_permission = True
                matched_role = role_name
                break

        if not has_base_permission:
            return PolicyDecision(
                allowed=False,
                requires_elevation=False,
                reason="Denied by IAM: no matching permission.",
            )

        # Step 2: Boundary policy enforcement
        obligations: List[str] = []

        # Tenant isolation check
        identity_tenant = identity.attributes.get("tenant")
        if identity_tenant and identity_tenant != resource.owner_tenant:
            return PolicyDecision(
                allowed=False,
                requires_elevation=False,
                reason="Denied by policy: cross-tenant access not allowed.",
                matched_role=matched_role,
            )

        # Step 3: Sensitivity and PAM check
        if request.action in self.sensitive_actions:
            grant = self.pam.find_active_grant(
                principal_id=identity.principal_id,
                action=request.action,
                resource_type=resource.resource_type
            )
            if not grant:
                return PolicyDecision(
                    allowed=False,
                    requires_elevation=True,
                    reason="PAM elevation required for sensitive action.",
                    matched_role=matched_role,
                    obligations=["human_approval", "jit_elevation", "heightened_logging"],
                )
            obligations.extend(["pam_session_attached", "heightened_logging"])

        # Step 4: Action-specific runtime constraints
        
        # Payment threshold check
        if request.action == "approve_payment":
            amount = float(params.get("amount", 0))
            if amount > 10000:
                grant = self.pam.find_active_grant(
                    principal_id=identity.principal_id,
                    action=request.action,
                    resource_type=resource.resource_type
                )
                if not grant:
                    return PolicyDecision(
                        allowed=False,
                        requires_elevation=True,
                        reason="Payment above threshold requires privileged approval.",
                        matched_role=matched_role,
                        obligations=["two_person_review", "jit_elevation"],
                    )
                obligations.append("two_person_review_verified")

        # Email domain allowlist check
        if request.action == "send_external_email":
            to_address = str(params.get("to", ""))
            if "@" in to_address:
                to_domain = to_address.split("@")[-1].lower()
                allowed_domains = set(identity.attributes.get("allowed_email_domains", []))
                if to_domain not in allowed_domains:
                    return PolicyDecision(
                        allowed=False,
                        requires_elevation=False,
                        reason="Denied by policy: email domain outside allowlist.",
                        matched_role=matched_role,
                    )

        # All checks passed
        return PolicyDecision(
            allowed=True,
            requires_elevation=False,
            reason="Allowed by IAM and runtime boundary policy.",
            matched_role=matched_role,
            obligations=obligations,
        )

    def add_sensitive_action(self, action: str) -> None:
        """
        Register an action as sensitive (requires PAM elevation).
        
        Args:
            action: Action name to mark as sensitive
        """
        self.sensitive_actions.add(action)

    def remove_sensitive_action(self, action: str) -> None:
        """
        Remove an action from the sensitive list.
        
        Args:
            action: Action name to remove
        """
        self.sensitive_actions.discard(action)

    def is_sensitive_action(self, action: str) -> bool:
        """
        Check if an action is marked as sensitive.
        
        Args:
            action: Action name to check
            
        Returns:
            True if action is sensitive
        """
        return action in self.sensitive_actions
