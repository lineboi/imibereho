import React, { useState, useEffect } from 'react';
import {
  ExternalLink,
  AlertTriangle,
  ArrowRight,
  User,
  Loader2,
} from 'lucide-react';
import {
  fetchDashboardFilters,
  fetchNationalVulnerability,
  fetchDistrictVulnerability,
  type DashboardFiltersResponse,
  type DistrictVulnerabilityResponse,
} from '../../services/api';
import type { DecisionMakerTab } from '../../types';

interface DistrictHeatmapViewProps {
  onNavigateTab: (tab: DecisionMakerTab) => void;
  onOpenProfile: () => void;
}

interface DistrictTile {
  districtCode: string;
  name: string;
  score: number;
  band: string;
}

export const DistrictHeatmapView: React.FC<DistrictHeatmapViewProps> = ({
  onNavigateTab,
  onOpenProfile,
}) => {
  const [filters, setFilters] = useState<DashboardFiltersResponse | null>(null);
  const [districts, setDistricts] = useState<DistrictTile[]>([]);
  const [selectedGeography, setSelectedGeography] = useState<string>('all');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('2026-10');
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [selectedDistrictCode, setSelectedDistrictCode] = useState<string>('gasabo');
  const [districtDetail, setDistrictDetail] = useState<DistrictVulnerabilityResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);

  // Load filter options on mount
  useEffect(() => {
    let mounted = true;
    fetchDashboardFilters()
      .then((res) => {
        if (mounted && res) {
          setFilters(res);
          const defaultGeo = res.geographies.find((g) => g.isDefault)?.code || 'all';
          const defaultPer = res.periods.find((p) => p.isDefault)?.code || '2026-10';
          const defaultGrp = res.householdGroups.find((h) => h.isDefault)?.code || 'all';
          setSelectedGeography(defaultGeo);
          setSelectedPeriod(defaultPer);
          setSelectedGroup(defaultGrp);
        }
      })
      .catch((err) => {
        console.warn('Failed to load filters:', err);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Load 30 districts from database
  useEffect(() => {
    let mounted = true;
    fetchNationalVulnerability()
      .then((res) => {
        if (!mounted || !res || !res.items) return;
        const list: DistrictTile[] = res.items.map((it: unknown) => {
          const raw = it as { districtCode?: string; code?: string; name: string; score: number; band: string };
          return {
            districtCode: raw.districtCode || raw.code || '',
            name: raw.name,
            score: Math.round(raw.score),
            band: raw.band,
          };
        });
        // Sort alphabetically by name to match 5x6 layout from screenshot
        list.sort((a, b) => a.name.localeCompare(b.name));
        setDistricts(list);
      })
      .catch((err) => {
        console.warn('Failed to load national vulnerability:', err);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Load selected district detail
  useEffect(() => {
    if (!selectedDistrictCode) return;
    let mounted = true;
    fetchDistrictVulnerability(selectedDistrictCode)
      .then((detail) => {
        if (mounted && detail) {
          setDistrictDetail(detail);
        }
      })
      .catch((err) => {
        console.warn('Failed to load district detail:', err);
      })
      .finally(() => {
        if (mounted) setIsLoadingDetail(false);
      });

    return () => {
      mounted = false;
    };
  }, [selectedDistrictCode]);

  // Color generator for tile based on score
  const getTileColor = (score: number) => {
    if (score >= 70) {
      return {
        bg: '#A0533C',
        text: 'text-white',
        border: 'border-[#8B422D]',
      };
    }
    if (score >= 60) {
      return {
        bg: '#EBD8BD',
        text: 'text-[#4A3B24]',
        border: 'border-[#D9C4A6]',
      };
    }
    if (score >= 40) {
      return {
        bg: '#BED4B5',
        text: 'text-[#1D3220]',
        border: 'border-[#A9C19F]',
      };
    }
    return {
      bg: '#96B688',
      text: 'text-[#142918]',
      border: 'border-[#82A374]',
    };
  };

  // Top 6 districts sorted by score descending
  const top6Districts = [...districts]
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);

  // Selected district components
  const incomeComp = districtDetail?.components.find((c) => c.code === 'incomeInstability')?.value ?? 50;
  const costComp = districtDetail?.components.find((c) => c.code === 'essentialCostPressure')?.value ?? 40;
  const bufferComp = districtDetail?.components.find((c) => c.code === 'lowBufferExposure')?.value ?? 50;
  const currentScore = districtDetail?.score ?? 46;
  const currentName = districtDetail?.name ?? 'Gasabo';

  return (
    <div className="flex-1 bg-[#FAF8F4] min-h-screen text-stone-900 pb-20">
      {/* Top Header / Breadcrumbs Bar */}
      <div className="border-b border-stone-200/80 bg-white/70 backdrop-blur-sm sticky top-0 z-10 px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-medium text-stone-500 uppercase tracking-wider">
          <span>Decision-maker workspace</span>
          <span>/</span>
          <span className="text-stone-900 font-semibold">Heatmap</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigateTab('data_methodology')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold tracking-wide uppercase text-[#123927] hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200/60 rounded-md transition-colors cursor-pointer"
          >
            <span>Data Methodology</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onOpenProfile}
            title="Household Account Profile"
            className="w-8 h-8 rounded-full bg-stone-100 hover:bg-stone-200 border border-stone-300 flex items-center justify-center text-stone-700 transition-colors cursor-pointer"
          >
            <User className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 pt-8 space-y-6">
        {/* Title and Subtitle */}
        <div>
          <h1 className="font-serif text-3xl md:text-4xl font-bold tracking-tight text-[#142d1f]">
            Districts in focus.
          </h1>
          <p className="text-stone-600 text-sm md:text-base mt-1.5">
            Explore a provisional vulnerability lens. Test index scores as illustrative, not definitive.
          </p>
        </div>

        {/* Notice Banner */}
        <div className="bg-[#F6EFE3] border border-[#E8DDCA] rounded-xl px-4 py-3 flex items-start sm:items-center gap-3 text-xs md:text-sm text-[#705834]">
          <div className="w-5 h-5 rounded-full bg-[#E5D5BA] flex items-center justify-center shrink-0 text-[#6B512C]">
            <AlertTriangle className="w-3 h-3" />
          </div>
          <span className="leading-relaxed">
            All figures, trends and vulnerability scores are synthetic demo values. Not official census or policy guidance.
          </span>
        </div>

        {/* Dynamic Filters Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Geography Dropdown */}
          <div className="bg-white rounded-xl p-3 border border-stone-200 shadow-xs">
            <label className="block text-[11px] font-bold tracking-wider uppercase text-stone-400 mb-1.5">
              Geography
            </label>
            <select
              value={selectedGeography}
              onChange={(e) => setSelectedGeography(e.target.value)}
              className="w-full bg-stone-50/70 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20 focus:border-[#123927]"
            >
              {filters?.geographies.map((geo) => (
                <option key={geo.code} value={geo.code}>
                  {geo.label}
                </option>
              )) || <option value="all">All 30 districts</option>}
            </select>
          </div>

          {/* Reference Period Dropdown */}
          <div className="bg-white rounded-xl p-3 border border-stone-200 shadow-xs">
            <label className="block text-[11px] font-bold tracking-wider uppercase text-stone-400 mb-1.5">
              Reference Period
            </label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="w-full bg-stone-50/70 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20 focus:border-[#123927]"
            >
              {filters?.periods.map((per) => (
                <option key={per.code} value={per.code}>
                  {per.label}
                </option>
              )) || <option value="2026-10">Demo month - October</option>}
            </select>
          </div>

          {/* Household Group Dropdown */}
          <div className="bg-white rounded-xl p-3 border border-stone-200 shadow-xs">
            <label className="block text-[11px] font-bold tracking-wider uppercase text-stone-400 mb-1.5">
              Household Group
            </label>
            <select
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
              className="w-full bg-stone-50/70 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20 focus:border-[#123927]"
            >
              {filters?.householdGroups.map((grp) => (
                <option key={grp.code} value={grp.code}>
                  {grp.label}
                </option>
              )) || <option value="all">All sample households</option>}
            </select>
          </div>
        </div>

        {/* Heatmap Main Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Heatmap Grid Card (7 cols) */}
          <div className="lg:col-span-8 bg-white rounded-2xl p-6 border border-stone-200 shadow-xs space-y-5">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-serif text-lg font-bold text-stone-900">
                  District vulnerability · Demo index
                </h2>
                <p className="text-xs text-stone-500 mt-0.5">
                  Index falls from 0 (lowest) to 100 (highest risk) based on 3 components
                </p>
              </div>
              <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider bg-stone-100 text-stone-700 rounded-md">
                30 of 30
              </span>
            </div>

            {/* 5 Rows x 6 Columns Grid */}
            {isLoading ? (
              <div className="py-20 flex flex-col items-center justify-center gap-2 text-stone-400">
                <Loader2 className="w-7 h-7 animate-spin text-[#123927]" />
                <span className="text-xs">Loading database records...</span>
              </div>
            ) : (
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2.5">
                {districts.map((d) => {
                  const colors = getTileColor(d.score);
                  const isSelected = selectedDistrictCode.toLowerCase() === d.districtCode.toLowerCase();

                  return (
                    <button
                      key={d.districtCode}
                      onClick={() => {
                        setSelectedDistrictCode(d.districtCode);
                        setIsLoadingDetail(true);
                      }}
                      className={`p-2.5 rounded-xl border text-left flex flex-col justify-between h-20 transition-all cursor-pointer ${
                        isSelected
                          ? 'ring-3 ring-[#123927] shadow-md scale-[1.02] z-1'
                          : 'hover:scale-[1.01] hover:shadow-xs'
                      }`}
                      style={{ backgroundColor: colors.bg }}
                    >
                      <span className={`text-xs font-semibold truncate ${colors.text}`}>
                        {d.name}
                      </span>
                      <span className={`text-lg font-bold font-serif ${colors.text}`}>
                        {d.score}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Legend underneath */}
            <div className="pt-2 border-t border-stone-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#96B688]" />
                  <span className="text-stone-600 text-[11px]">0-39</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#BED4B5]" />
                  <span className="text-stone-600 text-[11px]">40-59</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#EBD8BD]" />
                  <span className="text-stone-600 text-[11px]">60-69</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#A0533C]" />
                  <span className="text-stone-600 text-[11px]">70-100</span>
                </div>
              </div>
              <p className="text-[10px] text-stone-400 leading-tight max-w-sm">
                Provisional demo vulnerability = 40% income vulnerability 20% buffer capacity 40% essential costs. Not validated district ranking.
              </p>
            </div>
          </div>

          {/* Right Panel (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            {/* Selected District Card (Soft Green Tint) */}
            <div className="bg-[#EDF5EC] border border-[#D5E6D4] rounded-2xl p-6 space-y-4 shadow-xs">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                    Selected District
                  </span>
                  {isLoadingDetail && <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-800" />}
                </div>
                <div className="flex items-baseline justify-between mt-1">
                  <h3 className="font-serif text-2xl font-bold text-[#142d1f]">
                    {currentName}
                  </h3>
                  <div className="text-2xl font-serif font-bold text-[#142d1f]">
                    {currentScore} <span className="text-sm font-normal text-stone-500">/ 100</span>
                  </div>
                </div>
                <p className="text-xs text-stone-500 mt-0.5">
                  Provisional vulnerability index
                </p>
              </div>

              {/* Component breakdown inputs */}
              <div className="space-y-3 pt-2 border-t border-[#D5E6D4]/80">
                <span className="block text-[11px] font-bold text-stone-700">
                  Demo component inputs: (0-100)
                </span>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center text-stone-700">
                    <span>Income instability · 40%</span>
                    <strong className="font-mono">{incomeComp}</strong>
                  </div>
                  <div className="flex justify-between items-center text-stone-700">
                    <span>Essential cost pressure · 40%</span>
                    <strong className="font-mono">{costComp}</strong>
                  </div>
                  <div className="flex justify-between items-center text-stone-700">
                    <span>Low-buffer exposure · 20%</span>
                    <strong className="font-mono">{bufferComp}</strong>
                  </div>
                </div>
              </div>

              {/* Formula explanation box */}
              <div className="text-[11px] text-stone-600 bg-white/70 p-3 rounded-xl border border-[#D5E6D4] leading-relaxed">
                0.4 x {incomeComp} + 0.4 x {costComp} + 0.2 x {bufferComp} = {currentScore}. Weights and weights are illustrative for this prototype.
              </div>
            </div>

            {/* Compare with care card */}
            <div className="bg-white border border-stone-200 rounded-2xl p-5 space-y-3 shadow-xs">
              <h4 className="font-serif text-base font-bold text-stone-900">
                Compare with care.
              </h4>
              <p className="text-xs text-stone-600 leading-relaxed">
                Use this view to ask better questions, not to allocate resources. District averages can hide differences within communities.
              </p>
              <button
                onClick={() => onNavigateTab('data_methodology')}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#123927] hover:text-emerald-900 group cursor-pointer"
              >
                <span>Read the methodology</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>
        </div>

        {/* Warning Banner */}
        <div className="bg-[#FAF3EA] border border-[#EBDDCB] rounded-xl px-4 py-3 text-xs text-[#7A5B36] flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 text-[#8B643A]" />
          <span>
            Synthetic demo dataset only. No NISR/MINECOFIN endorsement. Indicators are indicative, not actual field census data.
          </span>
        </div>

        {/* Bottom Card: Highest Demo Scores */}
        <div className="bg-white rounded-2xl p-6 border border-stone-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-serif text-base font-bold text-stone-900">
              Highest demo scores
            </h3>
            <span className="text-[11px] text-stone-400 font-medium">
              Ranked top 6 of 30 districts
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {top6Districts.map((dist) => (
              <div
                key={dist.districtCode}
                onClick={() => {
                  setSelectedDistrictCode(dist.districtCode);
                  setIsLoadingDetail(true);
                }}
                className="p-3 rounded-xl bg-stone-50 border border-stone-200 hover:border-[#123927] hover:bg-emerald-50/40 transition-all cursor-pointer"
              >
                <div className="text-xs font-semibold text-stone-700 truncate">
                  {dist.name}
                </div>
                <div className="text-2xl font-serif font-bold text-stone-900 mt-1">
                  {dist.score}
                </div>
                <div className="text-[10px] text-stone-400 mt-0.5">
                  Score index / 100
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Page Footer */}
        <div className="pt-4 text-center text-xs text-stone-400">
          Imibereho · Concept blueprint · Transparent methodology and evidence base accessible by certification.
        </div>
      </div>
    </div>
  );
};
