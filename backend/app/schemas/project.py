from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DetectedTech(BaseModel):
    backend: Optional[str] = "FastAPI"
    frontend: Optional[str] = "React/TypeScript"
    python_files: int = 0
    typescript_files: int = 0
    test_files: int = 0

class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: str
    file_count: int
    detected_tech: Dict[str, Any]
    status: str

class ScannedFileItem(BaseModel):
    relative_path: str
    file_type: str
    size_bytes: int

class ProjectDetailResponse(ProjectResponse):
    extracted_path: str
    files: List[ScannedFileItem] = Field(default_factory=list)
    endpoints_count: int = 0
    schemas_count: int = 0

class DeleteResponse(BaseModel):
    success: bool
    message: str
    project_id: str
