import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { eventApi, communityApi } from '@/lib/communityApi';
import { Calendar, MapPin, Search, Clock, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function CommunityEvents() {
  const { slug } = useParams();
  const [community, setCommunity] = useState(null);
  const [events, setEvents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    try {
      const [comm, evts] = await Promise.all([
        communityApi.get(slug),
        eventApi.list(slug),
      ]);
      setCommunity(comm);
      setEvents(evts);
    } catch (e) {
      console.error('Error loading events:', e);
    } finally {
      setLoading(false);
    }
  };

  const filtered = events.filter(e => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return e.title.toLowerCase().includes(q) || (e.venue || '').toLowerCase().includes(q) || e.description.toLowerCase().includes(q);
  });

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading events...</div></div>;
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="events-page">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-4">
          <ArrowLeft className="h-3.5 w-3.5" />{community?.name || 'Community'}
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="events-title">
            Events
          </h1>
          <p className="text-base text-muted-foreground max-w-2xl mb-6">
            Join us for gatherings, meetups, and conversations. Limited seats to keep the experience meaningful.
          </p>
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Search events..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" data-testid="events-search-input" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8" data-testid="events-list">
          {filtered.length === 0 ? (
            <div className="col-span-full text-center py-16 bg-muted/30 rounded-xl">
              <p className="text-muted-foreground">
                {searchQuery ? 'No events found matching your search.' : 'No upcoming events at the moment. Check back soon!'}
              </p>
            </div>
          ) : (
            filtered.map((event) => (
              <div key={event.event_id} className="bg-card border border-border rounded-xl overflow-hidden hover:shadow-md transition-all duration-200" data-testid={`event-card-${event.event_id}`}>
                <div className="p-6">
                  <h2 className="text-xl font-body font-medium mb-3 text-title" data-testid={`event-title-${event.event_id}`}>
                    {event.title}
                  </h2>
                  <div className="flex flex-wrap gap-3 text-sm text-muted-foreground mb-4">
                    {event.venue && (
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4" strokeWidth={1.5} />
                        <span>{event.venue}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" strokeWidth={1.5} />
                      <span>{new Date(event.event_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
                    </div>
                    {event.event_time && (
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4" strokeWidth={1.5} />
                        <span>{event.event_time}</span>
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-foreground/80 leading-relaxed mb-4 line-clamp-3">{event.description}</p>
                  <div className="text-xs text-muted-foreground">
                    Created by {event.creator_name}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
