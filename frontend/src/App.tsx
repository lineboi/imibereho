import { useState } from 'react';
import { Header } from './components/Header';
import { HeroIllustration } from './components/HeroIllustration';
import { QuickStartForm } from './components/QuickStartForm';
import { DesktopInsightCard } from './components/DesktopInsightCard';
import { PayloadModal } from './components/PayloadModal';
import { DailyTrackerPage } from './components/DailyTracker/DailyTrackerPage';
import { DistrictAdvisorPage } from './components/DistrictAdvisor/DistrictAdvisorPage';
import { ResilienceSimulatorPage } from './components/ResilienceSimulator/ResilienceSimulatorPage';
import { SeasonalAgroSwapsPage } from './components/SeasonalAgroSwaps/SeasonalAgroSwapsPage';
import { INITIAL_PROFILE, TRANSLATIONS } from './data/mockData';
import type { HouseholdProfile, Language, AppPage, NavTab } from './types';
import { Check, Sparkles } from 'lucide-react';

export function App() {
  const [currentPage, setCurrentPage] = useState<AppPage>('tracker');
  const [activeTab, setActiveTab] = useState<NavTab>('agro_swaps');
  const [language, setLanguage] = useState<Language>('EN');
  const [profile, setProfile] = useState<HouseholdProfile>(INITIAL_PROFILE);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'continue' | 'create_account' | 'sign_in'>('continue');

  const t = TRANSLATIONS[language];

  const handleContinue = (submittedProfile: HouseholdProfile) => {
    setProfile(submittedProfile);
    setModalMode('continue');
    setModalOpen(true);
  };

  const handleCreateAccount = (submittedProfile: HouseholdProfile) => {
    setProfile(submittedProfile);
    setModalMode('create_account');
    setModalOpen(true);
  };

  const handleSignIn = (submittedProfile: HouseholdProfile) => {
    setProfile(submittedProfile);
    setModalMode('sign_in');
    setModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#F8F6F0] text-[#1E2922] flex flex-col font-sans selection:bg-[#1E5E45] selection:text-white">
      {/* Single Main Navigation Header */}
      <Header
        language={language}
        onLanguageChange={setLanguage}
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          setCurrentPage('tracker');
        }}
        onLogoClick={() => setCurrentPage('landing')}
      />

      {/* Conditionally Render Pages */}
      {currentPage === 'tracker' ? (
        activeTab === 'district_advisor' ? (
          <DistrictAdvisorPage
            language={language}
            onNavigateHome={() => setCurrentPage('landing')}
            defaultDistrict={profile.district}
            defaultHouseholdSize={profile.householdSize}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        ) : activeTab === 'resilience' ? (
          <ResilienceSimulatorPage
            language={language}
            onNavigateHome={() => setCurrentPage('landing')}
            district={profile.district}
            householdSize={profile.householdSize}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        ) : activeTab === 'agro_swaps' ? (
          <SeasonalAgroSwapsPage
            language={language}
            onNavigateHome={() => setCurrentPage('landing')}
            district={profile.district}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        ) : (
          <DailyTrackerPage
            language={language}
            onNavigateHome={() => setCurrentPage('landing')}
            district={profile.district}
            householdSize={profile.householdSize}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        )
      ) : (
        /* Landing Page / Welcome Setup */
        <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-8 lg:py-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-14 items-start">
            {/* Main Content & Form Column */}
            <div className="lg:col-span-7 flex flex-col gap-3.5 sm:gap-4">
              {/* Eyebrow tag */}
              <div className="text-[11.5px] sm:text-xs font-bold uppercase tracking-wider text-[#355D47]">
                {t.eyebrow}
              </div>

              {/* Primary Headline */}
              <h1 className="font-serif text-[28px] sm:text-4xl lg:text-[46px] leading-[1.18] sm:leading-[1.15] font-normal text-[#123927] tracking-tight">
                {t.heroHeadline}
              </h1>

              {/* Subtitle description */}
              <p className="text-[13.5px] sm:text-[15px] lg:text-[16px] leading-relaxed text-[#4A5D52] font-normal max-w-xl">
                {t.heroSubheadline}
              </p>

              {/* Smart Budgeting Advisor: Explains what the platform will do */}
              <div className="bg-[#FAF8F4] border border-[#E5DFD4] rounded-2xl p-3.5 sm:p-4 flex items-start gap-3 shadow-2xs my-0.5">
                <div className="w-8 h-8 rounded-xl bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 mt-0.5 border border-[#CFE4D7]">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <span className="text-[11.5px] sm:text-xs font-bold uppercase tracking-wider text-[#1E5E45] block">
                    {t.advisorTitle}
                  </span>
                  <p className="text-[12px] sm:text-[13px] text-[#4F6257] leading-relaxed mt-0.5">
                    {t.advisorDescription}
                  </p>
                </div>
              </div>

              {/* On Mobile Screens: Scenic illustration displays inline right here as in mockup */}
              <div className="block lg:hidden my-1">
                <HeroIllustration district={profile.district} />
              </div>

              {/* Interactive Quick Start Form */}
              <div className="mt-1 sm:mt-2 bg-transparent lg:bg-white lg:p-7 lg:rounded-2xl lg:border lg:border-[#E4DFD5] lg:shadow-xs">
                <QuickStartForm
                  profile={profile}
                  language={language}
                  onProfileChange={setProfile}
                  onSubmit={handleContinue}
                  onCreateAccount={handleCreateAccount}
                  onSignIn={handleSignIn}
                />
              </div>
            </div>

            {/* Right Column (Desktop Only): High-res Scenic Showcase + Live Perspective Card */}
            <div className="hidden lg:block lg:col-span-5 sticky top-24">
              <DesktopInsightCard profile={profile} language={language} />
            </div>
          </div>
        </main>
      )}

      {/* Backend Integration Mock Payload Modal */}
      <PayloadModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        profile={profile}
        language={language}
        mode={modalMode}
        onProceedToTracker={() => setCurrentPage('tracker')}
      />

      {/* Bottom Global Subtle Footer (When on Landing Page) */}
      {currentPage === 'landing' && (
        <footer className="border-t border-[#EAE5DB] bg-[#F2EDE3]/60 py-3.5 px-4 text-center text-xs text-[#7A8A81] mt-auto">
          <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>Imibereho Project · Prototype Demo</span>
            <div className="flex items-center gap-3 text-[11px] text-[#55695E]">
              <span className="flex items-center gap-1">
                <Check className="w-3 h-3 text-[#1E5E45]" />
                <span>Frontend Mock Objects Active</span>
              </span>
              <span>·</span>
              <span>Endpoints Ready to Connect</span>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

export default App;
