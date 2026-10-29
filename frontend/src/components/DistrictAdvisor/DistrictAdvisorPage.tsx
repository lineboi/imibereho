import React, { useState, useEffect } from 'react';
import type { Language, NavTab } from '../../types';
import {
  ADVISOR_TRANSLATIONS,
  COMPARISON_PRESETS,
  getDistrictBenchmark,
  formatHouseholdSize,
  type ComparisonMode,
  type StressTestScenario,
} from '../../data/mockAdvisorData';
import {
  fetchBudgetBenchmark,
  fetchDistrictVulnerability,
  fetchDistrictComparison,
  calculateStressTest,
  fetchDistrictFinancialInclusion,
  type BudgetBenchmarkData,
  type DistrictVulnerabilityResponse,
  type DistrictComparisonResponse,
  type StressTestResponse,
  type DistrictFinancialInclusionItem,
} from '../../services/api';
import { PolicyScenarioModal } from '../PolicyScenarioModal';
import { SearchableDistrictSelect } from './SearchableDistrictSelect';
import { DistrictComparisonCard } from './DistrictComparisonCard';
import { MyPlanComparisonCard } from './MyPlanComparisonCard';
import { WholePictureCard } from './WholePictureCard';
import { SimulatorPreviewModal } from './SimulatorPreviewModal';
import { IncomeRunwayCard } from './IncomeRunwayCard';
import { BudgetShareVisualizer } from './BudgetShareVisualizer';
import { MarketBasketDrawer } from './MarketBasketDrawer';
import { SeasonalHarvestCard } from './SeasonalHarvestCard';
import { StressTestChips } from './StressTestChips';
import { BottomNav } from '../DailyTracker/BottomNav';
import {
  ArrowLeftRight,
  Info,
  ArrowRight,
  Layers,
  Users,
} from 'lucide-react';

