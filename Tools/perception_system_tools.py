"""
Perception System Tools for Vortex AI
Provides tools for monitoring user activity and focus patterns
"""

from __future__ import annotations
from pathlib import Path
from livekit.agents import function_tool
from perception_system import get_perception_system, ActivityType, FocusLevel
import json

@function_tool()
async def start_perception_monitoring() -> str:
    """
    Start or check status of perception monitoring for user activity and behavior patterns
    
    Note: Perception monitoring automatically starts when Vortex AI initializes.
    This function can be used to verify it's running or restart if needed.
    
    Returns:
        str: Current status of perception monitoring
    """
    try:
        perception = get_perception_system()
        
        # Get current status
        status = perception.monitor_behavior()
        
        return """👁️ **Perception Monitoring Status**

✅ **Automatically Started** when Vortex AI launched

🔍 **Active Features**:
  • Real-time window detection
  • Activity classification (study, work, entertainment, etc.)
  • Focus level assessment
  • Behavior pattern learning
  • Procrastination tracking

📊 **Current Status**:
  • Real-time monitoring active
  • Pattern learning enabled
  • Focus detection active

💡 Perception monitoring runs continuously in background to provide personalized insights!"""
        
    except Exception as e:
        return f"❌ Failed to check perception monitoring: {str(e)}"

@function_tool()
async def get_current_activity_status() -> str:
    """
    Get current user activity and focus status
    
    Returns:
        str: Current activity, focus level, and session information
    """
    try:
        perception = get_perception_system()
        
        # Get current perception summary
        status = perception.monitor_behavior()
        
        result = "👁️ **Current Activity Status**\n\n"
        
        # Current activity
        current_activity = status.get('current_activity', 'unknown')
        current_focus = status.get('current_focus', 'unknown')
        current_window = status.get('current_window', 'Unknown')
        
        result += f"🖥️ **Active Window**: {current_window}\n"
        result += f"📋 **Activity Type**: {current_activity.replace('_', ' ').title()}\n"
        result += f"🎯 **Focus Level**: {current_focus.replace('_', ' ').title()}\n\n"
        
        # Session info
        if status.get('session_duration'):
            duration = status['session_duration']
            result += f"⏱️ **Session Duration**: {duration:.1f} minutes\n"
        
        # Study streak
        patterns = status.get('patterns', {})
        study_streak = patterns.get('study_streak', 0)
        if study_streak > 0:
            result += f"🔥 **Study Streak**: {study_streak} sessions\n"
        
        # Procrastination score
        proc_score = patterns.get('procrastination_score', 0)
        result += f"📊 **Procrastination Score**: {proc_score:.2f}/1.0\n"
        
        # Productive hours
        productive_hours = patterns.get('productive_hours', set())
        if productive_hours:
            result += f"⏰ **Productive Hours**: {sorted(productive_hours)}\n"
        
        # Recent activity summary
        recent_windows = patterns.get('recent_windows', [])
        if recent_windows:
            result += f"\n📈 **Recent Activities**:\n"
            for window in recent_windows[-3:]:  # Last 3 activities
                result += f"  • {window.get('title', 'Unknown')} ({window.get('activity_type', 'unknown')})\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get activity status: {str(e)}"

@function_tool()
async def analyze_focus_patterns() -> str:
    """
    Analyze user's focus patterns and productivity trends
    
    Returns:
        str: Detailed focus analysis and productivity insights
    """
    try:
        perception = get_perception_system()
        
        # Get perception data
        status = perception.monitor_behavior()
        patterns = status.get('patterns', {})
        
        result = "🎯 **Focus Pattern Analysis**\n\n"
        
        # Focus statistics
        avg_focus_duration = patterns.get('average_focus_duration', 0)
        result += f"📊 **Average Focus Duration**: {avg_focus_duration:.1f} minutes\n"
        
        # Total study time today
        total_study = patterns.get('total_study_today', 0)
        result += f"📚 **Total Study Time Today**: {total_study:.1f} minutes\n"
        
        # Study streak
        study_streak = patterns.get('study_streak', 0)
        result += f"🔥 **Current Study Streak**: {study_streak} sessions\n"
        
        # Procrastination analysis
        proc_score = patterns.get('procrastination_score', 0)
        if proc_score < 0.3:
            proc_status = "Low - Great focus!"
        elif proc_score < 0.6:
            proc_status = "Moderate - Room for improvement"
        else:
            proc_status = "High - Consider focus strategies"
        
        result += f"📈 **Procrastination Level**: {proc_score:.2f} - {proc_status}\n\n"
        
        # Productive hours analysis
        productive_hours = patterns.get('productive_hours', set())
        if productive_hours:
            result += "⏰ **Most Productive Hours**:\n"
            for hour in sorted(productive_hours):
                result += f"  • {hour:02d}:00 - {hour+1:02d}:00\n"
            result += "\n"
        
        # Distraction triggers
        distraction_triggers = patterns.get('distraction_triggers', set())
        if distraction_triggers:
            result += "🚫 **Common Distraction Triggers**:\n"
            for trigger in sorted(distraction_triggers)[:5]:
                result += f"  • {trigger}\n"
            result += "\n"
        
        # Recommendations based on patterns
        result += "💡 **Personalized Recommendations**:\n"
        
        if avg_focus_duration < 15:
            result += "  • Try the Pomodoro technique (25 min focus, 5 min break)\n"
        
        if proc_score > 0.5:
            result += "  • Consider using website blockers during study time\n"
            result += "  • Set specific study goals to maintain motivation\n"
        
        if study_streak < 2:
            result += "  • Build consistent study habits with shorter sessions\n"
        
        if len(productive_hours) < 3:
            result += "  • Experiment with different study times to find your peak hours\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to analyze focus patterns: {str(e)}"

