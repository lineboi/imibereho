import React, { useState } from 'react';
import type { Language } from '../../types';
import type { DistrictBenchmarkData } from '../../data/mockAdvisorData';
import {
  ADVISOR_TRANSLATIONS,
  getMarketBasketItems,
} from '../../data/mockAdvisorData';
import { ShoppingBasket, ChevronDown, ChevronUp, MapPin } from 'lucide-react';

interface MarketBasketDrawerProps {
  districtA: DistrictBenchmarkData;
  districtB: DistrictBenchmarkData;
  language: Language;
}

export const MarketBasketDrawer: React.FC<MarketBasketDrawerProps> = ({
  districtA,
  districtB,
  language,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const items = getMarketBasketItems(districtA.districtId, districtB.districtId);
  const filteredItems =
    activeCategory === 'all'
      ? items
      : items.filter((item) => item.category === activeCategory);

  return (
    <section
      aria-label="Itemized Local Market Basket Context"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-4 sm:p-6 shadow-xs flex flex-col gap-3.5 transition-all"
    >
      {/* Header with Toggle Button */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CEE4D6]">
            <ShoppingBasket className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-medium text-[#133A29]">
              {t.basketTitle}
            </h3>
            <p className="text-[11.5px] text-[#697B71]">
              {t.basketSub}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="py-1.5 px-3 rounded-xl border border-[#D5CFBF] hover:bg-[#F4EFE6] text-xs font-semibold text-[#254F3A] flex items-center gap-1.5 transition-colors cursor-pointer shrink-0"
        >
          <span>{isOpen ? t.hideBasketBtn : t.viewBasketBtn}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Expanded Content */}
      {isOpen && (
        <div className="flex flex-col gap-3 pt-3 border-t border-[#F0ECE4] animate-in fade-in duration-200">
          {/* Category Filter Chips */}
          <div className="flex items-center gap-1.5 flex-wrap pb-1">
            {['all', 'food', 'housing', 'transport', 'utilities'].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategory(cat)}
                className={`text-[11px] font-semibold py-1 px-3 rounded-full transition-all cursor-pointer capitalize ${
                  activeCategory === cat
                    ? 'bg-[#1E5E45] text-white shadow-2xs'
                    : 'bg-[#F2EFE8] text-[#55695D] hover:bg-[#E5E1D8]'
                }`}
              >
                {cat === 'all'
                  ? 'All Items'
                  : cat === 'food'
                  ? t.categoryFood
                  : cat === 'housing'
                  ? t.categoryHousing
                  : cat === 'transport'
                  ? t.categoryTransport
                  : t.categoryUtilities}
              </button>
            ))}
          </div>

          {/* Grid of Item Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="bg-[#FAF8F4] border border-[#E9E3D6] rounded-xl p-3.5 flex flex-col justify-between gap-2.5"
              >
                <div>
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#EAE4D7]">
                    <span className="font-bold text-xs sm:text-sm text-[#163D2B]">
                      {language === 'RW' ? item.nameRw : item.nameEn}
                    </span>
                    <span className="text-[10px] text-[#718478] bg-white border border-[#E0D9CB] px-2 py-0.5 rounded-full font-medium">
                      {language === 'RW' ? item.unitRw : item.unitEn}
                    </span>
                  </div>

                  {/* Price Comparison Side by Side */}
                  <div className="grid grid-cols-2 gap-2 pt-2">
                    <div className="flex items-start gap-1">
                      <MapPin className="w-3.5 h-3.5 text-[#1E5E45] shrink-0 mt-0.5" />
                      <div>
                        <span className="text-[10.5px] text-[#697B71] block">
                          {districtA.districtName}
                        </span>
                        <span className="font-bold text-sm text-[#143B2A]">
                          {item.districtACost}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-start gap-1">
                      <MapPin className="w-3.5 h-3.5 text-[#2B6047] shrink-0 mt-0.5" />
                      <div>
                        <span className="text-[10.5px] text-[#697B71] block">
                          {districtB.districtName}
                        </span>
                        <span className="font-bold text-sm text-emerald-800">
                          {item.districtBCost}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Insight Description */}
                <p className="text-[11px] text-[#55695D] leading-relaxed pt-2 border-t border-[#EDE7DB] italic">
                  {language === 'RW' ? item.insightRw : item.insightEn}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};
