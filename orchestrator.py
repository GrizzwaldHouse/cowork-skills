# orchestrator.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Multi-agent orchestration pipeline that coordinates three AI agents
#          (Claude Worker, ChatGPT Auditor, Supervisor) for session recovery
#          and code completion with cross-agent quality verification.
#          Implements event-driven coordination — no polling between agents.

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# Configure structured logging with contextual identifiers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('orchestrator')


# ============================================================================
# Configuration — All values driven by config, never hardcoded
# ============================================================================

@dataclass
class PipelineConfig:
    """Configuration for the multi-agent pipeline. Loaded from file or env."""
    
    # API endpoints (from environment variables, never hardcoded)
    claude_api_key: str = field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    openai_api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    
    # Model selection
    claude_model: str = 'claude-sonnet-4-20250514'
    openai_model: str = 'gpt-4o'
    supervisor_model: str = 'claude-sonnet-4-20250514'
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    
    # Review thresholds
    passing_score: int = 70
    auto_approve_score: int = 90
    
    # Timeouts (seconds)
    worker_timeout: int = 300
    auditor_timeout: int = 120
    supervisor_timeout: int = 120
    
    # Project context
    project_root: str = '.'
    primary_language: str = 'auto'
    architecture_constraints: list = field(default_factory=lambda: [
        'event_driven_only', 'no_polling', 'dependency_injection',
        'separation_of_concerns', 'config_driven'
    ])
    
    @classmethod
    def from_file(cls, config_path: str) -> 'PipelineConfig':
        """Load configuration from JSON file, falling back to defaults."""
        if Path(config_path).exists():
            with open(config_path) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()
    
    @classmethod
    def from_env(cls) -> 'PipelineConfig':
        """Load configuration from environment variables."""
        config = cls()
        # Override from env vars if present
        if env_model := os.getenv('CLAUDE_MODEL'):
            config.claude_model = env_model
        if env_model := os.getenv('OPENAI_MODEL'):
            config.openai_model = env_model
        if env_root := os.getenv('PROJECT_ROOT'):
            config.project_root = env_root
        return config


# ============================================================================
# Event System — Observer pattern for inter-agent communication
# ============================================================================

class PipelineEvent(Enum):
    """Events broadcast through the pipeline. Agents subscribe, not poll."""
    RECOVERY_STARTED = 'recovery_started'
    ANCHOR_DETECTED = 'anchor_detected'
    INTENT_RECONSTRUCTED = 'intent_reconstructed'
    PLAN_CREATED = 'plan_created'
    IMPLEMENTATION_COMPLETE = 'implementation_complete'
    BUILD_VALIDATED = 'build_validated'
    AUDIT_COMPLETE = 'audit_complete'
    SUPERVISOR_VERDICT = 'supervisor_verdict'
    REVISION_REQUIRED = 'revision_required'
    PIPELINE_COMPLETE = 'pipeline_complete'
    PIPELINE_FAILED = 'pipeline_failed'


