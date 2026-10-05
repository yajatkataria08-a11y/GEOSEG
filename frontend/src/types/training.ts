export type PhaseNumber = 1 | 2 | 3 | 4;

export interface PhaseInfo {
  phase: PhaseNumber;
  title: string;
  subtitle: string;
  dataset: string;
  channels: number;
  classes: number;
  metricLabel: string;
  targetMetric: string;
  description: string;
  badgeColor: string;
}

export interface TrainingConfig {
  phase: PhaseNumber;
  configPath?: string;
  epochs: number;
  lr: number;
  batchSize: number;
  loss: 'cross_entropy' | 'dice' | 'dice_ce' | 'focal';
  optimizer: 'adam' | 'adamw' | 'sgd';
  scheduler?: 'cosine' | 'plateau' | 'none';
  useIndices?: boolean;
}

export interface EpochMetrics {
  epoch: number;
  totalEpochs: number;
  trainLoss: number;
  valMetric: number;
  metricName: string;
  perClassIou?: Record<string, number>;
  lr?: number;
  timestamp?: number;
}

export interface TrainingStatus {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopped';
  phase: PhaseNumber | null;
  currentEpoch: number;
  totalEpochs: number;
  metrics: EpochMetrics | null;
  bestMetric: number;
  elapsedSeconds: number;
  message: string;
  history: EpochMetrics[];
}
