import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
function googleLogin() {
  const redirectUrl = window.location.origin + '/';
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
}

export function AuthCallback() {
  const { handleOAuthSession } = useAuth();
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;
    const hash = window.location.hash;
    const sessionId = new URLSearchParams(hash.substring(1)).get('session_id');
    if (sessionId) {
      handleOAuthSession(sessionId)
        .then(() => navigate('/', { replace: true }))
        .catch(() => navigate('/auth', { replace: true }));
    } else {
      navigate('/auth', { replace: true });
    }
  }, [handleOAuthSession, navigate]);

  return <div className="flex items-center justify-center h-screen"><p>Signing in...</p></div>;
}

export default function AuthPage() {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [signupForm, setSignupForm] = useState({ email: '', name: '', password: '' });

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(loginForm.email, loginForm.password);
      navigate('/');
    } catch (err) { setError(err.message); }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await signup(signupForm.email, signupForm.name, signupForm.password);
      navigate('/');
    } catch (err) { setError(err.message); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4" data-testid="auth-page">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-xl text-center">A Good Life</CardTitle>
        </CardHeader>
        <CardContent>
          {error && <div className="mb-4 p-2 bg-red-50 text-red-700 rounded text-sm" data-testid="auth-error">{error}</div>}
          <Tabs defaultValue="login">
            <TabsList className="w-full mb-4">
              <TabsTrigger value="login" className="flex-1" data-testid="login-tab">Login</TabsTrigger>
              <TabsTrigger value="signup" className="flex-1" data-testid="signup-tab">Sign Up</TabsTrigger>
            </TabsList>
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-3">
                <div><Label>Email</Label><Input data-testid="login-email" value={loginForm.email} onChange={e => setLoginForm(p => ({ ...p, email: e.target.value }))} type="email" required /></div>
                <div><Label>Password</Label><Input data-testid="login-password" value={loginForm.password} onChange={e => setLoginForm(p => ({ ...p, password: e.target.value }))} type="password" required /></div>
                <Button type="submit" className="w-full" data-testid="login-submit">Login</Button>
              </form>
            </TabsContent>
            <TabsContent value="signup">
              <form onSubmit={handleSignup} className="space-y-3">
                <div><Label>Name</Label><Input data-testid="signup-name" value={signupForm.name} onChange={e => setSignupForm(p => ({ ...p, name: e.target.value }))} required /></div>
                <div><Label>Email</Label><Input data-testid="signup-email" value={signupForm.email} onChange={e => setSignupForm(p => ({ ...p, email: e.target.value }))} type="email" required /></div>
                <div><Label>Password (8+ chars)</Label><Input data-testid="signup-password" value={signupForm.password} onChange={e => setSignupForm(p => ({ ...p, password: e.target.value }))} type="password" required minLength={8} /></div>
                <Button type="submit" className="w-full" data-testid="signup-submit">Sign Up</Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter className="flex-col gap-2">
          <div className="text-xs text-gray-400 w-full text-center">or</div>
          <Button variant="outline" className="w-full" onClick={googleLogin} data-testid="google-login-btn">Sign in with Google</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
