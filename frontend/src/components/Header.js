import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LogOut, Menu, X, Home, Users, User, LayoutDashboard } from 'lucide-react';
import { Button } from './ui/button';

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/auth');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border" data-testid="header">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="flex justify-between items-center py-4">
          <Link to="/" className="flex items-center space-x-3" data-testid="logo-link">
            <span className="font-heading text-xl font-medium tracking-tight text-title">A Good Life</span>
          </Link>

          <nav className="hidden md:flex items-center space-x-1">
            <Link to="/" data-testid="nav-home">
              <Button variant="ghost" data-slot="nav-btn" className={isActive('/') ? 'bg-muted' : ''}>
                <Home className="mr-2 h-4 w-4" strokeWidth={1.5} />Home
              </Button>
            </Link>
            <Link to="/communities" data-testid="nav-communities">
              <Button variant="ghost" data-slot="nav-btn" className={isActive('/communities') ? 'bg-muted' : ''}>
                <Users className="mr-2 h-4 w-4" strokeWidth={1.5} />Communities
              </Button>
            </Link>
            {user && (
              <>
                <Link to="/profile" data-testid="nav-profile">
                  <Button variant="ghost" data-slot="nav-btn" className={isActive('/profile') ? 'bg-muted' : ''}>
                    <User className="mr-2 h-4 w-4" strokeWidth={1.5} />Profile
                  </Button>
                </Link>
                {user.is_super_admin && (
                  <Link to="/admin" data-testid="nav-admin">
                    <Button variant="ghost" data-slot="nav-btn" className={location.pathname.startsWith('/admin') ? 'bg-muted' : ''}>
                      <LayoutDashboard className="mr-2 h-4 w-4" strokeWidth={1.5} />Admin
                    </Button>
                  </Link>
                )}
              </>
            )}
            {!user ? (
              <Link to="/auth" data-testid="nav-login">
                <Button className="ml-2 btn-primary-hover">Sign In</Button>
              </Link>
            ) : (
              <Button variant="ghost" data-slot="nav-btn" onClick={handleLogout} data-testid="logout-button">
                <LogOut className="mr-2 h-4 w-4" strokeWidth={1.5} />Logout
              </Button>
            )}
          </nav>

          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            data-testid="mobile-menu-button"
          >
            {mobileMenuOpen ? <X strokeWidth={1.5} /> : <Menu strokeWidth={1.5} />}
          </button>
        </div>

        {mobileMenuOpen && (
          <nav className="md:hidden pb-4 space-y-2" data-testid="mobile-menu">
            <Link to="/" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="ghost" className="w-full justify-start">Home</Button>
            </Link>
            <Link to="/communities" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="ghost" className="w-full justify-start">Communities</Button>
            </Link>
            {user && (
              <>
                <Link to="/profile" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start">Profile</Button>
                </Link>
                {user.is_super_admin && (
                  <Link to="/admin" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="ghost" className="w-full justify-start">Admin</Button>
                  </Link>
                )}
              </>
            )}
            {!user ? (
              <Link to="/auth" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full">Sign In</Button>
              </Link>
            ) : (
              <Button variant="ghost" onClick={handleLogout} className="w-full justify-start">
                <LogOut className="mr-2 h-4 w-4" strokeWidth={1.5} />Logout
              </Button>
            )}
          </nav>
        )}
      </div>
    </header>
  );
}
