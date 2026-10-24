import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.schemas.analysis import (
    EndpointInfo,
    PydanticFieldInfo,
    PydanticSchemaInfo,
)

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

def clean_type_annotation(node: Optional[ast.AST]) -> str:
    if node is None:
        return "Any"
    try:
        return ast.unparse(node)
    except Exception:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{clean_type_annotation(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{clean_type_annotation(node.value)}[{clean_type_annotation(node.slice)}]"
        return "Unknown"

class FastAPIFileVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.endpoints: List[EndpointInfo] = []
        self.schemas: List[PydanticSchemaInfo] = []
        self.router_prefixes: Dict[str, str] = {}
        self.current_router_prefix: Optional[str] = None

    def visit_Assign(self, node: ast.Assign):
        # Detect: router = APIRouter(prefix="/users")
        if isinstance(node.value, ast.Call):
            call = node.value
            func_name = ""
            if isinstance(call.func, ast.Name):
                func_name = call.func.id
            elif isinstance(call.func, ast.Attribute):
                func_name = call.func.attr

            if func_name == "APIRouter":
                prefix = ""
                for kw in call.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                        prefix = str(kw.value.value).rstrip("/")
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.router_prefixes[target.id] = prefix
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Detect Pydantic Model classes (BaseModel)
        is_pydantic = False
        for base in node.bases:
            base_str = clean_type_annotation(base)
            if "BaseModel" in base_str or "Schema" in base_str:
                is_pydantic = True
                break

        # Also heuristically treat classes with typed field annotations as potential schemas if named *Response, *Request, *Schema, *DTO
        if not is_pydantic:
            name_lower = node.name.lower()
            if any(term in name_lower for term in ["response", "request", "schema", "dto", "model", "item", "user"]):
                is_pydantic = True

        if is_pydantic:
            fields: List[PydanticFieldInfo] = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    type_str = clean_type_annotation(item.annotation)
                    has_default = item.value is not None
                    is_required = not has_default and "Optional" not in type_str
                    fields.append(
                        PydanticFieldInfo(
                            name=field_name,
                            type_annotation=type_str,
                            line_number=item.lineno,
                            required=is_required,
                        )
                    )
            self.schemas.append(
                PydanticSchemaInfo(
                    name=node.name,
                    file_path=self.rel_path,
                    line_number=node.lineno,
                    fields=fields,
                )
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_route_decorator(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_route_decorator(node)
        self.generic_visit(node)

    def _check_route_decorator(self, node: ast.AST):
        if not hasattr(node, "decorator_list"):
            return

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            call = decorator
            obj_name = ""
            method_name = ""

            if isinstance(call.func, ast.Attribute):
                method_name = call.func.attr.lower()
                if isinstance(call.func.value, ast.Name):
                    obj_name = call.func.value.id

            if method_name in HTTP_METHODS and (obj_name in self.router_prefixes or obj_name in ["app", "router", "api", "api_router"]):
                # Extract path
                route_path = "/"
                if call.args and isinstance(call.args[0], ast.Constant):
                    route_path = str(call.args[0].value)

                # Check keyword path if not in positional args
                for kw in call.keywords:
                    if kw.arg == "path" and isinstance(kw.value, ast.Constant):
                        route_path = str(kw.value.value)

                # Prefix resolution
                prefix = self.router_prefixes.get(obj_name, "")
                if prefix:
                    full_path = f"{prefix}/{route_path.lstrip('/')}".rstrip("/")
                    if not full_path:
                        full_path = "/"
                else:
                    full_path = route_path

                # Extract response_model
                response_model = None
                for kw in call.keywords:
                    if kw.arg == "response_model":
                        response_model = clean_type_annotation(kw.value)

                # If no response_model in decorator, check return type annotation
                if not response_model and hasattr(node, "returns") and node.returns:
                    ret_str = clean_type_annotation(node.returns)
                    if ret_str and ret_str != "None":
                        response_model = ret_str

                # Extract parameters
                params = []
                request_model = None
                for arg in node.args.args:
                    if arg.arg in ["self", "cls"]:
                        continue
                    param_type = clean_type_annotation(arg.annotation) if arg.annotation else "Any"
                    params.append({"name": arg.arg, "type": param_type})
                    # Heuristic for request body model
                    if any(t in param_type.lower() for t in ["create", "update", "request", "payload", "input", "body", "schema"]):
                        request_model = param_type

                endpoint_id = f"{method_name.upper()} {full_path}"
                self.endpoints.append(
                    EndpointInfo(
                        id=endpoint_id,
                        method=method_name.upper(),
                        path=full_path,
                        function_name=node.name,
                        file_path=self.rel_path,
                        line_number=node.lineno,
                        response_model=response_model,
                        request_model=request_model,
                        parameters=params,
                        router_prefix=prefix if prefix else None,
                    )
                )

def parse_python_file(file_path: Path, rel_path: str) -> Tuple[List[EndpointInfo], List[PydanticSchemaInfo]]:
    """
    Parses a single python file using AST, returning discovered endpoints and schemas.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
        visitor = FastAPIFileVisitor(rel_path)
        visitor.visit(tree)
        return visitor.endpoints, visitor.schemas
    except Exception:
        # Fallback to regex parser for broken/unparseable files
        return _regex_fallback_parse(file_path, rel_path)

def _regex_fallback_parse(file_path: Path, rel_path: str) -> Tuple[List[EndpointInfo], List[PydanticSchemaInfo]]:
    endpoints: List[EndpointInfo] = []
    schemas: List[PydanticSchemaInfo] = []
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines, start=1):
            # Match @app.get("/...") or @router.post("/...")
            route_match = re.search(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line, re.IGNORECASE)
            if route_match:
                method = route_match.group(1).upper()
                path = route_match.group(2)
                endpoints.append(
                    EndpointInfo(
                        id=f"{method} {path}",
                        method=method,
                        path=path,
                        function_name="unknown",
                        file_path=rel_path,
                        line_number=idx,
                    )
                )

            # Match class Model(BaseModel):
            class_match = re.search(r'class\s+([A-Za-z0-9_]+)\s*\(\s*(?:BaseModel|.*Schema.*)\s*\):', line)
            if class_match:
                schemas.append(
                    PydanticSchemaInfo(
                        name=class_match.group(1),
                        file_path=rel_path,
                        line_number=idx,
                        fields=[],
                    )
                )
    except Exception:
        pass
    return endpoints, schemas

def parse_all_python_files(project_dir: Path) -> Tuple[List[EndpointInfo], List[PydanticSchemaInfo]]:
    all_endpoints: List[EndpointInfo] = []
    all_schemas: List[PydanticSchemaInfo] = []

    for file_path in project_dir.rglob("*.py"):
        rel_path = file_path.relative_to(project_dir).as_posix()
        if "test" in rel_path.lower() or ".venv" in rel_path or "__pycache__" in rel_path:
            continue
        endpoints, schemas = parse_python_file(file_path, rel_path)
        all_endpoints.extend(endpoints)
        all_schemas.extend(schemas)

    return all_endpoints, all_schemas
