export interface AgroSwapItem {
  id: string;
  category: 'staple' | 'tuber' | 'protein' | 'vegetable' | 'fuel';
  titleEn: string;
  titleRw: string;
  descriptionEn: string;
  descriptionRw: string;
  from: {
    nameEn: string;
    nameRw: string;
    quantity: string;
    price: number;
  };
  to: {
    nameEn: string;
    nameRw: string;
    quantity: string;
    price: number;
  };
  difference: number;
  savingsMonthlyEstimate: number; // based on 3x/week
  footnoteEn: string;
  footnoteRw: string;
  nutritionTagEn: string;
  nutritionTagRw: string;
}

export const MONTH_NAMES = [
  { value: '1', labelEn: 'January', labelRw: 'Mutarama', season: 'A' },
  { value: '2', labelEn: 'February', labelRw: 'Gashyantare', season: 'A' },
  { value: '3', labelEn: 'March', labelRw: 'Werurwe', season: 'B' },
  { value: '4', labelEn: 'April', labelRw: 'Mata', season: 'B' },
  { value: '5', labelEn: 'May', labelRw: 'Gicurasi', season: 'B' },
  { value: '6', labelEn: 'June', labelRw: 'Kamena', season: 'B' },
  { value: '7', labelEn: 'July', labelRw: 'Nyakanga', season: 'C' },
  { value: '8', labelEn: 'August', labelRw: 'Kanama', season: 'C' },
  { value: '9', labelEn: 'September', labelRw: 'Nzeli', season: 'C' },
  { value: '10', labelEn: 'October', labelRw: 'Ukwakira', season: 'A' },
  { value: '11', labelEn: 'November', labelRw: 'Ugushyingo', season: 'A' },
  { value: '12', labelEn: 'December', labelRw: 'Ukuboza', season: 'A' },
];

