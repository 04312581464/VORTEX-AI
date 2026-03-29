from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents import CodingAgent, FileAgent, SecurityAgent, StudyAgent, SystemAgent
from behavior_engine import BehaviorEngine
from focus_mode import focus_manager
from dream_module import DreamModule, DreamRequest
from memory_graph import MemoryGraph
from vortex_activity_log import ActivityLogger
from stealth_automation import StealthAutomation
from emotional_intelligence import get_emotional_engine
from perception_system import get_perception_system
from voice_error_system import get_voice_error_system


@dataclass
class VortexRuntime:
    session: Any
    log: ActivityLogger
    memory_graph: MemoryGraph
    config: Dict[str, Any]
    emotional_engine: Any
    perception_system: Any
    voice_error_system: Any


class VortexAgentsController:
    """
    Central multi-agent controller:
    - intent detection (rule-based)
    - agent selection
    - directive/response merging (into one injected developer/system message)
    - starts passive + stealth tasks when session is available
    """

    def __init__(self, *, base_dir: Path):
        self.base_dir = base_dir
        self.log = ActivityLogger(base_dir / "json" / "vortex_activity_log.jsonl")
        self.memory_graph = MemoryGraph(base_dir / "json" / "memory_graph.json")
        self.behavior = BehaviorEngine(base_dir / "json" / "user_profile.json")
        self.dream = DreamModule()
        
        # Initialize core systems
        self.emotional_engine = get_emotional_engine()
        self.perception_system = get_perception_system()
        self.voice_error_system = get_voice_error_system()
        
        self.config: Dict[str, Any] = {
            "system_check_interval_s": 20,
            "ram_spike_pct": 90,
            "battery_drain_warn_pct_per_min": 2.0,
            "security_check_interval_s": 15,
        }

        self.coding_agent = CodingAgent()
        self.study_agent = StudyAgent()
        self.system_agent = SystemAgent()
        self.security_agent = SecurityAgent()
        self.file_agent = FileAgent()

        self._agents = [
            self.security_agent,
            self.system_agent,
            self.file_agent,
            self.coding_agent,
            self.study_agent,
        ]

        self._runtime: Optional[VortexRuntime] = None
        self._passive_tasks: List[asyncio.Task] = []
        self._stealth: Optional[StealthAutomation] = None

    def attach_session(self, session: Any) -> None:
        runtime = VortexRuntime(
            session=session, 
            log=self.log, 
            memory_graph=self.memory_graph, 
            config=self.config,
            emotional_engine=self.emotional_engine,
            perception_system=self.perception_system,
            voice_error_system=self.voice_error_system
        )
        self._runtime = runtime
        focus_manager.set_session(session)
        self.log.log("system", "VORTEX session attached with core systems", {})

    async def start_background(self) -> None:
        """
        Start Passive Mode + Stealth Automation Mode + Core Systems.
        Called once after session attach.
        """
        if not self._runtime or not self._runtime.session:
            return

        # Focus mode doomscroll interrupts
        await focus_manager.start()

        # Start perception system monitoring
        if hasattr(self.perception_system, 'start_monitoring'):
            asyncio.create_task(self.perception_system.start_monitoring())
            self.log.log("system", "Perception system monitoring started", {})

        # Enable voice error system
        if hasattr(self.voice_error_system, 'enable'):
            self.voice_error_system.enable()
            self.log.log("system", "Voice error system enabled", {})

        # Stealth automation
        if self._stealth is None:
            self._stealth = StealthAutomation(self.file_agent, self.log, enabled=True)
        await self._stealth.start()

        # Passive monitors from agents
        if not self._passive_tasks:
            for a in (self.security_agent, self.system_agent):
                self._passive_tasks.append(asyncio.create_task(a.start_passive(self._runtime)))

        self.log.log("system", "All background systems started", {})

    def show_what_i_did_today(self) -> str:
        events = self.log.get_today()
        if not events:
            return "No actions logged today."
        lines = ["Here’s what I did today (transparency log):"]
        for e in events[-30:]:
            lines.append(f"- [{e.kind}] {e.message}")
        return "\n".join(lines)

    def detect_intents(self, text: str) -> List[str]:
        t = (text or "").lower()
        intents: List[str] = []
        if any(k in t for k in ["show what you did", "what did you do today", "today log", "transparency log"]):
            intents.append("show_log")
        if any(k in t for k in ["focus mode", "doomscroll", "scrolling too much"]):
            intents.append("focus_mode")
        if any(k in t for k in ["memory graph", "relationships", "link this", "connect this"]):
            intents.append("memory_graph")
        if any(k in t for k in ["dream", "dream module", "future sight", "futuresight", "outcome simulator", "concept vision", "worldforge", "visual experience", "visualize"]):
            intents.append("dream")
        if any(k in t for k in ["organize", "downloads", "cleanup", "clear junk", "rename"]):
            intents.append("file_ops")
        if any(k in t for k in ["usb", "virus", "scan", "suspicious", "security", "malware"]):
            intents.append("security")
        if any(k in t for k in ["ram", "cpu", "battery", "slow", "performance"]):
            intents.append("system")
        if any(k in t for k in ["study", "learn", "physics", "math", "exam", "revision", "topic"]):
            intents.append("study")
        if any(k in t for k in ["code", "bug", "error", "traceback", "refactor", "python"]):
            intents.append("coding")
        # Emotional intelligence intents
        if any(k in t for k in ["feeling", "emotion", "mood", "sad", "happy", "angry", "frustrated", "stressed"]):
            intents.append("emotional")
        # Perception system intents
        if any(k in t for k in ["what am i doing", "activity", "focus", "distracted", "procrastinating"]):
            intents.append("perception")
        # Voice system intents
        if any(k in t for k in ["speak", "voice", "tell me", "announce", "read aloud"]):
            intents.append("voice")
        return intents

    def observe_user_message(self, text: str) -> None:
        intents = self.detect_intents(text)
        self.behavior.observe(text, intents=intents)
        self.log.log("behavior", "Observed user message", {"intents": intents, "summary": self.behavior.summary()})

    def select_agents(self, text: str) -> List[Any]:
        scored = [(a.match(text, None), a) for a in self._agents]
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [a for s, a in scored if s > 0]
        return selected[:3]  # keep it small and fast

    def merged_directives(self, text: str) -> str:
        intents = self.detect_intents(text)
        # Self-improving behavior engine update
        self.behavior.observe(text, intents=intents)
        selected = self.select_agents(text)
        results = [a.run(text, None) for a in selected]

        lines: List[str] = []
        lines.append("Multi-Agent Controller:")
        lines.append(f"- Behavior profile: {self.behavior.summary()}")
        if intents:
            lines.append(f"- Detected intents: {', '.join(intents)}")
        if selected:
            lines.append(f"- Selected agents: {', '.join(a.name for a in selected)}")

        # Add emotional intelligence context
        if self._runtime and hasattr(self._runtime.emotional_engine, 'get_current_state'):
            try:
                emotional_state = self._runtime.emotional_engine.get_current_state()
                lines.append(f"- Emotional context: {emotional_state}")
            except Exception:
                pass

        # Add perception system context
        if self._runtime and hasattr(self._runtime.perception_system, 'get_current_activity'):
            try:
                activity = self._runtime.perception_system.get_current_activity()
                lines.append(f"- Current activity: {activity}")
            except Exception:
                pass

        for r in results:
            if r.directives:
                lines.append(f"\n[{r.agent}] directives:")
                for d in r.directives:
                    lines.append(f"- {d}")
            if r.tool_hints:
                lines.append(f"[{r.agent}] tool hints:")
                for h in r.tool_hints:
                    lines.append(f"- {h}")

        # Built-in behaviors
        if "show_log" in intents:
            lines.append("\nController action: respond with today's transparency log.")

        if "dream" in intents:
            mode = self.dream.classify(text)
            ctx = self._dream_context_summary()
            prompt = self.dream.build_prompt(
                DreamRequest(user_input=text, mode=mode, context_summary=ctx),
                user_profile=self.behavior.profile.__dict__,
            )
            lines.append("\nDream Module:")
            lines.append(f"- Classified mode: {mode}")
            lines.append("- If user asks for a visual, call generate_ai_image with the generated prompt.")
            lines.append(f"- Generated prompt: {prompt}")

        return "\n".join(lines)

    def _dream_context_summary(self) -> str:
        # Pull small hints from memory graph + behavior topics
        topics = sorted(self.behavior.profile.topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        tstr = ", ".join(f"{k}" for k, _ in topics) if topics else ""
        return f"top_topics={tstr}"

