import React, { useState } from 'react';
import type { Language } from '../../types';
import { BALANCED_PLATE_COMPONENTS, AGRO_SWAPS_TRANSLATIONS } from '../../data/mockAgroSwapsData';
import { Utensils, Info, ShieldCheck, Zap, Heart } from 'lucide-react';

interface BalancedPlateCardProps {
  language: Language;
}

export const BalancedPlateCard: React.FC<BalancedPlateCardProps> = ({ language }) => {
  const t = AGRO_SWAPS_TRANSLATIONS[language];
  const [selectedComponent, setSelectedComponent] = useState<string>('energy');

  const getIcon = (code: string) => {
    if (code === 'energy') return <Zap className="w-3.5 h-3.5 text-[#D97706]" />;
    if (code === 'protective') return <ShieldCheck className="w-3.5 h-3.5 text-[#1E5E45]" />;
    return <Heart className="w-3.5 h-3.5 text-[#7C3AED]" />;
  };

  return (
    <div className="bg-[#EBF2EC] rounded-2xl border border-[#D1E3D7] p-4 sm:p-5 flex flex-col gap-3.5 shadow-2xs">
      {/* Title & Description Matching the Uploaded Design Mockup */}
      <div className="flex items-start gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-[#DEECE2] text-[#1E5E45] flex items-center justify-center shrink-0 mt-0.5 border border-[#C5DDD0]">
          <Utensils className="w-4 h-4" />
        </div>
        <div>
          <h3 className="font-serif text-lg sm:text-xl font-normal text-[#123927] leading-snug">
            {language === 'RW' ? t.balancedPlateTitle : 'Keep variety on the plate.'}
          </h3>
          <p className="text-[13px] text-[#3E5C4B] leading-relaxed mt-1">
            {language === 'RW' ? t.balancedPlateSub : t.balancedPlateSub}
          </p>
        </div>
      </div>

      {/* Innovative Rwandan "Indyo Yuzuye" 3-Part Plate Visualizer */}
      <div className="bg-white/80 backdrop-blur-xs rounded-xl p-3 border border-[#CFE3D5] flex flex-col gap-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-[#183928] flex items-center gap-1.5">
            <span>🇷🇼</span>
            <span>{language === 'RW' ? 'Ingano y’Indyo Yuzuye (MINAGRI/MINISANTE)' : 'Balanced Plate Standard (Indyo Yuzuye)'}</span>
          </span>
          <span className="text-[11px] text-[#557362] font-mono">50% · 25% · 25%</span>
        </div>

        {/* Proportional Plate Bar */}
        <div className="h-3.5 w-full rounded-full flex overflow-hidden ring-1 ring-black/5 p-0.5 bg-gray-100">
          <div
            className="bg-[#D97706] h-full rounded-l-full cursor-pointer transition-opacity hover:opacity-90"
            style={{ width: '50%' }}
            onClick={() => setSelectedComponent('energy')}
            title="50% Energy Staples"
          />
          <div
            className="bg-[#1E5E45] h-full cursor-pointer transition-opacity hover:opacity-90"
            style={{ width: '25%' }}
            onClick={() => setSelectedComponent('protective')}
            title="25% Protective Greens & Vegetables"
          />
          <div
            className="bg-[#7C3AED] h-full rounded-r-full cursor-pointer transition-opacity hover:opacity-90"
            style={{ width: '25%' }}
            onClick={() => setSelectedComponent('protein')}
            title="25% Plant Protein / Legumes"
          />
        </div>

        {/* Interactive Segment Buttons */}
        <div className="grid grid-cols-3 gap-1.5 pt-0.5">
          {BALANCED_PLATE_COMPONENTS.map((comp) => {
            const isSelected = selectedComponent === comp.code;
            return (
              <button
                key={comp.code}
                type="button"
                onClick={() => setSelectedComponent(comp.code)}
                className={`p-2 rounded-lg text-left text-xs transition-all cursor-pointer border ${
                  isSelected
                    ? 'bg-white shadow-2xs border-[#1E5E45] ring-1 ring-[#1E5E45]/20'
                    : 'bg-[#F6FAF7] border-transparent hover:bg-white text-[#4A6354]'
                }`}
              >
                <div className="flex items-center gap-1 font-semibold text-[11px] text-[#193A2A]">
                  {getIcon(comp.code)}
                  <span className="truncate">{comp.code === 'energy' ? '50% Energy' : comp.code === 'protective' ? '25% Greens' : '25% Protein'}</span>
                </div>
                <div className="text-[10px] text-[#5A7465] mt-0.5 line-clamp-1">
                  {language === 'RW' ? comp.nameRw : comp.nameEn}
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Component Detail Box */}
        {(() => {
          const activeComp = BALANCED_PLATE_COMPONENTS.find((c) => c.code === selectedComponent)!;
          return (
            <div className="bg-[#FAFDFB] rounded-lg p-2.5 border border-[#D5E7DC] text-xs">
              <span className="font-semibold text-[#1B4332] block">
                {language === 'RW' ? activeComp.nameRw : activeComp.nameEn}:
              </span>
              <p className="text-[11.5px] text-[#456353] mt-0.5">
                {language === 'RW' ? activeComp.examplesRw : activeComp.examplesEn}
              </p>
            </div>
          );
        })()}
      </div>

      {/* Practical Kitchen Tip */}
      <div className="flex items-start gap-2 text-xs text-[#2A533C]">
        <Info className="w-3.5 h-3.5 text-[#1E5E45] shrink-0 mt-0.5" />
        <span className="text-[11.5px] leading-relaxed">
          {language === 'RW'
            ? 'Inama y’Igikoni: Gutekera ibijumba rimwe n’ibishyimbo mu nkono imwe bizigama 35% by’amakara cyangwa gazi yo guteka.'
            : 'Kitchen Fuel Tip: Boiling sweet potatoes alongside beans in the same pot cuts charcoal consumption by 35% while keeping all nutrients intact.'}
        </span>
      </div>
    </div>
  );
};
