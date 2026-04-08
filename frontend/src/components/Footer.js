import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-border bg-muted/30 mt-20" data-testid="footer">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-heading text-xl mb-4 text-title">A Good Life</h3>
            <p className="text-sm text-muted-foreground leading-relaxed" data-testid="footer-brand-text">
              A curated community platform for creators, artists, designers, founders, travellers, and thoughtful professionals.
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-4">Platform</h4>
            <div className="space-y-2 text-sm">
              <Link to="/communities" className="block text-muted-foreground hover:text-foreground transition-colors">
                Communities
              </Link>
              <Link to="/auth" className="block text-muted-foreground hover:text-foreground transition-colors">
                Sign In
              </Link>
            </div>
          </div>
          <div>
            <h4 className="font-medium mb-4">Values</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Empathy, thoughtful living, creativity, diversity, contribution, and authentic connection.
            </p>
          </div>
        </div>
        <div className="mt-8 pt-8 border-t border-border text-center text-sm text-muted-foreground" data-testid="footer-copyright">
          &copy; 2026 A Good Life. Built with intention.
        </div>
      </div>
    </footer>
  );
}
