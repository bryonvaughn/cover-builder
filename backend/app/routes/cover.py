import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Project, BriefRun, CoverImage
from app.schemas.cover_brief import CoverBriefRequest, CoverBriefResponse, CoverDirection
from app.services.openai_client import OpenAIClient
from app.schemas.cover_image import CoverImageGenerateRequest, CoverImageGenerateResponse, CoverImageOut

from uuid import uuid4
from app.settings import get_settings

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

@router.post("/image", response_model=CoverImageGenerateResponse)
def generate_cover_images(payload: CoverImageGenerateRequest, db: Session = Depends(get_db)) -> CoverImageGenerateResponse:
    settings = get_settings()

    proj = db.get(Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.brief_run_id:
        run = db.get(BriefRun, payload.brief_run_id)
        if not run or run.project_id != payload.project_id:
            raise HTTPException(status_code=400, detail="brief_run_id is invalid for this project")

    model = payload.model or settings.image_model
    size = payload.size or settings.image_size

    client = OpenAIClient()

    # Generate bytes
    try:
        images_bytes = client.generate_images(prompt=payload.prompt, n=payload.n, model=model, size=size)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {e}")

    # Save files + DB rows
    storage_root = Path(settings.storage_dir)
    rel_dir = Path("images") / str(payload.project_id)
    abs_dir = storage_root / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    out: list[CoverImageOut] = []

    for img_bytes in images_bytes:
        image_id = uuid4()
        filename = f"{image_id}.png"
        rel_path = str(rel_dir / filename)  # stored in DB
        abs_path = abs_dir / filename

        abs_path.write_bytes(img_bytes)

        row = CoverImage(
            id=image_id,
            project_id=payload.project_id,
            brief_run_id=payload.brief_run_id,
            direction_index=payload.direction_index,
            prompt=payload.prompt,
            model=model,
            size=size,
            image_path=rel_path,
        )
        db.add(row)
        db.flush()  # get ids without committing each time

        out.append(
            CoverImageOut(
                id=row.id,
                project_id=row.project_id,
                brief_run_id=row.brief_run_id,
                direction_index=row.direction_index,
                prompt=row.prompt,
                model=row.model,
                size=row.size,
                image_url=f"/static/{row.image_path}",
            )
        )

    db.commit()

    return CoverImageGenerateResponse(images=out)
