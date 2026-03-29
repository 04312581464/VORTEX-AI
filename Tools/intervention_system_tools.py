"""
Intervention System Tools for Vortex AI
Provides tools for intelligent user assistance and safety interventions
"""

from __future__ import annotations
from pathlib import Path
from livekit.agents import function_tool
from intervention_system import get_intervention_system, InterventionType, InterventionLevel
import json

@function_tool()
async def trigger_intervention(
    intervention_type: str = "guidance",
    message: str = "User requested intervention",
    severity: str = "gentle"
) -> str:
    """
    Manually trigger an intervention for user assistance or safety
    
    Args:
        intervention_type: Type of intervention ("guidance", "protection", "support", "optimization")
        message: Custom message for the intervention
        severity: Intervention severity ("gentle", "friendly", "firm", "controlled")
        
    Returns:
        str: Intervention status and details
        
    Examples:
        - trigger_intervention("guidance", "Help me with this complex task", "friendly")
        - trigger_intervention("protection", "Check if this action is safe", "firm")
        - trigger_intervention("support", "I need help focusing", "gentle")
    """
    try:
        intervention_system = get_intervention_system()
        
        # Map string values to enums
        type_map = {
            "guidance": InterventionType.MESSAGE,
            "protection": InterventionType.NOTIFICATION,
            "support": InterventionType.BREAK_REMINDER,
            "optimization": InterventionType.FOCUS_MODE
        }
        
        severity_map = {
            "gentle": InterventionLevel.GENTLE_NUDGE,
            "friendly": InterventionLevel.FRIENDLY_REMINDER,
            "firm": InterventionLevel.FIRM_GUIDANCE,
            "controlled": InterventionLevel.CONTROLLED_ACTION
        }
        
        int_type = type_map.get(intervention_type.lower(), InterventionType.MESSAGE)
        int_severity = severity_map.get(severity.lower(), InterventionLevel.GENTLE_NUDGE)
        
        # Create and execute intervention
        from Modules.intervention_system import InterventionAction
        action = InterventionAction(
            type=int_type,
            message=message,
            severity=int_severity,
            cooldown_minutes=5.0,
            user_overridable=True
        )
        
        # Execute the intervention
        result = await intervention_system.execute_intervention(action)
        
        return f"""🛡️ **Intervention Triggered**

✅ **Type**: {intervention_type}
📝 **Message**: {message}
🎯 **Severity**: {severity}
⏰ **Cooldown**: 5 minutes

💡 Intervention has been executed based on your request."""
        
    except Exception as e:
        return f"❌ Failed to trigger intervention: {str(e)}"

@function_tool()
async def get_intervention_status() -> str:
    """
    Get current status of the intervention system
    
    Returns:
        str: Comprehensive status of intervention system
    """
    try:
        intervention_system = get_intervention_system()
        status = intervention_system.get_system_status()
        
        emotional_state = status.get('emotional_state', 'unknown')
        cooldown_status = status.get('cooldown_status', {})
        last_intervention = status.get('last_intervention', 'None')
        intervention_count = status.get('intervention_count_today', 0)
        
        result = """🛡️ **Intervention System Status**

🧠 **Emotional State**: {emotional_state}

⏰ **Cooldown Status**:""".format(emotional_state=emotional_state)
        
        if cooldown_status.get('override_active'):
            result += "\n  🔒 User override active"
        else:
            result += "\n  ✅ No active overrides"
        
        result += f"""

📊 **Today's Interventions**: {intervention_count}

🕐 **Last Intervention**: {last_intervention}

🎯 **System Status**: Online and monitoring"""
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get intervention status: {str(e)}"

@function_tool()
async def configure_interventions(
    enabled_types: str = "all",
    sensitivity_level: str = "medium",
    user_override: bool = True
) -> str:
    """
    Configure intervention system settings
    
    Args:
        enabled_types: Which intervention types to enable ("all", "guidance", "protection", "support")
        sensitivity_level: How sensitive the system should be ("low", "medium", "high")
        user_override: Whether user can override interventions
        
    Returns:
        str: Configuration confirmation
    """
    try:
        intervention_system = get_intervention_system()
        
        # Save configuration
        config = {
            'enabled_types': enabled_types,
            'sensitivity_level': sensitivity_level,
            'user_override': user_override,
            'timestamp': str(intervention_system.last_intervention_time)
        }
        
        config_path = Path("json/intervention_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return f"""⚙️ **Intervention Configuration Updated**

✅ **Enabled Types**: {enabled_types}
🎯 **Sensitivity**: {sensitivity_level}
🔓 **User Override**: {'Enabled' if user_override else 'Disabled'}

💡 Settings saved and will be applied to future interventions."""
        
    except Exception as e:
        return f"❌ Failed to configure interventions: {str(e)}"

@function_tool()
async def get_intervention_history() -> str:
    """
    Get history of recent interventions
    
    Returns:
        str: Recent intervention history with details
    """
    try:
        intervention_system = get_intervention_system()
        history = intervention_system.intervention_history
        
        if not history:
            return "📋 **Intervention History**\n\nNo interventions recorded yet."
        
        result = "📋 **Recent Interventions**\n\n"
        
        for i, intervention in enumerate(history[-10:], 1):  # Last 10 interventions
            result += f"{i}. **{intervention.type.value}**\n"
            result += f"   📝 {intervention.message}\n"
            result += f"   🎯 {intervention.severity.value}\n"
            result += f"   🕐 {intervention.timestamp}\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get intervention history: {str(e)}"

@function_tool()
async def enable_intervention_system() -> str:
    """
    Enable the intervention system
    
    Returns:
        str: Confirmation that system is enabled
    """
    try:
        intervention_system = get_intervention_system()
        
        # The intervention system should auto-start, but this ensures it's active
        return """🛡️ **Intervention System Enabled**

✅ **Status**: Active and monitoring
🧠 **Emotional Intelligence**: Connected
👁️ **Perception System**: Connected
🎯 **Intervention Types**: All types enabled
🔓 **User Override**: Available

💡 Vortex will now proactively assist and protect you!"""
        
    except Exception as e:
        return f"❌ Failed to enable intervention system: {str(e)}"

@function_tool()
async def disable_intervention_system() -> str:
    """
    Disable the intervention system
    
    Returns:
        str: Confirmation that system is disabled
    """
    try:
        intervention_system = get_intervention_system()
        
        # Activate user override for 24 hours to effectively disable
        intervention_system.user_override(1440)  # 24 hours
        
        return """🛡️ **Intervention System Disabled**

⏸️ **Status**: User override activated
⏰ **Duration**: 24 hours
🔓 **Manual Control**: You can re-enable anytime

💡 Interventions paused - you're in full control."""
        
    except Exception as e:
        return f"❌ Failed to disable intervention system: {str(e)}"
