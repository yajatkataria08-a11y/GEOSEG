import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children?: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'accent' | 'danger' | 'ghost' | 'glass';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  icon?: React.ReactNode;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  loading = false,
  className = '',
  disabled,
  ...props
}) => {
  const variantStyles = {
    primary:
      'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-400/40 border border-cyan-400/30',
    accent:
      'bg-gradient-to-r from-cyan-400 via-sky-500 to-purple-600 hover:from-cyan-300 hover:via-sky-400 hover:to-purple-500 text-slate-950 font-bold shadow-lg shadow-cyan-400/30 hover:shadow-cyan-300/50 border border-white/20',
    secondary:
      'bg-white/[0.06] hover:bg-white/[0.12] text-slate-200 hover:text-white border border-white/10 hover:border-cyan-400/40 backdrop-blur-md shadow-sm',
    glass:
      'bg-cyan-950/30 hover:bg-cyan-900/40 text-cyan-200 hover:text-white border border-cyan-500/30 hover:border-cyan-400/60 backdrop-blur-md shadow-lg shadow-cyan-950/40',
    danger:
      'bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 hover:text-rose-100 border border-rose-500/30 hover:border-rose-500/50',
    ghost:
      'bg-transparent hover:bg-white/5 text-slate-300 hover:text-white',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
    md: 'px-4 py-2 text-sm rounded-xl gap-2',
    lg: 'px-6 py-3 text-base rounded-2xl gap-2.5 font-semibold',
    xl: 'px-8 py-4 text-lg rounded-2xl gap-3 font-bold',
  };

  return (
    <motion.button
      whileHover={disabled || loading ? undefined : { scale: 1.025, y: -1 }}
      whileTap={disabled || loading ? undefined : { scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      disabled={disabled || loading}
      className={cn(
        'relative inline-flex items-center justify-center font-sans tracking-wide transition-all select-none cursor-pointer disabled:opacity-50 disabled:pointer-events-none overflow-hidden group',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/15 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 pointer-events-none" />

      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : (
        icon && <span className="inline-flex items-center justify-center transition-transform group-hover:scale-110">{icon}</span>
      )}
      {children}
    </motion.button>
  );
};
