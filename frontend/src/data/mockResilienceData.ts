export type ShockType =
  | 'income_drop'
  | 'medical_emergency'
  | 'school_fees'
  | 'harvest_disruption'
  | 'medical_clinic'
  | 'food_inflation'
  | 'school_term'
  | 'property_repair';

export interface ShockOption {
  id: ShockType;
  labelEn: string;
  labelRw: string;
  descriptionEn: string;
  descriptionRw: string;
  defaultAmount?: number;
  isLumpSum?: boolean;
}

export const SHOCK_OPTIONS: ShockOption[] = [
  {
    id: 'income_drop',
    labelEn: 'Monthly income falls',
    labelRw: 'Kugabanuka k’umushahara / inyungu',
    descriptionEn: 'Informal sector wage reduction, harvest delay, or client slowdown.',
    descriptionRw: 'Kugabanuka kw’amafaranga yinjira mu bucuruzi cyangwa akazi.',
  },
  {
    id: 'medical_clinic',
    labelEn: 'Urgent medical clinic visit',
    labelRw: 'Kuvuza umuntu byihutirwa',
    descriptionEn: 'Unexpected hospital fee or prescription outside basic Mutuelle de Santé.',
    descriptionRw: 'Kuvuza umuntu mu buryo butunguranye burenze ibyishingizi bisanzwe.',
    defaultAmount: 25000,
    isLumpSum: true,
  },
  {
    id: 'food_inflation',
    labelEn: 'Dry season food price surge (+20%)',
    labelRw: 'Izamuka ry’ibiciro by’ibiribwa (+20%)',
    descriptionEn: 'Seasonal drought or regional supply bottlenecks inflating staple market prices.',
    descriptionRw: 'Izamuka ry’ibiciro by’ibiribwa bitewe n’amapfa cyangwa ikirere.',
    defaultAmount: 13000,
  },
  {
    id: 'school_term',
    labelEn: 'School term start fees (Igihembwe)',
    labelRw: 'Ibikoresho n’amafaranga y’ishuri (Igihembwe)',
    descriptionEn: 'New uniforms, books, stationery, and community school contributions.',
    descriptionRw: 'Kwishyura amafaranga y’ishuri, imyenda n’amakaye y’abana.',
    defaultAmount: 35000,
    isLumpSum: true,
  },
  {
    id: 'property_repair',
    labelEn: 'Heavy rain roof / home damage',
    labelRw: 'Gusana inzu yangijwe n’imvura',
    descriptionEn: 'Emergency repairs after heavy rains or storm roof damage.',
    descriptionRw: 'Gusana inzu cyangwa igisenge cyangijwe n’imvura idasanzwe.',
    defaultAmount: 30000,
    isLumpSum: true,
  },
];

export const REDUCTION_PERCENTAGES = [
  { value: 10, label: '10%' },
  { value: 20, label: '20%' },
  { value: 30, label: '30%' },
  { value: 50, label: '50%' },
];

export const DURATION_MONTHS = [
  { value: 1, labelEn: '1 month', labelRw: 'Ukwezi 1' },
  { value: 2, labelEn: '2 months', labelRw: 'Amezi 2' },
  { value: 3, labelEn: '3 months', labelRw: 'Amezi 3' },
  { value: 6, labelEn: '6 months', labelRw: 'Amezi 6' },
];

// Innovative Rwandan Coping & Adaptation Levers
export interface CopingLever {
  id: string;
  titleEn: string;
  titleRw: string;
  subEn: string;
  subRw: string;
  type: 'monthly_reduction' | 'monthly_income' | 'lump_sum_aid';
  monthlySavings: number; // in RWF
  oneTimeBufferBoost?: number;
  iconType: 'trim' | 'tontine' | 'swap' | 'momo' | 'sidegig';
  defaultActive?: boolean;
}

