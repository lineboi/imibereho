import React, { useState, useEffect } from 'react';
import type { Language, NavTab } from '../../types';
import type { AgroSwapItem } from '../../data/mockAgroSwapsData';
import {
  AGRO_SWAPS_DATA,
  MONTH_NAMES,
  AGRO_SWAPS_TRANSLATIONS,
} from '../../data/mockAgroSwapsData';
import { DISTRICTS } from '../../data/mockData';
import { fetchSeasonalSwaps, type SeasonalSwapApiItem } from '../../services/api';
import { HeroMarketBanner } from './HeroMarketBanner';
import { AgroSwapSelectorCard } from './AgroSwapSelectorCard';
import { MonthlySavingsProjector } from './MonthlySavingsProjector';
import { BalancedPlateCard } from './BalancedPlateCard';
import { SeasonalCalendarCard } from './SeasonalCalendarCard';
import { SmartMarketChecklist } from './SmartMarketChecklist';
import { BottomNav } from '../DailyTracker/BottomNav';
import { Info, ChevronDown } from 'lucide-react';

interface SeasonalAgroSwapsPageProps {
  language: Language;
  onNavigateHome: () => void;
  district?: string;
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const SeasonalAgroSwapsPage: React.FC<SeasonalAgroSwapsPageProps> = ({
  language,
  onNavigateHome,
  district: initialDistrict = 'Gasabo',
  activeTab,
  onTabChange,
}) => {
  const t = AGRO_SWAPS_TRANSLATIONS[language];

  // Selected district & month state
  const [selectedDistrict, setSelectedDistrict] = useState<string>(initialDistrict);
  const [selectedMonth, setSelectedMonth] = useState<string>('10'); // October (Season A active)

  const [swapsList, setSwapsList] = useState<AgroSwapItem[]>(AGRO_SWAPS_DATA);
  const [selectedSwap, setSelectedSwap] = useState<AgroSwapItem>(AGRO_SWAPS_DATA[0]);

  useEffect(() => {
    let isMounted = true;
    const m = parseInt(selectedMonth, 10) || 10;
    fetchSeasonalSwaps(selectedDistrict, m).then((data) => {
      if (!isMounted) return;
      if (data && data.items.length > 0) {
        const mapped: AgroSwapItem[] = data.items.map((it: SeasonalSwapApiItem) => ({
          id: it.id,
          category: 'staple',
          titleEn: it.title,
          titleRw: it.title,
          descriptionEn: it.description,
          descriptionRw: it.description,
          from: {
            nameEn: it.from.name,
            nameRw: it.from.name,
            quantity: `${it.from.quantity} ${it.from.unit}`,
            price: it.from.price,
          },
          to: {
            nameEn: it.to.name,
            nameRw: it.to.name,
            quantity: `${it.to.quantity} ${it.to.unit}`,
            price: it.to.price,
          },
          difference: it.difference,
          savingsMonthlyEstimate: Math.round(it.difference * 3 * 4.33),
          footnoteEn: it.footnote,
          footnoteRw: it.footnote,
          nutritionTagEn: 'Energy Staple Alternative',
          nutritionTagRw: 'Ibiribwa bitanga imbaraga',
        }));
        setSwapsList(mapped);
        setSelectedSwap(mapped[0]);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [selectedDistrict, selectedMonth]);

  return (
    <div className="flex-1 flex flex-col justify-between w-full">
      {/* Illustrative Demo Top Notice Bar */}
      <div className="w-full bg-[#EAF2ED] border-b border-[#D8E8DC] py-1.5 px-4 text-center">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-[#29563E]">
          {language === 'RW'
            ? 'IKIGERERANYO CY’ICYITEGEREREZO · SI IMBARAGA ZA LETA'
            : 'ILLUSTRATIVE DEMO · Not official statistics'}
        </span>
      </div>

      {/* Main Content Container */}
      <main className="max-w-3xl mx-auto w-full px-4 sm:px-6 py-5 sm:py-8 flex flex-col gap-5">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-1.5 text-xs font-bold tracking-wider uppercase text-[#355D47]">
          <button
            type="button"
            onClick={onNavigateHome}
            className="hover:underline cursor-pointer"
          >
            {language === 'RW' ? 'AHA BANZA' : 'HOME'}
          </button>
          <span>/</span>
          <span>{t.breadcrumb}</span>
        </div>

        {/* Page Title & Subtitle */}
        <div className="flex flex-col gap-1.5 -mt-1">
          <h1 className="font-serif text-3xl sm:text-4xl text-[#123927] font-normal tracking-tight">
            {t.headline}
          </h1>
          <p className="text-[13.5px] sm:text-[15px] text-[#4F6257] leading-relaxed max-w-2xl">
            {t.subheadline}
          </p>
        </div>

        {/* District & Planning Month Dropdowns (Side-by-side matching mockup) */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          {/* District selector */}
          <div className="flex flex-col gap-1">
            <label
              htmlFor="agro-district-select"
              className="text-xs font-semibold text-[#455A4D]"
            >
              {t.districtLabel}
            </label>
            <div className="relative">
              <select
                id="agro-district-select"
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(e.target.value)}
                className="w-full bg-white border border-[#D8D2C5] rounded-xl px-3 py-2.5 text-xs sm:text-sm font-semibold text-[#183928] appearance-none pr-8 focus:outline-none focus:ring-1 focus:ring-[#1E5E45] cursor-pointer shadow-2xs"
              >
                {DISTRICTS.map((d) => (
                  <option key={d.id} value={d.name}>
                    {d.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-[#6C7E73] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Planning Month selector */}
          <div className="flex flex-col gap-1">
            <label
              htmlFor="agro-month-select"
              className="text-xs font-semibold text-[#455A4D]"
            >
              {t.planningMonthLabel}
            </label>
            <div className="relative">
              <select
                id="agro-month-select"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="w-full bg-white border border-[#D8D2C5] rounded-xl px-3 py-2.5 text-xs sm:text-sm font-semibold text-[#183928] appearance-none pr-8 focus:outline-none focus:ring-1 focus:ring-[#1E5E45] cursor-pointer shadow-2xs"
              >
                {MONTH_NAMES.map((m) => (
                  <option key={m.value} value={m.value}>
                    {language === 'RW' ? m.labelRw : m.labelEn} (Season {m.season})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-[#6C7E73] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Card 1: Hero Market Banner (Fresh photo from mockup + local market ideas) */}
        <HeroMarketBanner district={selectedDistrict} language={language} />

        {/* Card 2: Main Agro Swap Selector Card (Matching mockup staple swap card + switcher) */}
        <AgroSwapSelectorCard
          selectedSwap={selectedSwap}
          onSelectSwap={setSelectedSwap}
          language={language}
          swaps={swapsList}
        />

        {/* Innovative Feature 1: Monthly Family Savings Projector & Equivalencies */}
        <MonthlySavingsProjector
          selectedSwap={selectedSwap}
          language={language}
          onNavigateTab={onTabChange}
        />

        {/* Card 3: Soft Green Card - Keep variety on the plate + Indyo Yuzuye 3-part breakdown */}
        <BalancedPlateCard language={language} />

        {/* Innovative Feature 2: Rwanda Agricultural Seasons Calendar (Season A active) */}
        <SeasonalCalendarCard language={language} />

        {/* Innovative Feature 3: Smart Market Shopping Checklist with Copy to SMS/MoMo */}
        <SmartMarketChecklist district={selectedDistrict} language={language} />

        {/* Card 4: Cautionary Disclaimer Card (Light tan background with info icon from mockup) */}
        <div className="bg-[#F6EEDB] border border-[#E9DFC7] rounded-2xl p-4 flex items-start gap-3 text-xs text-[#6F5732]">
          <Info className="w-4 h-4 text-[#98763A] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {t.disclaimerText}
          </p>
        </div>
      </main>

      {/* Mobile Bottom Navigation */}
      <BottomNav
        activeTab={activeTab}
        onTabChange={onTabChange}
        language={language}
      />
    </div>
  );
};
