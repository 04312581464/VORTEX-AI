from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class FocusSettings:
    enabled: bool = True
    doomscroll_threshold_s: int = 18 * 60
    idle_reset_s: int = 90
    check_interval_s: int = 10


class FocusModeManager:
    """
    Doomscroll detection based on scroll events (tool-driven).
    """

    def __init__(self, settings: Optional[FocusSettings] = None):
        self.settings = settings or FocusSettings()
        self._session = None
        self._task: Optional[asyncio.Task] = None
        self._scroll_start_ts: Optional[float] = None
        self._last_scroll_ts: Optional[float] = None
        self._prompted_at_scroll_start: Optional[float] = None

    def set_session(self, session) -> None:
        self._session = session

    def enable(self, enabled: bool) -> None:
        self.settings.enabled = enabled

    def record_scroll(self) -> None:
        now = time.time()
        if self._scroll_start_ts is None:
            self._scroll_start_ts = now
            self._prompted_at_scroll_start = None
        self._last_scroll_ts = now

    def reset_scroll_session(self) -> None:
        self._scroll_start_ts = None
        self._last_scroll_ts = None
        self._prompted_at_scroll_start = None

    def _current_scroll_duration_s(self) -> int:
        if self._scroll_start_ts is None:
            return 0
        now = time.time()
        if self._last_scroll_ts and (now - self._last_scroll_ts) > self.settings.idle_reset_s:
            self._scroll_start_ts = None
            self._last_scroll_ts = None
            self._prompted_at_scroll_start = None
            return 0
        return int(now - self._scroll_start_ts)

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self.settings.check_interval_s)
            if not self.settings.enabled or not self._session:
                continue
            dur = self._current_scroll_duration_s()
            if dur <= 0:
                continue
            if dur >= self.settings.doomscroll_threshold_s:
                if self._prompted_at_scroll_start == self._scroll_start_ts:
                    continue
                self._prompted_at_scroll_start = self._scroll_start_ts
                mins = dur // 60
                await self._session.generate_reply(
                    instructions=(
                        f"Focus mode: You’ve been scrolling {mins} mins. Continue or stop?\n"
                        "Reply with: CONTINUE (to keep going) or STOP (to pause/lock distractions)."
                    )
                )


focus_manager = FocusModeManager()

