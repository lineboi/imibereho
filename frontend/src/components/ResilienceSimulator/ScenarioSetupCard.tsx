import React from 'react';
import type { Language } from '../../types';
import type { ShockType } from '../../data/mockResilienceData';
import {
  SHOCK_OPTIONS,
  REDUCTION_PERCENTAGES,
  DURATION_MONTHS,
  RESILIENCE_TRANSLATIONS,
} from '../../data/mockResilienceData';
import { ChevronDown, ArrowRight, ShieldAlert } from 'lucide-react';

interface ScenarioSetupCardProps {
  shockType: ShockType;
  onShockTypeChange: (s: ShockType) => void;
  reductionPct: number;
  onReductionPctChange: (pct: number) => void;
  durationMonths: number;
  onDurationMonthsChange: (m: number) => void;
  availableSavings: number;
  onSavingsChange: (savings: number) => void;
  language: Language;
}

export const ScenarioSetupCard: React.FC<ScenarioSetupCardProps> = ({
  shockType,
  onShockTypeChange,
  reductionPct,
  onReductionPctChange,
  durationMonths,
  onDurationMonthsChange,
  availableSavings,
  onSavingsChange,
  language,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];

  const handleSavingsInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
    onSavingsChange(isNaN(val) ? 0 : Math.max(0, val));
  };

  return (
    <section
      aria-label="Set your shock scenario"
      className="w-full bg-white rounded-3xl border border-[#E3DED4] p-5 sm:p-7 shadow-xs flex flex-col gap-4"
    >
      <div className="flex items-center justify-between pb-1">
        <h2 className="font-serif text-xl sm:text-2xl font-normal text-[#123927]">
          {t.scenarioCardTitle}
        </h2>
        <div className="w-8 h-8 rounded-xl bg-[#FAF0E1] border border-[#EED7B8] flex items-center justify-center text-[#9E6211] shrink-0">
          <ShieldAlert className="w-4 h-4" />
        </div>
      </div>

      {/* Shock to Explore Dropdown */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="shock-explore-select" className="text-xs font-semibold text-[#3F5448]">
          {t.shockToExploreLabel}
        </label>
        <div className="relative">
          <select
            id="shock-explore-select"
            value={shockType}
            onChange={(e) => onShockTypeChange(e.target.value as ShockType)}
            className="w-full bg-[#FAF8F4] border border-[#DCD5C9] rounded-xl py-3 pl-3.5 pr-8 text-xs sm:text-sm font-medium text-[#182C22] appearance-none focus:outline-none focus:ring-2 focus:ring-[#1E5E45] cursor-pointer"
          >
            {SHOCK_OPTIONS.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {language === 'RW' ? opt.labelRw : opt.labelEn}
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-[#66786D] absolute right-3 top-3.5 pointer-events-none" />
        </div>
      </div>

      {/* Row: Income reduction & Duration */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Income Reduction */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="income-reduction-select" className="text-xs font-semibold text-[#3F5448]">
            {t.incomeReductionLabel}
          </label>
          <div className="relative">
            <select
              id="income-reduction-select"
              value={reductionPct}
              onChange={(e) => onReductionPctChange(Number(e.target.value))}
              className="w-full bg-[#FAF8F4] border border-[#DCD5C9] rounded-xl py-3 pl-3.5 pr-8 text-xs sm:text-sm font-medium text-[#182C22] appearance-none focus:outline-none focus:ring-2 focus:ring-[#1E5E45] cursor-pointer"
            >
              {REDUCTION_PERCENTAGES.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[#66786D] absolute right-3 top-3.5 pointer-events-none" />
          </div>
        </div>

        {/* Duration */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="duration-select" className="text-xs font-semibold text-[#3F5448]">
            {t.durationLabel}
          </label>
          <div className="relative">
            <select
              id="duration-select"
              value={durationMonths}
              onChange={(e) => onDurationMonthsChange(Number(e.target.value))}
              className="w-full bg-[#FAF8F4] border border-[#DCD5C9] rounded-xl py-3 pl-3.5 pr-8 text-xs sm:text-sm font-medium text-[#182C22] appearance-none focus:outline-none focus:ring-2 focus:ring-[#1E5E45] cursor-pointer"
            >
              {DURATION_MONTHS.map((m) => (
                <option key={m.value} value={m.value}>
                  {language === 'RW' ? m.labelRw : m.labelEn}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[#66786D] absolute right-3 top-3.5 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Available Savings Row */}
      <div className="flex items-center justify-between pt-2 pb-1 border-t border-[#F0ECE4] text-xs">
        <span className="font-semibold text-[#3F5448]">{t.availableSavingsLabel}</span>
        <div className="flex items-center gap-1.5 bg-[#FAF8F4] border border-[#DCD5C9] rounded-xl px-3 py-1.5">
          <input
            type="text"
            value={availableSavings.toLocaleString()}
            onChange={handleSavingsInput}
            className="w-24 text-right font-bold text-sm sm:text-base text-[#143B2A] bg-transparent focus:outline-none"
          />
          <span className="text-[11px] font-semibold text-[#66796D]">RWF</span>
        </div>
      </div>

      {/* Footer Notice */}
      <p className="text-[11px] text-[#788A80] leading-relaxed">
        {t.scenarioFooterNotice}
      </p>

      {/* Button: Scenario applied */}
      <div className="w-full py-3 px-4 rounded-xl border border-[#D0C9B8] bg-white flex items-center justify-center gap-2 text-xs sm:text-sm font-semibold text-[#1E5E45] shadow-2xs">
        <span>{t.scenarioAppliedBtn}</span>
        <ArrowRight className="w-4 h-4" />
      </div>
    </section>
  );
};