export const AGRO_SWAPS_DATA: AgroSwapItem[] = [
  {
    id: 'rice-to-sweet-potato',
    category: 'staple',
    titleEn: 'Try a different staple',
    titleRw: 'Gerageza igihingwa cy’amazi n’imbaraga',
    descriptionEn:
      'For one household meal, consider sweet potatoes instead of rice. Pair with beans and leafy vegetables.',
    descriptionRw:
      'Ku ifunguro rimwe ry’umuryango, koresha ibijumba mu mwanya w’umuceri. Bitegurane n’ibishyimbo n’imboga rwatsi.',
    from: {
      nameEn: 'Imported Tanzanian Rice',
      nameRw: 'Umuceri utumizwa mu mahanga',
      quantity: '1 kg demo basket',
      price: 2000,
    },
    to: {
      nameEn: 'Fresh Sweet Potatoes (Ibijumba)',
      nameRw: 'Ibijumba bishya by’iwacu',
      quantity: '2 kg demo basket',
      price: 1600,
    },
    difference: 400,
    savingsMonthlyEstimate: 5200,
    footnoteEn: 'Different quantities; not a nutritional equivalent. Prices are invented, not market observations.',
    footnoteRw: 'Ingano iratandukanye; ibi si igipimo cy’ubuvuzi. Ibiciro ni iby’icyitegererezo.',
    nutritionTagEn: 'Rich in Dietary Fiber & Beta-Carotene (Vitamin A)',
    nutritionTagRw: 'Bikungahaye kuri Vitamini A n’Ibyubaka umubiri',
  },
  {
    id: 'irish-to-cassava',
    category: 'tuber',
    titleEn: 'Swap off-season Irish potatoes for cassava',
    titleRw: 'Simbuza ibirayi bihenze imyumbati myiza',
    descriptionEn:
      'When Northern Irish potato prices peak during transit dry spells, local fresh cassava provides hearty energy at half the cost.',
    descriptionRw:
      'Iyo ibirayi bihenze ku isoko, imyumbati myiza yera mu gihugu igabanya ikiguzi cya kabiri.',
    from: {
      nameEn: 'Irish Potatoes (Ibirayi)',
      nameRw: 'Ibirayi byo ku isoko',
      quantity: '2 kg basket',
      price: 1500,
    },
    to: {
      nameEn: 'Fresh Local Cassava (Imyumbati)',
      nameRw: 'Imyumbati mitswe y’iwacu',
      quantity: '2 kg basket',
      price: 900,
    },
    difference: 600,
    savingsMonthlyEstimate: 7800,
    footnoteEn: 'Boiling cassava alongside beans in one pot reduces cooking fuel by 35%.',
    footnoteRw: 'Gutekera imyumbati rimwe n’ibishyimbo bigabanya inkwi cyangwa amakara ku kigero cya 35%.',
    nutritionTagEn: 'Slow-Release Complex Carbohydrates for Long Energy',
    nutritionTagRw: 'Bitanga imbaraga zirambye mu mubiri',
  },
  {
    id: 'yellow-to-red-beans',
    category: 'protein',
    titleEn: 'Opt for hearty local red beans',
    titleRw: 'Hitamo ibishyimbo bitukura bisanzwe',
    descriptionEn:
      'Specialty yellow beans carry a premium price tag; standard red kidney beans offer identical plant-based protein at substantial savings.',
    descriptionRw:
      'Ibishyimbo by’umuhondo birahenda; ibitukura bisanzwe bitanga intungamubiri zingana ku giciro cyo hasi.',
    from: {
      nameEn: 'Specialty Yellow Beans (Umuhondo)',
      nameRw: 'Ibishyimbo by’umuhondo',
      quantity: '1 kg basket',
      price: 1300,
    },
    to: {
      nameEn: 'Local Red Kidney Beans (Ibitukura)',
      nameRw: 'Ibishyimbo bitukura by’iwacu',
      quantity: '1 kg basket',
      price: 850,
    },
    difference: 450,
    savingsMonthlyEstimate: 5850,
    footnoteEn: 'Equal high iron, plant protein, and dietary magnesium per serving.',
    footnoteRw: 'Bifite intungamubiri z’ubutare na poroteyine zifite agaciro kamwe.',
    nutritionTagEn: 'Essential Plant Protein & Iron Support',
    nutritionTagRw: 'Poroteyine n’Ubutare birinda amaraso gukendera',
  },
  {
    id: 'cabbage-to-dodo',
    category: 'vegetable',
    titleEn: 'Embrace fresh amaranth greens (Dodo)',
    titleRw: 'Koresha imboga rwatsi za Dodo cyangwa Isombe',
    descriptionEn:
      'Greenhouse cabbages are priced high in urban centers, while nutrient-dense local dodo bunches cost half as much and cook twice as fast.',
    descriptionRw:
      'Amashu arahenda mu migi; imboga za Dodo zihendutse cyane kandi zihisha vuba bikagabanya umuriro.',
    from: {
      nameEn: 'Head Cabbage (Amashu)',
      nameRw: 'Ishu ryo ku isoko',
      quantity: '1 large head',
      price: 900,
    },
    to: {
      nameEn: 'Fresh Amaranth Greens (Dodo)',
      nameRw: 'Imboga z’icyatsi za Dodo',
      quantity: '2 fresh bunches',
      price: 450,
    },
    difference: 450,
    savingsMonthlyEstimate: 5850,
    footnoteEn: 'Dodo cooks in 8 minutes, dramatically cutting cooking gas or charcoal usage.',
    footnoteRw: 'Dodo ihisha mu minota 8 gusa, bigatuma udakoresha amakara menshi.',
    nutritionTagEn: 'Vital Folate, Vitamin C & Antioxidants',
    nutritionTagRw: 'Vitamini C n’Imyunyungugu irinda indwara',
  },
  {
    id: 'cooking-fuel-saver',
    category: 'fuel',
    titleEn: 'Energy saver: pre-soak legumes',
    titleRw: 'Kuzigama amakara: banza unike ibishyimbo',
    descriptionEn:
      'Soaking dry beans for 2 hours in warm water before boiling cuts cooking time from 3.5 hours to 1.5 hours, saving over 40% on fuel.',
    descriptionRw:
      'Kwinika ibishyimbo amasaha 2 mbere yo kubiteka bigabanya umwanya wo kubiteka kuva ku masaha 3.5 kugera kuri 1.5, bikazigama 40% by’umuriro.',
    from: {
      nameEn: 'Direct Unsoaked Boiling',
      nameRw: 'Guhita uteka utabanje kwinika',
      quantity: 'Full charcoal basin',
      price: 1200,
    },
    to: {
      nameEn: '2-Hour Pre-Soaked Cooking',
      nameRw: 'Guteka nyuma yo kwinika',
      quantity: 'Reduced charcoal use',
      price: 650,
    },
    difference: 550,
    savingsMonthlyEstimate: 7150,
    footnoteEn: 'Significant cumulative monthly savings on charcoal bags or LPG cooking gas cylinders.',
    footnoteRw: 'Ubwizigame bukomeye ku mifuka y’amakara cyangwa icupa rya gazi.',
    nutritionTagEn: 'Improves Digestibility and Mineral Absorption',
    nutritionTagRw: 'Bifasha umubiri gukuramo intungamubiri vuba',
  },
];

