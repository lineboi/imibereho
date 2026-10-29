import React, { useState, useEffect } from 'react';
import type { HouseholdProfile, Language } from '../types';
import {
  fetchDistricts,
  fetchUserProfile,
  updateUserProfile,
  fetchBudgetBenchmark,
  getStoredToken,
  getStoredUser,
  clearStoredToken,
  type ApiDistrict,
} from '../services/api';
import {
  X,
  User,
  Shield,
  Building2,
  Users,
  Coins,
  PiggyBank,
  Sparkles,
  Check,
  AlertCircle,
  LogOut,
  LogIn,
  UserPlus,
} from 'lucide-react';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: HouseholdProfile;
  onProfileSaved: (newProfile: HouseholdProfile) => void;
  language: Language;
  onLanguageChange: (lang: Language) => void;
  onOpenAuthModal?: (mode: 'sign_in' | 'create_account') => void;
}

const ProfileModalContent: React.FC<ProfileModalProps> = ({
  onClose,
  profile,
  onProfileSaved,
  language,
  onLanguageChange,
  onOpenAuthModal,
}) => {
  const [districts, setDistricts] = useState<ApiDistrict[]>([]);
  const [district, setDistrict] = useState<string>(profile.district);
  const [householdSize, setHouseholdSize] = useState<number>(
    parseInt(profile.householdSize.replace(/[^0-9]/g, ''), 10) || 4
  );
  const [monthlyIncome, setMonthlyIncome] = useState<number>(
    parseInt(profile.monthlyIncome.replace(/[^0-9]/g, ''), 10) || 180000
  );
  const [plannedEssentials, setPlannedEssentials] = useState<number>(
    profile.plannedEssentials ?? 150000
  );
  const [savingsBuffer, setSavingsBuffer] = useState<number>(
    profile.savingsBuffer ?? 60000
  );
  const [role, setRole] = useState<'citizen' | 'decision_maker'>(
    profile.role || 'citizen'
  );
  const [preferredLanguage, setPreferredLanguage] = useState<Language>(language);

  const [isLoggedOut, setIsLoggedOut] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [autoFillLoading, setAutoFillLoading] = useState<boolean>(false);

  const token = !isLoggedOut ? getStoredToken() : null;
  const hasToken = !!token;
  const storedUser = !isLoggedOut ? getStoredUser() : null;

  useEffect(() => {
    let isMounted = true;
    fetchDistricts().then((items) => {
      if (isMounted && items && items.length > 0) {
        setDistricts(items);
      }
    });

    const authToken = getStoredToken();
    if (authToken) {
      fetchUserProfile(authToken).then((userProf) => {
        if (!isMounted || !userProf) return;
        setDistrict(userProf.district);
        setHouseholdSize(userProf.householdSize);
        setMonthlyIncome(userProf.monthlyIncome);
        if (userProf.plannedEssentials !== null) setPlannedEssentials(userProf.plannedEssentials);
        if (userProf.savingsBuffer !== null) setSavingsBuffer(userProf.savingsBuffer);
        if (userProf.role) setRole(userProf.role);
        if (userProf.preferredLanguage) {
          setPreferredLanguage(userProf.preferredLanguage);
          onLanguageChange(userProf.preferredLanguage);
        }
      });
    }

    return () => {
      isMounted = false;
    };
  }, [onLanguageChange]);

  const isRw = language === 'RW';

  // Auto-fill planned essentials from official live district benchmark
  const handleAutoFillBenchmark = async () => {
    setAutoFillLoading(true);
    try {
      const bench = await fetchBudgetBenchmark(district, householdSize);
      if (bench && bench.total > 0) {
        setPlannedEssentials(bench.total);
        setStatusMsg({
          type: 'success',
          text: isRw
            ? `Ingengo y'imari y'akarere ka ${bench.district.name} yakoreshejwe: ${bench.total.toLocaleString()} RWF`
            : `Updated planned essentials to official ${bench.district.name} benchmark: ${bench.total.toLocaleString()} RWF`,
        });
      }
    } catch {
      setStatusMsg({
        type: 'error',
        text: isRw ? 'Ntibyashobotse kubona ibipimo byakarere' : 'Failed to fetch district benchmark',
      });
    } finally {
      setAutoFillLoading(false);
    }
  };

  const handleSignOut = () => {
    clearStoredToken();
    setIsLoggedOut(true);
    setStatusMsg({
      type: 'success',
      text: isRw ? 'Wamaze gusohoka muri konte.' : 'Signed out of account. Session is now guest mode.',
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setStatusMsg(null);

    const safeIncome = Math.max(0, monthlyIncome);
    const safeEssentials = Math.max(0, plannedEssentials);
    const safeSavings = Math.max(0, savingsBuffer);
    const safeSize = Math.max(1, Math.min(20, householdSize));

    const updatedProfile: HouseholdProfile = {
      ...profile,
      district,
      householdSize: `${safeSize} ${safeSize === 1 ? (isRw ? 'umuntu' : 'person') : isRw ? 'abantu' : 'people'}`,
      monthlyIncome: `${safeIncome.toLocaleString()} RWF`,
      plannedEssentials: safeEssentials,
      savingsBuffer: safeSavings,
      preferredLanguage,
      role,
      updatedAt: new Date().toISOString(),
    };

    try {
      if (hasToken) {
        const dClean = district.toLowerCase();
        const patchRes = await updateUserProfile({
          district: dClean,
          householdSize: safeSize,
          monthlyIncome: safeIncome,
          plannedEssentials: safeEssentials,
          savingsBuffer: safeSavings,
          preferredLanguage,
          role,
        });

        if (patchRes) {
          updatedProfile.id = patchRes.id;
          setStatusMsg({
            type: 'success',
            text: isRw
              ? 'Umwirondoro wawe wabitswe neza!'
              : 'Profile successfully saved!',
          });
        } else {
          setStatusMsg({
            type: 'error',
            text: isRw
              ? 'Kunanirwa kubika kuri seriveri. Ubutumwa bwabitswe kuri iyi telefoni.'
              : 'Server sync failed. Saved to this device locally.',
          });
        }
      } else {
        setStatusMsg({
          type: 'success',
          text: isRw
            ? 'Umwirondoro wabitswe kuri iyi terefone (Guest Mode).'
            : 'Profile saved to this browser session (Guest Mode).',
        });
      }

      onProfileSaved(updatedProfile);
      if (preferredLanguage !== language) {
        onLanguageChange(preferredLanguage);
      }
    } catch (err) {
      console.error('Error saving profile:', err);
      setStatusMsg({
        type: 'error',
        text: isRw ? 'Habaye ikosa mu kubika umwirondoro.' : 'An error occurred while saving profile.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="profile-modal-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4"
    >
      <div className="bg-[#FAF8F3] border border-[#E3DED4] rounded-3xl shadow-2xl max-w-xl w-full max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-[#E8E2D6] bg-white flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#EAF5EE] border border-[#CDE5D6] flex items-center justify-center text-[#1E5E45]">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2
                id="profile-modal-title"
                className="font-serif text-xl sm:text-2xl text-[#143B2A] font-normal"
              >
                {isRw ? "Umwirondoro w'Urugo" : 'Household Profile'}
              </h2>
              <p className="text-xs text-[#5C7265]">
                {isRw
                  ? 'Ibisobanuro by’urugo rwawe n’ingengo y’imari'
                  : 'Manage household parameters, income target & baseline savings'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-[#F2EFE9] hover:bg-[#E5E1D8] text-[#55695D] flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Close Profile"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5">
          {/* Account Status Card */}
          <div className="p-4 rounded-2xl bg-white border border-[#E4DFD5] shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                  hasToken
                    ? 'bg-[#E8F3EC] text-[#1E5E45] border border-[#CEE3D5]'
                    : 'bg-[#FAF3E8] text-[#9E6211] border border-[#EED7B8]'
                }`}
              >
                <Shield className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#143B2A]">
                    {hasToken
                      ? isRw
                        ? 'Konte Yawe'
                        : 'Active Account'
                      : isRw
                      ? 'Umukoresha w’Agateganyo (Guest)'
                      : 'Guest / Local Session'}
                  </span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      hasToken ? 'bg-[#1E5E45]' : 'bg-[#D97706]'
                    }`}
                  />
                </div>
                <p className="text-[11.5px] text-[#55695D] mt-0.5">
                  {hasToken
                    ? storedUser?.identifier || 'Account Synced'
                    : isRw
                    ? 'Bika amakuru kuri konte yawe kugira ngo utayatakaza.'
                    : 'Sign in or register to sync across your devices.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
              {hasToken ? (
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="px-3 py-1.5 rounded-xl border border-[#D5DDD7] hover:bg-[#F2EFE8] text-xs font-semibold text-[#55695D] flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>{isRw ? 'Sohoka' : 'Sign Out'}</span>
                </button>
              ) : onOpenAuthModal ? (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onOpenAuthModal('sign_in');
                    }}
                    className="px-3 py-1.5 rounded-xl bg-[#E8F2EC] hover:bg-[#D7EAE0] text-[#1E5E45] border border-[#CCE3D5] text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    <span>{isRw ? 'Injira' : 'Sign In'}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onOpenAuthModal('create_account');
                    }}
                    className="px-3 py-1.5 rounded-xl bg-[#1E5E45] hover:bg-[#164835] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>{isRw ? 'Fungura Konte' : 'Register'}</span>
                  </button>
                </div>
              ) : null}
            </div>
          </div>

          {/* Feedback status message */}
          {statusMsg && (
            <div
              className={`p-3.5 rounded-xl text-xs flex items-center gap-2.5 border ${
                statusMsg.type === 'success'
                  ? 'bg-[#EBF5EE] border-[#CDE5D6] text-[#1E5E45]'
                  : 'bg-red-50 border-red-200 text-red-700'
              }`}
            >
              {statusMsg.type === 'success' ? (
                <Check className="w-4 h-4 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0" />
              )}
              <span>{statusMsg.text}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSave} className="space-y-4">
            {/* User Role Selection */}
            <div className="flex flex-col gap-2 p-3.5 rounded-xl bg-[#FAF8F3] border border-[#EBE7DF]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-[#1E5E45]" />
                  <span>{isRw ? 'Uruhare rw’umukoresha' : 'Platform Role & Workspace'}</span>
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded">
                  {role === 'decision_maker' ? 'Public Planner' : 'Citizen'}
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                <button
                  type="button"
                  onClick={() => setRole('citizen')}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    role === 'citizen'
                      ? 'bg-white border-[#1E5E45] shadow-xs ring-1 ring-[#1E5E45]'
                      : 'bg-white/60 border-stone-200 text-stone-600 hover:bg-white'
                  }`}
                >
                  <div className="text-xs font-bold text-stone-900">
                    Citizen Portal
                  </div>
                  <div className="text-[11px] text-stone-500 mt-0.5">
                    Family budgeting, agro-swaps & daily expense tracking
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setRole('decision_maker')}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    role === 'decision_maker'
                      ? 'bg-[#123927] text-white border-[#123927] shadow-xs'
                      : 'bg-white/60 border-stone-200 text-stone-600 hover:bg-white'
                  }`}
                >
                  <div className={`text-xs font-bold ${role === 'decision_maker' ? 'text-white' : 'text-stone-900'}`}>
                    Decision-Maker Workspace
                  </div>
                  <div className={`text-[11px] mt-0.5 ${role === 'decision_maker' ? 'text-emerald-200/80' : 'text-stone-500'}`}>
                    Macro overview, district heatmap & policy simulator
                  </div>
                </button>
              </div>
            </div>

            {/* District & Household Size Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* District */}
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="profile-district-select"
                  className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5"
                >
                  <Building2 className="w-3.5 h-3.5 text-[#1E5E45]" />
                  <span>{isRw ? 'Akarere utuyemo' : 'District'}</span>
                </label>
                <select
                  id="profile-district-select"
                  value={district.toLowerCase()}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full bg-white border border-[#DCD5C9] rounded-xl py-2.5 px-3 text-xs sm:text-sm font-medium text-[#182C22] focus:ring-2 focus:ring-[#1E5E45] focus:outline-none"
                >
                  {districts.length > 0 ? (
                    districts.map((d) => (
                      <option key={d.code} value={d.code}>
                        {d.name} {d.province ? `(${d.province})` : ''}
                      </option>
                    ))
                  ) : (
                    <option value={district}>{district}</option>
                  )}
                </select>
              </div>

              {/* Household Size */}
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="profile-household-size"
                  className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5"
                >
                  <Users className="w-3.5 h-3.5 text-[#1E5E45]" />
                  <span>{isRw ? 'Abagize urugo' : 'Household Size'}</span>
                </label>
                <div className="flex items-center bg-white border border-[#DCD5C9] rounded-xl overflow-hidden shadow-2xs h-10">
                  <button
                    type="button"
                    onClick={() => setHouseholdSize((prev) => Math.max(1, prev - 1))}
                    disabled={householdSize <= 1}
                    className="w-10 h-full flex items-center justify-center text-[#2D4537] hover:bg-[#F2EFE8] disabled:opacity-30 disabled:cursor-not-allowed border-r border-[#E3DDD1] cursor-pointer"
                  >
                    −
                  </button>
                  <input
                    id="profile-household-size"
                    type="number"
                    min={1}
                    max={20}
                    value={householdSize}
                    onChange={(e) => {
                      const val = parseInt(e.target.value, 10);
                      setHouseholdSize(isNaN(val) ? 1 : Math.max(1, Math.min(20, val)));
                    }}
                    className="flex-1 h-full text-center font-bold text-sm text-[#143B2A] focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setHouseholdSize((prev) => Math.min(20, prev + 1))}
                    disabled={householdSize >= 20}
                    className="w-10 h-full flex items-center justify-center text-[#2D4537] hover:bg-[#F2EFE8] disabled:opacity-30 disabled:cursor-not-allowed border-l border-[#E3DDD1] cursor-pointer"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>

            {/* Monthly Income Input */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="profile-monthly-income"
                className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5"
              >
                <Coins className="w-3.5 h-3.5 text-[#1E5E45]" />
                <span>{isRw ? 'Amafaranga yinjira ku kwezi (RWF)' : 'Monthly Income Target (RWF)'}</span>
              </label>
              <div className="relative">
                <input
                  id="profile-monthly-income"
                  type="text"
                  value={monthlyIncome.toLocaleString()}
                  onChange={(e) => {
                    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
                    setMonthlyIncome(isNaN(val) ? 0 : Math.min(100000000, val));
                  }}
                  className="w-full bg-white border border-[#DCD5C9] rounded-xl py-2.5 pl-3 pr-14 text-sm font-semibold text-[#182C22] focus:ring-2 focus:ring-[#1E5E45] focus:outline-none"
                />
                <span className="absolute right-3 top-2.5 text-xs font-semibold text-[#6E8175] pointer-events-none">
                  RWF
                </span>
              </div>
            </div>

            {/* Planned Essentials Input with Benchmark Helper */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="profile-planned-essentials"
                  className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#1E5E45]" />
                  <span>{isRw ? 'Ibikenerwa by’ibanze ku kwezi' : 'Planned Essentials Budget'}</span>
                </label>
                <button
                  type="button"
                  onClick={handleAutoFillBenchmark}
                  disabled={autoFillLoading}
                  className="text-[11px] text-[#1E5E45] hover:text-[#143B2A] font-semibold flex items-center gap-1 underline cursor-pointer disabled:opacity-50"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>
                    {autoFillLoading
                      ? '...'
                      : isRw
                      ? 'Koresha ibipimo by’akarere'
                      : 'Auto-fill with official benchmark'}
                  </span>
                </button>
              </div>
              <div className="relative">
                <input
                  id="profile-planned-essentials"
                  type="text"
                  value={plannedEssentials.toLocaleString()}
                  onChange={(e) => {
                    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
                    setPlannedEssentials(isNaN(val) ? 0 : Math.min(100000000, val));
                  }}
                  className="w-full bg-white border border-[#DCD5C9] rounded-xl py-2.5 pl-3 pr-14 text-sm font-semibold text-[#182C22] focus:ring-2 focus:ring-[#1E5E45] focus:outline-none"
                />
                <span className="absolute right-3 top-2.5 text-xs font-semibold text-[#6E8175] pointer-events-none">
                  RWF
                </span>
              </div>
            </div>

            {/* Savings Buffer Input with Quick Presets */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="profile-savings-buffer"
                  className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5"
                >
                  <PiggyBank className="w-3.5 h-3.5 text-[#1E5E45]" />
                  <span>{isRw ? 'Ububiko bwo gutabara (Savings Buffer)' : 'Emergency Savings Buffer'}</span>
                </label>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setSavingsBuffer(plannedEssentials)}
                    className="text-[10.5px] px-2 py-0.5 rounded-full bg-[#EAE5DC] text-[#425549] hover:bg-[#DDD7CC] transition-colors cursor-pointer"
                  >
                    {isRw ? 'Ukwezi 1' : '1 Month'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setSavingsBuffer(plannedEssentials * 3)}
                    className="text-[10.5px] px-2 py-0.5 rounded-full bg-[#EAE5DC] text-[#425549] hover:bg-[#DDD7CC] transition-colors cursor-pointer"
                  >
                    {isRw ? 'Amezi 3' : '3 Months'}
                  </button>
                </div>
              </div>
              <div className="relative">
                <input
                  id="profile-savings-buffer"
                  type="text"
                  value={savingsBuffer.toLocaleString()}
                  onChange={(e) => {
                    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
                    setSavingsBuffer(isNaN(val) ? 0 : Math.min(100000000, val));
                  }}
                  className="w-full bg-white border border-[#DCD5C9] rounded-xl py-2.5 pl-3 pr-14 text-sm font-semibold text-[#182C22] focus:ring-2 focus:ring-[#1E5E45] focus:outline-none"
                />
                <span className="absolute right-3 top-2.5 text-xs font-semibold text-[#6E8175] pointer-events-none">
                  RWF
                </span>
              </div>
            </div>

            {/* Language Preference */}
            <div className="flex items-center justify-between pt-2 border-t border-[#EDE7DD]">
              <span className="text-xs font-semibold text-[#2D4537]">
                {isRw ? 'Ururimi wifuza' : 'Preferred Language'}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPreferredLanguage('EN')}
                  className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    preferredLanguage === 'EN'
                      ? 'bg-[#1E5E45] text-white shadow-xs'
                      : 'bg-[#F2EFE9] text-[#55695D] hover:bg-[#E5E1D8]'
                  }`}
                >
                  English (EN)
                </button>
                <button
                  type="button"
                  onClick={() => setPreferredLanguage('RW')}
                  className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    preferredLanguage === 'RW'
                      ? 'bg-[#1E5E45] text-white shadow-xs'
                      : 'bg-[#F2EFE9] text-[#55695D] hover:bg-[#E5E1D8]'
                  }`}
                >
                  Kinyarwanda (RW)
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#EDE7DD]">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-xl border border-[#D5DDD7] hover:bg-[#F2EFE8] text-xs font-semibold text-[#55695D] transition-colors cursor-pointer"
              >
                {isRw ? 'Funga' : 'Cancel'}
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="px-5 py-2.5 rounded-xl bg-[#1E5E45] hover:bg-[#164835] text-white text-xs font-semibold transition-all shadow-xs disabled:opacity-50 cursor-pointer flex items-center gap-2"
              >
                {isSaving ? (
                  <span>{isRw ? 'Birimo kubikwa...' : 'Saving...'}</span>
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>
                      {isRw ? 'Bika Umwirondoro' : 'Save Profile'}
                    </span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export const ProfileModal: React.FC<ProfileModalProps> = (props) => {
  if (!props.isOpen) return null;
  return <ProfileModalContent {...props} />;
};