class EventBus:
    """
    Event-driven communication between pipeline stages.
    Agents subscribe to events they care about — no polling, no coupling.
    """
    
    def __init__(self):
        self._subscribers: dict[PipelineEvent, list[Callable]] = {}
        self._event_log: list[dict] = []
    
    def subscribe(self, event: PipelineEvent, callback: Callable) -> None:
        """Register a callback for a specific event type."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
        logger.debug(f"Subscriber registered for {event.value}")
    
    def unsubscribe(self, event: PipelineEvent, callback: Callable) -> None:
        """Remove a callback subscription. Prevents memory leaks."""
        if event in self._subscribers:
            self._subscribers[event] = [
                cb for cb in self._subscribers[event] if cb != callback
            ]
    
    async def broadcast(self, event: PipelineEvent, data: Any = None) -> None:
        """Broadcast an event to all subscribers. Non-blocking dispatch."""
        entry = {
            'event': event.value,
            'timestamp': datetime.now().isoformat(),
            'data_summary': str(data)[:200] if data else None,
        }
        self._event_log.append(entry)
        logger.info(f"[EVENT] {event.value}")
        
        if event in self._subscribers:
            for callback in self._subscribers[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Subscriber error on {event.value}: {e}")
    
    def get_event_log(self) -> list[dict]:
        """Return full event history for debugging and audit trail."""
        return self._event_log.copy()


# ============================================================================
# Agent Interfaces — Abstractions for swappable agent implementations
# ============================================================================

class AgentRole(Enum):
    WORKER = 'claude_worker'
    AUDITOR = 'chatgpt_auditor'
    SUPERVISOR = 'supervisor'


@dataclass
class AgentResponse:
    """Standardized response from any agent in the pipeline."""
    agent: str
    role: AgentRole
    success: bool
    content: dict
    token_usage: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    error: Optional[str] = None


class BaseAgent:
    """
    Interface for pipeline agents. Concrete implementations handle
    API-specific details while the orchestrator works with this contract.
    """
    
    def __init__(self, config: PipelineConfig, event_bus: EventBus, role: AgentRole):
        self.config = config
        self.event_bus = event_bus
        self.role = role
        self.logger = logging.getLogger(role.value)
    
    async def execute(self, prompt: str, context: dict) -> AgentResponse:
        """Execute the agent's task. Subclasses implement the API call."""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def build_system_prompt(self, context: dict) -> str:
        """Build the system prompt for this agent's role."""
        raise NotImplementedError("Subclasses must implement build_system_prompt()")


# ============================================================================
# Claude Worker Agent — Performs the actual session recovery and code completion
# ============================================================================

class ClaudeWorkerAgent(BaseAgent):
    """
    The workhorse agent. Uses Claude API to detect interruptions,
    reconstruct intent, plan completion, and implement code.
    """
    
    def __init__(self, config: PipelineConfig, event_bus: EventBus):
        super().__init__(config, event_bus, AgentRole.WORKER)
    
    def build_system_prompt(self, context: dict) -> str:
        """Construct the worker agent's system prompt with full project context."""
        constraints_str = '\n'.join(f'  - {c}' for c in self.config.architecture_constraints)
        
        return f"""You are a senior software engineer performing session recovery.
Your job is to find where the previous AI agent session was interrupted,
understand what was being built, complete the implementation, and ensure
it compiles with zero errors and zero warnings.

PROJECT CONTEXT:
- Root: {self.config.project_root}
- Language: {context.get('language', self.config.primary_language)}
- Architecture constraints:
{constraints_str}

CODING STANDARDS (NON-NEGOTIABLE):
- Comment-Driven Development: Write step-comments BEFORE implementation
- Comments explain WHY, never WHAT
- Event-driven communication only (no polling)
- Dependency injection (no hardcoded instantiation)
- No public mutable state
- No magic numbers/strings — use constants and config
- File headers on every source file (Developer, Date, Purpose)
- Single-line comments only (// or #), no /* */ blocks

RECOVERY PHASES:
1. Detect interruption point (scan git + code markers)
2. Reconstruct intent (read CDD comments, naming, interfaces)
3. Plan completion (break into independent steps)
4. Implement with guided comments
5. Validate build (0 errors, 0 warnings)
6. Verify behavior matches intent

When you complete implementation, output a structured report with:
- recovery_anchor: where the interruption was found
- intent_specification: what the code was supposed to do
- implementation_summary: what you implemented and why
- build_status: compilation result
- files_modified: list of all files you changed"""
    
    async def execute(self, prompt: str, context: dict) -> AgentResponse:
        """Execute the worker agent via Claude API."""
        start_time = time.time()
        
        try:
            # Dynamic import to handle optional dependency
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.config.claude_api_key)
            
            response = client.messages.create(
                model=self.config.claude_model,
                max_tokens=8192,
                system=self.build_system_prompt(context),
                messages=[{'role': 'user', 'content': prompt}],
            )
            
            content_text = ''.join(
                block.text for block in response.content if block.type == 'text'
            )
            
            elapsed = time.time() - start_time
            self.logger.info(f"Worker completed in {elapsed:.1f}s")
            
            return AgentResponse(
                agent=self.config.claude_model,
                role=self.role,
                success=True,
                content={'response': content_text},
                token_usage={
                    'input': response.usage.input_tokens,
                    'output': response.usage.output_tokens,
                },
                elapsed_seconds=elapsed,
            )
            
        except ImportError:
            self.logger.warning("anthropic package not installed — using mock mode")
            return self._mock_response(prompt, context, time.time() - start_time)
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Worker failed: {e}")
            return AgentResponse(
                agent=self.config.claude_model,
                role=self.role,
                success=False,
                content={},
                elapsed_seconds=elapsed,
                error=str(e),
            )
    
    def _mock_response(self, prompt: str, context: dict, elapsed: float) -> AgentResponse:
        """Mock response for testing without API keys."""
        return AgentResponse(
            agent='mock-claude',
            role=self.role,
            success=True,
            content={
                'response': '[MOCK] Worker would process recovery here',
                'mock': True,
            },
            elapsed_seconds=elapsed,
        )


