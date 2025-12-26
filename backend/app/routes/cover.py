import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BriefRun, Project
from app.schemas.cover_brief import CoverBriefRequest, CoverBriefResponse, CoverDirection
from app.services.openai_client import OpenAIClient

router = APIRouter(prefix="/cover", tags=["cover"])


@router.post("/brief", response_model=CoverBriefResponse)
def generate_cover_brief(payload: CoverBriefRequest, db: Session = Depends(get_db)) -> CoverBriefResponse:
    # Validate project exists
    proj = db.get(Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    client = OpenAIClient()

    prompt = f"""
You are a professional book cover art director.

Generate 6 distinct cover directions for the book below.
Return STRICT JSON only (no markdown) with this exact shape:

{{
  "directions": [
    {{
      "name": "string",
      "one_liner": "string",
      "imagery": "string",
      "typography": "string",
      "color_palette": "string",
      "layout_notes": "string",
      "avoid": "string",
      "image_prompt": "string"
    }}
  ]
}}

Book:
- Title: {payload.title}
- Subtitle: {payload.subtitle or ""}
- Author: {payload.author}
- Genre: {payload.genre}
- Subgenre: {payload.subgenre or ""}
- Blurb: {payload.blurb or ""}

Tone words: {", ".join(payload.tone_words) if payload.tone_words else ""}
Comps: {", ".join(payload.comps) if payload.comps else ""}
Constraints: {", ".join(payload.constraints) if payload.constraints else ""}

Guidelines:
- Make these market-aware for the stated genre/subgenre.
- Ensure strong thumbnail readability.
- Image prompts describe BACKGROUND ART ONLY (no text in the image).
- Each direction must feel clearly different.
""".strip()

    result = client.create_text(prompt=prompt)
    raw_text = result.get("output_text")

    if not raw_text:
        # Persist failed run
        db.add(
            BriefRun(
                project_id=payload.project_id,
                request_json=payload.model_dump(mode="json"),
                response_json={"raw_text": None},
                model=result.get("model", "unknown"),
                status="error",
                error_message="No output returned from model",
            )
        )
        db.commit()
        raise HTTPException(status_code=502, detail="No output returned from model")

    try:
        data = json.loads(raw_text)
        directions = [CoverDirection(**d) for d in data["directions"]]
    except Exception as e:
        # Persist failed run (store raw text)
        db.add(
            BriefRun(
                project_id=payload.project_id,
                request_json=payload.model_dump(mode="json"),
                response_json={"raw_text": raw_text},
                model=result.get("model", "unknown"),
                status="error",
                error_message=f"Bad JSON from model: {e}",
            )
        )
        db.commit()
        raise HTTPException(status_code=502, detail=f"Bad JSON from model: {e}")

    # Persist success
    db.add(
        BriefRun(
            project_id=payload.project_id,
            request_json=payload.model_dump(mode="json"),
            response_json=data,
            model=result.get("model", "unknown"),
            status="success",
        )
    )
    db.commit()

    return CoverBriefResponse(directions=directions, model=result["model"])
