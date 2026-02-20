import React from 'react';
import { motion } from 'motion/react';

interface LoadingSpinnerProps {
  size?: number;
  color?: string;
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 48, 
  color = '#2ED3A6',
  message 
}) => {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <motion.div
        className="relative"
        style={{ width: size, height: size }}
      >
        {/* Outer rotating ring */}
        <motion.div
          className="absolute inset-0 rounded-full border-4"
          style={{ 
            borderColor: `${color}20`,
            borderTopColor: color,
          }}
          animate={{ rotate: 360 }}
          transition={{ 
            duration: 1.2, 
            repeat: Infinity, 
            ease: 'linear' 
          }}
        />
        
        {/* Inner pulsing circle */}
        <motion.div
          className="absolute inset-2 rounded-full"
          style={{ backgroundColor: `${color}10` }}
          animate={{ 
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity, 
            ease: 'easeInOut' 
          }}
        />
      </motion.div>
      
      {message && (
        <motion.p
          className="text-sm text-foreground-secondary"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {message}
        </motion.p>
      )}
    </div>
  );
};
