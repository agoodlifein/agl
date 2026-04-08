import React, { useEffect, useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { communityApi, discussionApi, managerApi } from '@/lib/communityApi';
import { useAuth } from '@/contexts/AuthContext';
import { Users, MessageSquare, Calendar, UserPlus, ArrowLeft, Layers, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ManagerDashboard() {
  const { slug } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [community, setCommunity] = useState(null);
  const [stats, setStats] = useState({ members: 0, threads: 0, events: 0, joinRequests: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    try {
      const comm = await communityApi.get(slug);
      setCommunity(comm);
      const [members, threads, events, joinReqs] = await Promise.all([
        communityApi.members(slug).catch(() => []),
        discussionApi.threads(slug).catch(() => []),
        managerApi.managerEvents(slug).catch(() => []),
        managerApi.joinRequests(slug).catch(() => []),
      ]);
      setStats({
        members: members.length,
        threads: threads.length,
        events: events.length,
        joinRequests: joinReqs.filter(r => r.status === 'pending').length,
      });
    } catch (e) {
      console.error('Error loading dashboard:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="manager-dashboard">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-4">
          <ArrowLeft className="h-3.5 w-3.5" />{community?.name || 'Community'}
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="manager-dashboard-title">
            Manage Community
          </h1>
          <p className="text-base text-muted-foreground">
            Overview and management tools for {community?.name}.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12" data-testid="stats-grid">
          <div className="bg-card border border-border rounded-xl p-6">
            <Users className="text-primary mb-4 h-8 w-8" strokeWidth={1.5} />
            <div className="text-3xl font-heading mb-2" data-testid="stat-members">{stats.members}</div>
            <div className="text-sm text-muted-foreground">Members</div>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <UserPlus className="text-primary mb-4 h-8 w-8" strokeWidth={1.5} />
            <div className="text-3xl font-heading mb-2" data-testid="stat-pending">{stats.joinRequests}</div>
            <div className="text-sm text-muted-foreground">Pending Requests</div>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <MessageSquare className="text-primary mb-4 h-8 w-8" strokeWidth={1.5} />
            <div className="text-3xl font-heading mb-2" data-testid="stat-threads">{stats.threads}</div>
            <div className="text-sm text-muted-foreground">Discussions</div>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <Calendar className="text-primary mb-4 h-8 w-8" strokeWidth={1.5} />
            <div className="text-3xl font-heading mb-2" data-testid="stat-events">{stats.events}</div>
            <div className="text-sm text-muted-foreground">Events</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-card border border-border rounded-xl p-8">
          <h2 className="text-2xl font-heading font-normal mb-6 text-title">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link to={`/community/${slug}/manage/join-requests`}>
              <Button variant="outline" className="w-full" data-testid="action-join-requests">
                <UserPlus className="mr-2 h-4 w-4" strokeWidth={1.5} />Join Requests
              </Button>
            </Link>
            <Link to={`/community/${slug}/manage/categories`}>
              <Button variant="outline" className="w-full" data-testid="action-categories">
                <Layers className="mr-2 h-4 w-4" strokeWidth={1.5} />Categories
              </Button>
            </Link>
            <Link to={`/community/${slug}/manage/create-event`}>
              <Button variant="outline" className="w-full" data-testid="action-create-event">
                <Calendar className="mr-2 h-4 w-4" strokeWidth={1.5} />Create Event
              </Button>
            </Link>
            <Link to={`/community/${slug}/manage/moderation`}>
              <Button variant="outline" className="w-full" data-testid="action-moderation">
                <Shield className="mr-2 h-4 w-4" strokeWidth={1.5} />Moderation
              </Button>
            </Link>
            <Link to={`/community/${slug}/members`}>
              <Button variant="outline" className="w-full" data-testid="action-members">
                <Users className="mr-2 h-4 w-4" strokeWidth={1.5} />View Members
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
