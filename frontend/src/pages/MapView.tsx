import React from 'react';
import { motion } from 'framer-motion';
import { AOIMap } from '../components/Map/AOIMap';
import { pageVariants } from '../utils/animations';
import { MapPin } from 'lucide-react';

export const MapView: React.FC = () => {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="max-w-6xl mx-auto flex flex-col gap-6 py-2"
    >
      <div className="flex flex-col gap-1.5 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/20 text-cyan-300 text-xs font-bold w-fit mx-auto sm:mx-0">
          <MapPin size={13} className="text-cyan-400" />
          <span>Interactive Sentinel-2 Satellite Selector</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
          Choose an area
        </h1>
        <p className="text-slate-400 text-sm max-w-2xl font-medium">
          Search a place, select presets, or draw custom bounding boxes to query cloud-free Sentinel-2 L2A composites via Google Earth Engine.
        </p>
      </div>

      <AOIMap />
    </motion.div>
  );
};
