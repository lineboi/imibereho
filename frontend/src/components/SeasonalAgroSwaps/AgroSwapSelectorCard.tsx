import React, { useState } from 'react';
import type { Language } from '../../types';
import type { AgroSwapItem } from '../../data/mockAgroSwapsData';
import { AGRO_SWAPS_DATA, AGRO_SWAPS_TRANSLATIONS } from '../../data/mockAgroSwapsData';
import { ArrowLeftRight, Check, Sparkles, ChevronRight, ChevronLeft, Flame } from 'lucide-react';

interface AgroSwapSelectorCardProps {
  selectedSwap: AgroSwapItem;
  onSelectSwap: (swap: AgroSwapItem) => void;
  language: Language;
}

export const AgroSwapSelectorCard: React.FC<AgroSwapSelectorCardProps> = ({
  selectedSwap,
  onSelectSwap,
  language,
}) => {
  const t = AGRO_SWAPS_TRANSLATIONS[language];
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<string>('all');

  const categories = [
    { id: 'all', label: t.filterAll },
    { id: 'staple', label: t.filterStaple },
    { id: 'protein', label: t.filterProtein },
    { id: 'fuel', label: t.filterFuel },
  ];

  const filteredSwaps = AGRO_SWAPS_DATA.filter((s) => {
    if (activeCategoryFilter === 'all') return true;
    if (activeCategoryFilter === 'staple') return s.category === 'staple' || s.category === 'tuber';
    if (activeCategoryFilter === 'protein') return s.category === 'protein' || s.category === 'vegetable';
    if (activeCategoryFilter === 'fuel') return s.category === 'fuel';
    return true;
  });

  const currentIndex = AGRO_SWAPS_DATA.findIndex((s) => s.id === selectedSwap.id);

  const handleNext = () => {
    const nextIndex = (currentIndex + 1) % AGRO_SWAPS_DATA.length;
    onSelectSwap(AGRO_SWAPS_DATA[nextIndex]);
  };

  const handlePrev = () => {
    const prevIndex = (currentIndex - 1 + AGRO_SWAPS_DATA.length) % AGRO_SWAPS_DATA.length;
    onSelectSwap(AGRO_SWAPS_DATA[prevIndex]);
  };

  return (
    <div className="bg-white rounded-2xl border border-[#E5DFD4] shadow-xs p-4 sm:p-5 flex flex-col gap-4">
      {/* Innovative Top Category Pills */}
      <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1 scrollbar-none border-b border-[#F0EBE1] -mx-1 px-1">
        <div className="flex items-center gap-1.5 shrink-0">
          {categories.map((cat) => {
            const isActive = activeCategoryFilter === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setActiveCategoryFilter(cat.id)}
                className={`text-[11.5px] px-2.5 py-1 rounded-full font-medium transition-colors cursor-pointer shrink-0 ${
                  isActive
                    ? 'bg-[#1E5E45] text-white shadow-2xs'
                    : 'bg-[#F4EFE6] text-[#55695D] hover:bg-[#EAE4D9]'
                }`}
              >
                {cat.label}
              </button>
            );
          })}
        </div>

        {/* Mini swap navigation buttons */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={handlePrev}
            aria-label="Previous agro swap"
            className="w-7 h-7 rounded-lg border border-[#E0D9CD] flex items-center justify-center text-[#586C60] hover:bg-[#F5F1E8] cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs text-[#7A8A81] px-1 font-mono">
            {currentIndex + 1}/{AGRO_SWAPS_DATA.length}
          </span>
          <button
            type="button"
            onClick={handleNext}
            aria-label="Next agro swap"
            className="w-7 h-7 rounded-lg border border-[#E0D9CD] flex items-center justify-center text-[#586C60] hover:bg-[#F5F1E8] cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quick alternative cards carousel / chips */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
        {filteredSwaps.map((swap) => {
          const isCurrent = swap.id === selectedSwap.id;
          return (
            <button
              key={swap.id}
              type="button"
              onClick={() => onSelectSwap(swap)}
              className={`text-left p-2 rounded-xl border transition-all cursor-pointer flex flex-col justify-between min-h-[58px] ${
                isCurrent
                  ? 'bg-[#EBF4EE] border-[#2A6D51] ring-1 ring-[#2A6D51]/30 shadow-xs'
                  : 'bg-[#FAF8F3] border-[#E8E2D7] hover:border-[#CFE0D6] text-[#4F6257]'
              }`}
            >
              <div className="flex items-center justify-between gap-1 w-full">
                <span className="text-[11px] font-semibold text-[#1B4332] truncate">
                  {swap.category === 'fuel' ? (
                    <span className="flex items-center gap-1 text-[#C05621]">
                      <Flame className="w-3 h-3 shrink-0" />
                      {language === 'RW' ? 'Amakara' : 'Fuel saver'}
                    </span>
                  ) : language === 'RW' ? (
                    swap.to.nameRw.split(' ')[0]
                  ) : (
                    swap.to.nameEn.split(' ')[0]
                  )}
                </span>
                {isCurrent && <Check className="w-3 h-3 text-[#1E5E45] shrink-0" />}
              </div>
              <span className="text-[10px] text-[#2D7354] font-medium mt-0.5">
                -{swap.difference.toLocaleString()} RWF
              </span>
            </button>
          );
        })}
      </div>

      {/* Main Feature Swap Block (Matching the user screenshot precisely) */}
      <div className="flex flex-col gap-3 pt-1">
        {/* Title with swap icon */}
        <div className="flex items-start gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#EBF4EE] text-[#1E5E45] flex items-center justify-center shrink-0 mt-0.5 border border-[#CFE4D7]">
            <ArrowLeftRight className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <h3 className="font-serif text-lg sm:text-xl font-normal text-[#123927] leading-snug">
              {language === 'RW' ? selectedSwap.titleRw : selectedSwap.titleEn}
            </h3>
            <p className="text-[13px] text-[#4F6257] leading-relaxed mt-1">
              {language === 'RW' ? selectedSwap.descriptionRw : selectedSwap.descriptionEn}
            </p>
          </div>
        </div>

        {/* Nutritional & Health Benefit Badge */}
        <div className="bg-[#FAF8F3] border border-[#E8E2D7] rounded-xl px-3 py-1.5 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-[#1E5E45] shrink-0" />
          <span className="text-[11.5px] text-[#345A46] font-medium">
            {language === 'RW' ? selectedSwap.nutritionTagRw : selectedSwap.nutritionTagEn}
          </span>
        </div>

        {/* Comparison Price Table (Exact layout from uploaded mockup) */}
        <div className="flex flex-col gap-2.5 pt-1">
          {/* Row 1: Item From */}
          <div className="flex items-baseline justify-between text-[13.5px]">
            <span className="text-[#3F5045]">
              {language === 'RW' ? selectedSwap.from.nameRw : selectedSwap.from.nameEn} -{' '}
              <span className="text-[#6C7E73]">{selectedSwap.from.quantity}</span>
            </span>
            <span className="font-semibold text-[#183928] tabular-nums">
              {selectedSwap.from.price.toLocaleString()} RWF
            </span>
          </div>

          {/* Row 2: Item To (Local / seasonal swap) */}
          <div className="flex items-baseline justify-between text-[13.5px]">
            <span className="text-[#3F5045]">
              {language === 'RW' ? selectedSwap.to.nameRw : selectedSwap.to.nameEn} -{' '}
              <span className="text-[#6C7E73]">{selectedSwap.to.quantity}</span>
            </span>
            <span className="font-semibold text-[#183928] tabular-nums">
              {selectedSwap.to.price.toLocaleString()} RWF
            </span>
          </div>

          {/* Thin divider */}
          <div className="h-px bg-[#EAE5DA] my-0.5" />

          {/* Row 3: Difference */}
          <div className="flex items-baseline justify-between text-[14px]">
            <span className="text-[#3F5045] font-medium">{t.exampleBasketDifference}</span>
            <span className="font-bold text-[#1E5E45] text-base tabular-nums">
              {selectedSwap.difference.toLocaleString()} RWF
            </span>
          </div>
        </div>

        {/* Footnote text from mockup */}
        <p className="text-[11px] text-[#78887F] leading-normal pt-1 border-t border-[#F2ECE2]">
          {language === 'RW' ? selectedSwap.footnoteRw : selectedSwap.footnoteEn}
        </p>
      </div>
    </div>
  );
};
