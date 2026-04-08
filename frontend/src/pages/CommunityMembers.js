import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { communityApi } from '@/lib/communityApi';
import { ArrowLeft } from 'lucide-react';
import Avatar from '@/components/Avatar';

export default function CommunityMembers() {
  const { slug } = useParams();
  const [community, setCommunity] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    try {
      const [comm, mems] = await Promise.all([
        communityApi.get(slug),
        communityApi.members(slug),
      ]);
      setCommunity(comm);
      setMembers(mems);
    } catch (e) {
      console.error('Error loading members:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center"><div className="text-muted-foreground">Loading members...</div></div>;
  }

  return (
    <div className="min-h-screen py-12 md:py-20" data-testid="members-page">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <Link to={`/community/${slug}`} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-4">
          <ArrowLeft className="h-3.5 w-3.5" />{community?.name || 'Community'}
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-heading font-light tracking-tight mb-4 text-title" data-testid="members-title">
            Members
          </h1>
          <p className="text-base text-muted-foreground">
            Meet the individuals who make up this community.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="members-grid">
          {members.length === 0 ? (
            <div className="col-span-full text-center py-16 bg-muted/30 rounded-xl">
              <p className="text-muted-foreground">No members yet.</p>
            </div>
          ) : (
            members.map((member) => (
              <div key={member.membership_id || member.user_id} className="bg-card border border-border rounded-xl p-6 hover:-translate-y-1 hover:shadow-md hover:border-border/80 transition-all duration-200" data-testid={`member-card-${member.user_id}`}>
                <div className="flex items-start space-x-4">
                  <Avatar user={{ name: member.user_name || member.name }} size="lg" className="flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium truncate" data-testid={`member-name-${member.user_id}`}>
                      {member.user_name || member.name}
                    </h3>
                    <span className="text-xs text-muted-foreground capitalize">{member.role?.replace('_', ' ')}</span>
                    {member.joined_at && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Joined {new Date(member.joined_at).toLocaleDateString()}
                      </p>
                    )}
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
