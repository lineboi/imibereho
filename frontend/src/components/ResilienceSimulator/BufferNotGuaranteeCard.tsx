import React from 'react';
import type { Language } from '../../types';
import { RESILIENCE_TRANSLATIONS } from '../../data/mockResilienceData';
import { ShieldCheck, Compass } from 'lucide-react';

interface BufferNotGuaranteeCardProps {
  savings: number;
  gap: number;
  runwayMonths: string;
  language: Language;
}

export const BufferNotGuaranteeCard: React.FC<BufferNotGuaranteeCardProps> = ({
  savings,
  gap,
  runwayMonths,
  language,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];

  return (
    <section
      aria-label="Buffer Runway and Practical Advice"
      className="w-full bg-white rounded-3xl border border-[#E3DED4] p-5 sm:p-7 shadow-xs flex flex-col gap-4"
    >
      {/* Top Header */}
      <div className="flex items-center justify-between pb-1">
        <h3 className="font-serif text-xl sm:text-2xl font-normal text-[#123927]">
          {t.bufferNotGuaranteeTitle}
        </h3>
        <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
          <ShieldCheck className="w-4 h-4" />
        </div>
      </div>

      {/* Runway Math Row */}
      <div className="flex items-baseline justify-between pt-1 pb-1">
        <span className="text-xs sm:text-sm font-semibold text-[#485C50]">
          {t.savingsDividedGapLabel}
        </span>
        <div className="font-serif text-2xl sm:text-3xl font-bold text-[#143B2A]">
          {runwayMonths}{' '}
          <span className="text-xs sm:text-sm font-sans font-normal text-[#64766C]">
            {t.runwayUnit}
          </span>
        </div>
      </div>

      {/* Math Formula Explainer */}
      <p className="text-[11.5px] sm:text-xs text-[#6B7D72] leading-relaxed -mt-1">
        {gap > 0
          ? `${savings.toLocaleString()} ÷ ${gap.toLocaleString()} = ${runwayMonths} ${t.runwayUnit} ${t.runwayMathText}`
          : language === 'RW'
          ? 'Nta cyuho gihari: ubwizigame bwawe burarinzwe 100% nta mafaranga akenewe gukurwaho.'
          : 'Zero monthly gap: your buffer is 100% protected and no savings drawdown is required.'}
      </p>

      {/* Practical Next Step Section */}
      <div className="pt-4 border-t border-[#F0ECE4] flex flex-col gap-1.5">
        <div className="flex items-center gap-1.5 text-xs font-bold text-[#1E5E45] uppercase tracking-wider">
          <Compass className="w-3.5 h-3.5" />
          <span>{t.practicalNextStepTitle}</span>
        </div>
        <p className="text-xs sm:text-[13px] text-[#44584C] leading-relaxed">
          {t.practicalNextStepText}
        </p>
      </div>
    </section>
  );
};