# ============================================================================
# ChatGPT Auditor Agent — Independent code review using a different model
# ============================================================================

class ChatGPTAuditorAgent(BaseAgent):
    """
    Independent auditor using OpenAI's GPT models. Provides a second
    opinion on code quality by reviewing with different training biases.
    Cross-model review catches blind spots that single-model review misses.
    """
    
    def __init__(self, config: PipelineConfig, event_bus: EventBus):
        super().__init__(config, event_bus, AgentRole.AUDITOR)
    
    def build_system_prompt(self, context: dict) -> str:
        """Construct the auditor's system prompt focused on quality review."""
        constraints_str = '\n'.join(f'  - {c}' for c in self.config.architecture_constraints)
        
        return f"""You are a senior code auditor performing an independent quality review.
Another AI agent (Claude) has completed a session recovery — finding where
a previous coding session was interrupted and completing the implementation.

Your job is to AUDIT the completed work against strict quality standards.
You are NOT modifying code. You are reviewing and scoring.

ARCHITECTURE CONSTRAINTS TO VERIFY:
{constraints_str}

REVIEW CRITERIA (score each 0-100):

1. COMMENT_CODE_ALIGNMENT (25%):
   - Every function has step-by-step CDD comments BEFORE implementation
   - Comments explain WHY, not WHAT
   - Implementation matches what comments describe

2. ARCHITECTURE_COMPLIANCE (30%):
   - Event-driven only (no polling)
   - Dependency injection used properly
   - Single responsibility per class/module
   - Config-driven (no hardcoded values)
   - Proper access control (no public mutable state)

3. BUILD_CLEANLINESS (20%):
   - Zero compilation errors
   - Zero warnings
   - Minimal dependencies in declarations

4. DEFENSIVE_PROGRAMMING (15%):
   - Input validation at boundaries
   - Typed error handling
   - Fail-fast on invalid state
   - Cleanup of subscriptions/listeners

5. DOCUMENTATION_QUALITY (10%):
   - File headers present
   - Single-line comments only
   - Design decisions documented

OUTPUT FORMAT (JSON):
{{
  "verdict": "APPROVED | REVISION_REQUIRED | REJECTED",
  "overall_score": <number>,
  "criteria_scores": {{
    "comment_code_alignment": <number>,
    "architecture_compliance": <number>,
    "build_cleanliness": <number>,
    "defensive_programming": <number>,
    "documentation_quality": <number>
  }},
  "issues": [
    {{
      "severity": "HIGH | MEDIUM | LOW",
      "criterion": "<which criterion>",
      "file": "<file path>",
      "line": <line number or 0>,
      "description": "<what's wrong>",
      "fix": "<suggested fix>"
    }}
  ],
  "commendations": ["<things done well>"]
}}

PASS threshold: 70+ on ALL criteria (not averaged).
Any single criterion below 70 = REVISION_REQUIRED."""
    
    async def execute(self, prompt: str, context: dict) -> AgentResponse:
        """Execute the auditor agent via OpenAI API."""
        start_time = time.time()
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.config.openai_api_key)
            
            response = client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {'role': 'system', 'content': self.build_system_prompt(context)},
                    {'role': 'user', 'content': prompt},
                ],
                max_tokens=4096,
                temperature=0.1,  # Low temperature for consistent review
            )
            
            content_text = response.choices[0].message.content or ''
            elapsed = time.time() - start_time
            self.logger.info(f"Auditor completed in {elapsed:.1f}s")
            
            # Attempt to parse JSON from auditor response
            review = self._parse_review(content_text)
            
            return AgentResponse(
                agent=self.config.openai_model,
                role=self.role,
                success=True,
                content={'review': review, 'raw': content_text},
                token_usage={
                    'input': response.usage.prompt_tokens if response.usage else 0,
                    'output': response.usage.completion_tokens if response.usage else 0,
                },
                elapsed_seconds=elapsed,
            )
            
        except ImportError:
            self.logger.warning("openai package not installed — using mock mode")
            return self._mock_response(time.time() - start_time)
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Auditor failed: {e}")
            return AgentResponse(
                agent=self.config.openai_model,
                role=self.role,
                success=False,
                content={},
                elapsed_seconds=elapsed,
                error=str(e),
            )
    
    def _parse_review(self, raw: str) -> dict:
        """Extract JSON review from auditor response, handling markdown fences."""
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            self.logger.warning("Could not parse auditor JSON — returning raw text")
            return {'verdict': 'PARSE_ERROR', 'raw_response': raw}
    
    def _mock_response(self, elapsed: float) -> AgentResponse:
        """Mock response for testing."""
        return AgentResponse(
            agent='mock-gpt',
            role=self.role,
            success=True,
            content={
                'review': {
                    'verdict': 'APPROVED',
                    'overall_score': 85,
                    'criteria_scores': {
                        'comment_code_alignment': 90,
                        'architecture_compliance': 85,
                        'build_cleanliness': 100,
                        'defensive_programming': 75,
                        'documentation_quality': 80,
                    },
                    'issues': [],
                    'commendations': ['[MOCK] Review would happen here'],
                },
                'mock': True,
            },
            elapsed_seconds=elapsed,
        )


