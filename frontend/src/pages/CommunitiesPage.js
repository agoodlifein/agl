import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';

export default function CommunitiesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.is_super_admin;
  const [communities, setCommunities] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', slug: '', description: '', privacy: 'public' });
  const [assignForm, setAssignForm] = useState({ slug: '', user_id: '' });
  const [users, setUsers] = useState([]);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  const load = () => api.get('/communities/').then(setCommunities).catch(() => {});

  useEffect(() => {
    load();
    if (isAdmin) api.get('/profiles/').then(setUsers).catch(() => {});
  }, [isAdmin]);

  const createCommunity = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      await api.post('/communities/', createForm);
      setMsg('Community created');
      setShowCreate(false);
      setCreateForm({ name: '', slug: '', description: '', privacy: 'public' });
      load();
    } catch (e) { setErr(e.message); }
  };

  const changeStatus = async (slug, action) => {
    setErr(''); setMsg('');
    try {
      await api.post(`/admin/communities/${slug}/${action}`, {});
      setMsg(`Community ${action}d`);
      load();
    } catch (e) { setErr(e.message); }
  };

  const assignManager = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      const res = await api.post(`/admin/communities/${assignForm.slug}/assign-manager`, { user_id: assignForm.user_id });
      setMsg(res.message);
      setAssignForm({ slug: '', user_id: '' });
    } catch (e) { setErr(e.message); }
  };

  const statusColor = (s) => s === 'active' ? 'default' : s === 'paused' ? 'secondary' : 'destructive';

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6" data-testid="communities-page">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Communities</h1>
        <div className="flex gap-2">
          {isAdmin && <Button size="sm" onClick={() => setShowCreate(!showCreate)} data-testid="create-community-btn">{showCreate ? 'Cancel' : 'Create Community'}</Button>}
          <Button variant="ghost" size="sm" onClick={() => navigate('/')}>Back</Button>
        </div>
      </div>
      {msg && <div className="p-2 bg-green-50 text-green-700 rounded text-sm" data-testid="communities-success">{msg}</div>}
      {err && <div className="p-2 bg-red-50 text-red-700 rounded text-sm" data-testid="communities-error">{err}</div>}

      {showCreate && isAdmin && (
        <Card>
          <CardHeader><CardTitle className="text-base">Create Community</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={createCommunity} className="space-y-3">
              <div><Label>Name</Label><Input data-testid="comm-name" value={createForm.name} onChange={e => setCreateForm(p => ({ ...p, name: e.target.value }))} required /></div>
              <div><Label>Slug (lowercase, hyphens)</Label><Input data-testid="comm-slug" value={createForm.slug} onChange={e => setCreateForm(p => ({ ...p, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') }))} required /></div>
              <div><Label>Description</Label><Textarea data-testid="comm-desc" value={createForm.description} onChange={e => setCreateForm(p => ({ ...p, description: e.target.value }))} required /></div>
              <div>
                <Label>Privacy</Label>
                <Select value={createForm.privacy} onValueChange={v => setCreateForm(p => ({ ...p, privacy: v }))}>
                  <SelectTrigger data-testid="comm-privacy"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">Public</SelectItem>
                    <SelectItem value="private">Private</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" data-testid="submit-create-community">Create</Button>
            </form>
          </CardContent>
        </Card>
      )}

      {isAdmin && (
        <Card>
          <CardHeader><CardTitle className="text-base">Assign Community Manager</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={assignManager} className="flex gap-2 items-end flex-wrap">
              <div>
                <Label>Community</Label>
                <Select value={assignForm.slug} onValueChange={v => setAssignForm(p => ({ ...p, slug: v }))}>
                  <SelectTrigger className="w-48" data-testid="assign-community-select"><SelectValue placeholder="Select" /></SelectTrigger>
                  <SelectContent>
                    {communities.map(c => <SelectItem key={c.slug} value={c.slug}>{c.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>User</Label>
                <Select value={assignForm.user_id} onValueChange={v => setAssignForm(p => ({ ...p, user_id: v }))}>
                  <SelectTrigger className="w-48" data-testid="assign-user-select"><SelectValue placeholder="Select" /></SelectTrigger>
                  <SelectContent>
                    {users.filter(u => !u.is_super_admin).map(u => <SelectItem key={u.user_id} value={u.user_id}>{u.name} ({u.email})</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" data-testid="assign-manager-btn">Assign</Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2">
        {communities.map(c => (
          <Card key={c.community_id} className="hover:shadow-sm transition-shadow">
            <CardContent className="p-4 flex justify-between items-center">
              <div>
                <Link to={`/communities/${c.slug}`} className="font-medium hover:underline" data-testid={`community-link-${c.slug}`}>{c.name}</Link>
                <p className="text-sm text-gray-500 line-clamp-1">{c.description}</p>
                <div className="flex gap-1 mt-1">
                  <Badge variant={statusColor(c.status)}>{c.status}</Badge>
                  <Badge variant="outline">{c.privacy}</Badge>
                </div>
              </div>
              {isAdmin && (
                <div className="flex gap-1 flex-shrink-0">
                  {c.status !== 'active' && <Button size="sm" variant="outline" onClick={() => changeStatus(c.slug, 'activate')} data-testid={`activate-${c.slug}`}>Activate</Button>}
                  {c.status === 'active' && <Button size="sm" variant="outline" onClick={() => changeStatus(c.slug, 'pause')} data-testid={`pause-${c.slug}`}>Pause</Button>}
                  {c.status !== 'disabled' && <Button size="sm" variant="destructive" onClick={() => changeStatus(c.slug, 'disable')} data-testid={`disable-${c.slug}`}>Disable</Button>}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
        {communities.length === 0 && <p className="text-gray-500 text-sm">No communities yet.</p>}
      </div>
    </div>
  );
}
