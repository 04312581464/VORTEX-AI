"""
Behavior Engine Tools for Vortex AI
Provides tools for behavior analysis and learning
"""

from __future__ import annotations
from pathlib import Path
from livekit.agents import function_tool
from behavior_engine import BehaviorEngine

# Global behavior engine instance
_behavior_engine = None

def get_behavior_engine() -> BehaviorEngine:
    """Get global behavior engine instance"""
    global _behavior_engine
    if _behavior_engine is None:
        _behavior_engine = BehaviorEngine(Path("json/behavior_profile.json"))
    return _behavior_engine

@function_tool()
async def analyze_behavior_patterns() -> str:
    """
    Analyze learned behavior patterns and user preferences
    
    Returns:
        str: Summary of learned behavior patterns including tone, priorities, habits, and topics
    """
    try:
        engine = get_behavior_engine()
        summary = engine.summary()
        
        profile = engine.profile
        
        result = "🧠 **Behavior Analysis Report**\n\n"
        
        # Tone analysis
        result += f"🎭 **Communication Tone**: {profile.tone.capitalize()}\n"
        
        # Top priorities
        priorities = sorted(profile.priorities.items(), key=lambda x: x[1], reverse=True)[:5]
        if priorities:
            result += "\n🎯 **Top Priorities**:\n"
            for priority, weight in priorities:
                result += f"  • {priority}: {weight:.2f}\n"
        else:
            result += "\n🎯 **Top Priorities**: None detected yet\n"
        
        # Habits
        habits = profile.habits
        result += f"\n📊 **Interaction Stats**:\n"
        result += f"  • Total messages analyzed: {habits.get('messages_seen', 0)}\n"
        
        # Time patterns
        time_buckets = habits.get('time_buckets', {})
        if time_buckets:
            result += "\n⏰ **Activity Patterns**:\n"
            for bucket, count in sorted(time_buckets.items()):
                result += f"  • {bucket}: {count} interactions\n"
        
        # Topic interests
        topics = profile.topic_counts
        if topics:
            result += "\n📚 **Topic Interests**:\n"
            for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]:
                result += f"  • {topic}: {count} mentions\n"
        else:
            result += "\n📚 **Topic Interests**: None detected yet\n"
        
        result += f"\n📅 **Last Updated**: {profile.updated_at}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to analyze behavior patterns: {str(e)}"

@function_tool()
async def observe_current_behavior(text: str, intents: str = "") -> str:
    """
    Observe and learn from current user interaction
    
    Args:
        text: The user's message/text to analyze
        intents: Comma-separated list of detected intents (e.g., "coding,help,question")
        
    Returns:
        str: Confirmation of behavior observation and learning
    """
    try:
        engine = get_behavior_engine()
        
        # Parse intents
        intent_list = []
        if intents:
            intent_list = [intent.strip() for intent in intents.split(',') if intent.strip()]
        
        # Observe the behavior
        engine.observe(text, intent_list)
        
        # Get updated summary
        profile = engine.profile
        
        result = "🧠 **Behavior Observed & Learned**\n\n"
        result += f"📝 **Text Length**: {len(text)} characters\n"
        
        if intent_list:
            result += f"🎯 **Detected Intents**: {', '.join(intent_list)}\n"
        
        result += f"🎭 **Updated Tone**: {profile.tone.capitalize()}\n"
        result += f"📊 **Total Messages**: {profile.habits.get('messages_seen', 0)}\n"
        
        # Show top priority if updated
        priorities = sorted(profile.priorities.items(), key=lambda x: x[1], reverse=True)[:1]
        if priorities:
            result += f"🏆 **Top Priority**: {priorities[0][0]} ({priorities[0][1]:.2f})\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to observe behavior: {str(e)}"

@function_tool()
async def reset_behavior_profile() -> str:
    """
    Reset the behavior learning profile
    
    Returns:
        str: Confirmation of profile reset
    """
    try:
        engine = get_behavior_engine()
        
        # Reset to fresh profile
        from Modules.behavior_engine import UserProfile
        engine.profile = UserProfile()
        engine._save(engine.profile)
        
        return "🧠 **Behavior Profile Reset**\n\n✅ All learning data has been cleared.\n🔄 Vortex will start learning fresh from new interactions."
        
    except Exception as e:
        return f"❌ Failed to reset behavior profile: {str(e)}"

@function_tool()
async def get_behavior_recommendations() -> str:
    """
    Get personalized recommendations based on learned behavior patterns
    
    Returns:
        str: Personalized recommendations for user
    """
    try:
        engine = get_behavior_engine()
        profile = engine.profile
        
        result = "🤖 **Personalized Recommendations**\n\n"
        
        # Tone-based recommendations
        if profile.tone == "formal":
            result += "🎭 **Communication Style**: You prefer formal interactions\n"
            result += "💡 Vortex will maintain professional tone with you\n\n"
        elif profile.tone == "casual":
            result += "🎭 **Communication Style**: You prefer casual interactions\n"
            result += "💡 Vortex can be more relaxed and friendly with you\n\n"
        elif profile.tone == "terse":
            result += "🎭 **Communication Style**: You prefer concise interactions\n"
            result += "💡 Vortex will keep responses brief and to the point\n\n"
        
        # Priority-based recommendations
        priorities = sorted(profile.priorities.items(), key=lambda x: x[1], reverse=True)[:3]
        if priorities:
            result += "🎯 **Based on Your Priorities**:\n"
            for priority, weight in priorities:
                if priority == "coding":
                    result += f"  • Focus on code assistance and debugging (weight: {weight:.2f})\n"
                elif priority == "study":
                    result += f"  • Provide study help and explanations (weight: {weight:.2f})\n"
                elif priority == "help":
                    result += f"  • Offer proactive assistance (weight: {weight:.2f})\n"
                else:
                    result += f"  • Support {priority} related tasks (weight: {weight:.2f})\n"
            result += "\n"
        
        # Topic-based recommendations
        topics = profile.topic_counts
        if topics:
            top_topic = max(topics.items(), key=lambda x: x[1])
            result += f"📚 **Interest Area**: {top_topic[0].title()} (mentioned {top_topic[1]} times)\n"
            result += f"💡 Vortex can provide more {top_topic[0]}-related content\n\n"
        
        # Time-based recommendations
        time_buckets = profile.habits.get('time_buckets', {})
        if time_buckets:
            most_active = max(time_buckets.items(), key=lambda x: x[1])
            result += f"⏰ **Most Active Time**: {most_active[0]} ({most_active[1]} interactions)\n"
            result += f"💡 Vortex can be more available during {most_active[0]}\n\n"
        
        if not priorities and not topics:
            result += "🔄 **Continue Learning**: Vortex is still learning your preferences\n"
            result += "💡 The more you interact, the better recommendations become\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to generate recommendations: {str(e)}"