# ============================================================================
# Supervisor Agent — Final quality gate that reconciles worker + auditor
# ============================================================================

class SupervisorAgent(BaseAgent):
    """
    Final decision-maker. Reconciles the worker's self-report with the
    auditor's independent review to produce a binding verdict.
    """
    
    def __init__(self, config: PipelineConfig, event_bus: EventBus):
        super().__init__(config, event_bus, AgentRole.SUPERVISOR)
    
    def build_system_prompt(self, context: dict) -> str:
        return """You are the supervisor agent — the final quality gate.

You receive two inputs:
1. The WORKER REPORT: What the Claude agent says it did
2. The AUDITOR REVIEW: What the ChatGPT agent found during independent review

Your job:
- Compare both perspectives
- Identify any discrepancies between them
- If the auditor found HIGH severity issues, verdict MUST be REVISION_REQUIRED
- If all criteria pass 70+, verdict is APPROVED
- If any criterion below 50, verdict is REJECTED

Output a final SUPERVISOR VERDICT in JSON:
{
  "verdict": "APPROVED | REVISION_REQUIRED | REJECTED",
  "reconciliation": "<explain any discrepancies between worker and auditor>",
  "final_scores": { <reconciled scores> },
  "action_items": ["<specific things to fix if not approved>"],
  "next_steps": "<what the worker should do next>"
}"""
    
    async def execute(self, prompt: str, context: dict) -> AgentResponse:
        """Execute supervisor review via Claude API."""
        start_time = time.time()
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.config.claude_api_key)
            
            response = client.messages.create(
                model=self.config.supervisor_model,
                max_tokens=4096,
                system=self.build_system_prompt(context),
                messages=[{'role': 'user', 'content': prompt}],
            )
            
            content_text = ''.join(
                block.text for block in response.content if block.type == 'text'
            )
            elapsed = time.time() - start_time
            self.logger.info(f"Supervisor completed in {elapsed:.1f}s")
            
            return AgentResponse(
                agent=self.config.supervisor_model,
                role=self.role,
                success=True,
                content={'verdict': content_text},
                elapsed_seconds=elapsed,
            )
        except ImportError:
            return AgentResponse(
                agent='mock-supervisor', role=self.role, success=True,
                content={'verdict': '{"verdict": "APPROVED", "mock": true}'},
                elapsed_seconds=time.time() - start_time,
            )
        except Exception as e:
            return AgentResponse(
                agent=self.config.supervisor_model, role=self.role,
                success=False, content={}, error=str(e),
                elapsed_seconds=time.time() - start_time,
            )


