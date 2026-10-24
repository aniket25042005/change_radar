import os
import re
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple
from fastapi import HTTPException

def apply_patch_to_workspace(project_dir: Path, patch_text: str) -> Tuple[str, List[str]]:
    """
    Safely applies a unified diff patch to files in project_dir after creating a backup.
    Returns (backup_id, modified_files).
    """
    if not patch_text.strip():
        raise HTTPException(status_code=400, detail="Patch content is empty")

    backup_id = f"bak_{uuid.uuid4().hex[:8]}"
    backup_dir = project_dir / ".backups" / backup_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Split patch by file diff blocks (e.g. --- a/... +++ b/...)
    diff_blocks = re.split(r'(?=^--- [ab]/)', patch_text, flags=re.MULTILINE)
    modified_files: List[str] = []

    for block in diff_blocks:
        if not block.strip():
            continue

        match = re.search(r'^\+\+\+ [ab]/(.+)$', block, flags=re.MULTILINE)
        if not match:
            continue

        rel_path = match.group(1).strip()
        target_file = (project_dir / rel_path).resolve()

        # Path traversal security check
        try:
            common = os.path.commonpath([str(target_file), str(project_dir.resolve())])
            if common != str(project_dir.resolve()):
                raise HTTPException(status_code=400, detail=f"Target file escapes workspace: {rel_path}")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid cross-drive target file: {rel_path}")

        if not target_file.exists():
            continue

        # Backup original file
        backup_file = backup_dir / rel_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_file, backup_file)

        # Apply simple unified diff changes
        original_lines = target_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        modified_lines = list(original_lines)

        # Parse removed lines and added lines
        lines_in_block = block.splitlines()
        for i, line in enumerate(lines_in_block):
            if line.startswith("-") and not line.startswith("---"):
                old_text = line[1:].strip()
                # Find matching line in modified_lines
                for idx, orig in enumerate(modified_lines):
                    if orig.strip() == old_text:
                        # Check if next line is an addition (+)
                        if i + 1 < len(lines_in_block) and lines_in_block[i + 1].startswith("+") and not lines_in_block[i + 1].startswith("+++"):
                            new_text = lines_in_block[i + 1][1:]
                            # Preserve leading indentation of original
                            indent = len(orig) - len(orig.lstrip())
                            modified_lines[idx] = (" " * indent) + new_text.strip()
                        else:
                            # It's a pure deletion (remove_field)
                            modified_lines[idx] = ""
                        break

        # Remove empty lines resulting from pure deletions if appropriate
        final_content = "\n".join([line for line in modified_lines if line is not None]) + "\n"
        target_file.write_text(final_content, encoding="utf-8")
        modified_files.append(rel_path)

    return backup_id, modified_files

def revert_patch_in_workspace(project_dir: Path, backup_id: str) -> List[str]:
    """
    Restores files from .backups/{backup_id}.
    """
    backup_dir = (project_dir / ".backups" / backup_id).resolve()
    if not backup_dir.exists():
        raise HTTPException(status_code=404, detail=f"Backup snapshot '{backup_id}' not found")

    restored_files: List[str] = []
    for root, _, files in os.walk(backup_dir):
        for f in files:
            full_backup_path = Path(root) / f
            rel_path = full_backup_path.relative_to(backup_dir).as_posix()
            target_dest = project_dir / rel_path

            target_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full_backup_path, target_dest)
            restored_files.append(rel_path)

    # Clean up backup snapshot directory
    shutil.rmtree(backup_dir, ignore_errors=True)
    return restored_files
