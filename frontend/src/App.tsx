import React, { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Navbar } from './components/Layout/Navbar';
import { Footer } from './components/Layout/Footer';
import { CosmicBackground } from './components/common/CosmicBackground';
import { Home } from './pages/Home';
import { Training } from './pages/Training';
import { Inference } from './pages/Inference';
import { MapView } from './pages/MapView';
import { CppDemo } from './pages/CppDemo';
import { Results } from './pages/Results';
import { SuperResolution } from './pages/SuperResolution';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab');
      if (tabParam) return tabParam;
      const hash = window.location.hash.replace('#', '');
      if (hash) return hash;
    }
    return 'home';
  });

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      window.history.replaceState(null, '', url.toString());
    }
  };

  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab') || 'home';
      setActiveTab(tabParam);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const renderActivePage = () => {
    switch (activeTab) {
      case 'home':
        return <Home setActiveTab={handleTabChange} key="home" />;
      case 'projects':
      case 'map':
        return <MapView key="projects" />;
      case 'models':
      case 'training':
        return <Training key="models" />;
      case 'predict':
      case 'inference':
        return <Inference key="predict" />;
      case 'results':
        return <Results key="results" />;
      case 'sr':
      case 'super-resolution':
      case 'psisr':
        return <SuperResolution key="sr" />;
      case 'developers':
      case 'cpp':
        return <CppDemo key="developers" />;
      default:
        return <Home setActiveTab={handleTabChange} key="home" />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#030712] text-slate-100 relative font-sans selection:bg-cyan-500/30 selection:text-cyan-200 overflow-x-hidden">
      {/* 60fps Dynamic Starfield & Nebula Background */}
      <CosmicBackground />

      {/* Top Navbar matching Figma Tabs */}
      <Navbar activeTab={activeTab} setActiveTab={handleTabChange} />

      {/* Main Page Body with Framer Motion Cross-fades */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 z-10">
        <AnimatePresence mode="wait">
          {renderActivePage()}
        </AnimatePresence>
      </main>

      {/* Modern Minimal Footer */}
      <Footer />
    </div>
  );
};

export default App;
