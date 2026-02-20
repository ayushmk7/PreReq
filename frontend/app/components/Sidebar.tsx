import React from 'react';
import { motion } from 'motion/react';
import { Home, Upload, LayoutDashboard, GitBranch, User } from 'lucide-react';
import { ConceptLensLogoUMich } from './ConceptLensLogoUMich';

type View = 'landing' | 'upload' | 'dashboard' | 'trace' | 'student';

interface SidebarProps {
  currentView: View;
  onNavigate: (view: View) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onNavigate }) => {
  const navItems = [
    { view: 'landing' as View, icon: Home, label: 'Home' },
    { view: 'upload' as View, icon: Upload, label: 'Upload' },
    { view: 'dashboard' as View, icon: LayoutDashboard, label: 'Dashboard' },
    { view: 'student' as View, icon: User, label: 'Students' },
  ];

  return (
    <div className="fixed left-0 top-0 h-screen w-20 bg-[#00274C] border-r border-[#003366] flex flex-col items-center py-6 z-40">
      {/* Logo */}
      <div className="mb-8">
        <ConceptLensLogoUMich size={48} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-2 w-full px-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.view;
          
          return (
            <motion.button
              key={item.view}
              onClick={() => onNavigate(item.view)}
              className={`relative w-full h-14 rounded-xl flex flex-col items-center justify-center gap-1 transition-colors group ${
                isActive 
                  ? 'bg-[#003366] text-[#FFCB05]' 
                  : 'text-white/60 hover:text-white hover:bg-[#003366]/50'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-[#003366] rounded-xl"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              <Icon className={`w-5 h-5 relative z-10 ${isActive ? 'text-[#FFCB05]' : ''}`} />
              <span className={`text-[10px] relative z-10 ${isActive ? 'text-[#FFCB05]' : ''}`}>
                {item.label}
              </span>
            </motion.button>
          );
        })}
      </nav>

      {/* Bottom indicator */}
      <div className="mt-auto">
        <div className="w-10 h-1 rounded-full bg-[#FFCB05]"></div>
      </div>
    </div>
  );
};
