from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


EntityType = Literal["person", "org", "bot", "page"]


class Entity(BaseModel):
    entity_id: str
    type: EntityType
    source: str
    source_identifier: str


class Observation(BaseModel):
    observation_id: str
    timestamp: datetime
    actor_entity_id: str
    kind: str
    target_entity_id: Optional[str] = None
    context: Optional[str] = None
    evidence_uri: Optional[str] = None


class Link(BaseModel):
    from_entity_id: str
    to_entity_id: str
    weight: float
    window_days: int
    derivation: str = Field(default="log(1 + count_30d)")
