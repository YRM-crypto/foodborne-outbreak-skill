import { Spin } from "antd";
import { Suspense, lazy } from "react";
import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layout/AppLayout";

const CasesView = lazy(() => import("./views/CasesView"));
const KnowledgeView = lazy(() => import("./views/KnowledgeView"));
const WorkspaceView = lazy(() => import("./views/WorkspaceView"));
const ReportView = lazy(() => import("./views/ReportView"));
const AssistantView = lazy(() => import("./views/AssistantView"));

export default function App() {
  return (
    <HashRouter>
      <Suspense fallback={<Spin style={{ display: "block", margin: "80px auto" }} />}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/cases" replace />} />
            <Route path="/cases" element={<CasesView />} />
            <Route path="/knowledge" element={<KnowledgeView />} />
            <Route path="/workspace" element={<Navigate to="/cases" replace />} />
            <Route path="/workspace/:eventId" element={<WorkspaceView />} />
            <Route path="/report" element={<ReportView />} />
            <Route path="/assistant" element={<AssistantView />} />
          </Route>
        </Routes>
      </Suspense>
    </HashRouter>
  );
}
