import React from 'react';

export type BadgeVariant = 'emerald' | 'cyan' | 'amber' | 'rose' | 'slate' | 'violet';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  dot?: boolean;
  pulse?: boolean;
  className?: string;
}

export function Badge({
  children,
  variant = 'cyan',
  dot = false,
  pulse = false,
  className = '',
}: BadgeProps) {
  const variantStyles: Record<BadgeVariant, { bg: string; text: string; border: string; dotColor: string }> = {
    emerald: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      border: 'border-emerald-500/30',
      dotColor: 'bg-emerald-400',
    },
    cyan: {
      bg: 'bg-cyan-500/10',
      text: 'text-cyan-400',
      border: 'border-cyan-500/30',
      dotColor: 'bg-cyan-400',
    },
    amber: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      dotColor: 'bg-amber-400',
    },
    rose: {
      bg: 'bg-rose-500/10',
      text: 'text-rose-400',
      border: 'border-rose-500/30',
      dotColor: 'bg-rose-400',
    },
    slate: {
      bg: 'bg-slate-800/60',
      text: 'text-slate-400',
      border: 'border-slate-700/60',
      dotColor: 'bg-slate-400',
    },
    violet: {
      bg: 'bg-violet-500/10',
      text: 'text-violet-400',
      border: 'border-violet-500/30',
      dotColor: 'bg-violet-400',
    },
  };

  const style = variantStyles[variant] || variantStyles.cyan;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${style.bg} ${style.text} ${style.border} ${className}`}
    >
      {dot && (
        <span className="relative flex h-2 w-2">
          {pulse && (
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full ${style.dotColor} opacity-75`}
            />
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${style.dotColor}`} />
        </span>
      )}
      {children}
    </span>
  );
}
