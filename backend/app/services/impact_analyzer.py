import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.schemas.analysis import (
    AnalyzeRequest,
    EndpointInfo,
    EvidenceItem,
    ImpactReportResponse,
    PydanticSchemaInfo,
)
from app.services.git_diff_parser import parse_git_diff_for_api_changes
from app.services.patch_service import generate_migration_patch
from app.services.typescript_parser import TypeScriptParser

def analyze_impact(
    project_dir: Path,
    project_id: str,
    request: AnalyzeRequest,
    endpoints: List[EndpointInfo],
    schemas: List[PydanticSchemaInfo],
) -> ImpactReportResponse:
    ts_parser = TypeScriptParser(project_dir)
    report_id = f"rep_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    affected_files: List[EvidenceItem] = []
    relevant_tests: List[EvidenceItem] = []
    suggested_tests: List[str] = []
    limitations: List[str] = [
        "Static heuristic parsing cannot execute dynamic template string concatenations at runtime.",
        "Third-party external consumers outside this repository cannot be detected.",
    ]
    migration_patch = None

    # Handle git_diff mode
    if request.change_type == "git_diff" and request.git_diff:
        diff_changes = parse_git_diff_for_api_changes(request.git_diff)
        if not diff_changes:
            return ImpactReportResponse(
                report_id=report_id,
                project_id=project_id,
                created_at=now,
                change_summary="No breaking backend route or model changes detected in provided Git Diff.",
                change_type="git_diff",
                confidence="High",
                confidence_score=0.95,
                risk_level="Informational",
                affected_files=[],
                relevant_tests=[],
                suggested_tests=["Ensure pull request passes existing CI tests."],
                limitations=limitations,
            )

        # Aggregate detected changes
        summaries = []
        for chg in diff_changes:
            if chg["change_type"] == "remove_field":
                f_name = chg["field_name"]
                summaries.append(f"Remove field '{f_name}'")
                ev = ts_parser.find_field_references(f_name)
                for item in ev:
                    if item.category == "test":
                        relevant_tests.append(item)
                    else:
                        affected_files.append(item)
            elif chg["change_type"] == "change_route":
                p = chg.get("old_path", "")
                m = chg.get("old_method", "")
                summaries.append(f"Modify route {m} {p}")
                ev = ts_parser.find_route_references(p, m)
                for item in ev:
                    if item.category == "test":
                        relevant_tests.append(item)
                    else:
                        affected_files.append(item)

        change_summary = f"Git Diff analysis: {', '.join(summaries)}"
        risk_level = "Breaking" if (affected_files or relevant_tests) else "Informational"
        confidence = "High" if affected_files else "Medium"
        confidence_score = 0.90 if affected_files else 0.70

        from app.services.agentic_copilot import run_agentic_copilot
        agentic_insights = run_agentic_copilot(
            project_id=project_id,
            change_summary=change_summary,
            change_type="git_diff",
            risk_level=risk_level,
            confidence=confidence,
            affected_files=[f.model_dump() for f in affected_files],
            relevant_tests=[t.model_dump() for t in relevant_tests],
            migration_patch=None,
        )

        return ImpactReportResponse(
            report_id=report_id,
            project_id=project_id,
            created_at=now,
            change_summary=change_summary,
            change_type="git_diff",
            confidence=confidence,
            confidence_score=confidence_score,
            risk_level=risk_level,
            affected_files=affected_files,
            relevant_tests=relevant_tests,
            suggested_tests=[
                "Run full frontend test suite: npm test",
                "Perform manual smoke test of UI views referencing modified endpoints",
            ],
            limitations=limitations,
            migration_patch=None,
            agentic_insights=agentic_insights,
        )

    # 1. REMOVE FIELD
    if request.change_type == "remove_field":
        field = request.field_name or "unknown_field"
        change_summary = f"Removal of response field '{field}' from API response"
        if request.model_name:
            change_summary += f" (Model: {request.model_name})"

        evidence = ts_parser.find_field_references(field, request.model_name)
        for item in evidence:
            if item.category == "test":
                relevant_tests.append(item)
            else:
                affected_files.append(item)

        # Deduce risk & confidence
        if affected_files:
            risk_level = "Breaking"
            confidence = "High"
            confidence_score = 0.92
            suggested_tests.append(f"Verify frontend components handle the absence of '{field}' gracefully without throwing 'undefined' runtime errors.")
            suggested_tests.append(f"Update TypeScript interfaces removing '{field}' and run `npm run build` or `tsc --noEmit`.")
        else:
            risk_level = "Informational"
            confidence = "Medium"
            confidence_score = 0.75
            suggested_tests.append(f"No direct frontend consumers found for '{field}'. Verify if external API consumers depend on it.")

        if relevant_tests:
            suggested_tests.append(f"Update unit tests asserting on '{field}' in: {', '.join({t.file_path for t in relevant_tests})}")

        # Generate Migration Patch for remove_field
        all_evidence = affected_files + relevant_tests
        migration_patch = generate_migration_patch(
            project_dir=project_dir,
            change_type="remove_field",
            field_name=field,
            affected_files=all_evidence,
        )

    # 2. RENAME FIELD
    elif request.change_type == "rename_field":
        field = request.field_name or "old_field"
        new_field = request.new_field_name or "new_field"
        change_summary = f"Renaming field '{field}' to '{new_field}'"
        if request.model_name:
            change_summary += f" (Model: {request.model_name})"

        evidence = ts_parser.find_field_references(field, request.model_name)
        for item in evidence:
            if item.category == "test":
                relevant_tests.append(item)
            else:
                affected_files.append(item)

        risk_level = "Breaking" if affected_files else "Informational"
        confidence = "High" if affected_files else "Medium"
        confidence_score = 0.94 if affected_files else 0.75

        # Generate Migration Patch
        all_evidence = affected_files + relevant_tests
        migration_patch = generate_migration_patch(
            project_dir=project_dir,
            change_type="rename_field",
            field_name=field,
            new_field_name=new_field,
            affected_files=all_evidence,
        )

        suggested_tests.append(f"Review and apply the generated 1-Click Migration Patch to rename '{field}' to '{new_field}'.")
        suggested_tests.append(f"Run tests to ensure frontend components render with '{new_field}'.")

    # 3. CHANGE FIELD TYPE
    elif request.change_type == "change_field_type":
        field = request.field_name or "field"
        new_type = request.new_field_type or "new_type"
        change_summary = f"Changing field '{field}' type to '{new_type}'"

        evidence = ts_parser.find_field_references(field, request.model_name)
        for item in evidence:
            if item.category == "test":
                relevant_tests.append(item)
            else:
                affected_files.append(item)

        risk_level = "Breaking" if any(i.category in ["component", "type_definition"] for i in affected_files) else "Warning"
        confidence = "High" if affected_files else "Medium"
        confidence_score = 0.88

        suggested_tests.append(f"Inspect TypeScript type errors when updating interface property '{field}: {new_type}'.")
        suggested_tests.append(f"Verify parsing or math/string operations on '{field}' in consumer components.")

        all_evidence = affected_files + relevant_tests
        migration_patch = generate_migration_patch(
            project_dir=project_dir,
            change_type="change_field_type",
            field_name=field,
            new_field_type=new_type,
            affected_files=all_evidence,
        )

    # 4. CHANGE ROUTE PATH
    elif request.change_type == "change_route":
        old_path = request.endpoint_id or "/api"
        # If endpoint_id has format "METHOD /path", extract path
        if " " in old_path:
            old_path = old_path.split(" ", 1)[1]
        new_path = request.new_path or "/new-api"
        change_summary = f"Changing route path from '{old_path}' to '{new_path}'"

        evidence = ts_parser.find_route_references(old_path)
        for item in evidence:
            if item.category == "test":
                relevant_tests.append(item)
            else:
                affected_files.append(item)

        risk_level = "Breaking" if affected_files else "Warning"
        confidence = "High" if affected_files else "Medium"
        confidence_score = 0.91

        migration_patch = generate_migration_patch(
            project_dir=project_dir,
            change_type="change_route",
            old_path=old_path,
            new_path=new_path,
            affected_files=affected_files + relevant_tests,
        )

        suggested_tests.append(f"Update API client calls targeting '{old_path}' to use '{new_path}'.")
        suggested_tests.append("Verify network requests in browser developer tools return 200 OK.")

    # 5. CHANGE HTTP METHOD
    elif request.change_type == "change_http_method":
        old_ep = request.endpoint_id or "GET /api"
        old_method = old_ep.split(" ")[0] if " " in old_ep else "GET"
        old_path = old_ep.split(" ")[1] if " " in old_ep else "/api"
        new_method = request.new_method or "POST"
        change_summary = f"Changing HTTP method for '{old_path}' from {old_method} to {new_method}"

        evidence = ts_parser.find_route_references(old_path, old_method)
        for item in evidence:
            if item.category == "test":
                relevant_tests.append(item)
            else:
                affected_files.append(item)

        risk_level = "Breaking" if affected_files else "Warning"
        confidence = "High" if affected_files else "Medium"
        confidence_score = 0.90
        suggested_tests.append(f"Update frontend client call to issue {new_method} request instead of {old_method}.")

    else:
        change_summary = f"Custom change: {request.change_type}"
        risk_level = "Informational"
        confidence = "Low"
        confidence_score = 0.50

    # Execute LangGraph Agentic Copilot workflow
    from app.services.agentic_copilot import run_agentic_copilot
    agentic_insights = run_agentic_copilot(
        project_id=project_id,
        change_summary=change_summary,
        change_type=request.change_type,
        risk_level=risk_level,
        confidence=confidence,
        affected_files=[f.model_dump() for f in affected_files],
        relevant_tests=[t.model_dump() for t in relevant_tests],
        migration_patch=migration_patch,
        field_name=request.field_name,
        new_field_name=request.new_field_name,
        new_field_type=request.new_field_type,
    )

    return ImpactReportResponse(
        report_id=report_id,
        project_id=project_id,
        created_at=now,
        change_summary=change_summary,
        change_type=request.change_type,
        confidence=confidence,
        confidence_score=confidence_score,
        risk_level=risk_level,
        affected_files=affected_files,
        relevant_tests=relevant_tests,
        suggested_tests=suggested_tests,
        limitations=limitations,
        migration_patch=migration_patch,
        agentic_insights=agentic_insights,
    )
