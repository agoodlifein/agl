import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';

export default function CommunityPage() {
  const { slug } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [community, setCommunity] = useState(null);
  const [membership, setMembership] = useState(null);
  const [threads, setThreads] = useState([]);
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  const isAdmin = user?.is_super_admin;
  const isManager = membership?.role === 'community_manager' || isAdmin;
  const isMember = membership?.is_member || isAdmin;

  const load = useCallback(async () => {
    try {
      const [c, m] = await Promise.all([
        api.get(`/communities/${slug}`),
        api.get(`/communities/${slug}/membership-status`),
      ]);
      setCommunity(c);
      setMembership(m);
      // Load content
      const cats = await api.get(`/communities/${slug}/categories`).catch(() => []);
      setCategories(cats);
      if (isAdmin || m.is_member) {
        const [t, e] = await Promise.all([
          api.get(`/communities/${slug}/threads`).catch(() => []),
          isAdmin || m.role === 'community_manager'
            ? api.get(`/manager/communities/${slug}/events`).catch(() => [])
            : api.get(`/communities/${slug}/events`).catch(() => []),
        ]);
        setThreads(t);
        setEvents(e);
      }
    } catch (e) { setErr(e.message); }
  }, [slug, isAdmin]);

  useEffect(() => { load(); }, [load]);

  const joinCommunity = async () => {
    setErr(''); setMsg('');
    try {
      const res = await api.post(`/communities/${slug}/request-join`, {});
      setMsg(res.message);
      load();
    } catch (e) { setErr(e.message); }
  };

  // ===== Create Thread =====
  const [showCreateThread, setShowCreateThread] = useState(false);
  const [threadForm, setThreadForm] = useState({ title: '', content: '', category_id: '' });
  const createThread = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      await api.post(`/communities/${slug}/threads`, threadForm);
      setMsg('Thread created');
      setShowCreateThread(false);
      setThreadForm({ title: '', content: '', category_id: '' });
      const t = await api.get(`/communities/${slug}/threads`);
      setThreads(t);
    } catch (e) { setErr(e.message); }
  };

  // ===== Create Category (manager) =====
  const [catName, setCatName] = useState('');
  const createCategory = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      await api.post(`/manager/communities/${slug}/categories`, { name: catName });
      setMsg('Category created');
      setCatName('');
      const cats = await api.get(`/communities/${slug}/categories`);
      setCategories(cats);
    } catch (e) { setErr(e.message); }
  };

  // ===== Create Event (manager) =====
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [eventForm, setEventForm] = useState({ title: '', description: '', event_date: '', event_time: '', venue: '', status: 'published' });
  const createEvent = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      const body = { ...eventForm };
      if (!body.event_time) delete body.event_time;
      if (!body.venue) delete body.venue;
      await api.post(`/manager/communities/${slug}/events`, body);
      setMsg('Event created');
      setShowCreateEvent(false);
      setEventForm({ title: '', description: '', event_date: '', event_time: '', venue: '', status: 'published' });
      const ev = await api.get(`/manager/communities/${slug}/events`);
      setEvents(ev);
    } catch (e) { setErr(e.message); }
  };

  // ===== Edit Community (manager) =====
  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState({});
  const startEdit = () => {
    setEditForm({ name: community.name || '', intro_copy: community.intro_copy || '', welcome_text: community.welcome_text || '', accent_color: community.accent_color || '', privacy: community.privacy || 'public' });
    setShowEdit(true);
  };
  const saveEdit = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      const updated = await api.patch(`/manager/communities/${slug}`, editForm);
      setCommunity(updated);
      setMsg('Community updated');
      setShowEdit(false);
    } catch (e) { setErr(e.message); }
  };

  if (!community) return <div className="p-6">Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4" data-testid="community-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">{community.name}</h1>
          <p className="text-sm text-gray-500">{community.description}</p>
          <div className="flex gap-1 mt-1">
            <Badge>{community.status}</Badge>
            <Badge variant="outline">{community.privacy}</Badge>
            {membership?.role && <Badge variant="secondary">{membership.role}</Badge>}
          </div>
        </div>
        <div className="flex gap-2">
          {!isMember && !membership?.has_pending_request && <Button onClick={joinCommunity} data-testid="join-btn">Join</Button>}
          {membership?.has_pending_request && <Badge variant="secondary">Request Pending</Badge>}
          <Button variant="ghost" size="sm" onClick={() => navigate('/communities')}>Back</Button>
        </div>
      </div>
      {msg && <div className="p-2 bg-green-50 text-green-700 rounded text-sm" data-testid="community-success">{msg}</div>}
      {err && <div className="p-2 bg-red-50 text-red-700 rounded text-sm" data-testid="community-error">{err}</div>}

      <Tabs defaultValue="discussions">
        <TabsList>
          <TabsTrigger value="discussions" data-testid="discussions-tab">Discussions</TabsTrigger>
          <TabsTrigger value="events" data-testid="events-tab">Events</TabsTrigger>
          {isManager && <TabsTrigger value="settings" data-testid="settings-tab">Settings</TabsTrigger>}
        </TabsList>

        {/* ===== DISCUSSIONS TAB ===== */}
        <TabsContent value="discussions" className="space-y-4">
          {isMember && (
            <div className="flex gap-2">
              <Button size="sm" onClick={() => setShowCreateThread(!showCreateThread)} data-testid="new-thread-btn">
                {showCreateThread ? 'Cancel' : 'New Thread'}
              </Button>
            </div>
          )}

          {showCreateThread && (
            <Card>
              <CardContent className="pt-4">
                <form onSubmit={createThread} className="space-y-3">
                  <div><Label>Title</Label><Input data-testid="thread-title" value={threadForm.title} onChange={e => setThreadForm(p => ({ ...p, title: e.target.value }))} required /></div>
                  <div><Label>Content</Label><Textarea data-testid="thread-content" value={threadForm.content} onChange={e => setThreadForm(p => ({ ...p, content: e.target.value }))} required /></div>
                  <div>
                    <Label>Category</Label>
                    <Select value={threadForm.category_id} onValueChange={v => setThreadForm(p => ({ ...p, category_id: v }))}>
                      <SelectTrigger data-testid="thread-category"><SelectValue placeholder="Select category" /></SelectTrigger>
                      <SelectContent>
                        {categories.map(c => <SelectItem key={c.category_id} value={c.category_id}>{c.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button type="submit" data-testid="submit-thread">Create Thread</Button>
                </form>
              </CardContent>
            </Card>
          )}

          {categories.length > 0 && (
            <div className="flex gap-1 flex-wrap">
              <span className="text-xs text-gray-500 self-center">Categories:</span>
              {categories.map(c => <Badge key={c.category_id} variant="outline">{c.name} ({c.thread_count})</Badge>)}
            </div>
          )}

          <div className="space-y-1">
            {threads.map(t => (
              <Link key={t.thread_id} to={`/communities/${slug}/discussions/${t.thread_id}`} className="block p-3 border rounded hover:bg-gray-50" data-testid={`thread-${t.thread_id}`}>
                <div className="flex justify-between">
                  <span className="font-medium">{t.title}</span>
                  <span className="text-xs text-gray-400">{t.reply_count} replies</span>
                </div>
                <p className="text-xs text-gray-500">by {t.author_name} · {new Date(t.created_at).toLocaleDateString()}</p>
              </Link>
            ))}
            {threads.length === 0 && <p className="text-sm text-gray-400">No discussions yet.</p>}
          </div>
        </TabsContent>

        {/* ===== EVENTS TAB ===== */}
        <TabsContent value="events" className="space-y-4">
          {isManager && (
            <Button size="sm" onClick={() => setShowCreateEvent(!showCreateEvent)} data-testid="new-event-btn">
              {showCreateEvent ? 'Cancel' : 'New Event'}
            </Button>
          )}

          {showCreateEvent && (
            <Card>
              <CardContent className="pt-4">
                <form onSubmit={createEvent} className="space-y-3">
                  <div><Label>Title (5-200 chars)</Label><Input data-testid="event-title" value={eventForm.title} onChange={e => setEventForm(p => ({ ...p, title: e.target.value }))} required minLength={5} /></div>
                  <div><Label>Description (10+ chars)</Label><Textarea data-testid="event-desc" value={eventForm.description} onChange={e => setEventForm(p => ({ ...p, description: e.target.value }))} required minLength={10} /></div>
                  <div className="grid grid-cols-2 gap-3">
                    <div><Label>Date</Label><Input data-testid="event-date" type="date" value={eventForm.event_date} onChange={e => setEventForm(p => ({ ...p, event_date: e.target.value }))} required /></div>
                    <div><Label>Time</Label><Input data-testid="event-time" type="time" value={eventForm.event_time} onChange={e => setEventForm(p => ({ ...p, event_time: e.target.value }))} /></div>
                  </div>
                  <div><Label>Venue</Label><Input data-testid="event-venue" value={eventForm.venue} onChange={e => setEventForm(p => ({ ...p, venue: e.target.value }))} /></div>
                  <div>
                    <Label>Status</Label>
                    <Select value={eventForm.status} onValueChange={v => setEventForm(p => ({ ...p, status: v }))}>
                      <SelectTrigger data-testid="event-status"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="published">Published</SelectItem>
                        <SelectItem value="draft">Draft</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button type="submit" data-testid="submit-event">Create Event</Button>
                </form>
              </CardContent>
            </Card>
          )}

          <div className="space-y-2">
            {events.map(ev => (
              <Link key={ev.event_id} to={`/communities/${slug}/events/${ev.event_id}`} className="block p-3 border rounded hover:bg-gray-50" data-testid={`event-${ev.event_id}`}>
                <div className="flex justify-between">
                  <span className="font-medium">{ev.title}</span>
                  <Badge variant={ev.status === 'published' ? 'default' : 'secondary'}>{ev.status}</Badge>
                </div>
                <p className="text-xs text-gray-500">{ev.event_date} {ev.event_time || ''} · {ev.venue || 'TBD'} · {ev.media_count} media</p>
              </Link>
            ))}
            {events.length === 0 && <p className="text-sm text-gray-400">No events yet.</p>}
          </div>
        </TabsContent>

        {/* ===== SETTINGS TAB (Manager/Admin) ===== */}
        {isManager && (
          <TabsContent value="settings" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row justify-between items-center">
                <CardTitle className="text-base">Edit Community</CardTitle>
                {!showEdit && <Button size="sm" variant="outline" onClick={startEdit} data-testid="edit-community-btn">Edit</Button>}
              </CardHeader>
              <CardContent>
                {showEdit ? (
                  <form onSubmit={saveEdit} className="space-y-3">
                    <div><Label>Name</Label><Input data-testid="edit-comm-name" value={editForm.name} onChange={e => setEditForm(p => ({ ...p, name: e.target.value }))} /></div>
                    <div><Label>Intro Copy (max 200)</Label><Input data-testid="edit-intro" value={editForm.intro_copy} onChange={e => setEditForm(p => ({ ...p, intro_copy: e.target.value }))} maxLength={200} /></div>
                    <div><Label>Welcome Text (max 1000)</Label><Textarea data-testid="edit-welcome" value={editForm.welcome_text} onChange={e => setEditForm(p => ({ ...p, welcome_text: e.target.value }))} maxLength={1000} /></div>
                    <div><Label>Accent Color</Label><Input data-testid="edit-color" value={editForm.accent_color} onChange={e => setEditForm(p => ({ ...p, accent_color: e.target.value }))} placeholder="#FF5500" /></div>
                    <div>
                      <Label>Privacy</Label>
                      <Select value={editForm.privacy} onValueChange={v => setEditForm(p => ({ ...p, privacy: v }))}>
                        <SelectTrigger data-testid="edit-privacy"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="public">Public</SelectItem>
                          <SelectItem value="private">Private</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex gap-2">
                      <Button type="submit" data-testid="save-community-btn">Save</Button>
                      <Button type="button" variant="outline" onClick={() => setShowEdit(false)}>Cancel</Button>
                    </div>
                  </form>
                ) : (
                  <div className="text-sm space-y-1" data-testid="community-details">
                    <p><span className="text-gray-500">Slug:</span> {community.slug}</p>
                    <p><span className="text-gray-500">Privacy:</span> {community.privacy}</p>
                    <p><span className="text-gray-500">Intro:</span> {community.intro_copy || '-'}</p>
                    <p><span className="text-gray-500">Welcome:</span> {community.welcome_text || '-'}</p>
                    <p><span className="text-gray-500">Accent Color:</span> {community.accent_color || '-'}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-base">Create Category</CardTitle></CardHeader>
              <CardContent>
                <form onSubmit={createCategory} className="flex gap-2">
                  <Input data-testid="category-name" value={catName} onChange={e => setCatName(e.target.value)} placeholder="Category name" required />
                  <Button type="submit" data-testid="create-category-btn">Add</Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
