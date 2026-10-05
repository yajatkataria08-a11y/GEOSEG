import { fetchApi } from './api';
import { InferenceJob } from '../types/inference';
import { AOIExportForm } from '../types/map';

export const DEMO_MODE = false;

export const inferenceApi = {
  async predict(formData: FormData): Promise<InferenceJob> {
    if (DEMO_MODE) {
      return {
        id: 'job-' + Math.random().toString(36).substring(7),
        status: 'completed',
        inputPath: 'data/uploads/sample_sentinel2.tif',
        inputFilename: 'sample_sentinel2.tif',
        outputPath: 'outputs/predictions/sample_landcover.tif',
        previewUrl: '',
        timestamp: new Date().toISOString(),
        elapsedSeconds: 2.34,
        dimensions: { width: 512, height: 512, bands: 13 },
        classDistribution: {
          'Forest': 38.4,
          'Croplands': 24.1,
          'Water': 14.8,
          'Urban': 12.3,
          'Grasslands': 10.4,
        },
      };
    }

    const response = await fetch('/api/inference/predict', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Inference API call failed with status ${response.status}`);
    }
    
    // We import caseTransform manually here or just rely on fetchApi for subsequent requests
    // but the initial job comes from native fetch so we should probably camelCase it.
    // Wait, the instruction says to just return job from polling.
    // Let's implement it carefully.
    const rawJob = await response.json();
    const initialJob = {
      ...rawJob,
      jobId: rawJob.job_id || rawJob.jobId || rawJob.id,
    };

    let job = initialJob;
    while (job.status === 'pending' || job.status === 'running') {
      await new Promise(r => setTimeout(r, 2000));
      job = await fetchApi<InferenceJob>(`/inference/result/${job.jobId || job.id}`);
    }
    return job;
  },

  async getResult(jobId: string): Promise<InferenceJob> {
    return await fetchApi<InferenceJob>(`/inference/result/${jobId}`);
  },

  async exportAOI(form: AOIExportForm): Promise<{ success: boolean; message: string; task_id?: string; is_synthetic?: boolean; isSynthetic?: boolean }> {
    if (DEMO_MODE) {
      return {
        success: true,
        message: 'Google Earth Engine export task started for region ' + JSON.stringify(form.region),
        task_id: 'gee-task-' + Math.random().toString(36).substring(7),
        isSynthetic: true,
      };
    }

    const payload = {
      west: form.region.west,
      south: form.region.south,
      east: form.region.east,
      north: form.region.north,
      startDate: form.startDate,
      endDate: form.endDate,
      maxCloudPct: form.maxCloudPct,
      scale: form.scale,
    };

    return await fetchApi<{ success: boolean; message: string; task_id?: string; is_synthetic?: boolean; isSynthetic?: boolean }>('/aoi/export', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
