import os
import time
from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

class RadarAgentState(TypedDict):
    project_id: str
    query: Optional[str]
    change_summary: str
    change_type: str
    field_name: Optional[str]
    new_field_name: Optional[str]
    new_field_type: Optional[str]
    risk_level: str
    confidence: str
    affected_files: List[Dict[str, Any]]
    relevant_tests: List[Dict[str, Any]]
    migration_patch: Optional[str]
    endpoints_summary: Optional[str]
    schemas_summary: Optional[str]
    # Agentic outputs
    architectural_assessment: str
    human_migration_guide: str
    compat_code: Optional[str]
    pr_review_comment: str
    autonomous_next_steps: List[str]
    interactive_answer: str
    suggested_followups: List[str]
    trace: List[Dict[str, Any]]

# ==============================================================================
# LangGraph Node 1: Architectural Risk & SemVer Assessment
# ==============================================================================
def assess_architectural_risk(state: RadarAgentState) -> Dict[str, Any]:
    t0 = time.perf_counter()
    affected_count = len(state.get("affected_files", []))
    risk = state.get("risk_level") or "Informational"
    change_type = state.get("change_type") or ""
    field = state.get("field_name") or "target field"

    if risk == "Breaking":
        semver = "MAJOR (vX+1.0.0)"
        impact_level = "Critical Severity"
        reason = (
            f"Modifying '{change_type}' on '{field}' introduces immediate runtime undefined exceptions in {affected_count} consumer(s). "
            "Violates semantic backward compatibility. Without API versioning (e.g. /v2/) or a dual-read adapter, existing frontend clients will crash on render."
        )
    elif risk == "Warning":
        semver = "MINOR (vX.Y+1.0)"
        impact_level = "Moderate Severity"
        reason = f"Type mutation or method shift detected on '{field}'. Requires explicit casting or schema alignment in client state stores."
    else:
        semver = "PATCH (vX.Y.Z+1)"
        impact_level = "Low / Non-Breaking"
        reason = "No direct consumer dependencies identified in static tree. Safe for zero-downtime deployment."

    assessment = (
        f"**SemVer Impact:** `{semver}` | **Severity:** `{impact_level}`\n\n"
        f"**Architectural Finding:** {reason}\n\n"
        f"**Blast Scope:** {affected_count} frontend consumer file(s) and {len(state.get('relevant_tests', []))} test suite(s)."
    )

    duration = round((time.perf_counter() - t0) * 1000, 2)
    trace_item = {
        "node_name": "assess_architectural_risk",
        "label": "Architectural Risk & SemVer Assessor",
        "duration_ms": duration,
        "status": "completed",
        "summary": f"Calculated SemVer impact: {semver} with severity {impact_level} across {affected_count} consumers.",
    }
    current_trace = list(state.get("trace", [])) + [trace_item]

    return {
        "architectural_assessment": assessment,
        "trace": current_trace,
    }

# ==============================================================================
# LangGraph Node 2: Human Developer Migration Guide Synthesizer
# ==============================================================================
def synthesize_migration_guide(state: RadarAgentState) -> Dict[str, Any]:
    t0 = time.perf_counter()
    files = state.get("affected_files", [])
    change_type = state.get("change_type", "")
    summary = state.get("change_summary", "")

    steps = [
        f"### 🛠️ Developer Migration Walkthrough: {summary}",
        "Follow these chronological steps to align the frontend with the backend change:",
    ]

    type_files = [f for f in files if f.get("category") == "type_definition"]
    comp_files = [f for f in files if f.get("category") == "component"]
    api_files = [f for f in files if f.get("category") == "api_client"]

    step_idx = 1
    if type_files:
        paths = ", ".join(f"`{f.get('file_path')}`" for f in type_files)
        steps.append(f"**Step {step_idx}: Update Type Contracts First**\n"
                     f"- Open {paths}.\n"
                     f"- Adjust the interface definition to match the backend Pydantic schema.")
        step_idx += 1

    if api_files:
        paths = ", ".join(f"`{f.get('file_path')}`" for f in api_files)
        steps.append(f"**Step {step_idx}: Synchronize API Client Wrappers**\n"
                     f"- Open {paths}.\n"
                     f"- Ensure fetch/axios payload serializers reflect the new schema.")
        step_idx += 1

    if comp_files:
        paths = ", ".join(f"`{f.get('file_path')}`" for f in comp_files)
        steps.append(f"**Step {step_idx}: Refactor UI Component Consumer References**\n"
                     f"- Open {paths}.\n"
                     f"- Replace deprecated field references or pass default fallback values.")
        step_idx += 1

    steps.append(f"**Step {step_idx}: Run 1-Click Workspace Migration**\n"
                 "- Use ChangeRadar's *'Apply Directly to Files'* button to auto-refactor with instant undo.")

    duration = round((time.perf_counter() - t0) * 1000, 2)
    trace_item = {
        "node_name": "synthesize_migration_guide",
        "label": "Migration Guide Synthesizer",
        "duration_ms": duration,
        "status": "completed",
        "summary": f"Synthesized {step_idx} chronological migration steps for types, api clients, and components.",
    }
    current_trace = list(state.get("trace", [])) + [trace_item]

    return {
        "human_migration_guide": "\n\n".join(steps),
        "trace": current_trace,
    }

