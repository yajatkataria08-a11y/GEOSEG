import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CheckCircle2, ArrowRight, Layers, Target, Cpu, Satellite } from 'lucide-react';
import { PhaseInfo, PhaseNumber } from '../../types/training';

interface PhaseTrackerProps {
  currentPhase: PhaseNumber;
  onSelectPhase?: (phase: PhaseNumber) => void;
}

export const phasesData: PhaseInfo[] = [
  {
    phase: 1,
    title: 'EuroSAT Classifier',
    subtitle: 'Pipeline Validation Baseline',
    dataset: 'EuroSAT (27k tiles)',
    channels: 13,
    classes: 10,
    metricLabel: 'Accuracy',
    targetMetric: '92.4%',
    description: 'Proves environment, torchgeo dataloaders, and PyTorch training loops work with 13-band Sentinel-2 input.',
    badgeColor: 'blue',
  },
  {
    phase: 2,
    title: 'U-Net Segmentation',
    subtitle: 'Pixel-wise Land Cover',
    dataset: 'DeepGlobe Land Cover',
    channels: 3,
    classes: 7,
    metricLabel: 'Mean IoU',
    targetMetric: '68.5%',
    description: 'Swaps classification head for pixel-wise segmentation with SMP U-Net and Dice+CrossEntropy combined loss.',
    badgeColor: 'amber',
  },
  {
    phase: 3,
    title: 'Multispectral + Band Math',
    subtitle: 'All 13 Bands + Indices',
    dataset: 'SEN12MS (IGBP Scheme)',
    channels: 16,
    classes: 11,
    metricLabel: 'Mean IoU',
    targetMetric: '74.2%',
    description: 'Expands ImageNet pretrained encoder from 3→16 channels with NDVI, NDWI, NDBI spectral index calculation.',
    badgeColor: 'purple',
  },
  {
    phase: 4,
    title: 'ResNet-CF Resolution Boost',
    subtitle: 'Sharma et al. (Elsevier 2024)',
    dataset: 'Sentinel-2 MS (ResNet-CF Super-Res)',
    channels: 16,
    classes: 7,
    metricLabel: 'Target mIoU',
    targetMetric: '81.4%',
    description: 'Enhances 20m/60m bands via Correlation Filter Residual Network (S016974392400217X) preserving fine spatial boundaries.',
    badgeColor: 'green',
  },
];

export const PhaseTracker: React.FC<PhaseTrackerProps> = ({
  currentPhase,
  onSelectPhase,
}) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
      {phasesData.map((p) => {
        const isCurrent = p.phase === currentPhase;
        const isCompleted = p.phase < currentPhase;

        return (
          <Card
            key={p.phase}
            interactive
            onClick={() => onSelectPhase?.(p.phase)}
            style={{
              borderColor: isCurrent ? 'var(--primary)' : isCompleted ? 'rgba(16, 185, 129, 0.4)' : undefined,
              background: isCurrent ? 'linear-gradient(180deg, rgba(56, 189, 248, 0.06) 0%, var(--bg-card) 100%)' : undefined,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.875rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.8125rem',
                  fontWeight: 800,
                  background: isCompleted ? '#10b981' : isCurrent ? 'var(--primary)' : '#1e293b',
                  color: isCompleted || isCurrent ? '#0b1120' : 'var(--text-muted)',
                }}>
                  {isCompleted ? <CheckCircle2 size={16} /> : p.phase}
                </span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Phase {p.phase}
                </span>
              </div>
              <Badge variant={p.badgeColor as any}>
                {isCompleted ? 'Validated' : isCurrent ? 'Active Focus' : 'Planned'}
              </Badge>
            </div>

            <h4 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
              {p.title}
            </h4>
            <p style={{ fontSize: '0.8125rem', color: '#38bdf8', fontWeight: 600, marginBottom: '0.75rem' }}>
              {p.subtitle}
            </p>

            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: 1.5, minHeight: '3.6em' }}>
              {p.description}
            </p>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.625rem 0.875rem',
              background: '#090d16',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.75rem',
            }}>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Input: </span>
                <strong style={{ color: 'var(--text-main)' }}>{p.channels} Bands</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>{p.metricLabel}: </span>
                <strong style={{ color: '#10b981' }}>{p.targetMetric}</strong>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};
