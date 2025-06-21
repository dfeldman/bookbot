"""
Models for LLM picker module.

This module defines the data models for LLM configuration and selection.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMGroup(str, Enum):
    """Enum for LLM task groups."""
    WRITER = "writer"
    EDITOR = "editor"
    EXPLICIT = "explicit"
    TAGGER = "tagger"
    THINKER = "thinker"
    REVIEWER = "reviewer"
    OVERRIDE = "override"
    EXPLICIT = "explicit"
    ALL = "all"  # Special case for LLMs that can be used for any task group


class LLMInfo(BaseModel):
    """Information about an LLM model and its capabilities."""
    id: str
    input_cost_per_mtok: float = Field(description="Input cost per million tokens")
    output_cost_per_mtok: float = Field(description="Output cost per million tokens")
    seconds_per_output_mtok: float = Field(default=0, description="Seconds per million output tokens, 0 if unknown")
    router: str = Field(default="openrouter", description="Router service, e.g., 'openrouter'")
    name: str = Field(description="Human-readable model name")
    description: str = Field(description="1-2 sentence description of the model's capabilities")
    company: str = Field(description="Company that created the model, e.g., 'OpenAI'")
    context_length: int = Field(description="Context length in tokens")
    groups: List[str] = Field(description="List of valid LLM groups for this model")
    quality_score: int = Field(description="Quality score from 1 to 10")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "anthropic/claude-3-haiku",
                "input_cost_per_mtok": 1.25,
                "output_cost_per_mtok": 3.75,
                "seconds_per_output_mtok": 0.75,
                "router": "openrouter",
                "name": "Claude 3 Haiku",
                "description": "Anthropic's fastest model with excellent reasoning capabilities.",
                "company": "Anthropic",
                "context_length": 200000,
                "groups": ["writer", "editor", "thinker", "reviewer"],
                "quality_score": 8
            }
        }


class LLMDefaults(BaseModel):
    """Book LLM default settings."""
    writer: Optional[str] = None  # The ID of the default LLM for writing
    editor: Optional[str] = None  # The ID of the default LLM for editing
    explicit: Optional[str] = None  # The ID of the default LLM for explicit content
    tagger: Optional[str] = None  # The ID of the default LLM for tagging
    thinker: Optional[str] = None  # The ID of the default LLM for thinking/planning
    reviewer: Optional[str] = None  # The ID of the default LLM for reviewing
    override: Optional[str] = None  # The ID of the override LLM (used for all tasks regardless of group)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMDefaults':
        """Create from dictionary, handling missing keys."""
        return cls(**{k: v for k, v in data.items() if k in cls.model_fields})


class LLMRequest(BaseModel):
    """Request model for setting LLM defaults."""
    llm_id: str = Field(description="LLM ID to set as default for the specified group")
    group: str = Field(description="LLM group to set the default for")
