import React, { useState } from 'react';
import {
  ExternalLink,
  AlertTriangle,
  User,
  Calculator,
  Database,
  CheckSquare,
  Square,
} from 'lucide-react';
import type { DecisionMakerTab } from '../../types';

interface DataMethodologyViewProps {
  onNavigateTab: (tab: DecisionMakerTab) => void;
  onOpenProfile: () => void;
}

export const DataMethodologyView: React.FC<DataMethodologyViewProps> = ({
  onNavigateTab,
  onOpenProfile,
}) => {
  const [checklist, setChecklist] = useState<Record<string, boolean>>({
    governance: false,
    codesign: false,
    weights: false,
    outreach: false,
  });

  const toggleCheck = (key: string) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex-1 bg-[#FAF8F4] min-h-screen text-stone-900 pb-20">
      {/* Top Header / Breadcrumbs Bar */}
      <div className="border-b border-stone-200/80 bg-white/70 backdrop-blur-sm sticky top-0 z-10 px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-medium text-stone-500 uppercase tracking-wider">
          <span>Decision-maker workspace</span>
          <span>/</span>
          <span className="text-stone-900 font-semibold">Methodology</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigateTab('policy_simulator')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold tracking-wide uppercase text-[#123927] hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200/60 rounded-md transition-colors cursor-pointer"
          >
            <span>Simulator Workspace</span>
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
            Know what is behind every number.
          </h1>
          <p className="text-stone-600 text-sm md:text-base mt-1.5">
            A transparent prototype contract: what is illustrative, how calculations work and what remains unvalidated.
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
            CONCEPT METHOD V0.1 · Baseline trends: Top-level indicators external to public core
          </span>
        </div>

        {/* Two-Column Methodology Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Readable Calculations Card */}
            <div className="bg-white rounded-2xl p-6 border border-stone-200 shadow-xs space-y-5">
              <div className="flex items-center gap-2">
                <Calculator className="w-4 h-4 text-[#123927]" />
                <h2 className="font-serif text-lg font-bold text-stone-900">
                  Readable calculations, visible assumptions
                </h2>
              </div>

              {/* Items List */}
              <div className="space-y-4 text-xs">
                {/* Item 1 */}
                <div className="p-3.5 bg-stone-50 rounded-xl border border-stone-200/80 space-y-1">
                  <div className="font-bold text-stone-900 text-xs">
                    Monthly household balance
                  </div>
                  <div className="text-stone-600 font-mono text-[11px] leading-relaxed">
                    Income - essentials = remainder. Demo baseline: 180,000 - 150,432 = 29,568 RWF
                  </div>
                </div>

                {/* Item 2 */}
                <div className="p-3.5 bg-stone-50 rounded-xl border border-stone-200/80 space-y-1">
                  <div className="font-bold text-stone-900 text-xs">
                    Shock and savings runway
                  </div>
                  <div className="text-stone-600 font-mono text-[11px] leading-relaxed">
                    (Income x (1 - 25%)) - 144,344 (MO-102) = -9,344 monthly gap. Runway = 60,000 / 9,344 = 6.4 months if unchanged.
                  </div>
                </div>

                {/* Item 3 */}
                <div className="p-3.5 bg-stone-50 rounded-xl border border-stone-200/80 space-y-1">
                  <div className="font-bold text-stone-900 text-xs">
                    Provisional vulnerability index (0-100)
                  </div>
                  <div className="text-stone-600 font-mono text-[11px] leading-relaxed">
                    40% income instability + 40% essential cost pressure + 20% low-buffer exposure, scaled and inverted to 0-100 so that a higher value means greater demo vulnerability.
                  </div>
                </div>
              </div>

              <p className="text-[11px] text-stone-500 pt-3 border-t border-stone-100 leading-relaxed">
                Weights, normalisation and formulas are exposed above so researchers can inspect the method. Every assumption is accessible, modifiable, and verifiable.
              </p>
            </div>

            {/* Data Needs Before Production Card */}
            <div className="bg-white rounded-2xl p-6 border border-stone-200 shadow-xs space-y-4">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[#123927]" />
                <h3 className="font-serif text-base font-bold text-stone-900">
                  Data needs before production
                </h3>
              </div>
              <p className="text-xs text-stone-500">
                Candidate input layer (any NISR dataset not been validated, duplicated or integrated):
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-stone-200 text-stone-500 font-semibold uppercase tracking-wider text-[10px]">
                      <th className="py-2.5 pr-2">CANDIDATE</th>
                      <th className="py-2.5 px-2">ILLUSTRATIVE SOURCE</th>
                      <th className="py-2.5 pl-2 text-right">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100 text-stone-700">
                    <tr>
                      <td className="py-2.5 pr-2 font-medium text-stone-900">
                        Household income benchmark
                      </td>
                      <td className="py-2.5 px-2 text-stone-500">
                        National household survey microdata
                      </td>
                      <td className="py-2.5 pl-2 text-right">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                          Not connected
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-2 font-medium text-stone-900">
                        Essential basket levels
                      </td>
                      <td className="py-2.5 px-2 text-stone-500">
                        District household expenditure surveys
                      </td>
                      <td className="py-2.5 pl-2 text-right">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
                          To confirm
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-2 font-medium text-stone-900">
                        Sector indicators
                      </td>
                      <td className="py-2.5 px-2 text-stone-500">
                        Agro-socio indicators at local markets
                      </td>
                      <td className="py-2.5 pl-2 text-right">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
                          To confirm
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-2 font-medium text-stone-900">
                        Disaster risk incidence
                      </td>
                      <td className="py-2.5 px-2 text-stone-500">
                        Local agricultural hazards review
                      </td>
                      <td className="py-2.5 pl-2 text-right">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-200">
                          Not validated
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Column (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Exploration Card (Mint Tint) */}
            <div className="bg-[#EDF5EC] border border-[#D5E6D4] rounded-2xl p-6 space-y-4 shadow-xs">
              <h3 className="font-serif text-base font-bold text-[#142d1f]">
                Use for exploration, not decisions.
              </h3>
              <p className="text-xs text-stone-700 leading-relaxed">
                The 3,000-household synthetic monthly series, and district scores are synthetic. They carry no coefficient of representation or confidence intervals.
              </p>

              <div className="space-y-2 pt-2 border-t border-[#D5E6D4]">
                <span className="block text-xs font-bold text-stone-900">
                  Important limitations:
                </span>
                <ul className="space-y-1.5 text-xs text-stone-700 list-disc list-inside">
                  <li>No macro-liquidity effects are modeled.</li>
                  <li>No observational behavioral shifts.</li>
                  <li>Average values hide intra-district variation.</li>
                  <li>Seasonality and food shocks are uncertain.</li>
                  <li>Delivery fees and delivery costs not added.</li>
                </ul>
              </div>
            </div>

            {/* Before This Goes Live Card */}
            <div className="bg-white rounded-2xl p-6 border border-stone-200 shadow-xs space-y-4">
              <h3 className="font-serif text-base font-bold text-stone-900">
                Before this goes live
              </h3>

              <div className="space-y-2.5">
                {[
                  { id: 'governance', text: 'Confirm local open balance data governance' },
                  { id: 'codesign', text: 'Co-design indicators with NISR/NGOs' },
                  { id: 'weights', text: 'Review indexing weights and uncertainty' },
                  { id: 'outreach', text: 'Test language, accessibility, and outreach' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => toggleCheck(item.id)}
                    className="w-full flex items-center gap-2.5 text-xs text-stone-700 hover:text-stone-900 text-left py-1 cursor-pointer"
                  >
                    {checklist[item.id] ? (
                      <CheckSquare className="w-4 h-4 text-[#123927] shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-stone-400 shrink-0" />
                    )}
                    <span>{item.text}</span>
                  </button>
                ))}
              </div>

              <p className="text-[11px] text-stone-400 pt-3 border-t border-stone-100 leading-relaxed">
                Every component is subject to rigorous protocol (NISR). Citizen privacy, data provenance, and public trust remain central.
              </p>
            </div>
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