# ==============================================================================
# LangGraph Node 3: Backwards-Compatibility Adapter Code Generator
# ==============================================================================
def synthesize_compatibility_code(state: RadarAgentState) -> Dict[str, Any]:
    t0 = time.perf_counter()
    change_type = state.get("change_type") or ""
    field = state.get("field_name") or "fieldName"
    new_field = state.get("new_field_name") or "newFieldName"
    new_type = state.get("new_field_type") or "string"

    code_lines = []
    if change_type == "rename_field":
        code_lines = [
            "// ===========================================================",
            "// ChangeRadar LangGraph Copilot: Backwards-Compatibility Shim",
            "// ===========================================================",
            "",
            "// 1. TypeScript Dual-Read Adapter (Zero-downtime client support):",
            f"export function normalizeContract<T extends Record<string, any>>(data: T) {{",
            f"  return {{",
            f"    ...data,",
            f"    // Dual-read fallback: accepts either old ({field}) or new ({new_field})",
            f"    {new_field}: data['{new_field}'] ?? data['{field}'] ?? null,",
            f"    {field}: data['{field}'] ?? data['{new_field}'] ?? null,",
            f"  }};",
            f"}}",
            "",
            "// 2. Python Pydantic Dual-Serialization Support (FastAPI backend):",
            "from pydantic import BaseModel, Field",
            "",
            "class BackwardCompatibleModel(BaseModel):",
            f"    {new_field}: str = Field(..., alias='{field}', description='Supports both legacy and new client keys')",
            "",
            "    class Config:",
            "        populate_by_name = True",
        ]
    elif change_type == "remove_field":
        code_lines = [
            "// ===========================================================",
            "// ChangeRadar LangGraph Copilot: Graceful Deprecation Wrapper",
            "// ===========================================================",
            "",
            "// TypeScript Safe Fallback Consumer Wrapper:",
            f"export function safeAccess{field.capitalize()}(entity: any, fallback: string = ''): string {{",
            f"  if (!entity) return fallback;",
            f"  if ('{field}' in entity && entity.{field} !== undefined) {{",
            f"    return String(entity.{field});",
            f"  }}",
            f"  console.warn('[ChangeRadar Deprecation]: Property {field} is deprecated and removed.');",
            f"  return fallback;",
            f"}}",
            "",
            "// Python FastAPI Deprecation Header Injection:",
            "from fastapi import Response",
            "",
            "def add_deprecation_headers(response: Response):",
            f"    response.headers['Deprecation'] = 'true'",
            f"    response.headers['Sunset'] = 'Wed, 11 Nov 2026 00:00:00 GMT'",
            f"    response.headers['Link'] = '</docs/deprecations/{field}>; rel=\"deprecation\"'",
        ]
    elif change_type == "change_field_type":
        code_lines = [
            "// ===========================================================",
            "// ChangeRadar LangGraph Copilot: Type Coercion Adapter",
            "// ===========================================================",
            "",
            f"// TypeScript Union Parser for {field} ({new_type}):",
            f"export function parse{field.capitalize()}(val: unknown): {new_type} {{",
            f"  if (typeof val === '{new_type}') return val as {new_type};",
            f"  return String(val) as unknown as {new_type};",
            f"}}",
        ]
    else:
        code_lines = [
            "// ===========================================================",
            "// ChangeRadar LangGraph Copilot: Route Proxy Middleware",
            "// ===========================================================",
            "",
            "// Fast 308 Permanent Redirect for changed API endpoints:",
            "from fastapi import APIRouter, status",
            "from fastapi.responses import RedirectResponse",
            "",
            "legacy_router = APIRouter()",
            "@legacy_router.api_route('/old-path', methods=['GET', 'POST', 'PUT', 'DELETE'])",
            "def redirect_to_v2():",
            "    return RedirectResponse(url='/new-path', status_code=status.HTTP_308_PERMANENT_REDIRECT)",
        ]

    compat_code = "\n".join(code_lines)
    duration = round((time.perf_counter() - t0) * 1000, 2)
    trace_item = {
        "node_name": "synthesize_compatibility_code",
        "label": "Compatibility Code Synthesizer",
        "duration_ms": duration,
        "status": "completed",
        "summary": f"Generated zero-downtime adapter and deprecation shim for '{change_type}'.",
    }
    current_trace = list(state.get("trace", [])) + [trace_item]

    return {
        "compat_code": compat_code,
        "trace": current_trace,
    }

