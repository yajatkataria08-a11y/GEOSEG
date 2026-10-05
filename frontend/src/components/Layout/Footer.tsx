import React from 'react';
import { Cpu, Satellite, Sparkles } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-cyan-500/10 py-6 px-6 bg-[#040817]/80 backdrop-blur-xl mt-auto z-10">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400 font-medium">
        <div className="flex items-center gap-2">
          <Satellite size={15} className="text-cyan-400" />
          <span>GeoSeg Multispectral Land Cover Semantic Segmentation</span>
          <span className="text-slate-600">•</span>
          <span className="text-slate-300">Sentinel-2 AI</span>
        </div>

        <div className="flex items-center gap-4 text-[11px]">
          <span className="flex items-center gap-1.5 text-cyan-300 font-mono">
            <Cpu size={13} />
            <span>13 Raw Bands + 3 Indices (16ch)</span>
          </span>
          <span className="text-slate-600">•</span>
          <span>PyTorch SMP U-Net + C++ OOP Engine</span>
        </div>
      </div>
    </footer>
  );
};
