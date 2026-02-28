"""
Matchmaker Task for IntroAgent.
Defines the task for finding the best intermediary person.
"""

from crewai import Task, Agent


def create_match_task(
    agent: Agent,
    target_name: str,
    purpose: str,
    attendees_context: str,
    user_profile_summary: str,
) -> Task:
    """
    Create a task for the Matchmaker Agent to find the best intermediary.
    """
    return Task(
        description=f"""
You are analyzing event attendee data to find the BEST intermediary person
who can introduce our user to the target person.

TARGET PERSON: {target_name}
USER'S PURPOSE: {purpose}

USER PROFILE:
{user_profile_summary}

AVAILABLE ATTENDEE DATA:
{attendees_context}

YOUR TASK:
1. Identify which attendees have the strongest potential connection to
   "{target_name}" based on:
   - Number of shared events (higher = stronger connection)
   - Overlapping interests with the target
   - Professional proximity (similar industry, role level)
   - Connection strength signal (weak/medium/strong)
   - Also consider the intermediary's connection to the USER — the
     stronger the link to both parties, the better.

2. Score EACH potential intermediary from 0-100 and rank them.

3. Select the TOP intermediary and provide a detailed justification.

4. Identify specific "connection points" — shared events, interests,
   or professional overlap that can be referenced in the outreach message.

IMPORTANT: If the target person is IN the attendee list, focus on finding
someone who knows them well. If the target is NOT in the list, find someone
whose network or influence is most likely to reach the target.
""",
        expected_output="""
A structured report with:

SELECTED INTERMEDIARY:
- Name: [full name]
- X Handle: [@handle]
- Title: [their title/role]
- Bio: [their bio]
- Interests: [list of interests]

MATCH SCORE: [0-100]

COMMON GROUND:
- Shared Events: [list of events both attended]
- Shared Interests: [overlapping interests]
- Professional Proximity: [explanation]

WHY THIS PERSON:
[2-3 sentences explaining why this is the best choice]

SUGGESTED APPROACH ANGLE:
[1-2 sentences on the best way to frame the introduction request]

RUNNER-UP OPTIONS:
1. [Name] - Score: [X] - Reason: [brief]
2. [Name] - Score: [X] - Reason: [brief]
""",
        agent=agent,
    )
