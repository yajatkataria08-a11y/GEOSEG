import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Activity, Cpu, Server, HardDrive, ShieldCheck, Zap, Layers, Sparkles } from 'lucide-react';

interface SystemDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  health: {
    status: string;
    gpuAvailable: boolean;
    gpuName?: string | null;
    version: string;
  } | null;
}

export const SystemDrawer: React.FC<SystemDrawerProps> = ({ isOpen, onClose, health }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          <motion.div
            initial={{ x: '100%', opacity: 0.5 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 26, stiffness: 280 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-[#080e22]/95 border-l border-cyan-500/20 backdrop-blur-2xl p-6 z-50 flex flex-col justify-between shadow-2xl shadow-cyan-950/50"
          >
            <div>
              <div className="flex items-center justify-between pb-5 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                    <Activity className="w-5 h-5 text-white animate-pulse" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">System Diagnostics</h3>
                    <p className="text-xs text-cyan-400 font-medium">Sentinel-2 AI Pipeline Engine</p>
                  </div>
                </div>
                <motion.button
                  whileHover={{ scale: 1.1, rotate: 90 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={onClose}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                >
                  <X size={18} />
                </motion.button>
              </div>

              <div className="mt-6 space-y-4">
                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:border-cyan-500/30 transition-colors">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                      <Server size={16} className="text-cyan-400" />
                      <span>FastAPI Core Server</span>
                    </div>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                      {health?.status === 'ok' ? 'ONLINE' : 'ACTIVE'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">Port 8000 • Reverse Proxy Active • v{health?.version || '0.1.0'}</p>
                </div>

                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:border-cyan-500/30 transition-colors">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                      <Zap size={16} className="text-amber-400" />
                      <span>Inference Accelerator</span>
                    </div>
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                      health?.gpuAvailable 
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                        : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                    }`}>
                      {health?.gpuAvailable ? 'CUDA ACTIVE' : 'CPU SIMD'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    {health?.gpuAvailable ? (health.gpuName || 'NVIDIA GPU Acceleration') : 'PyTorch CPU TorchGeo Inference Engine'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:border-purple-500/30 transition-colors">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                      <Cpu size={16} className="text-purple-400" />
                      <span>C++ OOP Native Module</span>
                    </div>
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      LINKED
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">pybind11 Zero-copy • TileManager 4.8× Speedup</p>
                </div>

                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:border-cyan-500/30 transition-colors">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-2">
                    <Layers size={16} className="text-cyan-400" />
                    <span>Spectral Pipeline Configuration</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-black/30 border border-white/5">
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Raw Bands</span>
                      <span className="text-white font-mono font-semibold">13 Bands (B01-B12)</span>
                    </div>
                    <div className="p-2 rounded-lg bg-black/30 border border-white/5">
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Spectral Math</span>
                      <span className="text-cyan-300 font-mono font-semibold">NDVI, NDWI, NDBI</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-white/10 text-center">
              <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
                <Sparkles size={14} className="text-cyan-400" />
                <span>GeoSeg Multispectral Earth Engine v0.1</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
