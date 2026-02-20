import React from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface CustomTooltipProps {
  content: string | React.ReactNode;
  visible: boolean;
  x: number;
  y: number;
}

export const CustomTooltip: React.FC<CustomTooltipProps> = ({ content, visible, x, y }) => {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="fixed pointer-events-none z-50"
          style={{ left: x, top: y }}
          initial={{ opacity: 0, scale: 0.9, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 10 }}
          transition={{ duration: 0.15 }}
        >
          <div className="bg-elevated border border-border rounded-lg px-3 py-2 shadow-xl">
            <div className="text-xs text-foreground whitespace-nowrap">
              {content}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
