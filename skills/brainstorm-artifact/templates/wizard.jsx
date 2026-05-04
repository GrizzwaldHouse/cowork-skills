import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { ChevronUp, ChevronDown, Mic, Flag, Edit3, Layers, Volume2, VolumeX, Award } from "lucide-react";

/* =========================================================================
   BRAINSTORM ARTIFACT WIZARD (Internal Mode)
   Replace BRAINSTORM_DATA with the session content. Everything below the
   data block is configuration-driven and should not need editing per project.
   ========================================================================= */

const BRAINSTORM_DATA = {
  metadata: {
    projectName: "Sample Project",
    sessionDate: "2026-05-01",
    themeKey: "vetassist_tactical",
    mode: "internal",
    preLockedContext: [
      { label: "Platform", value: "Web-first PWA" },
      { label: "Stack", value: "Next.js + Postgres" }
    ]
  },
  sections: [
    {
      id: "platform",
      title: "Platform & Storage",
      questions: [
        {
          id: "draft_storage",
          type: "single",
          prompt: "Where do in-progress drafts live during the wizard session?",
          options: [
            { label: "Local-first IndexedDB", rationale: "Works offline, sync on save." },
            { label: "Cloud-first Postgres", rationale: "Multi-device, requires connection." },
            { label: "Hybrid", rationale: "Local cache plus explicit cloud sync." },
            { label: "Session-only", rationale: "No persistence, fastest path." }
          ]
        }
      ]
    }
  ]
};

/* =========================================================================
   CONFIGURATION CONSTANTS (no hardcoded values inline)
   ========================================================================= */

const XP_RULES = {
  SINGLE_SELECT: 10,
  MULTI_SELECT_PER_OPTION: 10,
  TRUE_FALSE: 10,
  RANKED_CHANGE: 10,
  NUMERIC_SCALE_PER_ROW: 10,
  ABC_MATCH_PER_ROW: 10,
  OVERRIDE_USED: 5,
  HYBRID_USED: 5,
  FLAG_USED: 5
};

const RANK_THRESHOLD = 200;

const SOUND_CUES = {
  selection: { freq: [880], duration: 80 },
  lock: { freq: [523, 659], duration: 120 },
  achievement: { freq: [523, 659, 784], duration: 350 },
  rankUp: { freq: [523, 659, 784, 1047], duration: 440 }
};

const STORAGE_KEY_PREFIX = "brainstorm:";

const THEMES = {
  vetassist_tactical: {
    bgBase: "#0a0e0a",
    bgSurface: "#141a14",
    bgRaised: "#1f2820",
    accent: "#8a6d3b",
    accentBright: "#c9a96e",
    textPrimary: "#e8e0c8",
    textMuted: "#9aa093",
    border: "#2a3528",
    success: "#5a8a5a",
    warning: "#c9a96e",
    danger: "#a85a4a",
    sectionColors: ["#5a8a5a", "#8a6d3b", "#6d8a8a", "#a85a4a"],
    fontDisplay: "'Playfair Display', serif",
    fontBody: "'Playfair Display', serif",
    fontMono: "'JetBrains Mono', monospace",
    iconChar: "\u25C6",
    rankNames: ["Recruit", "PO3", "PO2", "PO1", "Chief", "Senior Chief", "Master Chief"]
  },
  game_dev_arcade: {
    bgBase: "#1a0a2e",
    bgSurface: "#241040",
    bgRaised: "#3a1a5a",
    accent: "#ff4d8d",
    accentBright: "#ff80b3",
    textPrimary: "#f0e8ff",
    textMuted: "#a890c8",
    border: "#4a2a6a",
    success: "#5affb3",
    warning: "#ffd84d",
    danger: "#ff4d4d",
    sectionColors: ["#5affb3", "#ff4d8d", "#ffd84d", "#80b3ff"],
    fontDisplay: "'Press Start 2P', monospace",
    fontBody: "'JetBrains Mono', monospace",
    fontMono: "'JetBrains Mono', monospace",
    iconChar: "\u25B2",
    rankNames: ["Pixel", "Sprite", "Coder", "Designer", "Architect", "Lead", "Director"]
  },
  research_editorial: {
    bgBase: "#f5efe0",
    bgSurface: "#ebe2cc",
    bgRaised: "#ddd0b0",
    accent: "#6b4a2a",
    accentBright: "#8a6a40",
    textPrimary: "#2a1f10",
    textMuted: "#6a5840",
    border: "#c9b890",
    success: "#5a7040",
    warning: "#a08040",
    danger: "#8a3a2a",
    sectionColors: ["#5a7040", "#6b4a2a", "#a08040", "#3a5a6a"],
    fontDisplay: "'Playfair Display', serif",
    fontBody: "Georgia, serif",
    fontMono: "'JetBrains Mono', monospace",
    iconChar: "\u2766",
    rankNames: ["Reader", "Scholar", "Author", "Fellow", "Professor", "Dean", "Laureate"]
  }
};

