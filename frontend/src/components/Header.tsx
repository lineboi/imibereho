import React from 'react';
import type { Language, NavTab } from '../types';
import { TRACKER_TRANSLATIONS } from '../data/mockTrackerData';
import { Home, BarChart2, ShieldCheck, Sprout } from 'lucide-react';

interface HeaderProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  activeTab?: NavTab;
  onTabChange?: (tab: NavTab) => void;
  onLogoClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  onLanguageChange,
  activeTab = 'tracker',
  onTabChange,
  onLogoClick,
}) => {
  const t = TRACKER_TRANSLATIONS[language];

  const tabs: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    {
      id: 'tracker',
      label: t.navHomeTracker,
      icon: <Home className="w-4 h-4" />,
    },
    {
      id: 'district_advisor',
      label: t.navDistrictAdvisor,
      icon: <BarChart2 className="w-4 h-4" />,
    },
    {
      id: 'resilience',
      label: t.navResilience,
      icon: <ShieldCheck className="w-4 h-4" />,
    },
    {
      id: 'agro_swaps',
      label: t.navAgroSwaps,
      icon: <Sprout className="w-4 h-4" />,
    },
  ];

  return (
    <header className="w-full bg-[#FAF8F3] border-b border-[#EBE7DF] sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
        {/* Brand / Logo */}
        <button
          type="button"
          onClick={onLogoClick}
          className="flex items-center gap-2.5 cursor-pointer text-left focus:outline-none shrink-0"
        >
          <div className="w-9 h-9 rounded-xl bg-[#1E5E45] flex items-center justify-center text-white shadow-sm ring-1 ring-[#1E5E45]/20 shrink-0">
            {/* Custom stylized sprout leaf icon */}
            <svg
              className="w-5 h-5 text-[#E6F4EA]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M7 20h10" />
              <path d="M10 20c5.5-2.5.8-6.4 3-10" />
              <path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-2-4.2 2.8-.5 3.9.2 4.5.8z" />
              <path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1.2-1 1.7-2.7 1.7-4.6-2.9-.2-4.2.9-4.9 2z" />
            </svg>
          </div>
          <span className="font-serif font-bold text-xl md:text-2xl text-[#143B2A] tracking-tight">
            Imibereho
          </span>
        </button>

        {/* Center: Desktop Navigation Tabs (All on same nav bar, hidden on mobile) */}
        {onTabChange && (
          <nav aria-label="Main Navigation" className="hidden lg:flex items-center gap-1">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-2 py-2 px-3 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#EAF3ED] text-[#1E5E45]'
                      : 'text-[#586C60] hover:text-[#183928] hover:bg-[#F2EFE8]'
                  }`}
                >
                  <div className={isActive ? 'text-[#1E5E45]' : 'text-[#6D7F74]'}>
                    {tab.icon}
                  </div>
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        )}

        {/* Right side: Language Switcher EN / RW */}
        <div className="flex items-center text-sm font-semibold tracking-wider shrink-0">
          <button
            type="button"
            onClick={() => onLanguageChange('EN')}
            className={`px-1.5 py-0.5 transition-colors cursor-pointer ${
              language === 'EN'
                ? 'text-[#143B2A] font-bold border-b-2 border-[#1E5E45]'
                : 'text-[#6B7D74] hover:text-[#143B2A]'
            }`}
          >
            EN
          </button>
          <span className="text-[#A2B0A7] mx-0.5">/</span>
          <button
            type="button"
            onClick={() => onLanguageChange('RW')}
            className={`px-1.5 py-0.5 transition-colors cursor-pointer ${
              language === 'RW'
                ? 'text-[#143B2A] font-bold border-b-2 border-[#1E5E45]'
                : 'text-[#6B7D74] hover:text-[#143B2A]'
            }`}
          >
            RW
          </button>
        </div>
      </div>
    </header>
  );
};
