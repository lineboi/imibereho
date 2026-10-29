import React, { useState, useEffect } from 'react';
import type { Language } from '../../types';
import { AGRO_SWAPS_TRANSLATIONS } from '../../data/mockAgroSwapsData';
import { fetchShoppingChecklist, type ShoppingChecklistResponse } from '../../services/api';
import { ShoppingBag, CheckSquare, Square, Copy, Check, Sparkles } from 'lucide-react';

interface SmartMarketChecklistProps {
  district: string;
  language: Language;
}

interface ChecklistItem {
  id: string;
  nameEn: string;
  nameRw: string;
  qtyEn: string;
  qtyRw: string;
  estPrice: number;
  isSeasonalSwap: boolean;
  checked: boolean;
}

export const SmartMarketChecklist: React.FC<SmartMarketChecklistProps> = ({
  district,
  language,
}) => {
  const t = AGRO_SWAPS_TRANSLATIONS[language];
  const [copied, setCopied] = useState<boolean>(false);
  const [checklistApi, setChecklistApi] = useState<ShoppingChecklistResponse | null>(null);
  const [items, setItems] = useState<ChecklistItem[]>([
    {
      id: 'item-1',
      nameEn: 'Fresh Sweet Potatoes (Ibijumba)',
      nameRw: 'Ibijumba byera mu gihugu',
      qtyEn: '3 kg demo basket',
      qtyRw: 'Ibiro 3',
      estPrice: 2400,
      isSeasonalSwap: true,
      checked: false,
    },
    {
      id: 'item-2',
      nameEn: 'Local Red Kidney Beans (Ibishyimbo)',
      nameRw: 'Ibishyimbo bitukura by’iwacu',
      qtyEn: '2 kg demo basket',
      qtyRw: 'Ibiro 2',
      estPrice: 1700,
      isSeasonalSwap: true,
      checked: false,
    },
    {
      id: 'item-3',
      nameEn: 'Fresh Amaranth Greens (Dodo)',
      nameRw: 'Imboga z’icyatsi za Dodo',
      qtyEn: '3 fresh bundles',
      qtyRw: 'Ibinyita 3 binini',
      estPrice: 650,
      isSeasonalSwap: true,
      checked: false,
    },
    {
      id: 'item-4',
      nameEn: 'Cooking Tomatoes & Red Onions',
      nameRw: 'Inyanya n’ibitunguru byo guteka',
      qtyEn: '1 kg market basket',
      qtyRw: 'Ikiro 1',
      estPrice: 1000,
      isSeasonalSwap: false,
      checked: false,
    },
    {
      id: 'item-5',
      nameEn: 'Local Ripe Avocados (Avoka)',
      nameRw: 'Amavoka meza yo kumeza',
      qtyEn: '4 pieces',
      qtyRw: 'Ibinini 4',
      estPrice: 500,
      isSeasonalSwap: false,
      checked: false,
    },
  ]);

  useEffect(() => {
    let active = true;
    fetchShoppingChecklist(district, 4).then((res) => {
      if (!active || !res) return;
      setChecklistApi(res);
      if (res.items && res.items.length > 0) {
        setItems(
          res.items.map((it, idx) => ({
            id: `api-item-${idx}`,
            nameEn: it.name,
            nameRw: it.name,
            qtyEn: it.quantity,
            qtyRw: it.quantity,
            estPrice: it.estPrice,
            isSeasonalSwap: it.isSwap,
            checked: false,
          }))
        );
      }
    });
    return () => {
      active = false;
    };
  }, [district]);

  const toggleItem = (id: string) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, checked: !item.checked } : item))
    );
  };

  const totalEstPrice = checklistApi?.totalEstimatedBasket ?? items.reduce((sum, item) => sum + item.estPrice, 0);
  const unoptimizedBasketPrice = checklistApi?.unoptimizedBasket ?? 8650;
  const basketSavings = checklistApi?.estimatedSavings ?? Math.max(0, unoptimizedBasketPrice - totalEstPrice);

  const handleCopyList = () => {
    const header =
      language === 'RW'
        ? `🛒 Urutonde rwo Guhaha ku Isoko (${district}) - Imibereho:\n`
        : `🛒 Smart Market Shopping List (${district}) - Imibereho:\n`;
    const lines = items.map((item) => {
      const name = language === 'RW' ? item.nameRw : item.nameEn;
      const qty = language === 'RW' ? item.qtyRw : item.qtyEn;
      return `• [${item.checked ? '✓' : ' '}] ${name} (${qty}) ~ ${item.estPrice.toLocaleString()} RWF`;
    });
    const footer = `\nTotal Estimated: ${totalEstPrice.toLocaleString()} RWF (Saved ~${basketSavings.toLocaleString()} RWF with Seasonal Swaps)`;
    const textToCopy = `${header}${lines.join('\n')}${footer}`;

    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="bg-white rounded-2xl border border-[#E5DFD4] shadow-xs p-4 sm:p-5 flex flex-col gap-3.5">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#EBF4EE] text-[#1E5E45] flex items-center justify-center shrink-0 border border-[#CFE4D7]">
            <ShoppingBag className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-normal text-[#123927]">
              {t.smartMarketChecklistTitle}
            </h3>
            <p className="text-[12px] text-[#55695D] leading-tight">
              {t.smartMarketChecklistSub}
            </p>
          </div>
        </div>

        {/* Copy button */}
        <button
          type="button"
          onClick={handleCopyList}
          className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-[#D5CFBF] bg-[#FAF8F3] hover:bg-[#F2ECE0] text-[#345241] cursor-pointer transition-colors shrink-0"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-[#1E5E45]" />
              <span className="text-[#1E5E45]">{t.copiedNotice}</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>{t.copyChecklistBtn}</span>
            </>
          )}
        </button>
      </div>

      {/* Interactive Items List */}
      <div className="flex flex-col gap-2 pt-1">
        {items.map((item) => {
          return (
            <div
              key={item.id}
              onClick={() => toggleItem(item.id)}
              className={`p-2.5 rounded-xl border flex items-center justify-between gap-3 cursor-pointer transition-all ${
                item.checked
                  ? 'bg-[#F4F9F6] border-[#D0E5D9] opacity-75'
                  : 'bg-[#FAF8F3] border-[#E8E2D7] hover:border-[#CFE0D6]'
              }`}
            >
              <div className="flex items-center gap-2.5 flex-1 min-w-0">
                <div className="text-[#1E5E45] shrink-0">
                  {item.checked ? (
                    <CheckSquare className="w-4 h-4" />
                  ) : (
                    <Square className="w-4 h-4 text-[#8BA094]" />
                  )}
                </div>
                <div className="truncate">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-[13px] font-medium truncate ${
                        item.checked
                          ? 'line-through text-[#6F8177]'
                          : 'text-[#1B3F2E]'
                      }`}
                    >
                      {language === 'RW' ? item.nameRw : item.nameEn}
                    </span>
                    {item.isSeasonalSwap && (
                      <span className="bg-[#E7F3EC] text-[#1E5E45] text-[10px] font-semibold px-1.5 py-0.2 rounded shrink-0">
                        Swap
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-[#718278] block">
                    {language === 'RW' ? item.qtyRw : item.qtyEn}
                  </span>
                </div>
              </div>

              <span className="text-xs font-semibold text-[#183928] tabular-nums shrink-0">
                {item.estPrice.toLocaleString()} RWF
              </span>
            </div>
          );
        })}
      </div>

      {/* Total & Savings Summary Bar */}
      <div className="bg-[#FAF8F4] border border-[#E6E0D5] rounded-xl p-3 flex items-center justify-between">
        <div>
          <span className="text-[11px] text-[#5A6F62] uppercase tracking-wider block font-medium">
            {t.checklistTotalLabel}
          </span>
          <span className="font-serif text-lg font-bold text-[#143B2A] tabular-nums">
            {totalEstPrice.toLocaleString()} RWF
          </span>
        </div>

        <div className="text-right">
          <span className="bg-[#EBF4EE] text-[#1E5E45] text-[11px] font-bold px-2 py-0.5 rounded-full inline-flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            <span>-{basketSavings.toLocaleString()} RWF saved</span>
          </span>
          <span className="text-[10.5px] text-[#728379] block mt-0.5">
            vs. non-seasonal basket
          </span>
        </div>
      </div>
    </div>
  );
};
