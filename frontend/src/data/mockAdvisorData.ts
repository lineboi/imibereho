export type ComparisonMode = 'district_vs_district' | 'my_plan_vs_benchmark';

export interface CategoryBenchmarkLine {
  categoryCode: 'food' | 'housing' | 'transport' | 'utilities' | 'other_essentials';
  nameEn: string;
  nameRw: string;
  amount: number;
  noteEn: string;
  noteRw: string;
}

export interface DistrictBenchmarkData {
  districtId: string;
  districtName: string;
  provinceEn: string;
  provinceRw: string;
  isUrban: boolean;
  baselineTotal: number; // for 4-person baseline
  lines: CategoryBenchmarkLine[];
  highlightsEn: string;
  highlightsRw: string;
}

// 4-person benchmark profiles for representative Rwandan districts
export const DISTRICT_BENCHMARKS: Record<string, DistrictBenchmarkData> = {
  gasabo: {
    districtId: 'gasabo',
    districtName: 'Gasabo',
    provinceEn: 'City of Kigali',
    provinceRw: 'Umujyi wa Kigali',
    isUrban: true,
    baselineTotal: 150000,
    lines: [
      {
        categoryCode: 'food',
        nameEn: 'Food & Groceries',
        nameRw: 'Ibiribwa n’Amasoko',
        amount: 65000,
        noteEn: 'Kimironko & local neighborhood market prices',
        noteRw: 'Ibiciro by’isoko rya Kimironko n’utundi dusoko',
      },
      {
        categoryCode: 'housing',
        nameEn: 'Housing & Rent',
        nameRw: 'Inzu n’Ubukode',
        amount: 40000,
        noteEn: 'Kigali urban perimeter residential rates',
        noteRw: 'Ibiciro by’inzu zikodeshwa mu nkengero za Kigali',
      },
      {
        categoryCode: 'transport',
        nameEn: 'Transport & Commute',
        nameRw: 'Ingendo n’Ubwikorezi',
        amount: 20000,
        noteEn: 'Tap&Go city bus fares and occasional moto-taxi',
        noteRw: 'Karisita ya bisi na moto za hato na hato',
      },
      {
        categoryCode: 'utilities',
        nameEn: 'Utilities (Water & Power)',
        nameRw: 'Amazi n’Umuriro',
        amount: 10000,
        noteEn: 'Prepaid CashPower and WASAC municipal water',
        noteRw: 'Amashanyarazi ya CashPower n’amazi ya WASAC',
      },
      {
        categoryCode: 'other_essentials',
        nameEn: 'Other essentials',
        nameRw: 'Ibindi bya ngombwa',
        amount: 15000,
        noteEn: 'Hygiene, school stationery, and airtime',
        noteRw: 'Isuku, amakaye y’abana n’ama-initsiye',
      },
    ],
    highlightsEn: 'High housing and daily commuting costs typical of Kigali metropolitan area.',
    highlightsRw: 'Ubukode buri hejuru n’ingendo za buri munsi biranga umugi wa Kigali.',
  },
  musanze: {
    districtId: 'musanze',
    districtName: 'Musanze',
    provinceEn: 'Northern Province',
    provinceRw: 'Intara y’Amajyaruguru',
    isUrban: false,
    baselineTotal: 115000,
    lines: [
      {
        categoryCode: 'food',
        nameEn: 'Food & Groceries',
        nameRw: 'Ibiribwa n’Amasoko',
        amount: 48000,
        noteEn: 'Direct farm gate & Kariyeri market potato and bean prices',
        noteRw: 'Ibirayi, ibishyimbo n’imboga bihendutse ku isoko rya Kariyeri',
      },
      {
        categoryCode: 'housing',
        nameEn: 'Housing & Rent',
        nameRw: 'Inzu n’Ubukode',
        amount: 28000,
        noteEn: 'Secondary city housing rentals in Muhoza & outskirts',
        noteRw: 'Ubukode bw’inzu buciriritse mu murenge wa Muhoza n’inkengero',
      },
      {
        categoryCode: 'transport',
        nameEn: 'Transport & Commute',
        nameRw: 'Ingendo n’Ubwikorezi',
        amount: 12000,
        noteEn: 'Compact district center; higher bicycle & walking transit',
        noteRw: 'Urugendo rugufi mu mujyi; amagare n’amaguru birakoreshwa cyane',
      },
      {
        categoryCode: 'utilities',
        nameEn: 'Utilities (Water & Power)',
        nameRw: 'Amazi n’Umuriro',
        amount: 12000,
        noteEn: 'Water collection point & regular CashPower electrical use',
        noteRw: 'Amazi y’umuyoboro n’umuriro w’amashanyarazi',
      },
      {
        categoryCode: 'other_essentials',
        nameEn: 'Other essentials',
        nameRw: 'Ibindi bya ngombwa',
        amount: 15000,
        noteEn: 'Standard retail commodities and school materials',
        noteRw: 'Ibikoresho by’isuku n’iby’ishuri ku biciro bisanzwe',
      },
    ],
    highlightsEn: 'Agricultural fertility lowers staples spend significantly; rents are 30% lower than Kigali.',
    highlightsRw: 'Ubutaka burumbuka butuma ibiribwa bihenduka; ubukode buri munsi ho 30% ugereranyije na Kigali.',
  },
  nyarugenge: {
    districtId: 'nyarugenge',
    districtName: 'Nyarugenge',
    provinceEn: 'City of Kigali',
    provinceRw: 'Umujyi wa Kigali',
    isUrban: true,
    baselineTotal: 155000,
    lines: [
      { categoryCode: 'food', nameEn: 'Food & Groceries', nameRw: 'Ibiribwa n’Amasoko', amount: 66000, noteEn: 'Nyamirambo & Nyabugogo wholesale-retail mix', noteRw: 'Isoko rya Nyamirambo na Nyabugogo' },
      { categoryCode: 'housing', nameEn: 'Housing & Rent', nameRw: 'Inzu n’Ubukode', amount: 43000, noteEn: 'Central urban residential density', noteRw: 'Ubukode mu duce tw’umujyi rwagati' },
      { categoryCode: 'transport', nameEn: 'Transport & Commute', nameRw: 'Ingendo n’Ubwikorezi', amount: 20000, noteEn: 'City public bus lines and transit hubs', noteRw: 'Bisi rusange n’ingendo z’umujyi' },
      { categoryCode: 'utilities', nameEn: 'Utilities (Water & Power)', nameRw: 'Amazi n’Umuriro', amount: 11000, noteEn: 'Continuous utilities in urban center', noteRw: 'Amashanyarazi n’amazi ya buri munsi' },
      { categoryCode: 'other_essentials', nameEn: 'Other essentials', nameRw: 'Ibindi bya ngombwa', amount: 15000, noteEn: 'Daily urban household consumables', noteRw: 'Iby’isuku n’ibindi bikenerwa mu rugo' },
    ],
    highlightsEn: 'Highest rental and utility density due to central commercial hubs.',
    highlightsRw: 'Ubukode bwisumbuye bitewe n’uko ari rwagati mu bucuruzi.',
  },
  kicukiro: {
    districtId: 'kicukiro',
    districtName: 'Kicukiro',
    provinceEn: 'City of Kigali',
    provinceRw: 'Umujyi wa Kigali',
    isUrban: true,
    baselineTotal: 148000,
    lines: [
      { categoryCode: 'food', nameEn: 'Food & Groceries', nameRw: 'Ibiribwa n’Amasoko', amount: 64000, noteEn: 'Zinia & Kabeza local markets', noteRw: 'Isoko rya Zinia na Kabeza' },
      { categoryCode: 'housing', nameEn: 'Housing & Rent', nameRw: 'Inzu n’Ubukode', amount: 41000, noteEn: 'Suburban residential rental zones', noteRw: 'Ubukode mu nkengero z’umujyi' },
      { categoryCode: 'transport', nameEn: 'Transport & Commute', nameRw: 'Ingendo n’Ubwikorezi', amount: 18000, noteEn: 'Commuter routes to city center', noteRw: 'Ingendo zihuza Kicukiro n’umujyi rwagati' },
      { categoryCode: 'utilities', nameEn: 'Utilities (Water & Power)', nameRw: 'Amazi n’Umuriro', amount: 10000, noteEn: 'Standard urban electricity and water', noteRw: 'Amashanyarazi na serivisi z’amazi' },
      { categoryCode: 'other_essentials', nameEn: 'Other essentials', nameRw: 'Ibindi bya ngombwa', amount: 15000, noteEn: 'Household upkeep items', noteRw: 'Ibikoresho by’urugo bisanzwe' },
    ],
    highlightsEn: 'Balanced Kigali residential profile with steady transport spend.',
    highlightsRw: 'Akarere gatuyemo benshi muri Kigali gafite ingendo ziringaniye.',
  },
  huye: {
    districtId: 'huye',
    districtName: 'Huye',
    provinceEn: 'Southern Province',
    provinceRw: 'Intara y’Amajyepfo',
    isUrban: false,
    baselineTotal: 118000,
    lines: [
      { categoryCode: 'food', nameEn: 'Food & Groceries', nameRw: 'Ibiribwa n’Amasoko', amount: 50000, noteEn: 'Taba & university town local market produce', noteRw: 'Ibiribwa by’isoko rya Huye na Taba' },
      { categoryCode: 'housing', nameEn: 'Housing & Rent', nameRw: 'Inzu n’Ubukode', amount: 29000, noteEn: 'Student & civil service residential rentals', noteRw: 'Inzu zikodeshwa mu mujyi w’amashuri' },
      { categoryCode: 'transport', nameEn: 'Transport & Commute', nameRw: 'Ingendo n’Ubwikorezi', amount: 13000, noteEn: 'Town bus and local bicycle transportation', noteRw: 'Ingendo z’amagare na bisi nto z’umujyi' },
      { categoryCode: 'utilities', nameEn: 'Utilities (Water & Power)', nameRw: 'Amazi n’Umuriro', amount: 11000, noteEn: 'Standard regional water and electric tariffs', noteRw: 'Amazi n’amashanyarazi bisanzwe' },
      { categoryCode: 'other_essentials', nameEn: 'Other essentials', nameRw: 'Ibindi bya ngombwa', amount: 15000, noteEn: 'Household necessities and education essentials', noteRw: 'Ibikoresho by’isuku n’iby’ishuri' },
    ],
    highlightsEn: 'Moderate housing costs with strong regional agricultural connectivity.',
    highlightsRw: 'Ubukode buciriritse n’ibiribwa bituruka mu turere tw’abahinzi.',
  },
  rubavu: {
    districtId: 'rubavu',
    districtName: 'Rubavu',
    provinceEn: 'Western Province',
    provinceRw: 'Intara y’Iburengerazuba',
    isUrban: false,
    baselineTotal: 122000,
    lines: [
      { categoryCode: 'food', nameEn: 'Food & Groceries', nameRw: 'Ibiribwa n’Amasoko', amount: 52000, noteEn: 'Gisenyi lake fish and cross-border trade produce', noteRw: 'Amafi yo ku kiyaga n’ibiribwa byo ku mupaka' },
      { categoryCode: 'housing', nameEn: 'Housing & Rent', nameRw: 'Inzu n’Ubukode', amount: 30000, noteEn: 'Border city residential rentals', noteRw: 'Inzu zo guturamo mu mujyi wa Gisenyi' },
      { categoryCode: 'transport', nameEn: 'Transport & Commute', nameRw: 'Ingendo n’Ubwikorezi', amount: 14000, noteEn: 'Active commercial transport & moto routes', noteRw: 'Ingendo za moto n’ubwikorezi bw’ubucuruzi' },
      { categoryCode: 'utilities', nameEn: 'Utilities (Water & Power)', nameRw: 'Amazi n’Umuriro', amount: 11000, noteEn: 'Lakeside urban utility infrastructure', noteRw: 'Umuriro n’amazi bisanzwe' },
      { categoryCode: 'other_essentials', nameEn: 'Other essentials', nameRw: 'Ibindi bya ngombwa', amount: 15000, noteEn: 'Household basic goods', noteRw: 'Ibikenerwa mu buzima bwa buri munsi' },
    ],
    highlightsEn: 'Dynamic cross-border trade economy; fresh lake food supplies.',
    highlightsRw: 'Ubukungu bushingiye ku bucuruzi bwambukiranya umupaka n’isoko ry’ifi.',
  },
  bugesera: {
    districtId: 'bugesera',
    districtName: 'Bugesera',
    provinceEn: 'Eastern Province',
    provinceRw: 'Intara y’Iburasirazuba',
    isUrban: false,
    baselineTotal: 125000,
    lines: [
      { categoryCode: 'food', nameEn: 'Food & Groceries', nameRw: 'Ibiribwa n’Amasoko', amount: 54000, noteEn: 'Nyamata market beans, cassava, and vegetables', noteRw: 'Ibijumba, imyumbati n’ibishyimbo bya Nyamata' },
      { categoryCode: 'housing', nameEn: 'Housing & Rent', nameRw: 'Inzu n’Ubukode', amount: 32000, noteEn: 'Rapidly growing airport corridor rental housing', noteRw: 'Ubukode bwiyongera buhoro kubera ibikorwa by’ikibuga cy’indege' },
      { categoryCode: 'transport', nameEn: 'Transport & Commute', nameRw: 'Ingendo n’Ubwikorezi', amount: 15000, noteEn: 'Kigali-Nyamata express bus transit', noteRw: 'Bisi zihuza Kigali na Nyamata' },
      { categoryCode: 'utilities', nameEn: 'Utilities (Water & Power)', nameRw: 'Amazi n’Umuriro', amount: 10000, noteEn: 'Regional water schemes and electricity', noteRw: 'Imiyoboro y’amazi n’umuriro' },
      { categoryCode: 'other_essentials', nameEn: 'Other essentials', nameRw: 'Ibindi bya ngombwa', amount: 14000, noteEn: 'Everyday household staples', noteRw: 'Ibya ngombwa by’ibanze mu rugo' },
    ],
    highlightsEn: 'Fast-developing Eastern gateway with moderate living costs below Kigali.',
    highlightsRw: 'Akarere k’Iburasirazuba gatera imbere vuba gafite ikiguzi kiri munsi ya Kigali.',
  },
  rwamagana: {
    districtId: 'rwamagana',
    districtName: 'Rwamagana',
    provinceEn: 'Eastern Province',
    provinceRw: 'Intara y’Iburasirazuba',
    isUrban: false,
    baselineTotal: 116000,
    lines: [
      { categoryCode: 'food', nameEn: 'Food & Groceries', nameRw: 'Ibiribwa n’Amasoko', amount: 51000, noteEn: 'Banana, maize and local dairy produce', noteRw: 'Ibitoki, ibigori n’amata by’iwabo' },
      { categoryCode: 'housing', nameEn: 'Housing & Rent', nameRw: 'Inzu n’Ubukode', amount: 27000, noteEn: 'Affordable town and peri-urban accommodation', noteRw: 'Ubukode buhendutse mu mujyi no mu giturage' },
      { categoryCode: 'transport', nameEn: 'Transport & Commute', nameRw: 'Ingendo n’Ubwikorezi', amount: 13000, noteEn: 'Local hub travel and highway access', noteRw: 'Ingendo z’umuhanda munini n’izo mu mujyi' },
      { categoryCode: 'utilities', nameEn: 'Utilities (Water & Power)', nameRw: 'Amazi n’Umuriro', amount: 10000, noteEn: 'Stable regional electrical connections', noteRw: 'Umuriro n’amazi by’akarere' },
      { categoryCode: 'other_essentials', nameEn: 'Other essentials', nameRw: 'Ibindi bya ngombwa', amount: 15000, noteEn: 'Family necessities', noteRw: 'Ibikenerwa mu muryango' },
    ],
    highlightsEn: 'Accessible food and low rents make Rwamagana a resilient eastern hub.',
    highlightsRw: 'Ibiribwa bihendutse n’ubukode bucye bituma haba ahantu ho gutura neza.',
  },
};

