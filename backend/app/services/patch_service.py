import difflib
import re
from pathlib import Path
from typing import Dict, List, Optional
from app.schemas.analysis import EvidenceItem

def generate_migration_patch(
    project_dir: Path,
    change_type: str,
    field_name: Optional[str] = None,
    new_field_name: Optional[str] = None,
    new_field_type: Optional[str] = None,
    old_path: Optional[str] = None,
    new_path: Optional[str] = None,
    affected_files: Optional[List[EvidenceItem]] = None,
) -> Optional[str]:
    """
    Generates a unified git-compatible patch for suggested frontend migrations:
    - remove_field: removes field from TypeScript interface declarations and marks usages
    - rename_field: renames deprecated property accessors across frontend files
    - change_field_type: updates TypeScript interface property annotations
    - change_route: updates API client endpoint path strings
    """
    if not affected_files:
        return None

    # Group affected files by file_path
    files_to_modify: Dict[str, List[EvidenceItem]] = {}
    for item in affected_files:
        if item.category in ["component", "type_definition", "api_client", "test"]:
            files_to_modify.setdefault(item.file_path, []).append(item)

    if not files_to_modify:
        return None

    patch_chunks: List[str] = []

    for rel_path, items in files_to_modify.items():
        disk_path = project_dir / rel_path
        if not disk_path.exists():
            continue

        try:
            original_content = disk_path.read_text(encoding="utf-8", errors="ignore")
            lines = original_content.splitlines(keepends=True)
            modified_lines = list(lines)

            # 1. RENAME FIELD
            if change_type == "rename_field" and field_name and new_field_name:
                pattern = re.compile(rf'\b{re.escape(field_name)}\b')
                for i, line in enumerate(modified_lines):
                    if pattern.search(line):
                        modified_lines[i] = pattern.sub(new_field_name, line)

            # 2. REMOVE FIELD
            elif change_type == "remove_field" and field_name:
                # In TypeScript interfaces/types: remove the property line
                if "type" in rel_path.lower() or "interface" in rel_path.lower() or "model" in rel_path.lower():
                    interface_prop_pattern = re.compile(rf'^\s*(?:readonly\s+)?{re.escape(field_name)}\s*\??\s*:', re.IGNORECASE)
                    modified_lines = [
                        line for line in modified_lines if not interface_prop_pattern.search(line)
                    ]
                else:
                    # In components/tests: comment out the removed field usage with deprecation note
                    dot_pattern = re.compile(rf'\b([a-zA-Z0-9_$]+)\.{re.escape(field_name)}\b')
                    for i, line in enumerate(modified_lines):
                        if dot_pattern.search(line):
                            modified_lines[i] = dot_pattern.sub(rf'/* REMOVED: \1.{field_name} */ undefined', line)

            # 3. CHANGE FIELD TYPE
            elif change_type == "change_field_type" and field_name and new_field_type:
                type_prop_pattern = re.compile(rf'(^\s*(?:readonly\s+)?{re.escape(field_name)}\s*\??\s*:\s*)([^;,\n]+)(.*)$')
                for i, line in enumerate(modified_lines):
                    if type_prop_pattern.search(line):
                        modified_lines[i] = type_prop_pattern.sub(rf'\g<1>{new_field_type}\g<3>', line)

            # 4. CHANGE ROUTE
            elif change_type == "change_route" and old_path and new_path:
                for i, line in enumerate(modified_lines):
                    if old_path in line:
                        modified_lines[i] = line.replace(old_path, new_path)

            if modified_lines != lines:
                diff = difflib.unified_diff(
                    lines,
                    modified_lines,
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                    lineterm="",
                )
                diff_text = "\n".join(diff)
                if diff_text:
                    patch_chunks.append(diff_text)
        except Exception:
            continue

    if not patch_chunks:
        return None

    return "\n\n".join(patch_chunks)
