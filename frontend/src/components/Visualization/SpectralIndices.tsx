import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

export const SpectralIndices: React.FC = () => {
  const [selectedIndex, setSelectedIndex] = useState<'ndvi' | 'ndwi' | 'ndbi'>('ndvi');

  const indices = {
    ndvi: {
      name: 'NDVI (Normalized Difference Vegetation Index)',
      formula: '(NIR [B08] - Red [B04]) / (NIR + Red)',
      purpose: 'Quantifies vegetation density and green photosynthetic vigor. Scale -1.0 to +1.0.',
      highMeaning: 'Dense Healthy Forest, Crop Canopy (0.6 - 0.9)',
      lowMeaning: 'Water Bodies (-0.2 - 0.0), Bare Soil, Concrete (0.0 - 0.2)',
      color: '#10b981',
      svgGradient: ['#7f1d1d', '#eab308', '#15803d'],
    },
    ndwi: {
      name: 'NDWI (Normalized Difference Water Index)',
      formula: '(Green [B03] - NIR [B08]) / (Green + NIR)',
      purpose: 'Delineates open water features and surface water bodies from terrestrial land.',
      highMeaning: 'Lakes, Rivers, Ocean Reservoirs (0.3 - 0.8)',
      lowMeaning: 'Dry Land, Urban Infrastructure, Forest Canopy (< 0.0)',
      color: '#38bdf8',
      svgGradient: ['#78350f', '#38bdf8', '#1e3a8a'],
    },
    ndbi: {
      name: 'NDBI (Normalized Difference Built-up Index)',
      formula: '(SWIR1 [B11] - NIR [B08]) / (SWIR1 + NIR)',
      purpose: 'Highlights urban built-up areas, asphalt roadways, and residential impervious surfaces.',
      highMeaning: 'Dense Commercial Urban, Asphalt Highways (0.2 - 0.5)',
      lowMeaning: 'Agricultural Fields, Deep Dense Forests (-0.5 - -0.1)',
      color: '#f59e0b',
      svgGradient: ['#1e3a8a', '#94a3b8', '#ea580c'],
    },
  };

  const current = indices[selectedIndex];

  return (
    <Card
      title="Spectral Indices Engine (Band Math)"
      subtitle="Computed directly from Sentinel-2 multispectral bands via native C++ OOP and PyTorch"
      icon={<Sparkles size={18} className="text-cyan-400" />}
    >
      <div className="flex gap-2 mb-4">
        {(['ndvi', 'ndwi', 'ndbi'] as const).map((key) => {
          const item = indices[key];
          const isSelected = selectedIndex === key;
          return (
            <motion.button
              key={key}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedIndex(key)}
              className={`flex-1 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all border ${
                isSelected
                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-md shadow-cyan-500/20'
                  : 'bg-black/40 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
            >
              {key}
            </motion.button>
          );
        })}
      </div>

      <div className="bg-black/40 rounded-2xl border border-white/5 p-4 sm:p-5 flex flex-col gap-4">
        <div>
          <h4 className="text-base font-bold text-white mb-1.5">{current.name}</h4>
          <div className="inline-block px-3 py-1 bg-white/[0.04] rounded-lg font-mono text-xs text-cyan-300 border border-cyan-500/20">
            Formula: {current.formula}
          </div>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">{current.purpose}</p>

        <div>
          <div className="flex justify-between text-[10px] text-slate-400 font-mono mb-1.5 font-bold">
            <span>-1.0 (Low Response)</span>
            <span>0.0 (Neutral)</span>
            <span>+1.0 (High Response)</span>
          </div>
          <div
            className="h-3 rounded-full shadow-md"
            style={{
              background: `linear-gradient(to right, ${current.svgGradient.join(', ')})`,
            }}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
          <div className="p-3 bg-white/[0.02] rounded-xl border border-white/5">
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block mb-1">
              High Values (+):
            </span>
            <p className="text-xs text-slate-200">{current.highMeaning}</p>
          </div>
          <div className="p-3 bg-white/[0.02] rounded-xl border border-white/5">
            <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider block mb-1">
              Low / Negative (-):
            </span>
            <p className="text-xs text-slate-200">{current.lowMeaning}</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