// Household size multipliers relative to standard 4-person baseline
export function getHouseholdSizeFactor(size: number): number {
  if (size <= 1) return 0.46;
  if (size === 2) return 0.70;
  if (size === 3) return 0.86;
  if (size === 4) return 1.00;
  if (size === 5) return 1.18;
  if (size === 6) return 1.34;
  return Math.min(2.5, Math.round((1.0 + (size - 4) * 0.16) * 100) / 100);
}

export function formatHouseholdSize(size: number, language: 'EN' | 'RW'): string {
  if (language === 'RW') {
    return size === 1 ? 'Umuntu 1' : `Abantu ${size}`;
  }
  return size === 1 ? '1 person' : `${size} people`;
}

// Generates benchmark for any of the 30 districts and any household size
export function getDistrictBenchmark(
  districtId: string,
  householdSize: number | string = 4
): DistrictBenchmarkData {
  const normId = districtId.toLowerCase().trim();
  const sizeNum =
    typeof householdSize === 'number'
      ? Math.max(1, householdSize)
      : parseInt(householdSize, 10) || 4;
  const factor = getHouseholdSizeFactor(sizeNum);

  // Use explicit profile if defined
  if (DISTRICT_BENCHMARKS[normId]) {
    const raw = DISTRICT_BENCHMARKS[normId];
    if (factor === 1.0) return raw;

    const scaledLines = raw.lines.map((l) => ({
      ...l,
      amount: Math.round((l.amount * factor) / 500) * 500,
    }));
    const total = scaledLines.reduce((acc, curr) => acc + curr.amount, 0);

    return {
      ...raw,
      baselineTotal: total,
      lines: scaledLines,
    };
  }

  // Fallback realistic heuristic for other districts in Rwanda
  const isKigali = ['gasabo', 'kicukiro', 'nyarugenge'].includes(normId);
  const baselineTotal = isKigali ? 150000 : 112000;
  const foodShare = isKigali ? 0.43 : 0.44;
  const housingShare = isKigali ? 0.27 : 0.24;
  const transportShare = isKigali ? 0.13 : 0.11;
  const utilitiesShare = isKigali ? 0.07 : 0.10;
  const otherShare = 0.10;

  const capitalised = normId.charAt(0).toUpperCase() + normId.slice(1);

  const rawLines: CategoryBenchmarkLine[] = [
    {
      categoryCode: 'food',
      nameEn: 'Food & Groceries',
      nameRw: 'Ibiribwa n’Amasoko',
      amount: Math.round((baselineTotal * foodShare * factor) / 500) * 500,
      noteEn: `${capitalised} market staple goods`,
      noteRw: `Ibiribwa by’isoko ry’i ${capitalised}`,
    },
    {
      categoryCode: 'housing',
      nameEn: 'Housing & Rent',
      nameRw: 'Inzu n’Ubukode',
      amount: Math.round((baselineTotal * housingShare * factor) / 500) * 500,
      noteEn: `Local rental benchmark in ${capitalised}`,
      noteRw: `Ubukode bwo guturamo muri ${capitalised}`,
    },
    {
      categoryCode: 'transport',
      nameEn: 'Transport & Commute',
      nameRw: 'Ingendo n’Ubwikorezi',
      amount: Math.round((baselineTotal * transportShare * factor) / 500) * 500,
      noteEn: 'Commuting and community mobility',
      noteRw: 'Ingendo n’ubwikorezi bw’aho',
    },
    {
      categoryCode: 'utilities',
      nameEn: 'Utilities (Water & Power)',
      nameRw: 'Amazi n’Umuriro',
      amount: Math.round((baselineTotal * utilitiesShare * factor) / 500) * 500,
      noteEn: 'Prepaid power and water access',
      noteRw: 'Amashanyarazi n’amazi y’ibanze',
    },
    {
      categoryCode: 'other_essentials',
      nameEn: 'Other essentials',
      nameRw: 'Ibindi bya ngombwa',
      amount: Math.round((baselineTotal * otherShare * factor) / 500) * 500,
      noteEn: 'Household sundries and personal items',
      noteRw: 'Iby’isuku n’ibindi bya ngombwa',
    },
  ];

  const scaledTotal = rawLines.reduce((acc, curr) => acc + curr.amount, 0);

  return {
    districtId: normId,
    districtName: capitalised,
    provinceEn: isKigali ? 'City of Kigali' : 'Province',
    provinceRw: isKigali ? 'Umujyi wa Kigali' : 'Intara',
    isUrban: isKigali,
    baselineTotal: scaledTotal,
    lines: rawLines,
    highlightsEn: `Community baseline essentials estimate for ${capitalised}.`,
    highlightsRw: `Igereranyo ry’ibanze ry’ibikenewe mu muryango muri ${capitalised}.`,
  };
}

