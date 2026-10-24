import tempfile
from pathlib import Path
from app.services.patch_applier import apply_patch_to_workspace, revert_patch_in_workspace

SAMPLE_PATCH = """--- a/src/user.ts
+++ b/src/user.ts
@@ -1,3 +1,3 @@
 export interface User {
-  email: string;
+  contact_email: string;
 }
"""

def test_apply_and_revert_patch():
    with tempfile.TemporaryDirectory() as tmp_dir:
        proj_dir = Path(tmp_dir)
        src_dir = proj_dir / "src"
        src_dir.mkdir(parents=True)

        user_file = src_dir / "user.ts"
        original_content = "export interface User {\n  email: string;\n}\n"
        user_file.write_text(original_content, encoding="utf-8")

        # 1. Apply patch
        backup_id, modified = apply_patch_to_workspace(proj_dir, SAMPLE_PATCH)
        assert len(modified) == 1
        assert "src/user.ts" in modified

        # Verify content was updated
        updated_content = user_file.read_text(encoding="utf-8")
        assert "contact_email: string;" in updated_content
        assert "  email: string;" not in updated_content

        # 2. Revert patch
        restored = revert_patch_in_workspace(proj_dir, backup_id)
        assert len(restored) == 1

        # Verify original content was restored
        reverted_content = user_file.read_text(encoding="utf-8")
        assert reverted_content == original_content
