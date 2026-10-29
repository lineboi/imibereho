import React from 'react';
import {
  BarChart3,
  MapPin,
  Sliders,
  BookOpen,
  Sparkles,
} from 'lucide-react';
import type { DecisionMakerTab } from '../../types';

interface DecisionMakerSidebarProps {
  activeTab: DecisionMakerTab;
  onTabChange: (tab: DecisionMakerTab) => void;
}

export const DecisionMakerSidebar: React.FC<DecisionMakerSidebarProps> = ({
  activeTab,
  onTabChange,
}) => {
  const navItems: Array<{
    id: DecisionMakerTab;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
  }> = [
    { id: 'macro_overview', label: 'Macro Overview', icon: BarChart3 },
    { id: 'district_heatmap', label: 'District Heatmap', icon: MapPin },
    { id: 'policy_simulator', label: 'Policy Simulator', icon: Sliders },
    { id: 'data_methodology', label: 'Data Methodology', icon: BookOpen },
  ];

  return (
    <aside className="w-64 bg-[#123927] text-white flex flex-col justify-between shrink-0 min-h-screen border-r border-[#1a4a33]">
      {/* Top Header & Branding */}
      <div>
        <div className="p-6 border-b border-[#1b4d36]/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#276a47] flex items-center justify-center text-emerald-200 shadow-inner">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-serif text-xl font-bold tracking-tight text-white leading-tight">
                Imibereho
              </h1>
            </div>
          </div>
          <div className="mt-2 text-[10px] font-bold tracking-widest uppercase text-emerald-300/80">
            Household Resilience Explorer
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-4 space-y-1.5" aria-label="Decision maker navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all text-left cursor-pointer ${
                  isActive
                    ? 'bg-[#1e583c] text-white shadow-sm ring-1 ring-emerald-400/30'
                    : 'text-emerald-100/70 hover:bg-[#1a4a33]/60 hover:text-white'
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? 'text-emerald-300' : 'text-emerald-200/60'
                  }`}
                />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Notes */}
      <div className="p-5 border-t border-[#1b4d36]/60 space-y-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold text-emerald-200">
            A shared view for public planning
          </p>
          <p className="text-[11px] text-emerald-100/70">
            For NISR, MINECOFIN & NGOs
          </p>
          <p className="text-[10px] text-emerald-100/50 leading-relaxed pt-1">
            Concept workspace. Not institutional advice or endorsement.
          </p>
          <div className="pt-2 text-[10px] text-emerald-300/60 uppercase tracking-wider font-mono">
            Baseline: English
          </div>
        </div>
      </div>
    </aside>
  );
};
