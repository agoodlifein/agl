import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { discussionApi, managerApi } from '@/lib/communityApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Plus, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function ManagerCategories() {
  const { slug } = useParams();
  const [categories, setCategories] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [slug]);

  const loadData = async () => {
    try {
      const cats = await discussionApi.categories(slug);
      setCategories(cats);
    } catch (e) {
      console.error('Error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await managerApi.createCategory(slug, formData);
      toast.success('Category created!');
      setFormData({ name: '', description: '' });
      setShowAddForm(false);
      loadData();
    } catch (e) {
      toast.error(e.message || 'Error creating category');
    }
  };

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="manager-categories-page">
      <div className="max-w-5xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}/manage`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-4">
          <ArrowLeft className="h-3.5 w-3.5" />Back to Dashboard
        </Link>

        <div className="mb-12 flex items-center justify-between">
          <div>
            <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="categories-title">
              Discussion Categories
            </h1>
            <p className="text-base text-muted-foreground">Manage forum categories for this community.</p>
          </div>
          <Button onClick={() => setShowAddForm(!showAddForm)} data-testid="add-category-button">
            <Plus className="mr-2 h-4 w-4" strokeWidth={1.5} />Add Category
          </Button>
        </div>

        {showAddForm && (
          <form onSubmit={handleAdd} className="bg-card border border-border rounded-xl p-8 mb-8" data-testid="add-category-form">
            <h2 className="text-xl font-heading font-normal mb-6">New Category</h2>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Name *</Label>
                <Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required data-testid="category-name-input" />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={2} data-testid="category-description-input" />
              </div>
              <div className="flex gap-4">
                <Button type="submit" data-testid="submit-category">Add</Button>
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>Cancel</Button>
              </div>
            </div>
          </form>
        )}

        <div className="space-y-4" data-testid="categories-list">
          {categories.length === 0 ? (
            <div className="text-center py-16 bg-muted/30 rounded-xl">
              <p className="text-muted-foreground">No categories yet. Create one to get started.</p>
            </div>
          ) : (
            categories.map((cat) => (
              <div key={cat.category_id} className="bg-card border border-border rounded-xl p-6" data-testid={`category-item-${cat.category_id}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-xl font-medium mb-1">{cat.name}</h3>
                    <p className="text-sm text-muted-foreground">{cat.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">Order: {cat.display_order} &middot; {cat.is_active ? 'Active' : 'Inactive'}</p>
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
