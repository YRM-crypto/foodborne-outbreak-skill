import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import CasesView from "./views/CasesView";
import KnowledgeView from "./views/KnowledgeView";
import WorkspaceView from "./views/WorkspaceView";
import ReportView from "./views/ReportView";
import AssistantView from "./views/AssistantView";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/cases" replace />} />
          <Route path="/cases" element={<CasesView />} />
          <Route path="/knowledge" element={<KnowledgeView />} />
          <Route path="/workspace" element={<WorkspaceView />} />
          <Route path="/report" element={<ReportView />} />
          <Route path="/assistant" element={<AssistantView />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}
