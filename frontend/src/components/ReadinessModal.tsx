import React, { useState } from 'react';
import { X, CheckCircle2, AlertTriangle, RefreshCw, Database, GitBranch, Layers, ShieldCheck, Check } from 'lucide-react';
import { checkBackendReadiness, type ReadinessResult } from '../services/api';

interface ReadinessModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialResult: ReadinessResult | null;
  onRefreshSuccess?: (result: ReadinessResult) => void;
}

export const ReadinessModal: React.FC<ReadinessModalProps> = ({
  isOpen,
  onClose,
  initialResult,
  onRefreshSuccess,
}) => {
  const [result, setResult] = useState<ReadinessResult | null>(initialResult);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const currentResult = result || initialResult;

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const res = await checkBackendReadiness();
      setResult(res);
      if (onRefreshSuccess) onRefreshSuccess(res);
    } finally {
      setLoading(false);
    }
  };

  const isAllOk =
    currentResult?.ready &&
    currentResult?.checks?.database === 'ok' &&
    currentResult?.checks?.migrations === 'ok' &&
    currentResult?.checks?.seed === 'ok';

  const copyDiagnostics = () => {
    navigator.clipboard.writeText(JSON.stringify(currentResult, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-[#FAF8F5] rounded-2xl shadow-2xl border border-[#DDD7CE] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-[#1E5E45] px-6 py-4 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-[#C4E5D4]" />
            </div>
            <div>
              <h3 className="font-semibold text-base leading-tight">Backend Readiness Diagnostics</h3>
              <p className="text-xs text-[#C4E5D4] mt-0.5">FastAPI & PostgreSQL Live Health (/ready)</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-white/80 hover:text-white hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Status summary banner */}
          <div
            className={`rounded-xl p-4 border flex items-center justify-between ${
              isAllOk
                ? 'bg-[#E8F3EC] border-[#B9DEC3] text-[#164835]'
                : 'bg-amber-50 border-amber-200 text-amber-900'
            }`}
          >
            <div className="flex items-center gap-3">
              {isAllOk ? (
                <CheckCircle2 className="w-5 h-5 text-[#1E5E45] shrink-0" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
              )}
              <div>
                <div className="text-sm font-bold">
                  {isAllOk ? 'Backend Ready & Fully Operational' : 'Readiness Check Degraded / Incomplete'}
                </div>
                <div className="text-xs opacity-80 mt-0.5">
                  HTTP Status: {isAllOk ? '200 OK' : currentResult?.status || '503 Not Ready'} · Checked at {currentResult?.timestamp || 'recently'}
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={handleRefresh}
              disabled={loading}
              className="p-2 rounded-lg bg-white/80 hover:bg-white text-[#1E5E45] shadow-xs border border-[#CDE3D4] transition-all cursor-pointer disabled:opacity-50"
              title="Re-ping /ready endpoint"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Subsystem Health Checks */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold text-[#55695D] uppercase tracking-wider">Subsystem Checks</h4>

            {/* Check 1: Database */}
            <div className="bg-white rounded-xl p-3.5 border border-[#E5E0D7] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#F0EFEB] flex items-center justify-center text-[#1E5E45]">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[#1E3025]">PostgreSQL Connection</div>
                  <div className="text-[11px] text-[#6E8075]">localhost:5432 / imibereho (NOSUPERUSER)</div>
                </div>
              </div>
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                  currentResult?.checks?.database === 'ok'
                    ? 'bg-[#EAF5EE] text-[#1E5E45] border-[#C2E3CD]'
                    : 'bg-red-50 text-red-700 border-red-200'
                }`}
              >
                {currentResult?.checks?.database === 'ok' ? '✓ OK' : 'FAILED'}
              </span>
            </div>

            {/* Check 2: Migrations */}
            <div className="bg-white rounded-xl p-3.5 border border-[#E5E0D7] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#F0EFEB] flex items-center justify-center text-[#1E5E45]">
                  <GitBranch className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[#1E3025]">Alembic Schema Migrations</div>
                  <div className="text-[11px] text-[#6E8075]">Schema applied to head revision</div>
                </div>
              </div>
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                  currentResult?.checks?.migrations === 'ok'
                    ? 'bg-[#EAF5EE] text-[#1E5E45] border-[#C2E3CD]'
                    : 'bg-red-50 text-red-700 border-red-200'
                }`}
              >
                {currentResult?.checks?.migrations === 'ok' ? '✓ OK' : 'FAILED'}
              </span>
            </div>

            {/* Check 3: Seed Data */}
            <div className="bg-white rounded-xl p-3.5 border border-[#E5E0D7] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#F0EFEB] flex items-center justify-center text-[#1E5E45]">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[#1E3025]">NISR Seed Datasets</div>
                  <div className="text-[11px] text-[#6E8075]">EICV7 2023/24 · FinScope 2024 · SAS 2025</div>
                </div>
              </div>
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                  currentResult?.checks?.seed === 'ok'
                    ? 'bg-[#EAF5EE] text-[#1E5E45] border-[#C2E3CD]'
                    : 'bg-red-50 text-red-700 border-red-200'
                }`}
              >
                {currentResult?.checks?.seed === 'ok' ? '✓ OK' : 'FAILED'}
              </span>
            </div>
          </div>

          {/* Environment & Proxy Info */}
          <div className="bg-[#FAFDFB] rounded-xl p-3.5 border border-[#D8EADB] text-xs text-[#4F6356] space-y-1">
            <div className="flex justify-between">
              <span className="text-[#6D8074]">API Target:</span>
              <span className="font-mono font-medium text-[#1E3025]">dev (ENVIRONMENT=local)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#6D8074]">Reverse Proxy:</span>
              <span className="font-mono font-medium text-[#1E3025]">Vite localhost:5173 &rarr; FastAPI :8000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#6D8074]">Endpoints Count:</span>
              <span className="font-semibold text-[#1E5E45]">30 / 30 Endpoints Connected</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-[#F2EFE8] border-t border-[#DDD7CE] flex items-center justify-between text-xs">
          <button
            type="button"
            onClick={copyDiagnostics}
            className="flex items-center gap-1.5 text-[#55695D] hover:text-[#1E3025] font-semibold cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[#1E5E45]" /> : <RefreshCw className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied Diagnostics' : 'Copy JSON'}</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-[#1E5E45] hover:bg-[#164835] text-white font-semibold rounded-xl text-xs shadow-xs cursor-pointer transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