// User-friendly preset comparison shortcuts
export const COMPARISON_PRESETS = [
  {
    id: 'kigali_vs_musanze',
    labelEn: 'Kigali (Gasabo) vs Musanze',
    labelRw: 'Gasabo vs Musanze',
    subEn: 'Capital City vs Northern Agricultural Hub',
    subRw: 'Umujyi wa Kigali n’Amajyaruguru',
    districtA: 'gasabo',
    districtB: 'musanze',
  },
  {
    id: 'gasabo_vs_huye',
    labelEn: 'Gasabo vs Huye',
    labelRw: 'Gasabo vs Huye',
    subEn: 'Metropolitan vs Southern University Town',
    subRw: 'Kigali n’Umujyi w’Amajyepfo',
    districtA: 'gasabo',
    districtB: 'huye',
  },
  {
    id: 'gasabo_vs_bugesera',
    labelEn: 'Gasabo vs Bugesera',
    labelRw: 'Gasabo vs Bugesera',
    subEn: 'Capital vs Eastern Growth Corridor',
    subRw: 'Kigali n’Iburasirazuba',
    districtA: 'gasabo',
    districtB: 'bugesera',
  },
  {
    id: 'kicukiro_vs_rubavu',
    labelEn: 'Kicukiro vs Rubavu',
    labelRw: 'Kicukiro vs Rubavu',
    subEn: 'Suburban Kigali vs Western Border & Lake Hub',
    subRw: 'Kicukiro n’Umujyi wo ku Kiyaga',
    districtA: 'kicukiro',
    districtB: 'rubavu',
  },
];

