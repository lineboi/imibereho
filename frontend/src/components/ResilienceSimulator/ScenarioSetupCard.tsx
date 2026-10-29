import React, { useState } from 'react';
import type { Language } from '../../types';
import type { ShockType, ShockOption } from '../../data/mockResilienceData';
import {
  SHOCK_OPTIONS,
  REDUCTION_PERCENTAGES,
  DURATION_MONTHS,
  RESILIENCE_TRANSLATIONS,
} from '../../data/mockResilienceData';
import { ChevronDown, ArrowRight, ShieldAlert, SlidersHorizontal, RotateCcw, Wallet, Sparkles } from 'lucide-react';

interface ScenarioSetupCardProps {
  shockType: ShockType;
  onShockTypeChange: (s: ShockType) => void;
  reductionPct: number;
  onReductionPctChange: (pct: number) => void;
  durationMonths: number;
  onDurationMonthsChange: (m: number) => void;
  availableSavings: number;
  onSavingsChange: (savings: number) => void;
  baseMonthlyIncome?: number;
  onBaseMonthlyIncomeChange?: (income: number) => void;
  basePlannedExpenses?: number;
  onBasePlannedExpensesChange?: (expenses: number) => void;
  onResetBaselineToBenchmark?: () => void;
  language: Language;
  shockOptions?: ShockOption[];
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
  baseMonthlyIncome = 180000,
  onBaseMonthlyIncomeChange,
  basePlannedExpenses = 150000,
  onBasePlannedExpensesChange,
  onResetBaselineToBenchmark,
  language,
  shockOptions = SHOCK_OPTIONS,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];
  const isRw = language === 'RW';
  const [showBaselineCustomizer, setShowBaselineCustomizer] = useState(false);

  const handleSavingsInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
    onSavingsChange(isNaN(val) ? 0 : Math.max(0, val));
  };

  const handleIncomeInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!onBaseMonthlyIncomeChange) return;
    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
    onBaseMonthlyIncomeChange(isNaN(val) ? 0 : Math.max(0, val));
  };

  const handleExpensesInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!onBasePlannedExpensesChange) return;
    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
    onBasePlannedExpensesChange(isNaN(val) ? 0 : Math.max(0, val));
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
            {shockOptions.map((opt) => (
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

      {/* Household Baseline Customizer Toggle */}
      <div className="pt-2 border-t border-[#F0ECE4] flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowBaselineCustomizer((prev) => !prev)}
            className="text-xs font-semibold text-[#1E5E45] hover:text-[#123927] flex items-center gap-1.5 cursor-pointer"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>
              {showBaselineCustomizer
                ? isRw
                  ? 'Hisha Igereranyo ry’Urugo'
                  : 'Hide Household Baseline'
                : isRw
                ? 'Hindura Igereranyo ry’Urugo (Income & Expenses)'
                : 'Customize Household Baseline (Income & Expenses)'}
            </span>
          </button>
          {onResetBaselineToBenchmark && showBaselineCustomizer && (
            <button
              type="button"
              onClick={onResetBaselineToBenchmark}
              className="text-[11px] text-[#55695D] hover:text-[#1E5E45] flex items-center gap-1 cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>{isRw ? 'Subiza ku bipimo by’akarere' : 'Reset to Benchmark'}</span>
            </button>
          )}
        </div>

        {/* Expandable Baseline Form */}
        {showBaselineCustomizer && (
          <div className="bg-[#FAF8F4] border border-[#E3DED4] rounded-2xl p-3.5 space-y-3 animate-in fade-in duration-150">
            {/* Monthly Income Baseline */}
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-[#465A4F] flex items-center gap-1.5">
                <Wallet className="w-3.5 h-3.5 text-[#1E5E45]" />
                <span>{isRw ? 'Amafaranga yinjira' : 'Monthly Income Baseline'}</span>
              </span>
              <div className="flex items-center gap-1.5 bg-white border border-[#D5DDD7] rounded-xl px-2.5 py-1">
                <input
                  type="text"
                  value={baseMonthlyIncome.toLocaleString()}
                  onChange={handleIncomeInput}
                  className="w-24 text-right font-bold text-xs sm:text-sm text-[#143B2A] bg-transparent focus:outline-none"
                />
                <span className="text-[10.5px] font-semibold text-[#66796D]">RWF</span>
              </div>
            </div>

            {/* Planned Essentials Baseline */}
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-[#465A4F] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#1E5E45]" />
                <span>{isRw ? 'Ibikenerwa by’ibanze' : 'Planned Essentials Baseline'}</span>
              </span>
              <div className="flex items-center gap-1.5 bg-white border border-[#D5DDD7] rounded-xl px-2.5 py-1">
                <input
                  type="text"
                  value={basePlannedExpenses.toLocaleString()}
                  onChange={handleExpensesInput}
                  className="w-24 text-right font-bold text-xs sm:text-sm text-[#143B2A] bg-transparent focus:outline-none"
                />
                <span className="text-[10.5px] font-semibold text-[#66796D]">RWF</span>
              </div>
            </div>
          </div>
        )}
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
