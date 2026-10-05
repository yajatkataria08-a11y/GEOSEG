import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { ClassLegend } from './ClassLegend';
import { ImageOverlay } from './ImageOverlay';
import { Download, SplitSquareVertical, Layers } from 'lucide-react';

interface PredictionViewerProps {
  title?: string;
  inputImage?: string;
  predictedMask?: string;
  groundTruthMask?: string;
  distribution?: Record<string, number>;
  scheme?: 'deepglobe' | 'sen12ms';
  onDownload?: () => void;
}

export const PredictionViewer: React.FC<PredictionViewerProps> = ({
  title = 'Sentinel-2 Land Cover Segmentation Result',
  inputImage = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" fill="%23071026"/><path d="M0 0 L512 512 M512 0 L0 512" stroke="%231e293b" stroke-width="2"/><text x="50%" y="45%" fill="%2338bdf8" font-size="22" font-family="sans-serif" text-anchor="middle" font-weight="bold">Sentinel-2 Composite (13 Bands)</text><text x="50%" y="55%" fill="%2394a3b8" font-size="14" font-family="sans-serif" text-anchor="middle">True Color Bands B04, B03, B02</text></svg>',
  predictedMask = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="250" fill="%2310b981" opacity="0.85"/><rect y="250" width="250" height="262" fill="%230284c7" opacity="0.85"/><rect x="250" y="250" width="262" height="262" fill="%23eab308" opacity="0.85"/><circle cx="256" cy="256" r="60" fill="%23ef4444" opacity="0.85"/><text x="50%" y="50%" fill="%23ffffff" font-size="24" font-family="sans-serif" text-anchor="middle" font-weight="bold">Classified Mask</text></svg>',
  groundTruthMask,
  distribution = {
    'Forest Land': 41.2,
    'Agriculture Land': 25.8,
    'Water Bodies': 17.5,
    'Urban Built-up': 10.3,
    'Barren Land': 5.2,
  },
  scheme = 'deepglobe',
  onDownload,
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'overlay'>('side-by-side');

  return (
    <Card
      title={title}
      subtitle="Processed via SMP U-Net (ResNet-34) with 16-Channel Multispectral Input"
      action={
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={viewMode === 'side-by-side' ? 'primary' : 'secondary'}
            onClick={() => setViewMode('side-by-side')}
            icon={<SplitSquareVertical size={13} />}
          >
            Side by Side
          </Button>
          <Button
            size="sm"
            variant={viewMode === 'overlay' ? 'primary' : 'secondary'}
            onClick={() => setViewMode('overlay')}
            icon={<Layers size={13} />}
          >
            Overlay
          </Button>
          {onDownload && (
            <Button
              size="sm"
              variant="accent"
              onClick={onDownload}
              icon={<Download size={13} />}
            >
              Export GeoTIFF
            </Button>
          )}
        </div>
      }
    >
      {viewMode === 'side-by-side' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
          <div className="bg-black/40 p-3 rounded-2xl border border-white/5 space-y-2">
            <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider block">
              Input: Sentinel-2 Composite (13 Bands)
            </span>
            <div className="h-72 rounded-xl overflow-hidden bg-[#050a18]">
              <img src={inputImage} alt="Input Satellite" className="w-full h-full object-cover" />
            </div>
          </div>

          <div className="bg-black/40 p-3 rounded-2xl border border-white/5 space-y-2">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">
              Prediction: U-Net Land Cover Mask
            </span>
            <div className="h-72 rounded-xl overflow-hidden bg-[#050a18]">
              <img src={predictedMask} alt="Predicted Land Cover" className="w-full h-full object-cover" />
            </div>
          </div>
        </div>
      ) : (
        <div className="my-4">
          <ImageOverlay baseImage={inputImage} overlayMask={predictedMask} height="360px" />
        </div>
      )}

      <div className="mt-4">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
          Class Legend & Spatial Area Distribution
        </span>
        <ClassLegend scheme={scheme} distribution={distribution} />
      </div>
    </Card>
  );
};
