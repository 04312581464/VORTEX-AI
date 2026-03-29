"""
Vortex Voice Error Tools
Tools for voice-based error reporting and system status
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import json

from livekit.agents import function_tool
from voice_error_system import (
    get_voice_error_system, 
    speak_error, 
    speak_info, 
    speak_warning, 
    speak_critical,
    speak_immediately,
    enable_voice_errors,
    disable_voice_errors,
    get_voice_status,
    ErrorSeverity
)


@function_tool()
async def speak_error_message(message: str, severity: str = "error") -> str:
    """
    Speak an error message with voice
    
    Args:
        message: The error message to speak
        severity: Error severity - "info", "warning", "error", or "critical"
    
    Use this to have Vortex speak errors instead of just logging them.
    
    Examples:
    - speak_error_message("Could not connect to internet", "warning")
    - speak_error_message("File not found", "error")
    - speak_error_message("System crash detected", "critical")
    """
    try:
        severity_map = {
            "info": ErrorSeverity.INFO,
            "warning": ErrorSeverity.WARNING,
            "error": ErrorSeverity.ERROR,
            "critical": ErrorSeverity.CRITICAL
        }
        
        error_severity = severity_map.get(severity.lower(), ErrorSeverity.ERROR)
        
        voice_system = get_voice_error_system()
        voice_system.speak_error(message, error_severity)
        
        return f"🗣️ Speaking {severity} message: {message}"
        
    except Exception as e:
        return f"❌ Could not speak error: {str(e)}"


@function_tool()
async def speak_info_message(message: str) -> str:
    """
    Speak an informational message
    
    Args:
        message: The informational message to speak
    
    Use this for general announcements and status updates.
    
    Examples:
    - speak_info_message("Vortex is now monitoring your activity")
    - speak_info_message("Study session started")
    - speak_info_message("Focus mode activated")
    """
    try:
        speak_info(message)
        return f"🗣️ Speaking info: {message}"
        
    except Exception as e:
        return f"❌ Could not speak info: {str(e)}"


@function_tool()
async def speak_warning_message(message: str) -> str:
    """
    Speak a warning message
    
    Args:
        message: The warning message to speak
    
    Use this for non-critical issues that need attention.
    
    Examples:
    - speak_warning_message("Battery is running low")
    - speak_warning_message("High CPU usage detected")
    - speak_warning_message("Storage space almost full")
    """
    try:
        speak_warning(message)
        return f"🗣️ Speaking warning: {message}"
        
    except Exception as e:
        return f"❌ Could not speak warning: {str(e)}"


@function_tool()
async def speak_critical_message(message: str) -> str:
    """
    Speak a critical error message immediately
    
    Args:
        message: The critical error message to speak
    
    Use this for serious system issues that require immediate attention.
    
    Examples:
    - speak_critical_message("System overheating detected")
    - speak_critical_message("Security breach detected")
    - speak_critical_message("Hardware failure detected")
    """
    try:
        speak_critical(message)
        return f"🗣️ Speaking critical: {message}"
        
    except Exception as e:
        return f"❌ Could not speak critical: {str(e)}"


@function_tool()
async def speak_immediate_message(message: str, severity: str = "info") -> str:
    """
    Speak a message immediately, bypassing the queue
    
    Args:
        message: The message to speak immediately
        severity: Error severity - "info", "warning", "error", or "critical"
    
    Use this for urgent messages that need to be spoken right away.
    
    Examples:
    - speak_immediate_message("Emergency shutdown initiated", "critical")
    - speak_immediate_message("User override activated", "info")
    - speak_immediate_message("Focus mode ending", "warning")
    """
    try:
        severity_map = {
            "info": ErrorSeverity.INFO,
            "warning": ErrorSeverity.WARNING,
            "error": ErrorSeverity.ERROR,
            "critical": ErrorSeverity.CRITICAL
        }
        
        error_severity = severity_map.get(severity.lower(), ErrorSeverity.INFO)
        
        voice_system = get_voice_error_system()
        voice_system.speak_immediately(message, error_severity)
        
        return f"🗣️ Speaking immediately: {message}"
        
    except Exception as e:
        return f"❌ Could not speak immediately: {str(e)}"


@function_tool()
async def enable_voice_reporting() -> str:
    """
    Enable voice error reporting
    
    Use this to turn on voice-based error reporting.
    Vortex will start speaking errors and important information.
    
    Returns:
        Confirmation message
    """
    try:
        enable_voice_errors()
        return "🗣️ Voice error reporting enabled. Vortex will now speak errors and important information."
        
    except Exception as e:
        return f"❌ Could not enable voice reporting: {str(e)}"


@function_tool()
async def disable_voice_reporting() -> str:
    """
    Disable voice error reporting
    
    Use this to turn off voice-based error reporting.
    Vortex will stop speaking errors.
    
    Returns:
        Confirmation message
    """
    try:
        disable_voice_errors()
        return "🔇 Voice error reporting disabled. Vortex will no longer speak errors."
        
    except Exception as e:
        return f"❌ Could not disable voice reporting: {str(e)}"


@function_tool()
async def get_voice_system_status() -> str:
    """
    Get current voice system status
    
    Returns detailed information about the voice error system including:
    - Whether voice reporting is enabled
    - Whether TTS is available
    - Current speaking status
    - Queue size
    - Voice settings
    
    Returns:
        Formatted status report
    """
    try:
        status = get_voice_status()
        
        status_lines = [
            "🗣️ **Voice System Status**",
            f"📢 **Enabled**: {'Yes' if status['enabled'] else 'No'}",
            f"🔊 **Available**: {'Yes' if status['available'] else 'No'}",
            f"🎤 **Speaking**: {'Yes' if status['speaking'] else 'No'}",
            f"📋 **Queue Size**: {status['queue_size']} messages",
            f"⚡ **Voice Rate**: {status['voice_rate']} words per minute",
            f"🔊 **Volume**: {status['voice_volume']*100:.0f}%"
        ]
        
        if not status['available']:
            status_lines.append("⚠️ **Note**: Text-to-speech engine not available. Install pyttsx3 for voice functionality.")
        
        return "\n".join(status_lines)
        
    except Exception as e:
        return f"❌ Could not get voice status: {str(e)}"


@function_tool()
async def set_voice_settings(rate: Optional[int] = None, volume: Optional[float] = None) -> str:
    """
    Adjust voice settings
    
    Args:
        rate: Speaking rate in words per minute (50-300)
        volume: Volume level (0.0-1.0)
    
    Use this to customize Vortex's voice characteristics.
    
    Examples:
    - set_voice_settings(rate=200) - Faster speaking
    - set_voice_settings(volume=0.9) - Louder volume
    - set_voice_settings(rate=100, volume=0.7) - Slower and quieter
    
    Returns:
        Confirmation of settings applied
    """
    try:
        voice_system = get_voice_error_system()
        changes = []
        
        if rate is not None:
            voice_system.set_voice_rate(rate)
            changes.append(f"rate: {rate} wpm")
        
        if volume is not None:
            voice_system.set_voice_volume(volume)
            changes.append(f"volume: {volume*100:.0f}%")
        
        if changes:
            return f"🗣️ Voice settings updated: {', '.join(changes)}"
        else:
            return "🗣️ No voice settings specified. Use rate and/or volume parameters."
        
    except Exception as e:
        return f"❌ Could not update voice settings: {str(e)}"


@function_tool()
async def clear_voice_queue() -> str:
    """
    Clear all pending voice messages
    
    Use this to clear the voice message queue.
    All pending messages will be removed.
    
    Returns:
        Confirmation message
    """
    try:
        voice_system = get_voice_error_system()
        queue_size = voice_system.message_queue.qsize()
        voice_system.clear_queue()
        
        return f"🗣️ Cleared {queue_size} pending voice messages from queue."
        
    except Exception as e:
        return f"❌ Could not clear voice queue: {str(e)}"


@function_tool()
async def test_voice_system() -> str:
    """
    Test the voice system with a sample message
    
    Use this to verify that voice reporting is working correctly.
    Vortex will speak a test message.
    
    Returns:
        Test result message
    """
    try:
        test_message = "Voice system test successful. Vortex can now speak errors and information."
        
        voice_system = get_voice_error_system()
        
        if not voice_system.is_available():
            return "❌ Voice system not available. Install pyttsx3 for voice functionality."
        
        voice_system.speak_immediately(test_message, ErrorSeverity.INFO)
        
        return f"🗣️ Voice test initiated. Vortex should say: '{test_message}'"
        
    except Exception as e:
        return f"❌ Voice test failed: {str(e)}"


@function_tool()
async def speak_emotional_state() -> str:
    """
    Speak Vortex's current emotional state
    
    Use this to have Vortex express how she's feeling about your progress.
    
    Returns:
        Confirmation message
    """
    try:
        from emotional_vortex import get_emotional_vortex
        vortex = get_emotional_vortex()
        emotional_summary = vortex.get_emotional_summary()
        
        speak_info(emotional_summary)
        
        return f"🗣️ Speaking emotional state: {emotional_summary}"
        
    except Exception as e:
        return f"❌ Could not speak emotional state: {str(e)}"


@function_tool()
async def speak_system_alert(alert_type: str, details: str) -> str:
    """
    Speak a system alert with appropriate severity
    
    Args:
        alert_type: Type of alert ("info", "warning", "error", "critical")
        details: Alert details to speak
    
    Use this for system-wide announcements and alerts.
    
    Examples:
    - speak_system_alert("warning", "High memory usage detected")
    - speak_system_alert("info", "User override activated")
    - speak_system_alert("critical", "System overheating")
    
    Returns:
        Confirmation message
    """
    try:
        return speak_error_message(details, alert_type)
        
    except Exception as e:
        return f"❌ Could not speak system alert: {str(e)}"
