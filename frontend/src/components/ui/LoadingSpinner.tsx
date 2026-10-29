import React from 'react';
import { Activity, Zap } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <svg
      className={`animate-spin text-cyan-500 ${sizeClasses[size]} ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

export function LoadingState({ message = 'Establishing Telemetry Handshake...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm text-center">
      <div className="relative mb-4 flex items-center justify-center">
        <div className="absolute w-14 h-14 rounded-full bg-cyan-500/10 animate-ping" />
        <div className="relative flex items-center justify-center w-12 h-12 rounded-xl bg-slate-800 border border-cyan-500/30 text-cyan-400">
          <Zap className="w-6 h-6 animate-pulse" />
        </div>
      </div>
      <h3 className="text-sm font-mono font-semibold tracking-wider text-slate-200 uppercase">{message}</h3>
      <p className="mt-1 text-xs text-slate-500 font-mono">Querying FastAPI backend via ASGI Gateway...</p>
    </div>
  );
}
