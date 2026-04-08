import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { communityApi } from '@/lib/communityApi';
import { useAuth } from '@/contexts/AuthContext';
import { Users, Lock, Globe, ArrowRight, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function CommunitiesPage() {
  const { user } = useAuth();
  const [communities, setCommunities] = useState([]);
  const [myCommunities, setMyCommunities] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      const all = await communityApi.list();
      setCommunities(all);
      if (user) {
        try {
          const mine = await communityApi.myCommunities();
          setMyCommunities(mine);
        } catch {}
      }
    } catch (e) {
      console.error('Error loading communities:', e);
    } finally {
      setLoading(false);
    }
  };

  const myCommSlugs = new Set(myCommunities.map(m => m.slug));

  const filtered = communities.filter(c => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return c.name.toLowerCase().includes(q) || (c.description || '').toLowerCase().includes(q);
  });

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-muted-foreground">Loading communities...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="communities-page">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="communities-title">
            Communities
          </h1>
          <p className="text-base text-muted-foreground max-w-2xl mb-6">
            Discover and join communities that resonate with you.
          </p>
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search communities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="communities-search-input"
            />
          </div>
        </div>

        {/* My Communities */}
        {myCommunities.length > 0 && (
          <div className="mb-12">
            <h2 className="text-xl font-heading font-normal mb-6 text-title">My Communities</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="my-communities-grid">
              {myCommunities.map((c) => (
                <Link key={c.community_id} to={`/community/${c.slug}`} data-testid={`my-community-${c.slug}`}>
                  <div className="bg-card border-2 border-primary/30 rounded-xl p-6 hover:-translate-y-1 hover:shadow-md transition-all duration-200">
                    <div className="flex items-center gap-3 mb-3">
                      {c.logo ? (
                        <img src={c.logo} alt={c.name} className="w-10 h-10 rounded-full object-cover" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <Users className="h-5 w-5 text-primary" strokeWidth={1.5} />
                        </div>
                      )}
                      <h3 className="text-lg font-medium">{c.name}</h3>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">{c.description}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* All Communities */}
        <div>
          <h2 className="text-xl font-heading font-normal mb-6 text-title">
            {myCommunities.length > 0 ? 'All Communities' : 'Explore Communities'}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="all-communities-grid">
            {filtered.length === 0 ? (
              <div className="col-span-full text-center py-16 bg-muted/30 rounded-xl">
                <p className="text-muted-foreground">
                  {searchQuery ? 'No communities found matching your search.' : 'No communities available yet.'}
                </p>
              </div>
            ) : (
              filtered.map((c) => (
                <Link key={c.community_id} to={`/community/${c.slug}`} data-testid={`community-card-${c.slug}`}>
                  <div className="bg-card border border-border rounded-xl p-6 hover:-translate-y-1 hover:shadow-md hover:border-border/80 transition-all duration-200 h-full">
                    <div className="flex items-center gap-3 mb-3">
                      {c.logo ? (
                        <img src={c.logo} alt={c.name} className="w-10 h-10 rounded-full object-cover" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <Users className="h-5 w-5 text-primary" strokeWidth={1.5} />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-medium truncate">{c.name}</h3>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          {c.privacy === 'private' ? <Lock className="h-3 w-3" /> : <Globe className="h-3 w-3" />}
                          <span className="capitalize">{c.privacy}</span>
                        </div>
                      </div>
                      {myCommSlugs.has(c.slug) && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">Joined</span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-4 line-clamp-2">
                      {c.description || 'Explore this community'}
                    </p>
                    <div className="flex items-center text-sm font-medium text-primary">
                      Explore <ArrowRight className="ml-2 h-4 w-4" strokeWidth={1.5} />
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
