import React, { useState } from 'react';
import { motion } from 'framer-motion';

export const EarthGlobe: React.FC = () => {
  const [isPaused, setIsPaused] = useState(false);

  return (
    <div 
      className="relative w-full max-w-[420px] aspect-square flex items-center justify-center select-none"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Outer Atmospheric Cosmic Glow */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-cyan-500/25 via-blue-600/35 to-purple-600/20 blur-[50px] pointer-events-none animate-pulse" />

      {/* Orbit 1: Outer Inclined Satellite Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 22, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-[-18px] rounded-full border border-cyan-400/25 border-dashed pointer-events-none"
        style={{ transform: 'rotateX(68deg) rotateY(-15deg)' }}
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full bg-cyan-400 shadow-[0_0_15px_#38bdf8] flex items-center justify-center">
          <div className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
        </div>
      </motion.div>

      {/* Orbit 2: Inner Polar Satellite Ring */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 32, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-[-30px] rounded-full border border-purple-400/25 border-dotted pointer-events-none"
        style={{ transform: 'rotateX(75deg) rotateY(40deg)' }}
      >
        <div className="absolute bottom-0 right-1/4 w-3 h-3 rounded-full bg-purple-400 shadow-[0_0_12px_#c084fc] flex items-center justify-center">
          <div className="w-1 h-1 rounded-full bg-white" />
        </div>
      </motion.div>

      {/* Earth Sphere Container */}
      <div className="relative w-[320px] h-[320px] rounded-full overflow-hidden shadow-[0_0_50px_rgba(56,189,248,0.35)] border border-cyan-400/40 bg-[#020817] group cursor-grab active:cursor-grabbing">
        
        {/* Real NASA Blue Marble Textured Surface with Continuous Axial Spin */}
        <div 
          className="absolute inset-0 w-full h-full rounded-full"
          style={{
            backgroundImage: "url('/assets/nasa-earth.jpg')",
            backgroundSize: 'auto 100%',
            backgroundRepeat: 'repeat-x',
            animation: `earthSpin 32s linear infinite ${isPaused ? 'paused' : 'running'}`,
            transform: 'rotate(11deg)', // Realistic Earth axial tilt
          }}
        />

        {/* Latitude & Longitude Coordinate Overlay Grid */}
        <svg className="absolute inset-0 w-full h-full opacity-25 pointer-events-none" viewBox="0 0 100 100">
          <ellipse cx="50" cy="50" rx="49" ry="49" fill="none" stroke="#38bdf8" strokeWidth="0.4" />
          <ellipse cx="50" cy="50" rx="49" ry="36" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
          <ellipse cx="50" cy="50" rx="49" ry="22" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
          <line x1="1" y1="50" x2="99" y2="50" stroke="#38bdf8" strokeWidth="0.5" />
          <line x1="50" y1="1" x2="50" y2="99" stroke="#38bdf8" strokeWidth="0.5" />
          <ellipse cx="50" cy="50" rx="36" ry="49" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
          <ellipse cx="50" cy="50" rx="20" ry="49" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
        </svg>

        {/* 3D Spherical Night-Side Terminator Shadow & Atmospheric Specular Glow */}
        <div 
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            boxShadow: `
              inset -45px -35px 80px 15px rgba(0, 0, 0, 0.96),
              inset 20px 20px 45px 5px rgba(56, 189, 248, 0.45),
              inset -10px -10px 30px rgba(0, 0, 0, 0.8)
            `
          }}
        />

        {/* Atmospheric Rim Fresnel Lighting Effect */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-cyan-500/20 via-transparent to-transparent pointer-events-none mix-blend-screen" />
        <div className="absolute inset-0 rounded-full bg-gradient-to-b from-transparent via-transparent to-black/70 pointer-events-none" />

        {/* Live Sentinel-2 Tracking Target Pins */}
        <div className="absolute top-[42%] left-[48%] -translate-x-1/2 -translate-y-1/2 pointer-events-none flex flex-col items-center">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#38bdf8] animate-ping" />
          <span className="w-1.5 h-1.5 rounded-full bg-white -mt-2" />
        </div>

        <div className="absolute top-[36%] left-[68%] -translate-x-1/2 -translate-y-1/2 pointer-events-none flex flex-col items-center">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] animate-ping" />
          <span className="w-1.5 h-1.5 rounded-full bg-white -mt-2" />
        </div>
      </div>

      {/* Animation keyframe injected inline for zero-config rotation */}
      <style>{`
        @keyframes earthSpin {
          0% { background-position: 0px 0; }
          100% { background-position: 640px 0; }
        }
      `}</style>
    </div>
  );
};
