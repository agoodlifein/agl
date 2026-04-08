import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { communityApi } from '@/lib/communityApi';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowRight, Users, Calendar, MessageSquare, Heart, Lightbulb, Compass } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function HomePage() {
  const { user } = useAuth();
  const [communities, setCommunities] = useState([]);

  useEffect(() => {
    communityApi.list().then(setCommunities).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen" data-testid="home-page">
      {/* Hero Section */}
      <section className="relative py-20 md:py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-accent/20 to-transparent"></div>
        <div className="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-light tracking-tight mb-6 text-title" data-testid="hero-title">
            A Good Life
          </h1>
          <p className="text-base sm:text-lg text-foreground/80 max-w-2xl mx-auto leading-relaxed mb-8">
            A private curated platform for creators, artists, designers, founders, travellers, and thoughtful professionals to build meaningful communities.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/communities">
              <Button size="lg" className="w-full sm:w-auto" data-testid="explore-communities-button">
                Explore Communities
              </Button>
            </Link>
            {!user && (
              <Link to="/auth">
                <Button size="lg" variant="outline" className="w-full sm:w-auto" data-testid="join-button">
                  Join Now
                </Button>
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-16 md:py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-12">
            <p className="text-xs uppercase tracking-[0.2em] font-medium text-muted-foreground mb-4">Our Values</p>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-heading font-normal tracking-tight text-title">
              Building with Intention
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center" data-testid="value-card-empathy">
              <Heart className="mx-auto mb-4 h-8 w-8 text-primary" strokeWidth={1.5} />
              <h3 className="text-xl font-medium mb-3">Empathy</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Understanding and valuing different perspectives, experiences, and ways of being.
              </p>
            </div>
            <div className="text-center" data-testid="value-card-creativity">
              <Lightbulb className="mx-auto mb-4 h-8 w-8 text-primary" strokeWidth={1.5} />
              <h3 className="text-xl font-medium mb-3">Creativity</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Celebrating diverse forms of expression and thoughtful approaches to living.
              </p>
            </div>
            <div className="text-center" data-testid="value-card-connection">
              <Compass className="mx-auto mb-4 h-8 w-8 text-primary" strokeWidth={1.5} />
              <h3 className="text-xl font-medium mb-3">Connection</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Building authentic relationships and meaningful conversations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Communities Preview */}
      {communities.length > 0 && (
        <section className="py-20 md:py-32">
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
            <div className="text-center mb-12">
              <p className="text-xs uppercase tracking-[0.2em] font-medium text-muted-foreground mb-4">Communities</p>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-heading font-normal tracking-tight mb-4 text-title">
                Find Your Circle
              </h2>
              <p className="text-base text-muted-foreground max-w-2xl mx-auto">
                Explore communities built around shared interests and meaningful conversations.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="communities-grid">
              {communities.slice(0, 6).map((c) => (
                <Link key={c.community_id} to={`/community/${c.slug}`} data-testid={`community-card-${c.slug}`}>
                  <div className="bg-card border border-border rounded-xl p-8 hover:-translate-y-1 hover:shadow-md hover:border-border/80 transition-all duration-200 h-full">
                    <div className="flex items-center gap-3 mb-4">
                      {c.logo ? (
                        <img src={c.logo} alt={c.name} className="w-10 h-10 rounded-full object-cover" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <Users className="h-5 w-5 text-primary" strokeWidth={1.5} />
                        </div>
                      )}
                      <div>
                        <h3 className="text-xl font-medium">{c.name}</h3>
                        <span className="text-xs text-muted-foreground capitalize">{c.privacy}</span>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-4 line-clamp-2">
                      {c.description || 'Join this community'}
                    </p>
                    <div className="flex items-center text-sm font-medium text-primary">
                      Explore <ArrowRight className="ml-2 h-4 w-4" strokeWidth={1.5} />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            {communities.length > 6 && (
              <div className="text-center mt-8">
                <Link to="/communities">
                  <Button variant="outline">View All Communities</Button>
                </Link>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
