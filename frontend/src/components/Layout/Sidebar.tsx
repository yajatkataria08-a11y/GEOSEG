import React from 'react';
import { 
  LayoutDashboard, 
  Flame, 
  Satellite, 
  MapPin, 
  FolderArchive, 
  Binary, 
  Sparkles,
  Layers
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'home', label: 'Overview', icon: LayoutDashboard },
    { id: 'training', label: 'Training Matrix', icon: Flame },
    { id: 'inference', label: 'GeoTIFF Inference', icon: Satellite },
    { id: 'map', label: 'Satellite AOI Map', icon: MapPin },
    { id: 'cpp', label: 'C++ OOP Engine', icon: Binary },
    { id: 'results', label: 'Result Archive', icon: FolderArchive },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: 'var(--radius-md)',
          background: 'linear-gradient(135deg, #0284c7 0%, #a855f7 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 15px rgba(2, 132, 199, 0.35)',
        }}>
          <Satellite size={20} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 800, letterSpacing: '-0.025em', color: 'var(--text-main)' }}>
            Geo<span style={{ color: '#38bdf8' }}>Seg</span>
          </h1>
          <p style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Multispectral 13-Band
          </p>
        </div>
      </div>

      <nav className="nav-links">
        <div style={{ padding: '0.5rem 0.5rem 0.25rem', fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-dim)' }}>
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`nav-item ${isActive ? 'active' : ''}`}
              style={{
                background: isActive ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                border: 'none',
                width: '100%',
                textAlign: 'left',
                cursor: 'pointer',
              }}
            >
              <Icon size={18} color={isActive ? '#38bdf8' : 'currentColor'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div style={{ padding: '1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{
          padding: '0.875rem',
          borderRadius: 'var(--radius-md)',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.6) 100%)',
          border: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.375rem' }}>
            <Sparkles size={14} color="#38bdf8" />
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-main)' }}>Spectral Indices</span>
          </div>
          <p style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
            NDVI (Vegetation), NDWI (Water), NDBI (Built-up) stacked as 16 channels.
          </p>
        </div>
      </div>
    </aside>
  );
};
