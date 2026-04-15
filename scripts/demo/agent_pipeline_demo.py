# agent_pipeline_demo.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Live demonstration of the multi-agent pipeline system

"""
Demonstrates the full agent pipeline:
  1. Bootstrap all 4 agents via AgentRuntime
  2. Inject events and watch them flow through the bus
  3. Show quality scoring with disposition routing
  4. Trigger the self-improvement loop path
  5. Display audit log and agent metrics

Run from project root:
    python scripts/demo/agent_pipeline_demo.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.agent_events import (
    AgentEvent,
    FileChangeEvent,
    SkillExtractedEvent,
    SkillValidatedEvent,
    SkillRefactorRequestedEvent,
    SkillImprovedEvent,
    SkillRefactorFailedEvent,
    SkillSyncedEvent,
    SessionDetectedEvent,
    AgentStatusChangedEvent,
)
from scripts.agent_event_bus import EventBus
from scripts.agent_protocol import AgentStatus
from scripts.agent_base import BaseAgent
from scripts.agent_registry import AgentRegistry
from scripts.agent_runtime import AgentRuntime
from scripts.quality_scoring import QualityScoringEngine
from scripts.improvement_tracker import (
    ImprovementTrendTracker,
    RefactorCooldownTracker,
    ImprovementRecord,
)


# -- Terminal colors (ANSI) ---------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[97m"

DIVIDER = f"{DIM}{'─' * 70}{RESET}"
DOUBLE_DIVIDER = f"{CYAN}{'═' * 70}{RESET}"


def header(text: str) -> None:
    print(f"\n{DOUBLE_DIVIDER}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{DOUBLE_DIVIDER}\n")


def step(num: int, text: str) -> None:
    print(f"  {BOLD}{YELLOW}[Step {num}]{RESET} {text}")


def event_log(event_name: str, detail: str) -> None:
    print(f"    {GREEN}>>> {event_name}{RESET} {DIM}— {detail}{RESET}")


def status_line(label: str, value: str, color: str = WHITE) -> None:
    print(f"    {DIM}{label:<24s}{RESET}{color}{value}{RESET}")


def score_bar(label: str, score: float, weight: float) -> None:
    bar_len = 30
    filled = int(score * bar_len)
    bar = f"{'█' * filled}{'░' * (bar_len - filled)}"
    color = GREEN if score >= 0.8 else YELLOW if score >= 0.5 else RED
    weighted = score * weight
    print(f"    {label:<16s} {color}{bar}{RESET} {score:.2f} (x{weight:.2f} = {weighted:.3f})")


def disposition_badge(disposition: str) -> str:
    colors = {
        "approved": f"{GREEN}{BOLD}APPROVED{RESET}",
        "needs_refactor": f"{YELLOW}{BOLD}NEEDS REFACTOR{RESET}",
        "needs_review": f"{MAGENTA}{BOLD}NEEDS REVIEW{RESET}",
        "rejected": f"{RED}{BOLD}REJECTED{RESET}",
    }
    return colors.get(disposition, disposition)


# -- Demo sections ------------------------------------------------------------


def demo_1_bootstrap() -> AgentRuntime:
    """Bootstrap the full agent runtime and display status."""
    header("DEMO 1: Agent Runtime Bootstrap")

    step(1, "Creating AgentRuntime and loading config...")
    runtime = AgentRuntime()

    step(2, "Bootstrapping all 4 agents...")
    runtime.bootstrap()

    infos = runtime.get_status()
    print()
    print(f"  {BOLD}Registered Agents:{RESET}")
    print(f"  {DIVIDER}")
    for info in infos:
        color = GREEN if info.status == AgentStatus.CONFIGURED else DIM
        print(
            f"    {color}● {info.name:<22s} "
            f"type={info.agent_type:<12s} "
            f"status={info.status.value}{RESET}"
        )
    print(f"  {DIVIDER}")
    print(f"  {DIM}EventBus handlers: {runtime.event_bus.handler_count}{RESET}")

    step(3, "Starting all agents...")
    started = runtime.start()
    print(f"    {GREEN}Started: {', '.join(started)}{RESET}")

    infos = runtime.get_status()
    print()
    for info in infos:
        print(
            f"    {GREEN}● {info.name:<22s} "
            f"status={BOLD}{info.status.value.upper()}{RESET}"
        )

    return runtime


def demo_2_event_flow(runtime: AgentRuntime) -> None:
    """Inject events and observe the typed dispatch."""
    header("DEMO 2: Typed Event Dispatch")

    bus = runtime.event_bus
    observed: list[str] = []

    # Tap into the bus with a wildcard observer
    def observer(event: AgentEvent) -> None:
        observed.append(type(event).__name__)

    bus.subscribe(None, observer)

    step(1, "Injecting FileChangeEvent into the bus...")
    event = FileChangeEvent(
        file_path="C:/ClaudeSkills/skills/test-skill/SKILL.md",
        event_type="modified",
        project="demo-project",
    )
    bus.publish(event)
    event_log("FileChangeEvent", f"file={event.file_path}")

    step(2, "Injecting SkillExtractedEvent...")
    extracted = SkillExtractedEvent(
        skill_id="demo-universal-formatter",
        skill_name="Universal Code Formatter",
        skill_data={
            "skill_id": "demo-universal-formatter",
            "name": "Universal Code Formatter",
            "intent": "Format code in any language using configurable rules for universal cross-project use",
            "execution_logic": (
                "Parse the AST for the target language, apply formatting rules "
                "loaded from a configuration file, validate output matches expected "
                "style constraints, and write the formatted result. Supports Python, "
                "JavaScript, TypeScript, C++, and Rust out of the box. Rules are "
                "parameterized and extensible via plugin system."
            ),
            "context": "Works with any project, framework-agnostic, portable across all environments",
            "input_pattern": "source_file: Path, config: dict[str, Any], language: str",
            "constraints": [
                "Must not modify code semantics",
                "Must be idempotent",
                "Must handle UTF-8 encoding",
            ],
            "expected_output": "Formatted source code matching configured style rules",
            "failure_modes": [
                "Parse error on malformed input",
                "Unsupported language fallback to raw copy",
            ],
        },
        source_project="demo-project",
        confidence=0.92,
    )
    bus.publish(extracted)
    event_log("SkillExtractedEvent", f"skill={extracted.skill_name} confidence={extracted.confidence}")

    step(3, "Injecting SessionDetectedEvent...")
    session = SessionDetectedEvent(
        signal="SESSION_ACTIVE",
        project="demo-project",
        artifacts=("plans/demo-plan.md",),
        details={"source": "demo"},
    )
    bus.publish(session)
    event_log("SessionDetectedEvent", f"signal={session.signal} project={session.project}")

    print(f"\n  {BOLD}Events observed by wildcard handler:{RESET}")
    for name in observed:
        print(f"    {CYAN}↳ {name}{RESET}")

    # Show audit log
    audit = bus.get_audit_log(limit=5)
    print(f"\n  {BOLD}EventBus Audit Log (last {len(audit)} entries):{RESET}")
    print(f"  {DIVIDER}")
    for entry in audit:
        print(
            f"    {DIM}{entry['timestamp'][:19]}{RESET}  "
            f"{CYAN}{entry['event_type']}{RESET}  "
            f"{DIM}id={entry['event_id'][:8]}...{RESET}"
        )
    print(f"  {DIVIDER}")

    bus.unsubscribe(None, observer)


def demo_3_quality_scoring() -> None:
    """Score skills with the 5-dimension engine and show disposition routing."""
    header("DEMO 3: Quality Scoring Engine — 5 Dimensions")

    engine = QualityScoringEngine()

    # --- Skill A: High-quality, universal skill ---
    step(1, "Scoring a high-quality universal skill...")
    good_skill = {
        "skill_id": "demo-universal-formatter",
        "name": "Universal Code Formatter",
        "intent": "Format code in any language using configurable rules for universal cross-project use",
        "execution_logic": (
            "Parse the AST for the target language, apply formatting rules "
            "loaded from a configuration file, validate output matches expected "
            "style constraints, and write the formatted result. Supports Python, "
            "JavaScript, TypeScript, C++, and Rust out of the box. Rules are "
            "parameterized and extensible via plugin system."
        ),
        "context": "Works with any project, framework-agnostic, portable, reusable across all environments",
        "input_pattern": "source_file: Path, config: dict[str, Any], language: str",
        "constraints": ["Must not modify semantics", "Must be idempotent", "Must handle UTF-8"],
        "expected_output": "Formatted source code matching configured style rules",
        "failure_modes": ["Parse error on malformed input", "Unsupported language"],
    }
    validation_report = {
        "architecture_score": 0.95,
        "security_score": 0.92,
        "quality_score": 0.88,
    }

    report = engine.score(good_skill, validation_report)
    print(f"\n  {BOLD}Skill: {good_skill['name']}{RESET}\n")

    for dim in report.dimensions:
        score_bar(dim.dimension.capitalize(), dim.score, dim.weight)

    composite = report.composite_score
    color = GREEN if composite >= 0.8 else YELLOW if composite >= 0.5 else RED
    print(f"\n    {'─' * 50}")
    print(f"    {BOLD}Composite Score:    {color}{composite:.4f}{RESET}")
    print(f"    {BOLD}Disposition:        {disposition_badge(report.disposition)}")

    if report.violations:
        print(f"\n    {DIM}Violations:{RESET}")
        for v in report.violations:
            print(f"      {DIM}• {v}{RESET}")

    # --- Skill B: Poor, project-specific skill ---
    step(2, "\nScoring a poor, project-specific skill...")
    bad_skill = {
        "skill_id": "demo-hacky-fix",
        "name": "Quick DB Patch",
        "intent": "Fix the prod DB",
        "execution_logic": "Run the SQL patch script",
        "context": "This repo only, works only with our internal database at C:\\Users\\bob\\project\\db",
        "input_pattern": "",
        "constraints": [],
        "expected_output": "",
        "failure_modes": [],
    }
    bad_validation = {
        "architecture_score": 0.30,
        "security_score": 0.25,
        "quality_score": 0.20,
    }

    report_bad = engine.score(bad_skill, bad_validation)
    print(f"\n  {BOLD}Skill: {bad_skill['name']}{RESET}\n")

    for dim in report_bad.dimensions:
        score_bar(dim.dimension.capitalize(), dim.score, dim.weight)

    composite_bad = report_bad.composite_score
    color = GREEN if composite_bad >= 0.8 else YELLOW if composite_bad >= 0.5 else RED
    print(f"\n    {'─' * 50}")
    print(f"    {BOLD}Composite Score:    {color}{composite_bad:.4f}{RESET}")
    print(f"    {BOLD}Disposition:        {disposition_badge(report_bad.disposition)}")

    if report_bad.violations:
        print(f"\n    {DIM}Violations:{RESET}")
        for v in report_bad.violations:
            print(f"      {RED}• {v}{RESET}")

    # --- Skill C: Borderline skill (needs refactor) ---
    step(3, "\nScoring a borderline skill (refactor territory)...")
    mid_skill = {
        "skill_id": "demo-logger-wrapper",
        "name": "Structured Logger",
        "intent": "Provide structured JSON logging for any application with configurable output",
        "execution_logic": (
            "Initialize logger with JSON formatter, configure output handlers "
            "based on environment config, support log levels and filtering."
        ),
        "context": "Reusable logging utility, cross-project",
        "input_pattern": "config: dict, app_name: str",
        "constraints": ["Must not block main thread"],
        "expected_output": "Configured logger instance writing structured JSON to outputs",
        "failure_modes": ["Config parse failure"],
    }
    mid_validation = {
        "architecture_score": 0.70,
        "security_score": 0.75,
        "quality_score": 0.60,
    }

    report_mid = engine.score(mid_skill, mid_validation)
    print(f"\n  {BOLD}Skill: {mid_skill['name']}{RESET}\n")

    for dim in report_mid.dimensions:
        score_bar(dim.dimension.capitalize(), dim.score, dim.weight)

    composite_mid = report_mid.composite_score
    color = GREEN if composite_mid >= 0.8 else YELLOW if composite_mid >= 0.5 else RED
    print(f"\n    {'─' * 50}")
    print(f"    {BOLD}Composite Score:    {color}{composite_mid:.4f}{RESET}")
    print(f"    {BOLD}Disposition:        {disposition_badge(report_mid.disposition)}")

    if report_mid.violations:
        print(f"\n    {DIM}Details:{RESET}")
        for v in report_mid.violations:
            print(f"      {YELLOW}• {v}{RESET}")


def demo_4_improvement_tracker() -> None:
    """Show the improvement trend tracker and cooldown system."""
    header("DEMO 4: Self-Improvement Loop — Trend Tracking")

    import tempfile
    import scripts.improvement_tracker as tracker_mod

    # Use temp dir for demo persistence
    with tempfile.TemporaryDirectory() as tmp:
        original_dir = tracker_mod._DATA_DIR
        tracker_mod._DATA_DIR = Path(tmp)

        trend = ImprovementTrendTracker({"improvement": {"regression_tolerance": 0.0}})
        cooldown = RefactorCooldownTracker(
            {"improvement": {"cooldown_seconds": 5, "max_consecutive_failures": 3}}
        )

        step(1, "Simulating improvement iterations for 'structured-logger'...")
        scores = [0.55, 0.62, 0.68, 0.74, 0.79]
        print()

        for i, score in enumerate(scores):
            prev = scores[i - 1] if i > 0 else 0.50
            record = ImprovementRecord(
                skill_id="demo-logger",
                skill_name="Structured Logger",
                previous_score=prev,
                new_score=score,
                improved=score > prev,
                iterations=i + 1,
            )
            trend.record(record)

            bar_len = 30
            filled = int(score * bar_len)
            bar = f"{'█' * filled}{'░' * (bar_len - filled)}"
            color = GREEN if score >= 0.8 else YELLOW if score >= 0.5 else RED
            delta = score - prev
            delta_str = f"{GREEN}+{delta:.2f}{RESET}" if delta > 0 else f"{RED}{delta:.2f}{RESET}"
            print(
                f"    Iteration {i + 1}: {color}{bar}{RESET} {score:.2f} "
                f"(delta: {delta_str})"
            )

        best = trend.get_best_score("demo-logger")
        trend_info = trend.get_trend("demo-logger")
        print(f"\n    {BOLD}Best Score:{RESET}    {GREEN}{best:.2f}{RESET}")
        print(f"    {BOLD}Trend:{RESET}         {trend_info['direction']} (avg delta: {trend_info['avg_delta']:+.4f})")

        step(2, "\nRegression detection test...")
        is_regression = trend.check_regression("demo-logger", 0.70)
        print(f"    Score 0.70 vs best {best:.2f}: {RED}REGRESSION BLOCKED{RESET}" if is_regression else f"    Score 0.70: Accepted")

        is_ok = trend.check_regression("demo-logger", 0.82)
        print(f"    Score 0.82 vs best {best:.2f}: {GREEN}ACCEPTED{RESET}" if not is_ok else f"    Score 0.82: Blocked")

        step(3, "\nCooldown & escalation demo...")
        print(f"    On cooldown initially: {cooldown.is_on_cooldown('demo-logger')}")

        for i in range(3):
            count = cooldown.record_failure("demo-logger")
            remaining = cooldown.get_cooldown_remaining("demo-logger")
            should_esc = cooldown.should_escalate("demo-logger")
            print(
                f"    Failure #{count}: cooldown={remaining:.1f}s "
                f"escalate={RED + 'YES' + RESET if should_esc else GREEN + 'no' + RESET}"
            )

        print(f"\n    {BOLD}After 3 failures → {RED}ESCALATED TO HUMAN REVIEW{RESET}")

        # Reset for success demo
        cooldown.record_success("demo-logger")
        print(f"    After success: failures reset to {cooldown.get_failure_count('demo-logger')}")

        tracker_mod._DATA_DIR = original_dir


def demo_5_full_pipeline(runtime: AgentRuntime) -> None:
    """Show the complete event pipeline with disposition routing."""
    header("DEMO 5: Full Pipeline — Event Flow Visualization")

    bus = runtime.event_bus
    pipeline_log: list[tuple[str, str, str]] = []

    # Tap all event types
    def log_event(event: AgentEvent) -> None:
        name = type(event).__name__
        detail = ""
        if isinstance(event, SkillValidatedEvent):
            detail = f"disposition={event.disposition} score={event.composite_score:.2f}"
        elif isinstance(event, SkillExtractedEvent):
            detail = f"skill={event.skill_name} confidence={event.confidence}"
        elif isinstance(event, SkillRefactorRequestedEvent):
            detail = f"skill={event.skill_name} target={event.target_score}"
        elif isinstance(event, SkillSyncedEvent):
            detail = f"skill={event.skill_name} type={event.sync_type}"
        pipeline_log.append((event.timestamp[:19], name, detail))

    bus.subscribe(None, log_event)

    step(1, "Publishing SkillValidatedEvent (APPROVED path)...")
    bus.publish(SkillValidatedEvent(
        skill_id="demo-approved",
        skill_name="Universal Formatter",
        disposition="approved",
        composite_score=0.91,
        dimension_scores={"architecture": 0.95, "security": 0.92, "quality": 0.88, "reusability": 0.90, "completeness": 0.85},
        violations=(),
    ))
    event_log("SkillValidatedEvent", "→ APPROVED → SyncAgent picks this up")

    step(2, "Publishing SkillValidatedEvent (NEEDS_REFACTOR path)...")
    bus.publish(SkillValidatedEvent(
        skill_id="demo-refactor",
        skill_name="Structured Logger",
        disposition="needs_refactor",
        composite_score=0.65,
        dimension_scores={"architecture": 0.70, "security": 0.75, "quality": 0.60, "reusability": 0.55, "completeness": 0.50},
        violations=("Reusability: no parameterized input_pattern defined",),
    ))
    event_log("SkillValidatedEvent", "→ NEEDS_REFACTOR → RefactorAgent would pick this up")

    step(3, "Publishing SkillValidatedEvent (REJECTED path)...")
    bus.publish(SkillValidatedEvent(
        skill_id="demo-rejected",
        skill_name="Quick DB Patch",
        disposition="rejected",
        composite_score=0.22,
        dimension_scores={"architecture": 0.30, "security": 0.25, "quality": 0.20, "reusability": 0.10, "completeness": 0.05},
        violations=(
            "Reusability: project-specific indicator found: 'this repo only'",
            "Completeness: missing section 'constraints'",
            "Completeness: missing section 'failure_modes'",
        ),
    ))
    event_log("SkillValidatedEvent", "→ REJECTED → Logged and discarded")

    step(4, "Simulating improvement success path...")
    bus.publish(SkillImprovedEvent(
        skill_id="demo-refactor",
        skill_name="Structured Logger",
        previous_score=0.65,
        new_score=0.84,
        iterations_used=4,
        branch_name="skill-improve/structured-logger-20260405",
    ))
    event_log("SkillImprovedEvent", "→ Re-enters ValidatorAgent for re-validation")

    # Display pipeline log
    print(f"\n  {BOLD}Pipeline Event Log:{RESET}")
    print(f"  {DIVIDER}")
    for ts, name, detail in pipeline_log:
        print(f"    {DIM}{ts}{RESET}  {CYAN}{name:<35s}{RESET} {detail}")
    print(f"  {DIVIDER}")

    bus.unsubscribe(None, log_event)


def demo_6_agent_metrics(runtime: AgentRuntime) -> None:
    """Show final agent metrics after the demo run."""
    header("DEMO 6: Agent Metrics Summary")

    infos = runtime.get_status()
    print(f"  {BOLD}{'Agent':<24s} {'Status':<12s} {'Processed':<12s} {'Emitted':<10s} {'Errors':<8s}{RESET}")
    print(f"  {DIVIDER}")
    for info in infos:
        status_color = GREEN if info.status == AgentStatus.RUNNING else DIM
        print(
            f"  {status_color}{info.name:<24s} "
            f"{info.status.value:<12s} "
            f"{info.events_processed:<12d} "
            f"{info.events_emitted:<10d} "
            f"{info.error_count:<8d}{RESET}"
        )
    print(f"  {DIVIDER}")

    print(f"\n  {BOLD}EventBus:{RESET}")
    status_line("Registered handlers:", str(runtime.event_bus.handler_count))
    audit = runtime.event_bus.get_audit_log(limit=100)
    status_line("Total events logged:", str(len(audit)))
    print()


# -- Main ---------------------------------------------------------------------

def main() -> None:
    print(f"\n{BOLD}{MAGENTA}")
    print("   ╔══════════════════════════════════════════════════════════╗")
    print("   ║     MULTI-AGENT PIPELINE FRAMEWORK — LIVE DEMO         ║")
    print("   ║     ClaudeSkills • Marcus Daley • 2026-04-05           ║")
    print("   ╚══════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    # Demo 1: Bootstrap
    runtime = demo_1_bootstrap()

    # Demo 2: Event dispatch
    demo_2_event_flow(runtime)

    # Demo 3: Quality scoring
    demo_3_quality_scoring()

    # Demo 4: Improvement tracker
    demo_4_improvement_tracker()

    # Demo 5: Full pipeline
    demo_5_full_pipeline(runtime)

    # Demo 6: Metrics
    demo_6_agent_metrics(runtime)

    # Shutdown
    runtime.stop()
    print(f"  {GREEN}All agents stopped. Demo complete.{RESET}\n")


if __name__ == "__main__":
    main()
