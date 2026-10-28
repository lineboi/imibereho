/**
 * Imibereho Backend API Client Service
 * Directly connects all frontend components to FastAPI backend endpoints (/api/v1/...) via Vite proxy.
 */

// ==========================================
// Base Reference Types
// ==========================================

export interface ApiDistrict {
  code: string;
  name: string;
  province: string | null;
}

export interface ApiExpenseCategory {
  code: string;
  name: string;
  icon: string | null;
}

export interface BenchmarkLine {
  categoryCode: string;
  monthlyAmount: number;
}

export interface BudgetBenchmarkData {
  district: {
    code: string;
    name: string;
  };
  householdSize: number;
  lines: BenchmarkLine[];
  total: number;
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

// ==========================================
// District Advisor & Benchmark Types
// ==========================================

export interface DistrictBasketData {
  district: {
    code: string;
    name: string;
  };
  householdSize: number;
  lines: BenchmarkLine[];
  total: number;
}

export interface DistrictComparisonResponse {
  districtA: DistrictBasketData;
  districtB: DistrictBasketData;
  variance: {
    netDifference: number;
    percentageDifference: number | null;
    lines: Array<{
      categoryCode: string;
      amountA: number;
      amountB: number;
      difference: number;
    }>;
  };
  costOfLivingMultiplier: number | null;
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface BasketDetailsResponse {
  districtCode: string;
  householdSize: number;
  referenceRentIndex: number;
  referenceTransitPass: number;
  staplePriceIndex: Record<string, number | null>;
  primaryMarketHub: string | null;
  unavailableFields: string[];
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export type StressScenarioCode = 'food_inflation_15' | 'rent_surge_10';

export interface StressTestRequest {
  district: string;
  householdSize: number;
  scenario: StressScenarioCode;
}

export interface StressTestResponse {
  baselineTotal: number;
  stressedTotal: number;
  monthlyIncrease: number;
  bufferImpactMonths: number | null;
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface PlanLine {
  categoryCode: string;
  plannedAmount: number;
}

export interface BudgetComparisonRequest {
  district: string;
  householdSize: number;
  plan: PlanLine[];
}

export interface BudgetComparisonResponse {
  lines: Array<{
    categoryCode: string;
    planned: number;
    reference: number;
    difference: number;
  }>;
  totals: {
    planned: number;
    reference: number;
    difference: number;
  };
  largestAbove?: {
    categoryCode: string;
    difference: number;
  } | null;
  largestBelow?: {
    categoryCode: string;
    difference: number;
  } | null;
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

// ==========================================
// Resilience Simulator Types
// ==========================================

export interface HouseholdShockRequest {
  baseline: {
    monthlyIncome: number;
    monthlyEssentials: number;
    savings: number;
  };
  shock: {
    type: 'income_fall';
    incomeReductionPct: number;
    durationMonths: number;
  };
}

export interface HouseholdShockResponse {
  baselineMonthlyBalance: number;
  shockedMonthlyIncome: number;
  monthlyGap: number;
  savingsUsed: number;
  savingsRemaining: number;
  savingsExhausted: boolean;
  runwayMonths: number;
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface ShockCatalogItem {
  id: string;
  title: string;
  description: string;
  isLumpSum: boolean;
  defaultPct?: number | null;
  defaultAmount?: number | null;
  defaultDuration: number;
}

export interface CopingLeverItem {
  id: string;
  title: string;
  description: string;
  reliefType: 'monthly_reduction' | 'lump_sum_support';
  reliefAmount: number;
}

export interface ShockCatalogResponse {
  items: ShockCatalogItem[];
  copingLevers: CopingLeverItem[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface ResilienceSimulationRequest {
  baseline: {
    monthlyIncome: number;
    monthlyEssentials: number;
    savings: number;
  };
  shock: {
    type: 'income_drop' | 'medical_emergency' | 'school_fees';
    incomeReductionPct?: number | null;
    durationMonths: number;
    amount?: number | null;
  };
  activeCopingLevers: string[];
}

export interface ResilienceSimulationResponse {
  rawMonthlyGap: number;
  copingReliefMonthly: number;
  lumpSumSupport: number;
  netMonthlyGap: number;
  totalEffectiveBuffer: number;
  runwayMonths: number | null;
  resilienceScore: number;
  scoreChange: number;
  shockCostMonthly: number;
  savingsUsed: number;
  savingsRemaining: number;
  savingsExhausted: boolean;
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

// ==========================================
// Seasonal Agro Swaps Types
// ==========================================

export interface SeasonalSwapApiItem {
  id: string;
  title: string;
  description: string;
  from: {
    name: string;
    quantity: number;
    unit: string;
    price: number;
  };
  to: {
    name: string;
    quantity: number;
    unit: string;
    price: number;
  };
  difference: number;
  footnote: string;
}

export interface SeasonalSwapApiResponse {
  items: SeasonalSwapApiItem[];
  tips: Array<{
    title: string;
    body: string;
  }>;
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface AgroSavingsProjectionRequest {
  swapId: string;
  mealsPerWeek: number;
  householdSize: number;
}

export interface PurchasingPowerEquivalent {
  item: string;
  metric: string;
  equivalentValue: string;
  contextEn: string;
  contextRw?: string;
}

export interface AgroSavingsProjectionResponse {
  swapId: string;
  perMealSavings: number;
  monthlyProjectedSavings: number;
  purchasingPowerEquivalents: PurchasingPowerEquivalent[];
  purchasingPowerStatus: 'available' | 'awaiting_validated_data';
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface PlateComponent {
  code: string;
  name: string;
  nameRw?: string;
  proportionPct: number;
  examples: string[];
}

export interface BalancedPlateResponse {
  status: 'available' | 'awaiting_validated_data';
  standard: string;
  plateComponents: PlateComponent[];
  energyTip: string | null;
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface HarvestCalendarResponse {
  status: 'available' | 'awaiting_validated_data';
  activeSeason: 'A' | 'B' | 'C' | null;
  seasonName: string | null;
  monthsRange: string | null;
  harvestHighlights: string[];
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface ShoppingChecklistItem {
  id: string;
  name: string;
  quantity: string;
  estPrice: number;
  isSwap: boolean;
}

export interface ShoppingChecklistResponse {
  status: 'available' | 'awaiting_validated_data';
  district: string;
  items: ShoppingChecklistItem[];
  totalEstimatedBasket: number | null;
  unoptimizedBasket: number | null;
  estimatedSavings: number | null;
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

// ==========================================
// National Statistics & Vulnerability Types
// ==========================================

export interface DistrictVulnerabilityResponse {
  districtCode: string;
  name: string;
  score: number;
  band: string;
  components: Array<{
    code: string;
    label: string;
    weight: number;
    value: number;
  }>;
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface NationalVulnerabilityResponse {
  model: {
    name: string;
    components: Array<{
      code: string;
      label: string;
      weight: number;
    }>;
  };
  items: Array<{
    code: string;
    name: string;
    score: number;
    band: string;
  }>;
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface SurveyIndicatorItem {
  dimension: string;
  group: string;
  estimate: number;
  confidenceInterval?: [number, number] | null;
}

export interface SurveyIndicatorResponse {
  status: string;
  source: {
    id: string;
    title: string;
    publisher: string;
    year?: string;
  };
  indicator: string;
  dimensions: string[];
  items: SurveyIndicatorItem[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

export interface DashboardOverviewResponse {
  kpis: {
    sampleSize: number;
    referenceHousehold: {
      districtCode: string;
      householdSize: number;
      monthlyIncome: number;
      monthlyEssentials: number;
      savings: number;
    };
    essentialsToIncomeRatio: number;
    shockDeficit: {
      incomeReductionPct: number;
      householdsInDeficit: number;
      share: number;
    };
  };
  essentialsTrend: {
    unit: string;
    incomeReference: number;
    points: Array<{
      month: string;
      essentials: number;
    }>;
  };
  incomeSources: Array<{
    code: string;
    label: string;
    households: number;
    share: number;
  }>;
  insight: {
    baselineMonthlyBalance: number;
    shockMonthlyGap: number;
    incomeReductionPct: number;
  };
  topDistricts: Array<{
    code: string;
    name: string;
    score: number;
    band: string;
  }>;
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

// ------------------------------------------
// System Readiness & Health Types
// ------------------------------------------

export interface ReadyChecks {
  database: 'ok' | 'failed';
  migrations: 'ok' | 'failed';
  seed: 'ok' | 'failed';
}

export interface ReadinessResult {
  ready: boolean;
  status: string;
  checks?: ReadyChecks;
  detail?: string;
  timestamp: string;
}

// ------------------------------------------
// Policy Scenario Types (POST /calculations/policy-scenario)
// ------------------------------------------

export interface PolicyScenarioRequest {
  instrument: 'monthly_cash_support';
  incomeLossPct: number;
  durationMonths: number;
  supportPerHouseholdMonthly: number;
  eligibleHouseholds: number;
  baseline?: {
    monthlyIncome?: number;
    monthlyEssentials?: number;
    savings?: number;
  };
}

export interface PolicyScenarioRow {
  no_shock: number;
  shock_only: number;
  shock_with_support: number;
}

export interface PolicyScenarioResponse {
  directTransferBudget: number;
  modelledMonthlyGapWithSupport: number;
  horizonMonths: number;
  baselineUsed: {
    monthlyIncome: number;
    monthlyEssentials: number;
    savings: number;
    source: 'reference' | 'request';
  };
  comparison: {
    columns: string[];
    rows: {
      incomePerMonth: PolicyScenarioRow;
      supportPerMonth: PolicyScenarioRow;
      expensesPerMonth: PolicyScenarioRow;
      netMonthlyBalance: PolicyScenarioRow;
      savingsAfterHorizon: PolicyScenarioRow;
    };
  };
  assumptions: string[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

// ------------------------------------------
// Dashboard Filters Types (GET /dashboard/filters)
// ------------------------------------------

export interface DashboardFilterOption {
  code: string;
  label: string;
  isDefault: boolean;
}

export interface DashboardFiltersResponse {
  geographies: DashboardFilterOption[];
  periods: DashboardFilterOption[];
  householdGroups: DashboardFilterOption[];
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

// ------------------------------------------
// NISR Official Sources & Financial Inclusion Types
// ------------------------------------------

export interface NisrSourceItem {
  id: string;
  title: string;
  publisher: string;
  sponsors: string | null;
  distributor: string;
  citation: string;
  publicationDate: string;
  surveyRound: string;
  fieldworkPeriod: string | null;
  population: string;
  sampleSize: number;
  lowestPublishedGeography: string;
  documentFile: string;
  documentUrl: string;
  catalogUrl: string;
  documentSha256?: string;
  retrievedOn: string;
  notes: string;
}

export interface NisrSourcesResponse {
  items: NisrSourceItem[];
  meta: {
    isIllustrative: boolean;
    dataKind: string;
    sourceIds: string[];
    count: number;
  };
}

export interface NationalInclusionIndicator {
  code: string;
  measure: string;
  label: string;
  definition: string;
  population: string;
  unit: string;
  year: number;
  valuePct: number;
  countPublished: string | null;
  comparison?: {
    year: number;
    valuePct: number;
    countPublished: string | null;
  };
  citation?: {
    page: number;
    tableOrFigure: string;
  };
  notes?: string | null;
}

export interface NationalFinancialInclusionResponse {
  status: string;
  geographicLevel: string;
  source: NisrSourceItem;
  indicators: NationalInclusionIndicator[];
  meta: {
    isIllustrative: boolean;
    dataKind: string;
    sourceIds: string[];
    count: number;
  };
}

export interface DistrictFinancialInclusionItem {
  districtCode: string;
  name: string;
  bankedPct: number;
  otherFormalNonBankPct: number;
  informalOnlyPct: number;
  excludedPct: number;
  citation?: {
    page: number;
    tableOrFigure: string;
  };
  notes?: string | null;
}

export interface DistrictFinancialInclusionResponse {
  status: string;
  geographicLevel: string;
  source: NisrSourceItem;
  categories: Array<{
    code: string;
    label: string;
    color?: string;
  }>;
  items: DistrictFinancialInclusionItem[];
  meta: {
    isIllustrative: boolean;
    dataKind: string;
    sourceIds: string[];
    count: number;
  };
}

// ------------------------------------------
// Auth & Profile Types
// ------------------------------------------

export interface RegisterPayload {
  identifier: string;
  password: string;
  profile: {
    district: string;
    householdSize: number;
    monthlyIncome: number;
    currency: 'RWF';
    preferredLanguage: 'EN' | 'RW';
  };
}

export interface RegisterResponse {
  token: string;
  tokenType: 'bearer';
  expiresIn: number;
  user: {
    id: string;
    identifier: string;
    district: string;
    householdSize: number;
  };
}

export interface LoginPayload {
  identifier: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  tokenType: 'bearer';
  user: {
    id: string;
    district: string;
  };
}

export interface UserProfileResponse {
  id: string;
  district: string;
  householdSize: number;
  monthlyIncome: number;
  plannedEssentials: number | null;
  savingsBuffer: number | null;
  preferredLanguage: 'EN' | 'RW';
}

export interface ProfilePatchPayload {
  district?: string;
  householdSize?: number;
  monthlyIncome?: number;
  plannedEssentials?: number | null;
  savingsBuffer?: number | null;
  preferredLanguage?: 'EN' | 'RW';
}

// ==========================================
// API Client Implementation
// ==========================================

const API_BASE = '/api/v1';

/**
 * Check backend readiness (/ready)
 * Returns detailed health checks for database, migrations, and seed data.
 */
export async function checkBackendReadiness(): Promise<ReadinessResult> {
  const timestamp = new Date().toLocaleTimeString();
  try {
    const res = await fetch('/ready');
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return {
        ready: false,
        status: data?.title || `HTTP ${res.status}`,
        checks: data?.checks,
        detail: data?.detail,
        timestamp,
      };
    }
    return {
      ready: data?.status === 'ready',
      status: data?.status || 'ready',
      checks: data?.checks,
      timestamp,
    };
  } catch (err) {
    return {
      ready: false,
      status: 'offline',
      detail: String(err),
      timestamp,
    };
  }
}

/**
 * GET /api/v1/districts
 */
export async function fetchDistricts(): Promise<ApiDistrict[]> {
  try {
    const res = await fetch(`${API_BASE}/districts`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.items || [];
  } catch (err) {
    console.warn('[API] fetchDistricts failed:', err);
    return [];
  }
}

/**
 * GET /api/v1/expense-categories
 */
export async function fetchExpenseCategories(): Promise<ApiExpenseCategory[]> {
  try {
    const res = await fetch(`${API_BASE}/expense-categories`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.items || [];
  } catch (err) {
    console.warn('[API] fetchExpenseCategories failed:', err);
    return [];
  }
}

/**
 * GET /api/v1/budget-benchmarks?district={district}&householdSize={householdSize}
 */
export async function fetchBudgetBenchmark(
  district: string,
  householdSize: number
): Promise<BudgetBenchmarkData | null> {
  try {
    const distClean = district.toLowerCase().trim();
    const size = Math.max(1, Math.min(20, householdSize));
    const res = await fetch(
      `${API_BASE}/budget-benchmarks?district=${encodeURIComponent(distClean)}&householdSize=${size}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchBudgetBenchmark failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/calculations/district-comparison?district_a={a}&district_b={b}&household_size={size}
 */
export async function fetchDistrictComparison(
  districtA: string,
  districtB: string,
  householdSize: number
): Promise<DistrictComparisonResponse | null> {
  try {
    const distAClean = districtA.toLowerCase().trim();
    const distBClean = districtB.toLowerCase().trim();
    const size = Math.max(1, Math.min(20, householdSize));
    const res = await fetch(
      `${API_BASE}/calculations/district-comparison?district_a=${encodeURIComponent(
        distAClean
      )}&district_b=${encodeURIComponent(distBClean)}&household_size=${size}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchDistrictComparison failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/districts/{code}/basket-details
 */
export async function fetchBasketDetails(
  districtCode: string
): Promise<BasketDetailsResponse | null> {
  try {
    const distClean = districtCode.toLowerCase().trim();
    const res = await fetch(`${API_BASE}/districts/${encodeURIComponent(distClean)}/basket-details`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchBasketDetails failed:', err);
    return null;
  }
}

/**
 * POST /api/v1/calculations/stress-test
 */
export async function calculateStressTest(
  district: string,
  householdSize: number,
  scenario: StressScenarioCode
): Promise<StressTestResponse | null> {
  try {
    const payload: StressTestRequest = {
      district: district.toLowerCase().trim(),
      householdSize: Math.max(1, Math.min(20, householdSize)),
      scenario,
    };
    const res = await fetch(`${API_BASE}/calculations/stress-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] calculateStressTest failed:', err);
    return null;
  }
}

/**
 * POST /api/v1/calculations/budget-comparison
 */
export async function calculateBudgetComparison(
  req: BudgetComparisonRequest
): Promise<BudgetComparisonResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/calculations/budget-comparison`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] calculateBudgetComparison failed:', err);
    return null;
  }
}

/**
 * POST /api/v1/calculations/household-shock
 */
export async function calculateHouseholdShock(params: {
  monthlyIncome: number;
  monthlyEssentials: number;
  savings: number;
  incomeReductionPct: number;
  durationMonths: number;
}): Promise<HouseholdShockResponse | null> {
  try {
    const payload: HouseholdShockRequest = {
      baseline: {
        monthlyIncome: Math.round(params.monthlyIncome),
        monthlyEssentials: Math.round(params.monthlyEssentials),
        savings: Math.round(params.savings),
      },
      shock: {
        type: 'income_fall',
        incomeReductionPct: Math.round(params.incomeReductionPct),
        durationMonths: Math.round(params.durationMonths),
      },
    };

    const res = await fetch(`${API_BASE}/calculations/household-shock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] calculateHouseholdShock failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/shocks/catalog
 */
export async function fetchShocksCatalog(): Promise<ShockCatalogResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/shocks/catalog`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchShocksCatalog failed:', err);
    return null;
  }
}

/**
 * POST /api/v1/calculations/resilience-simulation
 */
export async function calculateResilienceSimulation(
  req: ResilienceSimulationRequest
): Promise<ResilienceSimulationResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/calculations/resilience-simulation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] calculateResilienceSimulation failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/seasonal-swaps?district={district}&month={month}
 */
export async function fetchSeasonalSwaps(
  district: string,
  month: number
): Promise<SeasonalSwapApiResponse | null> {
  try {
    const distClean = district.toLowerCase().trim();
    const m = Math.max(1, Math.min(12, month));
    const res = await fetch(
      `${API_BASE}/seasonal-swaps?district=${encodeURIComponent(distClean)}&month=${m}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchSeasonalSwaps failed:', err);
    return null;
  }
}

/**
 * POST /api/v1/calculations/agro-savings-projection
 */
export async function calculateAgroSavingsProjection(
  swapId: string,
  mealsPerWeek: number,
  householdSize: number = 4
): Promise<AgroSavingsProjectionResponse | null> {
  try {
    const payload: AgroSavingsProjectionRequest = {
      swapId,
      mealsPerWeek: Math.max(1, Math.min(7, mealsPerWeek)),
      householdSize: Math.max(1, Math.min(20, householdSize)),
    };
    const res = await fetch(`${API_BASE}/calculations/agro-savings-projection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] calculateAgroSavingsProjection failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/nutrition/indyo-yuzuye
 */
export async function fetchIndyoYuzuyeGuidance(): Promise<BalancedPlateResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/nutrition/indyo-yuzuye`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchIndyoYuzuyeGuidance failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/agro/harvest-calendar
 */
export async function fetchHarvestCalendar(): Promise<HarvestCalendarResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/agro/harvest-calendar`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchHarvestCalendar failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/market/shopping-checklist?district={district}&household_size={householdSize}
 */
export async function fetchShoppingChecklist(
  district: string,
  householdSize: number = 4
): Promise<ShoppingChecklistResponse | null> {
  try {
    const distClean = district.toLowerCase().trim();
    const size = Math.max(1, Math.min(20, householdSize));
    const res = await fetch(
      `${API_BASE}/market/shopping-checklist?district=${encodeURIComponent(
        distClean
      )}&household_size=${size}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchShoppingChecklist failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/district-vulnerability/{districtCode}
 */
export async function fetchDistrictVulnerability(
  districtCode: string
): Promise<DistrictVulnerabilityResponse | null> {
  try {
    const distClean = districtCode.toLowerCase().trim();
    const res = await fetch(`${API_BASE}/district-vulnerability/${encodeURIComponent(distClean)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchDistrictVulnerability failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/district-vulnerability
 */
export async function fetchNationalVulnerability(): Promise<NationalVulnerabilityResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/district-vulnerability`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchNationalVulnerability failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/nisr/poverty
 */
export async function fetchPovertyEstimates(): Promise<SurveyIndicatorResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/nisr/poverty`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchPovertyEstimates failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/nisr/health-insurance
 */
export async function fetchHealthInsuranceEstimates(): Promise<SurveyIndicatorResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/nisr/health-insurance`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchHealthInsuranceEstimates failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/dashboard/overview
 */
export async function fetchDashboardOverview(): Promise<DashboardOverviewResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/dashboard/overview`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchDashboardOverview failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/dashboard/filters
 */
export async function fetchDashboardFilters(): Promise<DashboardFiltersResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/dashboard/filters`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchDashboardFilters failed:', err);
    return null;
  }
}

/**
 * POST /api/v1/calculations/policy-scenario
 */
export async function calculatePolicyScenario(
  payload: PolicyScenarioRequest
): Promise<PolicyScenarioResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/calculations/policy-scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      console.warn('[API] calculatePolicyScenario failed:', res.status, errData);
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn('[API] calculatePolicyScenario error:', err);
    return null;
  }
}

/**
 * GET /api/v1/nisr/sources
 */
export async function fetchNisrSources(): Promise<NisrSourcesResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/nisr/sources`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchNisrSources failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/nisr/financial-inclusion/national
 */
export async function fetchNationalFinancialInclusion(): Promise<NationalFinancialInclusionResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/nisr/financial-inclusion/national`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchNationalFinancialInclusion failed:', err);
    return null;
  }
}

/**
 * GET /api/v1/nisr/financial-inclusion/districts
 */
export async function fetchDistrictFinancialInclusion(): Promise<DistrictFinancialInclusionResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/nisr/financial-inclusion/districts`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchDistrictFinancialInclusion failed:', err);
    return null;
  }
}

// ------------------------------------------
// Auth & Profile Management
// ------------------------------------------

const TOKEN_STORAGE_KEY = 'imibereho_auth_token';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch (err) {
    console.warn('Failed to store token:', err);
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (err) {
    console.warn('Failed to clear token:', err);
  }
}

/**
 * POST /api/v1/auth/register
 */
export async function registerHousehold(
  payload: RegisterPayload
): Promise<{ success: boolean; data?: RegisterResponse; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      const msg = data.detail || (data.errors ? data.errors.map((e: { message: string }) => e.message).join(', ') : 'Registration failed');
      return { success: false, error: msg };
    }
    if (data.token) {
      setStoredToken(data.token);
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/**
 * POST /api/v1/auth/login
 */
export async function loginHousehold(
  payload: LoginPayload
): Promise<{ success: boolean; data?: LoginResponse; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      const msg = data.detail || 'Invalid phone/email or password';
      return { success: false, error: msg };
    }
    if (data.token) {
      setStoredToken(data.token);
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/**
 * GET /api/v1/user/profile
 */
export async function fetchUserProfile(token?: string): Promise<UserProfileResponse | null> {
  const authToken = token || getStoredToken();
  if (!authToken) return null;
  try {
    const res = await fetch(`${API_BASE}/user/profile`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) {
      if (res.status === 401) clearStoredToken();
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchUserProfile failed:', err);
    return null;
  }
}

/**
 * PATCH /api/v1/user/profile
 */
export async function updateUserProfile(
  patch: ProfilePatchPayload,
  token?: string
): Promise<UserProfileResponse | null> {
  const authToken = token || getStoredToken();
  if (!authToken) return null;
  try {
    const res = await fetch(`${API_BASE}/user/profile`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify(patch),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn('[API] updateUserProfile failed:', err);
    return null;
  }
}
