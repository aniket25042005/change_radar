from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from app.database import get_project_by_id, get_reports_by_project

router = APIRouter(prefix="/api/projects/{project_id}/reports", tags=["reports"])

@router.get("", response_model=List[Dict[str, Any]])
def list_reports(project_id: str):
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return get_reports_by_project(project_id)
