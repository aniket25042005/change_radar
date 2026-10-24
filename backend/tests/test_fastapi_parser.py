import tempfile
from pathlib import Path
from app.services.fastapi_parser import parse_python_file

SAMPLE_FASTAPI_CODE = """
from typing import List, Optional
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str = "user"
    bio: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    email: str

router = APIRouter(prefix="/users")

@router.get("", response_model=List[UserResponse])
def get_users():
    return []

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    return None

@router.post("", response_model=UserResponse)
def create_user(payload: UserCreate):
    return None
"""

def test_fastapi_and_pydantic_parsing():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(SAMPLE_FASTAPI_CODE)
        f_path = Path(f.name)

    try:
        endpoints, schemas = parse_python_file(f_path, "routes/users.py")

        # Verify endpoints
        assert len(endpoints) == 3
        paths = {ep.path for ep in endpoints}
        assert "/users" in paths
        assert "/users/{user_id}" in paths

        methods = {ep.method for ep in endpoints}
        assert "GET" in methods
        assert "POST" in methods

        # Verify response models
        response_models = [ep.response_model for ep in endpoints if ep.response_model]
        assert any("UserResponse" in rm for rm in response_models)

        # Verify Pydantic schemas
        assert len(schemas) == 2
        user_resp = next(s for s in schemas if s.name == "UserResponse")
        field_names = [f.name for f in user_resp.fields]
        assert "id" in field_names
        assert "name" in field_names
        assert "email" in field_names
        assert "role" in field_names
        assert "bio" in field_names

        email_field = next(f for f in user_resp.fields if f.name == "email")
        assert email_field.type_annotation == "str"
        assert email_field.required is True

        bio_field = next(f for f in user_resp.fields if f.name == "bio")
        assert bio_field.required is False

    finally:
        f_path.unlink(missing_ok=True)
