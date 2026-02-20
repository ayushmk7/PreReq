import React, { useState } from 'react';
import { motion } from 'motion/react';
import { ConceptLensButton } from '../components/ConceptLensButton';
import { Network, TrendingDown, Brain, Users, Target, LineChart, ArrowRight, Shield } from 'lucide-react';
import { ImageWithFallback } from '../components/figma/ImageWithFallback';
import { config } from '../services/config';

interface LandingPageProps {
  onLogin: (username: string, password: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onLogin }) => {
  const [username, setUsername] = useState(config.instructorUsername);
  const [password, setPassword] = useState(config.instructorPassword);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin(username, password);
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Grid pattern */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.03]">
          <defs>
            <pattern id="umich-grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#00274C" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#umich-grid)" />
        </svg>

        {/* Abstract data visualization image */}
        <motion.div
          className="absolute top-20 right-10 w-96 h-96 opacity-5"
          animate={{ 
            y: [0, -30, 0],
            rotate: [0, 3, 0]
          }}
          transition={{ 
            duration: 12, 
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        >
          <ImageWithFallback
            src="https://images.unsplash.com/photo-1664526936810-ec0856d31b92?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGdlb21ldHJpYyUyMG5ldHdvcmslMjBub2Rlc3xlbnwxfHx8fDE3NzE1NjIxOTV8MA&ixlib=rb-4.1.0&q=80&w=1080"
            alt="Network visualization"
            className="w-full h-full object-cover rounded-3xl"
          />
        </motion.div>

        {/* Neural network pattern */}
        <motion.div
          className="absolute bottom-32 left-10 w-80 h-80 opacity-5"
          animate={{ 
            y: [0, 20, 0],
            rotate: [0, -3, 0]
          }}
          transition={{ 
            duration: 10, 
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 1
          }}
        >
          <ImageWithFallback
            src="https://images.unsplash.com/photo-1744130268219-3efd622e04fb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxuZXVyYWwlMjBuZXR3b3JrJTIwcGF0dGVybnxlbnwxfHx8fDE3NzE1NjIxOTZ8MA&ixlib=rb-4.1.0&q=80&w=1080"
            alt="Neural pattern"
            className="w-full h-full object-cover rounded-3xl"
          />
        </motion.div>

        {/* Animated concept graph SVG */}
        <motion.div 
          className="absolute top-1/3 right-1/4 opacity-10"
          animate={{ 
            y: [0, -20, 0],
            rotate: [0, 5, 0]
          }}
          transition={{ 
            duration: 8, 
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        >
          <svg width="400" height="300" viewBox="0 0 400 300">
            <circle cx="100" cy="50" r="20" fill="none" stroke="#FFCB05" strokeWidth="2.5" opacity="0.6" />
            <circle cx="200" cy="50" r="20" fill="none" stroke="#FFCB05" strokeWidth="2.5" opacity="0.6" />
            <circle cx="150" cy="130" r="20" fill="none" stroke="#00274C" strokeWidth="2" opacity="0.6" />
            <circle cx="250" cy="130" r="20" fill="none" stroke="#00274C" strokeWidth="2" opacity="0.6" />
            <circle cx="200" cy="220" r="20" fill="none" stroke="#FFCB05" strokeWidth="2.5" opacity="0.6" />
            
            <line x1="100" y1="70" x2="150" y2="110" stroke="#00274C" strokeWidth="2" opacity="0.3" />
            <line x1="200" y1="70" x2="150" y2="110" stroke="#00274C" strokeWidth="2" opacity="0.3" />
            <line x1="200" y1="70" x2="250" y2="110" stroke="#00274C" strokeWidth="2" opacity="0.3" />
            <line x1="150" y1="150" x2="200" y2="200" stroke="#FFCB05" strokeWidth="2.5" opacity="0.4" />
            <line x1="250" y1="150" x2="200" y2="200" stroke="#FFCB05" strokeWidth="2.5" opacity="0.4" />
          </svg>
        </motion.div>

        {/* Maize accent circles */}
        <motion.div
          className="absolute top-1/4 left-1/3 w-64 h-64 rounded-full bg-[#FFCB05] opacity-[0.02] blur-3xl"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/3 w-96 h-96 rounded-full bg-[#00274C] opacity-[0.02] blur-3xl"
          animate={{ scale: [1.2, 1, 1.2] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <div className="relative z-10">
        {/* Hero Section */}
        <div className="flex items-center justify-center min-h-screen px-4 py-20">
          <div className="w-full max-w-6xl space-y-20">
            {/* Hero Content */}
            <div className="text-center space-y-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="space-y-6"
              >
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#00274C]/5 border border-[#00274C]/10 text-sm text-foreground">
                  <div className="w-2 h-2 rounded-full bg-[#FFCB05] animate-pulse"></div>
                  AI-Powered Assessment Intelligence
                </div>
                
                <h1 className="text-6xl text-foreground leading-tight max-w-4xl mx-auto">
                  Transform Exam Data into<br />
                  <span className="relative inline-block">
                    <span className="text-[#00274C]">Actionable Insights</span>
                    <motion.div
                      className="absolute -bottom-2 left-0 right-0 h-1 bg-[#FFCB05]"
                      initial={{ width: 0 }}
                      animate={{ width: '100%' }}
                      transition={{ delay: 0.5, duration: 0.8 }}
                    />
                  </span>
                </h1>
                
                <p className="text-xl text-foreground-secondary leading-relaxed max-w-2xl mx-auto">
                  PreReq analyzes student assessment data to reveal conceptual weaknesses, 
                  prerequisite gaps, and personalized intervention strategies—backed by dependency-aware AI.
                </p>
              </motion.div>

              <motion.form
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.8 }}
                className="flex flex-wrap gap-3 justify-center items-end pt-4"
                onSubmit={handleSubmit}
              >
                <input
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="px-4 py-3 rounded-xl border border-border bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#FFCB05] w-40"
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="px-4 py-3 rounded-xl border border-border bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#FFCB05] w-40"
                />
                <ConceptLensButton 
                  variant="primary" 
                  type="submit"
                  className="px-8 py-3 text-lg group inline-flex items-center justify-center"
                >
                  Start Now
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </ConceptLensButton>
              </motion.form>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.8 }}
                className="flex flex-wrap gap-8 justify-center pt-8 text-sm text-foreground-secondary"
              >
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-[#FFCB05]" />
                  Dependency-aware concept mapping
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-[#FFCB05]" />
                  Institutional-grade security
                </div>
                <div className="flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-[#FFCB05]" />
                  Root-cause intervention insights
                </div>
              </motion.div>
            </div>

            {/* Feature Grid */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.8 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {/* Feature 1 */}
              <motion.div 
                className="bg-white border border-border rounded-2xl p-6 space-y-4 hover:border-[#FFCB05] hover:shadow-lg transition-all"
                whileHover={{ y: -5 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#FFCB05]/10 flex items-center justify-center">
                  <Network className="w-6 h-6 text-[#00274C]" />
                </div>
                <div>
                  <h3 className="text-lg text-foreground mb-2">Dependency Mapping</h3>
                  <p className="text-sm text-foreground-secondary leading-relaxed">
                    See how topics connect so you can quickly spot what students should learn first.
                  </p>
                </div>
              </motion.div>

              {/* Feature 2 */}
              <motion.div 
                className="bg-white border border-border rounded-2xl p-6 space-y-4 hover:border-[#FFCB05] hover:shadow-lg transition-all"
                whileHover={{ y: -5 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#00274C]/10 flex items-center justify-center">
                  <TrendingDown className="w-6 h-6 text-[#00274C]" />
                </div>
                <div>
                  <h3 className="text-lg text-foreground mb-2">Root-Cause Analysis</h3>
                  <p className="text-sm text-foreground-secondary leading-relaxed">
                    Understand why scores drop by tracing problems back to the concepts students missed.
                  </p>
                </div>
              </motion.div>

              {/* Feature 3 */}
              <motion.div 
                className="bg-white border border-border rounded-2xl p-6 space-y-4 hover:border-[#FFCB05] hover:shadow-lg transition-all"
                whileHover={{ y: -5 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#FFCB05]/10 flex items-center justify-center">
                  <Brain className="w-6 h-6 text-[#00274C]" />
                </div>
                <div>
                  <h3 className="text-lg text-foreground mb-2">Concept Heatmaps</h3>
                  <p className="text-sm text-foreground-secondary leading-relaxed">
                    Get a clear visual snapshot of who is struggling and which topics need extra support.
                  </p>
                </div>
              </motion.div>

              {/* Feature 4 */}
              <motion.div 
                className="bg-white border border-border rounded-2xl p-6 space-y-4 hover:border-[#FFCB05] hover:shadow-lg transition-all"
                whileHover={{ y: -5 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#FFCB05]/10 flex items-center justify-center">
                  <Users className="w-6 h-6 text-[#00274C]" />
                </div>
                <div>
                  <h3 className="text-lg text-foreground mb-2">Student Profiles</h3>
                  <p className="text-sm text-foreground-secondary leading-relaxed">
                    View easy-to-read student summaries with practical next-step recommendations.
                  </p>
                </div>
              </motion.div>

              {/* Feature 5 */}
              <motion.div 
                className="bg-white border border-border rounded-2xl p-6 space-y-4 hover:border-[#FFCB05] hover:shadow-lg transition-all"
                whileHover={{ y: -5 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#00274C]/10 flex items-center justify-center">
                  <Target className="w-6 h-6 text-[#00274C]" />
                </div>
                <div>
                  <h3 className="text-lg text-foreground mb-2">Intervention Alerts</h3>
                  <p className="text-sm text-foreground-secondary leading-relaxed">
                    Receive timely alerts when a student may need help, along with suggested actions.
                  </p>
                </div>
              </motion.div>

              {/* Feature 6 */}
              <motion.div 
                className="bg-white border border-border rounded-2xl p-6 space-y-4 hover:border-[#FFCB05] hover:shadow-lg transition-all"
                whileHover={{ y: -5 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#FFCB05]/10 flex items-center justify-center">
                  <LineChart className="w-6 h-6 text-[#00274C]" />
                </div>
                <div>
                  <h3 className="text-lg text-foreground mb-2">Longitudinal Tracking</h3>
                  <p className="text-sm text-foreground-secondary leading-relaxed">
                    Track progress over time to see what is improving and what still needs attention.
                  </p>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </div>

        {/* Stats Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.8 }}
          className="px-4 py-20 border-t border-border"
        >
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <motion.div 
                className="text-center space-y-2"
                whileHover={{ scale: 1.05 }}
              >
                <div className="text-4xl text-[#00274C]">98%</div>
                <div className="text-sm text-foreground-secondary">Prediction Accuracy</div>
              </motion.div>
              <motion.div 
                className="text-center space-y-2"
                whileHover={{ scale: 1.05 }}
              >
                <div className="text-4xl text-[#00274C]">15min</div>
                <div className="text-sm text-foreground-secondary">Average Analysis Time</div>
              </motion.div>
              <motion.div 
                className="text-center space-y-2"
                whileHover={{ scale: 1.05 }}
              >
                <div className="text-4xl text-[#00274C]">50K+</div>
                <div className="text-sm text-foreground-secondary">Students Analyzed</div>
              </motion.div>
              <motion.div 
                className="text-center space-y-2"
                whileHover={{ scale: 1.05 }}
              >
                <div className="text-4xl text-[#00274C]">200+</div>
                <div className="text-sm text-foreground-secondary">Institutions</div>
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Footer */}
        <div className="px-4 py-12 border-t border-border">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-center gap-6">
              <p className="text-sm text-foreground-secondary">
                PreReq © 2026 — AI-Powered Assessment Intelligence for Higher Education
              </p>
              <div className="flex gap-6 text-sm text-foreground-secondary">
                <a href="#" className="hover:text-[#FFCB05] transition-colors">Privacy Policy</a>
                <a href="#" className="hover:text-[#FFCB05] transition-colors">Terms of Service</a>
                <a href="#" className="hover:text-[#FFCB05] transition-colors">Contact</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
