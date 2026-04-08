import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { discussionApi, communityApi } from '@/lib/communityApi';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import Avatar from '@/components/Avatar';

export default function ThreadDetail() {
  const { slug, threadId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [thread, setThread] = useState(null);
  const [posts, setPosts] = useState([]);
  const [replyContent, setReplyContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, [slug, threadId]);

  const loadData = async () => {
    try {
      const [t, p] = await Promise.all([
        discussionApi.thread(slug, threadId),
        discussionApi.posts(slug, threadId),
      ]);
      setThread(t);
      setPosts(p);
    } catch (e) {
      console.error('Error loading thread:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async (e) => {
    e.preventDefault();
    if (!replyContent.trim()) return;
    setSubmitting(true);
    try {
      await discussionApi.createPost(slug, threadId, { content: replyContent });
      setReplyContent('');
      toast.success('Reply posted!');
      loadData();
    } catch (e) {
      toast.error(e.message || 'Error posting reply');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePost = async (postId) => {
    try {
      await discussionApi.deletePost(slug, threadId, postId);
      toast.success('Reply deleted');
      loadData();
    } catch (e) {
      toast.error('Error deleting reply');
    }
  };

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  }

  if (!thread) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-heading font-normal mb-4">Discussion not found</h2>
          <Link to={`/community/${slug}/discussions`}><Button>Back to Discussions</Button></Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="thread-detail-page">
      <div className="max-w-4xl mx-auto px-6 sm:px-8 lg:px-12">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-8" data-testid="back-button">
          <ArrowLeft className="mr-2 h-4 w-4" strokeWidth={1.5} />Back
        </Button>

        {/* Thread */}
        <div className="bg-card border border-border p-8 mb-8 rounded-xl" data-testid="thread-post">
          <h1 className="text-3xl sm:text-4xl font-heading font-light tracking-tight mb-4 text-title" data-testid="thread-title">
            {thread.title}
          </h1>
          <div className="flex items-center gap-3 text-sm text-muted-foreground mb-6">
            <Avatar user={{ name: thread.author_name }} size="sm" />
            <span>by <span className="font-medium text-foreground">{thread.author_name}</span></span>
            <span className="mx-1">&middot;</span>
            <span>{new Date(thread.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
          </div>
          <p className="text-base text-foreground/90 leading-relaxed whitespace-pre-wrap" data-testid="thread-content">
            {thread.content}
          </p>
        </div>

        {/* Replies */}
        <div className="mb-8">
          <h2 className="text-2xl font-heading font-normal mb-6 text-title">Replies ({posts.length})</h2>
          <div className="space-y-4" data-testid="posts-list">
            {posts.map((post) => (
              <div key={post.post_id} className="bg-card border border-border p-6 rounded-xl" data-testid={`post-${post.post_id}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <Avatar user={{ name: post.author_name }} size="sm" />
                    <span className="font-medium text-foreground">{post.author_name}</span>
                    <span className="mx-1">&middot;</span>
                    <span>{new Date(post.created_at).toLocaleDateString()}</span>
                    {post.is_edited && <span className="text-xs">(edited)</span>}
                  </div>
                  {user && user.user_id === post.author_id && (
                    <Button variant="ghost" size="sm" onClick={() => handleDeletePost(post.post_id)} data-testid={`delete-post-${post.post_id}`}>
                      <Trash2 className="h-3.5 w-3.5" strokeWidth={1.5} />
                    </Button>
                  )}
                </div>
                <p className="text-base text-foreground/90 leading-relaxed whitespace-pre-wrap">{post.content}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Reply Form */}
        {user ? (
          <div className="bg-card border border-border p-8 rounded-xl" data-testid="reply-form">
            <h3 className="text-xl font-medium mb-4">Add a Reply</h3>
            <form onSubmit={handleReply}>
              <Textarea value={replyContent} onChange={(e) => setReplyContent(e.target.value)} placeholder="Share your thoughts..." rows={4} className="mb-4" data-testid="reply-textarea" />
              <Button type="submit" disabled={!replyContent.trim() || submitting} data-testid="post-reply-button">
                {submitting ? 'Posting...' : 'Post Reply'}
              </Button>
            </form>
          </div>
        ) : (
          <div className="bg-muted/30 border border-border p-8 text-center rounded-xl">
            <p className="text-muted-foreground mb-4">Sign in to join the conversation</p>
            <Link to="/auth"><Button>Sign In</Button></Link>
          </div>
        )}
      </div>
    </div>
  );
}
