import React from 'react';
import type { NavTab, Language } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import { Home, BarChart2, ShieldCheck, Sprout } from 'lucide-react';

interface BottomNavProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  language: Language;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  activeTab,
  onTabChange,
  language,
}) => {
  const t = TRACKER_TRANSLATIONS[language];

  const tabs: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    {
      id: 'tracker',
      label: t.navHomeTracker,
      icon: <Home className="w-4 h-4 sm:w-5 sm:h-5" />,
    },
    {
      id: 'district_advisor',
      label: t.navDistrictAdvisor,
      icon: <BarChart2 className="w-4 h-4 sm:w-5 sm:h-5" />,
    },
    {
      id: 'resilience',
      label: t.navResilience,
      icon: <ShieldCheck className="w-4 h-4 sm:w-5 sm:h-5" />,
    },
    {
      id: 'agro_swaps',
      label: t.navAgroSwaps,
      icon: <Sprout className="w-4 h-4 sm:w-5 sm:h-5" />,
    },
  ];

  return (
    <nav
      aria-label="Mobile Bottom Navigation"
      className="lg:hidden w-full bg-[#FAF8F4] border-t border-[#E5DFD4] sticky bottom-0 z-30 shadow-lg backdrop-blur-md"
    >
      <div className="max-w-4xl mx-auto px-2 sm:px-6 flex items-center justify-between">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onTabChange(tab.id)}
              className={`flex-1 py-2.5 sm:py-3 px-1 flex flex-col items-center justify-center gap-1 transition-colors relative cursor-pointer ${
                isActive
                  ? 'text-[#1E5E45] font-semibold'
                  : 'text-[#6C7D73] hover:text-[#1E5E45]'
              }`}
            >
              {/* Active top indicator pill */}
              {isActive && (
                <span className="absolute top-0 w-8 sm:w-12 h-0.5 bg-[#1E5E45] rounded-full" />
              )}
              <div
                className={`transition-transform duration-150 ${
                  isActive ? 'scale-110' : ''
                }`}
              >
                {tab.icon}
              </div>
              <span className="text-[10px] sm:text-[11px] text-center leading-tight max-w-[85px] sm:max-w-none line-clamp-2">
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
