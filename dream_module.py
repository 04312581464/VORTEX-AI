from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional


DreamMode = Literal["A", "B", "C", "D"]


@dataclass
class DreamRequest:
    user_input: str
    mode: DreamMode
    context_summary: str = ""


class DreamModule:
    """
    Dream Module MVP:
    - classify input into A/B/C/D
    - build a strong, personalized image prompt
    - (MVP) outputs images via existing image tool; video deferred
    """

    def classify(self, text: str) -> DreamMode:
        t = (text or "").lower()
        if any(k in t for k in ["if i", "what if", "alternate", "world", "worldforge", "explore"]):
            return "D"
        if any(k in t for k in ["consequence", "outcome", "if i do", "decision", "choice", "pros", "cons"]):
            return "B"
        if any(k in t for k in ["explain", "visualize", "concept", "diagram", "physics", "math", "how does"]):
            return "C"
        return "A"

    def build_prompt(self, req: DreamRequest, user_profile: Optional[Dict[str, Any]] = None) -> str:
        base_style = (
            "cinematic, high detail, realistic lighting, sharp focus, 35mm, "
            "clean composition, no text, no watermark"
        )
        tone = (user_profile or {}).get("tone", "neutral")
        tone_hint = {
            "formal": "clean, minimal, professional",
            "casual": "vibrant, energetic, modern",
            "terse": "minimal, direct, simple",
            "neutral": "balanced, clear, engaging",
        }.get(tone, "balanced, clear, engaging")

        if req.mode == "A":
            # FutureSight
            return (
                f"FutureSight visualization of the user's goal: {req.user_input}. "
                f"Show a plausible near-future scene with progress markers, mood of confidence, "
                f"{tone_hint}. Context: {req.context_summary}. Style: {base_style}."
            )
        if req.mode == "B":
            # Outcome Simulator
            return (
                f"Outcome Simulator diptych (two-panel scene, left vs right). "
                f"Decision: {req.user_input}. Left panel: best outcome. Right panel: worst outcome. "
                f"Clear emotional contrast, same character, same environment. "
                f"{tone_hint}. Context: {req.context_summary}. Style: {base_style}."
            )
        if req.mode == "C":
            # Concept Vision
            return (
                f"Concept Vision: visualize the concept: {req.user_input}. "
                f"Use a clean educational visual metaphor, layered components, but no text. "
                f"{tone_hint}. Context: {req.context_summary}. Style: {base_style}."
            )
        # D WorldForge
        return (
            f"WorldForge scene: {req.user_input}. "
            f"Create a simple exploratory 'what-if' environment with consistent world rules, "
            f"one focal subject, and room for imagination. {tone_hint}. "
            f"Context: {req.context_summary}. Style: {base_style}."
        )

