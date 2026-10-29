import React from 'react';
import type { ExpenseItem, IncomeItem, MonthlyBudgetPlan, Language } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import {
  ShoppingBag,
  Bus,
  Zap,
  Receipt,
  ShieldCheck,
  ArrowDownLeft,
  ArrowUpRight,
  Wallet,
  Smartphone,
  Trash2,
} from 'lucide-react';

interface TodaySpendingCardProps {
  expenses: ExpenseItem[];
  incomes: IncomeItem[];
  plan: MonthlyBudgetPlan;
  language: Language;
  onOpenAddIncome?: () => void;
  onDeleteTransaction?: (id: string) => void;
}

export const TodaySpendingCard: React.FC<TodaySpendingCardProps> = ({
  expenses,
  incomes,
  plan,
  language,
  onDeleteTransaction,
}) => {
  const t = TRACKER_TRANSLATIONS[language];

  const totalSpentToday = expenses.reduce((sum, item) => sum + item.amount, 0);
  const totalIncomeToday = incomes.reduce((sum, item) => sum + item.amount, 0);

  // Remaining days in month (derived dynamically from calendar)
  const now = new Date();
  const daysInCurrentMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const daysRemaining = Math.max(1, daysInCurrentMonth - now.getDate());
  // Daily safe allowance derived from planned budget
  const dailySafeLimit = Math.max(1000, Math.round(plan.plannedExpenses / (daysInCurrentMonth || 30)));
  const isWithinDailySafe = totalSpentToday <= dailySafeLimit;

  // Unified records combined into one chronological list
  interface UnifiedRecord {
    id: string;
    kind: 'expense' | 'income';
    title: string;
    subtitle: string;
    amount: number;
    iconType?: ExpenseItem['iconType'];
    isMobileMoney?: boolean;
  }

  const unifiedRecords: UnifiedRecord[] = [
    ...expenses.map((e) => ({
      id: e.id,
      kind: 'expense' as const,
      title: e.title,
      subtitle: `${e.category} · ${e.note}`,
      amount: e.amount,
      iconType: e.iconType,
    })),
    ...incomes.map((inc) => ({
      id: inc.id,
      kind: 'income' as const,
      title: inc.source,
      subtitle: `${inc.category}${inc.note ? ` · ${inc.note}` : ''}`,
      amount: inc.amount,
      isMobileMoney: inc.category.toLowerCase().includes('mobile'),
    })),
  ];

  const renderCategoryIcon = (rec: UnifiedRecord) => {
    if (rec.kind === 'income') {
      return rec.isMobileMoney ? (
        <Smartphone className="w-4 h-4 text-[#1E5E45]" />
      ) : (
        <Wallet className="w-4 h-4 text-[#1E5E45]" />
      );
    }

    switch (rec.iconType) {
      case 'food':
        return <ShoppingBag className="w-4 h-4 text-[#1E5E45]" />;
      case 'transport':
        return <Bus className="w-4 h-4 text-[#1E5E45]" />;
      case 'utilities':
        return <Zap className="w-4 h-4 text-[#1E5E45]" />;
      default:
        return <Receipt className="w-4 h-4 text-[#1E5E45]" />;
    }
  };

  const todayDateStr = new Intl.DateTimeFormat(language === 'RW' ? 'rw-RW' : 'en-US', {
    day: 'numeric',
    month: 'short',
  }).format(new Date());

  return (
    <section
      aria-label="Today's Spending and Cashflow"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-4 sm:p-5 shadow-xs flex flex-col gap-4"
    >
      {/* Header Row: Title & Date Pill */}
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg sm:text-xl font-normal text-[#133A29]">
          {t.todaySpendingTitle}
        </h2>
        <span className="bg-[#E4ECE5] text-[#244E38] text-xs font-semibold px-2.5 py-1 rounded-full">
          {todayDateStr}
        </span>
      </div>

      {/* Safe to Spend Today Highlight Box (Compact & balanced on all screen sizes) */}
      <div className="bg-[#FAF8F4] border border-[#E8E2D6] rounded-xl p-3 flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 min-w-0">
            <ShieldCheck className="w-4 h-4 text-[#1E5E45] shrink-0" />
            <span className="text-[11px] font-bold text-[#1E5E45] uppercase tracking-wider truncate">
              {t.safeToSpendBadge}
            </span>
          </div>

          {/* Compact status pill */}
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-semibold shrink-0 ${
              isWithinDailySafe
                ? 'bg-[#EAF5EE] text-[#1E5E45] border border-[#CCE7D5]'
                : 'bg-[#FFF8E7] text-[#9A6400] border border-[#F2DEB0]'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isWithinDailySafe ? 'bg-emerald-600' : 'bg-amber-500'}`} />
            <span>{isWithinDailySafe ? 'On track' : 'Multi-day grocery'}</span>
          </span>
        </div>

        <div className="flex items-baseline justify-between pt-1 border-t border-[#EDE7DC]">
          <div className="flex items-baseline gap-1.5">
            <span className="font-serif text-xl sm:text-2xl font-bold text-[#143B2A] tracking-tight">
              {dailySafeLimit.toLocaleString()} RWF
            </span>
            <span className="text-[11px] text-[#66796D]">/ day</span>
          </div>
          <span className="text-[10.5px] sm:text-[11px] text-[#697B71]">
            {t.safeToSpendSub}
          </span>
        </div>
      </div>

      {/* Today's Cashflow Overview */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[#F0ECE4] text-xs">
        <div>
          <span className="text-[11px] text-[#6B7E73] block">Today's Spending</span>
          <span className="font-serif text-xl sm:text-2xl font-medium text-[#123927]">
            {totalSpentToday.toLocaleString()} RWF
          </span>
        </div>

        {totalIncomeToday > 0 && (
          <div className="text-right">
            <span className="text-[11px] text-[#6B7E73] block">Money In Received</span>
            <span className="font-serif text-xl sm:text-2xl font-medium text-emerald-700">
              +{totalIncomeToday.toLocaleString()} RWF
            </span>
          </div>
        )}
      </div>

      {/* Unified Records List with Indicating Icons for Expense vs Money In */}
      {unifiedRecords.length === 0 ? (
        <div className="py-8 text-center text-xs text-[#718578] flex flex-col items-center justify-center gap-2 border border-dashed border-[#DDD7CE] rounded-xl bg-[#FAF8F3]">
          <Receipt className="w-6 h-6 text-[#98AAA0]" />
          <p className="font-semibold text-[#3D5245]">
            {language === 'RW'
              ? 'Nta mafaranga arandikwa mu bubiko bw’imibare.'
              : 'No transactions recorded yet in database ledger.'}
          </p>
          <p className="text-[11px] text-[#6E8075]">
            {language === 'RW'
              ? 'Kanda "+ Andika ibyakoreshejwe" hejuru kugira ngo wandike.'
              : 'Tap "+ Add Expense" or "+ Add Income" above to log a live entry.'}
          </p>
        </div>
      ) : (
        <div className="flex flex-col divide-y divide-[#F2EFE8]">
          {unifiedRecords.map((item) => {
            const isExpense = item.kind === 'expense';

            return (
              <div
                key={item.id}
                className="py-3 first:pt-1 last:pb-1 flex items-center justify-between gap-3 group"
              >
                {/* Left: Category Icon with indicator overlay + Title & Details */}
                <div className="flex items-center gap-3 min-w-0">
                  <div className="relative shrink-0">
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-transform duration-200 group-hover:scale-105 ${
                        isExpense
                          ? 'bg-[#E8F2EB] border-[#D5E5DA]'
                          : 'bg-[#EAF6EF] border-[#CDEBD8]'
                      }`}
                    >
                      {renderCategoryIcon(item)}
                    </div>

                    {/* Corner indicator badge on icon */}
                    <div
                      className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center shadow-xs border ${
                        isExpense
                          ? 'bg-rose-100 text-rose-700 border-rose-300'
                          : 'bg-emerald-100 text-emerald-700 border-emerald-300'
                      }`}
                      title={isExpense ? 'Expense (Money out)' : 'Money In (Income)'}
                    >
                      {isExpense ? (
                        <ArrowDownLeft className="w-2.5 h-2.5 stroke-[2.5]" />
                      ) : (
                        <ArrowUpRight className="w-2.5 h-2.5 stroke-[2.5]" />
                      )}
                    </div>
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-sm text-[#1A2D23] truncate">
                        {item.title}
                      </span>
                      {/* Inline tag indicating Expense or Money In */}
                      <span
                        className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${
                          isExpense
                            ? 'bg-rose-50 text-rose-700 border border-rose-200/70'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200/70'
                        }`}
                      >
                        {isExpense ? (
                          <>
                            <ArrowDownLeft className="w-2.5 h-2.5" />
                            <span>Expense</span>
                          </>
                        ) : (
                          <>
                            <ArrowUpRight className="w-2.5 h-2.5" />
                            <span>Money in</span>
                          </>
                        )}
                      </span>
                    </div>
                    <div className="text-xs text-[#66786F] truncate mt-0.5">
                      {item.subtitle}
                    </div>
                  </div>
                </div>

                {/* Right: Amount & Delete Button */}
                <div className="flex items-center gap-2.5 shrink-0">
                  <div className="text-right">
                    <span
                      className={`font-bold text-sm tracking-tight ${
                        isExpense ? 'text-[#182C22]' : 'text-emerald-700'
                      }`}
                    >
                      {isExpense ? `-${item.amount.toLocaleString()}` : `+${item.amount.toLocaleString()}`}
                    </span>
                    <span className="block text-[10px] text-[#7A8A81]">RWF</span>
                  </div>
                  {onDeleteTransaction && (
                    <button
                      type="button"
                      onClick={() => onDeleteTransaction(item.id)}
                      className="text-[#96A89E] hover:text-rose-600 transition-colors p-1 rounded-md hover:bg-rose-50 cursor-pointer"
                      title="Delete transaction from backend ledger"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footnote */}
      <div className="text-[11px] text-[#7A8A81] mt-1 pt-2.5 border-t border-[#F0ECE4] flex items-center justify-between">
        <span>{t.amountsFootnote}</span>
        <span className="text-[#516C5D] font-medium">{daysRemaining} days left in plan</span>
      </div>
    </section>
  );
};
