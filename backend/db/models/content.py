"""Collected content: authors and normalized posts.

``posts`` is the future high-volume table. It stores the *normalized* post plus a
``raw_payload_uri`` pointing at the original payload in object storage (R2) — the
full raw scraper payload is never stored in PostgreSQL. Uniqueness on
``(source_id, external_id)`` makes normalized ingestion idempotent.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.db.models.mixins import TimestampMixin, jsonb_dict, uuid_pk


class Author(Base, TimestampMixin):
    """A source-specific author identity.

    Kept in its own table so author data is not duplicated across every post.
    Unique on ``(source_id, external_author_id)``.
    """

    __tablename__ = "authors"
    __table_args__ = (
        UniqueConstraint("source_id", "external_author_id", name="uq_authors_source_external"),
        Index("ix_authors_source_id", "source_id"),
        Index("ix_authors_username", "username"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    source_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    external_author_id: Mapped[str] = mapped_column(String(256), nullable=False)
    username: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")

    posts: Mapped[list[Post]] = relationship(back_populates="author")


class Post(Base, TimestampMixin):
    """A normalized post. High-volume; indexed for ingestion & query access paths.

    Index rationale (kept deliberately lean for write throughput):
      * ``uq_posts_source_external`` (source_id, external_id) — idempotency AND
        serves source-scoped and external-id-by-source lookups (leftmost col).
      * single-column indexes only on the remaining documented access paths:
        published_at, collected_at, author_id, content_hash.
    """

    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_posts_source_external"),
        Index("ix_posts_published_at", "published_at"),
        Index("ix_posts_collected_at", "collected_at"),
        Index("ix_posts_author_id", "author_id"),
        Index("ix_posts_content_hash", "content_hash"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    source_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("authors.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    engagement: Mapped[dict] = jsonb_dict()
    raw_payload_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")

    author: Mapped[Author | None] = relationship(back_populates="posts")
