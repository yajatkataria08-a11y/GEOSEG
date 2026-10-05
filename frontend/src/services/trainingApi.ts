import { fetchApi } from './api';
import { TrainingConfig, TrainingStatus } from '../types/training';

export const DEMO_MODE = false;

export const trainingApi = {
  async start(config: TrainingConfig): Promise<{ success: boolean; message: string; run_id?: string }> {
    if (DEMO_MODE) {
      return {
        success: true,
        message: `Training started locally for Phase ${config.phase}`,
        run_id: 'sim-' + Math.random().toString(36).substring(7),
      };
    }

    return await fetchApi<{ success: boolean; message: string; run_id?: string }>('/training/start', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  async getStatus(): Promise<TrainingStatus> {
    if (DEMO_MODE) {
      return {
        status: 'idle',
        phase: 3,
        currentEpoch: 18,
        totalEpochs: 30,
        metrics: {
          epoch: 18,
          totalEpochs: 30,
          trainLoss: 0.2845,
          valMetric: 0.742,
          metricName: 'mIoU',
          lr: 0.00035,
          perClassIou: {
            'Evergreen Forest': 0.86,
            'Deciduous Forest': 0.81,
            'Shrublands': 0.72,
            'Savannas': 0.69,
            'Grasslands': 0.75,
            'Wetlands': 0.84,
            'Croplands': 0.79,
            'Urban': 0.68,
          },
        },
        bestMetric: 0.742,
        elapsedSeconds: 840,
        message: 'Phase 3 Multispectral U-Net training active',
        history: [],
      };
    }

    return await fetchApi<TrainingStatus>('/training/status');
  },

  async stop(): Promise<{ success: boolean; message: string }> {
    if (DEMO_MODE) {
      return { success: true, message: 'Training stopped' };
    }

    return await fetchApi<{ success: boolean; message: string }>('/training/stop', { method: 'POST' });
  },
};
