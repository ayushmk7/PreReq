import React from 'react';
import { motion } from 'motion/react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  trend?: {
    value: number;
    label: string;
  };
  color?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({ 
  icon: Icon, 
  label, 
  value, 
  trend,
  color = '#2ED3A6'
}) => {
  return (
    <motion.div
      className="bg-surface border border-border rounded-xl p-5"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-start justify-between mb-3">
        <div 
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${color}15` }}
        >
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        {trend && (
          <div className="text-right">
            <div className="text-xs" style={{ color: trend.value >= 0 ? '#2ED3A6' : '#E05A5A' }}>
              {trend.value >= 0 ? '+' : ''}{trend.value}%
            </div>
            <div className="text-[10px] text-foreground-secondary">{trend.label}</div>
          </div>
        )}
      </div>
      
      <div className="space-y-1">
        <div className="text-2xl text-foreground">{value}</div>
        <div className="text-xs text-foreground-secondary">{label}</div>
      </div>
    </motion.div>
  );
};