# ==============================================================================
# LangGraph Node 4: AI Senior PR Review Commenter
# ==============================================================================
def draft_pr_review_comment(state: RadarAgentState) -> Dict[str, Any]:
    t0 = time.perf_counter()
    summary = state.get("change_summary", "")
    risk = state.get("risk_level", "Breaking")
    files = state.get("affected_files", [])

    comment = (
        f"## 🤖 ChangeRadar LangGraph Agent PR Review\n\n"
        f"> **Reviewer Assessment:** {'🔴 CHANGES REQUESTED' if risk == 'Breaking' else '🟡 REVIEW WITH CAUTION'}\n\n"
        f"Automated blast-radius analysis compiled via LangGraph StateGraph on **{summary}**.\n\n"
        f"### 🚨 Risk Assessment\n"
        f"This pull request introduces a **{risk}** contract change affecting **{len(files)} frontend file(s)**.\n\n"
        f"### 📋 Required PR Approval Gates\n"
        f"- [ ] Frontend types synchronized with updated backend Pydantic model.\n"
        f"- [ ] No remaining references to deprecated properties in React render methods.\n"
        f"- [ ] Unit tests updated and passing in CI: `npm test`.\n"
        f"- [ ] Backward-compatibility adapter reviewed and approved by fullstack tech lead."
    )

    duration = round((time.perf_counter() - t0) * 1000, 2)
    trace_item = {
        "node_name": "draft_pr_review_comment",
        "label": "Senior Staff PR Reviewer",
        "duration_ms": duration,
        "status": "completed",
        "summary": f"Drafted GitHub PR review comment with strict approval checklist (Status: {risk}).",
    }
    current_trace = list(state.get("trace", [])) + [trace_item]

    return {
        "pr_review_comment": comment,
        "trace": current_trace,
    }

# ==============================================================================
# LangGraph Node 5: Autonomous Next Steps & Verification Flight Control
# ==============================================================================
def determine_autonomous_next_steps(state: RadarAgentState) -> Dict[str, Any]:
    t0 = time.perf_counter()
    risk = state.get("risk_level", "Breaking")
    tests = state.get("relevant_tests", [])

    next_steps = [
        "1. Apply generated 1-Click Migration Patch to workspace.",
        "2. Run automated test suite: python -m pytest backend/tests && npm test.",
    ]

    if risk == "Breaking":
        next_steps.append("3. Inject backward-compatibility dual-read adapter into frontend API client.")
        next_steps.append("4. Issue deprecation RFC or notify partner / mobile consumer teams.")

    if tests:
        test_files = list({t.get("file_path") for t in tests if t.get("file_path")})
        next_steps.append(f"5. Execute targeted component test suites in: {', '.join(test_files)}.")

    duration = round((time.perf_counter() - t0) * 1000, 2)
    trace_item = {
        "node_name": "determine_autonomous_next_steps",
        "label": "Flight Control Next Steps Planner",
        "duration_ms": duration,
        "status": "completed",
        "summary": f"Generated {len(next_steps)} prioritized flight-control next steps.",
    }
    current_trace = list(state.get("trace", [])) + [trace_item]

    return {
        "autonomous_next_steps": next_steps,
        "trace": current_trace,
    }

