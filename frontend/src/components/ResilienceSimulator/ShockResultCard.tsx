import React from 'react';
import type { Language } from '../../types';
import { RESILIENCE_TRANSLATIONS } from '../../data/mockResilienceData';
import { CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

interface ShockResultCardProps {
  shockedIncome: number;
  plannedExpenses: number;
  rawGap: number;
  netGap: number;
  durationMonths: number;
  availableSavings: number;
  savingsUsed: number;
  savingsRemain: number;
  language: Language;
  totalCopingRelief: number;
}

export const ShockResultCard: React.FC<ShockResultCardProps> = ({
  shockedIncome,
  plannedExpenses,
  netGap,
  durationMonths,
  savingsUsed,
  savingsRemain,
  language,
  totalCopingRelief,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];
  const isResolved = netGap === 0 && totalCopingRelief > 0;
  const isSurplus = netGap < 0;

  return (
    <section
      aria-label="Illustrative Monthly Result"
      className="w-full bg-[#1A4532] text-white rounded-3xl p-6 sm:p-7 shadow-md flex flex-col gap-4 relative overflow-hidden"
    >
      {/* Decorative background glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Tag Pill */}
      <div className="flex items-center justify-between">
        <span className="text-[10.5px] font-bold uppercase tracking-wider text-[#98C7AA]">
          {t.illustrativeResultBadge}
        </span>
        {isResolved && (
          <span className="inline-flex items-center gap-1 bg-[#2C6B4E] text-[#D8F5E5] text-[10.5px] font-bold px-2.5 py-0.5 rounded-full border border-emerald-400/40">
            <Sparkles className="w-3 h-3 text-emerald-300" />
            <span>{t.gapResolvedBadge}</span>
          </span>
        )}
      </div>

      {/* Large Hero Gap Number */}
      <div className="flex flex-col gap-1 -mt-1">
        <div className="font-serif text-4xl sm:text-5xl font-medium tracking-tight text-white flex items-baseline gap-2">
          {isSurplus ? (
            <>
              <span className="text-emerald-300">+{Math.abs(netGap).toLocaleString()}</span>
              <span className="text-xl sm:text-2xl font-sans font-normal text-[#C3E2D0]">
                {t.surplusSuffix}
              </span>
            </>
          ) : isResolved ? (
            <>
              <span className="text-emerald-300">0</span>
              <span className="text-xl sm:text-2xl font-sans font-normal text-[#C3E2D0]">
                {t.gapSuffix}
              </span>
            </>
          ) : (
            <>
              <span>{netGap.toLocaleString()}</span>
              <span className="text-xl sm:text-2xl font-sans font-normal text-[#C3E2D0]">
                {t.gapSuffix}
              </span>
            </>
          )}
        </div>

        {/* Explanatory text */}
        <p className="text-xs sm:text-sm text-[#C8E0D2] leading-relaxed">
          {t.incomeComparisonText}{' '}
          <strong className="text-white font-semibold">
            {shockedIncome.toLocaleString()} RWF
          </strong>{' '}
          {t.againstPlannedText.replace('150,000', plannedExpenses.toLocaleString())}
        </p>
      </div>

      {/* Drawdown & Remaining Savings Breakdown */}
      <div className="pt-4 border-t border-white/15 flex flex-col gap-2 text-xs sm:text-[13px] text-[#D2E7DC]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isResolved ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-300 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-amber-300 shrink-0" />
            )}
            <span>
              <strong className="text-white">{savingsUsed.toLocaleString()} RWF</strong>{' '}
              {t.savingsUsedText} {durationMonths} {language === 'RW' ? 'amezi' : 'months'}
            </span>
          </div>
          <span className="text-[11px] text-[#A6CDB7] font-mono">
            {durationMonths}mo impact
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded-full bg-emerald-400/20 border border-emerald-300/40 flex items-center justify-center shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-300" />
            </span>
            <span>
              <strong className="text-white">{savingsRemain.toLocaleString()} RWF</strong>{' '}
              {t.savingsRemainText}
            </span>
          </div>
          <span className="text-[11px] text-emerald-300 font-semibold">
            {savingsRemain > 0 ? 'Buffer Active' : 'Depleted'}
          </span>
        </div>
      </div>
    </section>
  );
};
