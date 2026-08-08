from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PostIngestRequest(BaseModel):
    source: str
    source_id: str
    title: str
    body: Optional[str] = None
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    published_at: datetime
    engagement: Dict[str, Any] = Field(default_factory=dict)
    native_tags: List[str] = Field(default_factory=list)

class PostModel(BaseModel):
    id: Optional[int] = None
    source: str
    source_id: str
    title: str
    body: Optional[str] = None
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    published_at: datetime
    fetched_at: datetime
    engagement: Dict[str, Any]
    native_tags: List[str]
    embedding: Optional[List[float]] = None

class ConceptModel(BaseModel):
    id: Optional[int] = None
    canonical_label: str
    aliases: List[str] = Field(default_factory=list)
    embedding: List[float]
    status: str = "active"
    merged_into: Optional[int] = None
    succeeds: List[int] = Field(default_factory=list)
    created_at: datetime
    last_evidence_at: Optional[datetime] = None
    community_id: Optional[int] = None
    community_version: int = 0
    post_count: int = 0

class ConceptEdgeModel(BaseModel):
    concept_a: int
    concept_b: int
    co_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    pmi: float = 0.0
    cross_community: bool = False

class TrendResponse(BaseModel):
    concept_id: int
    canonical_label: str
    post_count_recent: int
    post_count_prior: int
    growth_rate: float
    status: str

class ObservationResponse(BaseModel):
    concept_id: int
    canonical_label: str
    summary: str
    time_series: List[Dict[str, Any]]
    top_posts: List[Dict[str, Any]]
    neighbors: List[Dict[str, Any]]
    edge_changes: List[Dict[str, Any]]
