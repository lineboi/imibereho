import type { District, HouseholdProfile } from '../types';

export const DISTRICTS: District[] = [
  // Kigali City
  { id: 'gasabo', name: 'Gasabo', province: 'City of Kigali' },
  { id: 'kicukiro', name: 'Kicukiro', province: 'City of Kigali' },
  { id: 'nyarugenge', name: 'Nyarugenge', province: 'City of Kigali' },

  // Northern Province
  { id: 'burera', name: 'Burera', province: 'Northern Province' },
  { id: 'gakenke', name: 'Gakenke', province: 'Northern Province' },
  { id: 'gicumbi', name: 'Gicumbi', province: 'Northern Province' },
  { id: 'musanze', name: 'Musanze', province: 'Northern Province' },
  { id: 'rulindo', name: 'Rulindo', province: 'Northern Province' },

  // Southern Province
  { id: 'gisagara', name: 'Gisagara', province: 'Southern Province' },
  { id: 'huye', name: 'Huye', province: 'Southern Province' },
  { id: 'kamonyi', name: 'Kamonyi', province: 'Southern Province' },
  { id: 'muhanga', name: 'Muhanga', province: 'Southern Province' },
  { id: 'nyamagabe', name: 'Nyamagabe', province: 'Southern Province' },
  { id: 'nyanza', name: 'Nyanza', province: 'Southern Province' },
  { id: 'nyaruguru', name: 'Nyaruguru', province: 'Southern Province' },
  { id: 'ruhango', name: 'Ruhango', province: 'Southern Province' },

  // Eastern Province
  { id: 'bugesera', name: 'Bugesera', province: 'Eastern Province' },
  { id: 'gatsibo', name: 'Gatsibo', province: 'Eastern Province' },
  { id: 'kayonza', name: 'Kayonza', province: 'Eastern Province' },
  { id: 'kirehe', name: 'Kirehe', province: 'Eastern Province' },
  { id: 'ngoma', name: 'Ngoma', province: 'Eastern Province' },
  { id: 'nyagatare', name: 'Nyagatare', province: 'Eastern Province' },
  { id: 'rwamagana', name: 'Rwamagana', province: 'Eastern Province' },

  // Western Province
  { id: 'karongi', name: 'Karongi', province: 'Western Province' },
  { id: 'ngororero', name: 'Ngororero', province: 'Western Province' },
  { id: 'nyabihu', name: 'Nyabihu', province: 'Western Province' },
  { id: 'nyamasheke', name: 'Nyamasheke', province: 'Western Province' },
  { id: 'rubavu', name: 'Rubavu', province: 'Western Province' },
  { id: 'rusizi', name: 'Rusizi', province: 'Western Province' },
  { id: 'rutsiro', name: 'Rutsiro', province: 'Western Province' },
];

export const HOUSEHOLD_SIZES: { value: string; labelEn: string; labelRw: string }[] = [
  { value: '1 person', labelEn: '1 person', labelRw: 'Umuntu 1' },
  { value: '2 people', labelEn: '2 people', labelRw: 'Abantu 2' },
  { value: '3 people', labelEn: '3 people', labelRw: 'Abantu 3' },
  { value: '4 people', labelEn: '4 people', labelRw: 'Abantu 4' },
  { value: '5 people', labelEn: '5 people', labelRw: 'Abantu 5' },
  { value: '6 people', labelEn: '6 people', labelRw: 'Abantu 6' },
  { value: '7+ people', labelEn: '7+ people', labelRw: 'Abantu 7+' },
];

export const INCOME_BRACKETS: { value: string; label: string; numericValue: number }[] = [
  { value: '60,000 RWF', label: '60,000 RWF', numericValue: 60000 },
  { value: '120,000 RWF', label: '120,000 RWF', numericValue: 120000 },
  { value: '180,000 RWF', label: '180,000 RWF', numericValue: 180000 },
  { value: '250,000 RWF', label: '250,000 RWF', numericValue: 250000 },
  { value: '350,000 RWF', label: '350,000 RWF', numericValue: 350000 },
  { value: '500,000 RWF', label: '500,000 RWF', numericValue: 500000 },
  { value: '750,000 RWF', label: '750,000 RWF', numericValue: 750000 },
  { value: '1,000,000+ RWF', label: '1,000,000+ RWF', numericValue: 1000000 },
];

