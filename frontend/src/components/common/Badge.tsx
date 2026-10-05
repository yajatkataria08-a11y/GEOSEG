import React from 'react';
import { cn } from '../../utils/cn';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'blue' | 'green' | 'amber' | 'purple' | 'red' | 'gray';
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'blue',
  dot = false,
  className = '',
}) => {
  const styles = {
    blue: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/25',
    green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
    amber: 'bg-amber-500/10 text-amber-300 border-amber-500/25',
    purple: 'bg-purple-500/10 text-purple-300 border-purple-500/25',
    red: 'bg-rose-500/10 text-rose-300 border-rose-500/25',
    gray: 'bg-slate-500/10 text-slate-300 border-slate-500/25',
  };

  const dotColors = {
    blue: 'bg-cyan-400',
    green: 'bg-emerald-400',
    amber: 'bg-amber-400',
    purple: 'bg-purple-400',
    red: 'bg-rose-400',
    gray: 'bg-slate-400',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase tracking-wider border backdrop-blur-sm shadow-sm select-none',
        styles[variant],
        className
      )}
    >
      {dot && (
        <span className="relative flex h-1.5 w-1.5">
          <span className={cn('animate-ping absolute inline-flex h-full w-full rounded-full opacity-75', dotColors[variant])} />
          <span className={cn('relative inline-flex rounded-full h-1.5 w-1.5', dotColors[variant])} />
        </span>
      )}
      {children}
    </span>
  );
};
