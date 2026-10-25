import React from 'react';
import type { Language, MonthlyBudgetPlan } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import { X, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';

interface ShockScenarioModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan: MonthlyBudgetPlan;
  onApplyShock: (amount: number, shockTitle: string) => void;
  onResetPlan: () => void;
  language: Language;
}

export const ShockScenarioModal: React.FC<ShockScenarioModalProps> = ({
  isOpen,
  onClose,
  plan,
  onApplyShock,
  onResetPlan,
  language,
}) => {
  const t = TRACKER_TRANSLATIONS[language];

  if (!isOpen) return null;

  const scenarios = [
    {
      id: 'clinic',
      title: t.shockScenario1,
      deduction: 25000,
      description: 'Sudden outpatient fee & prescription medications.',
    },
    {
      id: 'food_inflation',
      title: t.shockScenario2,
      deduction: 18000,
      description: 'Seasonal market price swings in local beans and cooking oil.',
    },
    {
      id: 'school_term',
      title: t.shockScenario3,
      deduction: 35000,
      description: 'Term materials, uniforms, and community contribution.',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg bg-[#FAF8F4] rounded-2xl shadow-2xl border border-[#DDD7CE] overflow-hidden">
        {/* Header */}
        <div className="bg-[#163D2E] text-white px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-300" />
            <div>
              <h3 className="font-semibold text-base">{t.shockModalTitle}</h3>
              <p className="text-xs text-[#B2D8C3]">{t.shockModalSub}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 flex flex-col gap-4">
          {/* Status summary */}
          <div className="bg-white rounded-xl p-4 border border-[#E3DED4] flex items-center justify-between">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#697B71]">
                Current Cushion Available
              </span>
              <div className="text-xl font-bold text-[#143B2A] mt-0.5">
                {plan.leftAfterPlan.toLocaleString()} RWF
              </div>
            </div>
            <div className="text-right">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#697B71]">
                Savings Reserve
              </span>
              <div className="text-xl font-bold text-[#1E5E45] mt-0.5">
                {plan.demoSavings.toLocaleString()} RWF
              </div>
            </div>
          </div>

          {/* Scenarios list */}
          <div className="space-y-2.5">
            <span className="text-xs font-semibold text-[#1B2F25]">
              Select a scenario to test buffer resilience:
            </span>
            {scenarios.map((sc) => (
              <button
                key={sc.id}
                type="button"
                onClick={() => {
                  onApplyShock(sc.deduction, sc.title);
                  onClose();
                }}
                className="w-full text-left bg-white hover:bg-[#EBF3ED] border border-[#DDD7CE] hover:border-[#1E5E45] p-3.5 rounded-xl transition-all flex items-start justify-between gap-3 cursor-pointer group"
              >
                <div>
                  <div className="text-xs sm:text-sm font-semibold text-[#182C22] group-hover:text-[#1E5E45]">
                    {sc.title}
                  </div>
                  <div className="text-xs text-[#63756C] mt-0.5">
                    {sc.description}
                  </div>
                </div>
                <span className="text-xs font-bold text-red-700 shrink-0 bg-red-50 px-2 py-0.5 rounded-md">
                  -{sc.deduction.toLocaleString()} RWF
                </span>
              </button>
            ))}
          </div>

          {/* Reset / Guidance Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-[#E5DFD4]">
            <button
              type="button"
              onClick={onResetPlan}
              className="flex items-center gap-1.5 text-xs font-semibold text-[#5A6E63] hover:text-[#182C22] cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset to Base Plan</span>
            </button>
            <div className="flex items-center gap-1.5 text-xs text-[#1E5E45] font-semibold">
              <ShieldCheck className="w-4 h-4" />
              <span>Zero Risk Simulation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
