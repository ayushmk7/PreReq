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
    <img
      src="/icon.png"
      alt="PreReq logo"
      width={size}
      height={size}
      className={`object-contain ${className}`}
    />
  );
};