const ACHIEVEMENTS = [
  { id: "first_decision_locked", title: "First Decision Locked", description: "Locked your first answer", xp: 25 },
  { id: "voice_recon", title: "Voice Recon", description: "Used voice input for the first time", xp: 50 },
  { id: "field_notes", title: "Field Notes", description: "Used free-text override for the first time", xp: 30 },
  { id: "after_action_review", title: "After Action Review", description: "Flagged feedback for the first time", xp: 30 },
  { id: "section_cleared", title: "Section Cleared", description: "Answered every question in a section", xp: 75 },
  { id: "tier_master", title: "Tier Master", description: "Assigned every row in a tier-allocation question", xp: 100 },
  { id: "field_manual_complete", title: "Field Manual Complete", description: "Answered every question in the artifact", xp: 200 }
];

/* =========================================================================
   EVENT BUS (event-driven architecture)
   ========================================================================= */

function createEventBus() {
  const subs = new Map();
  return {
    on(event, fn) {
      if (!subs.has(event)) subs.set(event, new Set());
      subs.get(event).add(fn);
      return () => subs.get(event)?.delete(fn);
    },
    emit(event, payload) {
      subs.get(event)?.forEach((fn) => fn(payload));
      subs.get("*")?.forEach((fn) => fn({ event, payload }));
    }
  };
}

/* =========================================================================
   SOUND PLAYER (Web Audio, no external assets)
   ========================================================================= */

function playSequence(cue, enabled) {
  if (!enabled) return;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const stepMs = cue.duration / cue.freq.length;
    cue.freq.forEach((f, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = f;
      gain.gain.value = 0.15;
      osc.connect(gain).connect(ctx.destination);
      const t0 = ctx.currentTime + (i * stepMs) / 1000;
      osc.start(t0);
      osc.stop(t0 + stepMs / 1000);
    });
  } catch (e) {
    /* graceful degradation */
  }
}

/* =========================================================================
   STORAGE (window.storage in Claude artifacts)
   ========================================================================= */

async function loadAnswers(projectName) {
  const key = STORAGE_KEY_PREFIX + projectName;
  try {
    const r = await window.storage.get(key);
    return r ? JSON.parse(r.value) : {};
  } catch {
    return {};
  }
}

async function saveAnswers(projectName, answers) {
  const key = STORAGE_KEY_PREFIX + projectName;
  try {
    await window.storage.set(key, JSON.stringify(answers));
  } catch {
    /* storage failure should not break the wizard */
  }
}

/* =========================================================================
   QUESTION RENDERERS (registered in a map, not a switch)
   ========================================================================= */

function PillButton({ selected, onClick, theme, children }) {
  const style = selected
    ? { background: theme.accent, color: theme.bgBase, borderColor: theme.accentBright }
    : { background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border };
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-md border transition-colors"
      style={style}
    >
      {children}
    </button>
  );
}

