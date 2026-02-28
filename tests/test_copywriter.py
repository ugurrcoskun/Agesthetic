"""
Tests for the Copywriter agent module.
Uses unittest.mock to patch CrewAI's LLM creation since it validates
credentials at Agent creation time in CrewAI 1.9+.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.copywriter import create_copywriter_agent
from src.tasks.draft_task import create_draft_task


@pytest.fixture(autouse=True)
def mock_llm_creation():
    """Patch LLM creation to avoid API key validation during tests."""
    with patch("crewai.utilities.llm_utils.create_llm") as mock_create:
        mock_llm_instance = MagicMock()
        mock_llm_instance.model = "test-model"
        mock_create.return_value = mock_llm_instance
        yield mock_create


class TestCopywriterAgent:
    def test_agent_creation(self):
        agent = create_copywriter_agent("test/model")
        assert agent is not None
        assert "Copywriter" in agent.role
        assert agent.allow_delegation is False

    def test_agent_has_goal(self):
        agent = create_copywriter_agent("test/model")
        assert "dm" in agent.goal.lower() or "message" in agent.goal.lower()

    def test_agent_has_backstory(self):
        agent = create_copywriter_agent("test/model")
        assert len(agent.backstory) > 50
        assert "authentic" in agent.backstory.lower() or "personal" in agent.backstory.lower()


class TestDraftTask:
    def test_task_creation(self):
        agent = create_copywriter_agent("test/model")
        task = create_draft_task(
            agent=agent,
            target_name="Elon Musk",
            purpose="Discuss AI project",
            user_name="Ali Veli",
        )
        assert task is not None

    def test_task_contains_target(self):
        agent = create_copywriter_agent("test/model")
        task = create_draft_task(
            agent=agent,
            target_name="Jane Doe",
            purpose="Networking",
            user_name="Test User",
        )
        assert "Jane Doe" in task.description

    def test_task_has_writing_rules(self):
        agent = create_copywriter_agent("test/model")
        task = create_draft_task(
            agent=agent,
            target_name="Test",
            purpose="Test",
            user_name="Test",
        )
        assert "spam" in task.description.lower() or "bot" in task.description.lower()

    def test_task_expects_alternatives(self):
        agent = create_copywriter_agent("test/model")
        task = create_draft_task(
            agent=agent,
            target_name="Test",
            purpose="Test",
            user_name="Test",
        )
        assert "ALTERNATIVE" in task.expected_output
