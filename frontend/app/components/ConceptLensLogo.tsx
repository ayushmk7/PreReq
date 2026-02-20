import React from 'react';

interface ConceptLensLogoProps {
  size?: number;
}

export const ConceptLensLogo: React.FC<ConceptLensLogoProps> = ({ size = 24 }) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 32 32" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Abstract concept network visualization */}
      <circle cx="16" cy="8" r="3" fill="#2ED3A6" opacity="0.8" />
      <circle cx="8" cy="16" r="2.5" fill="#2ED3A6" opacity="0.6" />
      <circle cx="24" cy="16" r="2.5" fill="#2ED3A6" opacity="0.6" />
      <circle cx="16" cy="24" r="3" fill="#2ED3A6" opacity="0.9" />
      
      {/* Connection lines */}
      <line x1="16" y1="8" x2="8" y2="16" stroke="#2ED3A6" strokeWidth="1.5" opacity="0.3" />
      <line x1="16" y1="8" x2="24" y2="16" stroke="#2ED3A6" strokeWidth="1.5" opacity="0.3" />
      <line x1="8" y1="16" x2="16" y2="24" stroke="#2ED3A6" strokeWidth="1.5" opacity="0.3" />
      <line x1="24" y1="16" x2="16" y2="24" stroke="#2ED3A6" strokeWidth="1.5" opacity="0.3" />
      
      {/* Outer circle frame */}
      <circle cx="16" cy="16" r="14" stroke="#2ED3A6" strokeWidth="1" fill="none" opacity="0.2" />
    </svg>
  );
};
