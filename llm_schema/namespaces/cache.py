"""llm_schema.namespaces.cache — Semantic cache payload types.

Classes
-------
CacheHitPayload
    ``llm.cache.hit`` — a request was served from the cache.
CacheMissPayload
    ``llm.cache.miss`` — a request was not found in the cache.
CacheEvictedPayload
    ``llm.cache.evicted`` — one or more cache entries were evicted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CacheHitPayload:
    """Payload for ``llm.cache.hit``.

    Parameters
    ----------
    cache_key_hash:
        SHA-256 hex digest (or similar) of the normalised cache lookup key.
    cache_store:
        Identifier for the cache backend, e.g. ``"redis:prod-cluster"``.
    similarity_score:
        Optional cosine / semantic similarity score in ``[0.0, 1.0]`` for
        approximate (ANN) cache hits.
    cached_event_id:
        Optional ULID of the original :class:`~llm_schema.event.Event` that
        is being replayed from cache.
    ttl_seconds:
        Optional remaining TTL of the cache entry in seconds.
    """

    cache_key_hash: str
    cache_store: str
    similarity_score: Optional[float] = None
    cached_event_id: Optional[str] = None
    ttl_seconds: Optional[int] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.cache_key_hash or not isinstance(self.cache_key_hash, str):
            raise ValueError("CacheHitPayload.cache_key_hash must be a non-empty string")
        if not self.cache_store or not isinstance(self.cache_store, str):
            raise ValueError("CacheHitPayload.cache_store must be a non-empty string")
        if self.similarity_score is not None:
            if not isinstance(self.similarity_score, (int, float)):
                raise ValueError("CacheHitPayload.similarity_score must be a number or None")
            if not (0.0 <= self.similarity_score <= 1.0):
                raise ValueError(
                    f"CacheHitPayload.similarity_score must be in [0.0, 1.0], "
                    f"got {self.similarity_score}"
                )
        if self.ttl_seconds is not None and (
            not isinstance(self.ttl_seconds, int) or self.ttl_seconds < 0
        ):
            raise ValueError("CacheHitPayload.ttl_seconds must be a non-negative int or None")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "cache_key_hash": self.cache_key_hash,
            "cache_store": self.cache_store,
        }
        if self.similarity_score is not None:
            result["similarity_score"] = self.similarity_score
        if self.cached_event_id is not None:
            result["cached_event_id"] = self.cached_event_id
        if self.ttl_seconds is not None:
            result["ttl_seconds"] = self.ttl_seconds
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheHitPayload":
        """Reconstruct a :class:`CacheHitPayload` from a plain dict."""
        return cls(
            cache_key_hash=str(data["cache_key_hash"]),
            cache_store=str(data["cache_store"]),
            similarity_score=data.get("similarity_score"),
            cached_event_id=data.get("cached_event_id"),
            ttl_seconds=int(data["ttl_seconds"]) if data.get("ttl_seconds") is not None else None,
        )


@dataclass(frozen=True)
class CacheMissPayload:
    """Payload for ``llm.cache.miss``.

    Parameters
    ----------
    cache_key_hash:
        SHA-256 hex digest (or similar) of the normalised lookup key.
    cache_store:
        Identifier for the cache backend.
    reason:
        Optional human-readable reason for the miss, e.g. ``"key_not_found"``,
        ``"similarity_below_threshold"``, ``"expired"``.
    """

    cache_key_hash: str
    cache_store: str
    reason: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.cache_key_hash or not isinstance(self.cache_key_hash, str):
            raise ValueError("CacheMissPayload.cache_key_hash must be a non-empty string")
        if not self.cache_store or not isinstance(self.cache_store, str):
            raise ValueError("CacheMissPayload.cache_store must be a non-empty string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "cache_key_hash": self.cache_key_hash,
            "cache_store": self.cache_store,
        }
        if self.reason is not None:
            result["reason"] = self.reason
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheMissPayload":
        """Reconstruct a :class:`CacheMissPayload` from a plain dict."""
        return cls(
            cache_key_hash=str(data["cache_key_hash"]),
            cache_store=str(data["cache_store"]),
            reason=data.get("reason"),
        )


@dataclass(frozen=True)
class CacheEvictedPayload:
    """Payload for ``llm.cache.evicted``.

    Parameters
    ----------
    cache_key_hash:
        Hash of the primary evicted entry (or sentinel hash for bulk eviction).
    cache_store:
        Identifier for the cache backend.
    reason:
        Why the entry was evicted: ``"ttl_expired"``, ``"lru"``,
        ``"capacity"``, ``"manual"``, etc.
    evicted_count:
        Number of entries evicted in this operation (defaults to ``1``).
    """

    cache_key_hash: str
    cache_store: str
    reason: str
    evicted_count: int = 1

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.cache_key_hash or not isinstance(self.cache_key_hash, str):
            raise ValueError("CacheEvictedPayload.cache_key_hash must be a non-empty string")
        if not self.cache_store or not isinstance(self.cache_store, str):
            raise ValueError("CacheEvictedPayload.cache_store must be a non-empty string")
        if not self.reason or not isinstance(self.reason, str):
            raise ValueError("CacheEvictedPayload.reason must be a non-empty string")
        if not isinstance(self.evicted_count, int) or self.evicted_count < 1:
            raise ValueError("CacheEvictedPayload.evicted_count must be a positive int")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "cache_key_hash": self.cache_key_hash,
            "cache_store": self.cache_store,
            "reason": self.reason,
            "evicted_count": self.evicted_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEvictedPayload":
        """Reconstruct a :class:`CacheEvictedPayload` from a plain dict."""
        return cls(
            cache_key_hash=str(data["cache_key_hash"]),
            cache_store=str(data["cache_store"]),
            reason=str(data["reason"]),
            evicted_count=int(data.get("evicted_count", 1)),
        )


__all__: list[str] = [
    "CacheHitPayload",
    "CacheMissPayload",
    "CacheEvictedPayload",
]
