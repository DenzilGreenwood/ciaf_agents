"""
Evidence vault for tamper-evident audit trails.

Implements cryptographically signed, chained receipts for all actions and decisions.
"""

from typing import List, Optional
import uuid

from ciaf_agents.core.types import ActionRequest, ElevationGrant, EvidenceReceipt, PolicyDecision
from ciaf_agents.utils.helpers import canonical_json, sha256_hex, sign_receipt, utc_now


class EvidenceVault:
    """
    Tamper-evident storage for action receipts.
    
    The Evidence Vault:
    - Creates cryptographically signed receipts
    - Chains receipts via hash linking
    - Supports integrity verification
    - Provides append-only audit trail
    """
    
    def __init__(self, signing_secret: str) -> None:
        """
        Initialize evidence vault.
        
        Args:
            signing_secret: Secret key for HMAC signing (keep secure!)
        """
        self.signing_secret = signing_secret
        self.receipts: List[EvidenceReceipt] = []

    def append(
        self,
        request: ActionRequest,
        decision: PolicyDecision,
        grant: Optional[ElevationGrant],
    ) -> EvidenceReceipt:
        """
        Create and store a new evidence receipt.
        
        Args:
            request: The action request
            decision: The policy decision
            grant: Associated elevation grant (if any)
            
        Returns:
            The created receipt
        """
        # Get hash of previous receipt for chaining
        prior_hash = self.receipts[-1].receipt_hash if self.receipts else None
        
        # Hash the parameters
        params_hash = sha256_hex(canonical_json(request.params))

        # Build the core payload
        base_payload = {
            "receipt_id": str(uuid.uuid4()),
            "timestamp": utc_now().isoformat(),
            "principal_id": request.requested_by.principal_id,
            "principal_type": request.requested_by.principal_type,
            "action": request.action,
            "resource_id": request.resource.resource_id,
            "resource_type": request.resource.resource_type,
            "correlation_id": request.correlation_id,
            "decision": "allow" if decision.allowed else "deny",
            "reason": decision.reason,
            "elevation_grant_id": grant.grant_id if grant else None,
            "approved_by": grant.approved_by if grant else None,
            "params_hash": params_hash,
            "policy_obligations": decision.obligations,
            "prior_receipt_hash": prior_hash,
        }

        # Hash the payload
        receipt_hash = sha256_hex(canonical_json(base_payload))
        
        # Sign the payload + hash
        signature = sign_receipt(
            {**base_payload, "receipt_hash": receipt_hash},
            self.signing_secret
        )

        # Create the receipt object
        receipt = EvidenceReceipt(
            receipt_id=base_payload["receipt_id"],
            timestamp=__import__('datetime').datetime.fromisoformat(base_payload["timestamp"]),
            principal_id=base_payload["principal_id"],
            principal_type=base_payload["principal_type"],
            action=base_payload["action"],
            resource_id=base_payload["resource_id"],
            resource_type=base_payload["resource_type"],
            correlation_id=base_payload["correlation_id"],
            decision=base_payload["decision"],
            reason=base_payload["reason"],
            elevation_grant_id=base_payload["elevation_grant_id"],
            approved_by=base_payload["approved_by"],
            params_hash=base_payload["params_hash"],
            policy_obligations=base_payload["policy_obligations"],
            prior_receipt_hash=base_payload["prior_receipt_hash"],
            receipt_hash=receipt_hash,
            signature=signature,
        )
        
        self.receipts.append(receipt)
        return receipt

    def verify_chain(self) -> bool:
        """
        Verify the integrity of the entire receipt chain.
        
        Checks:
        - Hash integrity of each receipt
        - Signature validity
        - Chain linkage (each receipt references prior)
        
        Returns:
            True if chain is valid, False otherwise
        """
        previous_hash = None
        
        for receipt in self.receipts:
            # Reconstruct the payload
            payload = {
                "receipt_id": receipt.receipt_id,
                "timestamp": receipt.timestamp.isoformat(),
                "principal_id": receipt.principal_id,
                "principal_type": receipt.principal_type,
                "action": receipt.action,
                "resource_id": receipt.resource_id,
                "resource_type": receipt.resource_type,
                "correlation_id": receipt.correlation_id,
                "decision": receipt.decision,
                "reason": receipt.reason,
                "elevation_grant_id": receipt.elevation_grant_id,
                "approved_by": receipt.approved_by,
                "params_hash": receipt.params_hash,
                "policy_obligations": receipt.policy_obligations,
                "prior_receipt_hash": receipt.prior_receipt_hash,
            }

            # Verify hash
            expected_hash = sha256_hex(canonical_json(payload))
            if expected_hash != receipt.receipt_hash:
                return False

            # Verify signature
            expected_sig = sign_receipt(
                {**payload, "receipt_hash": receipt.receipt_hash},
                self.signing_secret
            )
            if expected_sig != receipt.signature:
                return False

            # Verify chain link
            if receipt.prior_receipt_hash != previous_hash:
                return False

            previous_hash = receipt.receipt_hash
        
        return True

    def verify_receipt(self, receipt: EvidenceReceipt) -> bool:
        """
        Verify a single receipt's integrity.
        
        Args:
            receipt: Receipt to verify
            
        Returns:
            True if receipt is valid
        """
        payload = {
            "receipt_id": receipt.receipt_id,
            "timestamp": receipt.timestamp.isoformat(),
            "principal_id": receipt.principal_id,
            "principal_type": receipt.principal_type,
            "action": receipt.action,
            "resource_id": receipt.resource_id,
            "resource_type": receipt.resource_type,
            "correlation_id": receipt.correlation_id,
            "decision": receipt.decision,
            "reason": receipt.reason,
            "elevation_grant_id": receipt.elevation_grant_id,
            "approved_by": receipt.approved_by,
            "params_hash": receipt.params_hash,
            "policy_obligations": receipt.policy_obligations,
            "prior_receipt_hash": receipt.prior_receipt_hash,
        }

        # Check hash
        expected_hash = sha256_hex(canonical_json(payload))
        if expected_hash != receipt.receipt_hash:
            return False

        # Check signature
        expected_sig = sign_receipt(
            {**payload, "receipt_hash": receipt.receipt_hash},
            self.signing_secret
        )
        return expected_sig == receipt.signature

    def get_receipts_by_principal(self, principal_id: str) -> List[EvidenceReceipt]:
        """
        Get all receipts for a specific principal.
        
        Args:
            principal_id: ID to search for
            
        Returns:
            List of receipts
        """
        return [r for r in self.receipts if r.principal_id == principal_id]

    def get_receipts_by_action(self, action: str) -> List[EvidenceReceipt]:
        """
        Get all receipts for a specific action.
        
        Args:
            action: Action to search for
            
        Returns:
            List of receipts
        """
        return [r for r in self.receipts if r.action == action]

    def get_denied_receipts(self) -> List[EvidenceReceipt]:
        """
        Get all denied action receipts.
        
        Returns:
            List of denied receipts
        """
        return [r for r in self.receipts if r.decision == "deny"]

    def get_elevated_receipts(self) -> List[EvidenceReceipt]:
        """
        Get all receipts that used privilege elevation.
        
        Returns:
            List of elevated receipts
        """
        return [r for r in self.receipts if r.elevation_grant_id is not None]

    def export_receipts(self) -> List[dict]:
        """
        Export all receipts as dictionaries for serialization.
        
        Returns:
            List of receipt dictionaries
        """
        return [r.to_dict() for r in self.receipts]
