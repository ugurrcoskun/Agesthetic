"""
Data loader for IntroAgent.
Loads and processes mock event data from JSON, deduplicates attendees,
and builds a unified attendee profile list.
"""

import json
from pathlib import Path
from typing import Optional

from src.data.models import MockData, Attendee, Event, UserProfile


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_MOCK_FILE = DATA_DIR / "luma_attendees_mock.json"


def load_mock_data(filepath: Optional[Path] = None) -> MockData:
    """Load mock data from JSON file and return as MockData model."""
    path = filepath or DEFAULT_MOCK_FILE
    if not path.exists():
        raise FileNotFoundError(f"Mock data file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return MockData.model_validate(raw)


def get_unique_attendees(data: MockData) -> list[Attendee]:
    """
    Deduplicate attendees across all events.
    When the same person appears in multiple events, merge their data
    and keep the highest connection_strength and mutual_events_count.
    """
    attendee_map: dict[str, Attendee] = {}
    strength_order = {"weak": 0, "medium": 1, "strong": 2}

    for event in data.events:
        for att in event.attendees:
            key = att.x_handle.lower()
            if key in attendee_map:
                existing = attendee_map[key]
                # Keep higher connection strength
                if strength_order.get(att.connection_strength, 0) > strength_order.get(
                    existing.connection_strength, 0
                ):
                    attendee_map[key] = att
                # Keep higher mutual_events_count
                elif att.mutual_events_count > existing.mutual_events_count:
                    attendee_map[key] = att.model_copy(
                        update={"connection_strength": existing.connection_strength}
                    )
            else:
                attendee_map[key] = att

    return list(attendee_map.values())


def find_attendee_by_name(
    attendees: list[Attendee], name: str
) -> Optional[Attendee]:
    """Find an attendee by name (case-insensitive partial match)."""
    name_lower = name.lower()
    for att in attendees:
        if name_lower in att.name.lower():
            return att
    return None


def get_events_for_attendee(data: MockData, x_handle: str) -> list[Event]:
    """Get all events a specific attendee has participated in."""
    handle_lower = x_handle.lower()
    events = []
    for event in data.events:
        for att in event.attendees:
            if att.x_handle.lower() == handle_lower:
                events.append(event)
                break
    return events


def get_shared_events(
    data: MockData, handle_a: str, handle_b: str
) -> list[Event]:
    """Get events where both attendees were present."""
    events_a = {e.event_id for e in get_events_for_attendee(data, handle_a)}
    shared = []
    for event in data.events:
        if event.event_id not in events_a:
            continue
        handles_in_event = {a.x_handle.lower() for a in event.attendees}
        if handle_b.lower() in handles_in_event:
            shared.append(event)
    return shared


def build_attendees_context(data: MockData) -> str:
    """
    Build a formatted text context of all attendees and events
    for the LLM agent to process.
    """
    lines = []
    lines.append("=== EVENT ATTENDEE DATA ===\n")

    for event in data.events:
        lines.append(f"📅 Event: {event.event_name}")
        lines.append(f"   Date: {event.date} | Location: {event.location}")
        lines.append(f"   Platform: {event.platform}")
        lines.append(f"   Attendees ({len(event.attendees)}):")
        for att in event.attendees:
            lines.append(f"   - {att.name} ({att.x_handle})")
            if att.title:
                lines.append(f"     Title: {att.title}")
            lines.append(f"     Interests: {', '.join(att.interests)}")
            lines.append(f"     Bio: {att.bio}")
            lines.append(
                f"     Connection: {att.connection_strength} "
                f"(mutual events: {att.mutual_events_count})"
            )
        lines.append("")

    lines.append("=== USER PROFILE ===")
    lines.append(f"Name: {data.user_profile.name}")
    lines.append(f"Handle: {data.user_profile.x_handle}")
    lines.append(f"Interests: {', '.join(data.user_profile.interests)}")
    lines.append(f"Bio: {data.user_profile.bio}")

    return "\n".join(lines)
