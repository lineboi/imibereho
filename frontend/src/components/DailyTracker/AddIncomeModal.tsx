import React, { useState } from 'react';
import type { IncomeItem, Language } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import { X, Plus, Wallet, Smartphone, Briefcase, ShoppingCart } from 'lucide-react';

interface AddIncomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddIncome: (income: Omit<IncomeItem, 'id'>) => void;
  language: Language;
}

export const AddIncomeModal: React.FC<AddIncomeModalProps> = ({
  isOpen,
  onClose,
  onAddIncome,
  language,
}) => {
  const t = TRACKER_TRANSLATIONS[language];
  const [source, setSource] = useState('');
  const [category, setCategory] = useState<'Mobile Money' | 'Day Wage' | 'Market Sales' | 'Side Gig'>('Mobile Money');
  const [note, setNote] = useState('');
  const [amount, setAmount] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const numAmount = parseInt(amount.replace(/[^0-9]/g, ''), 10);
    if (!source.trim() || isNaN(numAmount) || numAmount <= 0) return;

    const todayDateStr = new Intl.DateTimeFormat(language === 'RW' ? 'rw-RW' : 'en-US', {
      day: 'numeric',
      month: 'short',
    }).format(new Date());

    onAddIncome({
      source: source.trim(),
      category,
      note: note.trim() || 'Income received',
      amount: numAmount,
      date: todayDateStr,
    });

    setSource('');
    setNote('');
    setAmount('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg bg-[#FAF8F4] rounded-2xl shadow-2xl border border-[#DDD7CE] overflow-hidden">
        {/* Header */}
        <div className="bg-[#1E5E45] text-white px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
              <Wallet className="w-4 h-4 text-[#C6ECD6]" />
            </div>
            <div>
              <h3 className="font-semibold text-base">{t.modalIncomeTitle}</h3>
              <p className="text-xs text-[#B2D8C3]">{t.modalIncomeSub}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4">
          {/* Source name */}
          <div>
            <label className="block text-xs font-semibold text-[#1A2D23] mb-1">
              {t.incomeSourceLabel}
            </label>
            <input
              type="text"
              required
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="e.g. MoMo from brother, Daily casual labor, Banana harvest sale"
              className="w-full bg-white border border-[#DDD7CE] rounded-xl px-3.5 py-2 text-sm text-[#1A2D23] focus:border-[#1E5E45] focus:ring-2 focus:ring-[#1E5E45]/15 outline-none"
            />
          </div>

          {/* Category Selector */}
          <div>
            <label className="block text-xs font-semibold text-[#1A2D23] mb-1">
              {t.incomeCategoryLabel}
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { label: 'Mobile Money', icon: <Smartphone className="w-3.5 h-3.5" /> },
                { label: 'Day Wage', icon: <Briefcase className="w-3.5 h-3.5" /> },
                { label: 'Market Sales', icon: <ShoppingCart className="w-3.5 h-3.5" /> },
                { label: 'Side Gig', icon: <Wallet className="w-3.5 h-3.5" /> },
              ].map((cat) => (
                <button
                  key={cat.label}
                  type="button"
                  onClick={() => setCategory(cat.label as typeof category)}
                  className={`py-2 px-2 rounded-xl text-xs font-medium flex flex-col items-center gap-1 border transition-all cursor-pointer ${
                    category === cat.label
                      ? 'bg-[#EBF3ED] text-[#1E5E45] border-[#1E5E45] font-semibold'
                      : 'bg-white text-[#52635A] border-[#DDD7CE] hover:bg-[#F3EFE7]'
                  }`}
                >
                  {cat.icon}
                  <span className="truncate w-full text-center">{cat.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Details / Note */}
          <div>
            <label className="block text-xs font-semibold text-[#1A2D23] mb-1">
              Note (optional)
            </label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Direct cash, Transfer confirmation, Weekly settlement"
              className="w-full bg-white border border-[#DDD7CE] rounded-xl px-3.5 py-2 text-sm text-[#1A2D23] focus:border-[#1E5E45] focus:ring-2 focus:ring-[#1E5E45]/15 outline-none"
            />
          </div>

          {/* Amount */}
          <div>
            <label className="block text-xs font-semibold text-[#1A2D23] mb-1">
              {t.incomeAmountLabel}
            </label>
            <div className="relative">
              <input
                type="number"
                required
                min="100"
                step="100"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="e.g. 10000"
                className="w-full bg-white border border-[#DDD7CE] rounded-xl px-3.5 py-2 text-sm text-[#1A2D23] focus:border-[#1E5E45] focus:ring-2 focus:ring-[#1E5E45]/15 outline-none font-medium"
              />
              <span className="absolute right-3.5 top-2 text-xs font-semibold text-[#1E5E45]">
                RWF
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2 border-t border-[#E5DFD4]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-[#5A6E63] hover:bg-[#ECE6DB] transition-colors cursor-pointer"
            >
              {t.cancelButton}
            </button>
            <button
              type="submit"
              className="bg-[#1E5E45] hover:bg-[#164936] text-white px-5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{t.saveIncomeButton}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
