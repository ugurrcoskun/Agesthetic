"""
Draft Task for IntroAgent.
Defines the task for writing a personalized DM draft.
"""

from typing import List
from pydantic import BaseModel, Field
from crewai import Task, Agent

class DMDraft(BaseModel):
    label: str = Field(description="Label for this DM, e.g. Primary (Warm & Genuine), Professional, Casual")
    text: str = Field(description="The DM message itself, ready to send")

class DMDraftsOutput(BaseModel):
    dms: List[DMDraft] = Field(description="A list of distinct DM drafts.")
    personalization_points: List[str] = Field(description="List of strings explaining what personalization points were used.")
    recipient: str = Field(description="Name and handle of the intermediary recipient.")

def create_draft_task(
    agent: Agent,
    target_name: str,
    purpose: str,
    user_name: str,
) -> Task:
    """
    Create a task for the Copywriter Agent to write a DM draft.
    Uses the Matchmaker's output (passed via context) to personalize the message.
    """
    return Task(
        description=f"""
Using the Matchmaker's report about the selected intermediary, write a
warm, genuine X (Twitter) DM that asks the intermediary to introduce
our user to the target person.

TARGET PERSON: {target_name}
USER'S NAME: {user_name}
USER'S PURPOSE: {purpose}

WRITING RULES:
1. ❌ Do NOT make it sound like a bot or template wrote it
2. ❌ Do NOT use corporate buzzwords ("synergy", "leverage", "loop in")
3. ❌ Do NOT be overly formal or stiff
4. ❌ Do NOT write a wall of text — keep it SHORT
5. ✅ DO reference a SPECIFIC shared experience (event name, interest)
6. ✅ DO be respectful of the intermediary's time
7. ✅ DO include a clear but soft ask
8. ✅ DO match a conversational, friendly tone
9. ✅ DO keep the main message under 280 characters if possible
10. ✅ DO write in the language most natural for the context (Turkish
    if attendees are Turkish, English otherwise)

STRUCTURE GUIDE:
- Line 1: Warm greeting + specific reference (event, shared interest)
- Line 2: Brief context on why you're reaching out
- Line 3: The ask — clear but non-pushy
- Line 4: Gratitude / closing

EXAMPLE TONE (do NOT copy this verbatim, use it as inspiration):
"Hey [Name]! AI Builders meetup'ta tanışmıştık,
agent projeniz çok ilham vericiydi. [Target] ile bir AI
projemiz hakkında konuşmayı çok isterdim —
tanıştırma şansınız olur mu? 🙏"
""",
        expected_output="""
Provide 3 distinct versions of the DM message:
1. Primary (Warm, genuine, conversational)
2. Professional (Slightly more formal, respectful)
3. Casual (Relaxed and concise)

Ensure the output exactly matches the requested JSON structure.
""",
        output_json=DMDraftsOutput,
        agent=agent,
    )