@function_tool()
async def get_productivity_report() -> str:
    """
    Generate a comprehensive productivity report
    
    Returns:
        str: Detailed productivity analysis and recommendations
    """
    try:
        perception = get_perception_system()
        
        # Get current status
        status = perception.monitor_behavior()
        patterns = status.get('patterns', {})
        
        result = "📈 **Productivity Report**\n\n"
        
        # Overall productivity score
        study_time = patterns.get('total_study_today', 0)
        proc_score = patterns.get('procrastination_score', 0)
        
        # Calculate productivity score (0-100)
        base_score = 50
        study_bonus = min(study_time / 120 * 30, 30)  # Up to 30 points for 2+ hours study
        proc_penalty = proc_score * 25  # Up to 25 points penalty for procrastination
        productivity_score = max(0, min(100, base_score + study_bonus - proc_penalty))
        
        result += f"🏆 **Productivity Score**: {productivity_score:.0f}/100\n\n"
        
        # Breakdown
        result += "📊 **Score Breakdown**:\n"
        result += f"  • Base score: 50\n"
        result += f"  • Study time bonus: +{study_bonus:.0f} ({study_time:.1f} min studied)\n"
        result += f"  • Procrastination penalty: -{proc_penalty:.0f} ({proc_score:.2f} score)\n\n"
        
        # Performance rating
        if productivity_score >= 80:
            rating = "Excellent! 🌟"
        elif productivity_score >= 60:
            rating = "Good job! 👍"
        elif productivity_score >= 40:
            rating = "Room for improvement 📈"
        else:
            rating = "Needs attention ⚠️"
        
        result += f"🎯 **Performance**: {rating}\n\n"
        
        # Activity breakdown
        recent_windows = patterns.get('recent_windows', [])
        if recent_windows:
            activity_counts = {}
            for window in recent_windows:
                activity = window.get('activity_type', 'unknown')
                activity_counts[activity] = activity_counts.get(activity, 0) + 1
            
            result += "📋 **Activity Breakdown**:\n"
            for activity, count in sorted(activity_counts.items(), key=lambda x: x[1], reverse=True):
                result += f"  • {activity.replace('_', ' ').title()}: {count} times\n"
            result += "\n"
        
        # Recommendations
        result += "🚀 **Improvement Suggestions**:\n"
        
        if productivity_score < 60:
            result += "  • Set specific daily study goals\n"
            result += "  • Use time-blocking for better focus\n"
            result += "  • Minimize distractions during study time\n"
        elif productivity_score < 80:
            result += "  • Maintain consistent study schedule\n"
            result += "  • Take regular breaks to avoid burnout\n"
            result += "  • Track your progress to stay motivated\n"
        else:
            result += "  • Keep up the great work!\n"
            result += "  • Consider helping others with your productive habits\n"
            result += "  • Set challenging new goals\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to generate productivity report: {str(e)}"

@function_tool()
async def reset_perception_data() -> str:
    """
    Reset all perception and activity tracking data
    
    Returns:
        str: Confirmation of data reset
    """
    try:
        perception = get_perception_system()
        
        # Clear the data file
        if perception.data_path.exists():
            perception.data_path.unlink()
        
        # Reload with fresh data
        perception._load_patterns()
        
        return "🗑️ **Perception Data Reset**\n\n✅ All activity tracking data has been cleared.\n🔄 Vortex will start learning your patterns fresh from new interactions."
        
    except Exception as e:
        return f"❌ Failed to reset perception data: {str(e)}"
