import React from 'react';
import type { MonthlyBudgetPlan, Language } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';

interface MonthlyPlanCardProps {
  plan: MonthlyBudgetPlan;
  language: Language;
}

export const MonthlyPlanCard: React.FC<MonthlyPlanCardProps> = ({ plan, language }) => {
  const t = TRACKER_TRANSLATIONS[language];
  const spentPercent = Math.min(100, Math.round((plan.plannedExpenses / plan.monthlyIncome) * 100));

  return (
    <section
      aria-label="Monthly Budget Plan"
      className="w-full bg-[#163D2E] text-white rounded-2xl p-5 sm:p-6 shadow-md border border-[#123628] flex flex-col gap-4"
    >
      {/* Top Label */}
      <div>
        <span className="text-[11px] sm:text-xs font-bold tracking-wider uppercase text-[#B4D5C2]">
          {t.leftAfterPlanLabel}
        </span>
        <div className="font-serif text-3xl sm:text-4xl lg:text-[40px] font-normal tracking-tight text-white mt-1">
          {plan.leftAfterPlan.toLocaleString()} RWF
        </div>
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
