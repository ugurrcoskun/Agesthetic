"""
Research Task for IntroAgent.
Defines the task for analyzing the target person's profile.
"""

from crewai import Task, Agent

def create_research_task(
    agent: Agent,
    target_name: str,
    purpose: str,
    attendees_context: str,
) -> Task:
    """
    Create a research task to analyze the target person.
    """
    return Task(
        description=f"""
You are researching a target person to understand their profile and determine
the best outreach strategy.

TARGET PERSON: {target_name}
USER'S PURPOSE FOR REACHING THEM: {purpose}

AVAILABLE DATA (Event Attendees):
{attendees_context}

YOUR TASK:
1. Analyze the target person's profile from the available data.
2. Determine the BEST APPROACH STRATEGY.
3. Identify KEY TALKING POINTS.
""",
        expected_output="""
TARGET PROFILE:
- Name: [name]
- Key Interests: [list]

APPROACH STRATEGY:
- Best Angle: [1-2 sentences]

KEY TALKING POINTS:
1. [point]
2. [point]
""",
        agent=agent,
    )