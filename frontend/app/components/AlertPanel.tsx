import React from 'react';
import { motion } from 'motion/react';
import { AlertTriangle, TrendingDown, Users } from 'lucide-react';
import type { Alert } from '../data/mockData';

interface AlertPanelProps {
  alert: Alert;
  onClick?: () => void;
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alert, onClick }) => {
  const severityStyles = {
    high: 'border-critical/30 bg-critical/5',
    medium: 'border-warning/30 bg-warning/5',
    low: 'border-border bg-surface',
  };

  const severityColors = {
    high: '#E05A5A',
    medium: '#F5B942',
    low: '#9BA7B4',
  };

  return (
    <motion.div
      onClick={onClick}
      className={`border rounded-xl p-4 cursor-pointer transition-all ${severityStyles[alert.severity]}`}
      whileHover={{ scale: 1.01, borderColor: severityColors[alert.severity] }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5">
          <AlertTriangle className="w-4 h-4" style={{ color: severityColors[alert.severity] }} />
        </div>
        <div className="flex-1 space-y-2">
          <h4 className="text-sm text-foreground">{alert.conceptName}</h4>
          <p className="text-xs text-foreground-secondary leading-relaxed">{alert.message}</p>
          
          <div className="flex items-center gap-4 pt-1">
            <div className="flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-foreground-secondary" />
              <span className="text-xs text-foreground-secondary">{alert.studentsAffected} students</span>
            </div>
            <div className="flex items-center gap-1.5">
              <TrendingDown className="w-3.5 h-3.5 text-foreground-secondary" />
              <span className="text-xs text-foreground-secondary">{(alert.impact * 100).toFixed(0)}% impact</span>
            </div>
          </div>

          {/* Impact intensity bar */}
          <div className="w-full h-1 bg-surface rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: severityColors[alert.severity] }}
              initial={{ width: 0 }}
              animate={{ width: `${alert.impact * 100}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
};
