export interface BoundingBox {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface AOIPreset {
  id: string;
  name: string;
  category: 'Urban' | 'Agriculture' | 'Forest' | 'Coastal' | 'Mixed';
  description: string;
  bbox: BoundingBox;
  center: [number, number];
  zoom: number;
}

export interface AOIExportForm {
  region: BoundingBox;
  startDate: string;
  endDate: string;
  maxCloudPct: number;
  scale: number;
  gcpProject: string;
}
