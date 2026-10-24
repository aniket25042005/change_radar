import React, { useEffect, useState } from "react";
import { Header } from "./components/Header";
import { UploadPanel } from "./components/UploadPanel";
import { EndpointList } from "./components/EndpointList";
import { BlastRadiusGraph } from "./components/BlastRadiusGraph";
import { ChangeSimulator } from "./components/ChangeSimulator";
import { ImpactReport } from "./components/ImpactReport";
import { MigrationPatchModal } from "./components/MigrationPatchModal";
import { ReportHistory } from "./components/ReportHistory";
import { StatusMessage } from "./components/StatusMessage";
import { LangGraphWorkspace } from "./components/LangGraphWorkspace";
import {
  AnalyzePayload,
  BlastRadiusGraphResponse,
  deleteProject,
  EndpointInfo,
  fetchBlastRadiusGraph,
  fetchEndpoints,
  fetchProjects,
  fetchReports,
  ImpactReport as ImpactReportType,
  loadSampleProject,
  Project,
  PydanticSchemaInfo,
  runImpactAnalysis,
} from "./api/client";

export const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [showUpload, setShowUpload] = useState<boolean>(false);
  const [showAgentStudio, setShowAgentStudio] = useState<boolean>(false);

  // Scanned project data
  const [endpoints, setEndpoints] = useState<EndpointInfo[]>([]);
  const [schemas, setSchemas] = useState<PydanticSchemaInfo[]>([]);
  const [graph, setGraph] = useState<BlastRadiusGraphResponse | null>(null);
  const [reportsHistory, setReportsHistory] = useState<any[]>([]);

  // Current analysis state
  const [currentReport, setCurrentReport] = useState<ImpactReportType | null>(null);
  const [showPatchModal, setShowPatchModal] = useState<boolean>(false);

  // UI state
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingSample, setLoadingSample] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "error" | "success" | "info"; text: string } | null>(null);

  // Prefill states for ChangeSimulator
  const [prefillEndpoint, setPrefillEndpoint] = useState<EndpointInfo | null>(null);
  const [prefillField, setPrefillField] = useState<{ model: string; field: string } | null>(null);

  // Load project list on initial render
  useEffect(() => {
    loadProjectsList();
  }, []);

  const loadProjectsList = async () => {
    try {
      const list = await fetchProjects();
      setProjects(list);
      if (list.length > 0) {
        selectProject(list[0]);
      } else {
        setShowUpload(true);
      }
    } catch (err: any) {
      setStatusMsg({ type: "error", text: "Failed to connect to ChangeRadar backend. Ensure FastAPI server is running on port 8000." });
    }
  };

  const selectProject = async (proj: Project) => {
    setActiveProject(proj);
    setShowUpload(false);
    setCurrentReport(null);
    setPrefillEndpoint(null);
    setPrefillField(null);
    setLoading(true);

    try {
      const epData = await fetchEndpoints(proj.id);
      setEndpoints(epData.endpoints);
      setSchemas(epData.schemas);

      const graphData = await fetchBlastRadiusGraph(proj.id);
      setGraph(graphData);

      const reps = await fetchReports(proj.id);
      setReportsHistory(reps);
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to load project details." });
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async () => {
    setLoadingSample(true);
    setStatusMsg(null);
    try {
      const sampleProj = await loadSampleProject();
      setProjects((prev) => [sampleProj, ...prev]);
      await selectProject(sampleProj);
      setStatusMsg({ type: "success", text: "Demo Store project (FastAPI + React/TS) loaded successfully!" });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to load demo sample." });
    } finally {
      setLoadingSample(false);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!window.confirm("Are you sure you want to delete this project and its stored reports?")) return;
    try {
      await deleteProject(projectId);
      const remaining = projects.filter((p) => p.id !== projectId);
      setProjects(remaining);
      if (remaining.length > 0) {
        selectProject(remaining[0]);
      } else {
        setActiveProject(null);
        setEndpoints([]);
        setSchemas([]);
        setGraph(null);
        setShowUpload(true);
      }
      setStatusMsg({ type: "info", text: "Project deleted successfully." });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to delete project." });
    }
  };

  const handleRunAnalysis = async (payload: AnalyzePayload) => {
    if (!activeProject) return;
    setLoading(true);
    setStatusMsg(null);
    try {
      const report = await runImpactAnalysis(activeProject.id, payload);
      setCurrentReport(report);

      // Re-fetch graph with active affected field/endpoint highlighted
      const field = payload.field_name || "";
      const ep = payload.endpoint_id || "";
      const updatedGraph = await fetchBlastRadiusGraph(activeProject.id, field, ep);
      setGraph(updatedGraph);

      // Re-fetch reports history
      const updatedReps = await fetchReports(activeProject.id);
      setReportsHistory(updatedReps);

      setStatusMsg({
        type: report.risk_level === "Breaking" ? "error" : "success",
        text: `Analysis complete: ${report.risk_level} impact identified (${report.affected_files.length} consumers affected).`,
      });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to complete impact analysis." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <Header
        projects={projects}
        activeProject={activeProject}
        onSelectProject={selectProject}
        onDeleteProject={handleDeleteProject}
        onLoadSample={handleLoadSample}
        onOpenUpload={() => setShowUpload(true)}
        onOpenAgentStudio={() => setShowAgentStudio(true)}
        loadingSample={loadingSample}
      />

      {/* Global Status Message */}
      {statusMsg && (
        <StatusMessage
          type={statusMsg.type}
          message={statusMsg.text}
          onClose={() => setStatusMsg(null)}
        />
      )}

      {/* Upload View (Modal / Toggle) */}
      {showUpload && (
        <UploadPanel
          onUploadSuccess={(proj) => {
            setProjects((prev) => [proj, ...prev]);
            selectProject(proj);
          }}
          onLoadSample={handleLoadSample}
          loadingSample={loadingSample}
        />
      )}

      {/* Main Workspace */}
      {activeProject && !showUpload && (
        <>
          {/* Top Section: Interactive Blast Radius Visual Graph */}
          <BlastRadiusGraph
            graph={graph}
            loading={loading}
            onRefresh={() => fetchBlastRadiusGraph(activeProject.id).then(setGraph)}
          />

          {/* 2-Column Grid */}
          <div className="main-grid">
            {/* Left Column: Endpoints & Schemas Inventory + Report History */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <EndpointList
                endpoints={endpoints}
                schemas={schemas}
                onSelectEndpointForChange={(ep) => setPrefillEndpoint(ep)}
                onSelectFieldForChange={(model, field) => setPrefillField({ model, field })}
              />

              <ReportHistory
                reports={reportsHistory}
                onSelectReport={(rep) => setCurrentReport(rep)}
              />
            </div>

            {/* Right Column: Simulator & Impact Report */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <ChangeSimulator
                endpoints={endpoints}
                schemas={schemas}
                onRunAnalysis={handleRunAnalysis}
                loading={loading}
                prefillEndpoint={prefillEndpoint}
                prefillField={prefillField}
              />

              {currentReport && (
                <ImpactReport
                  report={currentReport}
                  onOpenPatchModal={() => setShowPatchModal(true)}
                />
              )}
            </div>
          </div>
        </>
      )}

      {/* 1-Click Migration Patch Modal */}
      {showPatchModal && currentReport?.migration_patch && (
        <MigrationPatchModal
          patch={currentReport.migration_patch}
          projectId={activeProject?.id}
          onClose={() => setShowPatchModal(false)}
        />
      )}

      {/* Standalone LangGraph Agent Studio Modal */}
      {showAgentStudio && activeProject && (
        <div
          className="modal-backdrop"
          onClick={() => setShowAgentStudio(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
        >
          <div
            style={{ maxWidth: "1000px", width: "100%", maxHeight: "90vh", overflowY: "auto" }}
            onClick={(e) => e.stopPropagation()}
          >
            <LangGraphWorkspace
              projectId={activeProject.id}
              contextReportId={currentReport?.report_id}
              changeType={currentReport?.change_type}
              fieldName={currentReport?.change_summary}
              onClose={() => setShowAgentStudio(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

