import React, { useState, useEffect } from 'react';
import {
  ExternalLink,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Building2,
  Users,
  Wallet,
  ShieldAlert,
  Loader2,
  User,
} from 'lucide-react';
import {
  fetchDashboardFilters,
  fetchDashboardOverview,
  type DashboardFiltersResponse,
  type DashboardOverviewResponse,
} from '../../services/api';
import type { DecisionMakerTab } from '../../types';

interface MacroOverviewViewProps {
  onNavigateTab: (tab: DecisionMakerTab) => void;
  onOpenProfile: () => void;
}

export const MacroOverviewView: React.FC<MacroOverviewViewProps> = ({
  onNavigateTab,
  onOpenProfile,
}) => {
  const [filters, setFilters] = useState<DashboardFiltersResponse | null>(null);
  const [overview, setOverview] = useState<DashboardOverviewResponse | null>(null);
  const [selectedGeography, setSelectedGeography] = useState<string>('all');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('2026-10');
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
        console.warn('Failed to load dashboard filters:', err);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Fetch overview data when filters change
  useEffect(() => {
    let mounted = true;
    fetchDashboardOverview({
      geography: selectedGeography,
      period: selectedPeriod,
      householdGroup: selectedGroup,
      topN: 2,
    })
      .then((data) => {
        if (!mounted) return;
        if (data) {
          setOverview(data);
          setError(null);
        } else {
          setError('Unable to load overview data from the live service.');
        }
      })
      .catch((err) => {
        if (!mounted) return;
        console.error('Error fetching dashboard overview:', err);
        setError('An error occurred while fetching live dashboard metrics.');
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [selectedGeography, selectedPeriod, selectedGroup]);

  // Month formatter helper (e.g., "2026-05" -> "May")
  const formatMonthName = (monthStr: string) => {
    try {
      const parts = monthStr.split('-');
      if (parts.length >= 2) {
        const monthNum = parseInt(parts[1], 10) - 1;
        const date = new Date(2026, monthNum, 1);
        return date.toLocaleString('en-US', { month: 'short' });
      }
      return monthStr;
    } catch {
      return monthStr;
    }
  };

  return (
    <div className="flex-1 bg-[#FAF8F4] min-h-screen text-stone-900 pb-20">
      {/* Top Header / Breadcrumbs Bar */}
      <div className="border-b border-stone-200/80 bg-white/70 backdrop-blur-sm sticky top-0 z-10 px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-medium text-stone-500 uppercase tracking-wider">
          <span>Decision-maker workspace</span>
          <span>/</span>
          <span className="text-stone-900 font-semibold">Overview</span>
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
            A clearer view of household resilience.
          </h1>
          <p className="text-stone-600 text-sm md:text-base mt-1.5">
            Explore household pressures, compare districts and test transparent assumptions.
          </p>
        </div>

        {/* Notice Banner */}
        <div className="bg-[#F6EFE3] border border-[#E8DDCA] rounded-xl px-4 py-3 flex items-start sm:items-center gap-3 text-xs md:text-sm text-[#705834]">
          <div className="w-5 h-5 rounded-full bg-[#E5D5BA] flex items-center justify-center shrink-0 text-[#6B512C]">
            <AlertTriangle className="w-3 h-3" />
          </div>
          <span className="leading-relaxed">
            All figures, benchmarks and vulnerability scores are synthetic demo values. Not official census data or policy guidance.
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
              onChange={(e) => {
                setSelectedGeography(e.target.value);
                setIsLoading(true);
              }}
              className="w-full bg-stone-50/70 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20 focus:border-[#123927]"
            >
              {filters?.geographies.map((geo) => (
                <option key={geo.code} value={geo.code}>
                  {geo.label}
                </option>
              )) || <option value="all">30 districts</option>}
            </select>
          </div>

          {/* Reference Period Dropdown */}
          <div className="bg-white rounded-xl p-3 border border-stone-200 shadow-xs">
            <label className="block text-[11px] font-bold tracking-wider uppercase text-stone-400 mb-1.5">
              Reference Period
            </label>
            <select
              value={selectedPeriod}
              onChange={(e) => {
                setSelectedPeriod(e.target.value);
                setIsLoading(true);
              }}
              className="w-full bg-stone-50/70 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20 focus:border-[#123927]"
            >
              {filters?.periods.map((per) => (
                <option key={per.code} value={per.code}>
                  {per.label}
                </option>
              )) || <option value="2026-10">Demo month · October</option>}
            </select>
          </div>

          {/* Household Group Dropdown */}
          <div className="bg-white rounded-xl p-3 border border-stone-200 shadow-xs">
            <label className="block text-[11px] font-bold tracking-wider uppercase text-stone-400 mb-1.5">
              Household Group
            </label>
            <select
              value={selectedGroup}
              onChange={(e) => {
                setSelectedGroup(e.target.value);
                setIsLoading(true);
              }}
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

        {/* Loading State or Error */}
        {isLoading && !overview && (
          <div className="bg-white rounded-2xl p-12 border border-stone-200 flex flex-col items-center justify-center gap-3 text-stone-500">
            <Loader2 className="w-7 h-7 animate-spin text-[#123927]" />
            <p className="text-sm font-medium">Loading live macroeconomic indicators from database...</p>
          </div>
        )}

        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-rose-800 text-sm">
            {error}
          </div>
        )}

        {/* Main Content when Overview is Available */}
        {overview && (
          <div className="space-y-6">
            {/* 4 KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* KPI 1: Synthetic Sample */}
              <div className="bg-white rounded-xl p-5 border border-stone-200/90 shadow-xs">
                <div className="flex items-center justify-between text-stone-400 mb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider">
                    Synthetic Sample
                  </span>
                  <Users className="w-4 h-4 text-stone-400" />
                </div>
                <div className="text-2xl lg:text-3xl font-bold font-serif text-stone-900">
                  {overview.kpis.sampleSize.toLocaleString()}
                </div>
                <div className="text-xs text-stone-500 mt-1 font-sans">
                  Diverse household income profiles
                </div>
              </div>

              {/* KPI 2: Reference Monthly Income */}
              <div className="bg-white rounded-xl p-5 border border-stone-200/90 shadow-xs">
                <div className="flex items-center justify-between text-stone-400 mb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider">
                    Reference Monthly Income
                  </span>
                  <Wallet className="w-4 h-4 text-stone-400" />
                </div>
                <div className="text-2xl lg:text-3xl font-bold font-serif text-stone-900">
                  {overview.kpis.referenceHousehold.monthlyIncome.toLocaleString()} RWF
                </div>
                <div className="text-xs text-stone-500 mt-1 font-sans">
                  Equates household of {overview.kpis.referenceHousehold.householdSize}
                </div>
              </div>

              {/* KPI 3: Average Essentials to Income */}
              <div className="bg-white rounded-xl p-5 border border-stone-200/90 shadow-xs">
                <div className="flex items-center justify-between text-stone-400 mb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider">
                    Average Essentials to Income
                  </span>
                  <TrendingUp className="w-4 h-4 text-stone-400" />
                </div>
                <div className="text-2xl lg:text-3xl font-bold font-serif text-stone-900">
                  {(overview.kpis.essentialsToIncomeRatio * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-stone-500 mt-1 font-sans">
                  {overview.kpis.referenceHousehold.monthlyEssentials.toLocaleString()} /{' '}
                  {overview.kpis.referenceHousehold.monthlyIncome.toLocaleString()} RWF
                </div>
              </div>

              {/* KPI 4: Sample with Zero Cushion */}
              <div className="bg-white rounded-xl p-5 border border-stone-200/90 shadow-xs">
                <div className="flex items-center justify-between text-stone-400 mb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider">
                    Sample with Zero Cushion
                  </span>
                  <ShieldAlert className="w-4 h-4 text-stone-400" />
                </div>
                <div className="text-2xl lg:text-3xl font-bold font-serif text-stone-900">
                  {(overview.kpis.shockDeficit.share * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-stone-500 mt-1 font-sans">
                  {overview.kpis.shockDeficit.householdsInDeficit.toLocaleString()} of{' '}
                  {overview.kpis.sampleSize.toLocaleString()} reference households
                </div>
              </div>
            </div>

            {/* Middle Section: Chart & Income Sources */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {/* Monthly Trend Chart (7 cols) */}
              <div className="lg:col-span-7 bg-white rounded-2xl p-6 border border-stone-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="font-serif text-lg font-bold text-stone-900">
                        Less room between income and essentials
                      </h2>
                      <p className="text-xs text-stone-500 mt-0.5">
                        Reference Household · Synthetic monthly series · RWF thousands
                      </p>
                    </div>
                    <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-md">
                      Synthetic series
                    </span>
                  </div>

                  {/* Chart Legend */}
                  <div className="flex items-center gap-5 mt-4 text-xs text-stone-600">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#123927]" />
                      <span>Essentials expenditure</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-4 h-0.5 bg-[#B86835]" />
                      <span>
                        Income: {overview.essentialsTrend.incomeReference.toLocaleString()} RWF
                      </span>
                    </div>
                  </div>

                  {/* Monthly Bars Chart */}
                  <div className="mt-8 pt-4 pb-2 relative">
                    {/* Reference Line for Income */}
                    {(() => {
                      const points = overview.essentialsTrend.points;
                      const maxVal = Math.max(
                        overview.essentialsTrend.incomeReference * 1.15,
                        ...points.map((p) => p.essentials * 1.25),
                        200000
                      );
                      const incomeRatio = Math.min(
                        0.95,
                        overview.essentialsTrend.incomeReference / maxVal
                      );
                      const incomeLineBottomPct = (incomeRatio * 100).toFixed(1);

                      return (
                        <>
                          {/* Reference guideline */}
                          <div
                            className="absolute left-0 right-0 border-b border-dashed border-[#B86835] z-0 flex items-center justify-end"
                            style={{ bottom: `calc(${incomeLineBottomPct}% + 28px)` }}
                          >
                            <span className="text-[10px] font-semibold text-[#B86835] bg-white px-1 -translate-y-2">
                              {Math.round(overview.essentialsTrend.incomeReference / 1000)}k RWF
                            </span>
                          </div>

                          {/* Bars Grid */}
                          <div className="h-52 flex items-end justify-between gap-3 sm:gap-6 pt-6 relative z-1">
                            {points.map((pt, idx) => {
                              const isLast = idx === points.length - 1;
                              const heightPct = Math.min(
                                100,
                                Math.max(15, (pt.essentials / maxVal) * 100)
                              );

                              return (
                                <div
                                  key={pt.month}
                                  className="flex-1 flex flex-col items-center justify-end h-full group"
                                >
                                  {/* Value on top of bar */}
                                  <span className="text-[11px] font-semibold text-stone-700 mb-1.5 tracking-tight group-hover:text-stone-900">
                                    {Math.round(pt.essentials / 1000)}k
                                  </span>

                                  {/* Bar pill */}
                                  <div
                                    className="w-full max-w-[48px] rounded-t-md transition-all duration-300 shadow-xs"
                                    style={{
                                      height: `${heightPct}%`,
                                      backgroundColor: isLast ? '#123927' : '#A4C39B',
                                    }}
                                    title={`${formatMonthName(pt.month)}: ${pt.essentials.toLocaleString()} RWF`}
                                  />

                                  {/* Month Label */}
                                  <span
                                    className={`text-xs mt-2.5 font-medium ${
                                      isLast ? 'text-stone-900 font-bold' : 'text-stone-500'
                                    }`}
                                  >
                                    {formatMonthName(pt.month)}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </>
                      );
                    })()}
                  </div>
                </div>

                {/* Trend Note */}
                <div className="pt-4 mt-4 border-t border-stone-100 text-xs text-stone-500 leading-relaxed">
                  {(() => {
                    const pts = overview.essentialsTrend.points;
                    const first = pts[0]?.essentials ?? 0;
                    const last = pts[pts.length - 1]?.essentials ?? 0;
                    const income = overview.essentialsTrend.incomeReference;
                    return `Demo income stays at ${income.toLocaleString()} RWF; essentials range from ${first.toLocaleString()} to ${last.toLocaleString()} RWF. This is our primary navigation trend.`;
                  })()}
                </div>
              </div>

              {/* Income Sources Panel (5 cols) */}
              <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-stone-200 shadow-xs flex flex-col justify-between">
                <div>
                  <h2 className="font-serif text-lg font-bold text-stone-900">
                    What sits behind the sample?
                  </h2>
                  <p className="text-xs text-stone-500 mt-0.5">
                    Primary income source · Synthetic, most Kigali
                  </p>

                  <div className="mt-6 space-y-5">
                    {overview.incomeSources.map((source) => {
                      const sharePct = Math.round(source.share * 100);
                      return (
                        <div key={source.code} className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-medium text-stone-700">{source.label}</span>
                            <span className="font-semibold text-stone-900">
                              {source.households.toLocaleString()} · {sharePct}%
                            </span>
                          </div>
                          <div className="w-full h-2.5 bg-stone-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[#123927] rounded-full transition-all duration-500"
                              style={{ width: `${sharePct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="pt-4 mt-6 border-t border-stone-100 text-xs text-stone-400 leading-relaxed">
                  Civil servant servants including for instance not conditioned. Farm crops baseline.
                </div>
              </div>
            </div>

            {/* Bottom Row: Callout Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Callout 1: Policy Gap */}
              <div className="bg-[#EEF5EE] border border-[#D5E6D5] rounded-2xl p-6 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-emerald-800 mb-2">
                    <Building2 className="w-4 h-4 text-emerald-800" />
                    <h3 className="font-serif text-base font-bold text-[#142d1f]">
                      Follow the gap, not just the average.
                    </h3>
                  </div>
                  <p className="text-xs sm:text-sm text-stone-700 leading-relaxed">
                    The reference household has {overview.insight.baselineMonthlyBalance.toLocaleString()} RWF left in its baseline plan, but a {overview.insight.incomeReductionPct}% income reduction creates a {overview.insight.shockMonthlyGap.toLocaleString()} RWF monthly gap.
                  </p>
                </div>

                <div className="pt-4 mt-4">
                  <button
                    onClick={() => onNavigateTab('policy_simulator')}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-[#123927] hover:text-emerald-900 group cursor-pointer"
                  >
                    <span>Open the policy simulator</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>

              {/* Callout 2: Top Vulnerable Districts */}
              <div className="bg-white border border-stone-200 rounded-2xl p-6 flex flex-col justify-between">
                <div>
                  <h3 className="font-serif text-base font-bold text-stone-900 mb-3">
                    Where would you look next?
                  </h3>

                  <div className="space-y-2.5">
                    {overview.topDistricts.map((dist) => (
                      <div
                        key={dist.code}
                        className="flex items-center justify-between text-xs py-1 border-b border-stone-100 last:border-b-0"
                      >
                        <span className="text-stone-700 font-medium">
                          {dist.name} · Demo vulnerability index
                        </span>
                        <span className="font-bold text-stone-900 font-mono">
                          {dist.score} / 100
                        </span>
                      </div>
                    ))}
                  </div>

                  <p className="text-[11px] text-stone-400 mt-3 leading-relaxed">
                    A quick indicator preview only. The index looks for income variance and does not describe actual poverty normality.
                  </p>
                </div>

                <div className="pt-4 mt-4 border-t border-stone-100">
                  <button
                    onClick={() => onNavigateTab('district_heatmap')}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-[#123927] hover:text-emerald-900 group cursor-pointer"
                  >
                    <span>Explore the district heatmap</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>
            </div>

            {/* Bottom Footer Note */}
            <div className="pt-4 text-center text-xs text-stone-400">
              Imibereho · Concept blueprint · Transparent methodology and evidence base accessible by certification.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
