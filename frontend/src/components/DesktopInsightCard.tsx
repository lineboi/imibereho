import React from 'react';
import { HeroIllustration } from './HeroIllustration';
import type { HouseholdProfile, Language } from '../types';
import { PieChart, MapPin, Sparkles, HeartHandshake } from 'lucide-react';

interface DesktopInsightCardProps {
  profile: HouseholdProfile;
  language: Language;
}

export const DesktopInsightCard: React.FC<DesktopInsightCardProps> = ({
  profile,
  language,
}) => {
  const numericIncome = parseInt(profile.monthlyIncome.replace(/[^0-9]/g, ''), 10) || 180000;
  const householdCount = parseInt(profile.householdSize, 10) || 4;
  
  // Baseline calculations
  const baselineCost = Math.round(householdCount * 36000 + 40000);
  const foodEst = Math.round(baselineCost * 0.48);
  const shelterEst = Math.round(baselineCost * 0.32);
  const healthTransEst = baselineCost - foodEst - shelterEst;
  const buffer = numericIncome - baselineCost;

  return (
    <div className="flex flex-col gap-5">
      {/* Scenic Illustration with Frame */}
      <div className="relative">
        <HeroIllustration district={profile.district} className="w-full shadow-md" />
        
        {/* Floating location badge */}
        <div className="absolute top-3 left-3 bg-[#133C2C]/85 backdrop-blur-md text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm border border-white/20">
          <MapPin className="w-3.5 h-3.5 text-[#A3E0C1]" />
          <span className="font-medium tracking-wide">
            {profile.district || 'Rwanda'} Lens
          </span>
        </div>
      </div>

      {/* Dynamic Live Perspective Card */}
      <div className="bg-white rounded-2xl p-5 border border-[#E3DED4] shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#ECE7DE]">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#1E5E45]">
            <PieChart className="w-4 h-4" />
            <span>
              {language === 'RW' ? "Igereranyo ry'ingengo y'imari" : 'Live Household Perspective'}
            </span>
          </div>
          <span className="text-[11px] font-semibold bg-[#EAF2ED] text-[#1E5E45] px-2 py-0.5 rounded-md">
            {profile.householdSize}
          </span>
        </div>

        {/* Breakdown bars */}
        <div className="space-y-2.5">
          <div>
            <div className="flex justify-between text-xs font-medium text-[#2C3E34] mb-1">
              <span>{language === 'RW' ? 'Ibiribwa & Isoko' : 'Food & Staples (est.)'}</span>
              <span className="font-semibold text-[#183628]">{foodEst.toLocaleString()} RWF</span>
            </div>
            <div className="h-2 w-full bg-[#EFECE4] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#2A6E50] rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (foodEst / numericIncome) * 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-[#2C3E34] mb-1">
              <span>{language === 'RW' ? 'Ubucumbi & Ingufu' : 'Housing & Utilities (est.)'}</span>
              <span className="font-semibold text-[#183628]">{shelterEst.toLocaleString()} RWF</span>
            </div>
            <div className="h-2 w-full bg-[#EFECE4] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#528F72] rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (shelterEst / numericIncome) * 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-[#2C3E34] mb-1">
              <span>{language === 'RW' ? 'Ubuzima & Ingendo' : 'Health & Transport (est.)'}</span>
              <span className="font-semibold text-[#183628]">{healthTransEst.toLocaleString()} RWF</span>
            </div>
            <div className="h-2 w-full bg-[#EFECE4] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#82B39B] rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (healthTransEst / numericIncome) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Live Cushion Calculation */}
        <div className="pt-3 border-t border-[#ECE7DE] flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-[#5A6E62]">
            <Sparkles className="w-3.5 h-3.5 text-[#1E5E45]" />
            <span>{language === 'RW' ? 'Amafaranga asaguka (igereranyo)' : 'Estimated Net Cushion'}</span>
          </div>
          <div className={`font-bold text-sm ${buffer >= 0 ? 'text-[#1E5E45]' : 'text-amber-700'}`}>
            {buffer >= 0 ? `+${buffer.toLocaleString()} RWF` : `${buffer.toLocaleString()} RWF`}
          </div>
        </div>

        {/* Household Financial Guidance Tip */}
        <div className="bg-[#FAF8F3] rounded-xl p-3 border border-[#EBE6DB] flex items-start gap-2.5 text-[11px] text-[#63756A] leading-relaxed">
          <HeartHandshake className="w-4 h-4 text-[#205A44] shrink-0 mt-0.5" />
          <span>
            {language === 'RW'
              ? 'Iyi mibare igufasha gupanga ingengo y’imari y’urugo rwawe no kubika ubwizigame bw’ejo hazaza.'
              : 'Estimates grounded in local district living costs to help you build your household savings buffer.'}
          </span>
        </div>
      </div>
    </div>
  );
};
