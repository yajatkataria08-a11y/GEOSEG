import React from 'react';
import { Button } from '../common/Button';
import { Download, Sliders, Calendar, Cloud, Crosshair, Layers } from 'lucide-react';
import { AOIExportForm } from '../../types/map';

interface MapControlsProps {
  form: AOIExportForm;
  setForm: React.Dispatch<React.SetStateAction<AOIExportForm>>;
  onExport: () => void;
  exporting?: boolean;
}

export const MapControls: React.FC<MapControlsProps> = ({
  form,
  setForm,
  onExport,
  exporting = false,
}) => {
  return (
    <div className="bg-[#0b132b]/80 border border-cyan-500/20 rounded-3xl p-5 backdrop-blur-xl shadow-xl flex flex-col gap-4">
      <div className="flex items-center gap-2.5 pb-2 border-b border-white/10">
        <Sliders size={18} className="text-cyan-400" />
        <h4 className="text-sm font-bold text-white tracking-wide">
          Earth Engine Export Parameters
        </h4>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Calendar size={13} className="text-cyan-400" />
            Start Date
          </label>
          <input
            type="date"
            className="bg-[#060c20] border border-cyan-500/20 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition-all font-mono"
            value={form.startDate}
            onChange={(e) => setForm({ ...form, startDate: e.target.value })}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Calendar size={13} className="text-cyan-400" />
            End Date
          </label>
          <input
            type="date"
            className="bg-[#060c20] border border-cyan-500/20 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition-all font-mono"
            value={form.endDate}
            onChange={(e) => setForm({ ...form, endDate: e.target.value })}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <span className="flex items-center gap-1.5">
              <Cloud size={13} className="text-cyan-400" />
              Max Cloud
            </span>
            <span className="text-cyan-300 font-mono">{form.maxCloudPct}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="30"
            value={form.maxCloudPct}
            onChange={(e) => setForm({ ...form, maxCloudPct: parseInt(e.target.value) })}
            className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg mt-2"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Layers size={13} className="text-cyan-400" />
            Resolution
          </label>
          <select
            className="bg-[#060c20] border border-cyan-500/20 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition-all font-sans cursor-pointer"
            value={form.scale}
            onChange={(e) => setForm({ ...form, scale: parseInt(e.target.value) })}
          >
            <option value={10}>10m (Sentinel-2 Native)</option>
            <option value={20}>20m (Fast Preview)</option>
            <option value={60}>60m (Overview)</option>
          </select>
        </div>
      </div>

      <div className="p-3.5 rounded-2xl bg-black/40 border border-white/5">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
          AOI Bounding Box (WGS84 Coordinates)
        </span>
        <div className="grid grid-cols-4 gap-2 text-xs font-mono">
          <div>
            <span className="text-[10px] text-slate-500 block mb-0.5">West</span>
            <input
              type="number"
              step="0.01"
              className="w-full bg-[#081026] border border-white/10 rounded-lg px-2 py-1 text-cyan-300 text-[11px] focus:outline-none focus:border-cyan-400"
              value={form.region.west}
              onChange={(e) => setForm({ ...form, region: { ...form.region, west: parseFloat(e.target.value) || 0 } })}
            />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 block mb-0.5">South</span>
            <input
              type="number"
              step="0.01"
              className="w-full bg-[#081026] border border-white/10 rounded-lg px-2 py-1 text-cyan-300 text-[11px] focus:outline-none focus:border-cyan-400"
              value={form.region.south}
              onChange={(e) => setForm({ ...form, region: { ...form.region, south: parseFloat(e.target.value) || 0 } })}
            />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 block mb-0.5">East</span>
            <input
              type="number"
              step="0.01"
              className="w-full bg-[#081026] border border-white/10 rounded-lg px-2 py-1 text-cyan-300 text-[11px] focus:outline-none focus:border-cyan-400"
              value={form.region.east}
              onChange={(e) => setForm({ ...form, region: { ...form.region, east: parseFloat(e.target.value) || 0 } })}
            />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 block mb-0.5">North</span>
            <input
              type="number"
              step="0.01"
              className="w-full bg-[#081026] border border-white/10 rounded-lg px-2 py-1 text-cyan-300 text-[11px] focus:outline-none focus:border-cyan-400"
              value={form.region.north}
              onChange={(e) => setForm({ ...form, region: { ...form.region, north: parseFloat(e.target.value) || 0 } })}
            />
          </div>
        </div>
      </div>

      <Button
        variant="accent"
        size="lg"
        onClick={onExport}
        loading={exporting}
        icon={<Download size={17} />}
        className="w-full mt-1"
      >
        Export GeoTIFF from Earth Engine
      </Button>
    </div>
  );
};
