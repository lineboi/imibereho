import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  ChevronDown,
  ArrowRight,
  UserPlus,
  LogIn,
  MapPin,
  Users,
  Wallet,
} from 'lucide-react';
import {
  DISTRICTS,
  HOUSEHOLD_SIZES,
  INCOME_BRACKETS,
  TRANSLATIONS,
} from '../data/mockData';
import { fetchDistricts } from '../services/api';
import type { HouseholdProfile, Language } from '../types';

interface QuickStartFormProps {
  profile: HouseholdProfile;
  language: Language;
  onProfileChange: (updated: HouseholdProfile) => void;
  onSubmit: (profile: HouseholdProfile) => void;
  onCreateAccount: (profile: HouseholdProfile) => void;
  onSignIn: (profile: HouseholdProfile) => void;
}

export const QuickStartForm: React.FC<QuickStartFormProps> = ({
  profile,
  language,
  onProfileChange,
  onSubmit,
  onCreateAccount,
  onSignIn,
}) => {
  const t = TRANSLATIONS[language];
  const [districtOpen, setDistrictOpen] = useState(false);
  const [sizeOpen, setSizeOpen] = useState(false);
  const [incomeOpen, setIncomeOpen] = useState(false);
  const [districtsList, setDistrictsList] = useState<Array<{ id: string; name: string }>>(DISTRICTS);

  useEffect(() => {
    fetchDistricts().then((apiDistricts) => {
      if (apiDistricts && apiDistricts.length > 0) {
        setDistrictsList(
          apiDistricts.map((d) => ({
            id: d.code,
            name: d.name,
          }))
        );
      }
    });
  }, []);

  const handleSelectDistrict = (districtName: string) => {
    onProfileChange({ ...profile, district: districtName });
    setDistrictOpen(false);
  };

  const handleSelectSize = (sizeValue: string) => {
    onProfileChange({ ...profile, householdSize: sizeValue });
    setSizeOpen(false);
  };

  const handleSelectIncome = (incomeValue: string) => {
    onProfileChange({ ...profile, monthlyIncome: incomeValue });
    setIncomeOpen(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(profile);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
      {/* Starting point indicator */}
      <div className="flex items-center gap-2 text-[#245239] text-[13px] font-medium pt-1">
        <CheckCircle2 className="w-4 h-4 text-[#2E6B47] shrink-0 stroke-[2]" />
        <span>{t.quickStartBadge}</span>
      </div>

      {/* Field 1: District - Optional */}
      <div className="relative">
        <label className="block text-[12.5px] font-semibold text-[#1D3227] mb-1.5">
          {t.fieldDistrictLabel}
        </label>
        <div className="relative">
          <button
            type="button"
            onClick={() => {
              setDistrictOpen(!districtOpen);
              setSizeOpen(false);
              setIncomeOpen(false);
            }}
            aria-expanded={districtOpen}
            aria-label={t.fieldDistrictLabel}
            className="w-full bg-white border border-[#DDD7CE] hover:border-[#1E5E45]/60 focus:border-[#1E5E45] focus:ring-2 focus:ring-[#1E5E45]/15 rounded-xl px-3.5 py-2.5 text-left flex items-center justify-between text-[#1E2922] text-sm sm:text-[15px] font-normal shadow-xs transition-all cursor-pointer"
          >
            <span className="flex items-center gap-2 truncate">
              <MapPin className="w-4 h-4 text-[#667A6F] shrink-0" />
              <span className="font-medium text-[#1A2D23]">{profile.district || t.districtPlaceholder}</span>
            </span>
            <ChevronDown
              className={`w-4 h-4 text-[#667A6F] transition-transform duration-200 ${
                districtOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* District Dropdown Menu */}
          {districtOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setDistrictOpen(false)}
              />
              <div className="absolute left-0 right-0 top-full mt-1.5 max-h-60 overflow-y-auto bg-white rounded-xl shadow-lg border border-[#DDD7CE] z-50 py-1 divide-y divide-gray-100">
                <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-[#7A8A80] bg-[#FAF8F5] flex items-center justify-between">
                  <span>Select Rwandan District</span>
                  <span className="text-[10px] text-[#1E5E45] font-mono lowercase">GET /districts (live)</span>
                </div>
                {districtsList.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSelectDistrict(item.name)}
                    className={`w-full px-3.5 py-2 text-left text-sm flex items-center justify-between hover:bg-[#F2F6F3] transition-colors cursor-pointer ${
                      profile.district === item.name
                        ? 'bg-[#EBF3ED] font-semibold text-[#1A4B35]'
                        : 'text-[#2D3A32]'
                    }`}
                  >
                    <span>{item.name}</span>
                    <span className="text-[11px] text-[#7A8A80]">Rwanda</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Field 2 & 3: Household size & Monthly income side by side */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        {/* Household Size */}
        <div className="relative">
          <label className="block text-[12.5px] font-semibold text-[#1D3227] mb-1.5">
            {t.fieldHouseholdLabel}
          </label>
          <button
            type="button"
            onClick={() => {
              setSizeOpen(!sizeOpen);
              setDistrictOpen(false);
              setIncomeOpen(false);
            }}
            aria-expanded={sizeOpen}
            aria-label={t.fieldHouseholdLabel}
            className="w-full bg-white border border-[#DDD7CE] hover:border-[#1E5E45]/60 focus:border-[#1E5E45] focus:ring-2 focus:ring-[#1E5E45]/15 rounded-xl px-3 py-2.5 text-left flex items-center justify-between text-[#1E2922] text-sm sm:text-[15px] shadow-xs transition-all cursor-pointer"
          >
            <span className="flex items-center gap-1.5 truncate">
              <Users className="w-3.5 h-3.5 text-[#667A6F] shrink-0 hidden sm:inline" />
              <span className="font-medium text-[#1A2D23]">{profile.householdSize}</span>
            </span>
            <ChevronDown
              className={`w-4 h-4 text-[#667A6F] shrink-0 transition-transform duration-200 ${
                sizeOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {sizeOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setSizeOpen(false)}
              />
              <div className="absolute left-0 right-0 top-full mt-1.5 max-h-56 overflow-y-auto bg-white rounded-xl shadow-lg border border-[#DDD7CE] z-50 py-1">
                {HOUSEHOLD_SIZES.map((size) => (
                  <button
                    key={size.value}
                    type="button"
                    onClick={() => handleSelectSize(size.value)}
                    className={`w-full px-3.5 py-2 text-left text-sm hover:bg-[#F2F6F3] transition-colors cursor-pointer ${
                      profile.householdSize === size.value
                        ? 'bg-[#EBF3ED] font-semibold text-[#1A4B35]'
                        : 'text-[#2D3A32]'
                    }`}
                  >
                    {language === 'RW' ? size.labelRw : size.labelEn}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Monthly Income */}
        <div className="relative">
          <label className="block text-[12.5px] font-semibold text-[#1D3227] mb-1.5">
            {t.fieldIncomeLabel}
          </label>
          <button
            type="button"
            onClick={() => {
              setIncomeOpen(!incomeOpen);
              setDistrictOpen(false);
              setSizeOpen(false);
            }}
            aria-expanded={incomeOpen}
            aria-label={t.fieldIncomeLabel}
            className="w-full bg-white border border-[#DDD7CE] hover:border-[#1E5E45]/60 focus:border-[#1E5E45] focus:ring-2 focus:ring-[#1E5E45]/15 rounded-xl px-3 py-2.5 text-left flex items-center justify-between text-[#1E2922] text-sm sm:text-[15px] shadow-xs transition-all cursor-pointer"
          >
            <span className="flex items-center gap-1.5 truncate">
              <Wallet className="w-3.5 h-3.5 text-[#667A6F] shrink-0 hidden sm:inline" />
              <span className="font-medium text-[#1A2D23] truncate">{profile.monthlyIncome}</span>
            </span>
            <ChevronDown
              className={`w-4 h-4 text-[#667A6F] shrink-0 transition-transform duration-200 ${
                incomeOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {incomeOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setIncomeOpen(false)}
              />
              <div className="absolute left-0 right-0 top-full mt-1.5 max-h-56 overflow-y-auto bg-white rounded-xl shadow-lg border border-[#DDD7CE] z-50 py-1">
                {INCOME_BRACKETS.map((inc) => (
                  <button
                    key={inc.value}
                    type="button"
                    onClick={() => handleSelectIncome(inc.value)}
                    className={`w-full px-3.5 py-2 text-left text-sm hover:bg-[#F2F6F3] transition-colors cursor-pointer ${
                      profile.monthlyIncome === inc.value
                        ? 'bg-[#EBF3ED] font-semibold text-[#1A4B35]'
                        : 'text-[#2D3A32]'
                    }`}
                  >
                    {inc.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Helper text */}
      <p className="text-[11.5px] text-[#63766D] leading-relaxed -mt-1">
        {t.helperText}
      </p>

      {/* Primary Action Button: Continue without creating an account */}
      <button
        type="submit"
        className="w-full bg-[#1E5E45] hover:bg-[#164936] active:bg-[#11392A] text-white py-3.5 px-6 rounded-xl font-semibold text-sm sm:text-[15px] flex items-center justify-center gap-2 shadow-sm transition-all duration-150 cursor-pointer group mt-1"
      >
        <span>{t.continueWithoutAccountButton}</span>
        <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
      </button>

      {/* Divider */}
      <div className="relative flex items-center justify-center my-0.5">
        <div className="w-full border-t border-[#E5DFD4]" />
        <span className="bg-[#F8F6F0] lg:bg-white px-3 text-[11px] font-semibold text-[#788B7F] uppercase tracking-wider shrink-0">
          {t.orDividerText}
        </span>
      </div>

      {/* Secondary Action Options: Create Account & Sign In */}
      <div className="grid grid-cols-2 gap-2.5 sm:gap-3">
        <button
          type="button"
          onClick={() => onCreateAccount(profile)}
          className="w-full bg-white hover:bg-[#1E5E45] hover:text-white hover:border-[#1E5E45] hover:shadow-md active:bg-[#154633] border border-[#DDD7CE] text-[#1D3528] py-2.5 px-3 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-2xs transition-all duration-200 cursor-pointer group"
        >
          <UserPlus className="w-3.5 h-3.5 text-[#1E5E45] group-hover:text-white transition-colors duration-200 shrink-0" />
          <span className="truncate">{t.createAccountButton}</span>
        </button>

        <button
          type="button"
          onClick={() => onSignIn(profile)}
          className="w-full bg-white hover:bg-[#1E5E45] hover:text-white hover:border-[#1E5E45] hover:shadow-md active:bg-[#154633] border border-[#DDD7CE] text-[#1D3528] py-2.5 px-3 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-2xs transition-all duration-200 cursor-pointer group"
        >
          <LogIn className="w-3.5 h-3.5 text-[#1E5E45] group-hover:text-white transition-colors duration-200 shrink-0" />
          <span className="truncate">{t.signInButton}</span>
        </button>
      </div>
    </form>
  );
};
