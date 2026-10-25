export type Language = 'EN' | 'RW';

export type AppPage = 'landing' | 'tracker';

export type NavTab = 'tracker' | 'district_advisor' | 'resilience' | 'agro_swaps';

export interface District {
  id: string;
  name: string;
  province: string;
}

export interface HouseholdProfile {
  district: string;
  householdSize: string;
  monthlyIncome: string;
  currency: string;
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