export const INNOVATIVE_COPING_LEVERS: CopingLever[] = [
  {
    id: 'trim_flexible',
    titleEn: 'Flexible Expense Trimming',
    titleRw: 'Kugabanya ibitari ngombwa',
    subEn: 'Pause leisure, extra snacks, and non-essential mobile airtime.',
    subRw: 'Guhagarika ibinezeza by’akanya gato n’ama-initsiye arenze.',
    type: 'monthly_reduction',
    monthlySavings: 7000,
    iconType: 'trim',
  },
  {
    id: 'agro_swap',
    titleEn: 'Seasonal Agro Swap (Ibihingwa)',
    titleRw: 'Guhindura ibiribwa by’amazi n’imyaka',
    subEn: 'Swap high-cost out-of-season produce for local sweet potatoes & seasonal greens.',
    subRw: 'Guhindura ibiribwa bihenze ukoresha ibijumba n’imboga z’igihembwe.',
    type: 'monthly_reduction',
    monthlySavings: 8000,
    iconType: 'swap',
  },
  {
    id: 'community_tontine',
    titleEn: 'Community Tontine / Ikimina Payout',
    titleRw: 'Amafaranga y’Ikimina cyangwa Ubwizigame',
    subEn: 'Request an early rotational payout or 0% community mutual fund loan.',
    subRw: 'Kwakira amafaranga y’ubwizigame bwo mu kimina cy’abaturanyi.',
    type: 'lump_sum_aid',
    monthlySavings: 0,
    oneTimeBufferBoost: 20000,
    iconType: 'tontine',
  },
  {
    id: 'momo_remittance',
    titleEn: 'Family Mobile Money Aid',
    titleRw: 'Ubufasha bw’umuryango kuri MoMo',
    subEn: 'Informal mutual assistance from relatives or diaspora support network.',
    subRw: 'Ubufasha buto bwahererekanwe n’abo mu muryango kuri telefoni.',
    type: 'lump_sum_aid',
    monthlySavings: 0,
    oneTimeBufferBoost: 15000,
    iconType: 'momo',
  },
  {
    id: 'micro_sidegig',
    titleEn: 'Micro Side-Gig (Ikiraka)',
    titleRw: 'Ikiraka cyangwa ubucuruzi bw’inyongera',
    subEn: 'Weekend artisan craft, delivery service, or urban informal trade.',
    subRw: 'Ikiraka cya wikendi cyangwa ubucuruzi buciriritse.',
    type: 'monthly_income',
    monthlySavings: 12000,
    iconType: 'sidegig',
  },
];

