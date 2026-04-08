import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { communityApi, discussionApi } from '@/lib/communityApi';
import { useAuth } from '@/contexts/AuthContext';
import { MessageSquare, Plus, Search, ArrowUpDown, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function CommunityDiscussions() {
  const { slug, categoryId } = useParams();
  const { user } = useAuth();
  const [community, setCommunity] = useState(null);
  const [categories, setCategories] = useState([]);
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [selectedCategory, setSelectedCategory] = useState(categoryId || 'all');

  useEffect(() => {
    loadData();
  }, [slug, categoryId]);

  const loadData = async () => {
    try {
      const [comm, cats, thrds] = await Promise.all([
        communityApi.get(slug),
        discussionApi.categories(slug),
        discussionApi.threads(slug, categoryId ? { category_id: categoryId } : {}),
      ]);
      setCommunity(comm);
      setCategories(cats);
      setThreads(thrds);
      if (categoryId) setSelectedCategory(categoryId);
    } catch (e) {
      console.error('Error loading discussions:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (value) => {
    setSelectedCategory(value);
  };

  const filteredThreads = threads
    .filter(t => {
      if (selectedCategory && selectedCategory !== 'all' && t.category_id !== selectedCategory) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return t.title.toLowerCase().includes(q) || t.content.toLowerCase().includes(q) || t.author_name.toLowerCase().includes(q);
    })
    .sort((a, b) => {
      if (sortBy === 'oldest') return new Date(a.created_at) - new Date(b.created_at);
      return new Date(b.created_at) - new Date(a.created_at);
    });

  const currentCategory = categories.find(c => c.category_id === selectedCategory);

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading...</div></div>;
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="discussions-page">
      <div className="max-w-5xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="mb-8">
          <Link to={`/community/${slug}`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-4">
            <ArrowLeft className="h-3.5 w-3.5" />{community?.name || 'Community'}
          </Link>

          <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
            <div>
              <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-2 text-title" data-testid="discussions-title">
                {currentCategory ? currentCategory.name : 'Discussions'}
              </h1>
              {currentCategory?.description && (
                <p className="text-base text-muted-foreground">{currentCategory.description}</p>
              )}
            </div>
            {user && (
              <Link to={`/community/${slug}/create-thread${selectedCategory !== 'all' ? `?category=${selectedCategory}` : ''}`}>
                <Button data-testid="new-thread-button">
                  <Plus className="mr-2 h-4 w-4" strokeWidth={1.5} />New Discussion
                </Button>
              </Link>
            )}
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3 mt-6" data-testid="search-filter-bar">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" strokeWidth={1.5} />
              <Input placeholder="Search discussions..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" data-testid="discussion-search-input" />
            </div>
            {!categoryId && categories.length > 0 && (
              <Select value={selectedCategory} onValueChange={handleCategoryChange}>
                <SelectTrigger className="w-full sm:w-[180px]" data-testid="category-filter">
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(cat => (
                    <SelectItem key={cat.category_id} value={cat.category_id}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-full sm:w-[160px]" data-testid="sort-select">
                <ArrowUpDown className="h-3.5 w-3.5 mr-2 text-muted-foreground" strokeWidth={1.5} />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Newest first</SelectItem>
                <SelectItem value="oldest">Oldest first</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Threads */}
        <div className="space-y-4" data-testid="threads-list">
          {filteredThreads.length === 0 ? (
            <div className="text-center py-16 bg-muted/30 rounded-xl">
              <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" strokeWidth={1.5} />
              <p className="text-muted-foreground mb-4">
                {searchQuery ? 'No discussions match your search.' : 'No discussions yet. Be the first to start a conversation!'}
              </p>
              {!searchQuery && user && (
                <Link to={`/community/${slug}/create-thread`}>
                  <Button>Start a Discussion</Button>
                </Link>
              )}
            </div>
          ) : (
            filteredThreads.map((thread) => (
              <Link key={thread.thread_id} to={`/community/${slug}/thread/${thread.thread_id}`} data-testid={`thread-item-${thread.thread_id}`}>
                <div className="bg-card border border-border rounded-xl p-6 hover:-translate-y-0.5 hover:shadow-md hover:border-border/80 transition-all duration-200">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <h3 className="text-xl font-medium mb-2" data-testid={`thread-title-${thread.thread_id}`}>
                        {thread.title}
                      </h3>
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{thread.content}</p>
                      <div className="flex items-center text-xs text-muted-foreground">
                        <span>by <span className="font-medium text-foreground">{thread.author_name}</span></span>
                        <span className="mx-2">&middot;</span>
                        <span>{new Date(thread.created_at).toLocaleDateString()}</span>
                        {thread.is_pinned && (
                          <>
                            <span className="mx-2">&middot;</span>
                            <span className="text-primary font-medium">Pinned</span>
                          </>
                        )}
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${thread.status === 'approved' ? 'bg-green-100 text-green-800' : thread.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                      {thread.status}
                    </span>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
