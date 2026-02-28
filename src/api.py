"""
IntroAgent Web API.
FastAPI backend that runs the 3-agent pipeline and streams progress via SSE.
"""

import json
import time
import asyncio
import threading
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_llm_string
from src.data.loader import load_mock_data, build_attendees_context, get_unique_attendees
from src.agents.researcher import create_researcher_agent
from src.agents.matchmaker import create_matchmaker_agent
from src.agents.copywriter import create_copywriter_agent
from src.tasks.research_task import create_research_task
from src.tasks.match_task import create_match_task
from src.tasks.draft_task import create_draft_task

from crewai import Crew, Process


app = FastAPI(title="IntroAgent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/attendees")
async def get_attendees():
    """Return all unique attendees from mock data."""
    data = load_mock_data()
    attendees = get_unique_attendees(data)
    return [
        {
            "name": a.name,
            "x_handle": a.x_handle,
            "title": a.title or "",
            "interests": a.interests,
            "bio": a.bio,
            "connection_strength": a.connection_strength,
        }
        for a in attendees
    ]


@app.get("/api/events")
async def get_events():
    """Return all events from mock data."""
    data = load_mock_data()
    return [
        {
            "event_id": e.event_id,
            "event_name": e.event_name,
            "date": e.date,
            "location": e.location,
            "attendee_count": len(e.attendees),
        }
        for e in data.events
    ]


@app.post("/api/person")
async def add_person(request: Request):
    """Add a new person to the first event's attendee list."""
    body = await request.json()
    data_path = Path(__file__).parent.parent / "data" / "luma_attendees_mock.json"
    with open(data_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    new_person = {
        "name": body.get("name", ""),
        "x_handle": body.get("x_handle", ""),
        "title": body.get("title", ""),
        "interests": body.get("interests", []),
        "bio": body.get("bio", ""),
        "mutual_events_count": 1,
        "connection_strength": "weak",
    }

    # Add to all events
    for event in raw["events"]:
        # Check if already exists
        existing = [a for a in event["attendees"] if a["name"] == new_person["name"]]
        if not existing:
            event["attendees"].append(new_person)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=4)

    return {"status": "ok", "person": new_person}


@app.post("/api/profile")
async def update_profile(request: Request):
    """Update the user profile."""
    body = await request.json()
    data_path = Path(__file__).parent.parent / "data" / "luma_attendees_mock.json"
    with open(data_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    raw["user_profile"] = {
        "name": body.get("name", raw["user_profile"]["name"]),
        "x_handle": body.get("x_handle", raw["user_profile"]["x_handle"]),
        "interests": body.get("interests", raw["user_profile"]["interests"]),
        "bio": body.get("bio", raw["user_profile"]["bio"]),
    }

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=4)

    return {"status": "ok", "profile": raw["user_profile"]}


@app.get("/api/profile")
async def get_profile():
    """Return user profile."""
    data = load_mock_data()
    p = data.user_profile
    return {"name": p.name, "x_handle": p.x_handle, "interests": p.interests, "bio": p.bio}




@app.get("/api/run")
async def run_agents(target_name: str, purpose: str):
    """
    Run the 3-agent pipeline and stream progress via SSE.
    Each agent's completion sends an event to the frontend.
    """

    async def event_stream():
        try:
            # Load data
            data = load_mock_data()
            attendees_context = build_attendees_context(data)
            user_profile = data.user_profile
            user_profile_summary = (
                f"Name: {user_profile.name}\n"
                f"Handle: {user_profile.x_handle}\n"
                f"Interests: {', '.join(user_profile.interests)}\n"
                f"Bio: {user_profile.bio}"
            )

            llm_string = get_llm_string()

            # --- Agent 1: Researcher ---
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'researcher', 'message': 'Hedef kişi profili analiz ediliyor...'})}\n\n"

            researcher = create_researcher_agent(llm_string)
            research_task = create_research_task(
                agent=researcher,
                target_name=target_name,
                purpose=purpose,
                attendees_context=attendees_context,
            )

            crew1 = Crew(
                agents=[researcher],
                tasks=[research_task],
                process=Process.sequential,
                verbose=False,
            )

            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, crew1.kickoff)

            research_output = research_task.output.raw if research_task.output else "No output"

            yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'researcher', 'result': research_output})}\n\n"

            # --- Agent 2: Matchmaker ---
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'matchmaker', 'message': 'En iyi aracı kişi aranıyor...'})}\n\n"

            matchmaker = create_matchmaker_agent(llm_string)
            match_task = create_match_task(
                agent=matchmaker,
                target_name=target_name,
                purpose=purpose,
                attendees_context=attendees_context,
                user_profile_summary=user_profile_summary,
            )
            match_task.context = [research_task]

            crew2 = Crew(
                agents=[matchmaker],
                tasks=[match_task],
                process=Process.sequential,
                verbose=False,
            )

            await loop.run_in_executor(None, crew2.kickoff)

            match_output = match_task.output.raw if match_task.output else "No output"

            yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'matchmaker', 'result': match_output})}\n\n"

            # --- Agent 3: Copywriter ---
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'copywriter', 'message': 'Kişiselleştirilmiş DM yazılıyor...'})}\n\n"

            copywriter = create_copywriter_agent(llm_string)
            draft_task = create_draft_task(
                agent=copywriter,
                target_name=target_name,
                purpose=purpose,
                user_name=user_profile.name,
            )
            draft_task.context = [research_task, match_task]

            crew3 = Crew(
                agents=[copywriter],
                tasks=[draft_task],
                process=Process.sequential,
                verbose=False,
            )

            await loop.run_in_executor(None, crew3.kickoff)

            draft_output = draft_task.output.raw if draft_task.output else "No output"

            yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'copywriter', 'result': draft_output})}\n\n"

            # --- Complete ---
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Tüm agentlar tamamlandı!'})}\n\n"

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                # Yield a soft warning instead of full blown crash
                yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'researcher', 'message': '[API LIMIT REACHED] Mock Mode Enabled'})}\n\n"
                
                # Mock Researcher
                yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'researcher', 'result': '- API quota exhausted. Continuing with mock context.'})}\n\n"
                
                # Mock Matchmaker
                yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'matchmaker', 'message': '[MOCK] En iyi aracı kişi aranıyor...'})}\n\n"
                time.sleep(1)
                yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'matchmaker', 'result': f'Selected Intermediary: {target_name}. Strong simulated connection.'})}\n\n"
                
                # Mock Copywriter
                yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'copywriter', 'message': '[MOCK] Kişiselleştirilmiş DM yazılıyor...'})}\n\n"
                time.sleep(1)
                
                fallback_dms = {
                    "dms": [
                        {"label": "Primary (Warm & Genuine)", "text": f"Hey, would love to connect with {target_name} regarding {purpose}!"},
                        {"label": "Professional", "text": f"Dear {target_name}, reaching out to discuss {purpose}."},
                        {"label": "Casual", "text": f"Yo {target_name}! Let's chat about {purpose}."}
                    ],
                    "personalization_points": ["Mock data loaded due to API limit"],
                    "recipient": target_name
                }
                yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'copywriter', 'result': json.dumps(fallback_dms)})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'message': 'Pipeline completed via API fallback.'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': error_str})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Serve frontend
WEB_DIR = Path(__file__).parent.parent / "web"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>IntroAgent Web UI</h1><p>web/index.html not found</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
