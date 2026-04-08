import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { discussionApi, managerApi } from '@/lib/communityApi';
import { Button } from '@/components/ui/button';
import { Check, X, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function ManagerModeration() {
  const { slug } = useParams();
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [slug]);

  const loadData = async () => {
    try {
      const t = await discussionApi.threads(slug);
      setThreads(t);
    } catch (e) {
      console.error('Error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (threadId) => {
    try {
      await managerApi.approveThread(slug, threadId);
      toast.success('Thread approved');
      loadData();
    } catch (e) {
      toast.error(e.message || 'Error approving thread');
    }
  };

  const handleReject = async (threadId) => {
    try {
      await managerApi.rejectThread(slug, threadId);
      toast.success('Thread rejected');
      loadData();
    } catch (e) {
      toast.error(e.message || 'Error rejecting thread');
    }
  };

  const pendingThreads = threads.filter(t => t.status === 'pending');
  const allThreads = threads;

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="moderation-page">
      <div className="max-w-5xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}/manage`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-4">
          <ArrowLeft className="h-3.5 w-3.5" />Back to Dashboard
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="moderation-title">
            Content Moderation
          </h1>
          <p className="text-base text-muted-foreground">Review and moderate discussion threads.</p>
        </div>

        {/* Pending */}
        {pendingThreads.length > 0 && (
          <div className="mb-12">
            <h2 className="text-xl font-heading font-normal mb-6 text-title">Pending Approval ({pendingThreads.length})</h2>
            <div className="space-y-4">
              {pendingThreads.map((thread) => (
                <div key={thread.thread_id} className="bg-card border-2 border-yellow-300/50 rounded-xl p-6" data-testid={`pending-thread-${thread.thread_id}`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-medium mb-1">{thread.title}</h3>
                      <p className="text-sm text-muted-foreground mb-2">by {thread.author_name} &middot; {new Date(thread.created_at).toLocaleDateString()}</p>
                      <p className="text-sm text-foreground/80 line-clamp-3">{thread.content}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleApprove(thread.thread_id)} data-testid={`approve-thread-${thread.thread_id}`}>
                        <Check className="mr-1 h-4 w-4" strokeWidth={1.5} />Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleReject(thread.thread_id)} data-testid={`reject-thread-${thread.thread_id}`}>
                        <X className="mr-1 h-4 w-4" strokeWidth={1.5} />Reject
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Threads */}
        <div>
          <h2 className="text-xl font-heading font-normal mb-6 text-title">All Threads ({allThreads.length})</h2>
          <div className="space-y-4" data-testid="all-threads-list">
            {allThreads.length === 0 ? (
              <div className="text-center py-16 bg-muted/30 rounded-xl">
                <p className="text-muted-foreground">No threads yet.</p>
              </div>
            ) : (
              allThreads.map((thread) => (
                <div key={thread.thread_id} className={`bg-card border border-border rounded-xl p-6 ${thread.status === 'rejected' ? 'opacity-60' : ''}`} data-testid={`thread-mod-${thread.thread_id}`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-lg font-medium">{thread.title}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded ${thread.status === 'approved' ? 'bg-green-100 text-green-800' : thread.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                          {thread.status}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">by {thread.author_name} &middot; {new Date(thread.created_at).toLocaleDateString()}</p>
                    </div>
                    {thread.status !== 'approved' && (
                      <Button size="sm" variant="outline" onClick={() => handleApprove(thread.thread_id)}>
                        <Check className="mr-1 h-4 w-4" strokeWidth={1.5} />Approve
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
