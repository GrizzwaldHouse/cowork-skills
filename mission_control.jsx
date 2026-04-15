import { useState, useEffect, useCallback } from "react";

const PHASES = [
  { id: "detect", name: "Detect interruption", icon: "🔍", color: "#534AB7", desc: "Git archaeology + code scanning" },
  { id: "intent", name: "Reconstruct intent", icon: "🧠", color: "#0F6E56", desc: "Read CDD comments + naming" },
  { id: "plan", name: "Plan completion", icon: "📋", color: "#185FA5", desc: "Break into discrete steps" },
  { id: "implement", name: "Implement code", icon: "⚡", color: "#D85A30", desc: "CDD step-comments first" },
  { id: "build", name: "Validate build", icon: "🔨", color: "#639922", desc: "0 errors, 0 warnings" },
  { id: "verify", name: "Behavioral verify", icon: "✅", color: "#1D9E75", desc: "Intent vs implementation" },
  { id: "supervisor", name: "Supervisor review", icon: "👨‍✈️", color: "#993556", desc: "Multi-agent verdict" },
];

const AGENTS = [
  { id: "claude", name: "Claude Worker", model: "claude-sonnet-4", status: "standby", role: "Implementation" },
  { id: "gpt", name: "ChatGPT Auditor", model: "gpt-4o", status: "standby", role: "Independent review" },
  { id: "supervisor", name: "Supervisor", model: "claude-sonnet-4", status: "standby", role: "Final verdict" },
];

const GITHUB_TOOLS = [
  { name: "GitHub Actions", status: "setup", benefit: "CI/CD pipeline", credit: "3000 min/mo" },
  { name: "GitHub Copilot", status: "active", benefit: "Code acceleration", credit: "Free" },
  { name: "DigitalOcean", status: "pending", benefit: "Deploy orchestrator", credit: "$200" },
  { name: "Azure", status: "pending", benefit: "Dashboard hosting", credit: "$100" },
  { name: "JetBrains Rider", status: "pending", benefit: "C# + UE5 IDE", credit: "Free" },
  { name: "Namecheap", status: "pending", benefit: "Portfolio domain", credit: ".me free" },
  { name: "MongoDB Atlas", status: "pending", benefit: "Scene memory DB", credit: "500MB" },
  { name: "Sentry", status: "pending", benefit: "Error tracking", credit: "5K events" },
];

const MILESTONES = [
  { week: "1-2", phase: "A", name: "Recovery infrastructure", done: true },
  { week: "2-3", phase: "B", name: "CI/CD + build verification", done: false },
  { week: "4-7", phase: "C", name: "Steam integration", done: false },
  { week: "8-12", phase: "D", name: "Multiplayer foundation", done: false },
  { week: "13-16", phase: "E", name: "Portfolio + job prep", done: false },
];

function PulseRing({ color, size = 8 }) {
  return (
    <div style={{ position: "relative", width: size * 2, height: size * 2 }}>
      <div style={{
        position: "absolute", inset: 0, borderRadius: "50%",
        background: color, opacity: 0.3,
        animation: "pulse 2s ease-in-out infinite",
      }} />
      <div style={{
        position: "absolute",
        top: size / 2, left: size / 2,
        width: size, height: size,
        borderRadius: "50%", background: color,
      }} />
    </div>
  );
}

function PhaseCard({ phase, index, active, completed, onClick }) {
  const isActive = active === index;
  const isDone = completed.includes(index);
  return (
    <div
      onClick={() => onClick(index)}
      style={{
        background: isActive ? "var(--color-background-primary)" : "var(--color-background-secondary)",
        border: `${isActive ? 2 : 0.5}px solid ${isActive ? phase.color : "var(--color-border-tertiary)"}`,
        borderRadius: 12, padding: "12px 14px", cursor: "pointer",
        transition: "all 0.2s", opacity: isDone ? 0.6 : 1,
        transform: isActive ? "scale(1.02)" : "scale(1)",
        position: "relative", overflow: "hidden",
      }}
    >
      {isDone && (
        <div style={{
          position: "absolute", top: 4, right: 8,
          fontSize: 11, fontWeight: 500, color: "var(--color-text-success)",
          background: "var(--color-background-success)",
          padding: "2px 8px", borderRadius: 6,
        }}>done</div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16 }}>{phase.icon}</span>
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>
          {phase.name}
        </span>
      </div>
      <div style={{ fontSize: 11, color: "var(--color-text-secondary)", lineHeight: 1.4 }}>
        {phase.desc}
      </div>
      {isActive && (
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0, height: 3,
          background: phase.color, borderRadius: "0 0 10px 10px",
        }} />
      )}
    </div>
  );
}

