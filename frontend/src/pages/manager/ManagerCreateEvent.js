import React, { useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { managerApi } from '@/lib/communityApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function ManagerCreateEvent() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_date: '',
    event_time: '',
    venue: '',
    max_attendees: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...formData,
        max_attendees: formData.max_attendees ? parseInt(formData.max_attendees) : null,
        event_time: formData.event_time || null,
      };
      await managerApi.createEvent(slug, payload);
      toast.success('Event created!');
      navigate(`/community/${slug}/manage`);
    } catch (e) {
      toast.error(e.message || 'Error creating event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="create-event-page">
      <div className="max-w-3xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}/manage`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-6">
          <ArrowLeft className="h-3.5 w-3.5" />Back to Dashboard
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="create-event-title">
            Create Event
          </h1>
          <p className="text-base text-muted-foreground">Add a new event for the community.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="bg-card border border-border rounded-xl p-8">
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="title">Event Title *</Label>
                <Input id="title" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required data-testid="event-title-input" placeholder="Creative Dinner" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="venue">Venue</Label>
                <Input id="venue" value={formData.venue} onChange={(e) => setFormData({ ...formData, venue: e.target.value })} data-testid="event-venue-input" placeholder="Location" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date">Date *</Label>
                  <Input id="date" type="date" value={formData.event_date} onChange={(e) => setFormData({ ...formData, event_date: e.target.value })} required data-testid="event-date-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="time">Time</Label>
                  <Input id="time" type="time" value={formData.event_time} onChange={(e) => setFormData({ ...formData, event_time: e.target.value })} data-testid="event-time-input" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="max">Max Attendees</Label>
                <Input id="max" type="number" value={formData.max_attendees} onChange={(e) => setFormData({ ...formData, max_attendees: e.target.value })} data-testid="event-max-input" placeholder="Leave empty for unlimited" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="desc">Description *</Label>
                <Textarea id="desc" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} required rows={6} data-testid="event-description-input" placeholder="Describe the event..." />
              </div>
            </div>
          </div>
          <div className="flex gap-4">
            <Button type="submit" disabled={loading} data-testid="submit-event-button">{loading ? 'Creating...' : 'Create Event'}</Button>
            <Button type="button" variant="outline" onClick={() => navigate(-1)} data-testid="cancel-event-button">Cancel</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
