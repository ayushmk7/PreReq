import React from 'react';

interface ConceptLensLogoUMichProps {
  className?: string;
  size?: number;
}

export const ConceptLensLogoUMich: React.FC<ConceptLensLogoUMichProps> = ({ 
  className = '', 
  size = 40 
}) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer circle - represents holistic view */}
      <circle 
        cx="50" 
        cy="50" 
        r="45" 
        stroke="#FFCB05" 
        strokeWidth="2.5" 
        fill="none"
      />
      
      {/* Inner concept nodes - dependency graph */}
      <circle cx="50" cy="25" r="6" fill="#00274C" />
      <circle cx="30" cy="45" r="6" fill="#00274C" />
      <circle cx="70" cy="45" r="6" fill="#00274C" />
      <circle cx="50" cy="65" r="6" fill="#FFCB05" />
      
      {/* Connection lines - showing dependencies */}
      <line x1="50" y1="31" x2="34" y2="42" stroke="#00274C" strokeWidth="2" opacity="0.4" />
      <line x1="50" y1="31" x2="66" y2="42" stroke="#00274C" strokeWidth="2" opacity="0.4" />
      <line x1="30" y1="51" x2="50" y2="59" stroke="#FFCB05" strokeWidth="2.5" opacity="0.6" />
      <line x1="70" y1="51" x2="50" y2="59" stroke="#FFCB05" strokeWidth="2.5" opacity="0.6" />
      
      {/* Lens focal point - magnifying glass suggestion */}
      <circle 
        cx="50" 
        cy="65" 
        r="12" 
        stroke="#FFCB05" 
        strokeWidth="1.5" 
        fill="none"
        opacity="0.3"
      />
    </svg>
  );
};