function AgentPanel({ agents, activeAgent }) {
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10,
    }}>
      {agents.map((agent) => {
        const isActive = activeAgent === agent.id;
        const colors = {
          claude: "#534AB7", gpt: "#1D9E75", supervisor: "#993556",
        };
        return (
          <div key={agent.id} style={{
            background: "var(--color-background-secondary)",
            borderRadius: 10, padding: "10px 12px",
            border: isActive ? `1.5px solid ${colors[agent.id]}` : "0.5px solid var(--color-border-tertiary)",
            transition: "all 0.3s",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
              <PulseRing color={isActive ? colors[agent.id] : "var(--color-text-tertiary)"} size={6} />
              <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)" }}>
                {agent.name}
              </span>
            </div>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{agent.role}</div>
            <div style={{
              fontSize: 10, marginTop: 6, padding: "2px 6px", borderRadius: 4,
              display: "inline-block",
              background: isActive ? colors[agent.id] + "20" : "var(--color-background-tertiary)",
              color: isActive ? colors[agent.id] : "var(--color-text-tertiary)",
              fontWeight: 500,
            }}>
              {isActive ? "working..." : "standby"}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function GitHubPackPanel() {
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8,
    }}>
      {GITHUB_TOOLS.map((tool) => (
        <div key={tool.name} style={{
          background: "var(--color-background-secondary)",
          borderRadius: 8, padding: "8px 10px",
          border: "0.5px solid var(--color-border-tertiary)",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: tool.status === "active" ? "#639922" : tool.status === "setup" ? "#BA7517" : "var(--color-text-tertiary)",
          }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)" }}>
              {tool.name}
            </div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary)" }}>
              {tool.benefit}
            </div>
          </div>
          <div style={{
            fontSize: 10, color: "var(--color-text-info)",
            background: "var(--color-background-info)",
            padding: "2px 6px", borderRadius: 4, fontWeight: 500,
            whiteSpace: "nowrap",
          }}>
            {tool.credit}
          </div>
        </div>
      ))}
    </div>
  );
}

function Timeline() {
  return (
    <div style={{ display: "flex", gap: 0, alignItems: "stretch" }}>
      {MILESTONES.map((m, i) => (
        <div key={i} style={{
          flex: 1, textAlign: "center", position: "relative",
          padding: "8px 4px",
        }}>
          <div style={{
            width: 20, height: 20, borderRadius: "50%", margin: "0 auto 6px",
            background: m.done ? "#639922" : "var(--color-background-secondary)",
            border: `2px solid ${m.done ? "#639922" : "var(--color-border-secondary)"}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 10, color: m.done ? "#fff" : "var(--color-text-tertiary)",
          }}>
            {m.done ? "✓" : m.phase}
          </div>
          {i < MILESTONES.length - 1 && (
            <div style={{
              position: "absolute", top: 17, left: "60%", right: "-40%",
              height: 2, background: m.done ? "#639922" : "var(--color-border-tertiary)",
            }} />
          )}
          <div style={{ fontSize: 10, fontWeight: 500, color: "var(--color-text-primary)" }}>
            {m.name}
          </div>
          <div style={{ fontSize: 9, color: "var(--color-text-tertiary)" }}>
            Wk {m.week}
          </div>
        </div>
      ))}
    </div>
  );
}

function SimLog({ logs }) {
  return (
    <div style={{
      background: "#1a1a2e", borderRadius: 8, padding: "10px 12px",
      fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.6,
      maxHeight: 160, overflowY: "auto", color: "#a8d8a8",
    }}>
      {logs.map((log, i) => (
        <div key={i} style={{
          color: log.type === "error" ? "#f77" : log.type === "success" ? "#7f7" : log.type === "warn" ? "#fd7" : "#a8d8a8",
        }}>
          <span style={{ color: "#666", marginRight: 8 }}>{log.time}</span>
          <span style={{ color: "#7af", marginRight: 8 }}>[{log.source}]</span>
          {log.msg}
        </div>
      ))}
      {logs.length === 0 && (
        <div style={{ color: "#666" }}>Waiting for pipeline activation...</div>
      )}
    </div>
  );
}

export default function MissionControl() {
  const [activePhase, setActivePhase] = useState(0);
  const [completedPhases, setCompletedPhases] = useState([]);
  const [activeAgent, setActiveAgent] = useState(null);
  const [simRunning, setSimRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [tab, setTab] = useState("pipeline");

  const addLog = useCallback((source, msg, type = "info") => {
    const now = new Date();
    const time = now.toLocaleTimeString("en-US", { hour12: false });
    setLogs((prev) => [...prev.slice(-30), { time, source, msg, type }]);
  }, []);

  const runSimulation = useCallback(async () => {
    setSimRunning(true);
    setCompletedPhases([]);
    setLogs([]);
    const delay = (ms) => new Promise((r) => setTimeout(r, ms));

    const steps = [
      { phase: 0, agent: "claude", log: "Scanning git log --oneline -20...", delay: 800 },
      { phase: 0, agent: "claude", log: "Found 3 uncommitted files + 2 TODO markers", delay: 600 },
      { phase: 0, agent: "claude", log: "Recovery anchor: SpawnManager.cpp:247 (COMMENTS_ONLY)", type: "success", delay: 700 },
      { phase: 1, agent: "claude", log: "Reading CDD step-comments in ExecuteBatchSpawn()...", delay: 900 },
      { phase: 1, agent: "claude", log: "Intent: async batch spawn with thread-safe chunks", type: "success", delay: 600 },
      { phase: 2, agent: "claude", log: "3 of 5 steps implemented, 2 PENDING", delay: 500 },
      { phase: 3, agent: "claude", log: "Writing STEP 4: Collect results on game thread...", delay: 1200 },
      { phase: 3, agent: "claude", log: "Writing STEP 5: Register actors + broadcast event...", delay: 1000 },
      { phase: 3, agent: "claude", log: "Implementation complete — 5/5 steps done", type: "success", delay: 500 },
      { phase: 4, agent: "claude", log: "Running: dotnet build --no-incremental...", delay: 1500 },
      { phase: 4, agent: "claude", log: "Build: 0 errors, 0 warnings", type: "success", delay: 600 },
      { phase: 5, agent: "claude", log: "Verifying event-driven flow (no polling)... PASS", type: "success", delay: 800 },
      { phase: 5, agent: "claude", log: "Verifying DI usage... PASS", type: "success", delay: 500 },
      { phase: 6, agent: "gpt", log: "ChatGPT auditor reviewing implementation...", delay: 1500 },
      { phase: 6, agent: "gpt", log: "Score: alignment=90, arch=85, build=100, defense=75, docs=80", type: "success", delay: 800 },
      { phase: 6, agent: "supervisor", log: "Reconciling worker + auditor reviews...", delay: 1000 },
      { phase: 6, agent: "supervisor", log: "VERDICT: APPROVED (overall: 86/100)", type: "success", delay: 800 },
    ];

    for (const step of steps) {
      setActivePhase(step.phase);
      setActiveAgent(step.agent);
      addLog(step.agent, step.log, step.type || "info");
      await delay(step.delay);
      if (step.type === "success" && step.phase < 6) {
        if (steps.findIndex((s) => s.phase === step.phase + 1) ===
            steps.indexOf(steps.find((s, idx) => idx > steps.indexOf(step) && s.phase === step.phase + 1))) {
        }
      }
    }

    setCompletedPhases([0, 1, 2, 3, 4, 5, 6]);
    setActiveAgent(null);
    setSimRunning(false);
    addLog("pipeline", "ALL PHASES COMPLETE — SESSION RECOVERED", "success");
  }, [addLog]);

  return (
    <div style={{ padding: "1rem 0" }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 0.3; }
          50% { transform: scale(2); opacity: 0; }
        }
      `}</style>

      <div style={{
        display: "flex", gap: 8, marginBottom: 16,
        borderBottom: "0.5px solid var(--color-border-tertiary)",
        paddingBottom: 8,
      }}>
        {["pipeline", "agents", "github", "roadmap"].map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{
            background: tab === t ? "var(--color-background-secondary)" : "transparent",
            border: tab === t ? "0.5px solid var(--color-border-secondary)" : "0.5px solid transparent",
            borderRadius: 6, padding: "6px 14px", cursor: "pointer",
            fontSize: 13, fontWeight: tab === t ? 500 : 400,
            color: tab === t ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            transition: "all 0.2s",
          }}>
            {t === "pipeline" ? "Recovery pipeline" :
             t === "agents" ? "Agent status" :
             t === "github" ? "GitHub pack" :
             "Roadmap"}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <button
          onClick={runSimulation}
          disabled={simRunning}
          style={{
            background: simRunning ? "var(--color-background-secondary)" : "#534AB7",
            color: simRunning ? "var(--color-text-secondary)" : "#fff",
            border: "none", borderRadius: 6, padding: "6px 16px",
            cursor: simRunning ? "not-allowed" : "pointer",
            fontSize: 12, fontWeight: 500, transition: "all 0.2s",
          }}
        >
          {simRunning ? "Running..." : "Simulate recovery"}
        </button>
      </div>

      {tab === "pipeline" && (
        <>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
            gap: 8, marginBottom: 16,
          }}>
            {PHASES.map((phase, i) => (
              <PhaseCard
                key={phase.id}
                phase={phase}
                index={i}
                active={activePhase}
                completed={completedPhases}
                onClick={setActivePhase}
              />
            ))}
          </div>
          <SimLog logs={logs} />
        </>
      )}

      {tab === "agents" && (
        <>
          <AgentPanel agents={AGENTS} activeAgent={activeAgent} />
          <div style={{ marginTop: 12 }}>
            <SimLog logs={logs} />
          </div>
        </>
      )}

      {tab === "github" && <GitHubPackPanel />}

      {tab === "roadmap" && <Timeline />}
    </div>
  );
}
