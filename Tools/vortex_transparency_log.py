from __future__ import annotations

from livekit.agents import function_tool


# This is set by agent.py at runtime
VORTEX_CONTROLLER = None


def set_controller(controller) -> None:
    global VORTEX_CONTROLLER
    VORTEX_CONTROLLER = controller


@function_tool()
async def show_what_you_did_today() -> str:
    """
    Shows VORTEX's transparency log for today (Stealth/Passive actions).
    """
    if VORTEX_CONTROLLER is None:
        return "Transparency log is not available yet (controller not initialized)."
    return VORTEX_CONTROLLER.show_what_i_did_today()

