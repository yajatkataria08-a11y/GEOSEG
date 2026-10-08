import { fetchApi } from './api';

export interface MetricData {
  psnr: number;
  ssim: number;
  correlationEfficiency: number;
  correlation_efficiency?: number;
  mse: number;
}

export interface BenchmarkRow {
  method: string;
  psnr2x?: number;
  psnr_2x?: number;
  ssim2x?: number;
  ssim_2x?: number;
  psnr4x?: number;
  psnr_4x?: number;
  ssim4x?: number;
  ssim_4x?: number;
  psnr8x?: number;
  psnr_8x?: number;
  ssim8x?: number;
  ssim_8x?: number;
  paramsM?: number;
  params_m?: number;
  correlationPct?: number;
  correlation_pct?: number;
  isProposed?: boolean;
  is_proposed?: boolean;
  gainPsnr?: string;
  gain_psnr?: string;
  gainSsim?: string;
  gain_ssim?: string;
}


export interface BenchmarkResponse {
  dataset: string;
  scales: string[];
  comparisonTable: BenchmarkRow[];
  comparison_table?: BenchmarkRow[];
}

export interface PaperMetadata {
  title: string;
  journal: string;
  year: number;
  volume: number;
  articleId: string;
  pii: string;
  doi: string;
  authors: string[];
  affiliations: string[];
  datasetUrl: string;
  keyContributions: string[];
  lossFunction: string;
  architecturalModules: string[];
  performanceMetrics: Record<string, string>;
}

export interface AIDSample {
  id: string;
  className: string;
  class_name?: string;
  color: string;
  description: string;
  url: string;
}

export interface AIDDatasetInfo {
  dataset: string;
  totalClasses: number;
  imageResolution: string;
  samples: AIDSample[];
}

export interface UpscaleResult {
  status: string;
  scaleFactor: number;
  inputResolution: string;
  outputResolution: string;
  lrUrl: string;
  srUrl: string;
  metrics: MetricData;
  modelEfficiency: number;
  flops: string;
  correlationEfficiencyPct: number;
}

export const superResolutionApi = {
  async getBenchmarks(): Promise<BenchmarkResponse> {
    return await fetchApi<BenchmarkResponse>('/sr/benchmarks');
  },

  async getPaperMetadata(): Promise<PaperMetadata> {
    return await fetchApi<PaperMetadata>('/sr/paper-metadata');
  },

  async getAidDataset(): Promise<AIDDatasetInfo> {
    return await fetchApi<AIDDatasetInfo>('/sr/aid-dataset');
  },

  async upscale(imageId: string, scaleFactor: 2 | 4 | 8): Promise<UpscaleResult> {
    return await fetchApi<UpscaleResult>('/sr/upscale', {
      method: 'POST',
      body: JSON.stringify({
        imageId,
        scaleFactor,
      }),
    });
  },
};
