import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function EventPage() {
  const { slug, eventId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [membership, setMembership] = useState(null);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [uploading, setUploading] = useState(false);

  const isAdmin = user?.is_super_admin;
  const isManager = membership?.role === 'community_manager' || isAdmin;

  useEffect(() => {
    api.get(`/communities/${slug}/events/${eventId}`).then(setEvent).catch(e => setErr(e.message));
    api.get(`/communities/${slug}/membership-status`).then(setMembership).catch(() => {});
  }, [slug, eventId]);

  const uploadMedia = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setErr(''); setMsg(''); setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await api.upload(`/manager/communities/${slug}/events/${eventId}/upload-media`, formData);
      setMsg('Image uploaded');
      const updated = await api.get(`/communities/${slug}/events/${eventId}`);
      setEvent(updated);
    } catch (e) { setErr(e.message); }
    finally { setUploading(false); e.target.value = ''; }
  };

  const deleteMedia = async (mediaUrl) => {
    // Extract media_id from the path - query DB via listing
    setErr(''); setMsg('');
    try {
      // We need the media_id. Let's get it from the event's media list in the backend.
      // Since we don't have direct access, we'll use a workaround - the URL contains the filename
      // Actually we need a separate approach. Let's reload the event which has media_urls but not media_ids.
      // For simplicity in this test UI, we'll note this limitation.
      setErr('Media deletion requires media_id - use the API directly for now');
    } catch (e) { setErr(e.message); }
  };

  if (!event) return <div className="p-6">{err || 'Loading...'}</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4" data-testid="event-page">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">{event.title}</h1>
        <Button variant="ghost" size="sm" onClick={() => navigate(`/communities/${slug}`)}>Back</Button>
      </div>

      {msg && <div className="p-2 bg-green-50 text-green-700 rounded text-sm" data-testid="event-success">{msg}</div>}
      {err && <div className="p-2 bg-red-50 text-red-700 rounded text-sm" data-testid="event-error">{err}</div>}

      <Card>
        <CardContent className="pt-4 space-y-2" data-testid="event-details">
          <div className="flex gap-2">
            <Badge variant={event.status === 'published' ? 'default' : 'secondary'}>{event.status}</Badge>
          </div>
          <p className="text-sm whitespace-pre-wrap">{event.description}</p>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <p><span className="text-gray-500">Date:</span> {event.event_date}</p>
            <p><span className="text-gray-500">Time:</span> {event.event_time || 'TBD'}</p>
            <p><span className="text-gray-500">Venue:</span> {event.venue || 'TBD'}</p>
            <p><span className="text-gray-500">Created by:</span> {event.creator_name}</p>
          </div>
          {event.details && <p className="text-sm"><span className="text-gray-500">Details:</span> {event.details}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row justify-between items-center">
          <CardTitle className="text-base">Media ({event.media_count})</CardTitle>
          {isManager && (
            <div>
              <Input data-testid="upload-media-input" type="file" accept="image/jpeg,image/png" onChange={uploadMedia} disabled={uploading} className="w-auto" />
            </div>
          )}
        </CardHeader>
        <CardContent>
          {event.media_urls?.length > 0 ? (
            <div className="grid grid-cols-3 gap-2">
              {event.media_urls.map((url, i) => (
                <div key={i} className="relative">
                  <img
                    src={`${process.env.REACT_APP_BACKEND_URL}${url}`}
                    alt={`Event media ${i + 1}`}
                    className="w-full h-32 object-cover rounded border"
                    data-testid={`event-media-${i}`}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No media uploaded yet.</p>
          )}
          {uploading && <p className="text-sm text-blue-500 mt-2">Uploading...</p>}
        </CardContent>
      </Card>
    </div>
  );
}
