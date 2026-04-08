import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

export default function DiscussionPage() {
  const { slug, threadId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [thread, setThread] = useState(null);
  const [posts, setPosts] = useState([]);
  const [replyContent, setReplyContent] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    api.get(`/communities/${slug}/threads/${threadId}`).then(setThread).catch(e => setErr(e.message));
    api.get(`/communities/${slug}/threads/${threadId}/posts`).then(setPosts).catch(() => {});
  }, [slug, threadId]);

  const submitReply = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    try {
      await api.post(`/communities/${slug}/threads/${threadId}/posts`, { content: replyContent });
      setReplyContent('');
      setMsg('Reply posted');
      const p = await api.get(`/communities/${slug}/threads/${threadId}/posts`);
      setPosts(p);
    } catch (e) { setErr(e.message); }
  };

  if (!thread) return <div className="p-6">{err || 'Loading...'}</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4" data-testid="discussion-page">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">{thread.title}</h1>
        <Button variant="ghost" size="sm" onClick={() => navigate(`/communities/${slug}`)}>Back</Button>
      </div>

      <Card>
        <CardContent className="pt-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="font-medium text-sm">{thread.author_name}</span>
              <span className="text-xs text-gray-400 ml-2">{new Date(thread.created_at).toLocaleString()}</span>
            </div>
            <div className="flex gap-1">
              {thread.is_pinned && <Badge variant="secondary">Pinned</Badge>}
              <Badge variant="outline">{thread.reply_count} replies</Badge>
              <Badge variant="outline">{thread.view_count} views</Badge>
            </div>
          </div>
          <p className="text-sm whitespace-pre-wrap" data-testid="thread-body">{thread.content}</p>
        </CardContent>
      </Card>

      {msg && <div className="p-2 bg-green-50 text-green-700 rounded text-sm" data-testid="discussion-success">{msg}</div>}
      {err && <div className="p-2 bg-red-50 text-red-700 rounded text-sm" data-testid="discussion-error">{err}</div>}

      <h2 className="text-base font-semibold">Replies ({posts.length})</h2>
      <div className="space-y-2">
        {posts.map(p => (
          <Card key={p.post_id}>
            <CardContent className="py-3 px-4">
              <div className="flex justify-between mb-1">
                <span className="font-medium text-sm">{p.author_name}</span>
                <span className="text-xs text-gray-400">{new Date(p.created_at).toLocaleString()}</span>
              </div>
              <p className="text-sm whitespace-pre-wrap" data-testid={`post-${p.post_id}`}>{p.content}</p>
              {p.is_edited && <span className="text-xs text-gray-400">(edited)</span>}
            </CardContent>
          </Card>
        ))}
        {posts.length === 0 && <p className="text-sm text-gray-400">No replies yet. Be the first!</p>}
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Reply</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={submitReply} className="space-y-3">
            <div><Label>Your Reply</Label><Textarea data-testid="reply-content" value={replyContent} onChange={e => setReplyContent(e.target.value)} required minLength={1} /></div>
            <Button type="submit" data-testid="submit-reply">Post Reply</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
