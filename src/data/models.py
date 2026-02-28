"""
Pydantic data models for IntroAgent.
Defines the schema for events, attendees, match results, and DM drafts.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Attendee(BaseModel):
    """A person who attended a Luma event."""
    name: str
    x_handle: str
    title: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    bio: str = ""
    mutual_events_count: int = 1
    connection_strength: str = "weak"  # weak | medium | strong


class Event(BaseModel):
    """A Luma event with its attendees."""
    event_id: str
    event_name: str
    date: str
    location: str
    platform: str = "Luma"
    attendees: list[Attendee] = Field(default_factory=list)


class UserProfile(BaseModel):
    """The current user's profile."""
    name: str
    x_handle: str
    interests: list[str] = Field(default_factory=list)
    bio: str = ""


class MockData(BaseModel):
    """Root model for the mock JSON data."""
    events: list[Event] = Field(default_factory=list)
    user_profile: UserProfile


class MatchResult(BaseModel):
    """Result from the Matchmaker Agent — the best intermediary found."""
    intermediary_name: str
    intermediary_handle: str
    intermediary_title: Optional[str] = None
    intermediary_bio: str = ""
    intermediary_interests: list[str] = Field(default_factory=list)
    target_name: str
    target_handle: Optional[str] = None
    match_score: float = Field(ge=0.0, le=100.0, description="Match score 0-100")
    common_interests: list[str] = Field(default_factory=list)
    common_events: list[str] = Field(default_factory=list)
    reasoning: str = ""


class DMDraft(BaseModel):
    """A generated DM draft from the Copywriter Agent."""
    recipient_name: str
    recipient_handle: str
    message: str
    tone: str = "friendly"  # friendly | professional | casual
    personalization_points: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
