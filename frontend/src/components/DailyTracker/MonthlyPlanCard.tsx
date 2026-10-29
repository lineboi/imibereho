import React from 'react';
import type { MonthlyBudgetPlan, Language } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import { SlidersHorizontal } from 'lucide-react';

interface MonthlyPlanCardProps {
  plan: MonthlyBudgetPlan;
  language: Language;
  onEditPlan?: () => void;
}

export const MonthlyPlanCard: React.FC<MonthlyPlanCardProps> = ({ plan, language, onEditPlan }) => {
  const t = TRACKER_TRANSLATIONS[language];
  const spentPercent =
    plan.monthlyIncome > 0
      ? Math.min(100, Math.round((plan.plannedExpenses / plan.monthlyIncome) * 100))
      : 0;

  return (
    <section
      aria-label="Monthly Budget Plan"
      className="w-full bg-[#163D2E] text-white rounded-2xl p-5 sm:p-6 shadow-md border border-[#123628] flex flex-col gap-4"
    >
      {/* Top Label & Edit Action */}
      <div className="flex items-start justify-between">
        <div>
          <span className="text-[11px] sm:text-xs font-bold tracking-wider uppercase text-[#B4D5C2]">
            {t.leftAfterPlanLabel}
          </span>
          <div className="font-serif text-3xl sm:text-4xl lg:text-[40px] font-normal tracking-tight text-white mt-1">
            {plan.leftAfterPlan.toLocaleString()} RWF
          </div>
        </div>

        {onEditPlan && (
          <button
            type="button"
            onClick={onEditPlan}
            title="Edit target income & planned expenses"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-xs font-semibold text-white transition-colors cursor-pointer"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-[#B4D5C2]" />
            <span>{language === 'RW' ? 'Hindura' : 'Edit Plan'}</span>
          </button>
        )}
      </div>

      {/* Segmented / Dual-tone Progress Bar */}
      <div className="w-full">
        <div className="h-2 w-full bg-[#204E3B] rounded-full overflow-hidden flex gap-1 p-0.5">
          <div
            className="h-full bg-[#8EBC9F] rounded-full transition-all duration-500"
            style={{ width: `${spentPercent}%` }}
            title={`Planned: ${plan.plannedExpenses.toLocaleString()} RWF`}
          />
          <div
            className="h-full bg-white/85 rounded-full transition-all duration-500"
            style={{ width: `${100 - spentPercent}%` }}
            title={`Remaining: ${plan.leftAfterPlan.toLocaleString()} RWF`}
          />
        </div>
      </div>

      {/* Income & Planned Expenses Row */}
      <div className="grid grid-cols-2 gap-4 pt-1">
        <div>
          <span className="text-[11.5px] sm:text-xs text-[#A8CDB7] block">
            {t.monthlyIncomeLabel}
          </span>
          <span className="text-base sm:text-lg font-bold text-white tracking-tight">
            {plan.monthlyIncome.toLocaleString()} RWF
          </span>
        </div>

        <div>
          <span className="text-[11.5px] sm:text-xs text-[#A8CDB7] block">
            {t.plannedExpensesLabel}
          </span>
          <span className="text-base sm:text-lg font-bold text-white tracking-tight">
            {plan.plannedExpenses.toLocaleString()} RWF
          </span>
        </div>
      </div>
    </section>
  );
};