// Default demo household plan for "My Plan vs Benchmark" mode (matching screenshot)
export const DEFAULT_MY_PLAN = {
  householdSize: '4 people',
  districtId: 'gasabo',
  monthlyTotal: 150000,
  lines: [
    { categoryCode: 'food' as const, amount: 60000 },
    { categoryCode: 'housing' as const, amount: 45000 },
    { categoryCode: 'transport' as const, amount: 18000 },
    { categoryCode: 'utilities' as const, amount: 12000 },
    { categoryCode: 'other_essentials' as const, amount: 15000 },
  ],
};

// Market Basket Item specification for local price transparency
export interface MarketBasketItem {
  id: string;
  nameEn: string;
  nameRw: string;
  category: 'food' | 'housing' | 'transport' | 'utilities';
  districtACost: string;
  districtBCost: string;
  unitEn: string;
  unitRw: string;
  insightEn: string;
  insightRw: string;
}

export type StressTestScenario = 'none' | 'food_inflation' | 'rent_surge' | 'annual_savings';

export function getMarketBasketItems(districtAId: string, districtBId: string): MarketBasketItem[] {
  const normA = districtAId.toLowerCase();
  const normB = districtBId.toLowerCase();
  const isAKigali = ['gasabo', 'kicukiro', 'nyarugenge'].includes(normA);
  const isBMusanze = normB === 'musanze';

  return [
    {
      id: 'potatoes',
      nameEn: 'Kinigi Irish Potatoes',
      nameRw: 'Ibirayi bya Kinigi',
      category: 'food',
      districtACost: isAKigali ? '580 RWF' : '380 RWF',
      districtBCost: isBMusanze ? '250 RWF' : '340 RWF',
      unitEn: 'per kg',
      unitRw: 'ku kilo',
      insightEn: isBMusanze
        ? 'Direct volcanic cooperative farm gate price at Kariyeri market vs freight transit markup in Kigali.'
        : 'Regional supply logistics and market stall tariffs.',
      insightRw: isBMusanze
        ? 'Ibiciro bituruka ku bahinzi b’i Musanze n’isoko rya Kariyeri bitarimo amafaranga yo kubitwara i Kigali.'
        : 'Ibiciro byo mu masoko y’uturere hashingiwe ku ngendo.',
    },
    {
      id: 'beans',
      nameEn: 'Climbing Farm Beans',
      nameRw: 'Ibishyimbo by’imishingiriro',
      category: 'food',
      districtACost: isAKigali ? '850 RWF' : '720 RWF',
      districtBCost: isBMusanze ? '600 RWF' : '680 RWF',
      unitEn: 'per kg',
      unitRw: 'ku kilo',
      insightEn: 'Northern highlands produce steady legume harvests, keeping local bean prices accessible.',
      insightRw: 'Amajyaruguru yeza ibishyimbo byinshi bituma ibiciro biguma hasi ku masoko.',
    },
    {
      id: 'greens',
      nameEn: 'Fresh Vegetables & Tomatoes',
      nameRw: 'Imboga n’Inyanya nshya',
      category: 'food',
      districtACost: isAKigali ? '12,000 RWF' : '8,000 RWF',
      districtBCost: isBMusanze ? '6,500 RWF' : '7,500 RWF',
      unitEn: 'monthly household bundle',
      unitRw: 'ibikenewe mu kwezi',
      insightEn: 'High humidity volcanic gardens allow year-round harvest with zero municipal freight overhead.',
      insightRw: 'Ubutaka bw’ibirunga bweraho imboga umwaka wose nta kiguzi cyo kuzitwara mu yindi migi.',
    },
    {
      id: 'rental',
      nameEn: '2-Bedroom Family Accommodation',
      nameRw: 'Inzu y’ibyumba 2 yo guturamo',
      category: 'housing',
      districtACost: isAKigali ? '40,000 RWF' : '30,000 RWF',
      districtBCost: isBMusanze ? '28,000 RWF' : '26,000 RWF',
      unitEn: 'per month',
      unitRw: 'ku kwezi',
      insightEn: isAKigali
        ? 'High urban land values and commuter demand inflate rental benchmarks in Gasabo.'
        : 'Spacious residential compounds with compound gardens in secondary town outskirts.',
      insightRw: isAKigali
        ? 'Ubutaka buhenze n’abantu benshi bashaka inzu bituma ubukode bwiyongera muri Gasabo.'
        : 'Inzu nziza zifite urugo mu nkengero z’umujyi wa Muhoza ku giciro cyiza.',
    },
    {
      id: 'transit',
      nameEn: 'Daily Work Transit & Mobility',
      nameRw: 'Ingendo za buri munsi z’akazi',
      category: 'transport',
      districtACost: isAKigali ? '20,000 RWF' : '14,000 RWF',
      districtBCost: isBMusanze ? '12,000 RWF' : '13,000 RWF',
      unitEn: 'monthly commuting estimate',
      unitRw: 'ku kwezi',
      insightEn: 'Kigali relies on smart-card bus lines and motos; Musanze residents utilize bicycles and walkable town centers.',
      insightRw: 'Kigali ikoresha bisi na moto kenshi; i Musanze amagare n’amaguru biroroshye mu mujyi rwagati.',
    },
    {
      id: 'utilities',
      nameEn: 'Cooking Energy & Water Tariffs',
      nameRw: 'Ingufu zo guteka n’amazi',
      category: 'utilities',
      districtACost: isAKigali ? '10,000 RWF' : '11,000 RWF',
      districtBCost: isBMusanze ? '12,000 RWF' : '11,500 RWF',
      unitEn: 'monthly baseline',
      unitRw: 'ku kwezi',
      insightEn: 'Clean water access points and charcoal/gas logistics remain comparable nationwide.',
      insightRw: 'Ibiciro by’amazi n’ingufu zo guteka birasa neza mu turere twose tw’igihugu.',
    },
  ];
}

