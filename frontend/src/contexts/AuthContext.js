import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the session first.
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      return;
    }
    const token = api.getToken();
    if (!token) { setLoading(false); return; }
    try {
      const data = await api.get('/auth/me');
      setUser(data);
    } catch {
      api.clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  const login = async (email, password) => {
    const data = await api.post('/auth/login', { email, password });
    api.setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  const signup = async (email, name, password) => {
    const data = await api.post('/auth/register', { email, name, password });
    api.setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  const handleOAuthSession = async (sessionId) => {
    const data = await api.post(`/auth/session?session_id=${sessionId}`, {});
    // The backend sets a cookie; also get user data for state
    const userData = await api.get('/auth/me');
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    try { await api.post('/auth/logout', {}); } catch {}
    api.clearToken();
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const data = await api.get('/auth/me');
      setUser(data);
    } catch {}
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, handleOAuthSession, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
