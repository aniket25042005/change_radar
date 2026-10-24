from app.services.agentic_copilot import (
    run_agentic_copilot,
    run_interactive_agent_query,
    get_agent_graph_spec,
)

def test_langgraph_agentic_copilot_execution():
    res = run_agentic_copilot(
        project_id="test_proj_langgraph",
        change_summary="Remove field 'email' from UserResponse",
        change_type="remove_field",
        risk_level="Breaking",
        confidence="High",
        affected_files=[
            {"file_path": "frontend/src/types/user.ts", "category": "type_definition"},
            {"file_path": "frontend/src/components/UserProfile.tsx", "category": "component"},
        ],
        relevant_tests=[
            {"file_path": "frontend/src/__tests__/UserProfile.test.tsx", "category": "test"},
        ],
        migration_patch="--- a/user.ts\n+++ b/user.ts\n- email: string;\n",
        field_name="email",
    )

    # Verify all state graph nodes executed
    assert "architectural_assessment" in res
    assert "human_migration_guide" in res
    assert "compat_code" in res
    assert "pr_review_comment" in res
    assert "autonomous_next_steps" in res
    assert "trace" in res

    assert "MAJOR" in res["architectural_assessment"]
    assert "Update Type Contracts" in res["human_migration_guide"]
    assert "ChangeRadar LangGraph Agent PR Review" in res["pr_review_comment"]
    assert len(res["autonomous_next_steps"]) >= 2
    assert len(res["trace"]) >= 4

def test_langgraph_interactive_agent_query():
    res = run_interactive_agent_query(
        project_id="test_proj_langgraph",
        query="How do I safely deprecate email without breaking mobile clients?",
        change_summary="Remove field 'email'",
        change_type="remove_field",
        field_name="email",
    )

    assert "answer" in res
    assert "Zero-Downtime Safe Deprecation Strategy" in res["answer"]
    assert "compatibility_code" in res
    assert len(res["trace"]) >= 2
    assert len(res["suggested_followups"]) >= 1

def test_langgraph_specification():
    spec = get_agent_graph_spec()
    assert spec["graph_id"] == "changeradar-langgraph-agent"
    assert len(spec["nodes"]) == 6
    assert len(spec["edges"]) >= 8
