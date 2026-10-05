import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type SpectralLayerType = 'satellite' | 'ndvi' | 'ndwi' | 'mask' | 'topo';

interface SpectralLayerCanvasProps {
  layer: SpectralLayerType;
  className?: string;
  isThumbnail?: boolean;
}

export const SpectralLayerCanvas: React.FC<SpectralLayerCanvasProps> = ({
  layer,
  className = '',
  isThumbnail = false,
}) => {
  return (
    <div className={`relative w-full h-full overflow-hidden select-none ${className}`}>
      {layer === 'satellite' && (
        <div className="w-full h-full bg-[#071329] relative overflow-hidden">
          <img
            src="/previews/bhopal_sat.png"
            alt="Sentinel-2 Optical Satellite L2A"
            className="w-full h-full object-cover select-none"
          />
        </div>
      )}

      {layer === 'ndvi' && (
        <div className="w-full h-full bg-[#120824] relative overflow-hidden">
          {/* NDVI Heatmap (Red to Yellow to Dark Green) */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#450a0a] via-[#1c1917] to-[#052e16]" />
          
          <svg className="w-full h-full" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice">
            <defs>
              <radialGradient id="denseVeg" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#10b981" />
                <stop offset="60%" stopColor="#059669" />
                <stop offset="100%" stopColor="#047857" />
              </radialGradient>
              <radialGradient id="modVeg" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#facc15" />
                <stop offset="70%" stopColor="#ca8a04" />
                <stop offset="100%" stopColor="#854d0e" />
              </radialGradient>
              <radialGradient id="barrenRed" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ef4444" />
                <stop offset="70%" stopColor="#b91c1c" />
                <stop offset="100%" stopColor="#7f1d1d" />
              </radialGradient>
            </defs>

            {/* Dense Canopy Patches */}
            <path d="M0,0 L220,0 Q180,100 120,140 Q60,180 0,180 Z" fill="url(#denseVeg)" opacity="0.9" />
            <path d="M220,0 L400,0 L400,160 Q300,140 210,180 Z" fill="url(#denseVeg)" opacity="0.85" />
            <path d="M0,180 Q100,170 180,210 Q240,240 280,300 L0,300 Z" fill="url(#denseVeg)" opacity="0.88" />

            {/* Crops / Moderate Canopy */}
            <circle cx="280" cy="80" r="55" fill="url(#modVeg)" opacity="0.8" />
            <circle cx="70" cy="80" r="40" fill="url(#modVeg)" opacity="0.75" />

            {/* Non-Vegetated Barren / Urban Core (Red) */}
            <circle cx="160" cy="110" r="36" fill="url(#barrenRed)" opacity="0.85" />
            <circle cx="220" cy="100" r="26" fill="url(#barrenRed)" opacity="0.8" />

            {/* Water Tributary (Negative NDVI - Dark Purple/Black) */}
            <path d="M400,40 Q280,70 190,140 T0,260" stroke="#020617" strokeWidth="4" fill="none" />
          </svg>
        </div>
      )}

      {layer === 'ndwi' && (
        <div className="w-full h-full bg-[#020617] relative overflow-hidden">
          {/* NDWI Water Index (Cyan to Deep Cobalt Blue) */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#082f49] via-[#0c4a6e] to-[#020617]" />
          
          <svg className="w-full h-full" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice">
            <defs>
              <linearGradient id="ndwiWater" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="50%" stopColor="#0284c7" />
                <stop offset="100%" stopColor="#0369a1" />
              </linearGradient>
            </defs>

            {/* Dry Land (Dark Brown/Gray) */}
            <path d="M0,0 L400,0 L400,300 L0,300 Z" fill="#0f172a" opacity="0.85" />

            {/* Ocean Basin & Deep Waters */}
            <path d="M400,300 L200,300 Q260,200 340,150 L400,120 Z" fill="url(#ndwiWater)" opacity="0.95" />
            <path d="M0,0 L180,0 Q120,120 0,160 Z" fill="#1e293b" opacity="0.9" />

            {/* Wetland & Reservoirs */}
            <ellipse cx="140" cy="180" rx="45" ry="25" fill="#38bdf8" opacity="0.9" filter="drop-shadow(0 0 8px #0284c7)" />
            <circle cx="280" cy="80" r="18" fill="#38bdf8" opacity="0.85" />

            {/* River network */}
            <path d="M400,40 Q280,70 190,140 T0,260" stroke="#38bdf8" strokeWidth="5" fill="none" opacity="0.95" filter="drop-shadow(0 0 6px #38bdf8)" />
          </svg>
        </div>
      )}

      {layer === 'mask' && (
        <div className="w-full h-full bg-[#030712] relative overflow-hidden">
          <img
            src="/previews/bhopal_mask.png"
            alt="Sentinel-2 Classified Raster"
            className="w-full h-full object-cover select-none"
            style={{ imageRendering: 'pixelated' }}
          />
        </div>
      )}

      {layer === 'topo' && (
        <div className="w-full h-full bg-[#080e22] relative overflow-hidden">
          {/* Topo / Street Grid */}
          <svg className="w-full h-full opacity-60" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice">
            {/* Grid Coordinates */}
            {[0, 50, 100, 150, 200, 250, 300, 350, 400].map((x) => (
              <line key={x} x1={x} y1="0" x2={x} y2="300" stroke="#38bdf8" strokeWidth="0.5" strokeDasharray="3,3" />
            ))}
            {[0, 50, 100, 150, 200, 250, 300].map((y) => (
              <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="#38bdf8" strokeWidth="0.5" strokeDasharray="3,3" />
            ))}

            {/* Contour Elevation Loops */}
            <ellipse cx="160" cy="110" rx="90" ry="60" fill="none" stroke="#a855f7" strokeWidth="1" opacity="0.5" />
            <ellipse cx="160" cy="110" rx="65" ry="40" fill="none" stroke="#a855f7" strokeWidth="1" opacity="0.7" />
            <ellipse cx="160" cy="110" rx="40" ry="22" fill="none" stroke="#a855f7" strokeWidth="1.2" opacity="0.9" />
          </svg>
        </div>
      )}

      {/* Futuristic Scanline Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_50%,rgba(0,0,0,0.25)_51%)] bg-[length:100%_4px] pointer-events-none opacity-40" />

      {/* Corner Brackets on Main Viewport */}
      {!isThumbnail && (
        <>
          <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-cyan-400 pointer-events-none" />
          <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-cyan-400 pointer-events-none" />
          <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-cyan-400 pointer-events-none" />
          <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-cyan-400 pointer-events-none" />
        </>
      )}
    </div>
  );
};
