export interface Project {
  id: string;
  name: string;
  created_at: string;
  file_count: number;
  detected_tech: {
    backend?: string;
    frontend?: string;
    python_files?: number;
    typescript_files?: number;
    test_files?: number;
    total_scanned_files?: number;
  };
  status: string;
}

export interface EndpointInfo {
  id: string;
  method: string;
  path: string;
  function_name: string;
  file_path: string;
  line_number: number;
  response_model?: string;
  request_model?: string;
  parameters: Array<{ name: string; type: string }>;
  router_prefix?: string;
}

export interface PydanticFieldInfo {
  name: string;
  type_annotation: string;
  line_number?: number;
  required: boolean;
}

export interface PydanticSchemaInfo {
  name: string;
  file_path: string;
  line_number: number;
  fields: PydanticFieldInfo[];
}

export interface DiscoveredEndpointsResponse {
  project_id: string;
  endpoints: EndpointInfo[];
  schemas: PydanticSchemaInfo[];
}

export interface EvidenceItem {
  file_path: string;
  line_number?: number;
  matched_symbol: string;
  code_snippet: string;
  reason: string;
  category: "component" | "type_definition" | "api_client" | "test" | "other";
}

export interface ImpactReport {
  report_id: string;
  project_id: string;
  created_at: string;
  change_summary: string;
  change_type: string;
  confidence: "High" | "Medium" | "Low";
  confidence_score: number;
  risk_level: "Breaking" | "Warning" | "Informational";
  affected_files: EvidenceItem[];
  relevant_tests: EvidenceItem[];
  suggested_tests: string[];
  limitations: string[];
  migration_patch?: string | null;
  agentic_insights?: AgenticInsights | null;
}

export interface AgenticInsights {
  architectural_assessment: string;
  human_migration_guide: string;
  compat_code?: string | null;
  pr_review_comment: string;
  autonomous_next_steps: string[];
  trace?: NodeExecutionTrace[];
}

export interface NodeExecutionTrace {
  node_name: string;
  label: string;
  duration_ms: number;
  status: "completed" | "running" | "skipped";
  summary: string;
}

export interface AgentQueryRequest {
  query: string;
  context_report_id?: string;
  change_type?: string;
  field_name?: string;
  endpoint_path?: string;
}

export interface AgentQueryResponse {
  query: string;
  answer: string;
  compatibility_code?: string | null;
  trace: NodeExecutionTrace[];
  suggested_followups: string[];
}

export interface AgentGraphSpecNode {
  id: string;
  label: string;
  node_type: string;
  description: string;
}

export interface AgentGraphSpecEdge {
  source: string;
  target: string;
  condition?: string;
}

export interface AgentGraphSpecResponse {
  graph_id: string;
  framework: string;
  nodes: AgentGraphSpecNode[];
  edges: AgentGraphSpecEdge[];
}

export interface OllamaStatusResponse {
  online: boolean;
  base_url: string;
  default_model: string;
  available_models: string[];
  message: string;
}


export interface GraphNode {
  id: string;
  label: string;
  node_type: "route" | "schema" | "field" | "type" | "client" | "component" | "test";
  status: "normal" | "affected" | "breaking" | "warning";
  details: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
}

export interface BlastRadiusGraphResponse {
  project_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  affected_node_ids: string[];
}

export interface AnalyzePayload {
  change_type: "remove_field" | "rename_field" | "change_field_type" | "change_route" | "change_http_method" | "git_diff";
  endpoint_id?: string;
  model_name?: string;
  field_name?: string;
  new_field_name?: string;
  new_field_type?: string;
  new_path?: string;
  new_method?: string;
  git_diff?: string;
}

const BASE_URL = "";

export async function fetchHealth(): Promise<{ status: string; app: string; local_mode: boolean }> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error("Backend offline or unreachable");
  return res.json();
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${BASE_URL}/api/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function uploadProject(file: File): Promise<Project> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/api/projects/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Failed to upload project ZIP");
  }
  return res.json();
}

export async function loadSampleProject(): Promise<Project> {
  const res = await fetch(`${BASE_URL}/api/projects/sample`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Sample load failed" }));
    throw new Error(err.detail || "Failed to load sample project");
  }
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete project");
}

export async function fetchEndpoints(projectId: string): Promise<DiscoveredEndpointsResponse> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/endpoints`);
  if (!res.ok) throw new Error("Failed to fetch endpoints");
  return res.json();
}

export async function fetchBlastRadiusGraph(
  projectId: string,
  field: string = "",
  endpoint: string = ""
): Promise<BlastRadiusGraphResponse> {
  const params = new URLSearchParams();
  if (field) params.append("field", field);
  if (endpoint) params.append("endpoint", endpoint);
  const url = `${BASE_URL}/api/projects/${projectId}/graph?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch blast radius graph");
  return res.json();
}

export async function runImpactAnalysis(projectId: string, payload: AnalyzePayload): Promise<ImpactReport> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(err.detail || "Failed to run impact analysis");
  }
  return res.json();
}

export async function fetchReports(projectId: string): Promise<any[]> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/reports`);
  if (!res.ok) throw new Error("Failed to fetch report history");
  return res.json();
}

export async function applyPatch(
  projectId: string,
  patch: string
): Promise<{ success: boolean; backup_id: string; modified_files: string[]; message: string }> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/apply-patch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patch }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Apply patch failed" }));
    throw new Error(err.detail || "Failed to apply migration patch");
  }
  return res.json();
}

export async function revertPatch(
  projectId: string,
  backupId: string
): Promise<{ success: boolean; restored_files: string[]; message: string }> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/revert-patch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ backup_id: backupId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Revert patch failed" }));
    throw new Error(err.detail || "Failed to revert migration patch");
  }
  return res.json();
}

export async function fetchAgentGraphSpec(projectId: string): Promise<AgentGraphSpecResponse> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/agent-graph-spec`);
  if (!res.ok) throw new Error("Failed to fetch LangGraph agent specification");
  return res.json();
}

export async function fetchOllamaStatus(): Promise<OllamaStatusResponse> {
  const res = await fetch(`${BASE_URL}/api/ollama/status`);
  if (!res.ok) throw new Error("Failed to check Ollama status");
  return res.json();
}

export async function queryAgentCopilot(
  projectId: string,
  payload: AgentQueryRequest
): Promise<AgentQueryResponse> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/agent-query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Agent query failed" }));
    throw new Error(err.detail || "Failed to query LangGraph agent");
  }
  return res.json();
}
