"""
Vortex Emotional Intelligence Tools
Tools for emotional AI companion integration
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import json
from datetime import datetime, timezone

from livekit.agents import function_tool
from emotional_intelligence import EmotionalEngine


@function_tool()
async def get_emotional_status() -> str:
    """
    Get current emotional status of Vortex
    
    Returns comprehensive emotional state including:
    - Current emotion and emotional levels
    - Perception summary (what user is doing)
    - Intervention status and cooldowns
    - Session statistics
    
    Use this to understand Vortex's current emotional state
    """
    try:
        vortex = EmotionalEngine()
        status = vortex.get_system_status()
        
        # Format status for user-friendly display
        emotional_state = status.get('emotional_state', {})
        perception_summary = status.get('perception_summary', {})
        
        response_parts = []
        
        # Emotional state
        emotion = emotional_state.get('emotion', 'neutral')
        care = emotional_state.get('care', 0.5)
        frustration = emotional_state.get('frustration', 0.0)
        patience = emotional_state.get('patience', 0.5)
        
        response_parts.append(f"🧠 **Emotional State:** {emotion.title()}")
        response_parts.append(f"💚 **Care Level:** {care:.1%}")
        response_parts.append(f"😤 **Frustration:** {frustration:.1%}")
        response_parts.append(f"⏳ **Patience:** {patience:.1%}")
        
        # Current activity
        activity = perception_summary.get('current_activity', 'unknown')
        is_distracted = perception_summary.get('is_distracted', False)
        is_studying = perception_summary.get('is_studying', False)
        
        response_parts.append(f"👁️ **Current Activity:** {activity}")
        
        if is_distracted:
            response_parts.append("⚠️ **Status:** I notice you might be distracted")
        elif is_studying:
            response_parts.append("📚 **Status:** Great! I see you're studying")
        
        # Study stats
        study_streak = perception_summary.get('study_streak', 0)
        total_study = perception_summary.get('total_study_today', 0.0)
        
        if study_streak > 0:
            response_parts.append(f"🔥 **Study Streak:** {study_streak} sessions")
        
        if total_study > 0:
            response_parts.append(f"⏰ **Study Today:** {total_study:.1f} minutes")
        
        # Intervention status
        intervention_status = status.get('intervention_status', {})
        cooldown_status = intervention_status.get('cooldown_status', {})
        
        if cooldown_status.get('override_active'):
            remaining = cooldown_status.get('override_remaining_minutes', 0)
            response_parts.append(f"🛡️ **User Override:** Active ({remaining:.1f} minutes remaining)")
        elif cooldown_status.get('global_cooldown_remaining', 0) > 0:
            remaining = cooldown_status.get('global_cooldown_remaining', 0)
            response_parts.append(f"⏸️ **Cooldown:** {remaining:.1f} minutes remaining")
        
        # Session stats
        session_duration = status.get('session_duration_minutes', 0)
        intervention_count = status.get('intervention_count_today', 0)
        
        response_parts.append(f"⏱️ **Session Duration:** {session_duration:.1f} minutes")
        response_parts.append(f"🎯 **Interventions Today:** {intervention_count}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error getting emotional status: {str(e)}"


@function_tool()
async def activate_user_override(duration_minutes: int = 30) -> str:
    """
    Activate user override to pause all interventions
    
    Args:
        duration_minutes: How long to pause interventions (default: 30 minutes)
    
    Use this when you want Vortex to stop intervening temporarily.
    This is useful when you need a break from guidance or want to work without interruptions.
    
    Examples:
    - activate_user_override() - Pause for 30 minutes
    - activate_user_override(60) - Pause for 1 hour
    - activate_user_override(15) - Pause for 15 minutes
    """
    try:
        vortex = EmotionalEngine()
        vortex.user_override(duration_minutes)
        
        return f"🛡️ **User Override Activated**\n\nInterventions paused for {duration_minutes} minutes.\n\nVortex will continue to monitor but won't intervene during this time. You can still ask for help or guidance manually.\n\nTo end override early, ask me to 'deactivate override'."
        
    except Exception as e:
        return f"❌ Error activating user override: {str(e)}"


@function_tool()
async def deactivate_user_override() -> str:
    """
    Deactivate user override and resume normal interventions
    
    Use this to end the user override early and allow Vortex to resume
    normal emotional guidance and interventions.
    """
    try:
        from intervention_system import InterventionSystem
        intervention_system = InterventionSystem()
        intervention_system.cooldown_manager.deactivate_user_override()
        
        return "🛡️ **User Override Deactivated**\n\nVortex has resumed normal emotional monitoring and interventions.\n\nI'll continue to care for your progress and provide guidance when needed."
        
    except Exception as e:
        return f"❌ Error deactivating user override: {str(e)}"


@function_tool()
async def manual_emotional_intervention(message: str, severity: str = "gentle") -> str:
    """
    Trigger a manual emotional intervention
    
    Args:
        message: The intervention message to deliver
        severity: Intervention intensity - "gentle", "reminder", "firm", or "action"
    
    Use this when you want Vortex to provide emotional guidance or intervention
    on demand, rather than waiting for automatic detection.
    
    Severity levels:
    - "gentle": Soft reminder, caring tone
    - "reminder": Friendly but clear reminder
    - "firm": Direct guidance, serious tone
    - "action": Strong intervention with potential actions
    
    Examples:
    - manual_emotional_intervention("Remember to take breaks", "gentle")
    - manual_emotional_intervention("Time to focus on your studies", "firm")
    - manual_emotional_intervention("Let's get back on track", "action")
    """
    try:
        vortex = get_emotional_vortex()
        response = vortex.manual_intervention(message, severity)
        
        severity_emoji = {
            "gentle": "💚",
            "reminder": "💛",
            "firm": "🧡",
            "action": "❤️"
        }
        
        emoji = severity_emoji.get(severity, "💚")
        
        return f"{emoji} **Manual Intervention ({severity.title()})**\n\n{response}"
        
    except Exception as e:
        return f"❌ Error triggering manual intervention: {str(e)}"


@function_tool()
async def get_emotional_summary() -> str:
    """
    Get a human-readable summary of Vortex's emotional state
    
    This provides a conversational summary of how Vortex is feeling
    and what she's observing about your current activity.
    """
    try:
        vortex = get_emotional_vortex()
        summary = vortex.get_emotional_summary()
        
        return f"🧠 **Vortex's Emotional Summary**\n\n{summary}"
        
    except Exception as e:
        return f"❌ Error getting emotional summary: {str(e)}"


@function_tool()
async def update_emotional_config(config_updates: Dict[str, Any]) -> str:
    """
    Update emotional intelligence configuration
    
    Args:
        config_updates: Dictionary of configuration changes
    
    Use this to customize Vortex's emotional behavior:
    - monitoring_interval: How often to check (seconds)
    - intervention_enabled: Enable/disable interventions
    - auto_intervene: Allow automatic interventions
    - care_baseline: Base care level (0.0-1.0)
    - patience_baseline: Base patience level (0.0-1.0)
    - frustration_threshold: When to get frustrated (0.0-1.0)
    
    Example:
    update_emotional_config({
        "monitoring_interval": 60,
        "care_baseline": 0.9,
        "intervention_enabled": True
    })
    """
    try:
        vortex = get_emotional_vortex()
        vortex.update_config(config_updates)
        
        # Format changes for display
        changes = []
        for key, value in config_updates.items():
            changes.append(f"- {key}: {value}")
        
        return f"⚙️ **Emotional Configuration Updated**\n\nChanges made:\n" + "\n".join(changes) + "\n\nConfiguration saved and applied."
        
    except Exception as e:
        return f"❌ Error updating emotional config: {str(e)}"


@function_tool()
async def get_current_focus_analysis() -> str:
    """
    Get detailed analysis of current focus and productivity
    
    Returns comprehensive analysis including:
    - Current focus level and activity
    - Recent activity patterns
    - Productivity metrics
    - Distraction analysis
    - Recommendations
    """
    try:
        vortex = get_emotional_vortex()
        status = vortex.get_system_status()
        perception = status.get('perception_summary', {})
        
        response_parts = []
        
        # Current focus
        activity = perception.get('current_activity', 'unknown')
        focus_level = perception.get('current_focus', 'unknown')
        
        response_parts.append(f"🎯 **Current Focus Analysis**")
        response_parts.append(f"📱 **Activity:** {activity}")
        response_parts.append(f"🧘 **Focus Level:** {focus_level}")
        
        # Productivity metrics
        procrastination = perception.get('procrastination_score', 0.0)
        distraction_freq = perception.get('distraction_frequency', 0.0)
        avg_focus = perception.get('avg_focus_duration', 0.0)
        
        response_parts.append(f"\n📊 **Productivity Metrics**")
        response_parts.append(f"📉 **Procrastination Score:** {procrastination:.1%}")
        response_parts.append(f"🔄 **Distraction Frequency:** {distraction_freq:.1f} per hour")
        response_parts.append(f"⏱️ **Avg Focus Duration:** {avg_focus:.1f} minutes")
        
        # Study patterns
        study_streak = perception.get('study_streak', 0)
        total_study = perception.get('total_study_today', 0.0)
        
        if study_streak > 0 or total_study > 0:
            response_parts.append(f"\n📚 **Study Patterns**")
            if study_streak > 0:
                response_parts.append(f"🔥 **Study Streak:** {study_streak} sessions")
            if total_study > 0:
                response_parts.append(f"⏰ **Study Today:** {total_study:.1f} minutes")
        
        # Recommendations
        response_parts.append(f"\n💡 **Recommendations**")
        
        if procrastination > 0.6:
            response_parts.append("⚠️ Consider using focus mode or taking a structured break")
        
        if distraction_freq > 2.0:
            response_parts.append("🎧 Try reducing distractions or using noise cancellation")
        
        if avg_focus < 15 and avg_focus > 0:
            response_parts.append("📈 Practice building longer focus sessions gradually")
        
        if study_streak > 3:
            response_parts.append("🎉 Great consistency! Consider taking a break to maintain quality")
        
        if total_study > 180:  # 3+ hours
            response_parts.append("🧘 You've been studying for a while - consider a break")
        
        if len(response_parts) == 3:  # Only headers, no recommendations
            response_parts.append("✅ Keep up the good work! Your focus patterns look healthy.")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error analyzing focus: {str(e)}"


@function_tool()
async def express_emotional_state() -> str:
    """
    Express Vortex's current emotional state conversationally
    
    This allows Vortex to express how she's feeling about your progress
    and current situation in a natural, conversational way.
    """
    try:
        vortex = get_emotional_vortex()
        emotional_state = vortex.emotional_engine.get_state_for_response()
        perception_summary = vortex.perception_system.monitor_behavior()
        
        # Generate emotional response
        response = vortex.response_generator.generate_response(
            emotional_state,
            perception_summary,
            context="emotional_expression"
        )
        
        return f"💭 **Vortex Expresses:**\n\n{response}"
        
    except Exception as e:
        return f"❌ Error expressing emotional state: {str(e)}"


@function_tool()
async def auto_detect_emotions(text: str) -> str:
    """
    Automatically detect emotions in user text and activate emotional intelligence
    
    This tool analyzes user input for emotional content and automatically
    activates Vortex's emotional intelligence system when emotions are detected.
    
    Args:
        text: User message or text to analyze for emotional content
        
    Returns:
        Detailed analysis of detected emotions and emotional intelligence activation status
    """
    try:
        vortex = EmotionalEngine()
        result = vortex.auto_activate_emotional_intelligence(text)
        
        if result['activated']:
            response = f"🧠 **Emotional Intelligence Auto-Activated!**\n\n"
            response += f"📊 **Primary Emotion Detected:** {result['primary_emotion']}\n\n"
            
            response += "**Detected Emotions:**\n"
            for emotion, score in result['detected_emotions'].items():
                if score > 0.1:
                    emoji = "🔥" if score > 0.6 else "💫" if score > 0.3 else "✨"
                    response += f"{emoji} {emotion.title()}: {score:.2f}\n"
            
            response += f"\n**Emotional State Updates Applied:**\n"
            deltas = result['applied_deltas']
            if deltas['frustration_delta'] != 0:
                response += f"😤 Frustration: {deltas['frustration_delta']:+.2f}\n"
            if deltas['care_delta'] != 0:
                response += f"💝 Care: {deltas['care_delta']:+.2f}\n"
            if deltas['patience_delta'] != 0:
                response += f"⏳ Patience: {deltas['patience_delta']:+.2f}\n"
            if deltas['concern_delta'] != 0:
                response += f"😟 Concern: {deltas['concern_delta']:+.2f}\n"
            if deltas['encouragement_delta'] != 0:
                response += f"🌟 Encouragement: {deltas['encouragement_delta']:+.2f}\n"
            
            response += f"\n**New Emotional State:** {result['new_state']['summary']}"
            
        else:
            response = f"🔍 **Emotion Analysis Complete**\n\n"
            response += f"No significant emotions detected (threshold not met).\n\n"
            
            response += "**Minor Emotions Detected:**\n"
            for emotion, score in result['detected_emotions'].items():
                if score > 0.05:
                    response += f"• {emotion.title()}: {score:.2f}\n"
            
            if not any(score > 0.05 for score in result['detected_emotions'].values()):
                response += "• No emotions detected\n"
        
        return response
        
    except Exception as e:
        return f"❌ Error in auto emotion detection: {str(e)}"


@function_tool()
async def get_emotion_detection_status() -> str:
    """
    Get current status of emotional intelligence auto-activation system
    
    Returns information about:
    - Whether emotional intelligence is auto-activated
    - Last emotion detection results
    - Current emotional state
    - Detection thresholds and patterns
    
    Use this to monitor the emotional intelligence system
    """
    try:
        vortex = EmotionalEngine()
        status = vortex.get_auto_activation_status()
        
        response = f"🧠 **Emotional Intelligence Auto-Activation Status**\n\n"
        
        if status['auto_activated']:
            response += "✅ **Status:** Auto-Activated\n\n"
            
            if status['last_detection']:
                detection = status['last_detection']
                response += f"📅 **Last Detection:** {detection['timestamp']}\n"
                response += f"🎯 **Primary Emotion:** {detection['primary_emotion']}\n"
                response += f"💬 **Original Text:** \"{detection['text']}\"\n\n"
                
                response += "**Detected Emotions in Last Analysis:**\n"
                for emotion, score in detection['detected_emotions'].items():
                    if score > 0.1:
                        emoji = "🔥" if score > 0.6 else "💫" if score > 0.3 else "✨"
                        response += f"{emoji} {emotion.title()}: {score:.2f}\n"
        else:
            response += "⏸️ **Status:** Not Auto-Activated\n\n"
            response += "Emotional intelligence will activate when emotion-rich text is detected.\n\n"
        
        response += f"**Current Emotional State:** {status['current_state']['summary']}\n"
        response += f"**Current Emotion:** {status['current_state']['emotion']}\n"
        response += f"**Intervention Level:** {status['current_state']['intervention_level']}\n\n"
        
        response += "**Detection Thresholds:**\n"
        response += "• Strong emotion: ≥ 0.4 (auto-activates)\n"
        response += "• Moderate emotion: ≥ 0.2 (considered in mixed emotions)\n"
        response += "• Mixed emotions: 2+ moderate emotions (auto-activates)\n\n"
        
        response += "**Monitored Emotions:**\n"
        response += "• Frustration (anger, annoyance, problems)\n"
        response += "• Sadness (unhappy, disappointed, failure)\n"
        response += "• Happiness (joy, love, excitement)\n"
        response += "• Anxiety (worry, stress, fear)\n"
        response += "• Care & Concern (help, support, gratitude)"
        
        return response
        
    except Exception as e:
        return f"❌ Error getting emotion detection status: {str(e)}"


@function_tool()
async def reset_emotional_auto_activation() -> str:
    """
    Reset the emotional intelligence auto-activation system
    
    This tool resets the auto-activation state, allowing the system
    to start fresh with new emotion detections. Use this when you
    want to clear the current emotional context.
    
    Returns:
        Confirmation of reset and current system status
    """
    try:
        vortex = EmotionalEngine()
        vortex.reset_auto_activation()
        
        response = f"🔄 **Emotional Auto-Activation Reset**\n\n"
        response += "✅ Auto-activation state has been reset.\n"
        response += "🧹 Emotional detection history cleared.\n"
        response += "🆕 System ready for new emotion detections.\n\n"
        
        # Get current status after reset
        current_state = vortex.get_state_for_response()
        response += f"**Current Emotional State:** {current_state['summary']}\n"
        response += f"**Current Emotion:** {current_state['emotion']}\n"
        response += f"**Intervention Level:** {current_state['intervention_level']}"
        
        return response
        
    except Exception as e:
        return f"❌ Error resetting emotional auto-activation: {str(e)}"
