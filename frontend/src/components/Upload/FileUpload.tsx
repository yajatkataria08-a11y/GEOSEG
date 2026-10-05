import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../common/Button';
import { UploadCloud, CheckCircle2, AlertCircle } from 'lucide-react';

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  acceptedFormats?: string[];
  maxSizeMB?: number;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelected,
  acceptedFormats = ['.tif', '.tiff', '.jp2', '.png', '.jpg'],
  maxSizeMB = 250,
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File exceeds maximum size of ${maxSizeMB} MB`);
      return;
    }

    setError(null);
    setSelectedFile(file);
    onFileSelected(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="flex flex-col gap-3">
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={acceptedFormats.join(',')}
        onChange={(e) => handleFiles(e.target.files)}
      />

      <motion.div
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-10 text-center cursor-pointer transition-all duration-300 backdrop-blur-xl ${
          dragActive
            ? 'border-cyan-400 bg-cyan-500/10 shadow-[0_0_30px_rgba(56,189,248,0.25)]'
            : 'border-cyan-500/25 bg-[#081026]/70 hover:border-cyan-400/60 hover:bg-[#0a1533]/80 shadow-xl'
        }`}
      >
        <motion.div
          animate={{ y: [-3, 3, -3] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          className="w-14 h-14 rounded-2xl bg-cyan-500/15 border border-cyan-400/30 text-cyan-300 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-cyan-500/20"
        >
          <UploadCloud size={28} />
        </motion.div>

        <h4 className="text-base font-bold text-white mb-1">
          Drag & drop Sentinel-2 GeoTIFF or satellite tile
        </h4>
        <p className="text-xs text-slate-400 mb-4 max-w-sm mx-auto leading-relaxed">
          Supports 13-band multispectral GeoTIFF, JP2, or RGB imagery up to {maxSizeMB} MB
        </p>

        <Button variant="secondary" size="sm" className="shadow-md">
          Browse Local Files
        </Button>
      </motion.div>

      {selectedFile && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-between backdrop-blur-md"
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle2 size={18} className="text-emerald-400" />
            <span className="text-xs font-semibold text-white truncate max-w-xs">
              {selectedFile.name}
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </span>
          </div>
          <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
            Ready for Inference
          </span>
        </motion.div>
      )}

      {error && (
        <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
