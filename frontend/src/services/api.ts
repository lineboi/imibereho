/**
 * Imibereho Backend API Client Service
 * Directly connects to FastAPI backend endpoints (/api/v1/...) via Vite proxy.
 */

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

export interface BudgetComparisonRequest {
  district: string;
  householdSize: number;
  plan: Array<{
    categoryCode: string;
    monthlyAmount: number;
  }>;
}

export interface BudgetComparisonResponse {
  district: {
    code: string;
    name: string;
  };
  householdSize: number;
  totalPlanned: number;
  totalBenchmark: number;
  netDifference: number;
  lines: Array<{
    categoryCode: string;
    plannedAmount: number;
    benchmarkAmount: number;
    difference: number;
  }>;
  meta: {
    isIllustrative: boolean;
    methodologyVersion: string;
  };
}

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

const API_BASE = '/api/v1';

/**
 * Check backend readiness (/ready)
 */
export async function checkBackendReadiness(): Promise<{ ready: boolean; status?: string }> {
  try {
    const res = await fetch('/ready');
    if (!res.ok) return { ready: false, status: `HTTP ${res.status}` };
    const data = await res.json();
    return { ready: data.status === 'ready', status: data.status };
  } catch (err) {
    return { ready: false, status: String(err) };
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
    console.warn('[API] fetchDistricts failed, falling back:', err);
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
    console.warn('[API] fetchExpenseCategories failed, falling back:', err);
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
    const res = await fetch(`${API_BASE}/budget-benchmarks?district=${encodeURIComponent(distClean)}&householdSize=${size}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchBudgetBenchmark failed:', err);
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
export async function calculateHouseholdShock(
  params: {
    monthlyIncome: number;
    monthlyEssentials: number;
    savings: number;
    incomeReductionPct: number;
    durationMonths: number;
  }
): Promise<HouseholdShockResponse | null> {
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
 * GET /api/v1/seasonal-swaps?district={district}&month={month}
 */
export async function fetchSeasonalSwaps(
  district: string,
  month: number
): Promise<SeasonalSwapApiResponse | null> {
  try {
    const distClean = district.toLowerCase().trim();
    const m = Math.max(1, Math.min(12, month));
    const res = await fetch(`${API_BASE}/seasonal-swaps?district=${encodeURIComponent(distClean)}&month=${m}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] fetchSeasonalSwaps failed:', err);
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
