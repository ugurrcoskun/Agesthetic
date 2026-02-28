"""
Tests for the Matchmaker agent module.
Uses unittest.mock to patch CrewAI's LLM creation since it validates
credentials at Agent creation time in CrewAI 1.9+.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.matchmaker import create_matchmaker_agent
from src.tasks.match_task import create_match_task


@pytest.fixture(autouse=True)
def mock_llm_creation():
    """Patch LLM creation to avoid API key validation during tests."""
    with patch("crewai.utilities.llm_utils.create_llm") as mock_create:
        mock_llm_instance = MagicMock()
        mock_llm_instance.model = "test-model"
        mock_create.return_value = mock_llm_instance
        yield mock_create


class TestMatchmakerAgent:
    def test_agent_creation(self):
        agent = create_matchmaker_agent("test/model")
        assert agent is not None
        assert "Matchmaker" in agent.role
        assert agent.allow_delegation is False

    def test_agent_has_goal(self):
        agent = create_matchmaker_agent("test/model")
        assert "intermediary" in agent.goal.lower()
        assert "target" in agent.goal.lower()

    def test_agent_has_backstory(self):
        agent = create_matchmaker_agent("test/model")
        assert len(agent.backstory) > 50


class TestMatchTask:
    def test_task_creation(self):
        agent = create_matchmaker_agent("test/model")
        task = create_match_task(
            agent=agent,
            target_name="Elon Musk",
            purpose="Discuss AI project",
            attendees_context="Test attendees data",
            user_profile_summary="Test user profile",
        )
        assert task is not None
        assert "Elon Musk" in task.description

    def test_task_contains_target_name(self):
        agent = create_matchmaker_agent("test/model")
        task = create_match_task(
            agent=agent,
            target_name="Jane Doe",
            purpose="Networking",
            attendees_context="",
            user_profile_summary="",
        )
        assert "Jane Doe" in task.description

    def test_task_has_expected_output(self):
        agent = create_matchmaker_agent("test/model")
        task = create_match_task(
            agent=agent,
            target_name="Test Person",
            purpose="Test",
            attendees_context="",
            user_profile_summary="",
        )
        assert "MATCH SCORE" in task.expected_output
        assert "SELECTED INTERMEDIARY" in task.expected_output
