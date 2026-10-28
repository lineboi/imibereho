import React from 'react';
import type { Language } from '../../types';
import type { StressTestScenario } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';
import type { StressTestResponse } from '../../services/api';
import { Activity, Zap, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface StressTestChipsProps {
  scenario: StressTestScenario;
  onScenarioChange: (s: StressTestScenario) => void;
  language: Language;
  netSavingsMonthly: number;
  apiResult?: StressTestResponse | null;
}

export const StressTestChips: React.FC<StressTestChipsProps> = ({
  scenario,
  onScenarioChange,
  language,
  netSavingsMonthly,
  apiResult,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];

  const chips: { id: StressTestScenario; label: string; icon: React.ReactNode }[] = [
    {
      id: 'none',
      label: t.chipBaseline,
      icon: <Activity className="w-3.5 h-3.5" />,
    },
    {
      id: 'food_inflation',
      label: t.chipFoodShock,
      icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />,
    },
    {
      id: 'rent_surge',
      label: t.chipRentSurge,
      icon: <TrendingUp className="w-3.5 h-3.5 text-rose-500" />,
    },
    {
      id: 'annual_savings',
      label: t.chipAnnual,
      icon: <Zap className="w-3.5 h-3.5 text-emerald-600" />,
    },
  ];

  return (
    <div className="w-full flex flex-col gap-2.5 bg-white rounded-2xl border border-[#E3DED4] p-3.5 sm:p-4 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase tracking-wider text-[#355D47] flex items-center gap-1.5">
          <Activity className="w-4 h-4 text-[#1E5E45]" />
          <span>{t.stressTestTitle}</span>
        </span>

        {/* Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {chips.map((chip) => {
            const isActive = scenario === chip.id;
            return (
              <button
                key={chip.id}
                type="button"
                onClick={() => onScenarioChange(chip.id)}
                className={`text-xs font-semibold py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer ${
                  isActive
                    ? 'bg-[#1E5E45] text-white shadow-2xs'
                    : 'bg-[#FAF8F4] text-[#475C50] hover:bg-[#EFEAE0] border border-[#DDD6C8]'
                }`}
              >
                {chip.icon}
                <span>{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Scenario Explanatory Callout */}
      {scenario === 'food_inflation' && (
        <div className="bg-[#FFF8EC] border border-[#F6E1B6] rounded-xl p-2.5 text-xs text-[#8A5408] flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            Simulating +15% staple food inflation: Districts with strong agricultural co-ops and local farm-gate access absorb food price volatility significantly better than transport-dependent transit hubs.
          </span>
        </div>
      )}

      {scenario === 'rent_surge' && (
        <div className="bg-[#FFF4F2] border border-[#FED7D2] rounded-xl p-2.5 text-xs text-[#9B2C1B] flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-rose-600 shrink-0" />
          <span>
            Simulating +10% housing rent inflation: High rental density in Kigali increases family overhead rapidly, whereas secondary city rental baselines remain moderate and stable.
          </span>
        </div>
      )}

      {apiResult && (scenario === 'food_inflation' || scenario === 'rent_surge') && (
        <div className="bg-[#EBF5EE] border border-[#CCE3D5] rounded-xl p-2.5 text-xs text-[#1E5E45] flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#1E5E45] shrink-0" />
            <span>
              Backend Stress Impact: Stressed basket total <strong>{apiResult.stressedTotal.toLocaleString()} RWF</strong> (+{apiResult.monthlyIncrease.toLocaleString()} RWF/mo, runway impact: {apiResult.bufferImpactMonths} mo)
            </span>
          </div>
          <span className="text-[10px] bg-white text-[#1E5E45] px-2 py-0.5 rounded border border-[#CCE3D5] font-mono shrink-0">
            POST /calculations/stress-test
          </span>
        </div>
      )}

      {scenario === 'annual_savings' && (
        <div className="bg-[#EBF7EE] border border-[#CCE8D5] rounded-xl p-2.5 text-xs text-[#175238] flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              Cumulative Annualized Impact: Living in a lower-cost district generates an estimated{' '}
              <strong>{(Math.abs(netSavingsMonthly) * 12).toLocaleString()} RWF/year</strong> in total net savings for your family.
            </span>
          </div>
          <span className="font-bold text-emerald-800 text-sm shrink-0">
            ~{(Math.abs(netSavingsMonthly) * 12).toLocaleString()} RWF/yr
          </span>
        </div>
      )}
    </div>
  );
};
