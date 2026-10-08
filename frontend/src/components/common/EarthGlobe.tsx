import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RotateCcw, Play, Pause, ZoomIn, ZoomOut, Navigation } from 'lucide-react';
import earthTexture from '../../assets/nasa-earth.jpg';

interface Pin {
  id: string;
  name: string;
  type: 'satellite' | 'aoi';
  coords: string;
  baseX: number; // percentage 0-100
  baseY: number; // percentage 0-100
  description: string;
}

const TARGET_PINS: Pin[] = [
  {
    id: 's2a',
    name: 'Sentinel-2A Orbit',
    type: 'satellite',
    coords: 'Alt 786 km • 98.6° SSO',
    baseX: 48,
    baseY: 38,
    description: '13 Spectral Bands (10m-60m GSD) Active Telemetry',
  },
  {
    id: 'bhopal',
    name: 'Bhopal AOI (India)',
    type: 'aoi',
    coords: '23.25°N, 77.41°E',
    baseX: 68,
    baseY: 42,
    description: 'Multispectral Test AOI • Agriculture & Water Index',
  },
  {
    id: 'california',
    name: 'California AOI (USA)',
    type: 'aoi',
    coords: '36.77°N, 119.41°W',
    baseX: 28,
    baseY: 36,
    description: 'Urban & Farmland High-Resolution Benchmark',
  },
];

