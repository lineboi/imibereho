import React from 'react';
import type { Language } from '../../types';
import type { ComparisonMode, DistrictBenchmarkData } from '../../data/mockAdvisorData';
import { ADVISOR_TRANSLATIONS } from '../../data/mockAdvisorData';

interface WholePictureCardProps {
  mode: ComparisonMode;
  districtA: DistrictBenchmarkData;
  districtB?: DistrictBenchmarkData;
  language: Language;
}

export const WholePictureCard: React.FC<WholePictureCardProps> = ({
  mode,
  districtA,
  districtB,
  language,
}) => {
  const t = ADVISOR_TRANSLATIONS[language];

  // Dynamic contextual synthesis
  const renderContent = () => {
    if (mode === 'my_plan_vs_benchmark') {
      if (language === 'RW') {
        return 'Ubukode buri hejuru ho 5,000 RWF ku bipimo by’icyitegererezo, mu gihe ibiribwa biri munsi ho 5,000 RWF. Rinda ibikenerwa by’ibanze mbere yo kugabanya amafaranga.';
      }
      return 'Housing is 5,000 RWF above the demo reference, while food is 5,000 RWF below. Protect essentials before making cuts.';
    }

    if (!districtB) return null;

    const diffFood = districtB.lines.find((l) => l.categoryCode === 'food')!.amount -
      districtA.lines.find((l) => l.categoryCode === 'food')!.amount;
    const diffHousing = districtB.lines.find((l) => l.categoryCode === 'housing')!.amount -
      districtA.lines.find((l) => l.categoryCode === 'housing')!.amount;

    if (language === 'RW') {
      return `Ubukode bw’inzu n’ibiribwa nibyo bigize itandukaniro rinini hagati ya ${districtA.districtName} na ${districtB.districtName}. Muri ${districtB.districtName}, ${
        diffFood < 0 ? `ibiribwa bigabanukaho ${Math.abs(diffFood).toLocaleString()} RWF` : 'ibiribwa birisumbuyeho gato'
      }, naho ${
        diffHousing < 0 ? `ubukode bukaba hasi ho ${Math.abs(diffHousing).toLocaleString()} RWF` : 'ubukode burisumbuyeho'
      }. Guhitamo aho gutura bifasha kurinda ubwizigame bw’urugo.`;
    }

    return `Housing and food account for the primary living cost variance between ${districtA.districtName} and ${districtB.districtName}. In ${districtB.districtName}, ${
      diffFood < 0 ? `food essentials are ${Math.abs(diffFood).toLocaleString()} RWF lower` : 'food essentials reflect regional logistics'
    }, while ${
      diffHousing < 0 ? `monthly rent is ${Math.abs(diffHousing).toLocaleString()} RWF lower` : 'housing reflects urban rental density'
    }. Geographic context helps families protect essential emergency buffers.`;
  };

  return (
    <div className="w-full bg-[#EBF1EC] border border-[#DCE6DE] rounded-2xl p-4 sm:p-5 flex flex-col gap-2 shadow-2xs">
      <h3 className="font-serif text-lg sm:text-xl font-normal text-[#133A29]">
        {t.wholePictureTitle}
      </h3>
      <p className="text-[12.5px] sm:text-[13.5px] text-[#3D5245] leading-relaxed">
        {renderContent()}
      </p>
    </div>
  );
};
