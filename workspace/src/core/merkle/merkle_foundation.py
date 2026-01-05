#!/usr/bin/env python3
"""
L0: Immutable Foundation - Merkle Foundation
AXIOM Layer 0: Merkle 樹驗證基礎

Responsibilities:
- Merkle tree construction and verification
- State integrity proofs
- Tamper-evident logging
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib
import json


@dataclass
class MerkleNode:
    """Merkle tree node."""
    hash: str
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    data: Optional[Any] = None


class MerkleTree:
    """
    Merkle tree implementation for state verification.

    Part of L0 Immutable Foundation layer.
    """

    VERSION = "2.0.0"
    LAYER = "L0_immutable_foundation"

    def __init__(self, hash_func=None):
        self.hash_func = hash_func or self._default_hash
        self.root: Optional[MerkleNode] = None
        self.leaves: List[MerkleNode] = []

    def _default_hash(self, data: bytes) -> str:
        """Default SHA-256 hash function."""
        return hashlib.sha256(data).hexdigest()

    def add_leaf(self, data: Any) -> str:
        """Add a leaf to the tree."""
        serialized = json.dumps(data, sort_keys=True).encode()
        leaf_hash = self.hash_func(serialized)
        node = MerkleNode(hash=leaf_hash, data=data)
        self.leaves.append(node)
        return leaf_hash

    def build(self) -> Optional[str]:
        """Build the Merkle tree and return root hash."""
        if not self.leaves:
            return None

        nodes = self.leaves.copy()

        while len(nodes) > 1:
            next_level = []
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else left

                combined = (left.hash + right.hash).encode()
                parent_hash = self.hash_func(combined)
                parent = MerkleNode(hash=parent_hash, left=left, right=right)
                next_level.append(parent)
            nodes = next_level

        self.root = nodes[0]
        return self.root.hash

    def get_proof(self, leaf_index: int) -> List[Dict[str, str]]:
        """Get Merkle proof for a leaf."""
        if not self.root or leaf_index >= len(self.leaves):
            return []

        proof = []
        # Simplified proof generation
        # Full implementation would traverse tree
        return proof

    def verify_proof(self, leaf_hash: str, proof: List[Dict[str, str]],
                     root_hash: str) -> bool:
        """Verify a Merkle proof."""
        current = leaf_hash
        for step in proof:
            if step.get("position") == "left":
                current = self.hash_func((step["hash"] + current).encode())
            else:
                current = self.hash_func((current + step["hash"]).encode())
        return current == root_hash

    def get_root_hash(self) -> Optional[str]:
        """Get the root hash."""
        return self.root.hash if self.root else None


class StateVerifier:
    """
    State verification using Merkle proofs.

    Ensures state integrity across system components.
    """

    def __init__(self):
        self.tree = MerkleTree()
        self.state_log: List[Dict[str, Any]] = []

    def record_state(self, component: str, state: Dict[str, Any]) -> str:
        """Record a component state."""
        entry = {
            "component": component,
            "state": state,
            "timestamp": self._get_timestamp(),
        }
        leaf_hash = self.tree.add_leaf(entry)
        self.state_log.append({"hash": leaf_hash, **entry})
        return leaf_hash

    def finalize(self) -> str:
        """Finalize and get root hash."""
        return self.tree.build()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Module exports
__all__ = [
    "MerkleTree",
    "MerkleNode",
    "StateVerifier",
]
