import React, { useState, useEffect } from 'react';
import { X, BookOpen, ExternalLink, Check, Copy, FileText, Shield } from 'lucide-react';
import { fetchNisrSources, type NisrSourceItem } from '../services/api';
import type { Language } from '../types';

interface SourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: Language;
}

export const SourcesModal: React.FC<SourcesModalProps> = ({
  isOpen,
  onClose,
  language,
}) => {
  const [sources, setSources] = useState<NisrSourceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    fetchNisrSources()
      .then((res) => {
        if (active && res?.items) {
          setSources(res.items);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const isRw = language === 'RW';

  const copyCitation = (src: NisrSourceItem) => {
    navigator.clipboard.writeText(src.citation);
    setCopiedId(src.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl bg-[#FAF8F5] rounded-2xl shadow-2xl border border-[#DDD7CE] overflow-hidden flex flex-col max-h-[88vh]">
        {/* Header */}
        <div className="bg-[#1E5E45] px-6 py-4 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-[#C4E5D4]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-base leading-tight">
                  {isRw ? 'Inkomoko y’Imibare n’Ubushakashatsi' : 'Official Statistics Provenance & Data Sources'}
                </h3>
                <span className="text-[10px] bg-white/20 font-mono px-2 py-0.5 rounded-full">
                  GET /nisr/sources
                </span>
              </div>
              <p className="text-xs text-[#C4E5D4] mt-0.5">
                {isRw
                  ? 'Ibyegeranyo bya NISR, Access to Finance Rwanda n’ibipimo by’igihugu'
                  : 'NISR EICV7 2023/24, FinScope 2024 & SAS 2025 Surveys'}
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

        {/* Content list */}
        <div className="p-6 overflow-y-auto space-y-4">
          {loading ? (
            <div className="text-center py-10 text-xs text-[#63776A]">
              Loading official survey citations from NISR catalog...
            </div>
          ) : (
            sources.map((src) => (
              <div
                key={src.id}
                className="bg-white rounded-xl p-5 border border-[#E3DED4] shadow-xs space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="font-bold text-sm text-[#183628] leading-snug">
                      {src.title}
                    </h4>
                    <div className="text-xs text-[#526659] mt-0.5">
                      <strong>Publisher:</strong> {src.publisher} ({src.publicationDate})
                      {src.sponsors ? ` · Sponsors: ${src.sponsors}` : ''}
                    </div>
                  </div>
                  <span className="text-[10.5px] font-mono bg-[#EAF2ED] text-[#1E5E45] px-2 py-0.5 rounded-md shrink-0">
                    {src.surveyRound}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-[#FAF8F3] p-3 rounded-lg border border-[#EDE8DE]">
                  <div>
                    <span className="text-[#6D8074]">Sample Size: </span>
                    <strong className="text-[#1E3025]">{src.sampleSize?.toLocaleString()} units</strong>
                  </div>
                  <div>
                    <span className="text-[#6D8074]">Lowest Geography: </span>
                    <strong className="text-[#1E3025]">{src.lowestPublishedGeography}</strong>
                  </div>
                  {src.fieldworkPeriod && (
                    <div className="sm:col-span-2">
                      <span className="text-[#6D8074]">Fieldwork: </span>
                      <span className="text-[#1E3025]">{src.fieldworkPeriod}</span>
                    </div>
                  )}
                  <div className="sm:col-span-2 text-[11px] text-[#63776A] mt-1 italic">
                    {src.notes}
                  </div>
                </div>

                {/* Citation & Action links */}
                <div className="pt-2 border-t border-[#ECE7DE] flex flex-wrap items-center justify-between gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => copyCitation(src)}
                    className="flex items-center gap-1.5 text-[#1E5E45] hover:text-[#143B2A] font-semibold cursor-pointer"
                  >
                    {copiedId === src.id ? (
                      <Check className="w-3.5 h-3.5 text-[#1E5E45]" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span>{copiedId === src.id ? 'Copied Citation' : 'Copy Citation'}</span>
                  </button>

                  <div className="flex items-center gap-3">
                    {src.documentUrl && (
                      <a
                        href={src.documentUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-[#2A6E50] hover:underline"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Document</span>
                      </a>
                    )}
                    {src.catalogUrl && (
                      <a
                        href={src.catalogUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-[#2A6E50] hover:underline font-semibold"
                      >
                        <span>NISR Catalog</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-[#F2EFE8] border-t border-[#DDD7CE] flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-[#55695D]">
            <Shield className="w-3.5 h-3.5 text-[#1E5E45]" />
            <span>National Institute of Statistics of Rwanda (NISR) Official Open Data</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-[#1E5E45] hover:bg-[#164835] text-white font-semibold rounded-xl text-xs shadow-xs cursor-pointer transition-colors"
          >
            {isRw ? 'Funga' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
