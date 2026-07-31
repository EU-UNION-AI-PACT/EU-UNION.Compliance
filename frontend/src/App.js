import React from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { Layout } from "./components/Layout";
import Landing from "./pages/Landing";
import ConceptPaper from "./pages/ConceptPaper";
import Sandbox from "./pages/Sandbox";
import Compliance from "./pages/Compliance";
import TrustPipeline from "./pages/TrustPipeline";
import Federation from "./pages/Federation";
import DeveloperHub from "./pages/DeveloperHub";
import AdminPortal from "./pages/AdminPortal";
import PNIARegistry from "./pages/PNIARegistry";
import PNIAMemorial from "./pages/PNIAMemorial";
import PNIAConcept from "./pages/PNIAConcept";
import HNOSSBridge from "./pages/HNOSSBridge";
import Governance from "./pages/Governance";
import PNIACompliance from "./pages/PNIACompliance";
import IdentityBroker from "./pages/IdentityBroker";
import ComplianceValidator from "./pages/ComplianceValidator";
import Blueprint from "./pages/Blueprint";
import { AuthProvider, AuthCallback } from "./lib/auth";
import "./i18n";
import "./App.css";

function AppRouter() {
  const location = useLocation();
  // Emergent Google Auth callback — must run BEFORE regular routes render
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/paper" element={<ConceptPaper />} />
        <Route path="/paper/:slug" element={<ConceptPaper />} />
        <Route path="/sandbox" element={<Sandbox />} />
        <Route path="/compliance" element={<Compliance />} />
        <Route path="/trust" element={<TrustPipeline />} />
        <Route path="/federation" element={<Federation />} />
        <Route path="/hub" element={<DeveloperHub />} />
        <Route path="/pnia-registry" element={<PNIARegistry />} />
        <Route path="/pnia-memorial/:id" element={<PNIAMemorial />} />
        <Route path="/pnia-concept" element={<PNIAConcept />} />
        <Route path="/hnoss-bridge" element={<HNOSSBridge />} />
        <Route path="/governance" element={<Governance />} />
        <Route path="/pnia-compliance" element={<PNIACompliance />} />
        <Route path="/identity-broker" element={<IdentityBroker />} />
        <Route path="/validator" element={<ComplianceValidator />} />
        <Route path="/blueprint" element={<Blueprint />} />
        <Route path="/mesh-catalog" element={<Sandbox />} />
        <Route path="/uce" element={<Sandbox />} />
        <Route path="/admin" element={<AdminPortal />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="bottom-right"
          theme="dark"
          toastOptions={{
            style: {
              background: "#0a0f19",
              color: "#e5e7eb",
              border: "1px solid rgba(245,158,11,0.3)",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "12px",
            },
          }}
        />
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
