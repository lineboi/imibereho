import React from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';
import { Wallet, TrendingUp, Sparkles } from 'lucide-react';

interface IncomeRunwayCardProps {
  districtA: DistrictBenchmarkData;
  districtB: DistrictBenchmarkData;
  householdIncome: number;
  onIncomeChange: (val: number) => void;
  language: Language;
}

export const IncomeRunwayCard: React.FC<IncomeRunwayCardProps> = ({
  districtA,
  districtB,
  householdIncome,
  onIncomeChange,
  language,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];

  // Calculations for District A
  const spendRatioA = Math.min(100, Math.round((districtA.baselineTotal / householdIncome) * 100));
  const bufferA = Math.max(0, householdIncome - districtA.baselineTotal);
  const emergencyFundA = districtA.baselineTotal * 3;
  const monthsToEmergencyA = bufferA > 0 ? (emergencyFundA / bufferA).toFixed(1) : '∞';

  // Calculations for District B
  const spendRatioB = Math.min(100, Math.round((districtB.baselineTotal / householdIncome) * 100));
  const bufferB = Math.max(0, householdIncome - districtB.baselineTotal);
  const emergencyFundB = districtB.baselineTotal * 3;
  const monthsToEmergencyB = bufferB > 0 ? (emergencyFundB / bufferB).toFixed(1) : '∞';

  // Speedup multiplier
  const speedup =
    bufferA > 0 && bufferB > 0 ? (Number(monthsToEmergencyA) / Number(monthsToEmergencyB)).toFixed(1) : '1.0';
  const isFasterInB = Number(speedup) > 1.0;

  const handleIncomeInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value.replace(/[^0-9]/g, ''), 10);
    onIncomeChange(isNaN(val) ? 0 : Math.max(10000, val));
  };

  return (
    <section
      aria-label="Household Income Feasibility and Buffer Runway"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-4 sm:p-6 shadow-xs flex flex-col gap-4"
    >
      {/* Title & Income Input Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#F0ECE4]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
            <Wallet className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-medium text-[#133A29]">
              {t.incomeRunwayTitle}
            </h3>
            <p className="text-[11.5px] text-[#697B71]">
              {t.incomeRunwaySub}
            </p>
          </div>
        </div>

        {/* Income Input Field */}
        <div className="flex items-center gap-2 self-start sm:self-auto bg-[#FAF8F4] border border-[#DCD5C9] rounded-xl px-3 py-1.5 shadow-2xs">
          <span className="text-xs font-semibold text-[#485C50]">
            {t.monthlyIncomeInputLabel}:
          </span>
          <div className="flex items-center">
            <input
              type="text"
              value={householdIncome.toLocaleString()}
              onChange={handleIncomeInput}
              className="w-24 text-right font-bold text-sm text-[#143B2A] bg-transparent focus:outline-none"
            />
            <span className="text-[11px] font-semibold text-[#6E8074] ml-1">RWF</span>
          </div>
        </div>
      </div>

      {/* Side-by-Side Runway Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* District A Metric Box */}
        <div className="bg-[#FAF8F4] border border-[#E7E2D6] rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-[#1E5E45] uppercase tracking-wider">
              {districtA.districtName} (Baseline)
            </span>
            <span
              className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                spendRatioA > 80
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              }`}
            >
              {spendRatioA}% {t.essentialsShareLabel}
            </span>
          </div>

          {/* Visual Spend vs Buffer Bar */}
          <div className="w-full bg-[#E5DFD4] h-2.5 rounded-full overflow-hidden flex">
            <div
              className={`h-full ${spendRatioA > 80 ? 'bg-amber-600' : 'bg-[#1E5E45]'}`}
              style={{ width: `${spendRatioA}%` }}
              title={`Essentials: ${spendRatioA}%`}
            />
            <div
              className="h-full bg-emerald-400"
              style={{ width: `${100 - spendRatioA}%` }}
              title={`Savings buffer: ${100 - spendRatioA}%`}
            />
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-[#ECE6DB] text-xs">
            <div>
              <span className="text-[10.5px] text-[#6E8175] block">{t.bufferLeftLabel}</span>
              <span className="font-bold text-sm text-[#153D2B]">
                +{bufferA.toLocaleString()} RWF
              </span>
            </div>
            <div>
              <span className="text-[10.5px] text-[#6E8175] block">{t.monthsToEmergencyFund}</span>
              <span className="font-bold text-sm text-[#153D2B]">
                {monthsToEmergencyA} months
              </span>
            </div>
          </div>
        </div>

        {/* District B Metric Box */}
        <div className="bg-[#FAF8F4] border border-[#E7E2D6] rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-[#2A5C46] uppercase tracking-wider">
              {districtB.districtName} (Comparison)
            </span>
            <span
              className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                spendRatioB > 80
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              }`}
            >
              {spendRatioB}% {t.essentialsShareLabel}
            </span>
          </div>

          {/* Visual Spend vs Buffer Bar */}
          <div className="w-full bg-[#E5DFD4] h-2.5 rounded-full overflow-hidden flex">
            <div
              className={`h-full ${spendRatioB > 80 ? 'bg-amber-600' : 'bg-[#1E5E45]'}`}
              style={{ width: `${spendRatioB}%` }}
              title={`Essentials: ${spendRatioB}%`}
            />
            <div
              className="h-full bg-emerald-400"
              style={{ width: `${100 - spendRatioB}%` }}
              title={`Savings buffer: ${100 - spendRatioB}%`}
            />
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-[#ECE6DB] text-xs">
            <div>
              <span className="text-[10.5px] text-[#6E8175] block">{t.bufferLeftLabel}</span>
              <span className="font-bold text-sm text-emerald-800">
                +{bufferB.toLocaleString()} RWF
              </span>
            </div>
            <div>
              <span className="text-[10.5px] text-[#6E8175] block">{t.monthsToEmergencyFund}</span>
              <span className="font-bold text-sm text-emerald-800">
                {monthsToEmergencyB} months
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Runway Speedup Insight Banner */}
      {isFasterInB && (
        <div className="bg-[#EBF7EE] border border-[#CFE8D7] rounded-xl p-3 flex items-center justify-between gap-3 text-xs text-[#185339]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>{speedup}× {t.runwaySpeedup} {districtB.districtName}</strong>: Saving an extra{' '}
              {Math.abs(bufferB - bufferA).toLocaleString()} RWF each month reduces emergency buffer build time from{' '}
              {monthsToEmergencyA} to {monthsToEmergencyB} months.
            </span>
          </div>
          <div className="flex items-center gap-1 font-bold text-emerald-700 shrink-0">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>High Resilience</span>
          </div>
        </div>
      )}
    </section>
  );
};
