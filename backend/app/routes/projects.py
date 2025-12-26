from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models import BriefRun, CoverImage, Project
from app.schemas.brief_runs import BriefRunOut
from app.schemas.cover_image import CoverImageListOut
from app.schemas.projects import ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectOut:
    proj = Project(
        title=payload.title,
        author=payload.author,
        genre=payload.genre,
        subgenre=payload.subgenre,
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectOut]:
    rows = db.execute(select(Project).order_by(Project.created_at.desc())).scalars().all()
    return rows


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> ProjectOut:
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.get("/{project_id}/brief-runs", response_model=list[BriefRunOut])
def list_brief_runs(project_id: UUID, db: Session = Depends(get_db)) -> list[BriefRunOut]:
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    runs = (
        db.execute(
            select(BriefRun)
            .where(BriefRun.project_id == project_id)
            .order_by(BriefRun.created_at.desc())
        )
        .scalars()
        .all()
    )
    return runs


@router.get("/{project_id}/images", response_model=list[CoverImageListOut])
def list_project_images(project_id: UUID, db: Session = Depends(get_db)) -> list[CoverImageListOut]:
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    rows = (
        db.execute(
            select(CoverImage)
            .where(CoverImage.project_id == project_id)
            .order_by(CoverImage.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [
        CoverImageListOut(
            id=row.id,
            project_id=row.project_id,
            brief_run_id=row.brief_run_id,
            direction_index=row.direction_index,
            prompt=row.prompt,
            model=row.model,
            size=row.size,
            image_url=f"/static/{row.image_path}",
            created_at=row.created_at,
        )
        for row in rows
    ]
