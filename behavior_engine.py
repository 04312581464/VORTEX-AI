from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


@dataclass
class UserProfile:
    updated_at: str = field(default_factory=_now_iso)
    # Learned preferences
    tone: str = "neutral"  # neutral | formal | casual | terse
    priorities: Dict[str, float] = field(default_factory=dict)  # intent -> weight
    habits: Dict[str, Any] = field(default_factory=dict)  # lightweight counters / timings
    topic_counts: Dict[str, int] = field(default_factory=dict)


class BehaviorEngine:
    """
    Lightweight, self-improving behavior engine (MVP):
    - Learns tone (heuristic)
    - Learns priorities (intent frequency/recency)
    - Learns habits (message frequency + time-of-day buckets)
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.profile = self._load()

    def _load(self) -> UserProfile:
        if not self.path.exists():
            p = UserProfile()
            self._save(p)
            return p
        try:
            obj = json.loads(self.path.read_text(encoding="utf-8"))
            return UserProfile(
                updated_at=str(obj.get("updated_at") or _now_iso()),
                tone=str(obj.get("tone") or "neutral"),
                priorities=dict(obj.get("priorities") or {}),
                habits=dict(obj.get("habits") or {}),
                topic_counts=dict(obj.get("topic_counts") or {}),
            )
        except Exception:
            p = UserProfile()
            self._save(p)
            return p

    def _save(self, p: Optional[UserProfile] = None) -> None:
        p = p or self.profile
        p.updated_at = _now_iso()
        self.path.write_text(json.dumps(p.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

    def observe(self, text: str, intents: Optional[List[str]] = None) -> None:
        t = (text or "").strip()
        if not t:
            return

        self._update_habits()
        self._update_tone(t)
        self._update_topics(t)
        if intents:
            self._update_priorities(intents)
        self._save()

    def _update_habits(self) -> None:
        h = self.profile.habits
        h["messages_seen"] = int(h.get("messages_seen", 0)) + 1
        # time-of-day bucket (local)
        hour = datetime.now().astimezone().hour
        bucket = (
            "late_night"
            if hour < 6
            else "morning"
            if hour < 12
            else "afternoon"
            if hour < 18
            else "evening"
        )
        by_bucket = dict(h.get("time_buckets") or {})
        by_bucket[bucket] = int(by_bucket.get(bucket, 0)) + 1
        h["time_buckets"] = by_bucket

    def _update_tone(self, t: str) -> None:
        # Heuristic: terse if very short, formal if "please"/complete sentences, casual if slang/emphasis.
        length = len(t)
        formal_markers = sum(1 for w in ["please", "kindly", "could you", "would you"] if w in t.lower())
        casual_markers = sum(1 for w in ["bro", "lol", "pls", "ya", "wanna"] if w in t.lower())
        exclaim = t.count("!") >= 2

        score_formal = formal_markers * 0.4 + (0.2 if re.search(r"[.;:]\s*$", t) else 0.0)
        score_casual = casual_markers * 0.4 + (0.2 if exclaim else 0.0)
        score_terse = 0.6 if length <= 35 else 0.0

        if score_formal >= max(score_casual, score_terse) and score_formal >= 0.4:
            self.profile.tone = "formal"
        elif score_casual >= max(score_formal, score_terse) and score_casual >= 0.4:
            self.profile.tone = "casual"
        elif score_terse >= max(score_formal, score_casual) and score_terse >= 0.6:
            self.profile.tone = "terse"
        else:
            self.profile.tone = "neutral"

    def _update_topics(self, t: str) -> None:
        keywords = {
            "coding": ["code", "bug", "error", "python", "js", "typescript"],
            "study": ["study", "physics", "math", "learn", "exam"],
            "system": ["ram", "cpu", "battery", "performance", "slow"],
            "security": ["virus", "malware", "scan", "usb", "suspicious"],
            "focus": ["focus", "doomscroll", "scroll"],
            "dream": ["dream", "visualize", "imagine", "future", "simulate", "worldforge"],
        }
        low = t.lower()
        for topic, ks in keywords.items():
            if any(k in low for k in ks):
                self.profile.topic_counts[topic] = int(self.profile.topic_counts.get(topic, 0)) + 1

    def _update_priorities(self, intents: List[str]) -> None:
        p = self.profile.priorities
        # decay existing slightly
        for k in list(p.keys()):
            p[k] = float(p.get(k, 0.0)) * 0.97
        for it in intents:
            p[it] = _clamp(float(p.get(it, 0.0)) + 0.08, 0.0, 1.0)

    def summary(self) -> str:
        # Top 3 priorities
        pr = sorted(self.profile.priorities.items(), key=lambda x: x[1], reverse=True)[:3]
        pr_s = ", ".join(f"{k}({v:.2f})" for k, v in pr) if pr else "none"
        return f"tone={self.profile.tone}; priorities={pr_s}"

