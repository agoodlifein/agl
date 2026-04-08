import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { managerApi } from '@/lib/communityApi';
import { Button } from '@/components/ui/button';
import { Check, X, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function ManagerJoinRequests() {
  const { slug } = useParams();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [slug]);

  const loadData = async () => {
    try {
      const reqs = await managerApi.joinRequests(slug);
      setRequests(reqs.filter(r => r.status === 'pending'));
    } catch (e) {
      console.error('Error loading requests:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      await managerApi.approveJoinRequest(slug, id);
      toast.success('Request approved!');
      loadData();
    } catch (e) {
      toast.error(e.message || 'Error approving request');
    }
  };

  const handleReject = async (id) => {
    try {
      await managerApi.rejectJoinRequest(slug, id);
      toast.success('Request rejected');
      loadData();
    } catch (e) {
      toast.error(e.message || 'Error rejecting request');
    }
  };

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="join-requests-page">
      <div className="max-w-5xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}/manage`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-4">
          <ArrowLeft className="h-3.5 w-3.5" />Back to Dashboard
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="join-requests-title">
            Join Requests
          </h1>
          <p className="text-base text-muted-foreground">Review and approve pending membership requests.</p>
        </div>

        {requests.length === 0 ? (
          <div className="text-center py-16 bg-muted/30 rounded-xl">
            <p className="text-muted-foreground">No pending requests at the moment.</p>
          </div>
        ) : (
          <div className="space-y-6" data-testid="requests-list">
            {requests.map((req) => (
              <div key={req.request_id} className="bg-card border border-border rounded-xl p-8" data-testid={`request-card-${req.request_id}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-heading font-normal mb-2">{req.user_name || req.user_email}</h2>
                    <p className="text-sm text-muted-foreground">{req.user_email}</p>
                    {req.message && <p className="text-sm text-foreground/80 mt-2">{req.message}</p>}
                    <p className="text-xs text-muted-foreground mt-2">Requested {new Date(req.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => handleApprove(req.request_id)} size="sm" data-testid={`approve-${req.request_id}`}>
                      <Check className="mr-2 h-4 w-4" strokeWidth={1.5} />Approve
                    </Button>
                    <Button onClick={() => handleReject(req.request_id)} variant="outline" size="sm" data-testid={`reject-${req.request_id}`}>
                      <X className="mr-2 h-4 w-4" strokeWidth={1.5} />Reject
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