export const BALANCED_PLATE_COMPONENTS = [
  {
    code: 'protective',
    nameEn: 'Vitamins & Minerals (25%)',
    nameRw: 'Ibirinda Indwara (25%)',
    examplesEn: 'Amaranth (Dodo), Cassava leaves (Isombe), Sukuma, Tomatoes',
    examplesRw: 'Dodo, Isombe, Sukuma wiki, Inyanya, Imboga rwatsi',
    colorHex: '#1E5E45',
    colorBg: 'bg-[#1E5E45]',
    colorText: 'text-[#1E5E45]',
  },
  {
    code: 'protein',
    nameEn: 'Plant & Bodybuilding Protein (25%)',
    nameRw: 'Ibyubaka Umubiri (25%)',
    examplesEn: 'Local Red & Yellow Beans, Groundnuts, Soy, Peas, Sambaza',
    examplesRw: 'Ibishyimbo bitukura, Ubunyobwa, Amashaza, Isambaza',
    colorHex: '#8B5CF6',
    colorBg: 'bg-[#7C3AED]',
    colorText: 'text-[#7C3AED]',
  },
  {
    code: 'energy',
    nameEn: 'Energy & Healthy Carbohydrates (50%)',
    nameRw: 'Ibitera Imbaraga (50%)',
    examplesEn: 'Sweet potatoes (Ibijumba), Cassava (Imyumbati), Green bananas (Ibitoki)',
    examplesRw: 'Ibijumba, Imyumbati, Ibitoki, Ibirayi bya Kinigi',
    colorHex: '#D97706',
    colorBg: 'bg-[#D97706]',
    colorText: 'text-[#D97706]',
  },
];

