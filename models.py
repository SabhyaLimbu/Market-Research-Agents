"""Structured data passed between agent roles."""
from typing import Optional
from pydantic import BaseModel, Field


class Source(BaseModel):
    title: str
    url: str = ""
    snippet: str = ""


class Findings(BaseModel):
    """Researcher output."""
    facts: list[str] = Field(description="Concise facts supported by the sources")
    sources: list[Source]
    data_origin: str = Field(description="'web' or 'sample'")
    gaps: list[str] = Field(default_factory=list, description="Things we could not find")


class Brief(BaseModel):
    """Analyst output (draft and final)."""
    summary: str
    competitors: list[str] = Field(default_factory=list, description="At most two")
    key_observations: list[str]
    sources: list[str] = Field(description="Titles/URLs actually used")
    missing_information: list[str] = Field(default_factory=list)


class Critique(BaseModel):
    """Critic output."""
    approved: bool
    feedback: str = ""


class WorkflowState(BaseModel):
    """Shared state handed from role to role."""
    query: str
    findings: Optional[Findings] = None
    draft: Optional[Brief] = None
    critique: Optional[Critique] = None
    final: Optional[Brief] = None
    revised: bool = False
    log: list[str] = Field(default_factory=list)
