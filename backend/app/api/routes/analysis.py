from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.database import get_project_by_id, insert_report, get_report_by_id
from app.schemas.analysis import (
    AnalyzeRequest,
    AgentGraphSpecResponse,
    AgentQueryRequest,
    AgentQueryResponse,
    BlastRadiusGraphResponse,
    DiscoveredEndpointsResponse,
    ImpactReportResponse,
)
from app.services.agentic_copilot import get_agent_graph_spec, run_interactive_agent_query
from app.services.blast_radius import build_blast_radius_graph
from app.services.fastapi_parser import parse_all_python_files
from app.services.impact_analyzer import analyze_impact
from app.services.typescript_parser import TypeScriptParser

router = APIRouter(prefix="/api/projects/{project_id}", tags=["analysis"])

def get_valid_project_dir(project_id: str) -> Path:
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    proj_dir = Path(project["extracted_path"])
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail="Extracted project directory is missing")
    return proj_dir

@router.get("/endpoints", response_model=DiscoveredEndpointsResponse)
def get_endpoints(project_id: str):
    proj_dir = get_valid_project_dir(project_id)
    endpoints, schemas = parse_all_python_files(proj_dir)
    return DiscoveredEndpointsResponse(
        project_id=project_id,
        endpoints=endpoints,
        schemas=schemas,
    )

@router.get("/graph", response_model=BlastRadiusGraphResponse)
def get_blast_radius_graph(
    project_id: str,
    field: Optional[str] = Query(default="", description="Active change field name"),
    endpoint: Optional[str] = Query(default="", description="Active endpoint ID"),
):
    proj_dir = get_valid_project_dir(project_id)
    endpoints, schemas = parse_all_python_files(proj_dir)
    ts_parser = TypeScriptParser(proj_dir)

    # Gather frontend evidence
    frontend_evidence = []
    if field:
        frontend_evidence.extend(ts_parser.find_field_references(field))
    if endpoint:
        path = endpoint.split(" ")[1] if " " in endpoint else endpoint
        frontend_evidence.extend(ts_parser.find_route_references(path))

    # If neither query specified, collect all interface fields & route references
    if not field and not endpoint:
        for schema in schemas:
            for f in schema.fields:
                frontend_evidence.extend(ts_parser.find_field_references(f.name))
        for ep in endpoints:
            frontend_evidence.extend(ts_parser.find_route_references(ep.path))

    graph = build_blast_radius_graph(
        project_id=project_id,
        endpoints=endpoints,
        schemas=schemas,
        frontend_evidence=frontend_evidence,
        active_change_field=field,
        active_endpoint_id=endpoint,
    )
    return graph

@router.post("/analyze", response_model=ImpactReportResponse)
def run_impact_analysis(project_id: str, request: AnalyzeRequest):
    proj_dir = get_valid_project_dir(project_id)
    endpoints, schemas = parse_all_python_files(proj_dir)

    report = analyze_impact(
        project_dir=proj_dir,
        project_id=project_id,
        request=request,
        endpoints=endpoints,
        schemas=schemas,
    )

    # Persist report to SQLite database
    insert_report(
        report_id=report.report_id,
        project_id=project_id,
        change_type=report.change_type,
        change_payload=request.model_dump(),
        report_data=report.model_dump(),
    )

    return report

class ApplyPatchRequest(BaseModel):
    patch: str

class RevertPatchRequest(BaseModel):
    backup_id: str

@router.post("/apply-patch")
def apply_migration_patch(project_id: str, payload: ApplyPatchRequest):
    proj_dir = get_valid_project_dir(project_id)
    from app.services.patch_applier import apply_patch_to_workspace
    backup_id, modified_files = apply_patch_to_workspace(proj_dir, payload.patch)
    return {
        "success": True,
        "backup_id": backup_id,
        "modified_files": modified_files,
        "message": f"Successfully applied migration patch to {len(modified_files)} file(s).",
    }

@router.post("/revert-patch")
def revert_migration_patch(project_id: str, payload: RevertPatchRequest):
    proj_dir = get_valid_project_dir(project_id)
    from app.services.patch_applier import revert_patch_in_workspace
    restored_files = revert_patch_in_workspace(proj_dir, payload.backup_id)
    return {
        "success": True,
        "restored_files": restored_files,
        "message": f"Successfully reverted {len(restored_files)} file(s) from snapshot {payload.backup_id}.",
    }

@router.get("/agent-graph-spec", response_model=AgentGraphSpecResponse)
def get_langgraph_specification(project_id: str):
    get_valid_project_dir(project_id)
    spec = get_agent_graph_spec()
    return AgentGraphSpecResponse(**spec)

@router.post("/agent-query", response_model=AgentQueryResponse)
def ask_langgraph_copilot(project_id: str, payload: AgentQueryRequest):
    proj_dir = get_valid_project_dir(project_id)

    # Optional: fetch context report if specified
    report_data = None
    if payload.context_report_id:
        record = get_report_by_id(payload.context_report_id)
        if record:
            report_data = record.get("report_data")

    # If report context is available, extract fields
    change_summary = ""
    change_type = payload.change_type or "rename_field"
    field_name = payload.field_name
    risk_level = "Breaking"
    confidence = "High"
    affected_files = []
    relevant_tests = []

    if report_data:
        change_summary = report_data.get("change_summary", "")
        change_type = report_data.get("change_type", change_type)
        risk_level = report_data.get("risk_level", "Breaking")
        confidence = report_data.get("confidence", "High")
        affected_files = report_data.get("affected_files", [])
        relevant_tests = report_data.get("relevant_tests", [])

    if not field_name and report_data:
        # Infer field name from report change summary if possible
        summary = report_data.get("change_summary", "")
        if "'" in summary:
            parts = summary.split("'")
            if len(parts) >= 2:
                field_name = parts[1]

    # If still no affected files, do AST inspection for the project
    if not affected_files:
        ts_parser = TypeScriptParser(proj_dir)
        target_field = field_name or "email"
        affected_files = [f.model_dump() for f in ts_parser.find_field_references(target_field)]

    result = run_interactive_agent_query(
        project_id=project_id,
        query=payload.query,
        change_summary=change_summary,
        change_type=change_type,
        risk_level=risk_level,
        confidence=confidence,
        affected_files=affected_files,
        relevant_tests=relevant_tests,
        field_name=field_name,
    )

    return AgentQueryResponse(
        query=result.get("query", payload.query),
        answer=result.get("answer", ""),
        compatibility_code=result.get("compatibility_code"),
        trace=result.get("trace", []),
        suggested_followups=result.get("suggested_followups", []),
    )

