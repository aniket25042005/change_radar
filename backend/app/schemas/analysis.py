from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class PydanticFieldInfo(BaseModel):
    name: str
    type_annotation: str
    line_number: Optional[int] = None
    required: bool = True

class PydanticSchemaInfo(BaseModel):
    name: str
    file_path: str
    line_number: int
    fields: List[PydanticFieldInfo] = Field(default_factory=list)

class EndpointInfo(BaseModel):
    id: str
    method: str
    path: str
    function_name: str
    file_path: str
    line_number: int
    response_model: Optional[str] = None
    request_model: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    router_prefix: Optional[str] = None

class DiscoveredEndpointsResponse(BaseModel):
    project_id: str
    endpoints: List[EndpointInfo]
    schemas: List[PydanticSchemaInfo]

class AnalyzeRequest(BaseModel):
    change_type: Literal[
        "remove_field",
        "rename_field",
        "change_field_type",
        "change_route",
        "change_http_method",
        "git_diff",
    ]
    endpoint_id: Optional[str] = None
    model_name: Optional[str] = None
    field_name: Optional[str] = None
    new_field_name: Optional[str] = None
    new_field_type: Optional[str] = None
    new_path: Optional[str] = None
    new_method: Optional[str] = None
    git_diff: Optional[str] = None

class EvidenceItem(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    matched_symbol: str
    code_snippet: str
    reason: str
    category: Literal["component", "type_definition", "api_client", "test", "other"]

class ImpactReportResponse(BaseModel):
    report_id: str
    project_id: str
    created_at: str
    change_summary: str
    change_type: str
    confidence: Literal["High", "Medium", "Low"]
    confidence_score: float
    risk_level: Literal["Breaking", "Warning", "Informational"]
    affected_files: List[EvidenceItem] = Field(default_factory=list)
    relevant_tests: List[EvidenceItem] = Field(default_factory=list)
    suggested_tests: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    migration_patch: Optional[str] = None
    agentic_insights: Optional[Dict[str, Any]] = None

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: Literal["route", "schema", "field", "type", "client", "component", "test"]
    status: Literal["normal", "affected", "breaking", "warning"] = "normal"
    details: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str

class BlastRadiusGraphResponse(BaseModel):
    project_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    affected_node_ids: List[str] = Field(default_factory=list)

class NodeExecutionTrace(BaseModel):
    node_name: str
    label: str
    duration_ms: float
    status: Literal["completed", "running", "skipped"] = "completed"
    summary: str

class AgentQueryRequest(BaseModel):
    query: str
    context_report_id: Optional[str] = None
    change_type: Optional[str] = None
    field_name: Optional[str] = None
    endpoint_path: Optional[str] = None

class AgentQueryResponse(BaseModel):
    query: str
    answer: str
    compatibility_code: Optional[str] = None
    trace: List[NodeExecutionTrace] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)

class AgentGraphSpecNode(BaseModel):
    id: str
    label: str
    node_type: str
    description: str

class AgentGraphSpecEdge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None

class AgentGraphSpecResponse(BaseModel):
    graph_id: str
    framework: str = "LangGraph StateGraph"
    nodes: List[AgentGraphSpecNode]
    edges: List[AgentGraphSpecEdge]
