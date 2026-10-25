import React, { useState } from 'react';
import type { Language, NavTab, MonthlyBudgetPlan, ExpenseItem, IncomeItem } from '../../types';
import {
  TRACKER_TRANSLATIONS,
  INITIAL_MONTHLY_PLAN,
  INITIAL_TODAY_EXPENSES,
  INITIAL_TODAY_INCOME,
} from '../../data/mockTrackerData';
import { MonthlyPlanCard } from './MonthlyPlanCard';
import { TodaySpendingCard } from './TodaySpendingCard';
import { BufferAdviceCard } from './BufferAdviceCard';
import { DailySpendingChartCard } from './DailySpendingChartCard';
import { BottomNav } from './BottomNav';
import { AddExpenseModal } from './AddExpenseModal';
import { AddIncomeModal } from './AddIncomeModal';
import { ShockScenarioModal } from './ShockScenarioModal';
import { ArrowLeft, ArrowDownLeft, ArrowUpRight } from 'lucide-react';

interface DailyTrackerPageProps {
  language: Language;
  onNavigateHome: () => void;
  district?: string;
  householdSize?: string;
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const DailyTrackerPage: React.FC<DailyTrackerPageProps> = ({
  language,
  onNavigateHome,
  district = 'Gasabo',
  householdSize = '4 people',
  activeTab,
  onTabChange,
}) => {
  const t = TRACKER_TRANSLATIONS[language];
  const [plan, setPlan] = useState<MonthlyBudgetPlan>({
    ...INITIAL_MONTHLY_PLAN,
    district,
    householdSize,
  });
  const [expenses, setExpenses] = useState<ExpenseItem[]>(INITIAL_TODAY_EXPENSES);
  const [incomes, setIncomes] = useState<IncomeItem[]>(INITIAL_TODAY_INCOME);
  const [addExpenseOpen, setAddExpenseOpen] = useState(false);
  const [addIncomeOpen, setAddIncomeOpen] = useState(false);
  const [shockModalOpen, setShockModalOpen] = useState(false);

  const handleAddExpense = (newExpense: Omit<ExpenseItem, 'id'>) => {
    const item: ExpenseItem = {
      ...newExpense,
      id: `exp-${Date.now()}`,
    };
    setExpenses((prev) => [item, ...prev]);

    // Update planned expenses and left after plan
    setPlan((prev) => ({
      ...prev,
      plannedExpenses: prev.plannedExpenses + newExpense.amount,
      leftAfterPlan: Math.max(0, prev.leftAfterPlan - newExpense.amount),
    }));
  };

  const handleAddIncome = (newIncome: Omit<IncomeItem, 'id'>) => {
    const item: IncomeItem = {
      ...newIncome,
      id: `inc-${Date.now()}`,
    };
    setIncomes((prev) => [item, ...prev]);

    // Update monthlyIncome and increase remaining leftAfterPlan
    setPlan((prev) => ({
      ...prev,
      monthlyIncome: prev.monthlyIncome + newIncome.amount,
      leftAfterPlan: prev.leftAfterPlan + newIncome.amount,
    }));
  };

  const handleApplyShock = (amount: number) => {
    setPlan((prev) => ({
      ...prev,
      plannedExpenses: prev.plannedExpenses + amount,
      leftAfterPlan: Math.max(0, prev.leftAfterPlan - amount),
      demoSavings: Math.max(0, prev.demoSavings - (amount > prev.leftAfterPlan ? amount - prev.leftAfterPlan : 0)),
    }));
  };

  const handleResetPlan = () => {
    setPlan({
      ...INITIAL_MONTHLY_PLAN,
      district,
      householdSize,
    });
    setExpenses(INITIAL_TODAY_EXPENSES);
    setIncomes(INITIAL_TODAY_INCOME);
  };

  return (
    <div className="flex-1 flex flex-col justify-between w-full">
      {/* Main Content Area */}
      <main className="max-w-5xl mx-auto w-full px-4 sm:px-6 py-5 sm:py-8 flex flex-col gap-5">
        {/* Navigation & Breadcrumb Header */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={onNavigateHome}
            className="flex items-center gap-1.5 text-[11px] sm:text-xs font-bold uppercase tracking-wider text-[#355D47] hover:text-[#143B2A] transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>{t.breadcrumb}</span>
          </button>

          <button
            type="button"
            onClick={onNavigateHome}
            className="text-xs text-[#526D5E] hover:text-[#1E5E45] font-medium hidden sm:inline-flex"
          >
            {t.backToLanding}
          </button>
        </div>

        {/* Page Headline */}
        <div>
          <h1 className="font-serif text-[28px] sm:text-4xl text-[#123927] font-normal tracking-tight leading-[1.18]">
            {t.headline}
          </h1>

          {/* Context Badges Row */}
          <div className="flex items-center gap-2.5 mt-2.5">
            <span className="bg-[#E2EDE4] text-[#1E5E45] text-xs font-semibold px-3 py-1 rounded-full border border-[#D0E2D4]">
              {plan.district} · {plan.householdSize}
            </span>
            <span className="text-xs text-[#687B70] font-medium">
              {plan.month}
            </span>
          </div>
        </div>

        {/* Responsive Layout Grid (Balanced 2 equal columns on desktop) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {/* Column 1: Monthly Overview & Actions & Buffer Guidance */}
          <div className="flex flex-col gap-4 sm:gap-5">
            {/* Monthly Plan Overview Card */}
            <MonthlyPlanCard plan={plan} language={language} />

            {/* Action Buttons Row (Mobile View) */}
            <div className="block lg:hidden">
              <div className="grid grid-cols-2 gap-2.5">
                <button
                  type="button"
                  onClick={() => setAddExpenseOpen(true)}
                  className="w-full bg-[#235843] hover:bg-[#1A4534] active:bg-[#133729] text-white py-3.5 px-3 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-1.5 shadow-xs transition-colors cursor-pointer group"
                >
                  <ArrowDownLeft className="w-4 h-4 text-emerald-300 transition-transform group-hover:translate-y-0.5" />
                  <span className="truncate">{t.addExpenseButton}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setAddIncomeOpen(true)}
                  className="w-full bg-[#EBF4EE] hover:bg-[#D8EDE0] active:bg-[#C6E5D0] text-[#144730] border border-[#BDDDC7] py-3.5 px-3 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-1.5 shadow-xs transition-colors cursor-pointer group"
                >
                  <ArrowUpRight className="w-4 h-4 text-[#1E5E45] transition-transform group-hover:-translate-y-0.5" />
                  <span className="truncate">{t.addIncomeButton}</span>
                </button>
              </div>
            </div>

            {/* On Mobile: Today's spending sits here */}
            <div className="block lg:hidden">
              <TodaySpendingCard
                expenses={expenses}
                incomes={incomes}
                plan={plan}
                language={language}
                onOpenAddIncome={() => setAddIncomeOpen(true)}
              />
            </div>

            {/* Buffer Guidance Card */}
            <BufferAdviceCard
              language={language}
              onOpenShockScenario={() => setShockModalOpen(true)}
            />

            {/* Daily Spending vs Ideal Benchmark Chart Card (Bellow buffer card) */}
            <DailySpendingChartCard
              language={language}
              idealDailyLimit={5000}
              todaySpent={expenses.reduce((sum, item) => sum + item.amount, 0)}
            />
          </div>

          {/* Column 2 (Desktop): Action Buttons + Today's Spending */}
          <div className="hidden lg:flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => setAddExpenseOpen(true)}
                className="w-full bg-[#235843] hover:bg-[#1A4534] active:bg-[#133729] text-white py-3.5 px-3 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-1.5 shadow-xs transition-colors cursor-pointer group"
              >
                <ArrowDownLeft className="w-4 h-4 text-emerald-300 transition-transform group-hover:translate-y-0.5" />
                <span className="truncate">{t.addExpenseButton}</span>
              </button>

              <button
                type="button"
                onClick={() => setAddIncomeOpen(true)}
                className="w-full bg-[#EBF4EE] hover:bg-[#D8EDE0] active:bg-[#C6E5D0] text-[#144730] border border-[#BDDDC7] py-3.5 px-3 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-1.5 shadow-xs transition-colors cursor-pointer group"
              >
                <ArrowUpRight className="w-4 h-4 text-[#1E5E45] transition-transform group-hover:-translate-y-0.5" />
                <span className="truncate">{t.addIncomeButton}</span>
              </button>
            </div>

            <TodaySpendingCard
              expenses={expenses}
              incomes={incomes}
              plan={plan}
              language={language}
              onOpenAddIncome={() => setAddIncomeOpen(true)}
            />
          </div>
        </div>
      </main>

      {/* Bottom Navigation (Mobile Only) */}
      <BottomNav
        activeTab={activeTab}
        onTabChange={(tab) => {
          onTabChange(tab);
          if (tab === 'resilience') {
            setShockModalOpen(true);
          }
        }}
        language={language}
      />

      {/* Modals */}
      <AddExpenseModal
        isOpen={addExpenseOpen}
        onClose={() => setAddExpenseOpen(false)}
        onAddExpense={handleAddExpense}
        language={language}
      />

      <AddIncomeModal
        isOpen={addIncomeOpen}
        onClose={() => setAddIncomeOpen(false)}
        onAddIncome={handleAddIncome}
        language={language}
      />

      <ShockScenarioModal
        isOpen={shockModalOpen}
        onClose={() => setShockModalOpen(false)}
        plan={plan}
        onApplyShock={handleApplyShock}
        onResetPlan={handleResetPlan}
        language={language}
      />
    </div>
  );
};
