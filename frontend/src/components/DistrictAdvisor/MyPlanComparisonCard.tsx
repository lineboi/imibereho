import React from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';

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

  // User's custom plan mix matching the mockup screenshot
  // Total: 150,000 RWF (Food: 60k, Housing: 45k, Transport: 18k, Utilities: 12k, Other: 15k)
  const userPlanItems = [
    { categoryCode: 'food', name: t.categoryFood, you: 60000, demo: 65000 },
    { categoryCode: 'housing', name: t.categoryHousing, you: 45000, demo: 40000 },
    { categoryCode: 'transport', name: t.categoryTransport, you: 18000, demo: 20000 },
    { categoryCode: 'utilities', name: t.categoryUtilities, you: 12000, demo: 10000 },
    { categoryCode: 'other_essentials', name: t.categoryOtherEssentials, you: 15000, demo: 15000 },
  ];

  const totalYou = userPlanItems.reduce((acc, curr) => acc + curr.you, 0);
  const totalDemo = userPlanItems.reduce((acc, curr) => acc + curr.demo, 0);
  const maxAmount = 70000;

  return (
    <section
      aria-label="My Plan vs Benchmark Comparison Card"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-5 sm:p-7 shadow-xs flex flex-col gap-4"
    >
      {/* Illustrative Benchmark Pill */}
      <div className="flex items-center justify-between">
        <span className="bg-[#E4ECE5] text-[#244E38] text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider inline-block">
          {t.illustrativeBenchmarkBadge}
        </span>
        <span className="text-[11px] text-[#55695D] font-medium bg-[#FAF8F3] px-2.5 py-1 rounded-full border border-[#E8E2D6]">
          {district.districtName} · {householdSize}
        </span>
      </div>
      <div className="text-[11.5px] text-[#697B71] font-medium mt-1">
        {t.monthlyEssentialsLabel}
      </div>

      {/* Hero Large Benchmark Total */}
      <div className="font-serif text-4xl sm:text-5xl font-normal text-[#123927] tracking-tight">
        {totalDemo.toLocaleString()}
      </div>

      {/* Explanatory text */}
      <p className="text-[13px] text-[#4A5D52] leading-relaxed -mt-1">
        {t.comparisonInsightSameTotal}
      </p>

      {/* Legend Row */}
      <div className="flex items-center gap-6 text-xs text-[#52665B] pt-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1A4532]" />
          <span className="font-medium">{t.legendYourPlan}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-xs border border-[#8C9E93] bg-[#EAE7DF]" />
          <span>{t.legendDemoRef}</span>
        </div>
      </div>

      {/* Comparison Table / Rows */}
      <div className="flex flex-col mt-2 pt-3 border-t border-[#EDE7DD]">
        {/* Column Headers */}
        <div className="flex items-center justify-between pb-2 text-[10.5px] font-bold text-[#718479] uppercase tracking-wider">
          <span>{t.categoryHeader}</span>
          <div className="flex items-center gap-6">
            <span className="w-16 text-right">{t.youHeader}</span>
            <span className="w-16 text-right">{t.demoHeader}</span>
          </div>
        </div>

        {/* Rows */}
        <div className="flex flex-col divide-y divide-[#F2EFE8]">
          {userPlanItems.map((item) => {
            const youWidth = Math.round((item.you / maxAmount) * 100);
            const demoWidth = Math.round((item.demo / maxAmount) * 100);

            return (
              <div key={item.categoryCode} className="py-3 flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-sm text-[#182C22]">{item.name}</span>
                  <div className="flex items-center gap-6">
                    <span className="w-16 text-right font-bold text-sm text-[#163D2B]">
                      {item.you.toLocaleString()}
                    </span>
                    <span className="w-16 text-right font-normal text-sm text-[#62756A]">
                      {item.demo.toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Comparative Double Bars (Matching the screenshot's exact aesthetic) */}
                <div className="w-full flex flex-col gap-1 mt-0.5">
                  <div className="w-full bg-[#EAE6DD] h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#194C37] h-full rounded-full"
                      style={{ width: `${youWidth}%` }}
                    />
                  </div>
                  <div className="w-full bg-[#EAE6DD] h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#9AB0A2] h-full rounded-full"
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
          <span className="font-medium text-[#465A4F]">{t.totalMonthlyEssentials}</span>
          <span className="font-serif text-base sm:text-lg font-bold text-[#143B2A]">
            {totalYou.toLocaleString()} / {totalDemo.toLocaleString()}
          </span>
        </div>
      </div>
    </section>
  );
};
