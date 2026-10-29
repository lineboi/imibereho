import React, { useState, useEffect } from 'react';
import type { Language, NavTab, MonthlyBudgetPlan, ExpenseItem, IncomeItem } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import {
  fetchTrackerOverview,
  fetchTrackerTransactions,
  createTrackerTransaction,
  deleteTrackerTransaction,
  fetchTrackerDailyTrend,
  fetchTrackerBurnRate,
  fetchBudgetBenchmark,
  type TrackerOverviewResponse,
  type TrackerDailyTrendPoint,
  type TrackerBurnRateResponse,
  type TrackerCategory,
  type BudgetBenchmarkData,
} from '../../services/api';
import { MonthlyPlanCard } from './MonthlyPlanCard';
import { TodaySpendingCard } from './TodaySpendingCard';
import { BufferAdviceCard } from './BufferAdviceCard';
import { DailySpendingChartCard } from './DailySpendingChartCard';
import { BottomNav } from './BottomNav';
import { AddExpenseModal } from './AddExpenseModal';
import { AddIncomeModal } from './AddIncomeModal';
import { ShockScenarioModal } from './ShockScenarioModal';
import { EditBudgetPlanModal } from './EditBudgetPlanModal';
import { ArrowLeft, ArrowDownLeft, ArrowUpRight } from 'lucide-react';

