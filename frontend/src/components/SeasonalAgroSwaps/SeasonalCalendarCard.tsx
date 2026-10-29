import React, { useState, useEffect } from 'react';
import type { Language } from '../../types';
import { AGRO_SWAPS_TRANSLATIONS } from '../../data/mockAgroSwapsData';
import { fetchHarvestCalendar, type HarvestCalendarResponse } from '../../services/api';
import { Calendar, Sun, CloudRain, Sprout } from 'lucide-react';

interface SeasonalCalendarCardProps {
  language: Language;
}

export const SeasonalCalendarCard: React.FC<SeasonalCalendarCardProps> = ({ language }) => {
  const t = AGRO_SWAPS_TRANSLATIONS[language];
  const [calendarApi, setCalendarApi] = useState<HarvestCalendarResponse | null>(null);

  useEffect(() => {
    fetchHarvestCalendar().then((res) => {
      if (res) setCalendarApi(res);
    });
  }, []);

  const seasons = [
    {
      code: 'A',
      nameEn: 'Season A (Umuhindo)',
      nameRw: 'Igihembwe cya A (Umuhindo)',
      monthsEn: 'Sept – Feb',
      monthsRw: 'Nzeli – Gashyantare',
      harvestEn: 'Root Tubers, Fresh Beans, Dodo Greens',
      harvestRw: 'Ibijumba, Imyumbati, Ibishyimbo, Dodo',
      isActive: true,
      badgeText: language === 'RW' ? 'Kiriho ubu' : 'Active Now',
    },
    {
      code: 'B',
      nameEn: 'Season B (Itumba)',
      nameRw: 'Igihembwe cya B (Itumba)',
      monthsEn: 'March – June',
      monthsRw: 'Werurwe – Kamena',
      harvestEn: 'Climbing Beans, Maize, Irish Potatoes',
      harvestRw: 'Ibishyimbo by’imishingiriro, Ibigori, Ibirayi',
      isActive: false,
      badgeText: language === 'RW' ? 'Imvura nyinshi' : 'Long Rains',
    },
    {
      code: 'C',
      nameEn: 'Season C (Icyi / Marshland)',
      nameRw: 'Igihembwe cya C (Icyi mu bishanga)',
      monthsEn: 'July – August',
      monthsRw: 'Nyakanga – Kanama',
      harvestEn: 'Marshland Vegetables, Sweet Corn, Cabbage',
      harvestRw: 'Imboga z’ibishanga, Amashu, Epinari',
      isActive: false,
      badgeText: language === 'RW' ? 'Ibishanga' : 'Irrigated',
    },
  ];

  return (
    <div className="bg-white rounded-2xl border border-[#E5DFD4] shadow-xs p-4 sm:p-5 flex flex-col gap-3.5">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#EBF4EE] text-[#1E5E45] flex items-center justify-center shrink-0 border border-[#CFE4D7]">
            <Calendar className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-normal text-[#123927]">
              {t.seasonalCalendarTitle}
            </h3>
            <p className="text-[12px] text-[#55695D] leading-tight">
              {language === 'RW'
                ? 'Igihembwe cy’umusaruro kigena ibiciro byo ku masoko mu turere twose.'
                : 'National crop calendar drives market prices across all 30 Rwandan districts.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="bg-[#E7F3EC] text-[#1E5E45] text-[11px] font-bold px-2 py-0.5 rounded-full border border-[#CCE2D4]">
            🇷🇼 MINAGRI Cycle
          </span>
        </div>
      </div>

      {/* Seasons Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
        {seasons.map((season) => {
          return (
            <div
              key={season.code}
              className={`p-3 rounded-xl border flex flex-col justify-between gap-2 transition-all ${
                season.isActive
                  ? 'bg-[#F2F8F4] border-[#2E7D5B] ring-1 ring-[#2E7D5B]/25'
                  : 'bg-[#FAF8F4] border-[#E8E2D7] opacity-80'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#1A4230]">
                    {language === 'RW' ? season.nameRw : season.nameEn}
                  </span>
                  {season.isActive ? (
                    <span className="bg-[#1E5E45] text-white text-[10px] font-bold px-1.5 py-0.2 rounded-sm shrink-0">
                      {season.badgeText}
                    </span>
                  ) : (
                    <span className="text-[10px] text-[#718278]">{season.badgeText}</span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 text-xs text-[#52665A] mb-1.5">
                  {season.isActive ? (
                    <CloudRain className="w-3.5 h-3.5 text-[#1E5E45]" />
                  ) : season.code === 'C' ? (
                    <Sun className="w-3.5 h-3.5 text-[#D97706]" />
                  ) : (
                    <Sprout className="w-3.5 h-3.5 text-[#3C644E]" />
                  )}
                  <span className="font-medium">
                    {language === 'RW' ? season.monthsRw : season.monthsEn}
                  </span>
                </div>

                <p className="text-[11.5px] text-[#334E3F] leading-tight">
                  {language === 'RW' ? season.harvestRw : season.harvestEn}
                </p>
              </div>

              {season.isActive && (
                <div className="pt-2 border-t border-[#D5E7DC] text-[10.5px] text-[#24543B] font-medium leading-tight">
                  💡 {language === 'RW'
                    ? 'Ibijumba n’imboga bihendutse cyane muri iki gihe ku masoko!'
                    : 'Sweet potatoes & fresh greens are at peak volume and lowest price now!'}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {/* Harvest Highlights from NISR SAS 2025 */}
      {calendarApi?.harvestHighlights && calendarApi.harvestHighlights.length > 0 && (
        <div className="bg-[#FAF8F3] border border-[#E8E2D6] rounded-xl p-3 flex flex-col gap-1.5 text-xs text-[#3E5547]">
          <span className="font-semibold text-[11px] uppercase tracking-wider text-[#1E5E45]">
            {language === 'RW' ? 'Umusaruro w’Igihembwe cya A (NISR SAS 2025)' : 'Official Season A Production Highlights (NISR SAS 2025)'}
          </span>
          <div className="flex flex-col gap-1">
            {calendarApi.harvestHighlights.map((hl, i) => (
              <span key={i} className="text-[11.5px] text-[#4F6456]">
                • {hl}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
