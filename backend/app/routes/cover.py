import json
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Project, BriefRun, CoverImage
from app.schemas.cover_brief import CoverBriefRequest, CoverBriefResponse, CoverDirection
from app.schemas.cover_image import CoverImageGenerateRequest, CoverImageGenerateResponse, CoverImageOut
from app.services.openai_client import OpenAIClient
from app.settings import get_settings

router = APIRouter(prefix="/cover", tags=["cover"])


def _use_real_openai_from_request(request: Request, settings) -> bool:
    """
    Priority:
      1) Request header X-Use-Real-OpenAI (from Streamlit toggle)
      2) settings.use_real_openai (env default)
    """
    header_val = (request.headers.get("X-Use-Real-OpenAI") or "").strip().lower()
    if header_val in {"1", "true", "yes", "on"}:
        return True
    if header_val in {"0", "false", "no", "off"}:
        return False
    return bool(getattr(settings, "use_real_openai", False))


@router.post("/brief", response_model=CoverBriefResponse)
def generate_cover_brief(
    payload: CoverBriefRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CoverBriefResponse:
    settings = get_settings()
    use_real = _use_real_openai_from_request(request, settings)

    # Validate project exists
    proj = db.get(Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # ---------------------------------------------------------------------
    # STUB MODE (DEV): Return deterministic directions without calling OpenAI
    # Placement: after project validation, before creating OpenAIClient/prompt
    # ---------------------------------------------------------------------
    if not use_real:
        stub_data = {
            "directions": [
                {
                    "name": "Midnight Rain",
                    "one_liner": "A moody, cinematic cover built on rain, neon reflections, and quiet intensity.",
                    "imagery": "Rain-soaked London street at night, neon signs reflected in puddles, distant silhouettes, soft fog.",
                    "typography": "Elegant serif for title; clean small caps sans for author; strong thumbnail contrast.",
                    "color_palette": "Charcoal, deep navy, wet asphalt gray, restrained neon teal/amber accents.",
                    "layout_notes": "Large negative space for title; keep focal light source behind upper third.",
                    "avoid": "Literal faces, bright daytime scenes, cluttered signage.",
                    "image_prompt": "Moody rainy city street at night, neon reflections in puddles, cinematic lighting, soft fog, shallow depth of field, high contrast, film grain, romantic noir atmosphere, background only, no text",
                },
                {
                    "name": "Backstage Shadows",
                    "one_liner": "Intimate romance suggested through backstage light and shadow, not literal characters.",
                    "imagery": "Dim corridor, stage door glow, light spill across concrete, haze and bokeh from stage lights.",
                    "typography": "Bold condensed title with subtle texture; author in modern sans.",
                    "color_palette": "Black, smoke gray, warm tungsten gold, muted crimson accent.",
                    "layout_notes": "Title stacked big; keep a strong vertical light beam for structure.",
                    "avoid": "Band photos, instruments front-and-center, cheesy spotlights.",
                    "image_prompt": "Dark backstage corridor with warm stage light spilling through a door, haze, bokeh stage lights, dramatic shadows, cinematic composition, high contrast, subtle grain, intimate mood, background only, no text",
                },
            ]
        }

        directions = [CoverDirection(**d) for d in stub_data["directions"]]

        # Persist success (stub run) so your history UI still works
        db.add(
            BriefRun(
                project_id=payload.project_id,
                request_json=payload.model_dump(mode="json"),
                response_json=stub_data,
                model="stub",
                status="success",
            )
        )
        db.commit()

        return CoverBriefResponse(directions=directions, model="stub")
    # ---------------------------------------------------------------------
    # END STUB MODE
    # ---------------------------------------------------------------------

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
def generate_cover_images(
    payload: CoverImageGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CoverImageGenerateResponse:
    settings = get_settings()
    use_real = _use_real_openai_from_request(request, settings)

    proj = db.get(Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.brief_run_id:
        run = db.get(BriefRun, payload.brief_run_id)
        if not run or run.project_id != payload.project_id:
            raise HTTPException(status_code=400, detail="brief_run_id is invalid for this project")

    model = payload.model or settings.image_model
    size = payload.size or settings.image_size

    # ---------------------------------------------------------------------
    # STUB MODE (DEV): create placeholder PNG bytes with Pillow (no OpenAI)
    # Placement: before creating OpenAIClient / calling generate_images
    # ---------------------------------------------------------------------
    if not use_real:
        try:
            import io
            from PIL import Image, ImageDraw

            w_str, h_str = size.split("x")
            w, h = int(w_str), int(h_str)

            images_bytes: list[bytes] = []
            for i in range(payload.n):
                img = Image.new("RGB", (w, h), color=(28, 28, 32))
                draw = ImageDraw.Draw(img)

                # simple diagonal accent
                draw.rectangle([0, int(h * 0.65), w, h], fill=(18, 18, 22))
                draw.line((0, 0, w, h), fill=(70, 70, 80), width=3)

                # small label (purely for dev visibility; remove later)
                label = f"STUB {i+1}/{payload.n}"
                draw.text((24, 24), label, fill=(200, 200, 210))

                buf = io.BytesIO()
                img.save(buf, format="PNG")
                images_bytes.append(buf.getvalue())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stub image generation failed: {e}")
    else:
        client = OpenAIClient()
        try:
            images_bytes = client.generate_images(prompt=payload.prompt, n=payload.n, model=model, size=size)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Image generation failed: {e}")
    # ---------------------------------------------------------------------
    # END STUB MODE
    # ---------------------------------------------------------------------

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
            model=model if use_real else "stub-image",
            size=size,
            image_path=rel_path,
        )
        db.add(row)
        db.flush()

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