export const RESILIENCE_TRANSLATIONS = {
  EN: {
    breadcrumb: 'RESILIENCE SIMULATOR',
    headline: 'What if income slows down?',
    subheadline: 'Explore a possible shock before it happens. A scenario is a guide, not a prediction.',
    householdTag: 'Gasabo · 4 people · Demo household',
    scenarioCardTitle: 'Set your scenario',
    shockToExploreLabel: 'Shock to explore',
    incomeReductionLabel: 'Income reduction',
    durationLabel: 'Duration',
    availableSavingsLabel: 'Available savings',
    scenarioFooterNotice: 'Expenses held at 150,000 RWF/month. No new borrowing or additional shocks.',
    scenarioAppliedBtn: 'Scenario applied',
    illustrativeResultBadge: 'ILLUSTRATIVE RESULT · MONTHLY',
    gapSuffix: 'RWF gap',
    surplusSuffix: 'RWF buffer intact',
    incomeComparisonText: 'Income becomes',
    againstPlannedText: 'against 150,000 RWF of planned expenses.',
    savingsUsedText: 'of savings used over',
    savingsRemainText: 'savings remain',
    bufferNotGuaranteeTitle: 'A buffer, not a guarantee',
    savingsDividedGapLabel: 'Savings ÷ monthly gap',
    runwayUnit: 'months',
    runwayMathText: 'if this same gap continues. This is not a risk score.',
    practicalNextStepTitle: 'One practical next step',
    practicalNextStepText: 'Review flexible purchases first. Keep food, housing and health needs in view before drawing down savings.',
    disclaimerText: 'Demo arithmetic only. Income timing, debt, price changes and household needs can change the result.',
    solutionsTitle: 'Innovative Coping Levers (Action Playbook)',
    solutionsSub: 'Activate community and household mechanisms to close the gap and protect your savings.',
    activeLeversCount: 'active levers',
    gapResolvedBadge: 'Gap Fully Resolved · Buffer 100% Protected',
    gapRemainingBadge: 'Deficit Active · Savings Drawdown in Progress',
    depletionTimelineTitle: 'Month-by-Month Savings Timeline',
    depletionTimelineSub: 'Track how your savings evolve with and without coping actions.',
    resilienceScoreTitle: 'Household Resilience Health Score',
    resilienceScoreSub: 'Evaluated across buffer capacity, overhead flexibility, and mutual aid.',
    baselineScoreLabel: 'Baseline Under Shock',
    actionScoreLabel: 'With Action Levers',
    scorePillarBuffer: 'Savings Buffer',
    scorePillarFlex: 'Flexibility',
    scorePillarCommunity: 'Mutual Aid (Ibimina)',
    leverSavesMonthly: 'saves / mo',
    leverOneTimeBoost: 'one-time boost',
  },
  RW: {
    breadcrumb: 'GUSUZUMA UBUDAHANGARWA',
    headline: 'Biramutse byanze se amafaranga yinjira akagabanuka?',
    subheadline: 'Suzuma ikibazo gishobora kuvuka mbere y’uko kiba. Iki ni icyitegererezo, si ubuhanuzi.',
    householdTag: 'Gasabo · Abantu 4 · Urugo rw’icyitegererezo',
    scenarioCardTitle: 'Gena ikibazo ushaka gusuzuma',
    shockToExploreLabel: 'Ikibazo cy’ubuzima ushaka gusuzuma',
    incomeReductionLabel: 'Igipimo cyo kugabanukaho',
    durationLabel: 'Igihe bizamara',
    availableSavingsLabel: 'Ubwizigame buhari',
    scenarioFooterNotice: 'Ibikenerwa by’ukwezi bibarirwa ku 150,000 RWF. Nta nguzanyo nshya cyangwa ibindi bibazo bibariwemo.',
    scenarioAppliedBtn: 'Ibisubizo byasuzumwe',
    illustrativeResultBadge: 'IBIVAMO BY’UKWEZI · ICYITEGEREREZO',
    gapSuffix: 'RWF habuze',
    surplusSuffix: 'RWF ubwizigame burinzwe',
    incomeComparisonText: 'Amafaranga yinjira aba',
    againstPlannedText: 'ugereranyije na 150,000 RWF y’ingengo y’imari.',
    savingsUsedText: 'byakoreshejwe mu bwizigame mu gihe cy’amezi',
    savingsRemainText: 'asigaye mu bwizigame',
    bufferNotGuaranteeTitle: 'Ubwizigame ni ingabo, si igihano',
    savingsDividedGapLabel: 'Ubwizigame ÷ amafaranga abura',
    runwayUnit: 'amezi',
    runwayMathText: 'niba iki kibazo cyakomeza. Iki si igipimo cy’akaga.',
    practicalNextStepTitle: 'Intambwe y’ingenzi wahita utera',
    practicalNextStepText: 'Banza usuzume ibintu bishobora kugabanurwa. Rinda amafunguro, inzu n’ubuvuzi mbere yo gukora ku bwizigame.',
    disclaimerText: 'Ibi ni imibare yo kwerekana gusa. Uko amafaranga abonekera, amadeni n’ibiciro ku isoko bishobora guhindura ibivamo.',
    solutionsTitle: 'Uburyo bwo Guhangana n’Ibibazo (Amayeri y’Urugo)',
    solutionsSub: 'Koresha uburyo bugezweho n’ubw’abaturanyi kugira ngo uzibe icyuho kandi urinde ubwizigame.',
    activeLeversCount: 'uburyo bukoreshejwe',
    gapResolvedBadge: 'Icyuho cyakemutse · Ubwizigame burarinzwe 100%',
    gapRemainingBadge: 'Harakibura amafaranga · Ubwizigame buri gukoreshwa',
    depletionTimelineTitle: 'Uko Ubwizigame Bugabanuka Uko Amezi Ahita',
    depletionTimelineSub: 'Reba uko amafaranga yawe agenda akoreshwa hamwe no gukoresha amayeri.',
    resilienceScoreTitle: 'Igipimo cy’Ubudahangamwa bw’Urugo',
    resilienceScoreSub: 'Gisuzuma ingano y’ubwizigame, guhindura ingengo y’imari, n’ibimina by’abaturanyi.',
    baselineScoreLabel: 'Muri iki kibazo',
    actionScoreLabel: 'Umaze gufata ingamba',
    scorePillarBuffer: 'Ubwizigame',
    scorePillarFlex: 'Guhindura ibikoreshwa',
    scorePillarCommunity: 'Ibimina n’Umuryango',
    leverSavesMonthly: 'asaguka / ku kwezi',
    leverOneTimeBoost: 'yongerewe rimwe',
  },
} as const;
