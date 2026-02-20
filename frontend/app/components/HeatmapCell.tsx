import React, { useState } from 'react';
import { motion } from 'motion/react';

interface HeatmapCellProps {
  value: number;
  onClick?: () => void;
  row: number;
  col: number;
}

export const HeatmapCell: React.FC<HeatmapCellProps> = ({ value, onClick, row, col }) => {
  const [isHovered, setIsHovered] = useState(false);

  const getColor = (val: number) => {
    if (val >= 0.7) return 'rgba(255, 203, 5, 0.8)';
    if (val >= 0.5) return 'rgba(245, 185, 66, 0.8)';
    return 'rgba(224, 90, 90, 0.8)';
  };

  const getBorderColor = (val: number) => {
    if (val >= 0.7) return '#FFCB05';
    if (val >= 0.5) return '#F5B942';
    return '#E05A5A';
  };

  return (
    <motion.div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="relative cursor-pointer rounded-md overflow-hidden"
      style={{
        backgroundColor: getColor(value),
        aspectRatio: '1',
      }}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: (row + col) * 0.01 }}
      whileHover={{ 
        scale: 1.15, 
        zIndex: 10,
        boxShadow: `0 0 0 2px ${getBorderColor(value)}, 0 4px 12px rgba(0, 39, 76, 0.2)`,
      }}
      whileTap={{ scale: 1.05 }}
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <motion.span 
          className="text-[10px] text-white font-mono font-medium"
          animate={{ scale: isHovered ? 1.2 : 1 }}
          transition={{ duration: 0.2 }}
        >
          {Math.round(value * 100)}
        </motion.span>
      </div>
    </motion.div>
  );
};
