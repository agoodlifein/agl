import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [myCommunities, setMyCommunities] = useState([]);

  useEffect(() => {
    api.get('/communities/my-communities').then(setMyCommunities).catch(() => {});
  }, []);

  const handleLogout = async () => { await logout(); navigate('/auth'); };

  const isAdmin = user?.is_super_admin;
  const managerCommunities = myCommunities.filter(c => c.role === 'community_manager');
  const memberCommunities = myCommunities.filter(c => c.role === 'member');

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6" data-testid="dashboard">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <div className="text-sm text-gray-500">Welcome, {user?.name}
            {isAdmin && <Badge className="ml-2" variant="destructive">Super Admin</Badge>}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate('/profile')} data-testid="profile-link">Profile</Button>
          <Button variant="ghost" size="sm" onClick={handleLogout} data-testid="logout-btn">Logout</Button>
        </div>
      </div>

      {isAdmin && (
        <Card>
          <CardHeader><CardTitle className="text-base">Admin Panel</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <Button className="w-full justify-start" variant="outline" onClick={() => navigate('/communities')} data-testid="admin-communities-link">
              Manage All Communities
            </Button>
          </CardContent>
        </Card>
      )}

      {managerCommunities.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Communities I Manage</CardTitle></CardHeader>
          <CardContent className="space-y-1">
            {managerCommunities.map(c => (
              <Link key={c.community.community_id} to={`/communities/${c.community.slug}`} className="block p-2 hover:bg-gray-50 rounded" data-testid={`managed-${c.community.slug}`}>
                <span className="font-medium">{c.community.name}</span>
                <Badge className="ml-2" variant="secondary">Manager</Badge>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}

      {memberCommunities.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">My Communities</CardTitle></CardHeader>
          <CardContent className="space-y-1">
            {memberCommunities.map(c => (
              <Link key={c.community.community_id} to={`/communities/${c.community.slug}`} className="block p-2 hover:bg-gray-50 rounded" data-testid={`member-${c.community.slug}`}>
                <span className="font-medium">{c.community.name}</span>
                <Badge className="ml-2" variant="outline">Member</Badge>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle className="text-base">Browse Communities</CardTitle></CardHeader>
        <CardContent>
          <Button variant="outline" onClick={() => navigate('/communities')} data-testid="browse-communities-link">Browse All Communities</Button>
        </CardContent>
      </Card>
    </div>
  );
}
