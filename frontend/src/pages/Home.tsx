import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { EarthGlobe } from '../components/common/EarthGlobe';
import { Button } from '../components/common/Button';
import { 
  ChevronLeft, 
  ChevronRight, 
  MapPin, 
  Cpu, 
  Satellite, 
  Sparkles, 
  ArrowRight,
  Binary,
  ScanLine
} from 'lucide-react';
import { pageVariants } from '../utils/animations';

interface HomeProps {
  setActiveTab: (tab: string) => void;
}

export const Home: React.FC<HomeProps> = ({ setActiveTab }) => {
  const [currentSlide, setCurrentSlide] = useState<number>(0);

  const slides = [
    {
      id: 'choose-area',
      title: 'Choose an area',
      subtitle: 'Pick a place on the map. You can also upload a GeoTIFF file.',
      actionTab: 'projects',
      actionText: 'Open Map Explorer',
      badge: 'Step 1 • Satellite AOI',
      icon: <MapPin className="w-6 h-6 text-cyan-400" />,
      chips: [
        { name: 'True Color RGB', color: '#38bdf8' },
        { name: 'NDVI Vegetation', color: '#10b981' },
        { name: 'Classified Mask', color: '#a855f7' },
      ]
    },
    {
      id: 'let-learn',
      title: 'Let it learn',
      subtitle: 'We train the model to recognize forests, water, roads, and buildings.',
      actionTab: 'models',
      actionText: 'Configure Training Matrix',
      badge: 'Step 2 • Deep Learning',
      icon: <Cpu className="w-6 h-6 text-purple-400" />,
      metrics: [
        { label: 'Multispectral', val: '16 Bands', sub: '13 Raw + 3 Indices' },
        { label: 'Validation mIoU', val: '74.2%', sub: 'SEN12MS Benchmark' },
        { label: 'Loss Objective', val: 'Dice + CE', sub: 'Class-balanced' },
      ]
    },
    {
      id: 'see-results',
      title: 'See your results',
      subtitle: 'Look at the visual map showing land forms in your area.',
      actionTab: 'results',
      actionText: 'Inspect Predictions',
      badge: 'Step 3 • Land Cover',
      icon: <Satellite className="w-6 h-6 text-emerald-400" />,
      classes: [
        { name: 'Water Bodies', color: '#0284c7' },
        { name: 'Trees & Forest', color: '#10b981' },
        { name: 'Crops & Farm', color: '#eab308' },
        { name: 'Built-up Urban', color: '#ef4444' },
        { name: 'Bare Ground', color: '#f59e0b' },
      ]
    },
  ];

  const handleNext = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
  };

  const handlePrev = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const slide = slides[currentSlide];

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="max-w-6xl mx-auto flex flex-col gap-10 py-4"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center bg-[#09112a]/70 border border-cyan-500/15 rounded-3xl p-8 lg:p-12 backdrop-blur-2xl relative overflow-hidden shadow-2xl shadow-black/50">
        <div className="absolute -top-24 -left-24 w-72 h-72 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-purple-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="lg:col-span-7 flex flex-col items-start gap-6 relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-xs font-bold tracking-wider uppercase"
          >
            <Sparkles size={14} className="text-cyan-400 animate-pulse" />
            <span>Multispectral Sentinel-2 Earth Observation</span>
          </motion.div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white leading-tight">
            Turn satellite photos into <span className="text-gradient-cyan">land maps</span>
          </h1>

          <p className="text-slate-300 text-base sm:text-lg leading-relaxed max-w-xl font-normal">
            End-to-end multi-band remote sensing platform featuring <strong>all 13 Sentinel-2 bands</strong>,{' '}
            <strong>C++ OOP image processing accelerator</strong>, and <strong>pretrained U-Net deep learning models</strong>.
          </p>

          <div className="flex flex-wrap items-center gap-3.5 pt-2">
            <Button
              variant="accent"
              size="lg"
              onClick={() => setActiveTab('projects')}
              icon={<ScanLine size={18} />}
            >
              Choose an Area
            </Button>
            <Button
              variant="secondary"
              size="lg"
              onClick={() => setActiveTab('predict')}
              icon={<Satellite size={18} />}
            >
              Run Prediction
            </Button>
            <Button
              variant="glass"
              size="lg"
              onClick={() => setActiveTab('developers')}
              icon={<Binary size={18} />}
            >
              C++ Engine
            </Button>
          </div>
        </div>

        <div className="lg:col-span-5 flex items-center justify-center relative z-10 py-4">
          <EarthGlobe />
        </div>
      </div>

      <div className="flex flex-col gap-5">
        <div className="text-center space-y-1">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Turn satellite photos into land maps
          </h2>
          <p className="text-slate-400 text-sm font-medium">
            This interactive workflow helps you explore, train, and segment live Earth data
          </p>
        </div>

        <div className="relative max-w-4xl mx-auto w-full">
          <button
            onClick={handlePrev}
            className="absolute -left-4 sm:-left-6 top-1/2 -translate-y-1/2 z-20 p-3 rounded-full bg-[#0d1838]/90 border border-cyan-500/30 text-cyan-300 hover:text-white hover:bg-cyan-500/20 hover:scale-110 active:scale-95 transition-all shadow-xl backdrop-blur-md"
            title="Previous Step"
          >
            <ChevronLeft size={22} />
          </button>
          <button
            onClick={handleNext}
            className="absolute -right-4 sm:-right-6 top-1/2 -translate-y-1/2 z-20 p-3 rounded-full bg-[#0d1838]/90 border border-cyan-500/30 text-cyan-300 hover:text-white hover:bg-cyan-500/20 hover:scale-110 active:scale-95 transition-all shadow-xl backdrop-blur-md"
            title="Next Step"
          >
            <ChevronRight size={22} />
          </button>

          <AnimatePresence mode="wait">
            <motion.div
              key={slide.id}
              initial={{ opacity: 0, x: 40, scale: 0.98 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: -40, scale: 0.98 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="bg-[#0a122c]/85 border border-cyan-500/25 rounded-3xl p-8 sm:p-10 backdrop-blur-2xl shadow-2xl shadow-black/60 relative overflow-hidden"
            >
              <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="flex-1 space-y-4 text-center md:text-left">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/20 text-cyan-300 text-xs font-bold">
                    {slide.icon}
                    <span>{slide.badge}</span>
                  </div>

                  <h3 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                    {slide.title}
                  </h3>

                  <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-md">
                    {slide.subtitle}
                  </p>

                  <div className="pt-2">
                    <Button
                      variant="accent"
                      size="lg"
                      onClick={() => setActiveTab(slide.actionTab)}
                      icon={<ArrowRight size={18} />}
                    >
                      {slide.actionText}
                    </Button>
                  </div>
                </div>

                <div className="flex-1 w-full max-w-sm flex items-center justify-center">
                  {slide.id === 'choose-area' && (
                    <div className="relative w-64 h-64 flex items-center justify-center">
                      <motion.div
                        whileHover={{ scale: 1.08 }}
                        className="w-36 h-36 rounded-full bg-gradient-to-tr from-cyan-900 to-blue-600 p-1 shadow-2xl shadow-cyan-500/40 cursor-pointer overflow-hidden border-2 border-cyan-400"
                      >
                        <div className="w-full h-full rounded-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-700 via-teal-800 to-slate-900 flex items-center justify-center text-center p-3">
                          <span className="text-xs font-bold text-white uppercase tracking-wider">
                            Satellite AOI
                          </span>
                        </div>
                      </motion.div>

                      <motion.div
                        animate={{ y: [-6, 6, -6] }}
                        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                        className="absolute -top-2 right-2 w-20 h-20 rounded-full bg-emerald-950/80 p-1 border-2 border-emerald-400/80 shadow-lg shadow-emerald-500/30 flex items-center justify-center text-center backdrop-blur-md"
                      >
                        <span className="text-[10px] font-bold text-emerald-300">NDVI Green</span>
                      </motion.div>

                      <motion.div
                        animate={{ y: [6, -6, 6] }}
                        transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
                        className="absolute -bottom-2 -left-2 w-22 h-22 rounded-full bg-purple-950/80 p-1 border-2 border-purple-400/80 shadow-lg shadow-purple-500/30 flex items-center justify-center text-center backdrop-blur-md"
                      >
                        <span className="text-[10px] font-bold text-purple-300">Land Mask</span>
                      </motion.div>
                    </div>
                  )}

                  {slide.id === 'let-learn' && (
                    <div className="flex flex-col gap-3 w-full">
                      {slide.metrics?.map((m, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.04] border border-cyan-500/20 hover:border-cyan-400/50 transition-colors backdrop-blur-md"
                        >
                          <div>
                            <span className="text-xs font-medium text-slate-400">{m.label}</span>
                            <span className="text-[10px] text-slate-500 block">{m.sub}</span>
                          </div>
                          <span className="text-base font-extrabold text-cyan-300 font-mono">{m.val}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {slide.id === 'see-results' && (
                    <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 w-full space-y-2.5 backdrop-blur-md">
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
                        Categorical Legend
                      </span>
                      {slide.classes?.map((c, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2.5">
                            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: c.color }} />
                            <span className="text-slate-200 font-medium">{c.name}</span>
                          </div>
                          <span className="text-slate-400 font-mono">Class {i + 1}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          <div className="flex items-center justify-center gap-2.5 mt-5">
            {slides.map((s, idx) => (
              <button
                key={s.id}
                onClick={() => setCurrentSlide(idx)}
                className={`transition-all duration-300 rounded-full h-2 ${
                  currentSlide === idx
                    ? 'w-8 bg-cyan-400 shadow-[0_0_10px_#38bdf8]'
                    : 'w-2 bg-white/20 hover:bg-white/40'
                }`}
                title={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="text-center pt-4 pb-2 border-t border-white/5">
        <p className="text-xs text-slate-500 font-medium">
          An Open-source Sentinel-2 satellite AI framework for Earth observation and land cover semantic segmentation.
        </p>
      </div>
    </motion.div>
  );
};
