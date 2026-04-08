import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { profileApi } from '@/lib/communityApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import Avatar from '@/components/Avatar';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({ name: '', bio: '', phone: '', location: '' });

  useEffect(() => {
    if (!user) { navigate('/auth'); return; }
    loadProfile();
  }, [user]);

  const loadProfile = async () => {
    try {
      const p = await profileApi.get();
      setProfile(p);
      setFormData({
        name: p.name || '',
        bio: p.bio || '',
        phone: p.phone || '',
        location: p.location || '',
      });
    } catch {}
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await profileApi.update(formData);
      toast.success('Profile updated!');
      setEditing(false);
      await refreshUser();
      loadProfile();
    } catch (e) {
      toast.error(e.message || 'Error updating profile');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;
  const displayProfile = profile || user;

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="profile-page">
      <div className="max-w-3xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="mb-12 flex items-center justify-between">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight text-title" data-testid="profile-title">
            My Profile
          </h1>
          {!editing && (
            <Button onClick={() => setEditing(true)} data-testid="edit-profile-button">Edit Profile</Button>
          )}
        </div>

        {editing ? (
          <form onSubmit={handleSubmit} className="space-y-8" data-testid="profile-edit-form">
            <div className="bg-card border border-border rounded-xl p-8">
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input id="name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} data-testid="profile-name-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input id="location" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} data-testid="profile-location-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input id="phone" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} data-testid="profile-phone-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea id="bio" value={formData.bio} onChange={(e) => setFormData({ ...formData, bio: e.target.value })} rows={4} data-testid="profile-bio-textarea" placeholder="Tell us about yourself..." />
                </div>
              </div>
            </div>
            <div className="flex gap-4">
              <Button type="submit" disabled={loading} data-testid="save-profile-button">{loading ? 'Saving...' : 'Save Changes'}</Button>
              <Button type="button" variant="outline" onClick={() => setEditing(false)} data-testid="cancel-edit-button">Cancel</Button>
            </div>
          </form>
        ) : (
          <div className="bg-card border border-border rounded-xl p-8" data-testid="profile-view">
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <Avatar user={displayProfile} size="xl" />
                <div>
                  <h2 className="text-2xl font-medium" data-testid="profile-display-name">{displayProfile.name}</h2>
                  <p className="text-sm text-muted-foreground">{displayProfile.email}</p>
                </div>
              </div>
              {displayProfile.location && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Location</h3>
                  <p className="text-base" data-testid="profile-display-location">{displayProfile.location}</p>
                </div>
              )}
              {displayProfile.phone && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Phone</h3>
                  <p className="text-base" data-testid="profile-display-phone">{displayProfile.phone}</p>
                </div>
              )}
              {displayProfile.bio && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Bio</h3>
                  <p className="text-base leading-relaxed" data-testid="profile-display-bio">{displayProfile.bio}</p>
                </div>
              )}
              {displayProfile.is_super_admin && (
                <div className="inline-block px-3 py-1 bg-primary/10 text-primary text-sm rounded-full font-medium">
                  Super Admin
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
