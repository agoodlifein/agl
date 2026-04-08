import React from 'react';

export default function Avatar({ user, size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-12 h-12 text-base',
    lg: 'w-16 h-16 text-xl',
    xl: 'w-24 h-24 text-3xl'
  };

  const sizeClass = sizes[size] || sizes.md;
  const name = user?.name || user?.full_name || 'U';

  if (user?.picture || user?.profile_picture) {
    return (
      <img
        src={user.picture || user.profile_picture}
        alt={name}
        className={`${sizeClass} object-cover rounded-full ${className}`}
        data-testid="user-avatar"
      />
    );
  }

  return (
    <div
      className={`${sizeClass} bg-primary/10 rounded-full flex items-center justify-center font-body text-primary ${className}`}
      data-testid="user-avatar-placeholder"
    >
      {name.charAt(0).toUpperCase()}
    </div>
  );
}
