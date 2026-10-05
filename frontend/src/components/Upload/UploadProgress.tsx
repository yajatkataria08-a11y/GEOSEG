import React from 'react';

interface UploadProgressProps {
  progress: number;
  fileName: string;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({ progress, fileName }) => {
  return (
    <div style={{
      padding: '1rem',
      background: '#090d16',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-subtle)',
      marginTop: '1rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: '0.5rem' }}>
        <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{fileName}</span>
        <span style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{progress}%</span>
      </div>
      <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ width: `${progress}%`, height: '100%', background: 'linear-gradient(90deg, #38bdf8, #a855f7)', transition: 'width 0.2s ease' }} />
      </div>
    </div>
  );
};
