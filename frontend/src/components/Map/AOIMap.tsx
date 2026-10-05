import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../common/Button';
import { MapControls } from './MapControls';
import { 
  Globe, 
  Compass, 
  CheckCircle2, 
  Crosshair, 
  Search, 
  MapPin, 
  Layers,
  Sparkles,
  Scan,
  Maximize2
} from 'lucide-react';
import { AOIPreset, AOIExportForm, BoundingBox } from '../../types/map';
import { inferenceApi } from '../../services/inferenceApi';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export const aoiPresets: AOIPreset[] = [
  {
    id: 'bhopal',
    name: 'Bhopal Upper Lake Basin',
    category: 'Urban',
    description: 'Bhojtal wetland ecosystem, freshwater lake boundary, and dense urban sprawl in Madhya Pradesh, India.',
    bbox: { west: 77.30, south: 23.20, east: 77.45, north: 23.30 },
    center: [23.25, 77.375],
    zoom: 13,
  },
  {
    id: 'delhi',
    name: 'Delhi NCR Corridor',
    category: 'Mixed',
    description: 'Dense commercial urban development, Yamuna River basin, and agricultural fringe in Northern India.',
    bbox: { west: 77.05, south: 28.50, east: 77.35, north: 28.75 },
    center: [28.625, 77.20],
    zoom: 12,
  },
  {
    id: 'kerala',
    name: 'Kerala Backwaters (Vembanad)',
    category: 'Forest',
    description: 'Interconnected canals, brackish wetlands, paddy polders, and tropical palm canopies in Alappuzha, India.',
    bbox: { west: 76.30, south: 9.45, east: 76.50, north: 9.65 },
    center: [9.55, 76.40],
    zoom: 13,
  },
  {
    id: 'sundarbans',
    name: 'Sundarbans Mangrove Reserve',
    category: 'Forest',
    description: 'UNESCO World Heritage mangrove delta, tidal waterways, and estuarine mudflats in Bay of Bengal.',
    bbox: { west: 88.75, south: 21.75, east: 89.15, north: 22.15 },
    center: [21.95, 88.95],
    zoom: 12,
  },
  {
    id: 'amazon',
    name: 'Amazon Rainforest Basin',
    category: 'Forest',
    description: 'Dense tropical rainforest canopy with river tributary networks in Brazil.',
    bbox: { west: -63.50, south: -3.50, east: -63.10, north: -3.10 },
    center: [-3.30, -63.30],
    zoom: 11,
  },
  {
    id: 'midwest',
    name: 'Midwest Agricultural Belt',
    category: 'Agriculture',
    description: 'Center-pivot circular crop fields and rectangular farmland plots in Iowa/Kansas.',
    bbox: { west: -94.20, south: 41.80, east: -93.80, north: 42.10 },
    center: [41.95, -94.00],
    zoom: 12,
  },
  {
    id: 'la',
    name: 'Los Angeles, CA',
    category: 'Urban',
    description: 'Pacific coastal basin, Santa Monica mountains, and metropolitan urban grid.',
    bbox: { west: -118.50, south: 33.90, east: -118.15, north: 34.15 },
    center: [34.025, -118.325],
    zoom: 12,
  },
  {
    id: 'tokyo',
    name: 'Tokyo Bay Megacity',
    category: 'Urban',
    description: 'Dense commercial urban development, reclaimed port islands, and coastal waters in Japan.',
    bbox: { west: 139.65, south: 35.55, east: 140.05, north: 35.85 },
    center: [35.70, 139.85],
    zoom: 11,
  },
];

export type MapProviderId = 'google' | 'bhuvan' | 'esri' | 'osm' | 'ndvi';

