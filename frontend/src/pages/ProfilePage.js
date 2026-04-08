import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '' });
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    api.get('/profile/').then(p => { setProfile(p); setForm({ name: p.name || '', bio: p.bio || '', phone: p.phone || '', location: p.location || '' }); });
  }, []);

  const saveProfile = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      const updated = await api.patch('/profile/', form);
      setProfile(updated);
      setEditing(false);
      setMsg('Profile updated');
      refreshUser();
    } catch (e) { setErr(e.message); }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      await api.post('/auth/change-password', pwForm);
      setMsg('Password changed');
      setPwForm({ current_password: '', new_password: '' });
    } catch (e) { setErr(e.message); }
  };

  if (!profile) return <div className="p-6">Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6" data-testid="profile-page">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Profile</h1>
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>Back</Button>
      </div>
      {msg && <div className="p-2 bg-green-50 text-green-700 rounded text-sm" data-testid="profile-success">{msg}</div>}
      {err && <div className="p-2 bg-red-50 text-red-700 rounded text-sm" data-testid="profile-error">{err}</div>}

      <Card>
        <CardHeader className="flex flex-row justify-between items-center">
          <CardTitle className="text-base">Profile Info</CardTitle>
          {!editing && <Button variant="outline" size="sm" onClick={() => setEditing(true)} data-testid="edit-profile-btn">Edit</Button>}
        </CardHeader>
        <CardContent>
          {editing ? (
            <form onSubmit={saveProfile} className="space-y-3">
              <div><Label>Name</Label><Input data-testid="profile-name" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} /></div>
              <div><Label>Bio</Label><Textarea data-testid="profile-bio" value={form.bio} onChange={e => setForm(p => ({ ...p, bio: e.target.value }))} maxLength={500} /></div>
              <div><Label>Phone</Label><Input data-testid="profile-phone" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} /></div>
              <div><Label>Location</Label><Input data-testid="profile-location" value={form.location} onChange={e => setForm(p => ({ ...p, location: e.target.value }))} /></div>
              <div className="flex gap-2">
                <Button type="submit" data-testid="save-profile-btn">Save</Button>
                <Button type="button" variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </form>
          ) : (
            <div className="space-y-2 text-sm" data-testid="profile-view">
              <p><span className="text-gray-500">Email:</span> {profile.email}</p>
              <p><span className="text-gray-500">Name:</span> {profile.name}</p>
              <p><span className="text-gray-500">Bio:</span> {profile.bio || '-'}</p>
              <p><span className="text-gray-500">Phone:</span> {profile.phone || '-'}</p>
              <p><span className="text-gray-500">Location:</span> {profile.location || '-'}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
          <CardHeader><CardTitle className="text-base">Change Password</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={changePassword} className="space-y-3">
              <div><Label>Current Password</Label><Input data-testid="current-password" value={pwForm.current_password} onChange={e => setPwForm(p => ({ ...p, current_password: e.target.value }))} type="password" required /></div>
              <div><Label>New Password (8+)</Label><Input data-testid="new-password" value={pwForm.new_password} onChange={e => setPwForm(p => ({ ...p, new_password: e.target.value }))} type="password" required minLength={8} /></div>
              <Button type="submit" data-testid="change-password-btn">Change Password</Button>
            </form>
          </CardContent>
        </Card>
    </div>
  );
}
