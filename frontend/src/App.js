import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { Toaster } from '@/components/ui/sonner';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

import HomePage from '@/pages/HomePage';
import AuthPage, { AuthCallback } from '@/pages/AuthPage';
import CommunitiesPage from '@/pages/CommunitiesPage';
import CommunityHome from '@/pages/CommunityHome';
import CommunityDiscussions from '@/pages/CommunityDiscussions';
import ThreadDetail from '@/pages/ThreadDetail';
import CreateThread from '@/pages/CreateThread';
import CommunityEvents from '@/pages/CommunityEvents';
import CommunityMembers from '@/pages/CommunityMembers';
import ProfilePage from '@/pages/ProfilePage';
import ManagerDashboard from '@/pages/manager/ManagerDashboard';
import ManagerJoinRequests from '@/pages/manager/ManagerJoinRequests';
import ManagerCategories from '@/pages/manager/ManagerCategories';
import ManagerCreateEvent from '@/pages/manager/ManagerCreateEvent';
import ManagerModeration from '@/pages/manager/ManagerModeration';

import '@/App.css';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  if (!user) return <Navigate to="/auth" replace />;
  return children;
}

function AppContent() {
  const location = useLocation();
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          {/* Public */}
          <Route path="/" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/communities" element={<CommunitiesPage />} />

          {/* Community (public viewable for public communities) */}
          <Route path="/community/:slug" element={<CommunityHome />} />
          <Route path="/community/:slug/discussions" element={<CommunityDiscussions />} />
          <Route path="/community/:slug/discussions/:categoryId" element={<CommunityDiscussions />} />
          <Route path="/community/:slug/thread/:threadId" element={<ThreadDetail />} />
          <Route path="/community/:slug/events" element={<CommunityEvents />} />
          <Route path="/community/:slug/members" element={<CommunityMembers />} />

          {/* Protected: requires auth */}
          <Route path="/community/:slug/create-thread" element={<ProtectedRoute><CreateThread /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />

          {/* Manager routes */}
          <Route path="/community/:slug/manage" element={<ProtectedRoute><ManagerDashboard /></ProtectedRoute>} />
          <Route path="/community/:slug/manage/join-requests" element={<ProtectedRoute><ManagerJoinRequests /></ProtectedRoute>} />
          <Route path="/community/:slug/manage/categories" element={<ProtectedRoute><ManagerCategories /></ProtectedRoute>} />
          <Route path="/community/:slug/manage/create-event" element={<ProtectedRoute><ManagerCreateEvent /></ProtectedRoute>} />
          <Route path="/community/:slug/manage/moderation" element={<ProtectedRoute><ManagerModeration /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
      <Toaster position="top-center" />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