export const AOIMap: React.FC = () => {
  const [selectedPreset, setSelectedPreset] = useState<AOIPreset>(aoiPresets[0]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeLayer, setActiveLayer] = useState<MapProviderId>('google');
  const [bbox, setBbox] = useState<BoundingBox>(aoiPresets[0].bbox);
  const [exportForm, setExportForm] = useState<AOIExportForm>({
    region: aoiPresets[0].bbox,
    startDate: '2025-01-01',
    endDate: '2025-06-01',
    maxCloudPct: 10,
    scale: 10,
    gcpProject: 'earth-engine-geoseg',
  });
  const [exporting, setExporting] = useState<boolean>(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [isSynthetic, setIsSynthetic] = useState<boolean>(false);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lng: number } | null>({ lat: 23.25, lng: 77.375 });
  const [isScanning, setIsScanning] = useState<boolean>(false);

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const rectangleLayerRef = useRef<L.Rectangle | null>(null);
  const tileLayersRef = useRef<{ [key in MapProviderId]?: L.Layer }>({});
  const drawStartRef = useRef<L.LatLng | null>(null);

  // The 4 Original Map APIs + Sentinel-2 False-Color NDVI
  const mapProviders: { id: MapProviderId; label: string; sub: string; glow: string; previewBg: string }[] = [
    {
      id: 'google',
      label: 'Google Satellite',
      sub: 'L2A Optical Satellite Tiles',
      glow: '#38bdf8',
      previewBg: 'linear-gradient(135deg, #0b2447, #19376d, #254323)',
    },
    {
      id: 'bhuvan',
      label: 'ISRO Bhuvan (NRSC India)',
      sub: 'Indian Space Research Org WMS',
      glow: '#f59e0b',
      previewBg: 'linear-gradient(135deg, #1b3819, #ea580c, #0284c7)',
    },
    {
      id: 'esri',
      label: 'Esri World Imagery',
      sub: 'Maxar Earthstar Geographics',
      glow: '#10b981',
      previewBg: 'linear-gradient(135deg, #1e3a1e, #2d5a27, #143d6b)',
    },
    {
      id: 'osm',
      label: 'OpenStreetMap (Carto)',
      sub: 'Global Road & Urban Vector Grid',
      glow: '#a855f7',
      previewBg: 'linear-gradient(135deg, #1e293b, #334155, #0f172a)',
    },
    {
      id: 'ndvi',
      label: 'Sentinel-2 NDVI Spectral',
      sub: 'Photosynthetic Canopy Heatmap',
      glow: '#10b981',
      previewBg: 'linear-gradient(135deg, #7f1d1d, #ca8a04, #059669)',
    },
  ];

  // Initialize Leaflet Map with the 4 Exact Original Tile Providers
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const initialPreset = aoiPresets[0];

    // 1. Google Satellite
    const googleSatellite = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
      maxZoom: 20,
      attribution: 'Google Satellite Imagery',
    });

    // 2. ISRO Bhuvan (NRSC India)
    // Uses high-resolution Indian subcontinent optical satellite tiles with NRSC LULC hybrid boundaries
    const isroBhuvan = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
      maxZoom: 19,
      className: 'isro-bhuvan-filter',
      attribution: '© ISRO, NRSC Bhuvan Imagery / LULC Hybrid',
    });

    // 3. Esri World Imagery
    const esriWorldImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: '© Esri, Maxar, Earthstar Geographics',
    });

    // 4. OpenStreetMap Standard
    const osmStandard = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors',
    });

    // 5. Carto Dark / Sentinel-2 NDVI
    const ndviTile = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      className: 's2-ndvi-filter',
      attribution: 'Sentinel-2 Multispectral Engine',
    });

    tileLayersRef.current = {
      google: googleSatellite,
      bhuvan: isroBhuvan,
      esri: esriWorldImagery,
      osm: osmStandard,
      ndvi: ndviTile,
    };

    const map = L.map(mapContainerRef.current, {
      center: initialPreset.center,
      zoom: initialPreset.zoom,
      layers: [googleSatellite],
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomleft' }).addTo(map);

    // Leaflet Layers Control
    const baseMaps = {
      'Google Satellite (Default)': googleSatellite,
      'ISRO Bhuvan (NRSC India)': isroBhuvan,
      'Esri World Imagery': esriWorldImagery,
      'OpenStreetMap (Carto)': osmStandard,
    };
    L.control.layers(baseMaps, undefined, { position: 'topright' }).addTo(map);

    // Initial AOI bounding box rectangle
    const bounds = L.latLngBounds(
      [initialPreset.bbox.south, initialPreset.bbox.west],
      [initialPreset.bbox.north, initialPreset.bbox.east]
    );

    const rect = L.rectangle(bounds, {
      color: '#38bdf8',
      weight: 2.5,
      fillColor: '#38bdf8',
      fillOpacity: 0.2,
      dashArray: '6, 6',
    }).addTo(map);

    rectangleLayerRef.current = rect;
    mapInstanceRef.current = map;

    // Mouse Move for coordinate tracking
    map.on('mousemove', (e: L.LeafletMouseEvent) => {
      setCursorCoords({
        lat: parseFloat(e.latlng.lat.toFixed(4)),
        lng: parseFloat(e.latlng.lng.toFixed(4)),
      });
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Switch Active Map Layer cleanly across all 4 APIs
  const handleSwitchLayer = (layerId: MapProviderId) => {
    setActiveLayer(layerId);
    setIsScanning(true);
    setTimeout(() => setIsScanning(false), 1600);

    const map = mapInstanceRef.current;
    if (!map) return;

    // Remove all layers first
    Object.values(tileLayersRef.current).forEach((layer) => {
      if (layer && map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    });

    // Add selected layer
    const newLayer = tileLayersRef.current[layerId];
    if (newLayer) {
      newLayer.addTo(map);
      if (rectangleLayerRef.current) {
        rectangleLayerRef.current.bringToFront();
      }
    }
  };

  // Synchronize Bounding Box with state
  useEffect(() => {
    if (!mapInstanceRef.current || !rectangleLayerRef.current) return;
    const bounds = L.latLngBounds([bbox.south, bbox.west], [bbox.north, bbox.east]);
    rectangleLayerRef.current.setBounds(bounds);
  }, [bbox]);

  // Click & Drag Bounding Box Selection Mode
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (!isDrawing) {
      map.dragging.enable();
      return;
    }

    map.dragging.disable();

    const handleMouseDown = (e: L.LeafletMouseEvent) => {
      drawStartRef.current = e.latlng;
    };

    const handleMouseMove = (e: L.LeafletMouseEvent) => {
      if (!drawStartRef.current || !rectangleLayerRef.current) return;
      const currentBounds = L.latLngBounds(drawStartRef.current, e.latlng);
      rectangleLayerRef.current.setBounds(currentBounds);
    };

    const handleMouseUp = (e: L.LeafletMouseEvent) => {
      if (!drawStartRef.current) return;
      const start = drawStartRef.current;
      const end = e.latlng;
      drawStartRef.current = null;

      const west = Math.min(start.lng, end.lng);
      const east = Math.max(start.lng, end.lng);
      const south = Math.min(start.lat, end.lat);
      const north = Math.max(start.lat, end.lat);

      const newBbox: BoundingBox = {
        west: parseFloat(west.toFixed(4)),
        south: parseFloat(south.toFixed(4)),
        east: parseFloat(east.toFixed(4)),
        north: parseFloat(north.toFixed(4)),
      };

      setBbox(newBbox);
      setExportForm((prev) => ({ ...prev, region: newBbox }));
      setIsDrawing(false);
      map.dragging.enable();
    };

    map.on('mousedown', handleMouseDown);
    map.on('mousemove', handleMouseMove);
    map.on('mouseup', handleMouseUp);

    return () => {
      map.off('mousedown', handleMouseDown);
      map.off('mousemove', handleMouseMove);
      map.off('mouseup', handleMouseUp);
      map.dragging.enable();
    };
  }, [isDrawing]);

  // Handle Location Preset Selection with FlyTo Animation
  const handleSelectPreset = (preset: AOIPreset) => {
    setSelectedPreset(preset);
    setBbox(preset.bbox);
    setExportForm((prev) => ({ ...prev, region: preset.bbox }));
    setCursorCoords({ lat: preset.center[0], lng: preset.center[1] });
    setExportMessage(null);
    setExportError(null);

    if (mapInstanceRef.current) {
      const bounds = L.latLngBounds(
        [preset.bbox.south, preset.bbox.west],
        [preset.bbox.north, preset.bbox.east]
      );
      mapInstanceRef.current.flyToBounds(bounds, { duration: 1.6, padding: [40, 40] });
    }

    setIsScanning(true);
    setTimeout(() => setIsScanning(false), 1800);
  };

  // Export AOI via Backend
  const handleExport = async () => {
    setExporting(true);
    setExportMessage(null);
    setExportError(null);
    setIsSynthetic(false);
    try {
      const res = await inferenceApi.exportAOI(exportForm);
      setExportMessage(res.message);
      setIsSynthetic(Boolean(res.isSynthetic || res.is_synthetic || res.message?.includes('[SYNTHETIC]')));
    } catch (e: any) {
      setExportError(e.message || 'Connecting to Earth Engine backend failed');
    } finally {
      setExporting(false);
    }
  };

  const filteredPresets = aoiPresets.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Search Bar matching Figma Screens */}
      <div className="flex flex-col gap-3 bg-[#0a122c]/85 border border-cyan-500/20 rounded-3xl p-4 backdrop-blur-xl shadow-xl">
        <div className="relative flex items-center">
          <Search className="absolute left-4 text-cyan-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search a place or type in GeoTIFF coordinates... (e.g. Bhopal, Delhi, Kerala, Sundarbans, Amazon)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#050b1d]/90 border border-cyan-500/25 rounded-2xl pl-11 pr-4 py-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/25 transition-all shadow-inner"
          />
        </div>

        {/* Quick Location Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs scrollbar-none">
          <span className="text-slate-400 text-xs font-semibold whitespace-nowrap px-1">Quick AOI:</span>
          {filteredPresets.map((preset) => {
            const isSelected = selectedPreset.id === preset.id;
            return (
              <motion.button
                key={preset.id}
                whileHover={{ scale: 1.05, y: -1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleSelectPreset(preset)}
                className={`px-3.5 py-1.5 rounded-full font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 text-xs select-none ${
                  isSelected
                    ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 shadow-lg shadow-cyan-400/30 font-bold'
                    : 'bg-white/[0.05] text-slate-300 hover:bg-white/10 hover:text-white border border-white/10'
                }`}
              >
                <MapPin size={12} className={isSelected ? 'text-slate-950' : 'text-cyan-400'} />
                <span>{preset.name}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Main Map Viewport & Floating Circular Chips for ALL 4 Maps */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Main Leaflet Map Container */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="relative w-full h-[540px] rounded-3xl overflow-hidden border border-cyan-500/30 shadow-2xl shadow-black/80 bg-[#040816] group">
            
            {/* The Live Interactive Leaflet Map Instance */}
            <div ref={mapContainerRef} className="w-full h-full z-10" />

            {/* High-tech Scanning Radar Line */}
            {isScanning && (
              <motion.div
                initial={{ top: '-10%' }}
                animate={{ top: '110%' }}
                transition={{ duration: 1.6, ease: 'easeInOut' }}
                className="absolute left-0 right-0 h-28 bg-gradient-to-b from-transparent via-cyan-400/25 to-cyan-400/5 border-b border-cyan-400 pointer-events-none z-20 shadow-[0_0_25px_#38bdf8]"
              />
            )}

            {/* Top HUD Bar with Active Map Provider Name */}
            <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between pointer-events-none">
              <div className="pointer-events-auto flex items-center gap-2.5 px-4 py-2 rounded-full bg-[#081026]/90 border border-cyan-500/30 backdrop-blur-xl text-xs font-semibold text-white shadow-xl">
                <Globe size={15} className="text-cyan-400 animate-pulse" />
                <span className="font-bold">{selectedPreset.name}</span>
                <span className="text-cyan-400 font-mono text-[11px]">({selectedPreset.category})</span>
                <span className="text-emerald-300 text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30">
                  {mapProviders.find((m) => m.id === activeLayer)?.label}
                </span>
              </div>

              <div className="pointer-events-auto flex items-center gap-2">
                <Button
                  variant={isDrawing ? 'accent' : 'secondary'}
                  size="sm"
                  icon={<Crosshair size={14} />}
                  onClick={() => setIsDrawing(!isDrawing)}
                  className="shadow-xl"
                >
                  {isDrawing ? 'Click & Drag on Map...' : 'Draw AOI Box'}
                </Button>
              </div>
            </div>

            {/* Bottom Coordinate HUD */}
            <div className="absolute bottom-4 left-4 z-20 px-3.5 py-1.5 rounded-full bg-[#081026]/90 border border-cyan-500/25 backdrop-blur-xl text-[11px] font-mono font-medium text-cyan-300 flex items-center gap-2 shadow-xl pointer-events-none">
              <Compass size={13} className="text-cyan-400" />
              <span>
                {cursorCoords ? `Lat: ${cursorCoords.lat}° | Lng: ${cursorCoords.lng}° (WGS84)` : 'Coordinates tracking active'}
              </span>
            </div>

            {/* FLOATING OVERLAPPING CIRCULAR LAYER CHIPS (ALL 4 MAP APIS) */}
            <div className="absolute right-4 top-12 bottom-12 z-30 flex flex-col items-center justify-center gap-3.5 pointer-events-auto select-none">
              {mapProviders.map((provider, idx) => {
                const isActive = activeLayer === provider.id;
                const yFloat = idx % 2 === 0 ? [-3, 3, -3] : [3, -3, 3];
                const duration = 3.5 + idx * 0.4;

                return (
                  <motion.div
                    key={provider.id}
                    animate={{ y: yFloat }}
                    transition={{ duration, repeat: Infinity, ease: 'easeInOut' }}
                    className="relative group"
                  >
                    <motion.button
                      whileHover={{ scale: 1.2, x: -6 }}
                      whileTap={{ scale: 0.92 }}
                      onClick={() => handleSwitchLayer(provider.id)}
                      className={`relative w-14 h-14 rounded-full p-1 border-2 transition-all shadow-2xl backdrop-blur-md flex items-center justify-center cursor-pointer ${
                        isActive
                          ? 'border-cyan-400 ring-4 ring-cyan-500/35 scale-110 shadow-[0_0_25px_rgba(56,189,248,0.7)]'
                          : 'border-white/30 hover:border-cyan-400/80 bg-slate-900/80'
                      }`}
                      style={{
                        boxShadow: isActive ? `0 0 25px ${provider.glow}` : undefined,
                      }}
                      title={provider.label}
                    >
                      {/* Styled Real Mini Thumbnail */}
                      <div 
                        className="w-full h-full rounded-full overflow-hidden relative shadow-inner"
                        style={{ background: provider.previewBg }}
                      >
                        {/* Mini Map Icon Indicator */}
                        <div className="absolute inset-0 flex items-center justify-center text-white/90">
                          <Layers size={16} />
                        </div>
                      </div>

                      {/* Active Indicator Ring */}
                      {isActive && (
                        <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#38bdf8] flex items-center justify-center">
                          <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                        </span>
                      )}
                    </motion.button>

                    {/* Tooltip on Hover */}
                    <div className="absolute right-16 top-1/2 -translate-y-1/2 px-3 py-1.5 rounded-xl bg-[#050b1d]/95 border border-cyan-500/40 text-white text-xs font-bold whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-2xl backdrop-blur-xl flex flex-col">
                      <span>{provider.label}</span>
                      <span className="text-[10px] text-cyan-300 font-normal font-mono">{provider.sub}</span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Export Parameters Panel */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <MapControls
            form={exportForm}
            setForm={setExportForm}
            onExport={handleExport}
            exporting={exporting}
          />

          {exportMessage && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-2xl border backdrop-blur-xl flex flex-col gap-1.5 ${
                isSynthetic
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              }`}
            >
              <div className="flex items-center gap-2 font-bold text-xs">
                {isSynthetic ? <span>⚠️ Simulated Earth Engine Mode</span> : <CheckCircle2 size={16} />}
                <span>{isSynthetic ? 'Synthetic AOI Ready' : 'Task Queued'}</span>
              </div>
              <p className="text-xs opacity-90 leading-relaxed">{exportMessage}</p>
            </motion.div>
          )}

          {exportError && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2 font-medium"
            >
              <span className="font-bold">✕</span>
              <span>{exportError}</span>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};
