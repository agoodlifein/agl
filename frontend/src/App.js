import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import AuthPage, { AuthCallback } from "@/pages/AuthPage";
import Dashboard from "@/pages/Dashboard";
import ProfilePage from "@/pages/ProfilePage";
import CommunitiesPage from "@/pages/CommunitiesPage";
import CommunityPage from "@/pages/CommunityPage";
import DiscussionPage from "@/pages/DiscussionPage";
import EventPage from "@/pages/EventPage";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (!user) return <Navigate to="/auth" replace />;
  return children;
}

function AppRouter() {
  const location = useLocation();
  // Check URL fragment for session_id synchronously (prevents race conditions)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      <Route path="/communities" element={<ProtectedRoute><CommunitiesPage /></ProtectedRoute>} />
      <Route path="/communities/:slug" element={<ProtectedRoute><CommunityPage /></ProtectedRoute>} />
      <Route path="/communities/:slug/discussions/:threadId" element={<ProtectedRoute><DiscussionPage /></ProtectedRoute>} />
      <Route path="/communities/:slug/events/:eventId" element={<ProtectedRoute><EventPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