// UI Translations for District Budget Advisor
export const ADVISOR_TRANSLATIONS = {
  EN: {
    breadcrumb: 'DISTRICT BUDGET ADVISOR',
    headline: 'Your budget, in local context.',
    subheadline: 'Compare a monthly plan, not your worth. Every household has different needs.',
    modeDistrictVsDistrict: 'Compare 2 Districts',
    modeMyPlanVsBenchmark: 'My Plan vs Benchmark',
    modeDistrictVsDistrictSub: 'Living cost comparison between regions',
    modeMyPlanVsBenchmarkSub: 'Original single-district advisor view',
    districtALabel: 'Primary District (A)',
    districtBLabel: 'Comparison District (B)',
    districtSingleLabel: 'District',
    householdSizeLabel: 'Household size',
    swapDistricts: 'Swap districts',
    quickPresetsTitle: 'Popular Comparisons',
    illustrativeBenchmarkBadge: 'ILLUSTRATIVE BENCHMARK',
    monthlyEssentialsLabel: 'Monthly essentials · RWF',
    categoryHeader: 'CATEGORY',
    youHeader: 'YOU',
    demoHeader: 'DEMO',
    differenceHeader: 'DIFFERENCE',
    totalMonthlyEssentials: 'Total monthly essentials',
    wholePictureTitle: 'Look at the whole picture.',
    disclaimerText: 'This is an illustrative comparison, not official statistics or a recommended minimum. Validated local benchmarks still need confirmation.',
    usePlanInSimulatorBtn: 'Use this plan in the simulator',
    categoryFood: 'Food',
    categoryHousing: 'Housing',
    categoryTransport: 'Transport',
    categoryUtilities: 'Utilities',
    categoryOtherEssentials: 'Other essentials',
    costDifferencePrefix: 'is',
    costDifferenceLess: 'lower living cost than',
    costDifferenceMore: 'higher living cost than',
    savingsPerMonth: 'estimated monthly difference',
    modalTitle: 'Send Plan to Resilience Simulator',
    modalSub: 'Test how this budget allocation withstands agricultural price surges and household shocks.',
    modalBtnConfirm: 'Open Simulator with this Plan',
    modalBtnCancel: 'Close',
    legendDistrictA: 'District A baseline',
    legendDistrictB: 'District B comparison',
    legendYourPlan: 'Your plan',
    legendDemoRef: 'Demo reference',
    comparisonInsightSameTotal: 'Your plan and the demo comparison total are the same; the mix is different.',
    compareNoticePrefix: 'Living in',
    compareNoticeSuffix: 'for a family of',
    incomeRunwayTitle: 'Household Income & Buffer Runway',
    incomeRunwaySub: 'See what the living cost difference means for your actual emergency savings.',
    monthlyIncomeInputLabel: 'Your Monthly Income',
    essentialsShareLabel: 'of income spent on essentials',
    bufferLeftLabel: 'Leftover buffer per month',
    monthsToEmergencyFund: 'Months to build 3-month emergency fund',
    runwaySpeedup: 'faster buffer accumulation in',
    budgetShareTitle: 'Where Every 10,000 RWF Goes',
    budgetShareSub: 'Structural expenditure allocation comparison',
    fixedOverheadNote: 'Fixed overhead (Rent + Commute) consumes',
    basketTitle: 'What’s in the Basket? Real Market Context',
    basketSub: 'Local market dynamics explaining why prices diverge between districts.',
    viewBasketBtn: 'Explore Itemized Market Prices',
    hideBasketBtn: 'Hide Itemized Market Prices',
    seasonalTitle: 'Season A Harvest Alert · October (Ukwakira)',
    seasonalBadge: 'Agricultural Cycle Insight',
    seasonalText: 'Volcanic fertile soils in Northern Rwanda are currently yielding fresh potatoes and beans, keeping local farm-gate prices low relative to Kigali freight tariffs.',
    stressTestTitle: 'Test Economic Scenarios',
    chipBaseline: 'Normal Baseline',
    chipFoodShock: '+15% Food Price Spike',
    chipRentSurge: '+10% Rent Surge',
    chipAnnual: '12-Month Net Savings',
  },
  RW: {
    breadcrumb: 'INAMA Y’INGENGO Y’IMARI Y’AKARERE',
    headline: 'Ingengo yawe, mu rwego rw’akarere.',
    subheadline: 'Gereranya ingengo y’ukwezi, si agaciro kawe. Buri rugo rugira ibyo rukenera bitandukanye.',
    modeDistrictVsDistrict: 'Gereranya Uturere 2',
    modeMyPlanVsBenchmark: 'Ingengo yanjye vs Igereranyo',
    modeDistrictVsDistrictSub: 'Kugereranya ikiguzi cy’ubuzima hagati y’uturere',
    modeMyPlanVsBenchmarkSub: 'Uburyo bwo kureba akarere kamwe',
    districtALabel: 'Akarere ka Mbere (A)',
    districtBLabel: 'Akarere ko Kugereranya (B)',
    districtSingleLabel: 'Akarere',
    householdSizeLabel: 'Ingano y’umuryango',
    swapDistricts: 'Hinduranya uturere',
    quickPresetsTitle: 'Ibyo abandi bakunze kugereranya',
    illustrativeBenchmarkBadge: 'IGERERANYO RY’ICYITEGEREREZO',
    monthlyEssentialsLabel: 'Ibikenerwa by’ibanze ku kwezi · RWF',
    categoryHeader: 'ICYICIRO',
    youHeader: 'WOGEZE',
    demoHeader: 'IGERERANYO',
    differenceHeader: 'ITANDUKANIRO',
    totalMonthlyEssentials: 'Ibikenerwa byose by’ukwezi',
    wholePictureTitle: 'Reba ishusho yose muri rusange.',
    disclaimerText: 'Ibi ni ibigereranyo byo kwerekana gusa, si imibare yemewe ya leta cyangwa igipimo ntarengwa. Igereranyo ryemewe riracyari gukusanywa.',
    usePlanInSimulatorBtn: 'Koresha iyi ngengo mu gusuzuma ubudahangarwa',
    categoryFood: 'Ibiribwa',
    categoryHousing: 'Inzu n’Ubukode',
    categoryTransport: 'Ingendo',
    categoryUtilities: 'Amazi n’Umuriro',
    categoryOtherEssentials: 'Ibindi bya ngombwa',
    costDifferencePrefix: 'ihera ku kiguzi kiri munsi ho',
    costDifferenceLess: 'ikiguzi cy’ubuzima kiri hasi ugereranyije na',
    costDifferenceMore: 'ikiguzi cy’ubuzima kiri hejuru ugereranyije na',
    savingsPerMonth: 'itandukaniro rigereranywa ku kwezi',
    modalTitle: 'Kohereza iyi Ngengo mu Gusuzuma Ubudahangarwa',
    modalSub: 'Reba uburyo aya mafaranga yabasha guhangana n’izamuka ry’ibiciro by’ibiribwa n’ibindi bibazo bitunguranye.',
    modalBtnConfirm: 'Fungura muri Simulator',
    modalBtnCancel: 'Funga',
    legendDistrictA: 'Akarere ka A',
    legendDistrictB: 'Akarere ka B',
    legendYourPlan: 'Ingengo yawe',
    legendDemoRef: 'Igereranyo cy’icyitegererezo',
    comparisonInsightSameTotal: 'Ingengo yawe n’iy’icyitegererezo birangana mu mubare wose; gusa uko agabanyijwe biratandukanye.',
    compareNoticePrefix: 'Gutura muri',
    compareNoticeSuffix: 'ku muryango w’abantu',
    incomeRunwayTitle: 'Amafaranga Yinjira n’Ubwizigame Burambye',
    incomeRunwaySub: 'Reba icyo itandukaniro ry’ibiciro rivuze ku mafaranga uzigama.',
    monthlyIncomeInputLabel: 'Amafaranga winjiza ku kwezi',
    essentialsShareLabel: 'y’amafaranga yose agenda ku by’ibanze',
    bufferLeftLabel: 'Asigara ku kwezi yo kwizigama',
    monthsToEmergencyFund: 'Amezi yo gukora ubwizigame bw’amezi 3',
    runwaySpeedup: 'byihuse mu gukora ubwizigame muri',
    budgetShareTitle: 'Aho Buri 10,000 RWF Yerekeza',
    budgetShareSub: 'Uko ingengo y’imari igabanyije mu byiciro',
    fixedOverheadNote: 'Amafaranga adahinduka (Ubukode + Ingendo) afata',
    basketTitle: 'Ibiri mu Gatebo: Ibiciro Nyakuri ku Isoko',
    basketSub: 'Ibisobanuro by’amasoko y’aho byerekana impamvu ibiciro bitandukanye.',
    viewBasketBtn: 'Reba ibiciro bya buri kintu ku isoko',
    hideBasketBtn: 'Hisha ibiciro by’isoko',
    seasonalTitle: 'Igihe cy’Ihinga A · Ukwakira (Umuhindo)',
    seasonalBadge: 'Ubumenyi bw’Ibihe by’Ubuhinzi',
    seasonalText: 'Ubutaka bw’ibirunga mu majyaruguru buri kweza ibirayi n’imboga bihendutse ku masoko y’aho ugereranyije na Kigali.',
    stressTestTitle: 'Gerageza Ibihe Bitandukanye by’Ubukungu',
    chipBaseline: 'Bisanzwe',
    chipFoodShock: '+15% Izamuka ry’Ibiribwa',
    chipRentSurge: '+10% Izamuka ry’Ubukode',
    chipAnnual: 'Ubwizigame bw’Umwaka Wose',
  },
} as const;
