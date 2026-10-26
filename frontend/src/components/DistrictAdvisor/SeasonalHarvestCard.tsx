import React from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';
import { Sprout, Calendar } from 'lucide-react';

interface SeasonalHarvestCardProps {
  districtA: DistrictBenchmarkData;
  districtB: DistrictBenchmarkData;
  language: Language;
}

export const SeasonalHarvestCard: React.FC<SeasonalHarvestCardProps> = ({
  districtA,
  districtB,
  language,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];

  return (
    <div className="w-full bg-[#F4F8F4] border border-[#CFE4D6] rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl bg-[#E0EFE5] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#BEDEC8] mt-0.5">
          <Sprout className="w-5 h-5" />
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-serif text-sm sm:text-base font-semibold text-[#143D2C]">
              {t.seasonalTitle}
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider bg-[#E0EFE5] text-[#1E5E45] px-2 py-0.5 rounded-full border border-[#BEDEC8]">
              {t.seasonalBadge}
            </span>
          </div>
          <p className="text-xs sm:text-[12.5px] text-[#445A4C] leading-relaxed max-w-2xl">
            {t.seasonalText} In {districtB.districtName}, farm-to-table access preserves grocery budgets compared to metropolitan {districtA.districtName}.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#1E5E45] shrink-0 self-start sm:self-auto bg-white px-3 py-1.5 rounded-xl border border-[#CFE4D6]">
        <Calendar className="w-3.5 h-3.5" />
        <span>Season A Active</span>
      </div>
    </div>
  );
};
