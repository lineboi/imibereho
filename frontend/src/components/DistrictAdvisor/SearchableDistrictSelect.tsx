import React, { useState, useRef, useEffect } from 'react';
import type { Language } from '../../types';
import { DISTRICTS } from '../../data/mockData';
import { MapPin, Search, ChevronDown, Check, X } from 'lucide-react';

interface SearchableDistrictSelectProps {
  id: string;
  label: string;
  value: string; // district id (e.g. 'gasabo')
  onChange: (districtId: string) => void;
  language: Language;
  placeholder?: string;
}

export const SearchableDistrictSelect: React.FC<SearchableDistrictSelectProps> = ({
  id,
  label,
  value,
  onChange,
  language,
  placeholder,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Selected district object
  const currentDistrict = DISTRICTS.find((d) => d.id === value.toLowerCase()) ?? DISTRICTS[0];

  // Filter districts based on query (name or province)
  const filteredDistricts = DISTRICTS.filter((d) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      d.name.toLowerCase().includes(q) ||
      d.province.toLowerCase().includes(q) ||
      d.id.toLowerCase().includes(q)
    );
  });

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (districtId: string) => {
    onChange(districtId);
    setIsOpen(false);
    setSearchQuery('');
  };

  const cleanProvince = (prov: string) => {
    return prov
      .replace('City of Kigali', 'Kigali')
      .replace(' Province', '');
  };

  return (
    <div className="flex flex-col gap-1 w-full relative" ref={containerRef}>
      <label htmlFor={id} className="text-xs font-semibold text-[#3F5448] flex items-center justify-between">
        <span>{label}</span>
        <span className="text-[10.5px] font-normal text-[#75877C]">
          {language === 'RW' ? 'Andika cyangwa uhitemo' : 'Type to search or select'}
        </span>
      </label>

      {/* Main Input Box / Combobox Header */}
      <div
        className={`w-full bg-[#FAF8F4] border rounded-xl flex items-center px-3 py-2 transition-all ${
          isOpen
            ? 'border-[#1E5E45] ring-2 ring-[#1E5E45]/20 bg-white'
            : 'border-[#DCD5C9] hover:border-[#B5C2B9]'
        }`}
      >
        <MapPin className="w-4 h-4 text-[#1E5E45] shrink-0 mr-2" />

        <input
          id={id}
          ref={inputRef}
          type="text"
          value={isOpen ? searchQuery : `${currentDistrict.name} (${cleanProvince(currentDistrict.province)})`}
          placeholder={
            placeholder ??
            (language === 'RW' ? 'Andika akarere (urug. Musanze, Gasabo)...' : 'Type a district (e.g. Musanze, Gasabo)...')
          }
          onFocus={() => {
            setIsOpen(true);
            setSearchQuery('');
          }}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setIsOpen(false);
              setSearchQuery('');
            } else if (e.key === 'Enter' && filteredDistricts.length > 0) {
              e.preventDefault();
              handleSelect(filteredDistricts[0].id);
            }
          }}
          className="w-full bg-transparent text-xs sm:text-sm font-medium text-[#182C22] placeholder:text-[#9AA8A0] focus:outline-none"
        />

        {isOpen && searchQuery ? (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setSearchQuery('');
              inputRef.current?.focus();
            }}
            className="p-1 text-[#8B9C92] hover:text-[#182C22] rounded-full hover:bg-gray-100 cursor-pointer shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => {
              setIsOpen((prev) => !prev);
              if (!isOpen) {
                setTimeout(() => inputRef.current?.focus(), 50);
              }
            }}
            className="p-0.5 text-[#6D7F74] hover:text-[#182C22] cursor-pointer shrink-0"
          >
            <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        )}
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-[calc(100%+4px)] left-0 right-0 z-40 bg-white border border-[#DDD6C9] rounded-2xl shadow-xl max-h-60 overflow-y-auto p-1.5 flex flex-col gap-0.5 animate-in fade-in duration-150">
          {/* Search Hint Header */}
          <div className="px-2.5 py-1.5 text-[10.5px] font-semibold text-[#7D8F83] uppercase tracking-wider flex items-center justify-between border-b border-[#F2ECE2] mb-1">
            <span className="flex items-center gap-1.5">
              <Search className="w-3 h-3" />
              <span>{language === 'RW' ? 'Uturere twose tw’u Rwanda (30)' : 'All 30 Rwanda Districts'}</span>
            </span>
            <span>{filteredDistricts.length} found</span>
          </div>

          {filteredDistricts.length === 0 ? (
            <div className="p-4 text-center text-xs text-[#7D8F83]">
              {language === 'RW' ? 'Nta karere kabonetse gashakishwa' : `No districts found matching "${searchQuery}"`}
            </div>
          ) : (
            filteredDistricts.map((district) => {
              const isSelected = district.id === currentDistrict.id;
              const isKigali = district.province.includes('Kigali');

              return (
                <button
                  key={district.id}
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault(); // Prevent blur before select
                    handleSelect(district.id);
                  }}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs sm:text-[13px] flex items-center justify-between transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-[#EBF4EE] text-[#164330] font-semibold'
                      : 'hover:bg-[#F8F6F0] text-[#2C4134]'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="truncate">{district.name}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${
                        isKigali
                          ? 'bg-[#E3EFE7] text-[#245A3E]'
                          : 'bg-[#F2EFE8] text-[#697B71]'
                      }`}
                    >
                      {cleanProvince(district.province)}
                    </span>
                  </div>

                  {isSelected && <Check className="w-3.5 h-3.5 text-[#1E5E45] shrink-0" />}
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};
