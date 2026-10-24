import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.schemas.analysis import EvidenceItem

class TypeScriptParser:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def scan_frontend_files(self) -> List[Dict[str, Any]]:
        """
        Scans all TypeScript, TSX, JS, and JSX files in the project directory.
        """
        results = []
        for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
            for file_path in self.project_dir.rglob(ext):
                rel_path = file_path.relative_to(self.project_dir).as_posix()
                if "node_modules" in rel_path or "dist" in rel_path or "build" in rel_path:
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    results.append({
                        "file_path": rel_path,
                        "content": content,
                        "lines": lines,
                        "is_test": "test" in rel_path.lower() or "spec" in rel_path.lower() or "__tests__" in rel_path,
                        "is_component": ext in ["*.tsx", "*.jsx"] or "component" in rel_path.lower(),
                        "is_api": "api" in rel_path.lower() or "client" in rel_path.lower() or "service" in rel_path.lower(),
                        "is_type": "type" in rel_path.lower() or "interface" in rel_path.lower() or "model" in rel_path.lower(),
                    })
                except Exception:
                    continue
        return results

    def find_route_references(self, route_path: str, method: Optional[str] = None) -> List[EvidenceItem]:
        """
        Finds occurrences where a route path (e.g., /users or /users/{id}) is referenced
        in frontend API calls, fetch, axios, or string literals.
        """
        evidence_list: List[EvidenceItem] = []
        files = self.scan_frontend_files()

        # Generate search patterns
        # Handle parametrized routes like /users/{user_id} -> /users/
        base_path = re.sub(r'\{[^}]+\}', '', route_path).rstrip('/')
        path_segments = [seg for seg in route_path.split('/') if seg and not seg.startswith('{')]
        keyword = path_segments[-1] if path_segments else base_path.lstrip('/')

        for file_info in files:
            lines = file_info["lines"]
            for idx, line in enumerate(lines, start=1):
                matched = False
                reason = ""

                # Direct path match
                if route_path in line or (base_path and len(base_path) > 2 and base_path in line):
                    matched = True
                    reason = f"Contains direct reference to route path '{route_path}'"

                # Check template literals e.g. `/users/${id}`
                elif keyword and f"`/{keyword}" in line or f"`{base_path}" in line:
                    matched = True
                    reason = f"Matches template string literal targeting '{base_path}'"

                # Method check if provided
                if matched and method:
                    if method.lower() in line.lower():
                        reason += f" and mentions HTTP method {method}"

                if matched:
                    cat = "test" if file_info["is_test"] else ("api_client" if file_info["is_api"] else ("component" if file_info["is_component"] else "other"))
                    evidence_list.append(
                        EvidenceItem(
                            file_path=file_info["file_path"],
                            line_number=idx,
                            matched_symbol=route_path,
                            code_snippet=line.strip(),
                            reason=reason,
                            category=cat,
                        )
                    )

        return evidence_list

    def find_field_references(self, field_name: str, model_name: Optional[str] = None) -> List[EvidenceItem]:
        """
        Finds occurrences of a field name (e.g. 'email', 'user_id') in:
        1. TypeScript interface/type declarations
        2. Component member access (e.g., user.email, item.email, { email })
        3. Unit tests asserting or rendering the field
        """
        evidence_list: List[EvidenceItem] = []
        files = self.scan_frontend_files()

        # Strict regex patterns for high confidence
        interface_field_pattern = re.compile(rf'^\s*(?:readonly\s+)?{re.escape(field_name)}\s*\??\s*:', re.IGNORECASE)
        dot_access_pattern = re.compile(rf'\b[a-zA-Z0-9_$]+\.{re.escape(field_name)}\b')
        destructure_pattern = re.compile(rf'\{{[^}}]*\b{re.escape(field_name)}\b[^}}]*\}}')
        jsx_usage_pattern = re.compile(rf'<[^>]*\b{re.escape(field_name)}\b[^>]*>')
        test_assertion_pattern = re.compile(rf'(?:expect|assert|getBy|findBy|queryBy)[^;\n]*\b{re.escape(field_name)}\b', re.IGNORECASE)

        for file_info in files:
            lines = file_info["lines"]
            for idx, line in enumerate(lines, start=1):
                matched = False
                reason = ""
                cat = "other"

                if interface_field_pattern.search(line):
                    matched = True
                    reason = f"Declares property '{field_name}' in TypeScript interface/type"
                    cat = "type_definition"
                elif dot_access_pattern.search(line):
                    matched = True
                    reason = f"Accesses property '{field_name}' on object"
                    cat = "test" if file_info["is_test"] else "component"
                elif destructure_pattern.search(line):
                    matched = True
                    reason = f"Destructures property '{field_name}' from object or response payload"
                    cat = "test" if file_info["is_test"] else "component"
                elif file_info["is_test"] and test_assertion_pattern.search(line):
                    matched = True
                    reason = f"Asserts or queries on property '{field_name}' in test"
                    cat = "test"
                elif file_info["is_component"] and field_name in line and ("{" in line or "<" in line):
                    # JSX rendering context e.g. <div>{user.name}</div> or <UserCard email={...} />
                    matched = True
                    reason = f"Renders or passes '{field_name}' in UI component"
                    cat = "component"

                if matched:
                    evidence_list.append(
                        EvidenceItem(
                            file_path=file_info["file_path"],
                            line_number=idx,
                            matched_symbol=field_name,
                            code_snippet=line.strip(),
                            reason=reason,
                            category=cat,
                        )
                    )

        return evidence_list
