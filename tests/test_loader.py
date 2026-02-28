"""
Tests for the data loader module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.data.loader import (
    load_mock_data,
    get_unique_attendees,
    find_attendee_by_name,
    get_events_for_attendee,
    get_shared_events,
    build_attendees_context,
)
from src.data.models import MockData


# --- Fixtures ---

SAMPLE_DATA = {
    "events": [
        {
            "event_id": "evt_test_001",
            "event_name": "Test Meetup 1",
            "date": "2025-01-01",
            "location": "Istanbul",
            "platform": "Luma",
            "attendees": [
                {
                    "name": "Alice Smith",
                    "x_handle": "@alice",
                    "title": "Engineer",
                    "interests": ["AI", "startups"],
                    "bio": "Tech enthusiast",
                    "mutual_events_count": 2,
                    "connection_strength": "strong",
                },
                {
                    "name": "Bob Jones",
                    "x_handle": "@bob",
                    "title": "Designer",
                    "interests": ["design", "AI"],
                    "bio": "Creative thinker",
                    "mutual_events_count": 1,
                    "connection_strength": "weak",
                },
            ],
        },
        {
            "event_id": "evt_test_002",
            "event_name": "Test Meetup 2",
            "date": "2025-02-01",
            "location": "Ankara",
            "platform": "Luma",
            "attendees": [
                {
                    "name": "Alice Smith",
                    "x_handle": "@alice",
                    "title": "Engineer",
                    "interests": ["AI", "startups"],
                    "bio": "Tech enthusiast",
                    "mutual_events_count": 2,
                    "connection_strength": "strong",
                },
                {
                    "name": "Charlie Brown",
                    "x_handle": "@charlie",
                    "title": "Founder",
                    "interests": ["startups", "venture capital"],
                    "bio": "Serial entrepreneur",
                    "mutual_events_count": 1,
                    "connection_strength": "medium",
                },
            ],
        },
    ],
    "user_profile": {
        "name": "Test User",
        "x_handle": "@testuser",
        "interests": ["AI", "startups"],
        "bio": "Test bio",
    },
}


@pytest.fixture
def sample_json_file():
    """Create a temporary JSON file with sample data."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(SAMPLE_DATA, f)
        return Path(f.name)


@pytest.fixture
def mock_data(sample_json_file):
    """Load sample data as MockData."""
    return load_mock_data(sample_json_file)


# --- Tests ---


class TestLoadMockData:
    def test_loads_valid_json(self, sample_json_file):
        data = load_mock_data(sample_json_file)
        assert isinstance(data, MockData)
        assert len(data.events) == 2

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_mock_data(Path("/nonexistent/file.json"))

    def test_user_profile_loaded(self, mock_data):
        assert mock_data.user_profile.name == "Test User"
        assert mock_data.user_profile.x_handle == "@testuser"

    def test_event_attendees_loaded(self, mock_data):
        assert len(mock_data.events[0].attendees) == 2
        assert mock_data.events[0].attendees[0].name == "Alice Smith"


class TestGetUniqueAttendees:
    def test_deduplicates_attendees(self, mock_data):
        unique = get_unique_attendees(mock_data)
        names = [a.name for a in unique]
        assert len(names) == 3  # Alice, Bob, Charlie
        assert names.count("Alice Smith") == 1

    def test_keeps_strongest_connection(self, mock_data):
        unique = get_unique_attendees(mock_data)
        alice = next(a for a in unique if a.name == "Alice Smith")
        assert alice.connection_strength == "strong"


class TestFindAttendeeByName:
    def test_finds_exact_name(self, mock_data):
        attendees = get_unique_attendees(mock_data)
        result = find_attendee_by_name(attendees, "Alice Smith")
        assert result is not None
        assert result.x_handle == "@alice"

    def test_finds_partial_name(self, mock_data):
        attendees = get_unique_attendees(mock_data)
        result = find_attendee_by_name(attendees, "alice")
        assert result is not None

    def test_returns_none_for_unknown(self, mock_data):
        attendees = get_unique_attendees(mock_data)
        result = find_attendee_by_name(attendees, "Unknown Person")
        assert result is None


class TestGetEventsForAttendee:
    def test_finds_events(self, mock_data):
        events = get_events_for_attendee(mock_data, "@alice")
        assert len(events) == 2

    def test_single_event(self, mock_data):
        events = get_events_for_attendee(mock_data, "@bob")
        assert len(events) == 1
        assert events[0].event_name == "Test Meetup 1"


class TestGetSharedEvents:
    def test_shared_events(self, mock_data):
        shared = get_shared_events(mock_data, "@alice", "@bob")
        assert len(shared) == 1
        assert shared[0].event_id == "evt_test_001"

    def test_no_shared_events(self, mock_data):
        shared = get_shared_events(mock_data, "@bob", "@charlie")
        assert len(shared) == 0


class TestBuildAttendeesContext:
    def test_context_contains_events(self, mock_data):
        ctx = build_attendees_context(mock_data)
        assert "Test Meetup 1" in ctx
        assert "Test Meetup 2" in ctx

    def test_context_contains_attendees(self, mock_data):
        ctx = build_attendees_context(mock_data)
        assert "Alice Smith" in ctx
        assert "@alice" in ctx

    def test_context_contains_user_profile(self, mock_data):
        ctx = build_attendees_context(mock_data)
        assert "Test User" in ctx
        assert "@testuser" in ctx