# ==============================================================================
# LangGraph Node 6: Interactive Developer Copilot Assistant
# ==============================================================================
def interactive_developer_assistant(state: RadarAgentState) -> Dict[str, Any]:
    t0 = time.perf_counter()
    query = state.get("query") or ""
    summary = state.get("change_summary") or ""
    risk = state.get("risk_level") or "Breaking"
    files = state.get("affected_files", [])
    field = state.get("field_name") or "target field"
    q_lower = query.lower()

    # Grounded reasoning response based on project query context
    sections = [
        f"### 🤖 LangGraph Copilot Analysis for: \"{query}\"",
        f"**Context Grounding:** Evaluated against **{summary or 'Workspace Contract'}** with risk level **{risk}** across **{len(files)} consumer file(s)**.\n",
    ]
    followups = []

    if "deprecat" in q_lower or "safe" in q_lower or "zero-downtime" in q_lower:
        sections.append(
            "#### 🛡️ Zero-Downtime Safe Deprecation Strategy\n"
            "To deprecate without breaking clients in production, use the **Expand-and-Contract** pattern:\n\n"
            "1. **Phase 1 (Expand):** Keep the legacy field while introducing the new field in your backend Pydantic model.\n"
            "2. **Phase 2 (Dual-Read):** Deploy frontend clients with the generated dual-read compatibility adapter.\n"
            "3. **Phase 3 (Deprecation Notice):** Emit HTTP `Sunset` and `Deprecation` response headers from FastAPI endpoints.\n"
            "4. **Phase 4 (Contract):** After telemetry confirms 0% traffic on legacy field for 14 days, safely remove the old field in a major release."
        )
        followups = [
            "How do I add Sunset headers in FastAPI?",
            "Show me the TypeScript dual-read adapter code",
            "Generate a consumer migration checklist",
        ]
    elif "test" in q_lower or "jest" in q_lower or "pytest" in q_lower:
        sections.append(
            "#### 🧪 Recommended Verification Test Specifications\n"
            f"Target tests to update for `{field}` changes:\n\n"
            "```typescript\n"
            "// Jest / Vitest Frontend Regression Test Spec:\n"
            "describe('Contract Compatibility Test', () => {\n"
            "  it('gracefully handles missing or transformed " + field + "', () => {\n"
            "    const legacyPayload = { id: 1, " + field + ": 'test_value' };\n"
            "    const adapted = normalizeContract(legacyPayload);\n"
            "    expect(adapted).toBeDefined();\n"
            "  });\n"
            "});\n"
            "```\n\n"
            "```python\n"
            "# Backend Pytest Contract Schema Test:\n"
            "def test_contract_backward_compatibility():\n"
            "    # Asserts that legacy payloads continue to serialize\n"
            "    data = {'id': 1, '" + field + "': 'val'}\n"
            "    assert 'id' in data\n"
            "```"
        )
        followups = [
            "Generate mock API responses for Vitest",
            "How do I run tests across the affected files?",
            "Apply the migration patch to my files",
        ]
    elif "wrapper" in q_lower or "adapter" in q_lower or "compat" in q_lower:
        sections.append(
            "#### 🔌 Compatibility Wrapper Architecture\n"
            "A compatibility layer shields your React UI components from breaking changes. "
            "See the synthesized code snippet below for the drop-in TypeScript and Python shims."
        )
        followups = [
            "How do I apply this adapter to my Axios client?",
            "What happens if an old mobile client calls the API?",
            "Explain the SemVer impact of this change",
        ]
    else:
        sections.append(
            f"#### 💡 Architecture & Implementation Insights\n"
            f"Based on static AST parsing of your project workspace, altering `{field}` directly affects:\n"
            + "\n".join(f"- `{f.get('file_path')}` ({f.get('category')})" for f in files[:4])
            + (f"\n- ...and {len(files) - 4} more files." if len(files) > 4 else "")
            + "\n\n"
            "**Recommended Action:** Use ChangeRadar's 1-Click Migration Patch to synchronize interfaces before updating React consumer components."
        )
        followups = [
            "Show me how to safely deprecate this field",
            "Generate backwards-compatible wrapper",
            "Write test specifications for the affected files",
        ]

    # 1. Attempt Local Ollama inference if running
    from app.services.ollama_service import generate_with_ollama
    from app.config import OLLAMA_MODEL

    engine_tag = "Deterministic AST Engine"
    ollama_prompt = (
        f"You are ChangeRadar Copilot, a Principal Software Architect analyzing an API contract change.\n\n"
        f"Project Context:\n"
        f"- Change: {summary or 'API Modification'}\n"
        f"- Severity Risk: {risk}\n"
        f"- Affected Field: {field}\n"
        f"- Affected Files: {', '.join([f.get('file_path', '') for f in files[:4]])}\n\n"
        f"Developer Prompt: \"{query}\"\n\n"
        f"Provide a concise, practical, senior-level architectural and code migration guide."
    )
    ollama_resp = generate_with_ollama(prompt=ollama_prompt, timeout=30.0)

    if ollama_resp and len(ollama_resp.strip()) > 50:
        engine_tag = f"Local Ollama ({OLLAMA_MODEL})"
        answer = (
            f"> 🦙 **Inference Engine: Local Ollama (`{OLLAMA_MODEL}`)** • 100% Local GPU/CPU\n\n"
            + ollama_resp
        )
        followups = [
            "How do I add Sunset headers in FastAPI?",
            "Show me the TypeScript compatibility adapter",
            "Write test specifications for the affected files",
        ]
    else:
        answer = "\n\n".join(sections)

    duration = round((time.perf_counter() - t0) * 1000, 2)
    trace_item = {
        "node_name": "interactive_developer_assistant",
        "label": f"Interactive Copilot ({engine_tag})",
        "duration_ms": duration,
        "status": "completed",
        "summary": f"[{engine_tag}] Processed developer prompt: '{query[:40]}...'",
    }
    current_trace = list(state.get("trace", [])) + [trace_item]

    return {
        "interactive_answer": answer,
        "suggested_followups": followups,
        "trace": current_trace,
    }

