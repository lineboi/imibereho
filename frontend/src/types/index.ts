export type Language = 'EN' | 'RW';

export type UserRole = 'citizen' | 'decision_maker';

export type AppPage = 'landing' | 'tracker' | 'decision_maker';

export type NavTab = 'tracker' | 'district_advisor' | 'resilience' | 'agro_swaps';

export type DecisionMakerTab =
  | 'macro_overview'
  | 'district_heatmap'
  | 'policy_simulator'
  | 'data_methodology';

export interface District {
  id: string;
  name: string;
  province: string;
}

export interface HouseholdProfile {
  id?: string;
  district: string;
  householdSize: string;
  monthlyIncome: string;
  currency: string;
  plannedEssentials?: number | null;
  savingsBuffer?: number | null;
  preferredLanguage?: 'EN' | 'RW';
  role?: UserRole;
  updatedAt?: string;
}

export interface ExpenseItem {
  id: string;
  title: string;
  category: string;
  note: string;
  amount: number;
  iconType: 'food' | 'transport' | 'utilities' | 'other';
  date?: string;
}

export interface IncomeItem {
  id: string;
  source: string;
  category: string;
  amount: number;
  date: string;
  note?: string;
}

export interface MonthlyBudgetPlan {
  monthlyIncome: number;
  plannedExpenses: number;
  leftAfterPlan: number;
  demoSavings: number;
  month: string;
  district: string;
  householdSize: string;
}

export interface DailyBudgetHealth {
  safeToSpendDaily: number;
  spentToday: number;
  remainingSafeToday: number;
  daysRemainingInMonth: number;
  status: 'safe' | 'caution' | 'exceeded';
}

export interface SimulationSummary {
  profile: HouseholdProfile;
  resilienceScoreEstimate: number;
  primaryExpensesCategory: string;
  recommendedEmergencyFund: string;
  notes: string[];
}
