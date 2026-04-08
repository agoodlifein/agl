import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function AuthCallback() {
  const { handleOAuthSession } = useAuth();
  const navigate = useNavigate();
  const hash = window.location.hash;
  const sessionId = new URLSearchParams(hash.replace('#', '?')).get('session_id');

  React.useEffect(() => {
    if (sessionId) {
      handleOAuthSession(sessionId)
        .then(() => {
          window.location.hash = '';
          navigate('/', { replace: true });
        })
        .catch(() => {
          toast.error('OAuth login failed');
          navigate('/auth', { replace: true });
        });
    }
  }, [sessionId, handleOAuthSession, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-muted-foreground">Completing sign in...</div>
    </div>
  );
}

export default function AuthPage() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, signup, user } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (user) navigate('/', { replace: true });
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === 'login') {
        await login(email, password);
        toast.success('Welcome back!');
      } else {
        await signup(email, name, password);
        toast.success('Account created!');
      }
      navigate('/');
    } catch (error) {
      toast.error(error.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const currentUrl = window.location.origin;
    window.location.href = `${API_URL}/api/auth/session?redirect_url=${encodeURIComponent(currentUrl)}`;
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-6" data-testid="auth-page">
      <div className="w-full max-w-md">
        <div className="bg-card border border-border rounded-xl p-8 shadow-sm">
          <div className="text-center mb-8">
            <h1 className="text-2xl sm:text-3xl font-heading font-light tracking-tight mb-2 text-title" data-testid="auth-title">
              {mode === 'login' ? 'Welcome Back' : 'Join A Good Life'}
            </h1>
            <p className="text-sm text-muted-foreground">
              {mode === 'login' ? 'Sign in to your account' : 'Create your account to get started'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {mode === 'signup' && (
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required data-testid="name-input" placeholder="Your name" />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required data-testid="email-input" placeholder="your@email.com" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required data-testid="password-input" placeholder={mode === 'signup' ? 'Min 8 characters' : ''} />
            </div>
            <Button type="submit" className="w-full" disabled={loading} data-testid="auth-submit-button">
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border" /></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">or</span></div>
          </div>

          <Button variant="outline" className="w-full" onClick={handleGoogleLogin} data-testid="google-login-button">
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
            Continue with Google
          </Button>

          <div className="mt-4 text-center text-sm text-muted-foreground">
            {mode === 'login' ? (
              <>Not a member yet?{' '}<button onClick={() => setMode('signup')} className="text-primary font-medium hover:underline" data-testid="switch-to-signup">Create Account</button></>
            ) : (
              <>Already have an account?{' '}<button onClick={() => setMode('login')} className="text-primary font-medium hover:underline" data-testid="switch-to-login">Sign In</button></>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
