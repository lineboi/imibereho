import React, { useState, useEffect } from 'react';
import type { Language, NavTab } from '../../types';
import type { AgroSwapItem } from '../../data/mockAgroSwapsData';
import { AGRO_SWAPS_TRANSLATIONS } from '../../data/mockAgroSwapsData';
import { calculateAgroSavingsProjection, type AgroSavingsProjectionResponse } from '../../services/api';
import { Calculator, ArrowRight, Droplets, Bus, HeartPulse, CheckCircle2 } from 'lucide-react';

interface MonthlySavingsProjectorProps {
  selectedSwap: AgroSwapItem;
  language: Language;
  onNavigateTab?: (tab: NavTab) => void;
}

export const MonthlySavingsProjector: React.FC<MonthlySavingsProjectorProps> = ({
  selectedSwap,
  language,
  onNavigateTab,
}) => {
  const t = AGRO_SWAPS_TRANSLATIONS[language];
  const [mealsPerWeek, setMealsPerWeek] = useState<number>(3);
  const [loggedNotice, setLoggedNotice] = useState<boolean>(false);
  const [apiSavings, setApiSavings] = useState<AgroSavingsProjectionResponse | null>(null);

  useEffect(() => {
    calculateAgroSavingsProjection(selectedSwap.id, mealsPerWeek, 4).then((res) => {
      if (res) setApiSavings(res);
    });
  }, [selectedSwap.id, mealsPerWeek]);

  // 4.33 weeks per average month (uses backend if loaded)
  const monthlySavings = apiSavings ? apiSavings.monthlyProjectedSavings : Math.round(selectedSwap.difference * mealsPerWeek * 4.33);

  const presets = [1, 2, 3, 5, 7];

  const handleSimulateInResilience = () => {
    if (onNavigateTab) {
      onNavigateTab('resilience');
    }
  };

  const handleLogToTracker = () => {
    setLoggedNotice(true);
    setTimeout(() => setLoggedNotice(false), 3000);
  };

  return (
    <div className="bg-[#FAF8F3] rounded-2xl border border-[#E3DDCF] p-4 sm:p-5 flex flex-col gap-4 shadow-2xs">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#E5ECE7] text-[#1E5E45] flex items-center justify-center shrink-0 border border-[#CEE0D4]">
            <Calculator className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-normal text-[#143B2A]">
              {t.calculatorTitle}
            </h3>
            <p className="text-[12px] text-[#55695D] leading-tight">
              {t.calculatorSub}
            </p>
          </div>
        </div>
      </div>

      {/* Slider & Presets */}
      <div className="flex flex-col gap-2.5 bg-white p-3.5 rounded-xl border border-[#EBE5DB]">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-[#2E4336]">{t.mealsPerWeekLabel}</span>
          <span className="font-bold text-[#1E5E45] bg-[#E8F2EC] px-2 py-0.5 rounded-md text-xs">
            {mealsPerWeek} {language === 'RW' ? 'ku cyumweru' : 'meals / week'}
          </span>
        </div>

        {/* Range Slider */}
        <input
          type="range"
          min="1"
          max="7"
          step="1"
          value={mealsPerWeek}
          onChange={(e) => setMealsPerWeek(Number(e.target.value))}
          className="w-full accent-[#1E5E45] cursor-pointer h-2 bg-[#E9E4DB] rounded-lg"
          aria-label="Meals per week slider"
        />

        {/* Quick selection chips */}
        <div className="flex items-center justify-between gap-1 pt-1">
          {presets.map((count) => {
            const isSelected = mealsPerWeek === count;
            return (
              <button
                key={count}
                type="button"
                onClick={() => setMealsPerWeek(count)}
                className={`flex-1 py-1 text-xs rounded-lg font-medium transition-colors cursor-pointer text-center ${
                  isSelected
                    ? 'bg-[#1E5E45] text-white font-semibold'
                    : 'bg-[#F4EFE6] text-[#55695D] hover:bg-[#EAE3D6]'
                }`}
              >
                {count}x
              </button>
            );
          })}
        </div>
      </div>

      {/* Output Projection Display */}
      <div className="bg-[#123627] text-white rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#98D8B6] block">
            {t.projectedMonthlySavings}
          </span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-white tabular-nums">
              +{monthlySavings.toLocaleString()} RWF
            </span>
            <span className="text-xs text-[#BEDCD0]">/ {language === 'RW' ? 'kwezi' : 'month'}</span>
            {apiSavings && (
              <span className="text-[10px] bg-[#1E5E45] text-[#A6E3C3] px-2 py-0.5 rounded border border-[#2D7354] font-mono shrink-0 ml-1">
                Live API 200 OK
              </span>
            )}
          </div>
          <span className="text-[11px] text-[#A6CDBE] block mt-0.5">
            ({selectedSwap.difference.toLocaleString()} RWF {t.perMealSavings} × {mealsPerWeek}x × 4.3 wks)
          </span>
        </div>

        {/* Action button to test in simulator */}
        <button
          type="button"
          onClick={handleSimulateInResilience}
          className="self-stretch sm:self-auto bg-[#2E7D5B] hover:bg-[#256B4E] text-white text-xs font-semibold px-3.5 py-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-colors cursor-pointer shrink-0 shadow-2xs"
        >
          <span>{language === 'RW' ? 'Gupima mu Igereranya' : 'Test in Simulator'}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Real-life Rwandan Purchasing Power Comparisons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
        <div className="bg-white p-2.5 rounded-xl border border-[#EAE4D8] flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#E6F4FF] text-[#0284C7] flex items-center justify-center shrink-0">
            <Droplets className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-semibold text-[#1F2937] block text-[11.5px]">WASAC Water</span>
            <span className="text-[10.5px] text-[#6B7280] leading-tight block">
              {language === 'RW' ? 'Yishyura amazi y’ukwezi' : 'Covers ~2-3 weeks tap water'}
            </span>
          </div>
        </div>

        <div className="bg-white p-2.5 rounded-xl border border-[#EAE4D8] flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#FEF3C7] text-[#D97706] flex items-center justify-center shrink-0">
            <Bus className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-semibold text-[#1F2937] block text-[11.5px]">Public Transit</span>
            <span className="text-[10.5px] text-[#6B7280] leading-tight block">
              {language === 'RW' ? 'Ingendo 8 za bisi' : '8 Kigali city bus rides'}
            </span>
          </div>
        </div>

        <div className="bg-white p-2.5 rounded-xl border border-[#EAE4D8] flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#FEE2E2] text-[#DC2626] flex items-center justify-center shrink-0">
            <HeartPulse className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-semibold text-[#1F2937] block text-[11.5px]">Health Buffer</span>
            <span className="text-[10.5px] text-[#6B7280] leading-tight block">
              {language === 'RW' ? 'Umutekano mu buzima' : 'Bolsters emergency buffer'}
            </span>
          </div>
        </div>
      </div>

      {/* Log into Tracker button */}
      <div className="flex items-center justify-between pt-1">
        <button
          type="button"
          onClick={handleLogToTracker}
          className="text-xs font-semibold text-[#1E5E45] hover:text-[#144230] flex items-center gap-1.5 cursor-pointer"
        >
          {loggedNotice ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-[#1E5E45]" />
              <span>{language === 'RW' ? 'Byanditswe mu ibarura!' : 'Saved to daily tracker!'}</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4 text-[#7A8C81]" />
              <span>{t.addToTrackerBtn}</span>
            </>
          )}
        </button>

        <span className="text-[11px] text-[#7E8E84]">
          {language === 'RW' ? 'Ubwizigame bubarwa ku kwezi' : 'Calculated over 30 days'}
        </span>
      </div>
    </div>
  );
};
