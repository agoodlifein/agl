import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { communityApi, discussionApi, eventApi } from '@/lib/communityApi';
import { useAuth } from '@/contexts/AuthContext';
import { MessageSquare, ArrowRight, Calendar, Users, Settings, UserPlus, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function CommunityHome() {
  const { slug } = useParams();
  const { user } = useAuth();
  const [community, setCommunity] = useState(null);
  const [categories, setCategories] = useState([]);
  const [events, setEvents] = useState([]);
  const [membership, setMembership] = useState(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    try {
      const comm = await communityApi.get(slug);
      setCommunity(comm);
      const [cats, evts] = await Promise.all([
        discussionApi.categories(slug).catch(() => []),
        eventApi.list(slug).catch(() => []),
      ]);
      setCategories(cats);
      setEvents(evts);
      if (user) {
        try {
          const ms = await communityApi.membershipStatus(slug);
          setMembership(ms);
        } catch {}
      }
    } catch (e) {
      console.error('Error loading community:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!user) {
      toast.error('Please sign in to join');
      return;
    }
    setJoining(true);
    try {
      if (community.privacy === 'private') {
        await communityApi.requestJoin(slug, {});
        toast.success('Join request sent! Awaiting approval.');
      } else {
        await communityApi.join(slug);
        toast.success('Welcome to the community!');
      }
      loadData();
    } catch (e) {
      toast.error(e.message || 'Error joining community');
    } finally {
      setJoining(false);
    }
  };

  const isMember = membership?.status === 'active';
  const isManager = membership?.role === 'community_manager' || membership?.role === 'moderator';
  const isPending = membership?.status === 'pending';

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  }

  if (!community) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-heading font-normal mb-4">Community not found</h2>
          <Link to="/communities"><Button>Browse Communities</Button></Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="community-home">
      {/* Hero Section */}
      <section className="relative py-16 md:py-24">
        <div className="absolute inset-0 bg-gradient-to-b from-accent/15 to-transparent"></div>
        <div className="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-4">
                {community.logo && <img src={community.logo} alt={community.name} className="w-14 h-14 rounded-full object-cover" />}
                <div>
                  <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight text-title" data-testid="community-name">
                    {community.name}
                  </h1>
                  <span className="text-sm text-muted-foreground capitalize">{community.privacy} community</span>
                </div>
              </div>
              <p className="text-base text-foreground/80 max-w-2xl leading-relaxed">
                {community.description}
              </p>
            </div>
            <div className="flex flex-col gap-2">
              {!user && (
                <Link to="/auth">
                  <Button data-testid="login-to-join-button"><LogIn className="mr-2 h-4 w-4" strokeWidth={1.5} />Sign in to Join</Button>
                </Link>
              )}
              {user && !isMember && !isPending && (
                <Button onClick={handleJoin} disabled={joining} data-testid="join-community-button">
                  <UserPlus className="mr-2 h-4 w-4" strokeWidth={1.5} />
                  {joining ? 'Joining...' : community.privacy === 'private' ? 'Request to Join' : 'Join Community'}
                </Button>
              )}
              {isPending && (
                <Button disabled variant="outline" data-testid="pending-button">Request Pending</Button>
              )}
              {isMember && (
                <span className="text-sm text-primary font-medium bg-primary/10 px-3 py-1.5 rounded-full text-center" data-testid="member-badge">Member</span>
              )}
              {isManager && (
                <Link to={`/community/${slug}/manage`}>
                  <Button variant="outline" size="sm" data-testid="manage-button">
                    <Settings className="mr-2 h-4 w-4" strokeWidth={1.5} />Manage
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-8 bg-muted/30 border-y border-border">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex flex-wrap gap-3">
            <Link to={`/community/${slug}/discussions`}>
              <Button variant="outline" size="sm" data-testid="nav-discussions">
                <MessageSquare className="mr-2 h-4 w-4" strokeWidth={1.5} />Discussions
              </Button>
            </Link>
            <Link to={`/community/${slug}/events`}>
              <Button variant="outline" size="sm" data-testid="nav-events">
                <Calendar className="mr-2 h-4 w-4" strokeWidth={1.5} />Events
              </Button>
            </Link>
            <Link to={`/community/${slug}/members`}>
              <Button variant="outline" size="sm" data-testid="nav-members">
                <Users className="mr-2 h-4 w-4" strokeWidth={1.5} />Members
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Forum Categories */}
      {categories.length > 0 && (
        <section className="py-16 md:py-20">
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
            <div className="text-center mb-12">
              <p className="text-xs uppercase tracking-[0.2em] font-medium text-muted-foreground mb-4">Forum</p>
              <h2 className="text-2xl sm:text-3xl font-heading font-normal tracking-tight mb-4 text-title">
                Join the Conversation
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="category-grid">
              {categories.map((cat) => (
                <Link key={cat.category_id} to={`/community/${slug}/discussions/${cat.category_id}`} data-testid={`category-card-${cat.category_id}`}>
                  <div className="bg-card border border-border rounded-xl p-8 hover:-translate-y-1 hover:shadow-md hover:border-border/80 transition-all duration-200 h-full">
                    <MessageSquare className="mb-4 h-8 w-8 text-primary" strokeWidth={1.5} />
                    <h3 className="text-xl font-medium mb-2">{cat.name}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-4">
                      {cat.description || 'Join the discussion'}
                    </p>
                    <div className="flex items-center text-sm font-medium text-primary">
                      Explore <ArrowRight className="ml-2 h-4 w-4" strokeWidth={1.5} />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Upcoming Events */}
      {events.length > 0 && (
        <section className="py-16 md:py-20 bg-muted/30">
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-heading font-normal text-title">Upcoming Events</h2>
              <Link to={`/community/${slug}/events`}>
                <Button variant="outline" size="sm">View All</Button>
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="events-preview">
              {events.slice(0, 4).map((ev) => (
                <div key={ev.event_id} className="bg-card border border-border rounded-xl p-6" data-testid={`event-preview-${ev.event_id}`}>
                  <h3 className="text-lg font-medium mb-2">{ev.title}</h3>
                  <div className="flex flex-wrap gap-3 text-sm text-muted-foreground mb-3">
                    <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{new Date(ev.event_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
                    {ev.venue && <span>{ev.venue}</span>}
                  </div>
                  <p className="text-sm text-foreground/80 line-clamp-2">{ev.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