interface DailyTrackerPageProps {
  language: Language;
  onNavigateHome: () => void;
  district?: string;
  householdSize?: string;
  monthlyIncome?: string;
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const DailyTrackerPage: React.FC<DailyTrackerPageProps> = ({
  language,
  onNavigateHome,
  district = 'Gasabo',
  householdSize = '4 people',
  monthlyIncome,
  activeTab,
  onTabChange,
}) => {
  const t = TRACKER_TRANSLATIONS[language];
  const sizeNum = parseInt(householdSize.replace(/[^0-9]/g, ''), 10) || 4;
  const currentMonth = new Intl.DateTimeFormat(language === 'RW' ? 'rw-RW' : 'en-US', {
    month: 'long',
    year: 'numeric',
  }).format(new Date());

  const parsedInitialIncome = parseInt((monthlyIncome || '').replace(/[^0-9]/g, ''), 10) || 0;

  // Real database-backed state: initialized from database benchmark upon fetch
  const [plan, setPlan] = useState<MonthlyBudgetPlan>({
    monthlyIncome: parsedInitialIncome,
    plannedExpenses: 0,
    leftAfterPlan: 0,
    demoSavings: 0,
    month: currentMonth,
    district,
    householdSize,
  });
  // Real database-backed state: starts empty (0 mock objects)
  const [expenses, setExpenses] = useState<ExpenseItem[]>([]);
  const [incomes, setIncomes] = useState<IncomeItem[]>([]);
  const [dailyTrendPoints, setDailyTrendPoints] = useState<TrackerDailyTrendPoint[]>([]);
  const [burnRate, setBurnRate] = useState<TrackerBurnRateResponse | null>(null);
  const [addExpenseOpen, setAddExpenseOpen] = useState(false);
  const [addIncomeOpen, setAddIncomeOpen] = useState(false);
  const [shockModalOpen, setShockModalOpen] = useState(false);
  const [editPlanOpen, setEditPlanOpen] = useState(false);

  // Helper to sync state from backend database responses
  const applyBackendData = (
    overview: TrackerOverviewResponse | null,
    txList: { items: { id: string; type: string; title: string; category: string; amount: number; date: string; note: string | null }[] } | null,
    trend: { points: TrackerDailyTrendPoint[] } | null,
    burn: TrackerBurnRateResponse | null,
    bench?: BudgetBenchmarkData | null
  ) => {
    if (overview || bench) {
      setPlan((prev) => {
        const planned = overview?.plannedExpenses ?? (bench?.total || prev.plannedExpenses);
        const inc = overview?.monthlyIncome ?? (prev.monthlyIncome > 0 ? prev.monthlyIncome : (bench ? Math.round(bench.total * 1.15) : 0));
        return {
          ...prev,
          monthlyIncome: inc,
          plannedExpenses: planned,
          leftAfterPlan: overview?.leftAfterPlan ?? Math.max(0, inc - planned),
          demoSavings: overview?.demoSavings ?? Math.round(inc * 0.2),
          district: bench ? bench.district.name : prev.district,
          householdSize: bench ? `${bench.householdSize} people` : prev.householdSize,
        };
      });
    }

    if (txList) {
      const validIcons = ['food', 'transport', 'utilities', 'other'] as const;
      const expItems: ExpenseItem[] = txList.items
        .filter((item) => item.type === 'expense')
        .map((item) => {
          const catLabel = item.category.charAt(0).toUpperCase() + item.category.slice(1);
          const iconType = validIcons.includes(item.category as typeof validIcons[number])
            ? (item.category as typeof validIcons[number])
            : 'other';
          return {
            id: item.id,
            title: item.title,
            category: catLabel,
            note: item.note || 'General expense',
            amount: item.amount,
            iconType,
            date: item.date ? item.date.slice(0, 10) : 'Today',
          };
        });

      const incItems: IncomeItem[] = txList.items
        .filter((item) => item.type === 'income')
        .map((item) => {
          const catLabel = item.category.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
          return {
            id: item.id,
            source: item.title,
            category: catLabel,
            note: item.note || 'Income received',
            amount: item.amount,
            date: item.date ? item.date.slice(0, 10) : 'Today',
          };
        });

      setExpenses(expItems);
      setIncomes(incItems);
    }

    if (trend?.points) setDailyTrendPoints(trend.points);
    if (burn) setBurnRate(burn);
  };

  const refreshTracker = async () => {
    try {
      const [overview, txList, trend, burn, bench] = await Promise.all([
        fetchTrackerOverview(),
        fetchTrackerTransactions(),
        fetchTrackerDailyTrend(),
        fetchTrackerBurnRate(),
        fetchBudgetBenchmark(district, sizeNum),
      ]);
      applyBackendData(overview, txList, trend, burn, bench);
    } catch (err) {
      console.warn('[Tracker] Error refreshing backend data:', err);
    }
  };

  useEffect(() => {
    let active = true;

    Promise.all([
      fetchTrackerOverview(),
      fetchTrackerTransactions(),
      fetchTrackerDailyTrend(),
      fetchTrackerBurnRate(),
      fetchBudgetBenchmark(district, sizeNum),
    ])
      .then(([overview, txList, trend, burn, bench]) => {
        if (!active) return;
        applyBackendData(overview, txList, trend, burn, bench);
      })
      .catch((err) => {
        console.warn('[Tracker] Error loading backend data:', err);
      });

    return () => {
      active = false;
    };
  }, [district, sizeNum]);

  const handleAddExpense = async (newExpense: Omit<ExpenseItem, 'id'>) => {
    const categoryMap: Record<string, TrackerCategory> = {
      Food: 'food',
      Transport: 'transport',
      Utilities: 'utilities',
      Other: 'other',
    };
    const cat = categoryMap[newExpense.category] || 'other';

    // Optimistic local update
    const item: ExpenseItem = {
      ...newExpense,
      id: `exp-${Date.now()}`,
    };
    setExpenses((prev) => [item, ...prev]);
    setPlan((prev) => ({
      ...prev,
      plannedExpenses: prev.plannedExpenses + newExpense.amount,
      leftAfterPlan: Math.max(0, prev.leftAfterPlan - newExpense.amount),
    }));

    // Persist to live backend
    try {
      await createTrackerTransaction({
        type: 'expense',
        title: newExpense.title,
        category: cat,
        note: newExpense.note || null,
        amount: newExpense.amount,
        date: new Date().toISOString(),
      });
      refreshTracker();
    } catch (err) {
      console.warn('Backend create expense failed:', err);
    }
  };

  const handleAddIncome = async (newIncome: Omit<IncomeItem, 'id'>) => {
    const categoryMap: Record<string, TrackerCategory> = {
      'Mobile Money': 'mobile_money',
      'Day Wage': 'day_wage',
      'Market Sales': 'market_sales',
      'Side Gig': 'side_gig',
    };
    const cat = categoryMap[newIncome.category] || 'mobile_money';

    // Optimistic local update
    const item: IncomeItem = {
      ...newIncome,
      id: `inc-${Date.now()}`,
    };
    setIncomes((prev) => [item, ...prev]);
    setPlan((prev) => ({
      ...prev,
      monthlyIncome: prev.monthlyIncome + newIncome.amount,
      leftAfterPlan: prev.leftAfterPlan + newIncome.amount,
    }));

    // Persist to live backend
    try {
      await createTrackerTransaction({
        type: 'income',
        title: newIncome.source,
        category: cat,
        note: newIncome.note || null,
        amount: newIncome.amount,
        date: new Date().toISOString(),
      });
      refreshTracker();
    } catch (err) {
      console.warn('Backend create income failed:', err);
    }
  };

  const handleDeleteTransaction = async (id: string) => {
    setExpenses((prev) => prev.filter((item) => item.id !== id));
    setIncomes((prev) => prev.filter((item) => item.id !== id));
    try {
      await deleteTrackerTransaction(id);
      refreshTracker();
    } catch (err) {
      console.warn('Backend delete transaction failed:', err);
    }
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
    setExpenses([]);
    setIncomes([]);
    refreshTracker();
  };

  const handleSavePlan = (income: number, expensesAmount: number) => {
    setPlan((prev) => ({
      ...prev,
      monthlyIncome: income,
      plannedExpenses: expensesAmount,
      leftAfterPlan: Math.max(0, income - expensesAmount),
      demoSavings: Math.round(income * 0.2),
    }));
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
          <div className="flex flex-wrap items-center gap-2.5 mt-2.5">
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
            <MonthlyPlanCard
              plan={plan}
              language={language}
              onEditPlan={() => setEditPlanOpen(true)}
            />

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
                onDeleteTransaction={handleDeleteTransaction}
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
              dailyTrendPoints={dailyTrendPoints}
              burnRate={burnRate}
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
              onDeleteTransaction={handleDeleteTransaction}
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

      <EditBudgetPlanModal
        isOpen={editPlanOpen}
        onClose={() => setEditPlanOpen(false)}
        plan={plan}
        onSavePlan={handleSavePlan}
        language={language}
      />
    </div>
  );
};
