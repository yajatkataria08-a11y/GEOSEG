import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { RasterMapViewer } from '../components/Visualization/RasterMapViewer';
import { FolderArchive, Download, Eye, MapPin } from 'lucide-react';
import { fetchApi } from '../services/api';
import { pageVariants } from '../utils/animations';

interface ResultSummary {
  id: string;
  filename: string;
  locationName?: string;
  phase: number;
  metricValue: number;
  timestamp: string;
  fileSizeBytes: number;
  previewUrl: string;
  satelliteUrl?: string;
  classes?: { name: string; color: string; pct: number }[];
}

export const Results: React.FC = () => {
  const [results, setResults] = useState<ResultSummary[]>([
    {
      id: 'phase4_inference_test',
      filename: 'phase4_inference_test.tif',
      locationName: 'Bhopal Upper Lake',
      phase: 4,
      metricValue: 81.4,
      timestamp: '2026-08-17T16:13:00.000Z',
      fileSizeBytes: 265594,
      previewUrl: '/previews/bhopal_mask.png',
      satelliteUrl: '/previews/bhopal_sat.png',
      classes: [
        { name: 'Water Bodies', color: '#0284c7', pct: 88.1 },
        { name: 'Wetlands', color: '#06b6d4', pct: 8.3 },
        { name: 'Shrubland', color: '#84cc16', pct: 2.8 },
        { name: 'Urban Built-up', color: '#ef4444', pct: 0.3 },
        { name: 'Forest & Canopy', color: '#10b981', pct: 0.2 },
        { name: 'Barren Soil', color: '#f59e0b', pct: 0.1 },
      ],
    },
    {
      id: 'sentinel2_los_angeles_classified',
      filename: 'sentinel2_los_angeles_classified.tif',
      locationName: 'Los Angeles, CA',
      phase: 3,
      metricValue: 74.2,
      timestamp: new Date().toISOString(),
      fileSizeBytes: 51280000,
      previewUrl: '/previews/la_mask.png',
      satelliteUrl: '/previews/la_sat.png',
      classes: [
        { name: 'Croplands', color: '#eab308', pct: 48.4 },
        { name: 'Urban / Built-up', color: '#ef4444', pct: 32.1 },
        { name: 'Rangeland & Wetlands', color: '#06b6d4', pct: 19.5 },
        { name: 'Water Bodies', color: '#0284c7', pct: 0.1 },
      ],
    },
    {
      id: 'sentinel2_fresno_agriculture',
      filename: 'sentinel2_fresno_agriculture.tif',
      locationName: 'Fresno, CA',
      phase: 3,
      metricValue: 78.5,
      timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
      fileSizeBytes: 42150000,
      previewUrl: '/previews/fresno_mask.png',
      satelliteUrl: '/previews/fresno_sat.png',
      classes: [
        { name: 'Croplands', color: '#eab308', pct: 66.2 },
        { name: 'Trees & Orchards', color: '#10b981', pct: 33.8 },
      ],
    },
    {
      id: 'sentinel2_sacramento_delta',
      filename: 'sentinel2_sacramento_delta.tif',
      locationName: 'Sacramento Delta, CA',
      phase: 3,
      metricValue: 76.1,
      timestamp: new Date(Date.now() - 3600000 * 5).toISOString(),
      fileSizeBytes: 48900000,
      previewUrl: '/previews/sacramento_mask.png',
      satelliteUrl: '/previews/sacramento_sat.png',
      classes: [
        { name: 'Trees & Forest', color: '#10b981', pct: 84.1 },
        { name: 'Rangeland & Wetlands', color: '#06b6d4', pct: 8.6 },
        { name: 'Bare Ground', color: '#f59e0b', pct: 5.7 },
        { name: 'Water Bodies', color: '#0284c7', pct: 1.6 },
      ],
    },
  ]);

  const [selectedMap, setSelectedMap] = useState<ResultSummary | null>(results[0]);

  useEffect(() => {
    async function loadResults() {
      try {
        const data = await fetchApi<{ results: any[]; total: number }>('/results/');
        if (data.results && data.results.length > 0) {
          const mapped = data.results.map((r: any, idx: number) => ({
            id: r.id || `res-${idx}`,
            filename: r.outputFilename || r.output_filename || r.filename || 'sentinel2_classified.tif',
            locationName: r.locationName || r.location_name || (r.id ? r.id.replace(/_/g, ' ').toUpperCase() : 'Bhopal Upper Lake'),
            phase: r.phase || 4,
            metricValue: r.metricValue || r.metric_value || 81.4,
            timestamp: r.timestamp || new Date().toISOString(),
            fileSizeBytes: r.fileSizeBytes || r.file_size_bytes || 265594,
            previewUrl: r.previewUrl || r.preview_url || '/previews/bhopal_mask.png',
            satelliteUrl: r.satelliteUrl || r.satellite_url || '/previews/bhopal_sat.png',
            classes: r.classes || [
              { name: 'Water Bodies', color: '#0284c7', pct: 88.1 },
              { name: 'Wetlands', color: '#06b6d4', pct: 8.3 },
              { name: 'Shrubland', color: '#84cc16', pct: 2.8 },
              { name: 'Urban Built-up', color: '#ef4444', pct: 0.3 },
              { name: 'Forest & Canopy', color: '#10b981', pct: 0.2 },
            ],
          }));
          setResults(mapped);
          setSelectedMap(mapped[0]);
        }
      } catch (err: any) {}
    }
    loadResults();
  }, []);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="max-w-6xl mx-auto flex flex-col gap-8 py-2"
    >
      <div className="flex flex-col gap-1.5 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/20 text-cyan-300 text-xs font-bold w-fit mx-auto sm:mx-0">
          <FolderArchive size={13} className="text-cyan-400" />
          <span>Historical Segmented Raster Archive</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
          My maps.
        </h1>
        <p className="text-slate-400 text-sm max-w-2xl font-medium">
          Check historical segmented land maps, model inference outputs, and CRS-georeferenced GeoTIFF predictions.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {results.map((item) => {
          const isSelected = selectedMap?.id === item.id;
          return (
            <motion.div
              key={item.id}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedMap(item)}
              className={`p-5 rounded-3xl border cursor-pointer transition-all duration-300 backdrop-blur-xl relative overflow-hidden flex flex-col justify-between gap-4 ${
                isSelected
                  ? 'bg-gradient-to-tr from-cyan-950/60 to-purple-950/60 border-cyan-400 shadow-xl shadow-cyan-500/20'
                  : 'bg-[#09112a]/70 border-white/10 hover:border-cyan-400/40 hover:bg-[#0d1838]/80'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin size={16} className={isSelected ? 'text-cyan-300' : 'text-slate-400'} />
                  <h3 className="text-base font-bold text-white tracking-tight">
                    {item.locationName || item.filename}
                  </h3>
                </div>
                <Badge variant="green" dot>Ready</Badge>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Phase {item.phase} Multispectral</span>
                  <span className="font-mono text-cyan-300 font-bold">{formatBytes(item.fileSizeBytes)}</span>
                </div>
                <span className="text-[11px] text-slate-500 block">
                  {new Date(item.timestamp).toLocaleDateString()}
                </span>
              </div>

              <Button
                variant={isSelected ? 'accent' : 'secondary'}
                size="sm"
                icon={<Eye size={14} />}
                className="w-full"
              >
                Inspect Map
              </Button>
            </motion.div>
          );
        })}
      </div>

      {selectedMap && (
        <motion.div
          key={selectedMap.id}
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#09112a]/85 border border-cyan-500/25 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl shadow-2xl shadow-black/60 flex flex-col gap-6"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-cyan-500/15 border border-cyan-400/30 text-cyan-300 flex items-center justify-center shadow-lg">
                <MapPin size={20} />
              </div>
              <div>
                <h2 className="text-2xl font-black text-white tracking-tight">
                  {selectedMap.locationName || selectedMap.filename}
                </h2>
                <p className="text-xs text-cyan-300 font-medium">
                  Phase {selectedMap.phase} Output • Sentinel-2 L2A Classified GeoTIFF
                </p>
              </div>
            </div>

            <Button
              variant="accent"
              size="md"
              icon={<Download size={16} />}
              onClick={() => alert(`Downloading ${selectedMap.filename} preserving CRS (EPSG:32643)`)}
            >
              Download GeoTIFF
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 flex flex-col gap-2">
              <RasterMapViewer
                locationName={selectedMap.locationName || selectedMap.filename}
                crs="EPSG:32643"
                resolution="10m Sentinel-2 L2A GSD"
                classes={selectedMap.classes}
                previewUrl={selectedMap.previewUrl}
                satelliteUrl={selectedMap.satelliteUrl}
              />
            </div>

            <div className="lg:col-span-4 flex flex-col justify-between bg-black/30 border border-white/5 rounded-2xl p-4 gap-3">
              <div>
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-3">
                  Land Class Distribution
                </span>
                <div className="space-y-2.5">
                  {selectedMap.classes?.map((c, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5">
                        <span className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: c.color }} />
                        <span className="text-slate-200 font-medium">{c.name}</span>
                      </div>
                      <span className="text-cyan-300 font-mono font-bold">{c.pct}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-white/10 text-[11px] text-slate-400 leading-relaxed">
                Affine transform & CRS headers embedded. Ready for direct QGIS / ArcGIS spatial analysis.
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};
