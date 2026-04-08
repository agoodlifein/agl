import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { discussionApi } from '@/lib/communityApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function CreateThread() {
  const { slug } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category_id: searchParams.get('category') || ''
  });

  useEffect(() => {
    discussionApi.categories(slug).then(setCategories).catch(() => {});
  }, [slug]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.category_id) {
      toast.error('Please select a category');
      return;
    }
    setLoading(true);
    try {
      await discussionApi.createThread(slug, formData);
      toast.success('Discussion created!');
      navigate(`/community/${slug}/discussions/${formData.category_id}`);
    } catch (e) {
      toast.error(e.message || 'Error creating discussion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="create-thread-page">
      <div className="max-w-3xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}/discussions`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-6">
          <ArrowLeft className="h-3.5 w-3.5" />Back to Discussions
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="create-thread-title">
            Start a Discussion
          </h1>
          <p className="text-base text-muted-foreground">
            Share your thoughts, questions, or ideas with the community.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="bg-card border border-border rounded-xl p-8">
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="category">Category *</Label>
                <Select value={formData.category_id} onValueChange={(v) => setFormData({ ...formData, category_id: v })}>
                  <SelectTrigger data-testid="category-select"><SelectValue placeholder="Select a category" /></SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat.category_id} value={cat.category_id}>{cat.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input id="title" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required data-testid="thread-title-input" placeholder="What's on your mind?" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="content">Content *</Label>
                <Textarea id="content" value={formData.content} onChange={(e) => setFormData({ ...formData, content: e.target.value })} required rows={8} data-testid="thread-content-textarea" placeholder="Share your thoughts in detail..." />
              </div>
            </div>
          </div>
          <div className="flex gap-4">
            <Button type="submit" disabled={loading || !formData.category_id} data-testid="submit-thread-button">
              {loading ? 'Creating...' : 'Create Discussion'}
            </Button>
            <Button type="button" variant="outline" onClick={() => navigate(-1)} data-testid="cancel-thread-button">Cancel</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
