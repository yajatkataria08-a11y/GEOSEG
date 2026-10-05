import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '../../utils/cn';

export interface CardProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
  children?: React.ReactNode;
  className?: string;
  interactive?: boolean;
  glow?: 'cyan' | 'purple' | 'emerald' | 'amber' | 'none';
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  interactive = false,
  glow = 'cyan',
  title,
  subtitle,
  action,
  icon,
  onClick,
  ...props
}) => {
  const glowStyles = {
    cyan: 'hover:border-cyan-500/40 hover:shadow-[0_8px_32px_rgba(6,182,212,0.15)]',
    purple: 'hover:border-purple-500/40 hover:shadow-[0_8px_32px_rgba(168,85,247,0.15)]',
    emerald: 'hover:border-emerald-500/40 hover:shadow-[0_8px_32px_rgba(16,185,129,0.15)]',
    amber: 'hover:border-amber-500/40 hover:shadow-[0_8px_32px_rgba(245,158,11,0.15)]',
    none: '',
  };

  return (
    <motion.div
      whileHover={interactive || onClick ? { y: -3, scale: 1.008 } : undefined}
      transition={{ type: 'spring', stiffness: 350, damping: 25 }}
      onClick={onClick}
      className={cn(
        'relative bg-[#0b132b]/60 backdrop-blur-xl border border-cyan-500/15 rounded-2xl p-6 shadow-xl shadow-black/40 transition-all duration-300',
        (interactive || onClick) && 'cursor-pointer hover:bg-[#0f1b3d]/80',
        glowStyles[glow],
        className
      )}
      {...props}
    >
      {(title || action || icon) && (
        <div className="flex items-start justify-between gap-4 mb-5">
          <div className="flex items-center gap-3.5">
            {icon && (
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shadow-inner">
                {icon}
              </div>
            )}
            <div>
              {title && <h3 className="text-base font-bold text-white tracking-tight">{title}</h3>}
              {subtitle && <p className="text-xs text-slate-400 mt-0.5 font-normal">{subtitle}</p>}
            </div>
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </motion.div>
  );
};
