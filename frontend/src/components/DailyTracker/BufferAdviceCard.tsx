import React from 'react';
import type { Language } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import { ArrowRight, ShieldAlert } from 'lucide-react';

interface BufferAdviceCardProps {
  language: Language;
  onOpenShockScenario: () => void;
}

export const BufferAdviceCard: React.FC<BufferAdviceCardProps> = ({
  language,
  onOpenShockScenario,
}) => {
  const t = TRACKER_TRANSLATIONS[language];

  return (
    <section
      aria-label="Buffer Guidance"
      className="w-full bg-[#E4ECE4] rounded-2xl p-5 border border-[#D3E1D4] flex flex-col shadow-2xs"
    >
      <h3 className="font-serif text-base sm:text-lg font-medium text-[#133A29]">
        {t.bufferCardTitle}
      </h3>

      <p className="text-xs sm:text-[13px] text-[#455A4E] leading-relaxed mt-1.5">
        {t.bufferCardDescription}
      </p>

      <button
        type="button"
        onClick={onOpenShockScenario}
        className="text-[#1E5E45] hover:text-[#123C2B] font-semibold text-xs sm:text-[13.5px] flex items-center gap-1.5 mt-3 self-start cursor-pointer group transition-colors"
      >
        <ShieldAlert className="w-3.5 h-3.5 text-[#1E5E45] group-hover:scale-110 transition-transform" />
        <span>{t.shockScenarioLink}</span>
        <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
      </button>
    </section>
  );
};
