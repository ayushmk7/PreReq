import React from 'react';
import { motion } from 'motion/react';

interface ConceptLensButtonProps {
  variant?: 'primary' | 'secondary' | 'subtle';
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

export const ConceptLensButton: React.FC<ConceptLensButtonProps> = ({
  variant = 'primary',
  children,
  onClick,
  className = '',
  disabled = false,
  type = 'button',
}) => {
  const baseStyles = 'px-6 py-2.5 rounded-[10px] transition-all duration-200 text-sm';
  
  const variantStyles = {
    primary: 'bg-[#FFCB05] text-[#00274C] hover:bg-[#FFD633] disabled:bg-[#FFCB05]/50 font-medium shadow-sm hover:shadow',
    secondary: 'bg-white text-[#00274C] border-2 border-[#00274C] hover:bg-surface disabled:bg-surface/50 font-medium',
    subtle: 'text-foreground-secondary hover:text-[#00274C] hover:bg-surface disabled:text-foreground-secondary/50',
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      whileHover={disabled ? {} : { scale: 1.01 }}
      whileTap={disabled ? {} : { scale: 0.99 }}
    >
      {children}
    </motion.button>
  );
};
