import React from 'react';
import { AlertTriangle, RefreshCw, Terminal } from 'lucide-react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  code?: string;
  field?: string | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorAlert({
  title = 'Backend Communication Disruption',
  message,
  code = 'ERR_CONNECTION',
  field,
  onRetry,
  className = '',
}: ErrorAlertProps) {
  return (
    <div
      className={`rounded-xl border border-rose-500/30 bg-rose-950/20 p-5 text-rose-200 backdrop-blur-sm ${className}`}
    >
      <div className="flex items-start gap-3.5">
        <div className="p-2 rounded-lg bg-rose-500/20 text-rose-400 shrink-0">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-semibold text-rose-100 text-sm tracking-wide">{title}</h4>
            {code && (
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-rose-900/60 text-rose-300 border border-rose-700/50">
                {code}
              </span>
            )}
            {field && (
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-rose-900/40 text-rose-400 border border-rose-800/40">
                field: {field}
              </span>
            )}
          </div>
          <p className="mt-1.5 text-xs text-rose-300/90 leading-relaxed font-sans">{message}</p>

          <div className="mt-3 text-[11px] font-mono text-rose-400/80 bg-black/40 rounded p-2.5 border border-rose-900/40 flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            <span>Remediation: Verify backend process is running: <code>uvicorn app.main:app --port 8000</code></span>
          </div>

          {onRetry && (
            <div className="mt-4">
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-mono font-medium border border-rose-500/40 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry Handshake
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
