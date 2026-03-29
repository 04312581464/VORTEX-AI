from __future__ import annotations

import asyncio
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional


def _home() -> Path:
    return Path(os.path.expanduser("~"))


def _downloads() -> Path:
    return _home() / "Downloads"


def _temp_dirs() -> list[Path]:
    out: list[Path] = []
    for env in ("TEMP", "TMP"):
        v = os.environ.get(env)
        if v:
            out.append(Path(v))
    out.append(_home() / "AppData" / "Local" / "Temp")
    # de-dup while preserving order
    seen = set()
    dedup = []
    for p in out:
        sp = str(p).lower()
        if sp in seen:
            continue
        seen.add(sp)
        dedup.append(p)
    return dedup


class StealthAutomation:
    """
    Conservative background automation:
    - organize Downloads into subfolders by extension (no deletion)
    - clear temp junk older than N days (best-effort, safe locations only)
    - maintain transparency via ActivityLogger
    """

    def __init__(self, file_agent, log, *, enabled: bool = True):
        self.file_agent = file_agent
        self.log = log
        self.enabled = enabled
        self._task: Optional[asyncio.Task] = None
        self._last_app_update_day: Optional[str] = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())

    async def _loop(self) -> None:
        # run once quickly on start, then periodically
        await self._run_once()
        while True:
            await asyncio.sleep(60 * 30)  # every 30 minutes
            await self._run_once()

    async def _run_once(self) -> None:
        if not self.enabled:
            return
        try:
            stats = await asyncio.to_thread(self.file_agent.organize_downloads, _downloads(), False)
            if self.log:
                self.log.log("stealth", "Organized Downloads", stats)
        except Exception as e:
            if self.log:
                self.log.log("stealth", "Downloads organize failed", {"error": str(e)})

        try:
            removed = await asyncio.to_thread(self._clear_temp, days=3)
            if self.log:
                self.log.log("stealth", "Cleared temp junk", {"removed": removed})
        except Exception as e:
            if self.log:
                self.log.log("stealth", "Temp cleanup failed", {"error": str(e)})

        # Best-effort app updates (Windows winget). Runs at most once per day.
        try:
            day = datetime.now().strftime("%Y-%m-%d")
            if self._last_app_update_day != day:
                self._last_app_update_day = day
                out = await self._winget_upgrade_all()
                if self.log:
                    self.log.log("stealth", "Attempted app updates", {"result": out[:4000]})
        except Exception as e:
            if self.log:
                self.log.log("stealth", "App update attempt failed", {"error": str(e)})

    async def _winget_upgrade_all(self) -> str:
        # Avoid hard failure if winget isn't installed.
        import subprocess

        cmd = [
            "winget",
            "upgrade",
            "--all",
            "--silent",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            return "winget not found; skipped."

        stdout, stderr = await proc.communicate()
        out = (stdout or b"").decode(errors="ignore").strip()
        err = (stderr or b"").decode(errors="ignore").strip()
        if err and not out:
            return f"winget stderr: {err}"
        if err:
            return f"{out}\n\n(stderr)\n{err}"
        return out or "winget finished (no output)."

    def _clear_temp(self, *, days: int = 3) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        for d in _temp_dirs():
            if not d.exists() or not d.is_dir():
                continue
            removed += self._remove_old_files(d, cutoff)
        return removed

    def _remove_old_files(self, root: Path, cutoff: datetime) -> int:
        removed = 0
        for p in self._iter_files(root):
            try:
                st = p.stat()
                mtime = datetime.fromtimestamp(st.st_mtime)
                if mtime > cutoff:
                    continue
                try:
                    p.unlink()
                    removed += 1
                except IsADirectoryError:
                    continue
                except PermissionError:
                    continue
            except Exception:
                continue

        # best-effort: remove empty directories
        for dp in sorted([x for x in root.rglob("*") if x.is_dir()], key=lambda x: len(str(x)), reverse=True):
            try:
                if not any(dp.iterdir()):
                    dp.rmdir()
            except Exception:
                pass
        return removed

    def _iter_files(self, root: Path) -> Iterable[Path]:
        try:
            yield from (p for p in root.rglob("*") if p.is_file())
        except Exception:
            return

