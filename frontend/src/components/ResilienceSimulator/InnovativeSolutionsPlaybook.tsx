import React from 'react';
import type { Language } from '../../types';
import {
  INNOVATIVE_COPING_LEVERS,
  RESILIENCE_TRANSLATIONS,
} from '../../data/mockResilienceData';
import {
  Scissors,
  Sprout,
  Users2,
  Smartphone,
  Briefcase,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

interface InnovativeSolutionsPlaybookProps {
  activeLeverIds: string[];
  onToggleLever: (leverId: string) => void;
  rawGap: number;
  netGap: number;
  language: Language;
}

export const InnovativeSolutionsPlaybook: React.FC<InnovativeSolutionsPlaybookProps> = ({
  activeLeverIds,
  onToggleLever,
  rawGap,
  netGap,
  language,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];

  const getLeverIcon = (type: string) => {
    switch (type) {
      case 'trim':
        return <Scissors className="w-4 h-4 text-[#1E5E45]" />;
      case 'swap':
        return <Sprout className="w-4 h-4 text-[#1E5E45]" />;
      case 'tontine':
        return <Users2 className="w-4 h-4 text-[#1E5E45]" />;
      case 'momo':
        return <Smartphone className="w-4 h-4 text-[#1E5E45]" />;
      default:
        return <Briefcase className="w-4 h-4 text-[#1E5E45]" />;
    }
  };

  const isGapResolved = netGap === 0 && rawGap > 0;
  const activeCount = activeLeverIds.length;

  return (
    <section
      aria-label="Innovative Coping Levers Playbook"
      className="w-full bg-white rounded-3xl border border-[#E3DED4] p-5 sm:p-7 shadow-xs flex flex-col gap-4.5"
    >
      {/* Title & Active Counter Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#F0ECE4]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-lg sm:text-xl font-normal text-[#123927]">
              {t.solutionsTitle}
            </h3>
            <p className="text-[11.5px] text-[#697B71]">
              {t.solutionsSub}
            </p>
          </div>
        </div>

        <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#EAF5EE] text-[#1E5E45] border border-[#CCE7D6] self-start sm:self-auto shrink-0">
          {activeCount} {t.activeLeversCount}
        </span>
      </div>

      {/* Levers List with Toggles */}
      <div className="flex flex-col divide-y divide-[#F2EFE8]">
        {INNOVATIVE_COPING_LEVERS.map((lever) => {
          const isActive = activeLeverIds.includes(lever.id);

          return (
            <div
              key={lever.id}
              className={`py-3.5 first:pt-1 last:pb-1 flex items-center justify-between gap-3 transition-colors rounded-xl px-2.5 ${
                isActive ? 'bg-[#F5FAF6]' : 'hover:bg-[#FAF8F4]'
              }`}
            >
              {/* Left: Icon, Title & Details */}
              <div className="flex items-start gap-3 min-w-0">
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border transition-all mt-0.5 ${
                    isActive
                      ? 'bg-[#1E5E45] text-white border-[#1E5E45]'
                      : 'bg-[#EBF3ED] border-[#D5E6DC]'
                  }`}
                >
                  {getLeverIcon(lever.iconType)}
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-xs sm:text-sm text-[#182C22]">
                      {language === 'RW' ? lever.titleRw : lever.titleEn}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        lever.type === 'lump_sum_aid'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      {lever.type === 'lump_sum_aid'
                        ? `+${lever.oneTimeBufferBoost?.toLocaleString()} RWF ${t.leverOneTimeBoost}`
                        : `+${lever.monthlySavings.toLocaleString()} RWF ${t.leverSavesMonthly}`}
                    </span>
                  </div>

                  <p className="text-[11px] text-[#697B71] mt-0.5 leading-relaxed line-clamp-2">
                    {language === 'RW' ? lever.subRw : lever.subEn}
                  </p>
                </div>
              </div>

              {/* Right: Interactive Toggle Switch */}
              <button
                type="button"
                onClick={() => onToggleLever(lever.id)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  isActive ? 'bg-[#1E5E45]' : 'bg-[#DCD5C9]'
                }`}
                role="switch"
                aria-checked={isActive}
                aria-label={`Toggle ${lever.titleEn}`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                    isActive ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          );
        })}
      </div>

      {/* Dynamic Coping Impact Callout */}
      {isGapResolved ? (
        <div className="bg-[#EBF7EE] border border-[#CCE8D5] rounded-2xl p-3.5 flex items-center justify-between gap-3 text-xs text-[#175238] shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>
              <strong>{t.gapResolvedBadge}:</strong> Your activated coping actions generate enough monthly savings to completely bridge the initial {rawGap.toLocaleString()} RWF gap without drawing down your family savings!
            </span>
          </div>
        </div>
      ) : (
        <div className="bg-[#FAF8F4] border border-[#EBE4D8] rounded-xl p-3 text-xs text-[#5C7063] flex items-center justify-between gap-2">
          <span>
            {language === 'RW'
              ? 'Kanda kuri buri mayeri hejuru kugira ngo uzibe icyuho kandi urinde ubwizigame bwawe.'
              : 'Toggle the action switches above to eliminate the monthly deficit and protect your savings.'}
          </span>
          <span className="font-bold text-[#1E5E45] shrink-0">
            {activeCount > 0 ? `${activeCount} levers active` : 'No levers active'}
          </span>
        </div>
      )}
    </section>
  );
};
