import React, { useState } from 'react';
import { DecisionMakerSidebar } from './DecisionMakerSidebar';
import { MacroOverviewView } from './MacroOverviewView';
import { DistrictHeatmapView } from './DistrictHeatmapView';
import { PolicySimulatorView } from './PolicySimulatorView';
import { DataMethodologyView } from './DataMethodologyView';
import type { DecisionMakerTab } from '../../types';

interface DecisionMakerPageProps {
  onOpenProfile: () => void;
}

export const DecisionMakerPage: React.FC<DecisionMakerPageProps> = ({
  onOpenProfile,
}) => {
  const [activeTab, setActiveTab] = useState<DecisionMakerTab>('macro_overview');

  return (
    <div className="min-h-screen bg-[#FAF8F4] flex flex-col md:flex-row antialiased font-sans">
      {/* Sidebar */}
      <DecisionMakerSidebar
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
      />

      {/* Main View Area */}
      <main className="flex-1 overflow-x-hidden min-h-screen">
        {activeTab === 'macro_overview' && (
          <MacroOverviewView
            onNavigateTab={(tab) => setActiveTab(tab)}
            onOpenProfile={onOpenProfile}
          />
        )}
        {activeTab === 'district_heatmap' && (
          <DistrictHeatmapView
            onNavigateTab={(tab) => setActiveTab(tab)}
            onOpenProfile={onOpenProfile}
          />
        )}
        {activeTab === 'policy_simulator' && (
          <PolicySimulatorView
            onNavigateTab={(tab) => setActiveTab(tab)}
            onOpenProfile={onOpenProfile}
          />
        )}
        {activeTab === 'data_methodology' && (
          <DataMethodologyView
            onNavigateTab={(tab) => setActiveTab(tab)}
            onOpenProfile={onOpenProfile}
          />
        )}
      </main>
    </div>
  );
};
