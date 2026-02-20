import React from 'react';

interface ConfidenceBadgeProps {
  level: 'high' | 'medium' | 'low';
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ level }) => {
  const styles = {
    high: 'bg-primary/10 text-primary border-primary/20',
    medium: 'bg-warning/10 text-warning border-warning/20',
    low: 'bg-critical/10 text-critical border-critical/20',
  };

  const labels = {
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-md border text-xs ${styles[level]}`}>
      {labels[level]}
    </span>
  );
};