interface DistrictAdvisorPageProps {
  language: Language;
  onNavigateHome: () => void;
  defaultDistrict?: string;
  defaultHouseholdSize?: string;
  monthlyIncome?: string;
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const DistrictAdvisorPage: React.FC<DistrictAdvisorPageProps> = ({
  language,
  onNavigateHome,
  defaultDistrict = 'Gasabo',
  defaultHouseholdSize = '4',
  monthlyIncome,
  activeTab,
  onTabChange,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];

  // Mode: Compare 2 districts (requested by user) vs My Plan vs Benchmark (original screenshot)
  const [mode, setMode] = useState<ComparisonMode>('district_vs_district');

  // District A (Baseline, defaults to Gasabo or user profile)
  const [districtAId, setDistrictAId] = useState<string>(
    defaultDistrict.toLowerCase() || 'gasabo'
  );

  // District B (Comparison target, defaults to Musanze as requested!)
  const [districtBId, setDistrictBId] = useState<string>('musanze');

  // Household size entered via numeric input box (defaults to 4)
  const initialSize = parseInt(defaultHouseholdSize, 10) || 4;
  const [householdSizeNumber, setHouseholdSizeNumber] = useState<number>(initialSize);

  // Stepper handlers
  const incrementHousehold = () => {
    setHouseholdSizeNumber((prev) => Math.min(25, prev + 1));
  };

  const decrementHousehold = () => {
    setHouseholdSizeNumber((prev) => Math.max(1, prev - 1));
  };

  const handleHouseholdInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) {
      setHouseholdSizeNumber(1);
    } else {
      setHouseholdSizeNumber(Math.max(1, Math.min(25, val)));
    }
  };

  const formattedHouseholdSize = formatHouseholdSize(householdSizeNumber, language);

  const parsedIncome = parseInt((monthlyIncome || '').replace(/[^0-9]/g, ''), 10) || 180000;
  // Household monthly income for Buffer Runway Feasibility
  const [householdIncome, setHouseholdIncome] = useState<number>(parsedIncome);

  // Active Stress-Test Scenario
  const [stressScenario, setStressScenario] = useState<StressTestScenario>('none');

  // Simulator Modal State
  const [simulatorModalOpen, setSimulatorModalOpen] = useState(false);

  // Backend live connection state
  const [backendBenchmarkA, setBackendBenchmarkA] = useState<BudgetBenchmarkData | null>(null);
  const [backendBenchmarkB, setBackendBenchmarkB] = useState<BudgetBenchmarkData | null>(null);
  const [vulnerabilityA, setVulnerabilityA] = useState<DistrictVulnerabilityResponse | null>(null);
  const [districtComparisonApi, setDistrictComparisonApi] = useState<DistrictComparisonResponse | null>(null);
  const [stressTestApi, setStressTestApi] = useState<StressTestResponse | null>(null);
  const [financialInclusionA, setFinancialInclusionA] = useState<DistrictFinancialInclusionItem | null>(null);
  const [policyModalOpen, setPolicyModalOpen] = useState(false);

  // Live call to GET /api/v1/budget-benchmarks, /district-vulnerability, /calculations/district-comparison, and /nisr/financial-inclusion/districts
  useEffect(() => {
    let isMounted = true;
    Promise.all([
      fetchBudgetBenchmark(districtAId, householdSizeNumber),
      fetchBudgetBenchmark(districtBId, householdSizeNumber),
      fetchDistrictVulnerability(districtAId),
      fetchDistrictComparison(districtAId, districtBId, householdSizeNumber),
      fetchDistrictFinancialInclusion(),
    ]).then(([benchA, benchB, vuln, comp, finInc]) => {
      if (!isMounted) return;
      if (benchA) {
        setBackendBenchmarkA(benchA);
      }
      if (benchB) setBackendBenchmarkB(benchB);
      if (vuln) setVulnerabilityA(vuln);
      if (comp) setDistrictComparisonApi(comp);
      if (finInc?.items) {
        const dClean = districtAId.toLowerCase();
        const found = finInc.items.find(
          (item) => item.districtCode.toLowerCase() === dClean || item.name.toLowerCase() === dClean
        );
        if (found) setFinancialInclusionA(found);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [districtAId, districtBId, householdSizeNumber]);

  // Live call to POST /api/v1/calculations/stress-test
  useEffect(() => {
    if (stressScenario !== 'food_inflation' && stressScenario !== 'rent_surge') return;
    let ignore = false;
    const code = stressScenario === 'food_inflation' ? 'food_inflation_15' : 'rent_surge_10';
    calculateStressTest(districtAId, householdSizeNumber, code).then((res) => {
      if (!ignore && res) setStressTestApi(res);
    });
    return () => {
      ignore = true;
    };
  }, [districtAId, householdSizeNumber, stressScenario]);

  // Benchmark data: seamlessly uses live backend benchmark data if available, falling back to local formulas
  const rawBaseBenchmarkA = getDistrictBenchmark(districtAId, householdSizeNumber);
  const baseBenchmarkA = backendBenchmarkA
    ? {
        ...rawBaseBenchmarkA,
        baselineTotal: backendBenchmarkA.total,
        lines: rawBaseBenchmarkA.lines.map((l) => {
          const match = backendBenchmarkA.lines.find((bl) => bl.categoryCode === l.categoryCode);
          return match ? { ...l, amount: match.monthlyAmount } : l;
        }),
      }
    : rawBaseBenchmarkA;

  const rawBaseBenchmarkB = getDistrictBenchmark(districtBId, householdSizeNumber);
  const baseBenchmarkB = backendBenchmarkB
    ? {
        ...rawBaseBenchmarkB,
        baselineTotal: backendBenchmarkB.total,
        lines: rawBaseBenchmarkB.lines.map((l) => {
          const match = backendBenchmarkB.lines.find((bl) => bl.categoryCode === l.categoryCode);
          return match ? { ...l, amount: match.monthlyAmount } : l;
        }),
      }
    : rawBaseBenchmarkB;

  // Dynamic scenario adjustment
  const applyScenario = (bench: typeof baseBenchmarkA) => {
    if (stressScenario === 'food_inflation') {
      const lines = bench.lines.map((l) =>
        l.categoryCode === 'food' ? { ...l, amount: Math.round(l.amount * 1.15) } : l
      );
      const total = lines.reduce((acc, curr) => acc + curr.amount, 0);
      return { ...bench, baselineTotal: total, lines };
    }
    if (stressScenario === 'rent_surge') {
      const lines = bench.lines.map((l) =>
        l.categoryCode === 'housing' ? { ...l, amount: Math.round(l.amount * 1.1) } : l
      );
      const total = lines.reduce((acc, curr) => acc + curr.amount, 0);
      return { ...bench, baselineTotal: total, lines };
    }
    return bench;
  };

  const benchmarkA = applyScenario(baseBenchmarkA);
  const benchmarkB = applyScenario(baseBenchmarkB);

  // Swap districts handler
  const handleSwapDistricts = () => {
    const temp = districtAId;
    setDistrictAId(districtBId);
    setDistrictBId(temp);
  };

  // Quick preset selector
  const handleSelectPreset = (distA: string, distB: string) => {
    setDistrictAId(distA);
    setDistrictBId(distB);
  };

  return (
    <div className="flex-1 flex flex-col justify-between w-full">
      {/* Main Content Area */}
      <main className="max-w-3xl mx-auto w-full px-4 sm:px-6 py-5 sm:py-8 flex flex-col gap-5">
        {/* Breadcrumb Header */}
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

          {/* District Context & Policy Actions */}
          <div className="flex flex-wrap items-center gap-2 mt-1">
            {vulnerabilityA && (
              <span className="bg-[#FAF3E8] text-[#925B1D] text-[11px] font-semibold px-2.5 py-0.5 rounded-full border border-[#E9D9C3]">
                {vulnerabilityA.name} Vulnerability: {vulnerabilityA.score}/100 ({vulnerabilityA.band})
              </span>
            )}
            {financialInclusionA && (
              <span className="bg-[#F0F5FA] text-[#225785] text-[11px] font-semibold px-2.5 py-0.5 rounded-full border border-[#D0E2F0]">
                FinScope 2024 ({financialInclusionA.name}): Banked {financialInclusionA.bankedPct}% · Non-Bank Formal {financialInclusionA.otherFormalNonBankPct}% · Excluded {financialInclusionA.excludedPct}%
              </span>
            )}
            <button
              type="button"
              onClick={() => setPolicyModalOpen(true)}
              className="bg-[#1E5E45] hover:bg-[#164835] text-white text-[11px] font-semibold px-2.5 py-0.5 rounded-full transition-colors cursor-pointer shadow-xs"
            >
              Simulate Policy Transfers &rarr;
            </button>
          </div>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="bg-[#EFECE5] p-1 rounded-2xl flex items-center gap-1 border border-[#E3DED4] self-start sm:self-auto w-full sm:w-auto">
          <button
            type="button"
            onClick={() => setMode('district_vs_district')}
            className={`flex-1 sm:flex-initial py-2 px-3.5 sm:px-5 rounded-xl text-xs sm:text-[13px] font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${
              mode === 'district_vs_district'
                ? 'bg-[#1E5E45] text-white shadow-xs'
                : 'text-[#485C50] hover:text-[#183928] hover:bg-[#E5E1D8]'
            }`}
          >
            <ArrowLeftRight className="w-3.5 h-3.5" />
            <span>{t.modeDistrictVsDistrict}</span>
          </button>

          <button
            type="button"
            onClick={() => setMode('my_plan_vs_benchmark')}
            className={`flex-1 sm:flex-initial py-2 px-3.5 sm:px-5 rounded-xl text-xs sm:text-[13px] font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${
              mode === 'my_plan_vs_benchmark'
                ? 'bg-[#1E5E45] text-white shadow-xs'
                : 'text-[#485C50] hover:text-[#183928] hover:bg-[#E5E1D8]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{t.modeMyPlanVsBenchmark}</span>
          </button>
        </div>

        {/* District & Household Configuration Controls */}
        <section
          aria-label="District selection controls"
          className="bg-white rounded-2xl border border-[#E4DFD5] p-4 sm:p-5 shadow-xs flex flex-col gap-3.5"
        >
          {mode === 'district_vs_district' ? (
            /* Mode 1: Dual District Searchable Selectors (e.g. Kigali Gasabo vs Musanze) */
            <div className="flex flex-col gap-3">
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
                {/* District A (Baseline) */}
                <div className="sm:col-span-5">
                  <SearchableDistrictSelect
                    id="select-district-a"
                    label={t.districtALabel}
                    value={districtAId}
                    onChange={setDistrictAId}
                    language={language}
                  />
                </div>

                {/* Swap Button */}
                <div className="sm:col-span-2 flex justify-center pb-0.5">
                  <button
                    type="button"
                    onClick={handleSwapDistricts}
                    title={t.swapDistricts}
                    className="w-10 h-10 rounded-xl bg-[#E8F2EC] hover:bg-[#D5E8DB] text-[#1E5E45] border border-[#CDE5D6] flex items-center justify-center transition-colors shadow-2xs cursor-pointer"
                  >
                    <ArrowLeftRight className="w-4 h-4" />
                  </button>
                </div>

                {/* District B (Comparison Target) */}
                <div className="sm:col-span-5">
                  <SearchableDistrictSelect
                    id="select-district-b"
                    label={t.districtBLabel}
                    value={districtBId}
                    onChange={setDistrictBId}
                    language={language}
                  />
                </div>
              </div>

              {/* Household Size Input Box & Popular Presets */}
              <div className="pt-3 border-t border-[#F0ECE4] flex flex-col lg:flex-row lg:items-center justify-between gap-3.5">
                <div className="flex items-center gap-3 shrink-0">
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Users className="w-4 h-4 text-[#1E5E45]" />
                    <label htmlFor="household-size-input" className="text-xs sm:text-[13px] font-semibold text-[#3F5448]">
                      {t.householdSizeLabel}:
                    </label>
                  </div>

                  {/* Interactive Number Input with Stepper Buttons */}
                  <div className="flex items-center bg-[#FAF8F4] border border-[#DCD5C9] rounded-xl overflow-hidden shadow-2xs h-10">
                    <button
                      type="button"
                      onClick={decrementHousehold}
                      disabled={householdSizeNumber <= 1}
                      className="w-9 h-full flex items-center justify-center text-[#2D4537] hover:bg-[#EAE4D7] disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-base font-bold cursor-pointer border-r border-[#E3DDD1]"
                      aria-label="Decrease household size"
                    >
                      −
                    </button>

                    <input
                      id="household-size-input"
                      type="number"
                      min={1}
                      max={25}
                      value={householdSizeNumber}
                      onChange={handleHouseholdInputChange}
                      className="w-12 h-full text-center font-bold text-sm sm:text-base text-[#143B2A] bg-transparent focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />

                    <button
                      type="button"
                      onClick={incrementHousehold}
                      disabled={householdSizeNumber >= 25}
                      className="w-9 h-full flex items-center justify-center text-[#2D4537] hover:bg-[#EAE4D7] disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-sm font-bold cursor-pointer border-l border-[#E3DDD1]"
                      aria-label="Increase household size"
                    >
                      +
                    </button>
                  </div>

                  {/* Properly Sized Household Size Badge on Desktop and Mobile */}
                  <div className="h-10 px-3.5 sm:px-4 rounded-xl bg-[#EAF5EE] border border-[#CDE8D7] flex items-center justify-center text-xs sm:text-sm font-semibold text-[#18533C] shadow-2xs shrink-0 whitespace-nowrap">
                    {formattedHouseholdSize}
                  </div>
                </div>

                {/* Popular Presets Pills */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[11px] text-[#718478] font-medium hidden xl:inline">
                    {t.quickPresetsTitle}:
                  </span>
                  {COMPARISON_PRESETS.map((preset) => {
                    const isSelected =
                      districtAId === preset.districtA && districtBId === preset.districtB;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        onClick={() => handleSelectPreset(preset.districtA, preset.districtB)}
                        className={`text-[11px] sm:text-xs font-medium py-1.5 px-3 rounded-full transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-[#1E5E45] text-white shadow-2xs'
                            : 'bg-[#F2EFE8] text-[#455A4E] hover:bg-[#E5E1D8]'
                        }`}
                      >
                        {language === 'RW' ? preset.labelRw : preset.labelEn}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            /* Mode 2: Single District Searchable Select & Household Input Box */
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
              <div className="sm:col-span-7">
                <SearchableDistrictSelect
                  id="select-single-district"
                  label={t.districtSingleLabel}
                  value={districtAId}
                  onChange={setDistrictAId}
                  language={language}
                />
              </div>

              <div className="sm:col-span-5 flex flex-col gap-1">
                <label htmlFor="single-household-input" className="text-xs sm:text-[13px] font-semibold text-[#3F5448]">
                  {t.householdSizeLabel}
                </label>
                <div className="flex items-center gap-2.5">
                  <div className="flex items-center bg-[#FAF8F4] border border-[#DCD5C9] rounded-xl overflow-hidden shadow-2xs h-10">
                    <button
                      type="button"
                      onClick={decrementHousehold}
                      disabled={householdSizeNumber <= 1}
                      className="w-9 h-full flex items-center justify-center text-[#2D4537] hover:bg-[#EAE4D7] disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-base font-bold cursor-pointer border-r border-[#E3DDD1]"
                    >
                      −
                    </button>
                    <input
                      id="single-household-input"
                      type="number"
                      min={1}
                      max={25}
                      value={householdSizeNumber}
                      onChange={handleHouseholdInputChange}
                      className="w-12 h-full text-center font-bold text-sm sm:text-base text-[#143B2A] bg-transparent focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />
                    <button
                      type="button"
                      onClick={incrementHousehold}
                      disabled={householdSizeNumber >= 25}
                      className="w-9 h-full flex items-center justify-center text-[#2D4537] hover:bg-[#EAE4D7] disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-sm font-bold cursor-pointer border-l border-[#E3DDD1]"
                    >
                      +
                    </button>
                  </div>
                  <div className="h-10 px-3.5 sm:px-4 rounded-xl bg-[#EAF5EE] border border-[#CDE8D7] flex items-center justify-center text-xs sm:text-sm font-semibold text-[#18533C] shadow-2xs whitespace-nowrap">
                    {formattedHouseholdSize}
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Seasonal Harvest Alert (Feature 4) */}
        {mode === 'district_vs_district' && (
          <SeasonalHarvestCard
            districtA={benchmarkA}
            districtB={benchmarkB}
            language={language}
          />
        )}

        {/* Quick Scenario Stress-Tester Chips (Feature 5) */}
        {mode === 'district_vs_district' && (
          <StressTestChips
            scenario={stressScenario}
            onScenarioChange={setStressScenario}
            language={language}
            netSavingsMonthly={benchmarkB.baselineTotal - benchmarkA.baselineTotal}
            apiResult={(stressScenario === 'food_inflation' || stressScenario === 'rent_surge') ? stressTestApi : null}
          />
        )}

        {/* Primary Benchmark Comparison Card */}
        {mode === 'district_vs_district' ? (
          <DistrictComparisonCard
            districtA={benchmarkA}
            districtB={benchmarkB}
            householdSize={formattedHouseholdSize}
            language={language}
            districtComparisonApi={districtComparisonApi}
          />
        ) : (
          <MyPlanComparisonCard
            district={benchmarkA}
            householdSize={formattedHouseholdSize}
            language={language}
          />
        )}

        {/* Feature 1: Household Income & Buffer Runway Feasibility Gauge */}
        {mode === 'district_vs_district' && (
          <IncomeRunwayCard
            districtA={benchmarkA}
            districtB={benchmarkB}
            householdIncome={householdIncome}
            onIncomeChange={setHouseholdIncome}
            language={language}
          />
        )}

        {/* Feature 3: "Where Every 10,000 RWF Goes" Budget Share Visualizer */}
        {mode === 'district_vs_district' && (
          <BudgetShareVisualizer
            districtA={benchmarkA}
            districtB={benchmarkB}
            language={language}
          />
        )}

        {/* Feature 2: "What's in the Basket?" Real Local Market Breakdown */}
        {mode === 'district_vs_district' && (
          <MarketBasketDrawer
            districtA={benchmarkA}
            districtB={benchmarkB}
            language={language}
          />
        )}

        {/* Look at the whole picture card */}
        <WholePictureCard
          mode={mode}
          districtA={benchmarkA}
          districtB={benchmarkB}
          language={language}
        />

        {/* Informative Disclaimer Card (Matching Screenshot Amber/Sand Box) */}
        <div className="bg-[#FAF0E1] border border-[#EED7B8] rounded-2xl p-4 sm:p-4.5 flex items-start gap-3 shadow-2xs">
          <Info className="w-5 h-5 text-[#9E6211] shrink-0 mt-0.5" />
          <p className="text-xs sm:text-[12.5px] text-[#784D12] leading-relaxed">
            {t.disclaimerText}
          </p>
        </div>

        {/* Primary Call to Action Button */}
        <button
          type="button"
          onClick={() => setSimulatorModalOpen(true)}
          className="w-full py-3.5 px-6 rounded-2xl bg-[#1E5E45] hover:bg-[#164935] text-white font-medium text-sm sm:text-base transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer group"
        >
          <span>{t.usePlanInSimulatorBtn}</span>
          <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
        </button>

        {/* Helpful Back Navigation Link */}
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={() => onTabChange('tracker')}
            className="text-xs font-semibold text-[#1E5E45] hover:underline cursor-pointer"
          >
            {language === 'RW' ? '← Subira ku Ibarura rya Buri Munsi' : '← Back to Daily Tracker'}
          </button>
        </div>
      </main>

      {/* Simulator Preview Modal */}
      <SimulatorPreviewModal
        isOpen={simulatorModalOpen}
        onClose={() => setSimulatorModalOpen(false)}
        districtA={benchmarkA}
        districtB={benchmarkB}
        householdSize={formattedHouseholdSize}
        language={language}
        onProceedToTracker={() => {
          setSimulatorModalOpen(false);
          onTabChange('resilience');
        }}
      />

      {/* Policy Scenario Simulator Modal */}
      <PolicyScenarioModal
        isOpen={policyModalOpen}
        onClose={() => setPolicyModalOpen(false)}
        language={language}
      />

      {/* Mobile-Only Bottom Navigation */}
      <BottomNav
        activeTab={activeTab}
        onTabChange={onTabChange}
        language={language}
      />
    </div>
  );
};
