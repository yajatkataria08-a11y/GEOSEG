import React, { useState } from 'react';
import { Sliders, Eye, EyeOff } from 'lucide-react';

interface ImageOverlayProps {
  baseImage: string;
  overlayMask: string;
  width?: string;
  height?: string;
}

export const ImageOverlay: React.FC<ImageOverlayProps> = ({
  baseImage,
  overlayMask,
  width = '100%',
  height = '400px',
}) => {
  const [opacity, setOpacity] = useState<number>(0.55);
  const [showMask, setShowMask] = useState<boolean>(true);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{
        position: 'relative',
        width,
        height,
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        border: '1px solid var(--border-subtle)',
        background: '#090d16',
      }}>
        {/* Base RGB Composite */}
        <img
          src={baseImage}
          alt="Satellite Base"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            display: 'block',
          }}
        />

        {/* Semi-transparent Predicted Mask */}
        {showMask && (
          <img
            src={overlayMask}
            alt="Segmentation Mask"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity,
              transition: 'opacity 0.15s ease',
              mixBlendMode: 'screen',
            }}
          />
        )}
      </div>

      {/* Opacity & Visibility Controls */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1rem',
        background: '#090d16',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        fontSize: '0.8125rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, maxWidth: '300px' }}>
          <Sliders size={16} color="var(--primary)" />
          <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>Mask Opacity</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={opacity}
            onChange={(e) => setOpacity(parseFloat(e.target.value))}
            style={{ flex: 1, accentColor: 'var(--primary)' }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, width: '35px' }}>
            {Math.round(opacity * 100)}%
          </span>
        </div>

        <button
          onClick={() => setShowMask(!showMask)}
          style={{
            background: 'transparent',
            border: 'none',
            color: showMask ? 'var(--primary)' : 'var(--text-dim)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.8125rem',
          }}
        >
          {showMask ? <Eye size={16} /> : <EyeOff size={16} />}
          <span>{showMask ? 'Hide Mask' : 'Show Mask'}</span>
        </button>
      </div>
    </div>
  );
};
