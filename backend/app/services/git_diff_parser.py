import re
from typing import Any, Dict, List, Optional

def parse_git_diff_for_api_changes(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parses a raw unified git diff text and extracts likely API changes:
    - Removed or modified fields in Pydantic models (e.g. - email: str)
    - Changed routes in @app or @router decorators
    """
    detected_changes: List[Dict[str, Any]] = []
    lines = diff_text.splitlines()

    current_file = ""
    for line in lines:
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue

        # Look for removed field in Python file: -    email: str
        if line.startswith("-") and not line.startswith("---"):
            removed_content = line[1:].strip()
            # Match field annotation: field_name: type
            field_match = re.match(r'^([a-zA-Z0-9_]+)\s*:\s*([a-zA-Z0-9_\[\], ]+)', removed_content)
            if field_match and not removed_content.startswith("def ") and not removed_content.startswith("class "):
                field_name = field_match.group(1)
                detected_changes.append({
                    "change_type": "remove_field",
                    "field_name": field_name,
                    "file_path": current_file,
                    "raw_line": removed_content,
                    "confidence": "High",
                })

            # Match removed route: - @app.get("/users")
            route_match = re.search(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', removed_content)
            if route_match:
                detected_changes.append({
                    "change_type": "change_route",
                    "old_method": route_match.group(1).upper(),
                    "old_path": route_match.group(2),
                    "file_path": current_file,
                    "confidence": "High",
                })

    return detected_changes
