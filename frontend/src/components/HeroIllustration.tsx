import React from 'react';

interface HeroIllustrationProps {
  className?: string;
  district?: string;
}

export const HeroIllustration: React.FC<HeroIllustrationProps> = ({
  className = '',
  district = 'Gasabo',
}) => {
  return (
    <figure className={`relative overflow-hidden rounded-2xl shadow-sm border border-[#E4DFD5] bg-[#EAE6DD] group ${className}`}>
      {/* Primary Scenic Painting Asset */}
      <img
        src="/assets/hero-illustration.png"
        alt={`Rural Rwandan homestead and agricultural terraced hills representing ${district}`}
        className="w-full h-auto object-cover object-center transition-transform duration-500 group-hover:scale-[1.02]"
        loading="eager"
      />

      {/* Subtle overlay vignette for artistic depth */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/10 via-transparent to-transparent pointer-events-none" />
    </figure>
  );
};
