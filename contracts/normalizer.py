"""Normalization contract.

The intelligence subsystem turns heterogeneous :class:`RawPost` objects into a
single common :class:`NormalizedPost` schema. This is the boundary between
"source-shaped" data and the shape the rest of TIDE reasons over.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from contracts.models import NormalizedPost, RawPost


class PostNormalizer(ABC):
    """Converts a raw, source-specific post into the common schema."""

    @abstractmethod
    async def normalize(self, post: RawPost) -> NormalizedPost:
        """Normalize a single raw post.

        Implementations should be pure with respect to their input: no network
        or storage side effects. Cleaning, language detection, de-boilerplating,
        and token counting belong here.
        """

    @abstractmethod
    def supports(self, post: RawPost) -> bool:
        """Return ``True`` if this normalizer can handle the given post."""
