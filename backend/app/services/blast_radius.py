from pathlib import Path
from typing import Any, Dict, List, Set
from app.schemas.analysis import (
    BlastRadiusGraphResponse,
    EndpointInfo,
    EvidenceItem,
    GraphEdge,
    GraphNode,
    PydanticSchemaInfo,
)

def build_blast_radius_graph(
    project_id: str,
    endpoints: List[EndpointInfo],
    schemas: List[PydanticSchemaInfo],
    frontend_evidence: List[EvidenceItem],
    active_change_field: str = "",
    active_endpoint_id: str = "",
) -> BlastRadiusGraphResponse:
    """
    Constructs an interactive cross-stack dependency graph:
    [Route] -> [Pydantic Schema] -> [Frontend Client / TS Type] -> [React Component] -> [Test]
    Highlights affected nodes in amber/red when an active change matches.
    """
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []
    affected_node_ids: Set[str] = set()

    edge_counter = 0

    def add_edge(src: str, tgt: str, rel: str):
        nonlocal edge_counter
        edge_counter += 1
        edges.append(
            GraphEdge(
                id=f"e_{edge_counter}",
                source=src,
                target=tgt,
                relationship=rel,
            )
        )

    # 1. Add Route nodes
    for ep in endpoints:
        is_affected = bool(active_endpoint_id and ep.id == active_endpoint_id)
        status = "breaking" if is_affected else "normal"
        if is_affected:
            affected_node_ids.add(ep.id)

        nodes[ep.id] = GraphNode(
            id=ep.id,
            label=f"{ep.method} {ep.path}",
            node_type="route",
            status=status,
            details={
                "method": ep.method,
                "path": ep.path,
                "file": ep.file_path,
                "line": ep.line_number,
                "response_model": ep.response_model,
            },
        )

    # 2. Add Schema nodes and link to routes
    for schema in schemas:
        schema_id = f"schema:{schema.name}"
        nodes[schema_id] = GraphNode(
            id=schema_id,
            label=f"Schema: {schema.name}",
            node_type="schema",
            status="normal",
            details={
                "name": schema.name,
                "file": schema.file_path,
                "line": schema.line_number,
                "fields": [f.name for f in schema.fields],
            },
        )

        # Check if any route references this schema as response_model
        for ep in endpoints:
            if ep.response_model and schema.name in ep.response_model:
                add_edge(ep.id, schema_id, "returns")
                if ep.id in affected_node_ids:
                    nodes[schema_id].status = "breaking"
                    affected_node_ids.add(schema_id)

    # 3. Add Frontend Evidence nodes (Types, Clients, Components, Tests)
    for ev in frontend_evidence:
        file_node_id = f"file:{ev.file_path}"
        node_type = "component"
        if ev.category == "type_definition":
            node_type = "type"
        elif ev.category == "api_client":
            node_type = "client"
        elif ev.category == "test":
            node_type = "test"

        is_affected = bool(
            active_change_field and (ev.matched_symbol == active_change_field or active_change_field in ev.code_snippet)
        )
        status = "breaking" if is_affected else "normal"
        if is_affected:
            affected_node_ids.add(file_node_id)

        if file_node_id not in nodes:
            nodes[file_node_id] = GraphNode(
                id=file_node_id,
                label=ev.file_path.split("/")[-1],
                node_type=node_type,
                status=status,
                details={
                    "full_path": ev.file_path,
                    "category": ev.category,
                    "first_line": ev.line_number,
                },
            )
        elif is_affected:
            nodes[file_node_id].status = "breaking"

        # Link from Schemas or Routes to Frontend Nodes
        for schema_id, schema_node in list(nodes.items()):
            if schema_node.node_type == "schema":
                # If schema has the matched field or name matches
                schema_fields = schema_node.details.get("fields", [])
                if ev.matched_symbol in schema_fields:
                    add_edge(schema_id, file_node_id, "consumed_by")

    return BlastRadiusGraphResponse(
        project_id=project_id,
        nodes=list(nodes.values()),
        edges=edges,
        affected_node_ids=list(affected_node_ids),
    )