function SingleRenderer({ question, answer, onAnswer, theme }) {
  return (
    <div className="space-y-2">
      {question.options.map((opt, i) => (
        <PillButton
          key={i}
          selected={answer?.selectedIndex === i}
          onClick={() => onAnswer({ selectedIndex: i })}
          theme={theme}
        >
          <div className="font-semibold">{opt.label}</div>
          {opt.rationale && (
            <div className="text-sm mt-1" style={{ color: answer?.selectedIndex === i ? theme.bgBase : theme.textMuted }}>
              {opt.rationale}
            </div>
          )}
        </PillButton>
      ))}
    </div>
  );
}

function MultiRenderer({ question, answer, onAnswer, theme }) {
  const selected = answer?.selectedIndices || [];
  const toggle = (i) => {
    const next = selected.includes(i) ? selected.filter((x) => x !== i) : [...selected, i];
    onAnswer({ selectedIndices: next });
  };
  return (
    <div className="space-y-2">
      {question.options.map((opt, i) => (
        <PillButton key={i} selected={selected.includes(i)} onClick={() => toggle(i)} theme={theme}>
          <div className="flex items-start gap-2">
            <div className="font-mono">{selected.includes(i) ? "[x]" : "[ ]"}</div>
            <div className="flex-1">
              <div className="font-semibold">{opt.label}</div>
              {opt.rationale && (
                <div className="text-sm mt-1" style={{ color: selected.includes(i) ? theme.bgBase : theme.textMuted }}>
                  {opt.rationale}
                </div>
              )}
            </div>
          </div>
        </PillButton>
      ))}
    </div>
  );
}

function TrueFalseRenderer({ question, answer, onAnswer, theme }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {question.options.map((opt, i) => (
        <button
          key={i}
          onClick={() => onAnswer({ selectedIndex: i })}
          className="p-6 rounded-md border text-center transition-colors"
          style={
            answer?.selectedIndex === i
              ? { background: theme.accent, color: theme.bgBase, borderColor: theme.accentBright }
              : { background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }
          }
        >
          <div className="text-2xl font-bold mb-2">{opt.label}</div>
          {opt.rationale && (
            <div className="text-sm" style={{ color: answer?.selectedIndex === i ? theme.bgBase : theme.textMuted }}>
              {opt.rationale}
            </div>
          )}
        </button>
      ))}
    </div>
  );
}

function RankedRenderer({ question, answer, onAnswer, theme }) {
  const order = answer?.order || question.options.map((_, i) => i);
  const move = (i, dir) => {
    const j = i + dir;
    if (j < 0 || j >= order.length) return;
    const next = [...order];
    [next[i], next[j]] = [next[j], next[i]];
    onAnswer({ order: next });
  };
  return (
    <div className="space-y-2">
      {order.map((optIdx, i) => (
        <div
          key={optIdx}
          className="flex items-center gap-3 p-3 rounded-md border"
          style={{ background: theme.bgRaised, borderColor: theme.border }}
        >
          <div className="font-mono text-lg w-8 text-center" style={{ color: theme.accentBright }}>
            {i + 1}
          </div>
          <div className="flex-1" style={{ color: theme.textPrimary }}>
            {question.options[optIdx].label}
          </div>
          <button onClick={() => move(i, -1)} className="p-1" style={{ color: theme.textMuted }}>
            <ChevronUp size={18} />
          </button>
          <button onClick={() => move(i, 1)} className="p-1" style={{ color: theme.textMuted }}>
            <ChevronDown size={18} />
          </button>
        </div>
      ))}
    </div>
  );
}

