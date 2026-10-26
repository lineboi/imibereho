import React from 'react';
import type { Language } from '../../types';
import { RESILIENCE_TRANSLATIONS } from '../../data/mockResilienceData';
import { TrendingDown, Shield } from 'lucide-react';

interface BufferRunwayTimelineProps {
  initialSavings: number;
  rawGap: number;
  netGap: number;
  durationMonths: number;
  language: Language;
}

export const BufferRunwayTimeline: React.FC<BufferRunwayTimelineProps> = ({
  initialSavings,
  rawGap,
  netGap,
  durationMonths,
  language,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];

  // Generate milestone months (Month 0, Month 1, Month 2, Month 3, and duration horizon)
  const months = Array.from({ length: Math.min(6, durationMonths + 1) }, (_, i) => i);

  return (
    <section
      aria-label="Month-by-Month Savings Timeline"
      className="w-full bg-white rounded-3xl border border-[#E3DED4] p-5 sm:p-7 shadow-xs flex flex-col gap-4"
    >
      <div className="flex items-center justify-between pb-2 border-b border-[#F0ECE4]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
            <TrendingDown className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-medium text-[#133A29]">
              {t.depletionTimelineTitle}
            </h3>
            <p className="text-[11.5px] text-[#697B71]">
              {t.depletionTimelineSub}
            </p>
          </div>
        </div>

        <span className="text-xs font-semibold text-[#1E5E45] bg-[#EAF5EE] px-2.5 py-1 rounded-full border border-[#CCE8D5]">
          {durationMonths} Months Horizon
        </span>
      </div>

      {/* Monthly Timeline Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {months.map((m) => {
          const rawBalance = Math.max(0, initialSavings - rawGap * m);
          const netBalance = Math.max(0, initialSavings - Math.max(0, netGap) * m);
          const isLeversActive = netGap < rawGap;

          return (
            <div
              key={m}
              className={`p-3 rounded-2xl border flex flex-col gap-1 transition-all ${
                m === 0
                  ? 'bg-[#FAF8F4] border-[#E2DBD0]'
                  : isLeversActive && netGap === 0
                  ? 'bg-[#F2FAF4] border-[#CDE8D5]'
                  : 'bg-white border-[#E7E1D4]'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-bold text-[#6D8075]">
                <span>{m === 0 ? 'Start' : `Month ${m}`}</span>
                {m === 0 && <Shield className="w-3 h-3 text-[#1E5E45]" />}
              </div>

              {/* Balance */}
              <div className="font-serif text-base sm:text-lg font-bold text-[#143B2A] mt-1">
                {isLeversActive && m > 0 && rawBalance !== netBalance && (
                  <span className="text-xs font-sans line-through text-[#8F9F95] mr-1.5 font-normal">
                    {rawBalance.toLocaleString()}
                  </span>
                )}
                {netBalance.toLocaleString()}
                <span className="text-[10px] font-sans font-normal text-[#64766C] ml-1">RWF</span>
              </div>

              {/* Status or Delta */}
              {m > 0 && (
                <div className="text-[10px] flex items-center justify-between pt-1 border-t border-[#EDE7DD]">
                  <span className="text-[#88998F]">
                    {isLeversActive && netGap === 0 ? 'Zero loss' : `-${(Math.max(0, netGap) * m).toLocaleString()}`}
                  </span>
                  <span
                    className={`font-semibold ${
                      netBalance > 0 ? 'text-emerald-700' : 'text-rose-600'
                    }`}
                  >
                    {netBalance > 0 ? 'Protected' : 'Exhausted'}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};
