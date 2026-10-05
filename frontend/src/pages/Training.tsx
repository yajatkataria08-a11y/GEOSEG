import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { TrainingProgress } from '../components/Dashboard/TrainingProgress';
import { phasesData } from '../components/Dashboard/PhaseTracker';
import { Play, Square, Cpu, Sliders, Database, Target } from 'lucide-react';
import { PhaseNumber, TrainingConfig, TrainingStatus } from '../types/training';
import { trainingApi } from '../services/trainingApi';
import { pageVariants } from '../utils/animations';

export const Training: React.FC = () => {
  const [selectedPhase, setSelectedPhase] = useState<PhaseNumber>(3);
  const [config, setConfig] = useState<TrainingConfig>({
    phase: 3,
    epochs: 30,
    lr: 0.001,
    batchSize: 8,
    loss: 'dice_ce',
    optimizer: 'adamw',
    scheduler: 'cosine',
    useIndices: true,
  });

  const [status, setStatus] = useState<TrainingStatus>({
    status: 'idle',
    phase: 3,
    currentEpoch: 18,
    totalEpochs: 30,
    metrics: {
      epoch: 18,
      totalEpochs: 30,
      trainLoss: 0.185,
      valMetric: 0.742,
      metricName: 'Mean IoU',
      perClassIou: {
        'Evergreen Forest': 0.86,
        'Croplands': 0.79,
        'Water Bodies': 0.84,
        'Urban / Built-up': 0.68,
        'Shrublands': 0.72,
        'Grasslands': 0.75,
      },
    },
    bestMetric: 0.742,
    elapsedSeconds: 248,
    message: 'Training epoch 18/30 active',
    history: [],
  });

  const [starting, setStarting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    async function initStatus() {
      try {
        const liveStatus = await trainingApi.getStatus();
        if (liveStatus) {
          setStatus(liveStatus);
        }
      } catch (e) {}
    }
    initStatus();
  }, []);

  useEffect(() => {
    let interval: any = null;
    if (status.status === 'running') {
      interval = setInterval(async () => {
        try {
          const liveStatus = await trainingApi.getStatus();
          if (liveStatus) {
            setStatus(liveStatus);
          }
        } catch (e) {}
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [status.status]);

  const handleStartTraining = async () => {
    setStarting(true);
    setErrorMsg(null);
    try {
      await trainingApi.start({ ...config, phase: selectedPhase });
      setStatus((prev) => ({
        ...prev,
        status: 'running',
        phase: selectedPhase,
        currentEpoch: 1,
        totalEpochs: config.epochs,
      }));
    } catch (err: any) {
      setErrorMsg(err.message || 'Connecting to training backend failed.');
    } finally {
      setStarting(false);
    }
  };

  const handleStopTraining = async () => {
    try {
      await trainingApi.stop();
      setStatus((prev) => ({ ...prev, status: 'stopped' }));
    } catch (err: any) {}
  };

  const progressPercent =
    status.totalEpochs > 0
      ? Math.round((status.currentEpoch / status.totalEpochs) * 100)
      : 0;

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="max-w-6xl mx-auto flex flex-col gap-8 py-2"
    >
      <div className="flex flex-col gap-1.5 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-400/20 text-purple-300 text-xs font-bold w-fit mx-auto sm:mx-0">
          <Cpu size={13} className="text-purple-400 animate-pulse" />
          <span>PyTorch Deep Learning & U-Net Matrix</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
          Let it learn
        </h1>
        <p className="text-slate-400 text-sm max-w-2xl font-medium">
          Choose parameters for the model to train. We optimize pretrained U-Nets to segment forests, wetlands, urban sprawl, and croplands.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2 font-medium">
          <span className="font-bold text-sm">Notice:</span>
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {phasesData.map((p) => {
          const isSelected = selectedPhase === p.phase;
          return (
            <motion.button
              key={p.phase}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setSelectedPhase(p.phase);
                setConfig((prev) => ({
                  ...prev,
                  phase: p.phase,
                  epochs: p.phase === 1 ? 10 : p.phase === 2 ? 20 : 30,
                }));
              }}
              className={`p-4 rounded-2xl text-left transition-all border relative overflow-hidden ${
                isSelected
                  ? 'bg-gradient-to-tr from-cyan-950/60 to-purple-950/60 border-cyan-400/80 shadow-lg shadow-cyan-500/20'
                  : 'bg-[#091129]/60 border-white/10 hover:border-white/20 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-xs font-bold uppercase tracking-wider ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`}>
                  Phase {p.phase}
                </span>
                <Badge variant={p.badgeColor as any}>{p.channels} Bands</Badge>
              </div>
              <h4 className="text-sm font-bold text-white mb-1">{p.title}</h4>
              <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{p.subtitle}</p>
            </motion.button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card
          title="Loss & Optimizer"
          subtitle="Balanced objective configuration"
          icon={<Sliders size={18} className="text-cyan-400" />}
        >
          <div className="flex flex-col gap-3 mt-1">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-slate-400">Loss Function</label>
              <select
                className="bg-[#060c20] border border-cyan-500/20 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400"
                value={config.loss}
                onChange={(e) => setConfig({ ...config, loss: e.target.value as any })}
              >
                <option value="dice_ce">Dice + CrossEntropy (Combined)</option>
                <option value="cross_entropy">Standard CrossEntropy</option>
                <option value="focal">Focal Loss</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                <span>Learning Rate</span>
                <span className="text-cyan-300 font-mono">{config.lr}</span>
              </div>
              <input
                type="number"
                step="0.0001"
                className="bg-[#060c20] border border-cyan-500/20 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-400"
                value={config.lr}
                onChange={(e) => setConfig({ ...config, lr: parseFloat(e.target.value) || 0.001 })}
              />
            </div>
          </div>
        </Card>

        <Card
          title="Dataset & Bands"
          subtitle="Sentinel-2 L2A Multispectral Input"
          icon={<Database size={18} className="text-purple-400" />}
        >
          <div className="flex flex-col gap-3 mt-1">
            <div className="p-3 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white block">13 Sentinel-2 Raw Bands</span>
                <span className="text-[10px] text-slate-400">B01-B12 (10m, 20m, 60m GSD)</span>
              </div>
              <Badge variant="blue">13-Band</Badge>
            </div>

            {selectedPhase === 3 && (
              <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/30 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-purple-300 block">+3 Spectral Indices (16ch)</span>
                  <span className="text-[10px] text-slate-400">NDVI + NDWI + NDBI</span>
                </div>
                <input
                  type="checkbox"
                  checked={config.useIndices}
                  onChange={(e) => setConfig({ ...config, useIndices: e.target.checked })}
                  className="w-4 h-4 accent-cyan-400 cursor-pointer"
                />
              </div>
            )}
          </div>
        </Card>

        <Card
          title="Model Architecture"
          subtitle="SMP U-Net + ResNet-34 Encoder"
          icon={<Target size={18} className="text-emerald-400" />}
        >
          <div className="flex flex-col gap-3 mt-1">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Epochs</span>
                <input
                  type="number"
                  value={config.epochs}
                  onChange={(e) => setConfig({ ...config, epochs: parseInt(e.target.value) || 10 })}
                  className="w-full bg-transparent text-white font-mono font-bold text-sm focus:outline-none"
                />
              </div>
              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Batch Size</span>
                <input
                  type="number"
                  value={config.batchSize}
                  onChange={(e) => setConfig({ ...config, batchSize: parseInt(e.target.value) || 8 })}
                  className="w-full bg-transparent text-white font-mono font-bold text-sm focus:outline-none"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="accent"
                size="md"
                onClick={handleStartTraining}
                loading={starting}
                icon={<Play size={15} />}
                className="flex-1"
              >
                Launch Phase {selectedPhase}
              </Button>
              <Button
                variant="danger"
                size="md"
                onClick={handleStopTraining}
                icon={<Square size={15} />}
              >
                Stop
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <div className="bg-[#09112a]/80 border border-cyan-500/20 rounded-3xl p-6 backdrop-blur-xl shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Training Progress • Phase {status.phase}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="text-slate-400">Epoch {status.currentEpoch} / {status.totalEpochs}</span>
            <span className="text-cyan-300 font-extrabold text-sm">{progressPercent}%</span>
          </div>
        </div>

        <div className="relative w-full h-4 rounded-full bg-slate-950/80 p-0.5 border border-cyan-500/30 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ type: 'spring', stiffness: 100, damping: 20 }}
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-600 shadow-[0_0_15px_#38bdf8] relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
          </motion.div>
        </div>

        <p className="text-xs text-slate-400 italic">{status.message}</p>
      </div>

      <TrainingProgress status={status} />
    </motion.div>
  );
};
