import React from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';
import { ShieldCheck, X, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';

interface SimulatorPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  districtA: DistrictBenchmarkData;
  districtB: DistrictBenchmarkData;
  householdSize: string;
  language: Language;
  onProceedToTracker: () => void;
}

export const SimulatorPreviewModal: React.FC<SimulatorPreviewModalProps> = ({
  isOpen,
  onClose,
  districtA,
  districtB,
  householdSize,
  language,
  onProceedToTracker,
}) => {
  if (!isOpen) return null;

  const t = ADVISOR_TRANSLATIONS[language];
  const diff = districtB.baselineTotal - districtA.baselineTotal;
  const isSavings = diff < 0;
  const absDiff = Math.abs(diff);

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0F291E]/50 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="bg-[#FAF8F4] border border-[#E2DBD0] rounded-3xl max-w-lg w-full p-5 sm:p-7 shadow-2xl flex flex-col gap-5 relative">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-5 right-5 text-[#63756A] hover:text-[#183928] p-1.5 rounded-full hover:bg-[#EFEAE1] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header with Icon */}
        <div className="flex items-start gap-3.5 pr-8">
          <div className="w-10 h-10 rounded-2xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-serif text-xl sm:text-2xl font-normal text-[#123927]">
              {t.modalTitle}
            </h3>
            <p className="text-xs sm:text-[13px] text-[#55695E] mt-1 leading-relaxed">
              {t.modalSub}
            </p>
          </div>
        </div>

        {/* Plan Snapshot Card */}
        <div className="bg-white rounded-2xl border border-[#E4DFD5] p-4 flex flex-col gap-3 shadow-2xs">
          <div className="flex items-center justify-between pb-2.5 border-b border-[#F0EBE2] text-xs">
            <span className="text-[#65796E] font-medium">Selected Configuration</span>
            <span className="bg-[#E4ECE5] text-[#244E38] text-[11px] font-bold px-2 py-0.5 rounded-full">
              {householdSize}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 divide-x divide-[#EFECE5]">
            <div>
              <span className="text-[11px] text-[#718478] block">{districtA.districtName} (Baseline)</span>
              <span className="font-serif text-lg font-bold text-[#143B2A]">
                {districtA.baselineTotal.toLocaleString()} RWF
              </span>
            </div>
            <div className="pl-3">
              <span className="text-[11px] text-[#718478] block">{districtB.districtName} (Comparison)</span>
              <span className="font-serif text-lg font-bold text-emerald-800">
                {districtB.baselineTotal.toLocaleString()} RWF
              </span>
            </div>
          </div>

          <div className="bg-[#FAF8F3] rounded-xl p-3 border border-[#EAE4D9] flex items-start gap-2.5 text-xs text-[#3E5246]">
            <Zap className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-[#143B2A] block">
                {isSavings
                  ? `Simulated Buffer Impact: +${absDiff.toLocaleString()} RWF/month`
                  : `Simulated Urban Premium: +${absDiff.toLocaleString()} RWF/month`}
              </span>
              <span className="text-[11.5px] text-[#5C7063] leading-relaxed block mt-0.5">
                {isSavings
                  ? `Living in ${districtB.districtName} frees up ${absDiff.toLocaleString()} RWF each month for family savings, allowing a 3-month emergency buffer to be accumulated 40% faster.`
                  : `Living in ${districtB.districtName} requires an additional ${absDiff.toLocaleString()} RWF monthly. Budget discipline and emergency savings become more crucial.`}
              </span>
            </div>
          </div>
        </div>

        {/* Simulated Shocks Ready checklist */}
        <div className="flex flex-col gap-1.5 text-xs text-[#4F6256]">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Clinic emergency test (-25,000 RWF shock)</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Dry season vegetable price surge (+15% food expense)</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-2.5 pt-2">
          <button
            type="button"
            onClick={onProceedToTracker}
            className="w-full sm:flex-1 py-3 px-4 rounded-xl bg-[#1E5E45] hover:bg-[#164935] text-white text-xs sm:text-sm font-semibold transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>{language === 'RW' ? 'Komeza ku Ibarura rya Buri Munsi' : 'Carry to Daily Tracker'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="w-full sm:w-auto py-3 px-5 rounded-xl border border-[#D5CFBF] hover:bg-[#EFEAE0] text-[#4A5D51] text-xs sm:text-sm font-medium transition-colors cursor-pointer"
          >
            {t.modalBtnCancel}
          </button>
        </div>
      </div>
    </div>
  );
};
