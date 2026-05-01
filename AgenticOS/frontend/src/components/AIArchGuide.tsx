// AIArchGuide.tsx
// Developer: Marcus Daley | Grizzwald Workshop
// Date: 2026-04-30
// Purpose: Interactive AI Architecture Field Guide — Beyond Transformers.
//          Converted from JSX to TSX. Informs AgenticOS domain color theming.
//          Access via /guide route in the React frontend.

import { useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Architecture {
  readonly id: string;
  readonly name: string;
  readonly emoji: string;
  readonly tag: string;
  readonly tagColor: string;
  readonly since: string;
  readonly analogy: string;
  readonly how: string;
  readonly strengths: readonly string[];
  readonly weaknesses: readonly string[];
  readonly gameDevUse: readonly string[];
  readonly runLocal: string;
  readonly rtxFit: string;
  readonly color: string;
  readonly bg: string;
}

type ProjectName = 'Deep Command' | 'UnrealMCP' | 'ForgePipeline' | 'WizardJam' | 'Portfolio / Grizzwald';
type TabName = 'guide' | 'compare' | 'roadmap';

// ---------------------------------------------------------------------------
// Domain color map — used by AgenticOS AgentCard domain theming
// ---------------------------------------------------------------------------

export const DOMAIN_COLORS: Record<string, string> = {
  'game-dev': '#10b981',      // Mamba green — real-time, fast
  'software-eng': '#f59e0b',  // Transformer amber — reasoning
  'va-advisory': '#06b6d4',   // GNN cyan — relationship graphs
  '3d-content': '#ec4899',    // Diffusion pink — generative art
  'general': '#8b5cf6',       // RWKV purple — hybrid
};

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const ARCHS: Architecture[] = [
  {
    id: 'transformer',
    name: 'Transformer',
    emoji: '⚡',
    tag: 'THE INCUMBENT',
    tagColor: '#f59e0b',
    since: '2017',
    analogy: 'A tactician who reads the ENTIRE battlefield before making one decision.',
    how: 'Self-attention: every token attends to every other token. Quadratic cost O(n²) in sequence length.',
    strengths: ['Best at reasoning & language', 'Parallel training (fast)', 'Massive ecosystem (HuggingFace, etc.)', 'Strong in-context learning'],
    weaknesses: ['Quadratic memory cost explodes on long sequences', 'Overkill for real-time game loops', 'High VRAM at inference'],
    gameDevUse: [
      'NPC dialogue generation (Llama 3, Mistral via Ollama)',
      'Quest log / lore writer',
      'Code assistant (Claude, GPT, Copilot)',
      'Level design prompts for UnrealMCP',
    ],
    runLocal: '✅ Ollama (qwen2.5-coder:14b, deepseek-r1:8b)',
    rtxFit: 'Good — your RTX 5080 handles 14B easily',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.08)',
  },
  {
    id: 'mamba',
    name: 'Mamba (SSM)',
    emoji: '🐍',
    tag: 'THE CHALLENGER',
    tagColor: '#10b981',
    since: '2023',
    analogy: 'A submarine navigator using a rolling compressed memory — only keeps what matters.',
    how: 'Selective State Space Model: parameters are functions of input, so the model CHOOSES what to remember vs forget. O(n) cost — linear!',
    strengths: [
      '5x faster inference than Transformer at same size',
      'Linear scaling — handles million-token sequences',
      'Excellent for temporal/sequential data (audio, sensor streams)',
      'Low memory footprint at inference',
    ],
    weaknesses: [
      'Weaker at in-context learning vs Transformers',
      'Less mature ecosystem',
      'Struggles with tasks requiring exact copying of long sequences',
    ],
    gameDevUse: [
      'Real-time NPC behavior from sensor streams (sonar/radar feeds for Deep Command)',
      'Game replay analysis — compress long match histories',
      'Audio-driven procedural events',
      'Naval combat state tracking over long sessions',
    ],
    runLocal: '⚠️ Limited Ollama support — use HuggingFace Transformers lib directly',
    rtxFit: 'Excellent — low memory, your 64GB RAM is overkill',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.08)',
  },
  {
    id: 'rwkv',
    name: 'RWKV',
    emoji: '🔄',
    tag: 'THE HYBRID',
    tagColor: '#8b5cf6',
    since: '2023',
    analogy: 'Trains like a Transformer but runs like an RNN — gets the best bill from both restaurants.',
    how: 'Receptance Weighted Key Value — linear attention variant that recasts attention as a recurrent operation. Parallelizable in training, O(1) per-step in inference.',
    strengths: [
      'Parallel training speed of Transformer',
      'RNN-style O(1) per-token inference cost',
      'Great for streaming / real-time generation',
      'Fully open source (RWKV-6 / Raven models)',
    ],
    weaknesses: [
      'Weaker than Transformer on complex reasoning tasks',
      'Harder to implement custom fine-tuning',
      'Less adoption vs Mamba',
    ],
    gameDevUse: [
      'Streaming NPC dialogue — character keeps \'remembering\' the conversation cheaply',
      'Real-time game commentary system',
      'Edge deployment on game consoles or handheld devices',
      'Chatbot companions with persistent memory window',
    ],
    runLocal: '✅ RWKV.cpp — runs on CPU or GPU, very lean',
    rtxFit: 'Excellent — barely touches your GPU',
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.08)',
  },
  {
    id: 'diffusion',
    name: 'Diffusion Models',
    emoji: '🌫️',
    tag: 'THE ARTIST',
    tagColor: '#ec4899',
    since: '2020',
    analogy: 'Starts with pure noise and sculpts it into signal, like a sculptor chipping marble.',
    how: 'Learns to reverse a noise process. Forward pass adds noise step-by-step. Model learns to predict and remove each step. Can be conditioned on text, images, or game state.',
    strengths: [
      'State of the art image/texture/3D generation',
      'Highly controllable via ControlNet / LoRA',
      'Works for audio, video, 3D meshes',
      'Incredible for game asset pipelines',
    ],
    weaknesses: [
      'Slow inference (many denoising steps)',
      'Not for text reasoning tasks',
      'VRAM hungry for image generation',
    ],
    gameDevUse: [
      'Procedural texture generation for Deep Command ships/ports',
      'ForgePipeline — 3D asset generation (your RTX 5080 is perfect)',
      'Concept art iteration for Grizzwald Workshop',
      'Heightmap / terrain generation for island escape levels',
    ],
    runLocal: '✅ ComfyUI, Automatic1111, or Python diffusers lib',
    rtxFit: 'Perfect — RTX 5080 was made for this',
    color: '#ec4899',
    bg: 'rgba(236,72,153,0.08)',
  },
  {
    id: 'gnn',
    name: 'Graph Neural Networks (GNN)',
    emoji: '🕸️',
    tag: 'THE CARTOGRAPHER',
    tagColor: '#06b6d4',
    since: '2016',
    analogy: 'Thinks in relationships, not sequences. Perfect for \'who knows who\' and \'what connects to what\'.',
    how: 'Nodes pass messages to neighbors iteratively. Each node aggregates information from its local graph neighborhood. Naturally handles non-Euclidean structured data.',
    strengths: [
      'Natural fit for graph-structured game data',
      'Handles social graphs, skill trees, level graphs',
      'Pathfinding and navigation mesh reasoning',
      'Faction/relationship modeling',
    ],
    weaknesses: [
      'Harder to train than Transformers',
      'Limited pre-trained foundation models',
      'Scaling to huge graphs is non-trivial',
    ],
    gameDevUse: [
      'Deep Command faction relationship graphs — who is allied/hostile',
      'Naval supply chain / port dependency graphs',
      'Skill tree traversal AI for character builds',
      'Dynamic event propagation across map nodes',
    ],
    runLocal: '✅ PyTorch Geometric or DGL — runs fine on your stack',
    rtxFit: 'Good — GPU accelerated, modest VRAM',
    color: '#06b6d4',
    bg: 'rgba(6,182,212,0.08)',
  },
  {
    id: 'cnn',
    name: 'CNN / Vision Models',
    emoji: '👁️',
    tag: 'THE ANALYST',
    tagColor: '#f97316',
    since: '2012',
    analogy: 'Slides a magnifying glass across an image, building up local features into global understanding.',
    how: 'Convolutional filters detect local spatial patterns. Pooling layers build hierarchical feature maps. Efficient for grid-structured data (images, voxels, game maps).',
    strengths: [
      'Best spatial/visual pattern recognition',
      'Extremely fast at inference',
      'Well-understood, massive pretrained model zoo',
      'Works on 2D maps, heightmaps, sprite sheets',
    ],
    weaknesses: [
      'Not designed for sequence/language tasks',
      'Limited long-range spatial reasoning',
      'Replaced by ViT for high-level vision',
    ],
    gameDevUse: [
      'Screenshot-based game state detection for UnrealMCP',
      'Voxel world analysis (ArcadiaTracker type tools)',
      'Minimap parsing / tactical overlay analysis',
      'Sprite / texture classification pipeline',
    ],
    runLocal: '✅ torchvision, ONNX Runtime — lightning fast',
    rtxFit: 'Perfect — classic GPU workload',
    color: '#f97316',
    bg: 'rgba(249,115,22,0.08)',
  },
  {
    id: 'rl',
    name: 'Reinforcement Learning (RL)',
    emoji: '🎮',
    tag: 'THE GAMER',
    tagColor: '#eab308',
    since: '1990s',
    analogy: 'Learns by playing. Gets reward for good moves, punishment for bad ones. Literally how games teach players.',
    how: 'Agent observes state, takes action, receives reward signal. Policy network (often a Transformer or CNN backbone) maps state → action probability distribution.',
    strengths: [
      'Learns genuinely intelligent behavior from scratch',
      'Can discover strategies humans never thought of',
      'Natural fit for game AI',
      'Works with any game engine that provides state/reward',
    ],
    weaknesses: [
      'Extremely sample-inefficient (needs millions of episodes)',
      'Reward shaping is notoriously hard',
      'Training instability',
      'Hard to debug and interpret',
    ],
    gameDevUse: [
      'Deep Command enemy AI — train naval commanders that learn fleet tactics',
      'WizardJam opponent AI',
      'Automated playtesting agents for balance',
      'Training data generation for imitation learning',
    ],
    runLocal: '✅ Stable-Baselines3, CleanRL, or custom PyTorch',
    rtxFit: 'Great — GPU-accelerated env rollouts',
    color: '#eab308',
    bg: 'rgba(234,179,8,0.08)',
  },
  {
    id: 'hybrid',
    name: 'Hybrid / MoE Models',
    emoji: '🧬',
    tag: 'THE FUTURE',
    tagColor: '#a78bfa',
    since: '2024',
    analogy: 'A special ops team where each member is an expert — the router decides who handles each job.',
    how: 'Mixture of Experts (MoE): sparse activation routes tokens to specialized sub-networks. Jamba = Transformer + Mamba layers alternating. Griffin = recurrence + local attention.',
    strengths: [
      'Best of multiple architectures',
      'Efficient: only activates relevant experts per token',
      'Current research frontier — likely where big models are going',
      'Flexible to new tasks',
    ],
    weaknesses: [
      'Complex to implement and fine-tune',
      'Load balancing across experts is tricky',
      'Fewer ready-made tools',
    ],
    gameDevUse: [
      'Master AI director for Deep Command — routes between tactical SSM and strategic Transformer',
      'ForgePipeline — route between diffusion (assets) and LLM (descriptions)',
      'UnrealMCP v2 — multi-expert agent routing game commands to the right handler',
    ],
    runLocal: '⚠️ Emerging — Mixtral is the easiest MoE to run locally via Ollama',
    rtxFit: 'Good for Mixtral-8x7B — needs smart quantization',
    color: '#a78bfa',
    bg: 'rgba(167,139,250,0.08)',
  },
];

