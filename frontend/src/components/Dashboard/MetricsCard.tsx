import React from 'react';
import { Card } from '../common/Card';

interface MetricsCardProps {
  title: string;
  value: string | number;
  change?: string;
  isPositive?: boolean;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  change,
  isPositive,
  subtitle,
  icon,
  color = '#38bdf8',
}) => {
  return (
    <Card>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {title}
          </p>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '0.375rem', letterSpacing: '-0.02em' }}>
            {value}
          </h3>
        </div>
        <div style={{
          padding: '0.75rem',
          borderRadius: 'var(--radius-lg)',
          background: `${color}15`,
          color: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {icon}
        </div>
      </div>

      {(change || subtitle) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.8125rem' }}>
          {change && (
            <span style={{
              fontWeight: 700,
              color: isPositive ? '#10b981' : isPositive === false ? '#ef4444' : 'var(--text-muted)',
            }}>
              {change}
            </span>
          )}
          {subtitle && <span style={{ color: 'var(--text-dim)' }}>{subtitle}</span>}
        </div>
      )}
    </Card>
  );
};
