import React, { useState } from 'react';
import type { Language, MonthlyBudgetPlan } from '../../types';
import { fetchBudgetBenchmark, updateUserProfile, getStoredToken } from '../../services/api';
import { X, Check, Sparkles, Coins, Wallet } from 'lucide-react';

interface EditBudgetPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan: MonthlyBudgetPlan;
  onSavePlan: (income: number, expenses: number) => void;
  language: Language;
}

export const EditBudgetPlanModal: React.FC<EditBudgetPlanModalProps> = ({
  isOpen,
  onClose,
  plan,
  onSavePlan,
  language,
}) => {
  const isRw = language === 'RW';
  const [income, setIncome] = useState<number>(plan.monthlyIncome);
  const [expenses, setExpenses] = useState<number>(plan.plannedExpenses);
  const [loadingBenchmark, setLoadingBenchmark] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleAutoFillBenchmark = async () => {
    setLoadingBenchmark(true);
    try {
      const sizeNum = parseInt(plan.householdSize.replace(/[^0-9]/g, ''), 10) || 4;
      const bench = await fetchBudgetBenchmark(plan.district, sizeNum);
      if (bench && bench.total > 0) {
        setExpenses(bench.total);
      }
    } catch (err) {
      console.warn('Failed to fetch benchmark:', err);
    } finally {
      setLoadingBenchmark(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    const safeIncome = Math.max(0, income);
    const safeExpenses = Math.max(0, expenses);

    try {
      const token = getStoredToken();
      if (token) {
        await updateUserProfile({
          monthlyIncome: safeIncome,
          plannedEssentials: safeExpenses,
        });
      }
      onSavePlan(safeIncome, safeExpenses);
      onClose();
    } catch (err) {
      console.warn('Error updating plan:', err);
      onSavePlan(safeIncome, safeExpenses);
      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-plan-modal-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4"
    >
      <div className="bg-[#FAF8F3] border border-[#E3DED4] rounded-3xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-[#E8E2D6] bg-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#E8F3EC] border border-[#CDE5D6] flex items-center justify-center text-[#1E5E45]">
              <Wallet className="w-4 h-4" />
            </div>
            <div>
              <h2
                id="edit-plan-modal-title"
                className="font-serif text-lg sm:text-xl font-normal text-[#143B2A]"
              >
                {isRw ? "Hindura Ingengo y'Imari" : 'Edit Monthly Budget Plan'}
              </h2>
              <p className="text-[11px] text-[#55695D]">
                {plan.district} · {plan.householdSize} · {plan.month}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-full bg-[#F2EFE9] hover:bg-[#E5E1D8] text-[#55695D] flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Monthly Income Input */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="edit-income-input"
              className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5"
            >
              <Coins className="w-3.5 h-3.5 text-[#1E5E45]" />
              <span>{isRw ? 'Amafaranga yinjira ku kwezi' : 'Monthly Income Target'}</span>
            </label>
            <div className="relative">
              <input
                id="edit-income-input"
                type="text"
                value={income.toLocaleString()}
                onChange={(e) => {
                  const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
                  setIncome(isNaN(val) ? 0 : Math.min(100000000, val));
                }}
                className="w-full bg-white border border-[#DCD5C9] rounded-xl py-2.5 pl-3 pr-14 text-sm font-semibold text-[#182C22] focus:ring-2 focus:ring-[#1E5E45] focus:outline-none"
              />
              <span className="absolute right-3 top-2.5 text-xs font-semibold text-[#6E8175] pointer-events-none">
                RWF
              </span>
            </div>
          </div>

          {/* Planned Monthly Expenses Input */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label
                htmlFor="edit-expenses-input"
                className="text-xs font-semibold text-[#2D4537] flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#1E5E45]" />
                <span>{isRw ? 'Ibikenerwa by’ibanze byateganyijwe' : 'Planned Essentials Budget'}</span>
              </label>
              <button
                type="button"
                onClick={handleAutoFillBenchmark}
                disabled={loadingBenchmark}
                className="text-[11px] text-[#1E5E45] hover:text-[#123927] underline font-semibold flex items-center gap-1 cursor-pointer disabled:opacity-50"
              >
                <span>{loadingBenchmark ? '...' : isRw ? 'Koresha iby’akarere' : 'Use benchmark'}</span>
              </button>
            </div>
            <div className="relative">
              <input
                id="edit-expenses-input"
                type="text"
                value={expenses.toLocaleString()}
                onChange={(e) => {
                  const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
                  setExpenses(isNaN(val) ? 0 : Math.min(100000000, val));
                }}
                className="w-full bg-white border border-[#DCD5C9] rounded-xl py-2.5 pl-3 pr-14 text-sm font-semibold text-[#182C22] focus:ring-2 focus:ring-[#1E5E45] focus:outline-none"
              />
              <span className="absolute right-3 top-2.5 text-xs font-semibold text-[#6E8175] pointer-events-none">
                RWF
              </span>
            </div>
          </div>

          {/* Projected Remaining Balance Preview */}
          <div className="p-3 rounded-xl bg-white border border-[#E3DED4] flex items-center justify-between text-xs">
            <span className="text-[#55695D] font-medium">
              {isRw ? 'Amafaranga asaguka nyuma ya gahunda' : 'Projected left after plan'}:
            </span>
            <span className="font-serif text-sm font-bold text-[#143B2A]">
              {Math.max(0, income - expenses).toLocaleString()} RWF
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#EDE7DD]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-[#D5DDD7] hover:bg-[#F2EFE8] text-xs font-semibold text-[#55695D] transition-colors cursor-pointer"
            >
              {isRw ? 'Reka' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 rounded-xl bg-[#1E5E45] hover:bg-[#164835] text-white text-xs font-semibold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{isSaving ? '...' : isRw ? 'Bika Gahunda' : 'Save Plan'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