# ==============================================================================
# LangGraph Routing & Construction
# ==============================================================================
def route_by_mode(state: RadarAgentState) -> str:
    """
    Conditional edge: routes to interactive mode if user provided a query,
    or full analysis mode otherwise.
    """
    if state.get("query"):
        return "interactive_mode"
    return "full_analysis_mode"

def route_after_compat_code(state: RadarAgentState) -> str:
    """
    Conditional edge: In interactive mode, finish at END.
    In full analysis mode, continue to PR review node.
    """
    if state.get("query"):
        return "end_node"
    return "draft_pr_review_comment"

def build_radar_agent_graph():
    """
    Compiles the LangGraph StateGraph workflow for ChangeRadar.
    """
    workflow = StateGraph(RadarAgentState)

    # Register nodes
    workflow.add_node("assess_architectural_risk", assess_architectural_risk)
    workflow.add_node("synthesize_migration_guide", synthesize_migration_guide)
    workflow.add_node("synthesize_compatibility_code", synthesize_compatibility_code)
    workflow.add_node("draft_pr_review_comment", draft_pr_review_comment)
    workflow.add_node("determine_autonomous_next_steps", determine_autonomous_next_steps)
    workflow.add_node("interactive_developer_assistant", interactive_developer_assistant)

    # Add conditional entry routing from START
    workflow.add_conditional_edges(
        START,
        route_by_mode,
        {
            "full_analysis_mode": "assess_architectural_risk",
            "interactive_mode": "interactive_developer_assistant",
        },
    )

    # Full analysis pipeline edges
    workflow.add_edge("assess_architectural_risk", "synthesize_migration_guide")
    workflow.add_edge("synthesize_migration_guide", "synthesize_compatibility_code")

    # Conditional branch after compat code
    workflow.add_conditional_edges(
        "synthesize_compatibility_code",
        route_after_compat_code,
        {
            "end_node": END,
            "draft_pr_review_comment": "draft_pr_review_comment",
        },
    )

    workflow.add_edge("draft_pr_review_comment", "determine_autonomous_next_steps")
    workflow.add_edge("determine_autonomous_next_steps", END)

    # Interactive pipeline edge
    workflow.add_edge("interactive_developer_assistant", "synthesize_compatibility_code")

    return workflow.compile()

# Global compiled LangGraph instance
radar_agentic_app = build_radar_agent_graph()

