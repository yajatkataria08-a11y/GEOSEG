export interface LandCoverClass {
  id: number;
  name: string;
  color: string; // Hex code
  rgb: [number, number, number];
  description?: string;
}

export interface InferenceConfig {
  modelCheckpoint: string;
  tileSize: number;
  overlap: number;
  useIndices: boolean;
  batchSize: number;
  device: 'cuda' | 'cpu';
}

export interface InferenceJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  inputPath: string;
  inputFilename: string;
  outputPath?: string;
  previewUrl?: string;
  classDistribution?: Record<string, number>;
  timestamp: string;
  elapsedSeconds: number;
  dimensions?: { width: number; height: number; bands: number };
}

export interface SpectralIndexMap {
  ndvi: string;
  ndwi: string;
  ndbi: string;
}
