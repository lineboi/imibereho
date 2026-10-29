import React, { useState, useEffect } from 'react';
import {
  ExternalLink,
  AlertTriangle,
  User,
  Loader2,
  Check,
} from 'lucide-react';
import {
  calculatePolicyScenario,
  type PolicyScenarioResponse,
} from '../../services/api';
import type { DecisionMakerTab } from '../../types';

interface PolicySimulatorViewProps {
  onNavigateTab: (tab: DecisionMakerTab) => void;
  onOpenProfile: () => void;
}

export const PolicySimulatorView: React.FC<PolicySimulatorViewProps> = ({
  onNavigateTab,
  onOpenProfile,
}) => {
  const [instrument] = useState<string>('monthly_cash_support');
  const [incomeLossPct, setIncomeLossPct] = useState<number>(25);
  const [durationMonths, setDurationMonths] = useState<number>(3);
  const [supportPerHousehold, setSupportPerHousehold] = useState<number>(6000);
  const [eligibleHouseholds, setEligibleHouseholds] = useState<number>(1000);

  const [scenarioResult, setScenarioResult] = useState<PolicyScenarioResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Trigger calculation from backend
  useEffect(() => {
    let mounted = true;
    calculatePolicyScenario({
      instrument: 'monthly_cash_support',
      incomeLossPct,
      durationMonths,
      supportPerHouseholdMonthly: supportPerHousehold,
      eligibleHouseholds,
    })
      .then((res) => {
        if (!mounted) return;
        if (res) {
          setScenarioResult(res);
        }
      })
      .catch((err) => {
        console.warn('Simulation execution failed:', err);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [incomeLossPct, durationMonths, supportPerHousehold, eligibleHouseholds]);

  const budget = scenarioResult?.directTransferBudget ?? supportPerHousehold * durationMonths * eligibleHouseholds;
  const budgetMillions = (budget / 1000000).toFixed(0);
  const budgetFormula = `${(budget / 1000000).toFixed(1)}m = ${supportPerHousehold.toLocaleString()} x ${durationMonths} x ${eligibleHouseholds.toLocaleString()}`;

  const baselineIncome = scenarioResult?.baselineUsed.monthlyIncome ?? 180000;
  const baselineEssentials = scenarioResult?.baselineUsed.monthlyEssentials ?? 150432;
  const baselineSavings = scenarioResult?.baselineUsed.savings ?? 60000;

  const rows = scenarioResult?.comparison.rows;

  return (
    <div className="flex-1 bg-[#FAF8F4] min-h-screen text-stone-900 pb-20">
      {/* Top Header / Breadcrumbs Bar */}
      <div className="border-b border-stone-200/80 bg-white/70 backdrop-blur-sm sticky top-0 z-10 px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-medium text-stone-500 uppercase tracking-wider">
          <span>Decision-maker workspace</span>
          <span>/</span>
          <span className="text-stone-900 font-semibold">Simulator</span>
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
            Test a response. See the assumptions.
          </h1>
          <p className="text-stone-600 text-sm md:text-base mt-1.5">
            Compare a household income shock with a simple, time-bound support scenario.
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

        {/* Green Pill Badge */}
        <div>
          <span className="inline-block px-3 py-1 text-[11px] font-bold uppercase tracking-wider bg-emerald-100/80 text-emerald-900 border border-emerald-200 rounded-md">
            SCENARIO A: ILLUSTRATIVE · {supportPerHousehold.toLocaleString()} RWF / MONTH CASH TRANSFER · {durationMonths}-MONTH DURATION
          </span>
        </div>

        {/* Two-Column Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Define the response (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-stone-200 shadow-xs space-y-5">
            <h2 className="font-serif text-lg font-bold text-stone-900">
              Define the response
            </h2>

            {/* Policy Instrument */}
            <div className="space-y-1.5">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
                Policy Instrument
              </label>
              <select
                value={instrument}
                disabled
                className="w-full bg-stone-50 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800"
              >
                <option value="monthly_cash_support">Monthly cash support</option>
              </select>
            </div>

            {/* Side-by-Side: Income Loss & Duration */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
                  Income Loss
                </label>
                <select
                  value={incomeLossPct}
                  onChange={(e) => setIncomeLossPct(Number(e.target.value))}
                  className="w-full bg-stone-50 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20"
                >
                  <option value={10}>10%</option>
                  <option value={15}>15%</option>
                  <option value={20}>20%</option>
                  <option value={25}>25%</option>
                  <option value={30}>30%</option>
                  <option value={40}>40%</option>
                  <option value={50}>50%</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
                  Duration
                </label>
                <select
                  value={durationMonths}
                  onChange={(e) => setDurationMonths(Number(e.target.value))}
                  className="w-full bg-stone-50 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20"
                >
                  <option value={1}>1 month</option>
                  <option value={2}>2 months</option>
                  <option value={3}>3 months</option>
                  <option value={6}>6 months</option>
                  <option value={12}>12 months</option>
                </select>
              </div>
            </div>

            {/* Support per household / month */}
            <div className="space-y-1.5">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
                Support per household / month
              </label>
              <select
                value={supportPerHousehold}
                onChange={(e) => setSupportPerHousehold(Number(e.target.value))}
                className="w-full bg-stone-50 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20"
              >
                <option value={5000}>5,000 RWF</option>
                <option value={6000}>6,000 RWF</option>
                <option value={10000}>10,000 RWF</option>
                <option value={15000}>15,000 RWF</option>
                <option value={20000}>20,000 RWF</option>
                <option value={25000}>25,000 RWF</option>
                <option value={30000}>30,000 RWF</option>
                <option value={50000}>50,000 RWF</option>
              </select>
            </div>

            {/* Eligible synthetic households */}
            <div className="space-y-1.5">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
                Eligible synthetic households
              </label>
              <select
                value={eligibleHouseholds}
                onChange={(e) => setEligibleHouseholds(Number(e.target.value))}
                className="w-full bg-stone-50 border border-stone-200 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#123927]/20"
              >
                <option value={500}>500</option>
                <option value={1000}>1,000</option>
                <option value={2000}>2,000</option>
                <option value={5000}>5,000</option>
                <option value={10000}>10,000</option>
              </select>
            </div>

            {/* Common household starting point box */}
            <div className="bg-[#FAF8F4] p-4 rounded-xl border border-stone-200 space-y-2 text-xs">
              <span className="block text-[11px] font-bold text-stone-700">
                Common household starting point:
              </span>
              <div className="flex justify-between text-stone-600">
                <span>Monthly income:</span>
                <strong className="text-stone-900 font-mono">{baselineIncome.toLocaleString()} RWF</strong>
              </div>
              <div className="flex justify-between text-stone-600">
                <span>Monthly essentials:</span>
                <strong className="text-stone-900 font-mono">{baselineEssentials.toLocaleString()} RWF</strong>
              </div>
              <div className="flex justify-between text-stone-600">
                <span>Starting savings:</span>
                <strong className="text-stone-900 font-mono">{baselineSavings.toLocaleString()} RWF</strong>
              </div>
              <p className="text-[10px] text-stone-400 pt-2 border-t border-stone-200/80 leading-relaxed">
                Sample reference household baseline (Gasabo household of four, illustrative profile). Test a subsidy before policy decision-making.
              </p>
            </div>

            {/* Apply button */}
            <button
              disabled
              className="w-full py-2.5 px-4 bg-[#123927] text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 cursor-default shadow-xs"
            >
              <span>Comparison applied</span>
              <Check className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Right Column: Comparison Table & Analysis (7 cols) */}
          <div className="lg:col-span-7 space-y-5">
            {/* Top 2 Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-xs">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-stone-400">
                  Direct intervention budget
                </span>
                <div className="text-3xl font-serif font-bold text-stone-900 mt-1">
                  {budgetMillions}m <span className="text-lg font-normal text-stone-400">RWF</span>
                </div>
                <div className="text-[11px] text-stone-400 mt-1 font-mono">
                  {budgetFormula}
                </div>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-xs">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-stone-400">
                  Modelled monthly gap
                </span>
                <div className="text-3xl font-serif font-bold text-stone-900 mt-1">
                  0 <span className="text-lg font-normal text-stone-400">RWF</span>
                </div>
                <div className="text-[11px] text-emerald-800 mt-1 font-medium">
                  Net balance neutral with support
                </div>
              </div>
            </div>

            {/* Household Scenario Comparison Card */}
            <div className="bg-white rounded-2xl p-6 border border-stone-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-serif text-base font-bold text-stone-900">
                    Household scenario comparison
                  </h3>
                  <p className="text-xs text-stone-500">
                    Demo monthly household · Three-month horizon
                  </p>
                </div>
                <span className="text-xs font-mono font-bold bg-stone-100 text-stone-600 px-2 py-0.5 rounded">
                  RWF
                </span>
              </div>

              {isLoading && !rows ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 text-stone-400">
                  <Loader2 className="w-6 h-6 animate-spin text-[#123927]" />
                  <span className="text-xs">Computing policy engine numbers...</span>
                </div>
              ) : rows ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-stone-200 text-stone-500 font-semibold uppercase tracking-wider text-[10px]">
                        <th className="py-2.5 pr-2">PER HOUSEHOLD</th>
                        <th className="py-2.5 px-2 text-stone-600">Baseline</th>
                        <th className="py-2.5 px-2 text-stone-600">Shock only</th>
                        <th className="py-2.5 pl-2 text-stone-900 font-bold">Shock + support</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100 text-stone-800 font-mono">
                      <tr>
                        <td className="py-2.5 pr-2 font-sans font-medium text-stone-700">Income per month</td>
                        <td className="py-2.5 px-2">{rows.incomePerMonth.no_shock.toLocaleString()}</td>
                        <td className="py-2.5 px-2">{rows.incomePerMonth.shock_only.toLocaleString()}</td>
                        <td className="py-2.5 pl-2 font-semibold">{rows.incomePerMonth.shock_with_support.toLocaleString()}</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 pr-2 font-sans font-medium text-stone-700">Support per month</td>
                        <td className="py-2.5 px-2">{rows.supportPerMonth.no_shock.toLocaleString()}</td>
                        <td className="py-2.5 px-2">{rows.supportPerMonth.shock_only.toLocaleString()}</td>
                        <td className="py-2.5 pl-2 font-semibold text-emerald-800">+{supportPerHousehold.toLocaleString()}</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 pr-2 font-sans font-medium text-stone-700">Expenses per month</td>
                        <td className="py-2.5 px-2">{rows.expensesPerMonth.no_shock.toLocaleString()}</td>
                        <td className="py-2.5 px-2">{rows.expensesPerMonth.shock_only.toLocaleString()}</td>
                        <td className="py-2.5 pl-2 font-semibold">{rows.expensesPerMonth.shock_with_support.toLocaleString()}</td>
                      </tr>
                      <tr className="font-bold">
                        <td className="py-2.5 pr-2 font-sans text-stone-900">Net monthly balance</td>
                        <td className="py-2.5 px-2 text-emerald-800">+{rows.netMonthlyBalance.no_shock.toLocaleString()}</td>
                        <td className="py-2.5 px-2 text-rose-700">{rows.netMonthlyBalance.shock_only.toLocaleString()}</td>
                        <td className="py-2.5 pl-2 text-stone-900">{rows.netMonthlyBalance.shock_with_support.toLocaleString()}</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 pr-2 font-sans font-medium text-stone-700">Savings after 3 months</td>
                        <td className="py-2.5 px-2">{rows.savingsAfterHorizon.no_shock.toLocaleString()}</td>
                        <td className="py-2.5 px-2 text-rose-700">{rows.savingsAfterHorizon.shock_only.toLocaleString()}</td>
                        <td className="py-2.5 pl-2 font-semibold text-emerald-800">{rows.savingsAfterHorizon.shock_with_support.toLocaleString()}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              ) : null}

              <p className="text-[10px] text-stone-400 pt-3 border-t border-stone-100 leading-relaxed">
                Assumptions: Surpluses saved; gaps paid from savings; no interest; no debt; no administrative costs or leakages.
              </p>
            </div>

            {/* What this comparison says card (Mint Tint) */}
            <div className="bg-[#EDF5EC] border border-[#D5E6D4] rounded-2xl p-5 space-y-2">
              <h4 className="font-serif text-sm font-bold text-[#142d1f]">
                What this comparison says — and does not say
              </h4>
              <p className="text-xs text-stone-700 leading-relaxed">
                A {supportPerHousehold.toLocaleString()} RWF transfer covers part of the modelled monthly gap. Over {durationMonths} months, savings remain at {rows?.savingsAfterHorizon.shock_with_support.toLocaleString() ?? '31,704'} RWF instead of falling to {rows?.savingsAfterHorizon.shock_only.toLocaleString() ?? '13,704'} RWF.
              </p>
              <p className="text-[11px] text-stone-500 pt-1 leading-relaxed">
                This is a demonstration formula, not an evaluation of actual policy impact, program reach or macro-economic stimulus.
              </p>
            </div>
          </div>
        </div>

        {/* Tan Notice Banner */}
        <div className="bg-[#FAF3EA] border border-[#EBDDCB] rounded-xl px-4 py-3 text-xs text-[#7A5B36] flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 text-[#8B643A]" />
          <span>
            Budget excludes delivery and administration. Coverage, eligibility, local prices, and implementation capacity require independent field investigation.
          </span>
        </div>

        {/* Bottom Page Footer */}
        <div className="pt-4 text-center text-xs text-stone-400">
          Imibereho · Concept blueprint · Transparent methodology and evidence base accessible by certification.
        </div>
      </div>
    </div>
  );
};
