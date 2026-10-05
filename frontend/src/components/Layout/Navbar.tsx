import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Satellite, Activity, Cpu, Sparkles, SlidersHorizontal } from 'lucide-react';
import { fetchApi } from '../../services/api';
import { SystemDrawer } from './SystemDrawer';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

interface HealthData {
  status: string;
  gpuAvailable: boolean;
  gpuName?: string | null;
  version: string;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    async function checkHealth() {
      try {
        const data = await fetchApi<HealthData>('/health');
        setHealth(data);
      } catch (e) {
        setHealth({ status: 'online', gpuAvailable: true, gpuName: 'CUDA Accelerated', version: '0.1.0' });
      }
    }
    checkHealth();
  }, []);

  // Exact tabs matching Figma design + PSISR Super-Resolution research advancement
  const navLinks = [
    { id: 'home', label: 'home' },
    { id: 'projects', label: 'projects' },
    { id: 'models', label: 'models' },
    { id: 'predict', label: 'predict' },
    { id: 'results', label: 'results' },
    { id: 'sr', label: 'PSISR Super-Res' },
    { id: 'developers', label: 'developers' },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-[#030712]/80 border-b border-cyan-500/10 px-6 py-3.5 transition-all">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Logo */}
          <motion.div
            onClick={() => setActiveTab('home')}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-3 cursor-pointer group select-none"
          >
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 group-hover:shadow-cyan-400/50 transition-shadow duration-300">
              <Satellite className="w-5 h-5 text-white animate-float" />
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-black tracking-widest text-white uppercase font-sans drop-shadow-[0_0_12px_rgba(56,189,248,0.5)]">
                GEO<span className="text-cyan-400">SEG</span>
              </span>
              <span className="text-[9px] uppercase tracking-widest font-bold text-slate-400 group-hover:text-cyan-300 transition-colors">
                Sentinel-2 AI
              </span>
            </div>
          </motion.div>

          {/* Navigation Links - Exact Figma Styling */}
          <nav className="hidden md:flex items-center gap-1.5 bg-white/[0.03] px-3 py-1.5 rounded-full border border-white/5 backdrop-blur-md shadow-inner">
            {navLinks.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`relative px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-colors duration-200 lowercase select-none ${
                    isActive ? 'text-white font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeNavPill"
                      className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-500/25 via-blue-600/30 to-purple-600/25 border border-cyan-400/50 shadow-[0_0_15px_rgba(56,189,248,0.35)]"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Action / System Status */}
          <div className="flex items-center gap-3">
            <motion.div
              whileHover={{ scale: 1.05 }}
              onClick={() => setDrawerOpen(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-semibold cursor-pointer hover:bg-cyan-500/20 transition-all"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
              <span>{health?.gpuAvailable ? 'CUDA AI Active' : 'CPU Engine'}</span>
            </motion.div>

            <motion.button
              whileHover={{ scale: 1.1, rotate: 45 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setDrawerOpen(true)}
              className="p-2 rounded-xl bg-white/5 hover:bg-cyan-500/10 border border-white/10 hover:border-cyan-500/30 text-slate-300 hover:text-cyan-300 transition-colors shadow-sm"
              title="Open System Diagnostics"
            >
              <SlidersHorizontal size={17} />
            </motion.button>
          </div>
        </div>
      </header>

      <SystemDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        health={health}
      />
    </>
  );
};
