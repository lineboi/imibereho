import React, { useState, useEffect } from 'react';
import type { Language, NavTab } from '../../types';
import type { ShockType, ShockOption, CopingLever } from '../../data/mockResilienceData';
import {
  SHOCK_OPTIONS,
  INNOVATIVE_COPING_LEVERS,
  RESILIENCE_TRANSLATIONS,
} from '../../data/mockResilienceData';
import {
  calculateHouseholdShock,
  calculateResilienceSimulation,
  fetchShocksCatalog,
  fetchBudgetBenchmark,
  type HouseholdShockResponse,
  type ResilienceSimulationResponse,
  type ShockCatalogResponse,
} from '../../services/api';
import { ScenarioSetupCard } from './ScenarioSetupCard';
import { ShockResultCard } from './ShockResultCard';
import { BufferNotGuaranteeCard } from './BufferNotGuaranteeCard';
import { InnovativeSolutionsPlaybook } from './InnovativeSolutionsPlaybook';
import { BufferRunwayTimeline } from './BufferRunwayTimeline';
import { ResilienceScoreMeter } from './ResilienceScoreMeter';
import { BottomNav } from '../DailyTracker/BottomNav';
import { Info } from 'lucide-react';

interface ResilienceSimulatorPageProps {
  language: Language;
  onNavigateHome: () => void;
  district?: string;
  householdSize?: string;
  monthlyIncome?: string;
  plannedEssentials?: number | null;
  savingsBuffer?: number | null;
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const ResilienceSimulatorPage: React.FC<ResilienceSimulatorPageProps> = ({
  language,
  onNavigateHome,
  district = 'Gasabo',
  householdSize = '4 people',
  monthlyIncome,
  plannedEssentials,
  savingsBuffer,
  activeTab,
  onTabChange,
}) => {
  const t = RESILIENCE_TRANSLATIONS[language];
  const sizeNum = parseInt(householdSize.replace(/[^0-9]/g, ''), 10) || 4;
  const parsedIncome = parseInt((monthlyIncome || '').replace(/[^0-9]/g, ''), 10) || 0;

  // Household Baseline Parameters from PostgreSQL database
  const [baseMonthlyIncome, setBaseMonthlyIncome] = useState<number>(
    parsedIncome > 0 ? parsedIncome : 500000
  );
  const [basePlannedExpenses, setBasePlannedExpenses] = useState<number>(
    plannedEssentials && plannedEssentials > 0 ? plannedEssentials : 250000
  );
  const [availableSavings, setAvailableSavings] = useState<number>(
    savingsBuffer && savingsBuffer > 0 ? savingsBuffer : 250000
  );

  // Core Scenario State
  const [shockType, setShockType] = useState<ShockType>('income_drop');
  const [reductionPct, setReductionPct] = useState<number>(20);
  const [durationMonths, setDurationMonths] = useState<number>(3);

  // Innovative Action Levers State
  const [activeLeverIds, setActiveLeverIds] = useState<string[]>([]);
  const [shocksCatalog, setShocksCatalog] = useState<ShockCatalogResponse | null>(null);
  const [apiShockResult, setApiShockResult] = useState<HouseholdShockResponse | null>(null);
  const [backendSimulationResult, setBackendSimulationResult] = useState<ResilienceSimulationResponse | null>(null);

  // Live database baseline sync: GET /api/v1/budget-benchmarks
  useEffect(() => {
    let isMounted = true;
    fetchBudgetBenchmark(district, sizeNum).then((bench) => {
      if (!isMounted || !bench) return;
      if (!plannedEssentials) {
        setBasePlannedExpenses(bench.total);
      }
      if (!parsedIncome) {
        setBaseMonthlyIncome(Math.round(bench.total * 1.15));
      }
      if (!savingsBuffer) {
        setAvailableSavings(Math.round(bench.total * 0.4));
      }
    });
    return () => {
      isMounted = false;
    };
  }, [district, sizeNum, plannedEssentials, parsedIncome, savingsBuffer]);

  const handleResetBaseline = () => {
    fetchBudgetBenchmark(district, sizeNum).then((bench) => {
      if (!bench) return;
      setBasePlannedExpenses(bench.total);
      setBaseMonthlyIncome(Math.round(bench.total * 1.15));
      setAvailableSavings(Math.round(bench.total * 0.4));
    });
  };

  // Load official shock catalog on mount: GET /api/v1/shocks/catalog
  useEffect(() => {
    let isMounted = true;
    fetchShocksCatalog().then((cat) => {
      if (isMounted && cat) setShocksCatalog(cat);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  // Dynamic Shocks from database catalog
  const dynamicShockOptions: ShockOption[] = shocksCatalog?.items
    ? shocksCatalog.items.map((it) => {
        const fallback = SHOCK_OPTIONS.find((s) => s.id === it.id);
        return {
          id: it.id as ShockType,
          labelEn: it.title,
          labelRw: fallback?.labelRw || it.title,
          descriptionEn: fallback?.descriptionEn || it.title,
          descriptionRw: fallback?.descriptionRw || it.title,
          defaultAmount: it.defaultAmount ?? undefined,
          isLumpSum: it.isLumpSum,
        };
      })
    : SHOCK_OPTIONS;

  // Dynamic Coping Levers from database catalog
  const dynamicCopingLevers: CopingLever[] = shocksCatalog?.copingLevers
    ? shocksCatalog.copingLevers.map((cl) => {
        const isOneOff = cl.kind === 'one_off_support';
        return {
          id: cl.id,
          titleEn: cl.title,
          titleRw:
            cl.id === 'trim_non_essentials'
              ? 'Kugabanya ibitari ngombwa'
              : cl.id === 'seasonal_agro_swaps'
              ? 'Ibihingwa by’amazi n’imyaka'
              : 'Amafaranga y’Ikimina cyangwa Ubwizigame',
          subEn: isOneOff ? 'Community rotational fund payout or 0% mutual fund loan.' : 'Reduce flexible household spending.',
          subRw: isOneOff ? 'Kwakira amafaranga y’ubwizigame bwo mu kimina cy’abaturanyi.' : 'Guhagarika ibinezeza by’akanya gato.',
          type: isOneOff ? ('lump_sum_aid' as const) : ('monthly_reduction' as const),
          monthlySavings: isOneOff ? 0 : cl.amount,
          oneTimeBufferBoost: isOneOff ? cl.amount : 0,
          iconType: cl.id === 'trim_non_essentials' ? 'trim' : cl.id === 'seasonal_agro_swaps' ? 'swap' : 'tontine',
        };
      })
    : INNOVATIVE_COPING_LEVERS;

  // Directly call live backend calculation endpoint: POST /api/v1/calculations/household-shock
  useEffect(() => {
    if (shockType !== 'income_drop') return;
    let ignore = false;
    calculateHouseholdShock({
      monthlyIncome: baseMonthlyIncome,
      monthlyEssentials: basePlannedExpenses,
      savings: availableSavings,
      incomeReductionPct: reductionPct,
      durationMonths: durationMonths,
    }).then((res) => {
      if (!ignore && res) {
        setApiShockResult(res);
      }
    });
    return () => {
      ignore = true;
    };
  }, [shockType, reductionPct, durationMonths, availableSavings, baseMonthlyIncome, basePlannedExpenses]);

  // Directly call live full simulation engine: POST /api/v1/calculations/resilience-simulation
  useEffect(() => {
    let ignore = false;
    const validLevers = activeLeverIds.filter((id) =>
      ['trim_non_essentials', 'seasonal_agro_swaps', 'ibimina_tontine'].includes(id)
    ) as ('trim_non_essentials' | 'seasonal_agro_swaps' | 'ibimina_tontine')[];

    const apiShockType: 'income_drop' | 'medical_emergency' | 'school_fees' =
      shockType === 'medical_emergency' || shockType === 'medical_clinic'
        ? 'medical_emergency'
        : shockType === 'school_fees' || shockType === 'school_term'
        ? 'school_fees'
        : 'income_drop';

    const isLump = apiShockType !== 'income_drop';

    calculateResilienceSimulation({
      baseline: {
        monthlyIncome: baseMonthlyIncome,
        monthlyEssentials: basePlannedExpenses,
        savings: availableSavings,
      },
      shock: {
        type: apiShockType,
        incomeReductionPct: !isLump ? reductionPct : null,
        durationMonths,
        amount: isLump ? 45000 : null,
      },
      activeCopingLevers: validLevers,
    }).then((res) => {
      if (!ignore && res) {
        setBackendSimulationResult(res);
      }
    });
    return () => {
      ignore = true;
    };
  }, [shockType, reductionPct, durationMonths, availableSavings, activeLeverIds, baseMonthlyIncome, basePlannedExpenses]);

  const handleToggleLever = (leverId: string) => {
    setActiveLeverIds((prev) =>
      prev.includes(leverId) ? prev.filter((id) => id !== leverId) : [...prev, leverId]
    );
  };

  // Calculations (uses live backend response if available, with resilient fallback)
  const selectedShockOption = SHOCK_OPTIONS.find((s) => s.id === shockType) ?? SHOCK_OPTIONS[0];

  let shockedIncome = baseMonthlyIncome;
  let effectivePlannedExpenses = basePlannedExpenses;

  if (shockType === 'income_drop') {
    if (apiShockResult) {
      shockedIncome = apiShockResult.shockedMonthlyIncome;
    } else {
      // BR-02 formula: 180,000 * (1 - 20/100) = 144,000 RWF
      shockedIncome = Math.round(baseMonthlyIncome * (1 - reductionPct / 100));
    }
  } else if (selectedShockOption.isLumpSum && selectedShockOption.defaultAmount) {
    // Lump sum shock distributed over duration or hit immediately
    effectivePlannedExpenses =
      basePlannedExpenses + Math.round(selectedShockOption.defaultAmount / durationMonths);
  } else if (selectedShockOption.defaultAmount) {
    effectivePlannedExpenses = basePlannedExpenses + selectedShockOption.defaultAmount;
  }

  // Raw monthly gap before coping actions (BR-03)
  const rawGap =
    backendSimulationResult
      ? backendSimulationResult.rawMonthlyGap
      : shockType === 'income_drop' && apiShockResult
      ? apiShockResult.monthlyGap
      : Math.max(0, effectivePlannedExpenses - shockedIncome);

  // Coping relief calculations
  const activeLevers = INNOVATIVE_COPING_LEVERS.filter((l) => activeLeverIds.includes(l.id));
  const monthlyCopingSavings =
    backendSimulationResult && activeLeverIds.length > 0
      ? backendSimulationResult.copingReliefMonthly
      : activeLevers.reduce((sum, l) => sum + l.monthlySavings, 0);

  const lumpSumCopingBoost =
    backendSimulationResult && activeLeverIds.length > 0
      ? backendSimulationResult.lumpSumSupport
      : activeLevers.reduce((sum, l) => sum + (l.oneTimeBufferBoost ?? 0), 0);

  // Net monthly gap after innovative coping actions
  const netGap =
    backendSimulationResult
      ? backendSimulationResult.netMonthlyGap
      : Math.max(0, rawGap - monthlyCopingSavings);

  // Total available buffer (base savings + lump sum mutual aid like tontines/MoMo)
  const totalEffectiveSavings = availableSavings + lumpSumCopingBoost;

  // Savings drawdown over duration (BR-04/BR-05)
  const savingsUsed =
    backendSimulationResult && activeLeverIds.length > 0
      ? backendSimulationResult.savingsUsed
      : Math.min(totalEffectiveSavings, netGap * durationMonths);

  const savingsRemain =
    backendSimulationResult && activeLeverIds.length > 0
      ? backendSimulationResult.savingsRemaining
      : Math.max(0, totalEffectiveSavings - savingsUsed);

  // Runway months (BR-06)
  const runwayMonthsStr =
    backendSimulationResult && backendSimulationResult.runwayMonths !== null
      ? backendSimulationResult.runwayMonths.toFixed(0)
      : netGap > 0
      ? (totalEffectiveSavings / netGap).toFixed(0)
      : rawGap > 0
      ? '∞ (Protected)'
      : '10';

  // Resilience Health Score (0 - 100)
  const activeScore =
    backendSimulationResult
      ? backendSimulationResult.resilienceScore
      : Math.max(45, Math.min(95, 70 - Math.round(rawGap / 2000) + activeLeverIds.length * 7));

  const baselineScore =
    backendSimulationResult
      ? Math.max(0, backendSimulationResult.resilienceScore - backendSimulationResult.scoreChange)
      : Math.max(45, Math.min(75, 70 - Math.round(rawGap / 2000)));

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

          {/* Household Tag Pill */}
          <div className="flex flex-wrap items-center gap-2 mt-1">
            <span className="bg-[#E4ECE5] text-[#244E38] text-xs font-semibold px-3 py-1 rounded-full border border-[#CCE2D3]">
              {district} · {householdSize} · {language === 'RW' ? 'Urugo rw’icyitegererezo' : 'Demo household'}
            </span>
          </div>
        </div>

        {/* Card 1: Set your scenario */}
        <ScenarioSetupCard
          shockType={shockType}
          onShockTypeChange={setShockType}
          reductionPct={reductionPct}
          onReductionPctChange={setReductionPct}
          durationMonths={durationMonths}
          onDurationMonthsChange={setDurationMonths}
          availableSavings={availableSavings}
          onSavingsChange={setAvailableSavings}
          baseMonthlyIncome={baseMonthlyIncome}
          onBaseMonthlyIncomeChange={setBaseMonthlyIncome}
          basePlannedExpenses={basePlannedExpenses}
          onBasePlannedExpensesChange={setBasePlannedExpenses}
          onResetBaselineToBenchmark={handleResetBaseline}
          language={language}
          shockOptions={dynamicShockOptions}
        />

        {/* Card 2: Illustrative Result · Monthly (Forest Green Card) */}
        <ShockResultCard
          shockedIncome={shockedIncome}
          plannedExpenses={effectivePlannedExpenses}
          rawGap={rawGap}
          netGap={netGap}
          durationMonths={durationMonths}
          availableSavings={availableSavings}
          savingsUsed={savingsUsed}
          savingsRemain={savingsRemain}
          language={language}
          totalCopingRelief={monthlyCopingSavings}
        />

        {/* The Game-Changing Feature: Innovative Solutions / Coping Playbook */}
        <InnovativeSolutionsPlaybook
          activeLeverIds={activeLeverIds}
          onToggleLever={handleToggleLever}
          rawGap={rawGap}
          netGap={netGap}
          language={language}
          copingLevers={dynamicCopingLevers}
        />

        {/* Month-by-Month Savings Timeline */}
        <BufferRunwayTimeline
          initialSavings={availableSavings}
          rawGap={rawGap}
          netGap={netGap}
          durationMonths={durationMonths}
          language={language}
        />

        {/* Household Resilience Health Score Meter */}
        <ResilienceScoreMeter
          baselineScore={baselineScore}
          activeScore={activeScore}
          activeLeversCount={activeLeverIds.length}
          language={language}
        />

        {/* Card 3: A buffer, not a guarantee */}
        <BufferNotGuaranteeCard
          savings={totalEffectiveSavings}
          gap={netGap > 0 ? netGap : rawGap}
          runwayMonths={runwayMonthsStr}
          language={language}
        />

        {/* Card 4: Disclaimer Card */}
        <div className="bg-[#FAF0E1] border border-[#EED7B8] rounded-2xl p-4 sm:p-4.5 flex items-start gap-3 shadow-2xs">
          <Info className="w-5 h-5 text-[#9E6211] shrink-0 mt-0.5" />
          <p className="text-xs sm:text-[12.5px] text-[#784D12] leading-relaxed">
            {t.disclaimerText}
          </p>
        </div>

        {/* Navigation back link */}
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={() => onTabChange('district_advisor')}
            className="text-xs font-semibold text-[#1E5E45] hover:underline cursor-pointer"
          >
            {language === 'RW' ? '← Reba Inama y’Akarere' : '← Back to District Budget Advisor'}
          </button>
        </div>
      </main>

      {/* Mobile-Only Bottom Navigation */}
      <BottomNav
        activeTab={activeTab}
        onTabChange={onTabChange}
        language={language}
      />
    </div>
  );
};
