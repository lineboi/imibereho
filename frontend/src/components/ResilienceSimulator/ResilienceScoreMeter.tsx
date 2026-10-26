import React from 'react';
import type { Language } from '../../types';
import { RESILIENCE_TRANSLATIONS } from '../../data/mockResilienceData';
import { Activity, ShieldCheck, Check } from 'lucide-react';

interface ResilienceScoreMeterProps {
  baselineScore: number;
  activeScore: number;
  activeLeversCount: number;
  language: Language;
}

export const ResilienceScoreMeter: React.FC<ResilienceScoreMeterProps> = ({
  baselineScore,
  activeScore,
  activeLeversCount,
  language,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];
  const isImproved = activeScore > baselineScore;

  return (
    <section
      aria-label="Household Resilience Health Score"
      className="w-full bg-white rounded-3xl border border-[#E3DED4] p-5 sm:p-7 shadow-xs flex flex-col gap-4"
    >
      <div className="flex items-center justify-between pb-2 border-b border-[#F0ECE4]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-medium text-[#133A29]">
              {t.resilienceScoreTitle}
            </h3>
            <p className="text-[11.5px] text-[#697B71]">
              {t.resilienceScoreSub}
            </p>
          </div>
        </div>

        <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#EBF6EE] text-[#1E5E45] border border-[#CFE7D6]">
          {isImproved ? `+${activeScore - baselineScore} pts boost` : 'Shock active'}
        </span>
      </div>

      {/* Main Score Comparison Display */}
      <div className="grid grid-cols-2 gap-3 divide-x divide-[#ECE6DC] bg-[#FAF8F4] border border-[#E8E2D6] rounded-2xl p-4">
        {/* Baseline Under Shock */}
        <div className="pr-2">
          <span className="text-[11px] font-semibold text-[#667A6E] block uppercase tracking-wider">
            {t.baselineScoreLabel}
          </span>
          <div className="font-serif text-3xl sm:text-4xl font-bold text-[#143B2A] mt-1">
            {baselineScore}
            <span className="text-sm font-sans font-normal text-[#667A6E] ml-1">/ 100</span>
          </div>
          <span className="text-[11px] font-medium text-amber-700 block mt-1">
            Moderate Buffer
          </span>
        </div>

        {/* With Action Levers */}
        <div className="pl-3 sm:pl-4">
          <span className="text-[11px] font-semibold text-[#667A6E] block uppercase tracking-wider">
            {t.actionScoreLabel}
          </span>
          <div className="font-serif text-3xl sm:text-4xl font-bold text-emerald-800 mt-1 flex items-baseline gap-1">
            <span>{activeScore}</span>
            <span className="text-sm font-sans font-normal text-[#667A6E]">/ 100</span>
          </div>
          <span className="text-[11px] font-medium text-emerald-700 block mt-1">
            {activeScore >= 80 ? 'High Resilience · Protected' : 'Moderate Resilience'}
          </span>
        </div>
      </div>

      {/* 3 Resilience Pillars */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1 text-xs">
        <div className="bg-[#FAF8F4] border border-[#EAE4D9] rounded-xl p-3 flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-[#1E5E45] shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-[#153D2A] block">{t.scorePillarBuffer}</span>
            <span className="text-[11px] text-[#697B71]">Liquid emergency reserves</span>
          </div>
        </div>

        <div className="bg-[#FAF8F4] border border-[#EAE4D9] rounded-xl p-3 flex items-start gap-2">
          <Check className="w-4 h-4 text-[#1E5E45] shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-[#153D2A] block">{t.scorePillarFlex}</span>
            <span className="text-[11px] text-[#697B71]">Discretionary spending agility</span>
          </div>
        </div>

        <div className="bg-[#FAF8F4] border border-[#EAE4D9] rounded-xl p-3 flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-[#153D2A] block">{t.scorePillarCommunity}</span>
            <span className="text-[11px] text-[#697B71]">
              {activeLeversCount > 0 ? 'Ibimina & mutual aid unlocked' : 'Informal safety nets'}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
