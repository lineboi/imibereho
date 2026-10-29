import React, { useState, useEffect, useMemo } from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';
import { calculateBudgetComparison } from '../../services/api';
import { SlidersHorizontal, RotateCcw, Check } from 'lucide-react';

interface MyPlanComparisonCardProps {
  district: DistrictBenchmarkData;
  householdSize: string;
  language: Language;
}

export const MyPlanComparisonCard: React.FC<MyPlanComparisonCardProps> = ({
  district,
  householdSize,
  language,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];
  const isRw = language === 'RW';
  const [isEditing, setIsEditing] = useState<boolean>(false);

  // Dynamic user plan numbers (persisted in localStorage or defaulted)
  const [userAmounts, setUserAmounts] = useState<Record<string, number>>(() => {
    try {
      const saved = localStorage.getItem('imibereho_user_plan_comparison');
      if (saved) return JSON.parse(saved);
    } catch {
      // ignore
    }
    return {
      food: 60000,
      housing: 45000,
      transport: 18000,
      utilities: 12000,
      other_essentials: 15000,
    };
  });

  const handleAmountChange = (categoryCode: string, valueStr: string) => {
    const val = parseInt(valueStr.replace(/[^0-9]/g, ''), 10);
    setUserAmounts((prev) => {
      const next = { ...prev, [categoryCode]: isNaN(val) ? 0 : Math.min(10000000, val) };
      try {
        localStorage.setItem('imibereho_user_plan_comparison', JSON.stringify(next));
      } catch {
        // ignore
      }
      return next;
    });
  };

  const handleResetToBenchmark = () => {
    const next: Record<string, number> = {};
    district.lines.forEach((l) => {
      next[l.categoryCode] = l.amount;
    });
    setUserAmounts(next);
    try {
      localStorage.setItem('imibereho_user_plan_comparison', JSON.stringify(next));
    } catch {
      // ignore
    }
  };

  const userPlanItems = useMemo(() => {
    const getDemo = (code: string, fallback: number) =>
      district.lines.find((l) => l.categoryCode === code)?.amount ?? fallback;
    return [
      {
        categoryCode: 'food',
        name: t.categoryFood,
        you: userAmounts['food'] ?? 60000,
        demo: getDemo('food', 65000),
      },
      {
        categoryCode: 'housing',
        name: t.categoryHousing,
        you: userAmounts['housing'] ?? 45000,
        demo: getDemo('housing', 40000),
      },
      {
        categoryCode: 'transport',
        name: t.categoryTransport,
        you: userAmounts['transport'] ?? 18000,
        demo: getDemo('transport', 20000),
      },
      {
        categoryCode: 'utilities',
        name: t.categoryUtilities,
        you: userAmounts['utilities'] ?? 12000,
        demo: getDemo('utilities', 10000),
      },
      {
        categoryCode: 'other_essentials',
        name: t.categoryOtherEssentials,
        you: userAmounts['other_essentials'] ?? 15000,
        demo: getDemo('other_essentials', 15000),
      },
    ];
  }, [t, district.lines, userAmounts]);

  useEffect(() => {
    calculateBudgetComparison({
      district: district.districtId,
      householdSize: 4,
      plan: userPlanItems.map((item) => ({
        categoryCode: item.categoryCode,
        plannedAmount: item.you,
      })),
    });
  }, [district.districtId, userPlanItems]);

  const totalYou = userPlanItems.reduce((acc, curr) => acc + curr.you, 0);
  const totalDemo = userPlanItems.reduce((acc, curr) => acc + curr.demo, 0);
  const maxAmount = Math.max(70000, ...userPlanItems.map((i) => Math.max(i.you, i.demo)));

  return (
    <section
      aria-label="My Plan vs Benchmark Comparison Card"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-5 sm:p-7 shadow-xs flex flex-col gap-4"
    >
      {/* Illustrative Benchmark Pill & Mode Controls */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="bg-[#E4ECE5] text-[#244E38] text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider inline-block">
          {t.illustrativeBenchmarkBadge}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsEditing((prev) => !prev)}
            className={`text-xs font-semibold px-2.5 py-1 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
              isEditing
                ? 'bg-[#1E5E45] text-white border-[#1E5E45] shadow-2xs'
                : 'bg-[#FAF8F4] text-[#1E5E45] border-[#D8DDD9] hover:bg-[#EAE5DC]'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{isEditing ? (isRw ? 'Uzuza Gahunda' : 'Done Editing') : isRw ? 'Hindura Gahunda Yanjye' : 'Customize My Plan'}</span>
          </button>
          <span className="text-[11px] text-[#55695D] font-medium bg-[#FAF8F3] px-2.5 py-1 rounded-full border border-[#E8E2D6]">
            {district.districtName} · {householdSize}
          </span>
        </div>
      </div>

      <div className="text-[11.5px] text-[#697B71] font-medium mt-1">
        {t.monthlyEssentialsLabel}
      </div>

      {/* Hero Large Benchmark Total */}
      <div className="font-serif text-4xl sm:text-5xl font-normal text-[#123927] tracking-tight flex items-baseline gap-3">
        <span>{totalDemo.toLocaleString()}</span>
        <span className="text-sm font-sans font-medium text-[#687C71]">
          {isRw ? 'RWF ku kwezi' : 'RWF / month (Benchmark)'}
        </span>
      </div>

      {/* Explanatory text & Quick Reset */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 -mt-1">
        <p className="text-[13px] text-[#4A5D52] leading-relaxed">
          {t.comparisonInsightSameTotal}
        </p>
        <div className="flex items-center gap-2 shrink-0">
          {isEditing && (
            <button
              type="button"
              onClick={handleResetToBenchmark}
              className="text-[11px] text-[#1E5E45] hover:text-[#133F2E] font-medium flex items-center gap-1 bg-[#EAF5EE] border border-[#CFE4D7] px-2.5 py-1 rounded-lg cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>{isRw ? 'Koresha iby’akarere' : 'Reset to Benchmark'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Legend Row */}
      <div className="flex items-center gap-6 text-xs text-[#52665B] pt-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1A4532]" />
          <span className="font-medium">{t.legendYourPlan} ({totalYou.toLocaleString()} RWF)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-xs border border-[#8C9E93] bg-[#EAE7DF]" />
          <span>{t.legendDemoRef} ({totalDemo.toLocaleString()} RWF)</span>
        </div>
      </div>

      {/* Comparison Table / Rows */}
      <div className="flex flex-col mt-2 pt-3 border-t border-[#EDE7DD]">
        {/* Column Headers */}
        <div className="flex items-center justify-between pb-2 text-[10.5px] font-bold text-[#718479] uppercase tracking-wider">
          <span>{t.categoryHeader}</span>
          <div className="flex items-center gap-6">
            <span className="w-24 text-right">{t.youHeader}</span>
            <span className="w-20 text-right">{t.demoHeader}</span>
          </div>
        </div>

        {/* Rows */}
        <div className="flex flex-col divide-y divide-[#F2EFE8]">
          {userPlanItems.map((item) => {
            const youWidth = Math.min(100, Math.round((item.you / maxAmount) * 100));
            const demoWidth = Math.min(100, Math.round((item.demo / maxAmount) * 100));

            return (
              <div key={item.categoryCode} className="py-3 flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-sm text-[#182C22]">{item.name}</span>
                  <div className="flex items-center gap-6">
                    {isEditing ? (
                      <div className="w-24 flex items-center bg-[#FAF8F4] border border-[#1E5E45] rounded-lg px-2 py-1 shadow-2xs">
                        <input
                          type="text"
                          value={item.you.toLocaleString()}
                          onChange={(e) => handleAmountChange(item.categoryCode, e.target.value)}
                          className="w-full text-right font-bold text-xs sm:text-sm text-[#163D2B] bg-transparent focus:outline-none"
                        />
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setIsEditing(true)}
                        title="Click to customize this category amount"
                        className="w-24 text-right font-bold text-sm text-[#163D2B] hover:text-[#1E5E45] hover:underline cursor-pointer"
                      >
                        {item.you.toLocaleString()}
                      </button>
                    )}
                    <span className="w-20 text-right font-normal text-sm text-[#62756A]">
                      {item.demo.toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Comparative Double Bars */}
                <div className="w-full flex flex-col gap-1 mt-0.5">
                  <div className="w-full bg-[#EAE6DD] h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#194C37] h-full rounded-full transition-all duration-300"
                      style={{ width: `${youWidth}%` }}
                    />
                  </div>
                  <div className="w-full bg-[#EAE6DD] h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#9AB0A2] h-full rounded-full transition-all duration-300"
                      style={{ width: `${demoWidth}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Total Row */}
        <div className="pt-4 mt-2 border-t border-[#E8E2D6] flex items-center justify-between text-xs">
          <span className="font-semibold text-[#304538]">{t.totalMonthlyEssentials}</span>
          <div className="flex items-center gap-3">
            {isEditing && (
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="text-[11px] bg-[#1E5E45] text-white px-3 py-1 rounded-lg font-semibold flex items-center gap-1 cursor-pointer"
              >
                <Check className="w-3 h-3" />
                <span>{isRw ? 'Kubika' : 'Apply'}</span>
              </button>
            )}
            <span className="font-serif text-base sm:text-lg font-bold text-[#143B2A]">
              {totalYou.toLocaleString()} / {totalDemo.toLocaleString()} RWF
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
