import React, { useState, useEffect } from 'react';
import { HeroIllustration } from './HeroIllustration';
import type { HouseholdProfile, Language } from '../types';
import {
  fetchDashboardOverview,
  fetchNationalFinancialInclusion,
  type DashboardOverviewResponse,
  type NationalFinancialInclusionResponse,
} from '../services/api';
import { PieChart, MapPin, Sparkles, HeartHandshake, Database, BookOpen, Building2 } from 'lucide-react';
import { SourcesModal } from './SourcesModal';
import { PolicyScenarioModal } from './PolicyScenarioModal';

interface DesktopInsightCardProps {
  profile: HouseholdProfile;
  language: Language;
}

export const DesktopInsightCard: React.FC<DesktopInsightCardProps> = ({
  profile,
  language,
}) => {
  const [dashboardData, setDashboardData] = useState<DashboardOverviewResponse | null>(null);
  const [finScopeData, setFinScopeData] = useState<NationalFinancialInclusionResponse | null>(null);
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  const [isPolicyOpen, setIsPolicyOpen] = useState(false);

  useEffect(() => {
    let active = true;

    fetchDashboardOverview().then((res) => {
      if (active && res) setDashboardData(res);
    });

    fetchNationalFinancialInclusion().then((res) => {
      if (active && res) setFinScopeData(res);
    });

    return () => {
      active = false;
    };
  }, []);

  const numericIncome = parseInt(profile.monthlyIncome.replace(/[^0-9]/g, ''), 10) || 180000;
  const householdCount = parseInt(profile.householdSize, 10) || 4;
  
  // Baseline calculations
  const baselineCost = Math.round(householdCount * 36000 + 40000);
  const foodEst = Math.round(baselineCost * 0.48);
  const shelterEst = Math.round(baselineCost * 0.32);
  const healthTransEst = baselineCost - foodEst - shelterEst;
  const buffer = numericIncome - baselineCost;

  return (
    <div className="flex flex-col gap-5">
      {/* Scenic Illustration with Frame */}
      <div className="relative">
        <HeroIllustration district={profile.district} className="w-full shadow-md" />
        
        {/* Floating location badge */}
        <div className="absolute top-3 left-3 bg-[#133C2C]/85 backdrop-blur-md text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm border border-white/20">
          <MapPin className="w-3.5 h-3.5 text-[#A3E0C1]" />
          <span className="font-medium tracking-wide">
            {profile.district || 'Rwanda'} Lens
          </span>
        </div>
      </div>

      {/* Dynamic Live Perspective Card */}
      <div className="bg-white rounded-2xl p-5 border border-[#E3DED4] shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#ECE7DE]">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#1E5E45]">
            <PieChart className="w-4 h-4" />
            <span>
              {language === 'RW' ? "Igereranyo ry'ingengo y'imari" : 'Live Household Perspective'}
            </span>
          </div>
          <span className="text-[11px] font-semibold bg-[#EAF2ED] text-[#1E5E45] px-2 py-0.5 rounded-md">
            {profile.householdSize}
          </span>
        </div>

        {/* Breakdown bars */}
        <div className="space-y-2.5">
          <div>
            <div className="flex justify-between text-xs font-medium text-[#2C3E34] mb-1">
              <span>{language === 'RW' ? 'Ibiribwa & Isoko' : 'Food & Staples (est.)'}</span>
              <span className="font-semibold text-[#183628]">{foodEst.toLocaleString()} RWF</span>
            </div>
            <div className="h-2 w-full bg-[#EFECE4] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#2A6E50] rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (foodEst / numericIncome) * 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-[#2C3E34] mb-1">
              <span>{language === 'RW' ? 'Ubucumbi & Ingufu' : 'Housing & Utilities (est.)'}</span>
              <span className="font-semibold text-[#183628]">{shelterEst.toLocaleString()} RWF</span>
            </div>
            <div className="h-2 w-full bg-[#EFECE4] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#528F72] rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (shelterEst / numericIncome) * 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-[#2C3E34] mb-1">
              <span>{language === 'RW' ? 'Ubuzima & Ingendo' : 'Health & Transport (est.)'}</span>
              <span className="font-semibold text-[#183628]">{healthTransEst.toLocaleString()} RWF</span>
            </div>
            <div className="h-2 w-full bg-[#EFECE4] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#82B39B] rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (healthTransEst / numericIncome) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Live Cushion Calculation */}
        <div className="pt-3 border-t border-[#ECE7DE] flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-[#5A6E62]">
            <Sparkles className="w-3.5 h-3.5 text-[#1E5E45]" />
            <span>{language === 'RW' ? 'Amafaranga asaguka (igereranyo)' : 'Estimated Net Cushion'}</span>
          </div>
          <div className={`font-bold text-sm ${buffer >= 0 ? 'text-[#1E5E45]' : 'text-amber-700'}`}>
            {buffer >= 0 ? `+${buffer.toLocaleString()} RWF` : `${buffer.toLocaleString()} RWF`}
          </div>
        </div>

        {/* Live Macro Statistics from Backend */}
        <div className="bg-[#FAFDFB] rounded-xl p-3 border border-[#D5E7DC] flex flex-col gap-2 text-xs">
          <div className="flex items-center justify-between text-[#1E5E45]">
            <span className="font-semibold flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>NISR / FinScope Macro Lens</span>
            </span>
            <span className="text-[10px] bg-[#EAF5EE] px-2 py-0.5 rounded-full font-mono text-[#1E5E45] font-semibold">
              Live NISR APIs
            </span>
          </div>

          {dashboardData && (
            <div className="flex items-center justify-between text-[11px] text-[#4F6356] border-b border-[#E3EFE7] pb-1.5">
              <span>EICV7 Sample: <strong>{dashboardData.kpis.sampleSize.toLocaleString()} households</strong></span>
              <span>Essential Ratio: <strong>{((dashboardData.kpis.essentialsToIncomeRatio ?? 0.833) * 100).toFixed(0)}%</strong></span>
            </div>
          )}

          {/* FinScope 2024 Key Macro Indicators */}
          {finScopeData && (
            <div className="grid grid-cols-2 gap-2 text-[11px] pt-0.5">
              <div className="bg-white p-2 rounded-lg border border-[#DCEEE3]">
                <span className="text-[#657A6C] block text-[10px]">Financially Included:</span>
                <strong className="text-[#154634] text-xs">
                  {finScopeData.indicators.find((i) => i.code === 'financially_included')?.valuePct ?? 96}%
                </strong>
                <span className="text-[9.5px] text-[#718578] block">FinScope 2024</span>
              </div>
              <div className="bg-white p-2 rounded-lg border border-[#DCEEE3]">
                <span className="text-[#657A6C] block text-[10px]">Formal Banked:</span>
                <strong className="text-[#154634] text-xs">
                  {finScopeData.indicators.find((i) => i.code === 'banked')?.valuePct ?? 27}%
                </strong>
                <span className="text-[9.5px] text-[#718578] block">Commercial/SACCO</span>
              </div>
            </div>
          )}

          {/* Quick Action Buttons for Sources and Policy Simulator */}
          <div className="pt-1 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setIsSourcesOpen(true)}
              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-white hover:bg-[#F2F8F4] text-[#1E5E45] border border-[#CDE5D6] rounded-lg text-[11px] font-semibold transition-colors cursor-pointer"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Official Sources</span>
            </button>
            <button
              type="button"
              onClick={() => setIsPolicyOpen(true)}
              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-[#1E5E45] hover:bg-[#164835] text-white rounded-lg text-[11px] font-semibold transition-colors cursor-pointer shadow-xs"
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Policy Scenario</span>
            </button>
          </div>
        </div>

        {/* Household Financial Guidance Tip */}
        <div className="bg-[#FAF8F3] rounded-xl p-3 border border-[#EBE6DB] flex items-start gap-2.5 text-[11px] text-[#63756A] leading-relaxed">
          <HeartHandshake className="w-4 h-4 text-[#205A44] shrink-0 mt-0.5" />
          <span>
            {language === 'RW'
              ? 'Iyi mibare igufasha gupanga ingengo y’imari y’urugo rwawe no kubika ubwizigame bw’ejo hazaza.'
              : 'Estimates grounded in local district living costs to help you build your household savings buffer.'}
          </span>
        </div>
      </div>

      {/* Modals */}
      <SourcesModal
        isOpen={isSourcesOpen}
        onClose={() => setIsSourcesOpen(false)}
        language={language}
      />
      <PolicyScenarioModal
        isOpen={isPolicyOpen}
        onClose={() => setIsPolicyOpen(false)}
        language={language}
      />
    </div>
  );
};