const PROJECT_MAP: Record<ProjectName, string[]> = {
  'Deep Command': ['mamba', 'transformer', 'rl', 'gnn'],
  'UnrealMCP': ['transformer', 'hybrid'],
  'ForgePipeline': ['diffusion', 'transformer', 'hybrid'],
  'WizardJam': ['rl', 'transformer'],
  'Portfolio / Grizzwald': ['cnn', 'diffusion'],
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AIArchGuide() {
  const [active, setActive] = useState<string | null>(null);
  const [filter, setFilter] = useState<ProjectName | null>(null);
  const [tab, setTab] = useState<TabName>('guide');

  const visibleArchs = filter
    ? ARCHS.filter((a) => PROJECT_MAP[filter]?.includes(a.id))
    : ARCHS;

  const selected = active ? ARCHS.find((a) => a.id === active) ?? null : null;

  return (
    <div style={{ fontFamily: "'IBM Plex Mono', 'Courier New', monospace", background: '#0d0d0f', minHeight: '100vh', color: '#e8d5b0', padding: '0' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Orbitron:wght@600;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #5a3e1b; border-radius: 3px; }
        .arch-card { border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 14px 16px; cursor: pointer; transition: all 0.2s; }
        .arch-card:hover { border-color: rgba(255,255,255,0.2); transform: translateY(-2px); }
        .tag-pill { font-size: 9px; font-weight: 700; letter-spacing: 0.12em; padding: 2px 8px; border-radius: 3px; text-transform: uppercase; }
        .project-btn { border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 6px 12px; cursor: pointer; background: transparent; color: #e8d5b0; font-family: inherit; font-size: 11px; transition: all 0.15s; letter-spacing: 0.05em; }
        .project-btn:hover { background: rgba(255,255,255,0.05); border-color: #c87941; }
        .project-btn.active { background: #2a1a08; border-color: #c87941; color: #f0a855; }
        .tab-btn { background: transparent; border: none; border-bottom: 2px solid transparent; color: #8a7060; font-family: inherit; font-size: 12px; padding: 8px 16px; cursor: pointer; transition: all 0.15s; letter-spacing: 0.08em; text-transform: uppercase; }
        .tab-btn.active { color: #f0a855; border-bottom-color: #c87941; }
        .detail-label { font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase; color: #8a7060; margin-bottom: 6px; }
        .chip { display: inline-block; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px; padding: 3px 8px; font-size: 11px; margin: 3px 3px 3px 0; line-height: 1.4; }
        .glow-line { height: 1px; background: linear-gradient(90deg, transparent, #c87941, transparent); margin: 20px 0; opacity: 0.4; }
        .matrix-cell { border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 10px 12px; background: rgba(255,255,255,0.02); }
      `}</style>

      {/* Header */}
      <div style={{ background: '#0a0805', borderBottom: '1px solid rgba(200,121,65,0.25)', padding: '18px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '22px' }}>⚙️</span>
          <div>
            <div style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '16px', color: '#c87941', letterSpacing: '0.12em' }}>GRIZZWALD WORKSHOP</div>
            <div style={{ fontSize: '10px', color: '#8a7060', letterSpacing: '0.15em', textTransform: 'uppercase' }}>AI Architecture Field Guide — Beyond Transformers</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '0 24px', background: '#0c0c0e' }}>
        {(['guide', 'compare', 'roadmap'] as TabName[]).map((t) => (
          <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'guide' ? '📖 Architecture Guide' : t === 'compare' ? '📊 Comparison Matrix' : '🗺️ Your AI Roadmap'}
          </button>
        ))}
      </div>

      {tab === 'guide' && (
        <div style={{ display: 'flex', height: 'calc(100vh - 110px)', overflow: 'hidden' }}>
          {/* Sidebar */}
          <div style={{ width: '340px', minWidth: '340px', overflowY: 'auto', padding: '16px', borderRight: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ marginBottom: '14px' }}>
              <div className="detail-label" style={{ marginBottom: '8px' }}>Filter by Your Project</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {(Object.keys(PROJECT_MAP) as ProjectName[]).map((p) => (
                  <button key={p} className={`project-btn ${filter === p ? 'active' : ''}`} onClick={() => setFilter(filter === p ? null : p)}>{p}</button>
                ))}
              </div>
            </div>
            <div className="glow-line" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {visibleArchs.map((a) => (
                <div
                  key={a.id}
                  className="arch-card"
                  style={{ background: active === a.id ? a.bg : 'rgba(255,255,255,0.02)', borderColor: active === a.id ? a.color : undefined }}
                  onClick={() => setActive(active === a.id ? null : a.id)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '18px' }}>{a.emoji}</span>
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 700, color: active === a.id ? a.color : '#e8d5b0' }}>{a.name}</div>
                        <div style={{ fontSize: '10px', color: '#6a5a4a' }}>Since {a.since}</div>
                      </div>
                    </div>
                    <span className="tag-pill" style={{ background: `${a.tagColor}20`, color: a.tagColor, border: `1px solid ${a.tagColor}40` }}>{a.tag}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#a09080', lineHeight: 1.5 }}>{a.analogy}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Detail panel */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
            {!selected ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#4a3a2a', textAlign: 'center' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🧭</div>
                <div style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '14px', marginBottom: '8px', color: '#6a5a3a' }}>SELECT AN ARCHITECTURE</div>
                <div style={{ fontSize: '12px', maxWidth: '300px', lineHeight: 1.6 }}>Click any card to explore how it works, why it matters, and how to use it in your game dev stack.</div>
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
                  <span style={{ fontSize: '32px' }}>{selected.emoji}</span>
                  <div>
                    <div style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '20px', color: selected.color }}>{selected.name}</div>
                    <span className="tag-pill" style={{ background: `${selected.tagColor}20`, color: selected.tagColor, border: `1px solid ${selected.tagColor}40` }}>{selected.tag}</span>
                  </div>
                </div>

                <div style={{ marginBottom: '18px' }}>
                  <div className="detail-label">⚙️ How It Works</div>
                  <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', padding: '12px 14px', fontSize: '12px', lineHeight: 1.7, color: '#d0b898' }}>{selected.how}</div>
                </div>

                <div style={{ marginBottom: '18px' }}>
                  <div className="detail-label">🎖️ The Submarine Analogy</div>
                  <div style={{ background: `${selected.color}10`, border: `1px solid ${selected.color}30`, borderRadius: '6px', padding: '12px 14px', fontSize: '12px', lineHeight: 1.7, color: '#e8d5b0', fontStyle: 'italic' }}>"{selected.analogy}"</div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '18px' }}>
                  <div>
                    <div className="detail-label">✅ Strengths</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                      {selected.strengths.map((s, i) => <div key={i} style={{ fontSize: '11px', color: '#a0d4a0', background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.1)', borderRadius: '4px', padding: '5px 8px', lineHeight: 1.4 }}>{s}</div>)}
                    </div>
                  </div>
                  <div>
                    <div className="detail-label">⚠️ Weaknesses</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                      {selected.weaknesses.map((w, i) => <div key={i} style={{ fontSize: '11px', color: '#d4a0a0', background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.1)', borderRadius: '4px', padding: '5px 8px', lineHeight: 1.4 }}>{w}</div>)}
                    </div>
                  </div>
                </div>

                <div className="glow-line" />

                <div style={{ marginBottom: '18px' }}>
                  <div className="detail-label">🎮 Your Game Dev Use Cases</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selected.gameDevUse.map((u, i) => <div key={i} style={{ fontSize: '11px', color: '#c8d4f0', background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: '4px', padding: '7px 10px', lineHeight: 1.5 }}>🔹 {u}</div>)}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                  <div className="matrix-cell"><div className="detail-label">🖥️ Run Locally</div><div style={{ fontSize: '11px', color: '#e8d5b0', lineHeight: 1.5 }}>{selected.runLocal}</div></div>
                  <div className="matrix-cell"><div className="detail-label">🎯 RTX 5080 Fit</div><div style={{ fontSize: '11px', color: '#e8d5b0', lineHeight: 1.5 }}>{selected.rtxFit}</div></div>
                </div>

                <div>
                  <div className="detail-label">📁 Relevant to Your Projects</div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {(Object.entries(PROJECT_MAP) as [ProjectName, string[]][])
                      .filter(([, ids]) => ids.includes(selected.id))
                      .map(([proj]) => <span key={proj} className="chip" style={{ color: '#c87941', borderColor: 'rgba(200,121,65,0.3)' }}>{proj}</span>)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'compare' && (
        <div style={{ padding: '24px', overflowY: 'auto', height: 'calc(100vh - 110px)' }}>
          <div className="detail-label" style={{ marginBottom: '16px' }}>Quick Comparison: All Architectures</div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 6px', fontSize: '11px' }}>
              <thead>
                <tr>{['Architecture', 'Complexity', 'Inference Speed', 'Long Sequences', 'Game Dev Fit', 'Local RTX 5080'].map((h) => <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: '#8a7060', fontSize: '9px', letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 600 }}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {[
                  ['⚡ Transformer', 'O(n²)', '🟡 Moderate', '🔴 Expensive', '⭐⭐⭐⭐', '✅ Ollama'],
                  ['🐍 Mamba (SSM)', 'O(n)', '🟢 Fast', '🟢 Excellent', '⭐⭐⭐⭐⭐', '⚠️ Manual setup'],
                  ['🔄 RWKV', 'O(1)/step', '🟢 Very Fast', '🟢 Excellent', '⭐⭐⭐⭐', '✅ RWKV.cpp'],
                  ['🌫️ Diffusion', 'O(steps×n)', '🟡 Moderate', 'N/A (images)', '⭐⭐⭐⭐⭐', '✅ ComfyUI'],
                  ['🕸️ GNN', 'O(E+V)', '🟢 Fast', '🟡 Graph-depth', '⭐⭐⭐', '✅ PyG'],
                  ['👁️ CNN/ViT', 'O(n)', '🟢 Very Fast', '🔴 Fixed grid', '⭐⭐⭐', '✅ torchvision'],
                  ['🎮 RL Agent', 'Varies', '🟢 Inference fast', '🟡 Episode length', '⭐⭐⭐⭐⭐', '✅ SB3/CleanRL'],
                  ['🧬 MoE Hybrid', 'O(n) sparse', '🟢 Fast (sparse)', '🟢 Good', '⭐⭐⭐⭐', '⚠️ Mixtral via Ollama'],
                ].map(([name, ...cells], i) => (
                  <tr key={i} style={{ background: 'rgba(255,255,255,0.02)' }}>
                    <td style={{ padding: '10px 12px', color: '#e8d5b0', fontWeight: 600, borderRadius: '6px 0 0 6px', border: '1px solid rgba(255,255,255,0.06)', borderRight: 'none' }}>{name}</td>
                    {cells.map((c, j) => <td key={j} style={{ padding: '10px 12px', color: '#b0a090', border: '1px solid rgba(255,255,255,0.06)', borderLeft: 'none', borderRight: j === cells.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none', borderRadius: j === cells.length - 1 ? '0 6px 6px 0' : '0' }}>{c}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'roadmap' && (
        <div style={{ padding: '24px', overflowY: 'auto', height: 'calc(100vh - 110px)' }}>
          <div className="detail-label" style={{ marginBottom: '20px' }}>Marcus's AI Integration Roadmap — Priority Order</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { phase: 'NOW', color: '#10b981', title: 'Keep using Transformers (Ollama)', desc: "You're already doing this right. qwen2.5-coder for code, Claude/GPT for architecture. Stick with it for UnrealMCP commands and Deep Command design work.", action: 'No change needed — you\'re set.' },
              { phase: 'NEXT', color: '#f59e0b', title: 'Add Diffusion for ForgePipeline', desc: 'Your RTX 5080 is purpose-built for this. ComfyUI + SDXL or Flux for texture/concept generation. This directly unblocks ForgePipeline\'s MVP.', action: 'Install ComfyUI, experiment with ControlNet for consistent ship textures.' },
              { phase: 'Q3 2026', color: '#8b5cf6', title: 'Explore Mamba for Deep Command sensors', desc: 'Naval combat data is a time series — sonar pings, radar sweeps, torpedo tracks. Mamba handles long temporal sequences with linear cost, perfect for real-time game state.', action: 'Study HuggingFace mamba-ssm library. Start with a Python prototype that takes game event logs as input.' },
              { phase: 'Q3 2026', color: '#06b6d4', title: 'RL Agent for enemy AI', desc: "Deep Command's enemy fleet commanders should LEARN fleet tactics. Start with Stable-Baselines3 + a simple UE5 Python bridge. WizardJam boss AI would also benefit.", action: 'Scope a simple 1v1 ship duel environment first. Get that training loop working before scaling.' },
              { phase: 'Q4 2026', color: '#ec4899', title: 'GNN for faction/diplomacy graph', desc: 'Nation defection mechanics and faction relationships are graph data. A GNN can learn \'who betrays who based on past interactions\' in a way a lookup table can\'t.', action: 'Model your faction system as a graph. PyTorch Geometric is the cleanest entry point.' },
              { phase: '2027', color: '#a78bfa', title: 'MoE Hybrid for UnrealMCP v2', desc: 'Route different command types to different expert models — natural language to a Transformer, sensor streams to an SSM, asset generation to Diffusion. This is the future architecture of your AI director.', action: 'Study Jamba (Transformer+Mamba hybrid) as the reference architecture.' },
            ].map((r, i) => (
              <div key={i} style={{ display: 'flex', gap: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '16px' }}>
                <div style={{ minWidth: '60px', textAlign: 'center' }}>
                  <div style={{ background: `${r.color}20`, border: `1px solid ${r.color}50`, borderRadius: '6px', padding: '4px 6px', fontSize: '9px', fontWeight: 700, color: r.color, letterSpacing: '0.1em' }}>{r.phase}</div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: r.color, marginBottom: '6px' }}>{r.title}</div>
                  <div style={{ fontSize: '11px', color: '#a09080', lineHeight: 1.6, marginBottom: '10px' }}>{r.desc}</div>
                  <div style={{ fontSize: '11px', color: '#c8d4f0', background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: '4px', padding: '7px 10px' }}>🎯 Action: {r.action}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