export const INITIAL_PROFILE: HouseholdProfile = {
  id: 'usr_01M628ZQ5KAPPWPNCZQZGW1KK6',
  district: 'Gasabo',
  householdSize: '4 people',
  monthlyIncome: '500,000 RWF',
  plannedEssentials: 250000,
  savingsBuffer: 250000,
  preferredLanguage: 'EN',
  currency: 'RWF',
};

export const TRANSLATIONS = {
  EN: {
    brandName: 'Imibereho',
    eyebrow: 'WELCOME',
    heroHeadline: 'Build financial resilience based on your everyday life.',
    heroSubheadline: 'A clearer view of your household budget, grounded in where you live.',
    advisorTitle: 'Smart Budgeting Advisor',
    advisorDescription: 'Imibereho analyzes district living benchmarks, estimates household expenses, and guides you in building an emergency cushion tailored to your daily realities.',
    quickStartBadge: 'A quick starting point · All fields optional',
    fieldDistrictLabel: 'Your district · optional',
    districtPlaceholder: 'Select district',
    fieldHouseholdLabel: 'Household size',
    fieldIncomeLabel: 'Monthly income',
    helperText: 'Example values shown. Income can be an estimate; change it whenever life changes.',
    continueWithoutAccountButton: 'Continue without creating an account',
    createAccountButton: 'Create an account',
    signInButton: 'Sign in / Login',
    orDividerText: 'or access with an account',
    alreadyHaveAccount: 'Already have an account?',
    simulationTitle: 'Household Snapshot Ready',
    simulationSub: 'This mock payload will be sent to the backend endpoint once connected:',
    closeModal: 'Close',
    viewMetrics: 'Simulated Budget Insights',
    estimatedLivingCost: 'Est. Baseline Cost (Gasabo)',
    resilienceBuffer: 'Resilience Buffer',
  },
  RW: {
    brandName: 'Imibereho',
    eyebrow: 'MURAHO NEZA',
    heroHeadline: "Komeza ubushobozi bwawe bwo guhangana n'ubuzima bishingiye ku mibereho ya buri munsi.",
    heroSubheadline: "Isura isobanutse y'ingengo y'imari y'urugo rwawe, ishingiye ku karere utuyemo.",
    advisorTitle: 'Umujyanama mu by’Ingengo y’Imari (Smart Budgeting Advisor)',
    advisorDescription: 'Imibereho isesengura ibiciro by’imibereho mu karere utuyemo, ikagereranya ibikenerwa mu rugo, ikanakuyobora mu kubaka ububiko bwo gutabara buhuye n’ubuzima bwawe bwa buri munsi.',
    quickStartBadge: 'Intangiriro yihuse · Kuzuza ibi byose ni amahitamo',
    fieldDistrictLabel: 'Akarere utuyemo · bitari itegeko',
    districtPlaceholder: 'Hitamo akarere',
    fieldHouseholdLabel: 'Abagize urugo',
    fieldIncomeLabel: 'Amafaranga yinjira ku kwezi',
    helperText: "Ingero z'imibare zatanzwe. Kwinjiza amafaranga bishobora kuba igereranyo; ubihindure igihe cyose ubuzima buhindutse.",
    continueWithoutAccountButton: 'Komeza udakoze konte',
    createAccountButton: 'Kora konte nshya',
    signInButton: 'Injira muri konte',
    orDividerText: 'cyangwa koresha konte',
    alreadyHaveAccount: 'Usanzwe ufite konte?',
    simulationTitle: 'Incamake y’Urugo Yiteguye',
    simulationSub: 'Ibi bintu bizoherezwa kuri backend endpoint igihe izaba yabonetse:',
    closeModal: 'Funga',
    viewMetrics: "Ibipimo by'Ingengo y'Imari",
    estimatedLivingCost: "Igereranyo ry'ikiguzi (Gasabo)",
    resilienceBuffer: 'Ububiko bwo gutabara',
  },
} as const;
