import React, { useState, useEffect } from 'react';
import { X, Code2, Sparkles, TrendingUp, UserCheck, KeyRound, ArrowRight, AlertCircle, LogIn, UserPlus, ShieldCheck } from 'lucide-react';
import type { HouseholdProfile, Language } from '../types';
import { TRANSLATIONS } from '../data/mockData';
import { registerHousehold, loginHousehold, getStoredToken, fetchBudgetBenchmark } from '../services/api';

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
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSuccess, setAuthSuccess] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(getStoredToken());
  const [dbBenchmarkCost, setDbBenchmarkCost] = useState<number | null>(null);

  const numericIncome = parseInt(profile.monthlyIncome.replace(/[^0-9]/g, ''), 10) || 180000;
  const householdCount = parseInt(profile.householdSize, 10) || 4;

  useEffect(() => {
    let active = true;
    if (isOpen) {
      fetchBudgetBenchmark(profile.district, householdCount).then((res) => {
        if (active && res) setDbBenchmarkCost(res.total);
      });
    }
    return () => {
      active = false;
    };
  }, [isOpen, profile.district, householdCount]);

  const t = TRANSLATIONS[language];

  if (!isOpen) return null;

  const estimatedCost = dbBenchmarkCost ?? Math.round(householdCount * 38000 + 45000);
  const balance = numericIncome - estimatedCost;
  const resilienceRatio = Math.min(100, Math.max(15, Math.round((numericIncome / estimatedCost) * 60)));

  const actionConfig = {
    continue: {
      endpoint: 'POST /api/v1/calculations/resilience-simulation',
      label: 'Direct Simulation (No Account)',
      statusLabel: 'Quick Session',
    },
    create_account: {
      endpoint: 'POST /api/v1/auth/register',
      label: 'Register Household Account',
      statusLabel: 'Account Registration',
    },
    sign_in: {
      endpoint: 'POST /api/v1/auth/login',
      label: 'Household Account Sign-In',
      statusLabel: 'Account Login',
    },
  }[mode];

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    setAuthSuccess(null);

    try {
      if (mode === 'create_account') {
        const districtClean = (profile.district || 'gasabo').toLowerCase().trim();
        const res = await registerHousehold({
          identifier: identifier.trim(),
          password,
          profile: {
            district: districtClean,
            householdSize: householdCount,
            monthlyIncome: numericIncome,
            currency: 'RWF',
            preferredLanguage: language === 'RW' ? 'RW' : 'EN',
          },
        });

        if (res.success && res.data) {
          setAuthToken(res.data.token);
          setAuthSuccess(`Account created successfully! User ID: ${res.data.user.id}`);
        } else {
          setAuthError(res.error || 'Failed to register account.');
        }
      } else if (mode === 'sign_in') {
        const res = await loginHousehold({
          identifier: identifier.trim(),
          password,
        });

        if (res.success && res.data) {
          setAuthToken(res.data.token);
          setAuthSuccess(`Signed in successfully! District: ${res.data.user.district}`);
        } else {
          setAuthError(res.error || 'Invalid credentials or user not found.');
        }
      }
    } finally {
      setAuthLoading(false);
    }
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
                Secure Account Access
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

          {/* Form View for Auth */}
          {mode !== 'continue' && (
            <form onSubmit={handleAuthSubmit} className="bg-white p-5 rounded-xl border border-[#E3DED4] space-y-4">
              <div className="text-xs font-bold uppercase tracking-wider text-[#2C4033] flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  {mode === 'create_account' ? <UserPlus className="w-4 h-4 text-[#1E5E45]" /> : <LogIn className="w-4 h-4 text-[#1E5E45]" />}
                  <span>{mode === 'create_account' ? 'Create Real Account' : 'Sign In with Credentials'}</span>
                </div>
              </div>

              {/* Preset Testing Credentials for Quick Presentation */}
              <div className="p-3 bg-[#FAF8F4] border border-[#E4DFD5] rounded-xl space-y-2">
                <div className="text-[11px] font-bold uppercase tracking-wider text-stone-500 flex items-center justify-between">
                  <span>Preset Testing Accounts</span>
                  <span className="text-[10px] text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded font-semibold">1-Click Fill</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIdentifier('citizen@imibereho.rw');
                      setPassword('Citizen2026!');
                    }}
                    className="p-2.5 text-left bg-white border border-stone-200 rounded-lg hover:border-[#1E5E45] hover:bg-emerald-50/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-stone-900 group-hover:text-[#1E5E45]">
                        Citizen Account
                      </span>
                      <span className="text-[9px] px-1.5 py-0.2 bg-stone-100 text-stone-600 rounded">Citizen</span>
                    </div>
                    <div className="text-[10.5px] text-stone-500 font-mono mt-1">
                      citizen@imibereho.rw
                    </div>
                    <div className="text-[10px] text-stone-400 font-mono">
                      Pass: Citizen2026!
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setIdentifier('planner@imibereho.rw');
                      setPassword('Planner2026!');
                    }}
                    className="p-2.5 text-left bg-white border border-stone-200 rounded-lg hover:border-[#123927] hover:bg-emerald-50/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-stone-900 group-hover:text-[#123927]">
                        Decision-Maker Account
                      </span>
                      <span className="text-[9px] px-1.5 py-0.2 bg-emerald-100 text-emerald-900 font-semibold rounded">Planner</span>
                    </div>
                    <div className="text-[10.5px] text-stone-500 font-mono mt-1">
                      planner@imibereho.rw
                    </div>
                    <div className="text-[10px] text-stone-400 font-mono">
                      Pass: Planner2026!
                    </div>
                  </button>
                </div>
              </div>

              {authError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{authError}</span>
                </div>
              )}

              {authSuccess && (
                <div className="p-3 bg-[#EAF5EE] border border-[#BDE0C8] text-[#164835] text-xs rounded-lg flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 shrink-0 text-[#1E5E45]" />
                  <span>{authSuccess}</span>
                </div>
              )}

              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-[#43574A] font-semibold mb-1">
                    Phone (+2507XXXXXXXX) or Email:
                  </label>
                  <input
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    className="w-full bg-[#FAF8F5] border border-[#D5CFC2] rounded-lg px-3 py-2 text-[#182C22] focus:outline-none focus:ring-1 focus:ring-[#1E5E45]"
                    placeholder="+250788123456 or user@example.com"
                  />
                </div>

                <div>
                  <label className="block text-[#43574A] font-semibold mb-1">
                    Password (min 8 characters):
                  </label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-[#FAF8F5] border border-[#D5CFC2] rounded-lg px-3 py-2 text-[#182C22] focus:outline-none focus:ring-1 focus:ring-[#1E5E45]"
                    placeholder="Min 8 characters"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-[11px] text-[#718478]">
                  {authToken ? '✓ Authenticated token in storage' : 'No active session'}
                </span>
                <button
                  type="submit"
                  disabled={authLoading}
                  className="px-4 py-2 bg-[#1E5E45] hover:bg-[#164835] text-white font-semibold rounded-lg text-xs shadow-xs cursor-pointer transition-colors disabled:opacity-50"
                >
                  {authLoading ? 'Submitting...' : mode === 'create_account' ? 'Create Account' : 'Sign In'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="bg-[#F0ECE3] px-6 py-3 border-t border-[#DDD7CE] flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-[11px] text-[#697A70]">
            Imibereho · Rwanda Household Financial Resilience
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
                <span>Enter Platform</span>
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