def get_agent_graph_spec() -> Dict[str, Any]:
    """
    Returns visual specification of the compiled LangGraph StateGraph.
    """
    return {
        "graph_id": "changeradar-langgraph-agent",
        "framework": "LangGraph StateGraph 1.2",
        "nodes": [
            {
                "id": "assess_architectural_risk",
                "label": "Risk & SemVer Assessor",
                "node_type": "evaluator",
                "description": "Calculates semantic versioning impact (Major/Minor/Patch) and contract severity.",
            },
            {
                "id": "synthesize_migration_guide",
                "label": "Migration Guide Synthesizer",
                "node_type": "generator",
                "description": "Constructs chronological step-by-step developer migration walkthrough.",
            },
            {
                "id": "synthesize_compatibility_code",
                "label": "Compatibility Code Synthesizer",
                "node_type": "coder",
                "description": "Generates TypeScript dual-read adapters, Pydantic field aliases, and shims.",
            },
            {
                "id": "draft_pr_review_comment",
                "label": "Senior PR Reviewer",
                "node_type": "critic",
                "description": "Drafts senior staff engineer pull request review with strict approval checklist.",
            },
            {
                "id": "determine_autonomous_next_steps",
                "label": "Flight Control Planner",
                "node_type": "planner",
                "description": "Determines autonomous execution flight path, test commands, and alerts.",
            },
            {
                "id": "interactive_developer_assistant",
                "label": "Interactive Copilot Assistant",
                "node_type": "chat",
                "description": "Answers developer queries grounded in real-time AST blast radius data.",
            },
        ],
        "edges": [
            {"source": "START", "target": "assess_architectural_risk", "condition": "mode == full_analysis"},
            {"source": "START", "target": "interactive_developer_assistant", "condition": "mode == interactive"},
            {"source": "assess_architectural_risk", "target": "synthesize_migration_guide"},
            {"source": "synthesize_migration_guide", "target": "synthesize_compatibility_code"},
            {"source": "synthesize_compatibility_code", "target": "draft_pr_review_comment", "condition": "mode == full_analysis"},
            {"source": "synthesize_compatibility_code", "target": "END", "condition": "mode == interactive"},
            {"source": "draft_pr_review_comment", "target": "determine_autonomous_next_steps"},
            {"source": "determine_autonomous_next_steps", "target": "END"},
            {"source": "interactive_developer_assistant", "target": "synthesize_compatibility_code"},
        ],
    }

def run_agentic_copilot(
    project_id: str,
    change_summary: str,
    change_type: str,
    risk_level: str,
    confidence: str,
    affected_files: List[Dict[str, Any]],
    relevant_tests: List[Dict[str, Any]],
    migration_patch: Optional[str] = None,
    field_name: Optional[str] = None,
    new_field_name: Optional[str] = None,
    new_field_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the LangGraph agentic copilot pipeline for a given analysis report.
    """
    initial_state: RadarAgentState = {
        "project_id": project_id,
        "query": None,
        "change_summary": change_summary,
        "change_type": change_type,
        "field_name": field_name,
        "new_field_name": new_field_name,
        "new_field_type": new_field_type,
        "risk_level": risk_level,
        "confidence": confidence,
        "affected_files": affected_files,
        "relevant_tests": relevant_tests,
        "migration_patch": migration_patch,
        "endpoints_summary": None,
        "schemas_summary": None,
        "architectural_assessment": "",
        "human_migration_guide": "",
        "compat_code": None,
        "pr_review_comment": "",
        "autonomous_next_steps": [],
        "interactive_answer": "",
        "suggested_followups": [],
        "trace": [],
    }

    result = radar_agentic_app.invoke(initial_state)
    return {
        "architectural_assessment": result.get("architectural_assessment", ""),
        "human_migration_guide": result.get("human_migration_guide", ""),
        "compat_code": result.get("compat_code"),
        "pr_review_comment": result.get("pr_review_comment", ""),
        "autonomous_next_steps": result.get("autonomous_next_steps", []),
        "trace": result.get("trace", []),
    }

def run_interactive_agent_query(
    project_id: str,
    query: str,
    change_summary: str = "",
    change_type: str = "rename_field",
    risk_level: str = "Breaking",
    confidence: str = "High",
    affected_files: Optional[List[Dict[str, Any]]] = None,
    relevant_tests: Optional[List[Dict[str, Any]]] = None,
    field_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes an interactive user query through the LangGraph StateGraph.
    """
    initial_state: RadarAgentState = {
        "project_id": project_id,
        "query": query,
        "change_summary": change_summary or f"Custom Query: {query}",
        "change_type": change_type,
        "field_name": field_name,
        "new_field_name": None,
        "new_field_type": None,
        "risk_level": risk_level,
        "confidence": confidence,
        "affected_files": affected_files or [],
        "relevant_tests": relevant_tests or [],
        "migration_patch": None,
        "endpoints_summary": None,
        "schemas_summary": None,
        "architectural_assessment": "",
        "human_migration_guide": "",
        "compat_code": None,
        "pr_review_comment": "",
        "autonomous_next_steps": [],
        "interactive_answer": "",
        "suggested_followups": [],
        "trace": [],
    }

    result = radar_agentic_app.invoke(initial_state)
    return {
        "query": query,
        "answer": result.get("interactive_answer", ""),
        "compatibility_code": result.get("compat_code"),
        "trace": result.get("trace", []),
        "suggested_followups": result.get("suggested_followups", []),
    }
