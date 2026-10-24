from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

def test_health_endpoint():
    init_db()
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["app"] == "ChangeRadar"
        assert data["local_mode"] is True

def test_sample_project_lifecycle():
    init_db()
    with TestClient(app) as client:
        # 1. Load sample project
        res_sample = client.post("/api/projects/sample")
        assert res_sample.status_code == 200
        sample_proj = res_sample.json()
        project_id = sample_proj["id"]
        assert sample_proj["name"] == "FastAPI + React Demo App (Sample)"

        try:
            # 2. Get discovered endpoints
            res_endpoints = client.get(f"/api/projects/{project_id}/endpoints")
            assert res_endpoints.status_code == 200
            endpoints_data = res_endpoints.json()
            assert len(endpoints_data["endpoints"]) >= 2
            assert len(endpoints_data["schemas"]) >= 1

            # 3. Get Blast Radius graph
            res_graph = client.get(f"/api/projects/{project_id}/graph?field=email")
            assert res_graph.status_code == 200
            graph_data = res_graph.json()
            assert len(graph_data["nodes"]) > 0
            assert len(graph_data["edges"]) > 0

            # 4. Run impact analysis
            res_analysis = client.post(
                f"/api/projects/{project_id}/analyze",
                json={
                    "change_type": "remove_field",
                    "field_name": "email",
                    "model_name": "UserResponse",
                },
            )
            assert res_analysis.status_code == 200
            report = res_analysis.json()
            assert report["risk_level"] == "Breaking"
            assert report["confidence"] == "High"
            assert len(report["affected_files"]) > 0

            # 5. Get saved reports
            res_reports = client.get(f"/api/projects/{project_id}/reports")
            assert res_reports.status_code == 200
            reports_list = res_reports.json()
            assert len(reports_list) >= 1

            # 5b. Query LangGraph Agent Graph Spec
            res_spec = client.get(f"/api/projects/{project_id}/agent-graph-spec")
            assert res_spec.status_code == 200
            spec_data = res_spec.json()
            assert "LangGraph StateGraph" in spec_data["framework"]
            assert len(spec_data["nodes"]) == 6

            # 5c. Query LangGraph Interactive Copilot
            res_agent = client.post(
                f"/api/projects/{project_id}/agent-query",
                json={
                    "query": "How do I safely deprecate email without breaking clients?",
                    "change_type": "remove_field",
                    "field_name": "email",
                },
            )
            assert res_agent.status_code == 200
            agent_data = res_agent.json()
            assert "answer" in agent_data
            assert len(agent_data["trace"]) >= 2
            assert agent_data["compatibility_code"] is not None

        finally:
            # 6. Delete project
            res_del = client.delete(f"/api/projects/{project_id}")
            assert res_del.status_code == 200
            del_data = res_del.json()
            assert del_data["success"] is True

            # Ensure subsequent get returns 404
            res_check = client.get(f"/api/projects/{project_id}")
            assert res_check.status_code == 404