export const AGRO_SWAPS_TRANSLATIONS = {
  EN: {
    breadcrumb: 'SEASONAL AGRO SWAPS',
    headline: 'Local choices, a little more flexibility.',
    subheadline: 'Ideas for your next market visit, without losing sight of a balanced meal.',
    districtLabel: 'District',
    planningMonthLabel: 'Planning month',
    marketHeroTag: 'MARKET IDEAS · NOT LIVE PRICES',
    marketHeroTitle: 'Start with what is available.',
    marketHeroSub: 'Availability varies by market, harvest and weather. Ask a vendor before planning around these ideas.',
    exampleBasketDifference: 'Example basket difference',
    calculatorTitle: 'Monthly Family Savings Projector',
    calculatorSub: 'Estimate how much this seasonal swap frees up for your household emergency buffer.',
    mealsPerWeekLabel: 'How many meals per week will you make this swap?',
    perMealSavings: 'saved per meal',
    projectedMonthlySavings: 'Projected Monthly Savings',
    runwayComparisonNotice: 'At 3 meals/week, this swap covers 2 weeks of WASAC water or 4 days of bus transit!',
    balancedPlateTitle: 'Keep variety on the plate (Indyo Yuzuye).',
    balancedPlateSub: 'Beans, amaranth leaves (dodo) and a locally available staple can offer variety. Consider cooking fuel, storage, dietary needs and portions for your household.',
    smartMarketChecklistTitle: 'Smart Market Shopping Checklist',
    smartMarketChecklistSub: 'Interactive basket list ready for your next market day.',
    checklistTotalLabel: 'Total estimated basket',
    copyChecklistBtn: 'Copy Shopping List',
    copiedNotice: 'Shopping list copied!',
    disclaimerText: 'Seasonal guidance is uncertain and unvalidated. These ideas are not nutrition advice or guaranteed savings.',
    addToTrackerBtn: 'Log to Daily Tracker',
    seasonalCalendarTitle: 'Rwanda Agricultural Harvest Seasons',
    seasonABadge: 'Season A (Umuhindo) · Active Now',
    seasonAText: 'Plentiful root tubers (sweet potato, cassava) and leafy greens across Northern and Eastern farm hubs.',
    filterAll: 'All Swaps',
    filterStaple: 'Staples & Tubers',
    filterProtein: 'Beans & Protein',
    filterFuel: 'Fuel & Cooking Energy',
  },
  RW: {
    breadcrumb: 'GUHINDURA IBIHINGWA BY’IGIHE',
    headline: 'Guhitamo iby’iwacu, kongera ubushobozi.',
    subheadline: 'Inama ku ifunguro ry’ubutaha ku isoko, udateshutse ku ifunguro ryuzuye.',
    districtLabel: 'Akarere',
    planningMonthLabel: 'Ukwezi k’ingengo',
    marketHeroTag: 'IBY’ISOKO · SI IBYEMEWE BURUNDI',
    marketHeroTitle: 'Tangirira ku biboneka hafi.',
    marketHeroSub: 'Ibiciro biterwa n’isoko, umusaruro n’ikirere. Banza ubaze umucuruzi mbere yo guhaha.',
    exampleBasketDifference: 'Itandukaniro ry’igikapu',
    calculatorTitle: 'Kubara Ubwizigame bw’Ukwezi',
    calculatorSub: 'Reba amafaranga asaguka mu muryango ku kwezi akoreshwa mu bindi bya ngombwa.',
    mealsPerWeekLabel: 'Uteka iri funguro inshuro zingahe mu cyumweru?',
    perMealSavings: 'asigara kuri buri funguro',
    projectedMonthlySavings: 'Amafaranga asaguka ku kwezi',
    runwayComparisonNotice: 'Kuri buri nshuro 3 mu cyumweru, aya mafaranga arishyura amazi ya WASAC y’ibyumweru 2!',
    balancedPlateTitle: 'Komeza kurya indyo yuzuye ifite amabara atatu.',
    balancedPlateSub: 'Ibishyimbo, imboga za Dodo n’ibiribwa by’amazi bitanga indyo nziza. Zirikana umuriro wo guteka, uko bibikwa, n’ingano y’umuryango wawe.',
    smartMarketChecklistTitle: 'Urutonde rwo Guhaha ku Isoko',
    smartMarketChecklistSub: 'Urutonde rwiteguye gukoreshwa igihe ugiye ku isoko.',
    checklistTotalLabel: 'Igiteranyo cy’igikapu',
    copyChecklistBtn: 'Koporora Urutonde',
    copiedNotice: 'Urutonde rwakoporowe!',
    disclaimerText: 'Ibi ni ibitekerezo byo kwerekana gusa. Si inama z’abaganga cyangwa ubwizigame bwasezeranyijwe.',
    addToTrackerBtn: 'Andika mu Ibarura rya Buri Munsi',
    seasonalCalendarTitle: 'Ibihe by’Ihinga mu Rwanda',
    seasonABadge: 'Igihembwe cya A (Umuhindo) · Kiriho ubu',
    seasonAText: 'Ibijumba, imyumbati n’imboga byinshi biri kuboneka ku masoko ku biciro byiza.',
    filterAll: 'Byose',
    filterStaple: 'Ibiribwa n’Imyumbati',
    filterProtein: 'Ibishyimbo n’Amashaza',
    filterFuel: 'Umuriro n’Amakara',
  },
} as const;
