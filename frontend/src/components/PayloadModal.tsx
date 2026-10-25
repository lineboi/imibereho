import React, { useState } from 'react';
import { X, Check, Copy, Code2, Sparkles, TrendingUp, UserCheck, KeyRound, ArrowRight } from 'lucide-react';
import type { HouseholdProfile, Language } from '../types';
import { TRANSLATIONS } from '../data/mockData';

interface PayloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: HouseholdProfile;
  language: Language;
  mode: 'continue' | 'create_account' | 'sign_in';
  onProceedToTracker?: () => void;
}

export const PayloadModal: React.FC<PayloadModalProps> = ({
  isOpen,
  onClose,
  profile,
  language,
  mode,
  onProceedToTracker,
}) => {
  const [copied, setCopied] = useState(false);
  const t = TRANSLATIONS[language];

  if (!isOpen) return null;

  // Derive mock financial insight object based on selections
  const numericIncome = parseInt(profile.monthlyIncome.replace(/[^0-9]/g, ''), 10) || 180000;
  const householdCount = parseInt(profile.householdSize, 10) || 4;
  const estimatedCost = Math.round(householdCount * 38000 + 45000);
  const balance = numericIncome - estimatedCost;
  const resilienceRatio = Math.min(100, Math.max(15, Math.round((numericIncome / estimatedCost) * 60)));

  const actionConfig = {
    continue: {
      endpoint: 'POST /api/v1/resilience/simulate',
      label: 'Direct Simulation (No Account)',
      statusLabel: 'Quick Session',
    },
    create_account: {
      endpoint: 'POST /api/v1/auth/register',
      label: 'New Account Creation',
      statusLabel: 'Account Registration',
    },
    sign_in: {
      endpoint: 'POST /api/v1/auth/login',
      label: 'Existing Account Sign-In',
      statusLabel: 'Account Login',
    },
  }[mode];

  const mockPayloadObject = {
    endpoint_target: actionConfig.endpoint,
    action_type: mode,
    status: 'frontend_mock_ready',
    household_profile: {
      district: profile.district,
      household_size: householdCount,
      household_size_raw: profile.householdSize,
      monthly_income_rwf: numericIncome,
      currency: 'RWF',
      timestamp: new Date().toISOString(),
    },
    client_metadata: {
      locale: language,
      platform: 'web',
    },
    mock_computed_preview: {
      estimated_baseline_cost_rwf: estimatedCost,
      estimated_monthly_buffer_rwf: balance,
      resilience_health_index: `${resilienceRatio}%`,
      recommended_buffer_months: balance > 0 ? 3 : 1,
    },
  };

  const jsonString = JSON.stringify(mockPayloadObject, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-[#FAF8F5] rounded-2xl shadow-2xl border border-[#DDD7CE] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-[#1E5E45] px-6 py-4 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
              <Code2 className="w-4 h-4 text-[#C4E5D4]" />
            </div>
            <div>
              <h3 className="font-semibold text-base leading-tight">
                {actionConfig.label}
              </h3>
              <p className="text-xs text-[#C4E5D4] mt-0.5">
                Frontend Mock Object · Target: {actionConfig.endpoint}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Status summary banner */}
          <div className="bg-white rounded-xl p-4 border border-[#E5DFD5] shadow-xs flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#1E5E45]">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Simulation Snapshot</span>
              </div>
              <div className="text-base font-semibold text-[#182C22] mt-0.5">
                {profile.district} · {profile.householdSize} · {profile.monthlyIncome}
              </div>
              <div className="text-xs text-[#607267] mt-0.5">
                Estimated living baseline: <span className="font-semibold">{estimatedCost.toLocaleString()} RWF/mo</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="bg-[#EBF3ED] px-3 py-1.5 rounded-lg border border-[#CCE2D4] text-center">
                <span className="block text-[10px] uppercase font-bold tracking-wider text-[#205A44]">
                  Resilience Score
                </span>
                <span className="text-lg font-bold text-[#164936]">
                  {resilienceRatio}%
                </span>
              </div>
            </div>
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-white p-3 rounded-xl border border-[#E5DFD5]">
              <div className="flex items-center gap-1.5 text-[#5F7166] mb-1 font-medium">
                <TrendingUp className="w-3.5 h-3.5 text-[#1E5E45]" />
                <span>Monthly Net Buffer</span>
              </div>
              <div className={`text-sm font-bold ${balance >= 0 ? 'text-[#1E5E45]' : 'text-amber-700'}`}>
                {balance >= 0 ? `+${balance.toLocaleString()} RWF` : `${balance.toLocaleString()} RWF`}
              </div>
            </div>

            <div className="bg-white p-3 rounded-xl border border-[#E5DFD5]">
              <div className="flex items-center gap-1.5 text-[#5F7166] mb-1 font-medium">
                {mode === 'sign_in' ? (
                  <KeyRound className="w-3.5 h-3.5 text-[#1E5E45]" />
                ) : (
                  <UserCheck className="w-3.5 h-3.5 text-[#1E5E45]" />
                )}
                <span>Action Selected</span>
              </div>
              <div className="text-sm font-semibold text-[#182C22]">
                {actionConfig.statusLabel}
              </div>
            </div>
          </div>

          {/* Code Viewer */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-[#3E5247]">
                Frontend Payload Object:
              </span>
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-[#1E5E45] hover:text-[#133D2D] font-medium bg-[#EBF3ED] px-2.5 py-1 rounded-md transition-colors cursor-pointer"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy JSON</span>
                  </>
                )}
              </button>
            </div>
            <pre className="bg-[#14201A] text-[#BEE3CE] p-4 rounded-xl text-xs font-mono overflow-x-auto max-h-56 leading-relaxed border border-[#23382E]">
              <code>{jsonString}</code>
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-[#F0ECE3] px-6 py-3 border-t border-[#DDD7CE] flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-[11px] text-[#697A70]">
            Ready to connect to backend endpoint as soon as provided.
          </p>
          <div className="flex items-center gap-2 self-end sm:self-auto">
            {onProceedToTracker && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onProceedToTracker();
                }}
                className="bg-[#1E5E45] hover:bg-[#164835] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5"
              >
                <span>Continue to Daily Tracker</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="bg-white hover:bg-gray-100 text-[#2D3A32] border border-[#D5CFBE] text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
            >
              {t.closeModal}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