function NumericScaleRenderer({ question, answer, onAnswer, theme }) {
  const values = answer?.values || {};
  const setRow = (rowId, v) => onAnswer({ values: { ...values, [rowId]: v } });
  return (
    <div>
      <div className="grid gap-1 mb-3" style={{ gridTemplateColumns: `1fr repeat(${question.scale.labels.length}, minmax(0, 1fr))` }}>
        <div />
        {question.scale.labels.map((lab, i) => (
          <div key={i} className="text-xs text-center" style={{ color: theme.textMuted }}>
            {lab}
          </div>
        ))}
      </div>
      {question.rows.map((row) => (
        <div
          key={row.id}
          className="grid gap-1 mb-2"
          style={{ gridTemplateColumns: `1fr repeat(${question.scale.labels.length}, minmax(0, 1fr))` }}
        >
          <div className="p-2 text-sm" style={{ color: theme.textPrimary }}>
            {row.label}
          </div>
          {question.scale.labels.map((_, i) => {
            const v = question.scale.min + i;
            const sel = values[row.id] === v;
            return (
              <button
                key={i}
                onClick={() => setRow(row.id, v)}
                className="rounded border p-2"
                style={
                  sel
                    ? { background: theme.accent, color: theme.bgBase, borderColor: theme.accentBright }
                    : { background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }
                }
              >
                {v}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function AbcMatchRenderer({ question, answer, onAnswer, theme }) {
  const assignments = answer?.assignments || {};
  const setRow = (rowId, catId) => onAnswer({ assignments: { ...assignments, [rowId]: catId } });
  return (
    <div>
      <div className="mb-3 p-3 rounded" style={{ background: theme.bgRaised, color: theme.textMuted }}>
        {question.categories.map((c) => (
          <div key={c.id} className="text-sm">
            <span className="font-semibold" style={{ color: theme.accentBright }}>{c.label}:</span> {c.description}
          </div>
        ))}
      </div>
      {question.rows.map((row) => (
        <div
          key={row.id}
          className="grid gap-1 mb-2"
          style={{ gridTemplateColumns: `1fr repeat(${question.categories.length}, minmax(0, 1fr))` }}
        >
          <div className="p-2 text-sm" style={{ color: theme.textPrimary }}>
            {row.label}
          </div>
          {question.categories.map((cat) => {
            const sel = assignments[row.id] === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setRow(row.id, cat.id)}
                className="rounded border p-2 text-sm"
                style={
                  sel
                    ? { background: theme.accent, color: theme.bgBase, borderColor: theme.accentBright }
                    : { background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }
                }
              >
                {cat.label}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}

const RENDERERS = {
  single: SingleRenderer,
  multi: MultiRenderer,
  true_false: TrueFalseRenderer,
  ranked: RankedRenderer,
  numeric_scale: NumericScaleRenderer,
  abc_match: AbcMatchRenderer
};

/* =========================================================================
   AFFORDANCES (free-text, voice, hybrid, feedback flag)
   ========================================================================= */

function Affordances({ answer, onAnswer, theme, bus, questionId }) {
  const [voiceState, setVoiceState] = useState("idle");
  const recogRef = useRef(null);

  const startVoice = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const r = new SR();
    r.continuous = false;
    r.interimResults = false;
    r.onresult = (e) => {
      const t = e.results[0][0].transcript;
      const next = (answer?.override || "") + (answer?.override ? " " : "") + t;
      onAnswer({ override: next });
      bus.emit("question.override.used", { questionId });
      setVoiceState("idle");
    };
    r.onend = () => setVoiceState("idle");
    r.onerror = () => setVoiceState("idle");
    r.start();
    recogRef.current = r;
    setVoiceState("listening");
  }, [answer, onAnswer, bus, questionId]);

  const voiceSupported = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

  return (
    <div className="mt-4 pt-4 border-t border-dashed" style={{ borderColor: theme.border }}>
      <div className="flex flex-wrap gap-2 mb-2">
        <button
          onClick={() => onAnswer({ overrideOpen: !answer?.overrideOpen })}
          className="flex items-center gap-1 px-3 py-1 rounded border text-sm"
          style={{ background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }}
        >
          <Edit3 size={14} /> Override
        </button>
        {voiceSupported && (
          <button
            onClick={startVoice}
            className="flex items-center gap-1 px-3 py-1 rounded border text-sm"
            style={{
              background: voiceState === "listening" ? theme.accent : theme.bgRaised,
              color: voiceState === "listening" ? theme.bgBase : theme.textPrimary,
              borderColor: theme.border
            }}
          >
            <Mic size={14} /> {voiceState === "listening" ? "Listening..." : "Voice"}
          </button>
        )}
        <button
          onClick={() => onAnswer({ hybridOpen: !answer?.hybridOpen })}
          className="flex items-center gap-1 px-3 py-1 rounded border text-sm"
          style={{ background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }}
        >
          <Layers size={14} /> Hybrid
        </button>
        <button
          onClick={() => onAnswer({ flagOpen: !answer?.flagOpen })}
          className="flex items-center gap-1 px-3 py-1 rounded border text-sm"
          style={{ background: theme.bgRaised, color: theme.warning, borderColor: theme.border }}
        >
          <Flag size={14} /> Flag
        </button>
      </div>
      {answer?.overrideOpen && (
        <textarea
          value={answer?.override || ""}
          onChange={(e) => {
            const v = e.target.value;
            onAnswer({ override: v });
            if (v && !answer?.overrideEmitted) {
              bus.emit("question.override.used", { questionId });
              onAnswer({ override: v, overrideEmitted: true });
            }
          }}
          placeholder="Free-text override (replaces preset answer in export)"
          className="w-full p-2 rounded border text-sm mt-2"
          rows={3}
          style={{ background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }}
        />
      )}
      {answer?.hybridOpen && (
        <textarea
          value={answer?.hybrid || ""}
          onChange={(e) => {
            const v = e.target.value;
            onAnswer({ hybrid: v });
            if (v && !answer?.hybridEmitted) {
              bus.emit("question.hybrid.used", { questionId });
              onAnswer({ hybrid: v, hybridEmitted: true });
            }
          }}
          placeholder="Hybrid composer (supplements preset answer with constraints)"
          className="w-full p-2 rounded border text-sm mt-2"
          rows={2}
          style={{ background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }}
        />
      )}
      {answer?.flagOpen && (
        <textarea
          value={answer?.flag || ""}
          onChange={(e) => {
            const v = e.target.value;
            onAnswer({ flag: v });
            if (v && !answer?.flagEmitted) {
              bus.emit("question.flag.used", { questionId });
              onAnswer({ flag: v, flagEmitted: true });
            }
          }}
          placeholder="Feedback flag (this question is ambiguous, missing options, poorly worded, etc.)"
          className="w-full p-2 rounded border text-sm mt-2"
          rows={2}
          style={{ background: theme.bgRaised, color: theme.textPrimary, borderColor: theme.border }}
        />
      )}
    </div>
  );
}

/* =========================================================================
   MAIN WIZARD COMPONENT
   ========================================================================= */

export default function BrainstormWizard() {
  const { metadata, sections } = BRAINSTORM_DATA;
  const theme = THEMES[metadata.themeKey] || THEMES.vetassist_tactical;
  const isInternal = metadata.mode !== "client";

  const [answers, setAnswers] = useState({});
  const [activeSection, setActiveSection] = useState(0);
  const [xp, setXp] = useState(0);
  const [unlocked, setUnlocked] = useState(new Set());
  const [toast, setToast] = useState(null);
  const [gamificationOn, setGamificationOn] = useState(isInternal);
  const [soundOn, setSoundOn] = useState(false);

  const bus = useMemo(() => createEventBus(), []);

  useEffect(() => {
    loadAnswers(metadata.projectName).then((a) => setAnswers(a || {}));
  }, [metadata.projectName]);

  useEffect(() => {
    saveAnswers(metadata.projectName, answers);
  }, [answers, metadata.projectName]);

  // event bus subscribers
  useEffect(() => {
    const unsubs = [];
    const award = (delta, reason) => {
      setXp((cur) => {
        const next = cur + delta;
        const oldRank = Math.floor(cur / RANK_THRESHOLD);
        const newRank = Math.floor(next / RANK_THRESHOLD);
        if (newRank > oldRank) {
          playSequence(SOUND_CUES.rankUp, soundOn);
          setToast({ title: `Rank up: ${theme.rankNames[Math.min(newRank, theme.rankNames.length - 1)]}`, sub: `${reason}`, xp: delta });
        }
        return next;
      });
    };
    unsubs.push(bus.on("question.option.selected", (p) => { award(p.xp || XP_RULES.SINGLE_SELECT, "selection"); playSequence(SOUND_CUES.lock, soundOn); }));
    unsubs.push(bus.on("question.row.assigned", (p) => { award(p.xp || XP_RULES.ABC_MATCH_PER_ROW, "row"); playSequence(SOUND_CUES.selection, soundOn); }));
    unsubs.push(bus.on("question.ranked.changed", () => { award(XP_RULES.RANKED_CHANGE, "rank"); playSequence(SOUND_CUES.selection, soundOn); }));
    unsubs.push(bus.on("question.override.used", () => award(XP_RULES.OVERRIDE_USED, "override")));
    unsubs.push(bus.on("question.hybrid.used", () => award(XP_RULES.HYBRID_USED, "hybrid")));
    unsubs.push(bus.on("question.flag.used", () => award(XP_RULES.FLAG_USED, "flag")));

    // achievement checker
    const tryUnlock = (id) => {
      setUnlocked((cur) => {
        if (cur.has(id)) return cur;
        const ach = ACHIEVEMENTS.find((a) => a.id === id);
        if (!ach) return cur;
        const next = new Set(cur);
        next.add(id);
        playSequence(SOUND_CUES.achievement, soundOn);
        setToast({ title: ach.title, sub: ach.description, xp: ach.xp });
        setXp((x) => x + ach.xp);
        return next;
      });
    };
    unsubs.push(bus.on("*", ({ event }) => {
      if (event === "question.option.selected" || event === "question.row.assigned") tryUnlock("first_decision_locked");
      if (event === "question.override.used") tryUnlock("field_notes");
      if (event === "question.flag.used") tryUnlock("after_action_review");
    }));

    return () => unsubs.forEach((u) => u());
  }, [bus, soundOn, theme.rankNames]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(t);
  }, [toast]);

  const setQuestionAnswer = (qid, patch) => {
    setAnswers((cur) => ({ ...cur, [qid]: { ...(cur[qid] || {}), ...patch } }));
  };

  const handleAnswer = (q, patch) => {
    setQuestionAnswer(q.id, patch);
    if (gamificationOn) {
      if (q.type === "single" || q.type === "true_false") bus.emit("question.option.selected", { questionId: q.id, xp: XP_RULES.SINGLE_SELECT });
      if (q.type === "multi") bus.emit("question.option.selected", { questionId: q.id, xp: XP_RULES.MULTI_SELECT_PER_OPTION });
      if (q.type === "numeric_scale" || q.type === "abc_match") bus.emit("question.row.assigned", { questionId: q.id });
      if (q.type === "ranked") bus.emit("question.ranked.changed", { questionId: q.id });
    }
  };

  const exportJson = () => {
    const out = {
      metadata,
      sections,
      answers,
      xp: gamificationOn ? xp : null,
      achievements: gamificationOn ? Array.from(unlocked) : null,
      exportedAt: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `brainstorm-${metadata.projectName}-${metadata.sessionDate}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const section = sections[activeSection];
  const rankIdx = Math.min(Math.floor(xp / RANK_THRESHOLD), theme.rankNames.length - 1);
  const rankName = theme.rankNames[rankIdx];
  const xpInRank = xp % RANK_THRESHOLD;

  return (
    <div className="min-h-screen p-4" style={{ background: theme.bgBase, color: theme.textPrimary, fontFamily: theme.fontBody }}>
      <div className="max-w-3xl mx-auto">
        <header className="mb-6 p-4 rounded-md" style={{ background: theme.bgSurface, borderLeft: `4px solid ${theme.accent}` }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm" style={{ color: theme.textMuted, fontFamily: theme.fontMono }}>
                {theme.iconChar} {metadata.sessionDate}
              </div>
              <h1 className="text-2xl font-bold" style={{ fontFamily: theme.fontDisplay, color: theme.accentBright }}>
                {metadata.projectName} Brainstorm
              </h1>
            </div>
            {gamificationOn && (
              <div className="text-right">
                <div className="text-xs" style={{ color: theme.textMuted }}>{rankName}</div>
                <div className="text-sm font-mono" style={{ color: theme.accentBright }}>{xp} XP</div>
                <div className="w-32 h-1 rounded mt-1" style={{ background: theme.border }}>
                  <div className="h-1 rounded" style={{ width: `${(xpInRank / RANK_THRESHOLD) * 100}%`, background: theme.accent }} />
                </div>
              </div>
            )}
          </div>
          {metadata.preLockedContext && metadata.preLockedContext.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {metadata.preLockedContext.map((ctx, i) => (
                <span key={i} className="text-xs px-2 py-1 rounded" style={{ background: theme.bgRaised, color: theme.textMuted }}>
                  {ctx.label}: {ctx.value}
                </span>
              ))}
            </div>
          )}
          <div className="mt-3 flex gap-2 text-xs">
            {isInternal && (
              <button onClick={() => setGamificationOn((v) => !v)} className="flex items-center gap-1 px-2 py-1 rounded border" style={{ borderColor: theme.border, color: theme.textMuted }}>
                <Award size={12} /> {gamificationOn ? "Gamification on" : "Gamification off"}
              </button>
            )}
            <button onClick={() => setSoundOn((v) => !v)} className="flex items-center gap-1 px-2 py-1 rounded border" style={{ borderColor: theme.border, color: theme.textMuted }}>
              {soundOn ? <Volume2 size={12} /> : <VolumeX size={12} />} {soundOn ? "Sound on" : "Sound off"}
            </button>
          </div>
        </header>

        <nav className="flex flex-wrap gap-2 mb-4">
          {sections.map((s, i) => (
            <button
              key={s.id}
              onClick={() => setActiveSection(i)}
              className="px-3 py-1 rounded text-sm"
              style={{
                background: i === activeSection ? theme.accent : theme.bgSurface,
                color: i === activeSection ? theme.bgBase : theme.textPrimary,
                borderLeft: `3px solid ${theme.sectionColors[i % theme.sectionColors.length]}`
              }}
            >
              {s.title}
            </button>
          ))}
        </nav>

        <main>
          <h2 className="text-xl mb-4" style={{ fontFamily: theme.fontDisplay, color: theme.accentBright }}>
            {section.title}
          </h2>
          {section.questions.map((q) => {
            const Renderer = RENDERERS[q.type];
            return (
              <div key={q.id} className="mb-6 p-4 rounded-md" style={{ background: theme.bgSurface, borderLeft: `3px solid ${theme.sectionColors[activeSection % theme.sectionColors.length]}` }}>
                <div className="font-semibold mb-3" style={{ color: theme.textPrimary }}>{q.prompt}</div>
                {Renderer && (
                  <Renderer
                    question={q}
                    answer={answers[q.id]}
                    onAnswer={(patch) => handleAnswer(q, patch)}
                    theme={theme}
                  />
                )}
                <Affordances answer={answers[q.id]} onAnswer={(patch) => setQuestionAnswer(q.id, patch)} theme={theme} bus={bus} questionId={q.id} />
              </div>
            );
          })}
        </main>

        <footer className="mt-6 flex gap-2">
          <button
            onClick={exportJson}
            className="px-4 py-2 rounded font-semibold"
            style={{ background: theme.accent, color: theme.bgBase }}
          >
            Export JSON
          </button>
        </footer>

        {toast && (
          <div
            className="fixed top-4 right-4 p-3 rounded-md shadow-lg max-w-xs"
            style={{ background: theme.bgRaised, borderLeft: `4px solid ${theme.success}`, color: theme.textPrimary }}
          >
            <div className="font-semibold" style={{ color: theme.success }}>{toast.title}</div>
            <div className="text-sm" style={{ color: theme.textMuted }}>{toast.sub}</div>
            <div className="text-xs font-mono mt-1" style={{ color: theme.accentBright }}>+{toast.xp} XP</div>
          </div>
        )}
      </div>
    </div>
  );
}
