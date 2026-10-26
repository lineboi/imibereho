import React from 'react';
import type { Language } from '../../types';
import { AGRO_SWAPS_TRANSLATIONS } from '../../data/mockAgroSwapsData';
import { Store, MapPin } from 'lucide-react';

interface HeroMarketBannerProps {
  district: string;
  language: Language;
}

export const HeroMarketBanner: React.FC<HeroMarketBannerProps> = ({ district, language }) => {
  const t = AGRO_SWAPS_TRANSLATIONS[language];

  // Representative local markets by district
  const getMarketName = (dist: string) => {
    const d = dist.toLowerCase();
    if (d === 'gasabo') return 'Kimironko & Kinyinya Markets';
    if (d === 'nyarugenge') return 'Nyabugogo & City Market';
    if (d === 'kicukiro') return 'Kicukiro & Zinia Markets';
    if (d === 'musanze') return 'Musanze Modern Market & Goico';
    if (d === 'huye') return 'Huye Main Market';
    if (d === 'rubavu') return 'Gisenyi Cross-Border Market';
    if (d === 'nyagatare') return 'Nyagatare Cattle & Produce Market';
    return `${dist} Central Market`;
  };

  return (
    <div className="bg-white rounded-2xl border border-[#E5DFD4] shadow-xs overflow-hidden">
      {/* Real photographic hero image extracted from user design mockup */}
      <div className="w-full h-48 sm:h-64 overflow-hidden relative bg-[#EFE9DF]">
        <img
          src="/assets/agro-basket.png"
          alt="Rwandan market fresh produce: beans, sweet potatoes, and amaranth greens"
          className="w-full h-full object-cover object-center"
        />
        {/* Subtle market badge in top corner */}
        <div className="absolute top-3 left-3 bg-[#1E2922]/75 backdrop-blur-md text-white text-[11px] font-medium px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-sm">
          <MapPin className="w-3 h-3 text-[#52B788]" />
          <span>{getMarketName(district)}</span>
        </div>
      </div>

      {/* Content description area directly below the photo, matching mockup */}
      <div className="p-4 sm:p-5 flex flex-col gap-2">
        <div>
          <span className="inline-block bg-[#E8F2EC] text-[#1E5E45] text-[10.5px] sm:text-[11px] font-bold tracking-wider uppercase px-2.5 py-0.5 rounded-full border border-[#D0E5D8]">
            {t.marketHeroTag}
          </span>
        </div>

        <h2 className="font-serif text-xl sm:text-2xl text-[#143B2A] font-normal leading-snug">
          {t.marketHeroTitle}
        </h2>

        <p className="text-[13px] sm:text-[13.5px] text-[#4F6257] leading-relaxed">
          {t.marketHeroSub}
        </p>

        {/* Local market insight footer */}
        <div className="mt-1 pt-2.5 border-t border-[#F0EBE1] flex items-center justify-between text-xs text-[#6B7D73]">
          <div className="flex items-center gap-1.5">
            <Store className="w-3.5 h-3.5 text-[#1E5E45]" />
            <span>
              {language === 'RW'
                ? `Isoko ry’ibanze: ${getMarketName(district)}`
                : `Primary reference: ${getMarketName(district)}`}
            </span>
          </div>
          <span className="hidden sm:inline-block text-[11px] bg-[#FAF8F3] px-2 py-0.5 rounded text-[#7B8B82] border border-[#EAE5DB]">
            {language === 'RW' ? 'Icyiciro cya A' : 'Season A Harvest'}
          </span>
        </div>
      </div>
    </div>
  );
};
