import tempfile
from pathlib import Path
from app.schemas.analysis import AnalyzeRequest, EndpointInfo, PydanticFieldInfo, PydanticSchemaInfo
from app.services.impact_analyzer import analyze_impact

def test_impact_analyzer_remove_and_rename_field():
    with tempfile.TemporaryDirectory() as tmp_dir:
        proj_dir = Path(tmp_dir)

        # Create frontend files
        src_dir = proj_dir / "src"
        src_dir.mkdir(parents=True)

        (src_dir / "user.ts").write_text(
            'export interface User {\n'
            '  id: number;\n'
            '  email: string;\n'
            '}\n'
        )

        (src_dir / "UserProfile.tsx").write_text(
            'export const UserProfile = ({ user }: { user: any }) => (\n'
            '  <div>{user.email}</div>\n'
            ');\n'
        )

        tests_dir = src_dir / "__tests__"
        tests_dir.mkdir()
        (tests_dir / "UserProfile.test.tsx").write_text(
            'test("renders email", () => {\n'
            '  expect(user.email).toBe("a@b.com");\n'
            '});\n'
        )

        # 1. Test remove_field
        endpoints = [
            EndpointInfo(
                id="GET /users",
                method="GET",
                path="/users",
                function_name="get_users",
                file_path="routes/users.py",
                line_number=10,
                response_model="UserResponse",
            )
        ]
        schemas = [
            PydanticSchemaInfo(
                name="UserResponse",
                file_path="schemas/user.py",
                line_number=5,
                fields=[
                    PydanticFieldInfo(name="id", type_annotation="int"),
                    PydanticFieldInfo(name="email", type_annotation="str"),
                ],
            )
        ]

        req_remove = AnalyzeRequest(
            change_type="remove_field",
            field_name="email",
            model_name="UserResponse",
        )

        report_remove = analyze_impact(proj_dir, "test_proj", req_remove, endpoints, schemas)
        assert report_remove.risk_level == "Breaking"
        assert report_remove.confidence == "High"
        assert len(report_remove.affected_files) >= 2  # user.ts and UserProfile.tsx
        assert len(report_remove.relevant_tests) >= 1  # UserProfile.test.tsx

        # 2. Test rename_field and migration patch generation
        req_rename = AnalyzeRequest(
            change_type="rename_field",
            field_name="email",
            new_field_name="contact_email",
            model_name="UserResponse",
        )

        report_rename = analyze_impact(proj_dir, "test_proj", req_rename, endpoints, schemas)
        assert report_rename.risk_level == "Breaking"
        assert report_rename.migration_patch is not None
        assert "contact_email" in report_rename.migration_patch
        assert "-  email: string;" in report_rename.migration_patch
        assert "+  contact_email: string;" in report_rename.migration_patch
