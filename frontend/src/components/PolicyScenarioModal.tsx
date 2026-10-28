import React, { useState, useEffect } from 'react';
import { X, Building2, ShieldCheck, RefreshCw } from 'lucide-react';
import { calculatePolicyScenario, type PolicyScenarioResponse } from '../services/api';
import type { Language } from '../types';

interface PolicyScenarioModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: Language;
}

export const PolicyScenarioModal: React.FC<PolicyScenarioModalProps> = ({
  isOpen,
  onClose,
  language,
}) => {
  const [incomeLossPct, setIncomeLossPct] = useState<number>(25);
  const [durationMonths, setDurationMonths] = useState<number>(3);
  const [supportPerHousehold, setSupportPerHousehold] = useState<number>(15000);
  const [eligibleHouseholds, setEligibleHouseholds] = useState<number>(500);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<PolicyScenarioResponse | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    let active = true;

    calculatePolicyScenario({
      instrument: 'monthly_cash_support',
      incomeLossPct,
      durationMonths,
      supportPerHouseholdMonthly: supportPerHousehold,
      eligibleHouseholds,
    })
      .then((res) => {
        if (active && res) {
          setResult(res);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen, incomeLossPct, durationMonths, supportPerHousehold, eligibleHouseholds]);

  if (!isOpen) return null;

  const isRw = language === 'RW';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl bg-[#FAF8F5] rounded-2xl shadow-2xl border border-[#DDD7CE] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-[#1E5E45] px-6 py-4 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-[#C4E5D4]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-base leading-tight">
                  {isRw ? 'Igereranyo rya Politiki y’Inkunga' : 'Policy Cash Transfer Scenario Simulator'}
                </h3>
                <span className="text-[10px] bg-white/20 font-mono px-2 py-0.5 rounded-full">
                  POST /calculations/policy-scenario
                </span>
              </div>
              <p className="text-xs text-[#C4E5D4] mt-0.5">
                {isRw
                  ? 'Isuzuma ry’ingaruka z’inkunga y’amafaranga ku miryango yahuye n’ibiza'
                  : 'Simulate direct cash transfers to mitigate household income shocks'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-white/80 hover:text-white hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Controls Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 bg-white p-4 rounded-xl border border-[#E3DED4] shadow-xs">
            {/* Control 1: Income Loss */}
            <div>
              <label className="block text-xs font-bold text-[#35483D] mb-1.5">
                {isRw ? 'Igabanuka ry’injiza (%)' : 'Income Loss (%)'}
              </label>
              <select
                value={incomeLossPct}
                onChange={(e) => setIncomeLossPct(Number(e.target.value))}
                className="w-full text-xs font-semibold bg-[#FAF8F3] border border-[#D5CFC2] rounded-lg px-2.5 py-2 text-[#1E3025] focus:outline-none focus:ring-1 focus:ring-[#1E5E45]"
              >
                <option value={15}>15% Loss</option>
                <option value={25}>25% Loss (Baseline)</option>
                <option value={35}>35% Loss (Severe)</option>
                <option value={50}>50% Loss (Acute)</option>
              </select>
            </div>

            {/* Control 2: Duration */}
            <div>
              <label className="block text-xs font-bold text-[#35483D] mb-1.5">
                {isRw ? 'Igihe (Amezi)' : 'Duration (Months)'}
              </label>
              <select
                value={durationMonths}
                onChange={(e) => setDurationMonths(Number(e.target.value))}
                className="w-full text-xs font-semibold bg-[#FAF8F3] border border-[#D5CFC2] rounded-lg px-2.5 py-2 text-[#1E3025] focus:outline-none focus:ring-1 focus:ring-[#1E5E45]"
              >
                <option value={1}>1 Month</option>
                <option value={3}>3 Months</option>
                <option value={6}>6 Months</option>
                <option value={12}>12 Months</option>
              </select>
            </div>

            {/* Control 3: Monthly Support */}
            <div>
              <label className="block text-xs font-bold text-[#35483D] mb-1.5">
                {isRw ? 'Inkunga / Ukwezi (RWF)' : 'Monthly Support / HH'}
              </label>
              <select
                value={supportPerHousehold}
                onChange={(e) => setSupportPerHousehold(Number(e.target.value))}
                className="w-full text-xs font-semibold bg-[#FAF8F3] border border-[#D5CFC2] rounded-lg px-2.5 py-2 text-[#1E3025] focus:outline-none focus:ring-1 focus:ring-[#1E5E45]"
              >
                <option value={10000}>10,000 RWF</option>
                <option value={15000}>15,000 RWF</option>
                <option value={20000}>20,000 RWF</option>
                <option value={30000}>30,000 RWF</option>
              </select>
            </div>

            {/* Control 4: Eligible Households */}
            <div>
              <label className="block text-xs font-bold text-[#35483D] mb-1.5">
                {isRw ? 'Imiryango igenerwa' : 'Eligible Households'}
              </label>
              <select
                value={eligibleHouseholds}
                onChange={(e) => setEligibleHouseholds(Number(e.target.value))}
                className="w-full text-xs font-semibold bg-[#FAF8F3] border border-[#D5CFC2] rounded-lg px-2.5 py-2 text-[#1E3025] focus:outline-none focus:ring-1 focus:ring-[#1E5E45]"
              >
                <option value={100}>100 Households</option>
                <option value={500}>500 Households</option>
                <option value={1000}>1,000 Households</option>
                <option value={2500}>2,500 Households</option>
              </select>
            </div>
          </div>

          {/* Results Overview KPI Cards */}
          {result && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-[#FAFDFB] rounded-xl p-4 border border-[#CEE3D5] shadow-xs">
                <div className="text-[11px] font-bold text-[#4B6B59] uppercase tracking-wider">
                  {isRw ? 'Ingengo y’Imari Yose y’Inkunga' : 'Total Direct Transfer Budget'}
                </div>
                <div className="text-xl font-bold font-serif text-[#164835] mt-1">
                  {result.directTransferBudget.toLocaleString()} RWF
                </div>
                <div className="text-[11px] text-[#6E8075] mt-0.5">
                  {eligibleHouseholds} HH &times; {supportPerHousehold.toLocaleString()} RWF &times; {durationMonths} mo
                </div>
              </div>

              <div className="bg-[#FAFDFB] rounded-xl p-4 border border-[#CEE3D5] shadow-xs">
                <div className="text-[11px] font-bold text-[#4B6B59] uppercase tracking-wider">
                  {isRw ? 'Icyuho gisigaye ku kwezi' : 'Modelled Gap with Support'}
                </div>
                <div
                  className={`text-xl font-bold font-serif mt-1 ${
                    result.modelledMonthlyGapWithSupport === 0 ? 'text-[#1E5E45]' : 'text-amber-700'
                  }`}
                >
                  {result.modelledMonthlyGapWithSupport.toLocaleString()} RWF
                </div>
                <div className="text-[11px] text-[#6E8075] mt-0.5">
                  {result.modelledMonthlyGapWithSupport === 0
                    ? '100% Shock deficit covered by transfer'
                    : 'Partial buffer remaining deficit'}
                </div>
              </div>

              <div className="bg-[#FAFDFB] rounded-xl p-4 border border-[#CEE3D5] shadow-xs">
                <div className="text-[11px] font-bold text-[#4B6B59] uppercase tracking-wider">
                  {isRw ? 'Ikerekezo cy’Isuzumwa' : 'Simulation Horizon'}
                </div>
                <div className="text-xl font-bold font-serif text-[#164835] mt-1">
                  {result.horizonMonths} {isRw ? 'Amezi' : 'Months'}
                </div>
                <div className="text-[11px] text-[#6E8075] mt-0.5">
                  Monthly cash support instrument (BR-01)
                </div>
              </div>
            </div>
          )}

          {/* Comparison Table */}
          {result && (
            <div className="bg-white rounded-xl border border-[#E3DED4] overflow-hidden shadow-xs">
              <div className="px-4 py-3 bg-[#F7F5F0] border-b border-[#E3DED4] flex items-center justify-between">
                <span className="text-xs font-bold text-[#35483D] uppercase tracking-wider">
                  {isRw ? 'Igereranya ry’Inzira 3' : 'Side-by-Side Impact Comparison Table'}
                </span>
                {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#1E5E45]" />}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-[#FAF8F5] text-[#55695D] font-bold border-b border-[#E3DED4]">
                    <tr>
                      <th className="py-2.5 px-4">{isRw ? 'Ikipimo cy’Imari' : 'Financial Dimension'}</th>
                      <th className="py-2.5 px-4">{isRw ? 'Nta Kiza (Gisanzwe)' : 'No Shock (Baseline)'}</th>
                      <th className="py-2.5 px-4 text-amber-800">{isRw ? 'Ikiza Gusa (Nta Nkunga)' : 'Shock Only (No Help)'}</th>
                      <th className="py-2.5 px-4 text-[#1E5E45]">{isRw ? 'Ikiza + Inkunga' : 'Shock + Cash Support'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EDE9E1]">
                    <tr>
                      <td className="py-2.5 px-4 font-semibold text-[#243B2E]">
                        {isRw ? 'Injiza ku kwezi' : 'Income per Month'}
                      </td>
                      <td className="py-2.5 px-4 font-mono">{result.comparison.rows.incomePerMonth.no_shock.toLocaleString()} RWF</td>
                      <td className="py-2.5 px-4 font-mono text-amber-700">{result.comparison.rows.incomePerMonth.shock_only.toLocaleString()} RWF</td>
                      <td className="py-2.5 px-4 font-mono text-[#1E5E45] font-semibold">{result.comparison.rows.incomePerMonth.shock_with_support.toLocaleString()} RWF</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-semibold text-[#243B2E]">
                        {isRw ? 'Inkunga ya leta ku kwezi' : 'Cash Support per Month'}
                      </td>
                      <td className="py-2.5 px-4 font-mono">0 RWF</td>
                      <td className="py-2.5 px-4 font-mono text-amber-700">0 RWF</td>
                      <td className="py-2.5 px-4 font-mono text-[#1E5E45] font-bold">+{result.comparison.rows.supportPerMonth.shock_with_support.toLocaleString()} RWF</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-semibold text-[#243B2E]">
                        {isRw ? 'Amafaranga akenerwa ku kwezi' : 'Essential Expenses per Month'}
                      </td>
                      <td className="py-2.5 px-4 font-mono">{result.comparison.rows.expensesPerMonth.no_shock.toLocaleString()} RWF</td>
                      <td className="py-2.5 px-4 font-mono">{result.comparison.rows.expensesPerMonth.shock_only.toLocaleString()} RWF</td>
                      <td className="py-2.5 px-4 font-mono">{result.comparison.rows.expensesPerMonth.shock_with_support.toLocaleString()} RWF</td>
                    </tr>
                    <tr className="bg-[#FAFDFB]">
                      <td className="py-2.5 px-4 font-bold text-[#1E5E45]">
                        {isRw ? 'Uburinganire ku kwezi' : 'Net Monthly Balance'}
                      </td>
                      <td className="py-2.5 px-4 font-mono font-semibold text-[#1E5E45]">
                        +{result.comparison.rows.netMonthlyBalance.no_shock.toLocaleString()} RWF
                      </td>
                      <td className="py-2.5 px-4 font-mono font-semibold text-amber-700">
                        {result.comparison.rows.netMonthlyBalance.shock_only.toLocaleString()} RWF
                      </td>
                      <td className="py-2.5 px-4 font-mono font-bold text-[#1E5E45]">
                        {result.comparison.rows.netMonthlyBalance.shock_with_support >= 0 ? '+' : ''}
                        {result.comparison.rows.netMonthlyBalance.shock_with_support.toLocaleString()} RWF
                      </td>
                    </tr>
                    <tr className="bg-[#F2F7F4]">
                      <td className="py-2.5 px-4 font-bold text-[#143B2A]">
                        {isRw ? 'Ubwizigame nyuma y’igihe cy’ikiza' : 'Savings Buffer Remaining After Horizon'}
                      </td>
                      <td className="py-2.5 px-4 font-mono font-semibold">
                        {result.comparison.rows.savingsAfterHorizon.no_shock.toLocaleString()} RWF
                      </td>
                      <td className="py-2.5 px-4 font-mono font-bold text-red-700">
                        {result.comparison.rows.savingsAfterHorizon.shock_only.toLocaleString()} RWF
                      </td>
                      <td className="py-2.5 px-4 font-mono font-bold text-[#1E5E45]">
                        {result.comparison.rows.savingsAfterHorizon.shock_with_support.toLocaleString()} RWF
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Model Assumptions Chips */}
          {result && (
            <div className="bg-[#FAF8F3] p-4 rounded-xl border border-[#EBE7DF] text-xs text-[#55695D]">
              <div className="font-bold text-[#1E3025] mb-2 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#1E5E45]" />
                <span>{isRw ? 'Amategeko agenga iki cyitegererezo' : 'Official Model Assumptions (Concept v0.1)'}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {result.assumptions.map((ass) => (
                  <span key={ass} className="bg-white border border-[#DDD7CE] text-[#33463B] px-2 py-0.5 rounded-md font-mono text-[10.5px]">
                    {ass}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-[#F2EFE8] border-t border-[#DDD7CE] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[#55695D]">
            <span>FastAPI Policy Simulation Engine</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-[#1E5E45] hover:bg-[#164835] text-white font-semibold rounded-xl text-xs shadow-xs cursor-pointer transition-colors"
          >
            {isRw ? 'Funga' : 'Close Simulator'}
          </button>
        </div>
      </div>
    </div>
  );
};