# ============================================================================
# Pipeline Orchestrator — Coordinates the three agents through event-driven flow
# ============================================================================

class RecoveryPipeline:
    """
    Orchestrates the full session recovery pipeline:
    1. Claude Worker detects interruption + completes code
    2. ChatGPT Auditor independently reviews the work
    3. Supervisor reconciles both and renders verdict
    4. If revision needed, loop back to Worker with feedback
    
    All coordination is event-driven — agents don't poll each other.
    """
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.event_bus = EventBus()
        self.worker = ClaudeWorkerAgent(config, self.event_bus)
        self.auditor = ChatGPTAuditorAgent(config, self.event_bus)
        self.supervisor = SupervisorAgent(config, self.event_bus)
        self.iteration = 0
        self.max_iterations = config.max_retries
        self.results: dict[str, Any] = {}
        
        # Wire up event subscriptions
        self.event_bus.subscribe(PipelineEvent.IMPLEMENTATION_COMPLETE, self._on_implementation_complete)
        self.event_bus.subscribe(PipelineEvent.AUDIT_COMPLETE, self._on_audit_complete)
        self.event_bus.subscribe(PipelineEvent.REVISION_REQUIRED, self._on_revision_required)
    
    async def _on_implementation_complete(self, data: Any) -> None:
        """When worker finishes, automatically trigger auditor."""
        self.logger = logging.getLogger('orchestrator')
        self.logger.info("Worker complete — dispatching to auditor")
    
    async def _on_audit_complete(self, data: Any) -> None:
        """When auditor finishes, automatically trigger supervisor."""
        self.logger = logging.getLogger('orchestrator')
        self.logger.info("Audit complete — dispatching to supervisor")
    
    async def _on_revision_required(self, data: Any) -> None:
        """When supervisor requests revision, re-dispatch to worker."""
        self.logger = logging.getLogger('orchestrator')
        self.logger.info("Revision required — re-dispatching to worker")
    
    async def run(self, recovery_context: Optional[dict] = None) -> dict:
        """Execute the full pipeline. Returns final results dict."""
        context = recovery_context or {}
        logger.info("=" * 60)
        logger.info("SESSION RECOVERY PIPELINE STARTED")
        logger.info("=" * 60)
        
        await self.event_bus.broadcast(PipelineEvent.RECOVERY_STARTED, context)
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            logger.info(f"\n--- Iteration {self.iteration}/{self.max_iterations} ---")
            
            # PHASE 1-4: Worker performs recovery and implementation
            worker_prompt = self._build_worker_prompt(context)
            worker_result = await self.worker.execute(worker_prompt, context)
            
            if not worker_result.success:
                logger.error(f"Worker failed: {worker_result.error}")
                await self.event_bus.broadcast(PipelineEvent.PIPELINE_FAILED, worker_result)
                self.results['status'] = 'WORKER_FAILED'
                self.results['error'] = worker_result.error
                return self.results
            
            self.results['worker'] = asdict(worker_result)
            await self.event_bus.broadcast(PipelineEvent.IMPLEMENTATION_COMPLETE, worker_result)
            
            # PHASE 5-6: Auditor independently reviews
            auditor_prompt = self._build_auditor_prompt(worker_result, context)
            auditor_result = await self.auditor.execute(auditor_prompt, context)
            
            if not auditor_result.success:
                logger.warning(f"Auditor failed: {auditor_result.error} — continuing with worker self-review")
                auditor_result = self._create_fallback_audit()
            
            self.results['auditor'] = asdict(auditor_result)
            await self.event_bus.broadcast(PipelineEvent.AUDIT_COMPLETE, auditor_result)
            
            # PHASE 7: Supervisor reconciles
            supervisor_prompt = self._build_supervisor_prompt(worker_result, auditor_result)
            supervisor_result = await self.supervisor.execute(supervisor_prompt, context)
            
            self.results['supervisor'] = asdict(supervisor_result)
            await self.event_bus.broadcast(PipelineEvent.SUPERVISOR_VERDICT, supervisor_result)
            
            # Check verdict
            verdict = self._extract_verdict(supervisor_result)
            self.results['final_verdict'] = verdict
            
            if verdict == 'APPROVED':
                logger.info("PIPELINE COMPLETE — APPROVED")
                await self.event_bus.broadcast(PipelineEvent.PIPELINE_COMPLETE, self.results)
                self.results['status'] = 'APPROVED'
                self.results['iterations'] = self.iteration
                return self.results
            
            elif verdict == 'REJECTED':
                logger.error("PIPELINE COMPLETE — REJECTED (major rework needed)")
                self.results['status'] = 'REJECTED'
                return self.results
            
            else:
                # REVISION_REQUIRED — loop with feedback
                logger.info("Revision required — feeding back to worker")
                context['revision_feedback'] = supervisor_result.content
                context['auditor_feedback'] = auditor_result.content
                await self.event_bus.broadcast(PipelineEvent.REVISION_REQUIRED, context)
        
        logger.warning(f"Max iterations ({self.max_iterations}) reached without approval")
        self.results['status'] = 'MAX_ITERATIONS_REACHED'
        return self.results
    
    def _build_worker_prompt(self, context: dict) -> str:
        """Construct the prompt for the worker agent."""
        base = f"""Perform session recovery on the project at: {self.config.project_root}

Execute all 7 phases of the recovery pipeline:
1. Detect the interruption point (scan git + code markers)
2. Reconstruct intent from CDD comments and naming
3. Plan the completion as discrete, independent steps
4. Implement with CDD step-comments BEFORE code
5. Validate build (0 errors, 0 warnings)
6. Verify behavior matches reconstructed intent
7. Prepare report for supervisor review"""
        
        if feedback := context.get('revision_feedback'):
            base += f"\n\nPREVIOUS REVIEW FEEDBACK (address these issues):\n{json.dumps(feedback, indent=2)}"
        
        if audit := context.get('auditor_feedback'):
            base += f"\n\nAUDITOR FEEDBACK:\n{json.dumps(audit, indent=2)}"
        
        return base
    
    def _build_auditor_prompt(self, worker_result: AgentResponse, context: dict) -> str:
        """Construct the prompt for the auditor agent."""
        return f"""Review the following code completion work performed by an AI agent.
Score each criterion 0-100, identify issues, and render a verdict.

WORKER REPORT:
{json.dumps(worker_result.content, indent=2)}

PROJECT CONSTRAINTS:
{json.dumps(self.config.architecture_constraints, indent=2)}

Provide your review in the specified JSON format."""
    
    def _build_supervisor_prompt(self, worker: AgentResponse, auditor: AgentResponse) -> str:
        """Construct the prompt for the supervisor agent."""
        return f"""Reconcile these two reviews and render a final verdict.

WORKER SELF-REPORT:
{json.dumps(worker.content, indent=2)}

AUDITOR INDEPENDENT REVIEW:
{json.dumps(auditor.content, indent=2)}

Identify discrepancies. Any HIGH severity issue from the auditor = REVISION_REQUIRED.
Output your final verdict in the specified JSON format."""
    
    def _extract_verdict(self, supervisor_result: AgentResponse) -> str:
        """Parse the supervisor's verdict from their response."""
        content = supervisor_result.content.get('verdict', '')
        if isinstance(content, dict):
            return content.get('verdict', 'REVISION_REQUIRED')
        
        # Try to extract from text
        for v in ['APPROVED', 'REJECTED', 'REVISION_REQUIRED']:
            if v in str(content).upper():
                return v
        
        return 'REVISION_REQUIRED'  # Default to requiring revision when uncertain
    
    def _create_fallback_audit(self) -> AgentResponse:
        """Fallback if auditor is unavailable — uses conservative defaults."""
        return AgentResponse(
            agent='fallback',
            role=AgentRole.AUDITOR,
            success=True,
            content={
                'review': {
                    'verdict': 'REVISION_REQUIRED',
                    'overall_score': 60,
                    'note': 'Auditor unavailable — conservative fallback applied',
                    'issues': [{
                        'severity': 'MEDIUM',
                        'description': 'Independent audit could not be performed',
                        'fix': 'Manual review recommended'
                    }]
                }
            },
        )
    
    def get_pipeline_report(self) -> str:
        """Generate a human-readable pipeline execution report."""
        events = self.event_bus.get_event_log()
        
        report = f"""
================================================================================
              MULTI-AGENT PIPELINE EXECUTION REPORT
================================================================================
Timestamp:    {datetime.now().isoformat()}
Iterations:   {self.iteration}/{self.max_iterations}
Final Status: {self.results.get('status', 'IN_PROGRESS')}
Verdict:      {self.results.get('final_verdict', 'PENDING')}

AGENT TIMELINE
==============
"""
        for event in events:
            report += f"  {event['timestamp']}  {event['event']}\n"
        
        report += f"""
TOKEN USAGE
===========
"""
        for agent_key in ['worker', 'auditor', 'supervisor']:
            if agent_data := self.results.get(agent_key):
                usage = agent_data.get('token_usage', {})
                elapsed = agent_data.get('elapsed_seconds', 0)
                report += f"  {agent_key:12s}: {usage.get('input', 0):>6d} in / {usage.get('output', 0):>6d} out ({elapsed:.1f}s)\n"
        
        return report


# ============================================================================
# CLI Entry Point
# ============================================================================

async def main():
    """CLI entry point for running the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Multi-Agent Session Recovery Pipeline'
    )
    parser.add_argument('--project-root', '-p', default='.', help='Project root directory')
    parser.add_argument('--config', '-c', default=None, help='Path to pipeline config JSON')
    parser.add_argument('--language', '-l', default='auto', help='Primary language (auto-detect if not specified)')
    parser.add_argument('--output', '-o', default=None, help='Output report file path')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode (no API calls)')
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = PipelineConfig.from_file(args.config)
    else:
        config = PipelineConfig.from_env()
    
    config.project_root = os.path.abspath(args.project_root)
    config.primary_language = args.language
    
    if args.mock:
        config.claude_api_key = ''
        config.openai_api_key = ''
    
    # Run pipeline
    pipeline = RecoveryPipeline(config)
    results = await pipeline.run({'language': args.language})
    
    # Output report
    report = pipeline.get_pipeline_report()
    print(report)
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2, default=str))
        logger.info(f"Full results written to {args.output}")
    
    # Exit code based on verdict
    status = results.get('status', 'FAILED')
    sys.exit(0 if status == 'APPROVED' else 1)


if __name__ == '__main__':
    asyncio.run(main())
