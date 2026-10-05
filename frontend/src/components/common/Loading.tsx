import React from 'react';
import { motion } from 'framer-motion';
import { Satellite } from 'lucide-react';

interface LoadingProps {
  text?: string;
  size?: number;
}

export const Loading: React.FC<LoadingProps> = ({
  text = 'Processing satellite multi-band rasters...',
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="relative w-20 h-20 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 border-r-cyan-400/50 shadow-[0_0_15px_rgba(56,189,248,0.3)]"
        />
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-2 rounded-full border-2 border-purple-500/20 border-b-purple-400 border-l-purple-400/50"
        />
        <motion.div
          animate={{ scale: [0.9, 1.1, 0.9] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="w-8 h-8 rounded-full bg-cyan-500/20 backdrop-blur-md flex items-center justify-center text-cyan-300 border border-cyan-400/40 shadow-inner"
        >
          <Satellite size={16} />
        </motion.div>
      </div>

      <motion.p
        animate={{ opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        className="mt-5 text-sm font-medium text-slate-300 tracking-wide text-center max-w-sm"
      >
        {text}
      </motion.p>
    </div>
  );
};
