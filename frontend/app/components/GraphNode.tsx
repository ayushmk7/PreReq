import React from 'react';
import { motion } from 'motion/react';
import type { ConceptNode } from '../data/mockData';

interface GraphNodeProps {
  node: ConceptNode;
  isSelected?: boolean;
  onClick?: () => void;
  size?: number;
}

export const GraphNode: React.FC<GraphNodeProps> = ({ 
  node, 
  isSelected = false, 
  onClick,
  size = 48 
}) => {
  const getColor = (readiness: number) => {
    if (readiness >= 0.7) return '#FFCB05';
    if (readiness >= 0.5) return '#F5B942';
    return '#E05A5A';
  };

  const color = getColor(node.readiness);
  const isBelowThreshold = node.readiness < 0.5;

  return (
    <motion.g
      onClick={onClick}
      style={{ cursor: 'pointer' }}
      whileHover={{ scale: 1.05 }}
      animate={isBelowThreshold ? {
        scale: [1, 1.05, 1],
      } : {}}
      transition={isBelowThreshold ? {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      } : {}}
    >
      {/* Outer ring for selected state */}
      {isSelected && (
        <motion.circle
          cx={node.x}
          cy={node.y}
          r={size / 2 + 4}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
        />
      )}
      
      {/* Main node circle */}
      <circle
        cx={node.x}
        cy={node.y}
        r={size / 2}
        fill="#FFFFFF"
        stroke={color}
        strokeWidth="2.5"
      />
      
      {/* Inner fill for readiness */}
      <circle
        cx={node.x}
        cy={node.y}
        r={(size / 2) * node.readiness}
        fill={color}
        opacity="0.15"
      />
      
      {/* Concept label */}
      <text
        x={node.x}
        y={(node.y ?? 0) + size / 2 + 16}
        textAnchor="middle"
        fill="#00274C"
        fontSize="12"
        fontWeight="500"
        fontFamily="system-ui, -apple-system, sans-serif"
      >
        {node.name}
      </text>
      
      {/* Readiness percentage */}
      <text
        x={node.x}
        y={(node.y ?? 0) + 4}
        textAnchor="middle"
        fill={color}
        fontSize="11"
        fontWeight="600"
        fontFamily="system-ui, -apple-system, sans-serif"
      >
        {Math.round(node.readiness * 100)}%
      </text>
    </motion.g>
  );
};
