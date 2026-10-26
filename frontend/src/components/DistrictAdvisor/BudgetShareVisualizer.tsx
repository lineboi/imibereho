import React from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';
import { PieChart } from 'lucide-react';

interface BudgetShareVisualizerProps {
  districtA: DistrictBenchmarkData;
  districtB: DistrictBenchmarkData;
  language: Language;
}

export const BudgetShareVisualizer: React.FC<BudgetShareVisualizerProps> = ({
  districtA,
  districtB,
  language,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];

  const getShares = (district: DistrictBenchmarkData) => {
    const total = district.baselineTotal;
    return district.lines.map((line) => ({
      code: line.categoryCode,
      name:
        line.categoryCode === 'food'
          ? t.categoryFood
          : line.categoryCode === 'housing'
          ? t.categoryHousing
          : line.categoryCode === 'transport'
          ? t.categoryTransport
          : line.categoryCode === 'utilities'
          ? t.categoryUtilities
          : t.categoryOtherEssentials,
      amount: line.amount,
      pct: Math.round((line.amount / total) * 100),
    }));
  };

  const sharesA = getShares(districtA);
  const sharesB = getShares(districtB);

  // Colors for categories
  const categoryColors: Record<string, { bg: string; text: string; hex: string }> = {
    food: { bg: 'bg-[#1E5E45]', text: 'text-[#1E5E45]', hex: '#1E5E45' },
    housing: { bg: 'bg-[#1E3A5F]', text: 'text-[#1E3A5F]', hex: '#1E3A5F' },
    transport: { bg: 'bg-[#D97706]', text: 'text-[#D97706]', hex: '#D97706' },
    utilities: { bg: 'bg-[#0284C7]', text: 'text-[#0284C7]', hex: '#0284C7' },
    other_essentials: { bg: 'bg-[#7C3AED]', text: 'text-[#7C3AED]', hex: '#7C3AED' },
  };

  // Fixed overhead (housing + transport)
  const overheadPctA = (sharesA.find((s) => s.code === 'housing')?.pct ?? 0) +
    (sharesA.find((s) => s.code === 'transport')?.pct ?? 0);
  const overheadPctB = (sharesB.find((s) => s.code === 'housing')?.pct ?? 0) +
    (sharesB.find((s) => s.code === 'transport')?.pct ?? 0);

  return (
    <section
      aria-label="Budget Share Expenditure Distribution"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-4 sm:p-6 shadow-xs flex flex-col gap-4"
    >
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#F0ECE4]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
            <PieChart className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-medium text-[#133A29]">
              {t.budgetShareTitle}
            </h3>
            <p className="text-[11.5px] text-[#697B71]">
              {t.budgetShareSub}
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-[11px] flex-wrap">
          {sharesA.map((cat) => (
            <div key={cat.code} className="flex items-center gap-1.5 font-medium">
              <span className={`w-2.5 h-2.5 rounded-sm ${categoryColors[cat.code].bg}`} />
              <span className="text-[#455A4E]">{cat.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Stacked Segmented Bars */}
      <div className="flex flex-col gap-3.5">
        {/* District A Stacked Bar */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#143B2A]">{districtA.districtName}</span>
            <span className="text-[#64766C] text-[11.5px]">
              Fixed overhead (Rent + Transport): <strong>{overheadPctA}%</strong>
            </span>
          </div>
          <div className="w-full h-5 rounded-lg overflow-hidden flex shadow-2xs">
            {sharesA.map((share) => (
              <div
                key={share.code}
                className={`${categoryColors[share.code].bg} h-full relative group transition-all`}
                style={{ width: `${share.pct}%` }}
                title={`${share.name}: ${share.pct}% (${share.amount.toLocaleString()} RWF)`}
              >
                {share.pct >= 10 && (
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] text-white font-bold tracking-tight">
                    {share.pct}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* District B Stacked Bar */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#143B2A]">{districtB.districtName}</span>
            <span className="text-[#64766C] text-[11.5px]">
              Fixed overhead (Rent + Transport): <strong>{overheadPctB}%</strong>
            </span>
          </div>
          <div className="w-full h-5 rounded-lg overflow-hidden flex shadow-2xs">
            {sharesB.map((share) => (
              <div
                key={share.code}
                className={`${categoryColors[share.code].bg} h-full relative group transition-all`}
                style={{ width: `${share.pct}%` }}
                title={`${share.name}: ${share.pct}% (${share.amount.toLocaleString()} RWF)`}
              >
                {share.pct >= 10 && (
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] text-white font-bold tracking-tight">
                    {share.pct}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Structural Insight Footnote */}
      <div className="bg-[#FAF8F4] border border-[#EBE4D8] rounded-xl p-3 text-xs text-[#4F6255] leading-relaxed">
        <strong>Structural Difference:</strong> In {districtA.districtName}, fixed overhead (housing & commuting) absorbs{' '}
        <strong>{overheadPctA}%</strong> of the essentials budget. In contrast, {districtB.districtName} commits only{' '}
        <strong>{overheadPctB}%</strong> to fixed costs, leaving a higher portion of disposable income for family nutrition, health, and emergency buffers.
      </div>
    </section>
  );
};
