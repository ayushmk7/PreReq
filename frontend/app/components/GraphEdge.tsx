import React from 'react';
import { motion } from 'motion/react';
import type { ConceptNode } from '../data/mockData';

interface GraphEdgeProps {
  from: ConceptNode;
  to: ConceptNode;
  isActive?: boolean;
  weight?: number;
}

export const GraphEdge: React.FC<GraphEdgeProps> = ({ 
  from, 
  to, 
  isActive = false,
  weight = 1 
}) => {
  if (!from.x || !from.y || !to.x || !to.y) return null;

  const strokeWidth = Math.max(1, weight * 2);
  const color = isActive ? '#FFCB05' : '#DEE2E6';

  // Calculate arrow position
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const angle = Math.atan2(dy, dx);
  const length = Math.sqrt(dx * dx + dy * dy);
  const nodeRadius = 24;
  
  const startX = from.x + Math.cos(angle) * nodeRadius;
  const startY = from.y + Math.sin(angle) * nodeRadius;
  const endX = to.x - Math.cos(angle) * nodeRadius;
  const endY = to.y - Math.sin(angle) * nodeRadius;

  return (
    <g>
      {/* Main edge line */}
      <motion.line
        x1={startX}
        y1={startY}
        x2={endX}
        y2={endY}
        stroke={color}
        strokeWidth={strokeWidth}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.5 }}
      />
      
      {/* Animated path trace when active */}
      {isActive && (
        <motion.line
          x1={startX}
          y1={startY}
          x2={endX}
          y2={endY}
          stroke="#FFCB05"
          strokeWidth={strokeWidth + 1}
          opacity="0.8"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: [0, 1] }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        />
      )}
      
      {/* Arrow head */}
      <polygon
        points={`${endX},${endY} ${endX - 8 * Math.cos(angle - Math.PI / 6)},${endY - 8 * Math.sin(angle - Math.PI / 6)} ${endX - 8 * Math.cos(angle + Math.PI / 6)},${endY - 8 * Math.sin(angle + Math.PI / 6)}`}
        fill={color}
      />
    </g>
  );
};
