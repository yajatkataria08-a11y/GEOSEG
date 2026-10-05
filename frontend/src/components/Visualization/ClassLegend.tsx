import React from 'react';
import { LandCoverClass } from '../../types/inference';

export const DEEPGLOBE_CLASSES: LandCoverClass[] = [
  { id: 0, name: 'Urban Land', color: '#ef4444', rgb: [239, 68, 68], description: 'Built-up structures, roads, infrastructure' },
  { id: 1, name: 'Agriculture Land', color: '#eab308', rgb: [234, 179, 8], description: 'Croplands, planted fields, orchards' },
  { id: 2, name: 'Rangeland', color: '#d946ef', rgb: [217, 70, 239], description: 'Pasture, open meadow, grasslands' },
  { id: 3, name: 'Forest Land', color: '#10b981', rgb: [16, 185, 129], description: 'Evergreen, deciduous tree cover' },
  { id: 4, name: 'Water Bodies', color: '#0284c7', rgb: [2, 132, 199], description: 'Rivers, lakes, reservoirs, oceans' },
  { id: 5, name: 'Barren Land', color: '#f59e0b', rgb: [245, 158, 11], description: 'Exposed rock, sand, bare soil' },
  { id: 6, name: 'Unknown / Cloud', color: '#64748b', rgb: [100, 116, 139], description: 'Cloud cover, sensor shadows' },
];

export const SEN12MS_CLASSES: LandCoverClass[] = [
  { id: 0, name: 'Evergreen Forest', color: '#006400', rgb: [0, 100, 0] },
  { id: 1, name: 'Deciduous Forest', color: '#00c800', rgb: [0, 200, 0] },
  { id: 2, name: 'Shrublands', color: '#bdb76b', rgb: [189, 183, 107] },
  { id: 3, name: 'Grasslands', color: '#d2b48c', rgb: [210, 180, 140] },
  { id: 4, name: 'Wetlands', color: '#00bfff', rgb: [0, 191, 255] },
  { id: 5, name: 'Croplands', color: '#ffa500', rgb: [255, 165, 0] },
  { id: 6, name: 'Urban / Built-up', color: '#ef4444', rgb: [239, 68, 68] },
];

interface ClassLegendProps {
  scheme?: 'deepglobe' | 'sen12ms';
  distribution?: Record<string, number>;
}

export const ClassLegend: React.FC<ClassLegendProps> = ({
  scheme = 'deepglobe',
  distribution,
}) => {
  const classes = scheme === 'deepglobe' ? DEEPGLOBE_CLASSES : SEN12MS_CLASSES;

  return (
    <div className="flex flex-wrap gap-2.5 p-3.5 bg-black/40 rounded-2xl border border-white/5">
      {classes.map((cls) => {
        const pct = distribution ? distribution[cls.name] : undefined;

        return (
          <div
            key={cls.id}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.03] border border-white/5 hover:border-cyan-400/40 transition-colors text-xs"
          >
            <span
              className="w-3 h-3 rounded-full shadow-sm flex-shrink-0"
              style={{ backgroundColor: cls.color, boxShadow: `0 0 8px ${cls.color}50` }}
            />
            <span className="text-slate-200 font-medium">{cls.name}</span>
            {pct !== undefined && (
              <span className="text-cyan-300 font-mono font-bold text-[11px]">
                {pct}%
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};