export const EarthGlobe: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [autoRotate, setAutoRotate] = useState(true);
  const [posX, setPosX] = useState(0);
  const [pitch, setPitch] = useState(11); // Earth axial tilt
  const [scale, setScale] = useState(1);
  const [activePin, setActivePin] = useState<Pin | null>(null);

  const dragStartRef = useRef<{ x: number; y: number; startPosX: number; startPitch: number }>({
    x: 0,
    y: 0,
    startPosX: 0,
    startPitch: 11,
  });
  const animFrameRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(performance.now());

  // Continuous auto-rotation animation loop when not dragging
  useEffect(() => {
    const animate = (time: number) => {
      const dt = (time - lastTimeRef.current) / 1000;
      lastTimeRef.current = time;

      if (autoRotate && !isDragging) {
        setPosX((prev) => (prev + 20 * dt) % 2048);
      }
      animFrameRef.current = requestAnimationFrame(animate);
    };

    lastTimeRef.current = performance.now();
    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [autoRotate, isDragging]);

  // Pointer drag event handlers for mouse & touch
  const handlePointerDown = (e: React.PointerEvent) => {
    setIsDragging(true);
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      startPosX: posX,
      startPitch: pitch,
    };
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;

    // Horizontal spin (wrapping seamlessly)
    setPosX((dragStartRef.current.startPosX - dx * 1.5) % 2048);

    // Vertical pitch tilt (clamped between -28deg and +28deg)
    const newPitch = Math.max(-28, Math.min(28, dragStartRef.current.startPitch + dy * 0.25));
    setPitch(newPitch);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    setIsDragging(false);
    try {
      (e.target as HTMLElement).releasePointerCapture?.(e.pointerId);
    } catch {}
  };

  // Zoom with mouse wheel
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setScale((prev) => Math.max(0.85, Math.min(1.35, prev - e.deltaY * 0.001)));
  };

  const resetView = useCallback(() => {
    setPosX(0);
    setPitch(11);
    setScale(1);
    setAutoRotate(true);
    setActivePin(null);
  }, []);

  return (
    <div 
      className="relative w-full max-w-[420px] aspect-square flex flex-col items-center justify-center select-none"
      onWheel={handleWheel}
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

      {/* Interactive Earth Sphere Container */}
      <div 
        className="relative w-[320px] h-[320px] rounded-full overflow-hidden shadow-[0_0_55px_rgba(56,189,248,0.4)] border border-cyan-400/40 bg-[#071830] cursor-grab active:cursor-grabbing transition-transform duration-100 ease-out touch-none"
        style={{ transform: `scale(${scale})` }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      >
        {/* Real NASA Blue Marble Textured Surface with Drag & Auto-Rotation */}
        <div 
          className="absolute inset-0 w-full h-full rounded-full"
          style={{
            backgroundColor: '#071830',
            backgroundImage: `url(${earthTexture})`,
            backgroundSize: 'auto 100%',
            backgroundRepeat: 'repeat-x',
            backgroundPosition: `${-posX}px 0`,
            transform: `rotate(${pitch}deg)`,
            transition: isDragging ? 'none' : 'transform 0.2s ease-out',
          }}
        />

        {/* Latitude & Longitude Coordinate Overlay Grid */}
        <svg className="absolute inset-0 w-full h-full opacity-30 pointer-events-none" viewBox="0 0 100 100">
          <ellipse cx="50" cy="50" rx="49" ry="49" fill="none" stroke="#38bdf8" strokeWidth="0.4" />
          <ellipse cx="50" cy="50" rx="49" ry="36" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
          <ellipse cx="50" cy="50" rx="49" ry="22" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
          <line x1="1" y1="50" x2="99" y2="50" stroke="#38bdf8" strokeWidth="0.5" />
          <line x1="50" y1="1" x2="50" y2="99" stroke="#38bdf8" strokeWidth="0.5" />
          <ellipse cx="50" cy="50" rx="36" ry="49" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
          <ellipse cx="50" cy="50" rx="20" ry="49" fill="none" stroke="#38bdf8" strokeWidth="0.25" strokeDasharray="1,2" />
        </svg>

        {/* 3D Spherical Night-Side Terminator Shadow & Specular Depth Glow */}
        <div 
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            boxShadow: `
              inset -45px -35px 80px 15px rgba(0, 0, 0, 0.95),
              inset 20px 20px 45px 5px rgba(56, 189, 248, 0.45),
              inset -10px -10px 30px rgba(0, 0, 0, 0.8)
            `
          }}
        />

        {/* Atmospheric Rim Fresnel Lighting Effect */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-cyan-500/20 via-transparent to-transparent pointer-events-none mix-blend-screen" />
        <div className="absolute inset-0 rounded-full bg-gradient-to-b from-transparent via-transparent to-black/70 pointer-events-none" />

        {/* Interactive Target Pins */}
        {TARGET_PINS.map((pin) => {
          // Adjust pin X dynamically based on rotation
          const offsetPercentage = ((pin.baseX + (posX / 2048) * 100) % 100);
          const isVisible = offsetPercentage > 15 && offsetPercentage < 85;
          if (!isVisible) return null;

          return (
            <div
              key={pin.id}
              className="absolute pointer-events-auto cursor-pointer z-20 group"
              style={{
                top: `${pin.baseY}%`,
                left: `${offsetPercentage}%`,
                transform: 'translate(-50%, -50%)',
              }}
              onClick={(e) => {
                e.stopPropagation();
                setActivePin(activePin?.id === pin.id ? null : pin);
              }}
            >
              <div className="relative flex items-center justify-center">
                <span className={`w-3.5 h-3.5 rounded-full ${pin.type === 'satellite' ? 'bg-cyan-400' : 'bg-emerald-400'} shadow-[0_0_10px_currentColor] animate-ping opacity-75`} />
                <span className={`absolute w-2 h-2 rounded-full ${pin.type === 'satellite' ? 'bg-cyan-300' : 'bg-emerald-300'} border border-white`} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Floating Interactive HUD Overlay & Tooltip */}
      <AnimatePresence>
        {activePin && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.95 }}
            className="absolute top-2 z-30 px-3.5 py-2 rounded-xl bg-slate-900/90 border border-cyan-400/40 backdrop-blur-md shadow-[0_8px_24px_rgba(0,0,0,0.6)] text-xs text-white max-w-[260px] pointer-events-auto"
          >
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
                <Navigation className="w-3 h-3 text-cyan-400" />
                {activePin.name}
              </span>
              <button 
                onClick={() => setActivePin(null)} 
                className="text-slate-400 hover:text-white text-[10px] px-1 py-0.5 rounded bg-slate-800"
              >
                ✕
              </button>
            </div>
            <div className="text-[11px] text-cyan-100 font-mono mb-1">{activePin.coords}</div>
            <div className="text-[10px] text-slate-300 leading-tight">{activePin.description}</div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Interactive Controls Dock (Drag • Spin • Zoom • Reset) */}
      <div className="mt-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-950/80 border border-cyan-500/30 backdrop-blur-md shadow-lg z-20 text-xs text-slate-300">
        <span className="text-[10px] font-mono text-cyan-400/80 uppercase tracking-wider flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          Drag to Rotate
        </span>

        <span className="text-slate-600">|</span>

        {/* Play / Pause Auto-Rotate */}
        <button
          onClick={() => setAutoRotate(!autoRotate)}
          className="p-1 rounded-full hover:bg-slate-800 text-slate-300 hover:text-cyan-300 transition-colors"
          title={autoRotate ? "Pause Auto-Rotation" : "Resume Auto-Rotation"}
        >
          {autoRotate ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
        </button>

        {/* Zoom Controls */}
        <button
          onClick={() => setScale((s) => Math.min(1.35, s + 0.1))}
          className="p-1 rounded-full hover:bg-slate-800 text-slate-300 hover:text-cyan-300 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setScale((s) => Math.max(0.85, s - 0.1))}
          className="p-1 rounded-full hover:bg-slate-800 text-slate-300 hover:text-cyan-300 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>

        {/* Reset View */}
        <button
          onClick={resetView}
          className="p-1 rounded-full hover:bg-slate-800 text-slate-300 hover:text-cyan-300 transition-colors"
          title="Reset View"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
