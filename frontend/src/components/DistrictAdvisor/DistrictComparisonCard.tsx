import React from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';
import type { DistrictComparisonResponse } from '../../services/api';
import {
  ShoppingBag,
  Home,
  Bus,
  Zap,
  Receipt,
  ArrowDownRight,
  ArrowUpRight,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';

interface DistrictComparisonCardProps {
  districtA: DistrictBenchmarkData;
  districtB: DistrictBenchmarkData;
  householdSize: string;
  language: Language;
  districtComparisonApi?: DistrictComparisonResponse | null;
}

export const DistrictComparisonCard: React.FC<DistrictComparisonCardProps> = ({
  districtA,
  districtB,
  householdSize,
  language,
  districtComparisonApi,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];

  const diffTotal = districtB.baselineTotal - districtA.baselineTotal;
  const isLower = diffTotal < 0;
  const absDiff = Math.abs(diffTotal);
  const percentDiff = Math.round((absDiff / districtA.baselineTotal) * 100);

  // Maximum value for proportional bar calculation
  const maxCategoryAmount = Math.max(
    ...districtA.lines.map((l) => l.amount),
    ...districtB.lines.map((l) => l.amount),
    1
  );

  const getCategoryIcon = (code: string) => {
    switch (code) {
      case 'food':
        return <ShoppingBag className="w-4 h-4 text-[#1E5E45]" />;
      case 'housing':
        return <Home className="w-4 h-4 text-[#1E5E45]" />;
      case 'transport':
        return <Bus className="w-4 h-4 text-[#1E5E45]" />;
      case 'utilities':
        return <Zap className="w-4 h-4 text-[#1E5E45]" />;
      default:
        return <Receipt className="w-4 h-4 text-[#1E5E45]" />;
    }
  };

  const getCategoryName = (code: string) => {
    switch (code) {
      case 'food':
        return t.categoryFood;
      case 'housing':
        return t.categoryHousing;
      case 'transport':
        return t.categoryTransport;
      case 'utilities':
        return t.categoryUtilities;
      default:
        return t.categoryOtherEssentials;
    }
  };

  return (
    <section
      aria-label="District Living Cost Comparison Card"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-4 sm:p-6 shadow-xs flex flex-col gap-5"
    >
      {/* Top Header Badge Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#F0ECE4]">
        <div>
          <span className="bg-[#E4ECE5] text-[#244E38] text-[11px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider inline-block">
            {t.illustrativeBenchmarkBadge}
          </span>
          <div className="text-[11.5px] text-[#697B71] font-medium mt-1.5 flex items-center gap-2">
            <span>{t.monthlyEssentialsLabel}</span>
            {districtComparisonApi?.costOfLivingMultiplier && (
              <span className="bg-[#E7F3EC] text-[#1E5E45] text-[10.5px] font-semibold px-2 py-0.5 rounded-full border border-[#CCE2D4] inline-flex items-center gap-1">
                <span>⚡ Cost Multiplier:</span>
                <strong>{districtComparisonApi.costOfLivingMultiplier}x (Live API)</strong>
              </span>
            )}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 font-medium text-[#143B2A]">
            <span className="w-2.5 h-2.5 rounded-full bg-[#1E5E45]" />
            <span>{districtA.districtName}</span>
          </div>
          <div className="flex items-center gap-1.5 font-medium text-[#5B6D62]">
            <span className="w-2.5 h-2.5 rounded-sm border-2 border-[#6D7F74] bg-[#9BB0A3]" />
            <span>{districtB.districtName}</span>
          </div>
        </div>
      </div>

      {/* Main Totals Comparison Box */}
      <div className="bg-[#FAF8F4] border border-[#E8E2D6] rounded-xl p-4 flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-3 divide-x divide-[#E7E1D4]">
          {/* District A Total */}
          <div className="pr-2">
            <span className="text-[11px] font-semibold text-[#576B60] block uppercase tracking-wider">
              {districtA.districtName}
            </span>
            <div className="font-serif text-2xl sm:text-3xl font-bold text-[#143B2A] mt-0.5">
              {districtA.baselineTotal.toLocaleString()}
              <span className="text-xs font-sans font-normal text-[#667A6E] ml-1">RWF</span>
            </div>
            <span className="text-[10.5px] text-[#718378] block mt-0.5">
              {districtA.provinceEn}
            </span>
          </div>

          {/* District B Total */}
          <div className="pl-3 sm:pl-4">
            <span className="text-[11px] font-semibold text-[#576B60] block uppercase tracking-wider">
              {districtB.districtName}
            </span>
            <div className="font-serif text-2xl sm:text-3xl font-bold text-[#143B2A] mt-0.5">
              {districtB.baselineTotal.toLocaleString()}
              <span className="text-xs font-sans font-normal text-[#667A6E] ml-1">RWF</span>
            </div>
            <span className="text-[10.5px] text-[#718378] block mt-0.5">
              {districtB.provinceEn}
            </span>
          </div>
        </div>

        {/* Highlight Difference Banner */}
        <div
          className={`pt-2.5 border-t border-[#E8E2D6] flex items-center justify-between gap-2 text-xs font-medium rounded-lg px-2.5 py-1.5 ${
            isLower
              ? 'bg-[#EAF5EE] text-[#1E5E45] border border-[#CCE7D5]'
              : diffTotal === 0
              ? 'bg-[#F4F1EA] text-[#4F6257]'
              : 'bg-[#FFF7E8] text-[#9A6400] border border-[#F2DEB0]'
          }`}
        >
          <div className="flex items-center gap-1.5 min-w-0">
            {isLower ? (
              <TrendingDown className="w-4 h-4 shrink-0 text-emerald-700" />
            ) : diffTotal === 0 ? (
              <span className="w-2 h-2 rounded-full bg-slate-400 shrink-0" />
            ) : (
              <TrendingUp className="w-4 h-4 shrink-0 text-amber-600" />
            )}
            <span className="truncate text-[11.5px] sm:text-xs">
              {districtB.districtName}{' '}
              {isLower
                ? `${absDiff.toLocaleString()} RWF (-${percentDiff}%) ${t.costDifferenceLess}`
                : diffTotal === 0
                ? `has equal living benchmark as`
                : `${absDiff.toLocaleString()} RWF (+${percentDiff}%) ${t.costDifferenceMore}`}{' '}
              {districtA.districtName} ({householdSize})
            </span>
          </div>
          <span className="font-bold shrink-0">
            {isLower ? `-${percentDiff}%` : diffTotal === 0 ? '0%' : `+${percentDiff}%`}
          </span>
        </div>
      </div>

      {/* Categories Table with Double Horizontal Bars */}
      <div className="flex flex-col gap-4">
        {/* Table Column Labels */}
        <div className="grid grid-cols-12 gap-2 pb-1.5 border-b border-[#F0ECE4] text-[10.5px] font-bold text-[#718378] uppercase tracking-wider">
          <div className="col-span-5">{t.categoryHeader}</div>
          <div className="col-span-2 text-right">{districtA.districtName.toUpperCase()}</div>
          <div className="col-span-2 text-right">{districtB.districtName.toUpperCase()}</div>
          <div className="col-span-3 text-right">{t.differenceHeader}</div>
        </div>

        {/* Rows */}
        <div className="flex flex-col divide-y divide-[#F2EFE8]">
          {districtA.lines.map((lineA, idx) => {
            const lineB = districtB.lines[idx] ?? lineA;
            const rowDiff = lineB.amount - lineA.amount;
            const isRowLower = rowDiff < 0;
            const rowPct = lineA.amount > 0 ? Math.round((Math.abs(rowDiff) / lineA.amount) * 100) : 0;

            const barAWidth = Math.round((lineA.amount / maxCategoryAmount) * 100);
            const barBWidth = Math.round((lineB.amount / maxCategoryAmount) * 100);

            return (
              <div key={lineA.categoryCode} className="py-3 flex flex-col gap-2 group">
                <div className="grid grid-cols-12 gap-2 items-center text-xs">
                  {/* Category Name & Icon */}
                  <div className="col-span-5 flex items-center gap-2 min-w-0">
                    <div className="w-7 h-7 rounded-lg bg-[#EBF3ED] flex items-center justify-center shrink-0 border border-[#D5E6DC]">
                      {getCategoryIcon(lineA.categoryCode)}
                    </div>
                    <div className="min-w-0">
                      <span className="font-semibold text-sm text-[#182C22] block truncate">
                        {getCategoryName(lineA.categoryCode)}
                      </span>
                      <span className="text-[10.5px] text-[#718479] truncate block hidden sm:block">
                        {language === 'RW' ? lineB.noteRw : lineB.noteEn}
                      </span>
                    </div>
                  </div>

                  {/* District A Amount */}
                  <div className="col-span-2 text-right">
                    <span className="font-bold text-sm text-[#143B2A]">
                      {lineA.amount.toLocaleString()}
                    </span>
                  </div>

                  {/* District B Amount */}
                  <div className="col-span-2 text-right">
                    <span className="font-medium text-sm text-[#4E6256]">
                      {lineB.amount.toLocaleString()}
                    </span>
                  </div>

                  {/* Difference Badge */}
                  <div className="col-span-3 text-right">
                    <span
                      className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[11px] font-bold ${
                        isRowLower
                          ? 'bg-[#EBF6EE] text-[#1E5E45] border border-[#CFE7D7]'
                          : rowDiff === 0
                          ? 'bg-gray-100 text-gray-600 border border-gray-200'
                          : 'bg-[#FFF6E6] text-[#A16207] border border-[#F6E1B6]'
                      }`}
                    >
                      {isRowLower ? (
                        <>
                          <ArrowDownRight className="w-3 h-3 text-emerald-700" />
                          <span>-{Math.abs(rowDiff).toLocaleString()}</span>
                        </>
                      ) : rowDiff === 0 ? (
                        <span>0</span>
                      ) : (
                        <>
                          <ArrowUpRight className="w-3 h-3 text-amber-600" />
                          <span>+{rowDiff.toLocaleString()}</span>
                        </>
                      )}
                    </span>
                    <span className="text-[9.5px] text-[#7E8F85] block mt-0.5 font-medium">
                      {isRowLower ? `-${rowPct}%` : rowDiff === 0 ? 'equal' : `+${rowPct}%`}
                    </span>
                  </div>
                </div>

                {/* Double Comparative Flat Bars */}
                <div className="flex flex-col gap-1 pl-9 pr-2">
                  {/* Bar for District A (Solid Forest Green) */}
                  <div className="w-full bg-[#EFECE5] h-2 rounded-full overflow-hidden flex items-center">
                    <div
                      className="bg-[#1E5E45] h-full transition-all duration-300"
                      style={{ width: `${barAWidth}%` }}
                      title={`${districtA.districtName}: ${lineA.amount.toLocaleString()} RWF`}
                    />
                  </div>

                  {/* Bar for District B (Muted Slate / Sage) */}
                  <div className="w-full bg-[#EFECE5] h-2 rounded-full overflow-hidden flex items-center">
                    <div
                      className="bg-[#718779] h-full transition-all duration-300"
                      style={{ width: `${barBWidth}%` }}
                      title={`${districtB.districtName}: ${lineB.amount.toLocaleString()} RWF`}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Total Monthly Essentials Footer Row */}
        <div className="pt-3 border-t-2 border-[#1E5E45]/20 flex items-center justify-between">
          <div>
            <span className="font-semibold text-sm text-[#182C22] block">
              {t.totalMonthlyEssentials}
            </span>
            <span className="text-[11px] text-[#697B71]">
              {districtA.districtName} vs {districtB.districtName} · {householdSize}
            </span>
          </div>

          <div className="text-right">
            <div className="font-serif text-lg sm:text-xl font-bold text-[#143B2A]">
              <span>{districtA.baselineTotal.toLocaleString()}</span>
              <span className="text-[#8B9C91] mx-1">/</span>
              <span className="text-[#4F6257]">{districtB.baselineTotal.toLocaleString()}</span>
              <span className="text-xs font-sans font-normal text-[#697B71] ml-1">RWF</span>
            </div>
            <span
              className={`text-[11px] font-semibold ${
                isLower ? 'text-emerald-700' : diffTotal === 0 ? 'text-gray-500' : 'text-amber-700'
              }`}
            >
              {isLower
                ? `Net savings: -${absDiff.toLocaleString()} RWF/mo in ${districtB.districtName}`
                : diffTotal === 0
                ? 'Equal total essentials cost'
                : `Higher: +${absDiff.toLocaleString()} RWF/mo in ${districtB.districtName}`}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
