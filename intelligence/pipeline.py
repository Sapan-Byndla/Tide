"""Intelligence pipeline skeleton.

Defines the *shape* of the normalize -> extract -> embed -> relate flow using the
ports from ``contracts``. Concrete extraction/embedding logic arrives in later
phases; Phase 0 wires the dependencies and documents the stages without running
any model.
"""

from __future__ import annotations

from collections.abc import Sequence

from contracts.embeddings import EmbeddingProvider
from contracts.models import EmbeddingVector, NormalizedPost, RawPost
from contracts.normalizer import PostNormalizer


class IntelligencePipeline:
    """Orchestrates conversion of raw posts into graph-ready knowledge.

    Dependencies are injected (constructor injection) so any adapter — including
    no-op stubs used in tests — satisfies the pipeline without code changes.
    """

    def __init__(
        self,
        normalizer: PostNormalizer,
        embeddings: EmbeddingProvider,
    ) -> None:
        self._normalizer = normalizer
        self._embeddings = embeddings

    async def normalize(self, post: RawPost) -> NormalizedPost:
        """Stage 1 — normalize a raw post into the common schema."""
        return await self._normalizer.normalize(post)

    async def embed(self, post: NormalizedPost) -> EmbeddingVector:
        """Stage 3 — embed normalized text for semantic retrieval."""
        return await self._embeddings.embed(post.dedup_key, post.text)

    async def process(self, posts: Sequence[RawPost]) -> list[NormalizedPost]:
        """Run available Phase 0 stages over a batch of raw posts.

        Entity/concept extraction and relationship building are intentionally not
        implemented in Phase 0; this method currently performs normalization only
        and exists to prove the wiring.
        """
        normalized: list[NormalizedPost] = []
        for post in posts:
            if self._normalizer.supports(post):
                normalized.append(await self._normalizer.normalize(post))
        return normalized
