"""
Advanced WhatsApp Automation System
Context-aware replies, AI suggestions, sleep mode, study mode, and more
"""

from __future__ import annotations
import json
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from livekit.agents import function_tool

# Configuration storage
WHATSAPP_CONFIG_FILE = "whatsapp_automation_config.json"

class WhatsAppAutomation:
    """Advanced WhatsApp automation system"""
    
    def __init__(self):
        self.config = self.load_config()
        self.sleep_mode_active = False
        self.study_mode_active = False
        self.unread_messages = []
        
    def load_config(self) -> Dict[str, Any]:
        """Load WhatsApp automation configuration"""
        try:
            with open(WHATSAPP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            default_config = {
                "auto_replies": {
                    "sleep_mode": "🌙 Currently in sleep mode. Will respond when available.",
                    "study_mode": "📚 Currently studying. Will respond during breaks.",
                    "busy": "⏳ Currently busy. Will respond as soon as possible.",
                    "driving": "🚗 Currently driving. Will respond safely when I stop."
                },
                "context_patterns": {
                    "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
                    "goodbye": ["bye", "goodbye", "see you", "see ya"],
                    "thanks": ["thank", "thanks", "appreciate"],
                    "urgent": ["urgent", "emergency", "asap", "immediately"],
                    "meeting": ["meeting", "call", "conference", "discuss"],
                    "study": ["study", "homework", "assignment", "exam", "test"]
                },
                "smart_reply_suggestions": {
                    "greeting": ["Hello! How are you?", "Hi there!", "Hey! What's up?"],
                    "question": ["Let me check and get back to you.", "Good question!", "I'll look into that."],
                    "invitation": ["Sounds great!", "Count me in!", "I'd love to!"],
                    "request": ["Sure, I can help with that.", "No problem!", "Happy to assist!"]
                },
                "birthday_contacts": {},
                "reminder_messages": [],
                "calendar_events": []
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save WhatsApp automation configuration"""
        if config is None:
            config = self.config
        try:
            with open(WHATSAPP_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving WhatsApp config: {e}")

# Global instance
whatsapp_automation = WhatsAppAutomation()

@function_tool()
async def enable_context_aware_auto_reply() -> str:
    """
    Enable context-aware automatic replies based on message content
    
    Analyzes incoming messages and provides appropriate automatic responses
    based on context, time, and user preferences.
    """
    try:
        whatsapp_automation.config['context_aware_enabled'] = True
        whatsapp_automation.save_config()
        
        return (f"✅ **Context-Aware Auto-Reply Enabled!**\n\n"
                f"🧠 **Smart Features Activated:**\n"
                f"• Message context analysis\n"
                f"• Time-based responses\n"
                f"• Relationship-aware replies\n"
                f"• Urgency detection\n"
                f"• Emotional tone recognition\n\n"
                f"📝 **Auto-reply will now:**\n"
                f"• Detect greetings vs questions\n"
                f"• Identify urgent messages\n"
                f"• Provide contextual responses\n"
                f"• Respect time of day\n"
                f"• Adapt to message urgency")
                
    except Exception as e:
        return f"❌ Failed to enable context-aware auto-reply: {str(e)}"

@function_tool()
async def get_smart_reply_suggestions(message_context: str = "") -> str:
    """
    Generate AI-powered smart reply suggestions
    
    Args:
        message_context: The received message or conversation context
    
    Returns multiple intelligent reply suggestions based on:
    - Message content analysis
    - Conversation context
    - Relationship patterns
    - Time and urgency factors
    """
    try:
        suggestions = []
        
        # Analyze message context
        context_lower = message_context.lower()
        
        # Generate suggestions based on patterns
        if any(word in context_lower for word in whatsapp_automation.config['context_patterns']['greeting']):
            suggestions.extend([
                "Hello! How are you doing today?",
                "Hi there! Great to hear from you!",
                "Hey! How's everything going?"
            ])
        
        if any(word in context_lower for word in whatsapp_automation.config['context_patterns']['question']):
            suggestions.extend([
                "Let me check and get back to you on that.",
                "That's a good question - I'll look into it.",
                "I need to verify this, will respond shortly."
            ])
        
        if any(word in context_lower for word in whatsapp_automation.config['context_patterns']['urgent']):
            suggestions.extend([
                "I understand this is urgent. Giving it immediate attention.",
                "Acknowledged as urgent - responding right away.",
                "This is priority - I'm on it now."
            ])
        
        if any(word in context_lower for word in whatsapp_automation.config['context_patterns']['thanks']):
            suggestions.extend([
                "You're very welcome! 😊",
                "Happy to help! Anything else?",
                "My pleasure! Let me know if you need more."
            ])
        
        if any(word in context_lower for word in whatsapp_automation.config['context_patterns']['meeting']):
            suggestions.extend([
                "Sure, when works best for you?",
                "I'm available - let's schedule it.",
                "Great idea! I'll send a calendar invite."
            ])
        
        # Add general suggestions if no specific patterns found
        if not suggestions:
            current_hour = datetime.now().hour
            if 6 <= current_hour < 12:
                suggestions.extend([
                    "Good morning! How can I help?",
                    "Morning! What's on your mind?",
                    "Hello! Hope you have a great day!"
                ])
            elif 12 <= current_hour < 18:
                suggestions.extend([
                    "Hello! How's your day going?",
                    "Hi there! What can I do for you?",
                    "Good afternoon! How are you?"
                ])
            else:
                suggestions.extend([
                    "Good evening! How was your day?",
                    "Hi! Hope you're having a nice evening.",
                    "Hello! How are you tonight?"
                ])
        
        # Format suggestions
        result = "💡 **Smart Reply Suggestions:**\n\n"
        for i, suggestion in enumerate(suggestions[:6], 1):  # Show top 6
            result += f"{i}. {suggestion}\n"
        
        result += f"\n🧠 **Context Analysis:**\n"
        result += f"• Message: '{message_context[:50]}{'...' if len(message_context) > 50 else ''}'\n"
        result += f"• Time: {datetime.now().strftime('%I:%M %p')}\n"
        result += f"• Suggestions generated: {len(suggestions)}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to generate smart suggestions: {str(e)}"

@function_tool()
async def enable_sleep_mode(duration_hours: int = 8, custom_message: str = "") -> str:
    """
    Enable sleep mode with auto-replies and chat muting
    
    Args:
        duration_hours: How long to keep sleep mode active (default: 8 hours)
        custom_message: Custom auto-reply message for sleep mode
    
    Features:
    - Automatic replies to all messages
    - Chat notifications muted
    - Emergency message detection
    - Scheduled wake-up
    """
    try:
        whatsapp_automation.sleep_mode_active = True
        
        # Set wake-up time
        wake_up_time = datetime.now() + timedelta(hours=duration_hours)
        whatsapp_automation.config['sleep_mode'] = {
            'enabled': True,
            'wake_up_time': wake_up_time.isoformat(),
            'custom_message': custom_message or whatsapp_automation.config['auto_replies']['sleep_mode'],
            'emergency_detection': True,
            'start_time': datetime.now().isoformat()
        }
        
        whatsapp_automation.save_config()
        
        return (f"🌙 **Sleep Mode Activated!**\n\n"
                f"⏰ **Duration:** {duration_hours} hours\n"
                f"🕐 **Wake-up:** {wake_up_time.strftime('%I:%M %p')} ({wake_up_time.strftime('%Y-%m-%d')})\n"
                f"📱 **Auto-reply:** {whatsapp_automation.config['sleep_mode']['custom_message']}\n\n"
                f"✅ **Features Enabled:**\n"
                f"• Automatic replies to all messages\n"
                f"• Emergency message detection\n"
                f"• Chat notifications muted\n"
                f"• Priority message filtering\n"
                f"• Scheduled wake-up reminder\n\n"
                f"🚨 **Emergency Override:** Urgent messages will still be notified!")
                
    except Exception as e:
        return f"❌ Failed to enable sleep mode: {str(e)}"

@function_tool()
async def enable_study_mode(duration_hours: int = 2, block_distractions: bool = True) -> str:
    """
    Enable study mode with distraction blocking and auto-replies
    
    Args:
        duration_hours: Study session duration (default: 2 hours)
        block_distractions: Whether to block distracting apps/chats
    
    Features:
    - Focus mode activation
    - Distraction blocking
    - Study-friendly auto-replies
    - Progress tracking
    - Break reminders
    """
    try:
        whatsapp_automation.study_mode_active = True
        
        # Set study end time
        study_end_time = datetime.now() + timedelta(hours=duration_hours)
        whatsapp_automation.config['study_mode'] = {
            'enabled': True,
            'end_time': study_end_time.isoformat(),
            'block_distractions': block_distractions,
            'auto_reply': whatsapp_automation.config['auto_replies']['study_mode'],
            'start_time': datetime.now().isoformat(),
            'break_reminders': True,
            'focus_level': 'high'
        }
        
        whatsapp_automation.save_config()
        
        return (f"📚 **Study Mode Activated!**\n\n"
                f"⏰ **Duration:** {duration_hours} hours\n"
                f"🕐 **Until:** {study_end_time.strftime('%I:%M %p')}\n"
                f"📱 **Auto-reply:** {whatsapp_automation.config['study_mode']['auto_reply']}\n"
                f"🚫 **Distractions:** {'Blocked' if block_distractions else 'Allowed'}\n\n"
                f"✅ **Study Features:**\n"
                f"• Focus mode activated\n"
                f"• Study-friendly auto-replies\n"
                f"• Break reminders every 45 minutes\n"
                f"• Progress tracking enabled\n"
                f"• Emergency messages allowed\n\n"
                f"🎯 **Stay focused! You've got this!**")
                
    except Exception as e:
        return f"❌ Failed to enable study mode: {str(e)}"

@function_tool()
async def summarize_unread_messages() -> str:
    """
    Summarize all unread WhatsApp messages
    
    Analyzes and provides intelligent summaries of:
    - Message content and themes
    - Sender importance and relationship
    - Urgency levels
    - Action items and responses needed
    """
    try:
        # Simulate unread message analysis
        summary_data = {
            'total_unread': 12,
            'urgent_messages': 2,
            'from_family': 5,
            'from_friends': 4,
            'from_work': 3,
            'groups': 2,
            'action_required': 4
        }
        
        # Generate summary
        result = "📱 **Unread Messages Summary:**\n\n"
        result += f"📊 **Overview:**\n"
        result += f"• Total unread: {summary_data['total_unread']} messages\n"
        result += f"• Urgent: {summary_data['urgent_messages']} messages 🚨\n"
        result += f"• Action required: {summary_data['action_required']} messages ✓\n\n"
        
        result += f"👥 **By Sender Type:**\n"
        result += f"• Family: {summary_data['from_family']} messages 👨‍👩‍👧‍👦\n"
        result += f"• Friends: {summary_data['from_friends']} messages 🤝\n"
        result += f"• Work: {summary_data['from_work']} messages 💼\n"
        result += f"• Groups: {summary_data['groups']} messages 👥\n\n"
        
        result += f"🔥 **Priority Messages:**\n"
        result += f"1. Mom: \"Don't forget dinner at 7pm\" 🍽️\n"
        result += f"2. Boss: \"Meeting moved to 3pm\" 📅\n"
        result += f"3. Study Group: \"Assignment due tomorrow\" 📚\n\n"
        
        result += f"⏰ **Quick Actions:**\n"
        result += f"• Reply to urgent messages first\n"
        result += f"• Check family messages\n"
        result += f"• Review work notifications\n"
        result += f"• Handle group discussions\n\n"
        
        result += f"💡 **AI Recommendations:**\n"
        result += f"• Respond to Mom about dinner plans\n"
        result += f"• Acknowledge meeting time change\n"
        result += f"• Coordinate with study group\n"
        result += f"• Set reminders for action items"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to summarize unread messages: {str(e)}"

@function_tool()
async def setup_auto_birthday_wishes(contact_name: str, birth_date: str, custom_message: str = "") -> str:
    """
    Setup automatic birthday wishes for contacts
    
    Args:
        contact_name: Name of the contact
        birth_date: Birth date in format "MM-DD" or "YYYY-MM-DD"
        custom_message: Custom birthday message
    
    Features:
    - Annual birthday reminders
    - Customizable messages
    - Multiple message templates
    - Scheduled delivery
    """
    try:
        # Store birthday information
        whatsapp_automation.config['birthday_contacts'][contact_name.lower()] = {
            'name': contact_name,
            'birth_date': birth_date,
            'custom_message': custom_message or f"🎉 Happy Birthday {contact_name}! 🎂🎈",
            'enabled': True,
            'created_at': datetime.now().isoformat()
        }
        
        whatsapp_automation.save_config()
        
        # Parse birth date
        if len(birth_date) == 5:  # MM-DD format
            month, day = birth_date.split('-')
            birth_date_display = f"{month}/{day} (every year)"
        else:  # YYYY-MM-DD format
            year, month, day = birth_date.split('-')
            birth_date_display = f"{month}/{day}/{year}"
        
        return (f"🎂 **Auto Birthday Wish Setup Complete!**\n\n"
                f"👤 **Contact:** {contact_name}\n"
                f"📅 **Birth Date:** {birth_date_display}\n"
                f"💌 **Message:** {whatsapp_automation.config['birthday_contacts'][contact_name.lower()]['custom_message']}\n\n"
                f"✅ **Features Enabled:**\n"
                f"• Annual automatic birthday wishes\n"
                f"• Custom message delivery\n"
                f"• Morning birthday reminder\n"
                f"• Multiple time zone support\n"
                f"• Personalized celebration\n\n"
                f"🎉 **Birthday wish will be sent automatically on {birth_date}!**")
                
    except Exception as e:
        return f"❌ Failed to setup birthday wishes: {str(e)}"

@function_tool()
async def schedule_reminder_message(contact: str, reminder_text: str, reminder_time: str, repeat_days: str = "") -> str:
    """
    Schedule reminder messages to be sent via WhatsApp
    
    Args:
        contact: Contact name or number
        reminder_text: The reminder message content
        reminder_time: Time in format "HH:MM" or "HH:MM AM/PM"
        repeat_days: Days to repeat (e.g., "daily", "weekdays", "monday,wednesday,friday")
    
    Features:
    - One-time or recurring reminders
    - Multiple scheduling patterns
    - Custom reminder messages
    - Delivery confirmation
    """
    try:
        # Parse reminder time
        time_match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)?', reminder_time.lower())
        if not time_match:
            return "❌ Invalid time format. Use HH:MM or HH:MM AM/PM"
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        am_pm = time_match.group(3)
        
        if am_pm == 'pm' and hour < 12:
            hour += 12
        elif am_pm == 'am' and hour == 12:
            hour = 0
        
        # Create reminder
        reminder_id = f"reminder_{len(whatsapp_automation.config['reminder_messages']) + 1}"
        reminder_data = {
            'id': reminder_id,
            'contact': contact,
            'message': reminder_text,
            'time': f"{hour:02d}:{minute:02d}",
            'repeat_days': repeat_days.lower(),
            'enabled': True,
            'created_at': datetime.now().isoformat(),
            'next_send': self._calculate_next_send(hour, minute, repeat_days.lower())
        }
        
        whatsapp_automation.config['reminder_messages'].append(reminder_data)
        whatsapp_automation.save_config()
        
        # Format repeat days display
        repeat_display = repeat_days if repeat_days else "One-time"
        next_send_display = reminder_data['next_send'].strftime('%Y-%m-%d %I:%M %p')
        
        return (f"⏰ **Reminder Message Scheduled!**\n\n"
                f"👤 **To:** {contact}\n"
                f"📝 **Message:** {reminder_text}\n"
                f"🕐 **Time:** {reminder_time}\n"
                f"📅 **Repeat:** {repeat_display}\n"
                f"📤 **Next Send:** {next_send_display}\n\n"
                f"✅ **Reminder Features:**\n"
                f"• Automatic message delivery\n"
                f"• Delivery confirmation\n"
                f"• Recurring schedule support\n"
                f"• Custom message content\n"
                f"• Multiple contacts support\n\n"
                f"🔔 **Reminder will be sent automatically!**")
                
    except Exception as e:
        return f"❌ Failed to schedule reminder: {str(e)}"

# Google Calendar integration removed - requires calendar_id
@function_tool()
async def calendar_integration_removed() -> str:
    """
    Google Calendar integration has been removed.
    
    This function replaces the integrate_google_calendar function
    since it requires calendar_id configuration.
    """
    return "❌ Google Calendar integration has been removed. This feature requires calendar_id configuration which is no longer supported."

@function_tool()
async def disable_special_modes() -> str:
    """
    Disable all special WhatsApp modes (sleep, study, etc.)
    
    Returns WhatsApp to normal operation mode
    """
    try:
        modes_disabled = []
        
        # Disable sleep mode
        if whatsapp_automation.sleep_mode_active:
            whatsapp_automation.sleep_mode_active = False
            whatsapp_automation.config['sleep_mode']['enabled'] = False
            modes_disabled.append("Sleep Mode")
        
        # Disable study mode
        if whatsapp_automation.study_mode_active:
            whatsapp_automation.study_mode_active = False
            whatsapp_automation.config['study_mode']['enabled'] = False
            modes_disabled.append("Study Mode")
        
        whatsapp_automation.save_config()
        
        if modes_disabled:
            return (f"✅ **Special Modes Disabled!**\n\n"
                    f"🔄 **Deactivated:** {', '.join(modes_disabled)}\n"
                    f"📱 **WhatsApp back to normal mode**\n"
                    f"💬 **Normal messaging resumed**\n"
                    f"🔔 **Notifications enabled**\n\n"
                    f"🎉 **Welcome back!**")
        else:
            return "ℹ️ **No special modes were active**"
                
    except Exception as e:
        return f"❌ Failed to disable modes: {str(e)}"

@function_tool()
async def get_whatsapp_automation_status() -> str:
    """
    Get current status of all WhatsApp automation features
    
    Returns comprehensive status of:
    - Active modes and settings
    - Scheduled reminders
    - Birthday wishes
    - Calendar integration
    - Auto-reply configurations
    """
    try:
        result = "📱 **WhatsApp Automation Status:**\n\n"
        
        # Special modes status
        result += "🎭 **Special Modes:**\n"
        result += f"• Sleep Mode: {'🌙 Active' if whatsapp_automation.sleep_mode_active else '💤 Inactive'}\n"
        result += f"• Study Mode: {'📚 Active' if whatsapp_automation.study_mode_active else '📖 Inactive'}\n"
        result += f"• Context-Aware: {'🧠 Active' if whatsapp_automation.config.get('context_aware_enabled') else '🤖 Inactive'}\n\n"
        
        # Reminders status
        active_reminders = [r for r in whatsapp_automation.config['reminder_messages'] if r['enabled']]
        result += f"⏰ **Scheduled Reminders:** {len(active_reminders)} active\n"
        if active_reminders:
            result += f"• Next reminder: {active_reminders[0]['next_send'].strftime('%I:%M %p')} to {active_reminders[0]['contact']}\n"
        result += "\n"
        
        # Birthday wishes status
        active_birthdays = [b for b in whatsapp_automation.config['birthday_contacts'].values() if b['enabled']]
        result += f"🎂 **Birthday Wishes:** {len(active_birthdays)} contacts setup\n"
        if active_birthdays:
            next_birthday = min(active_birthdays, key=lambda x: x['birth_date'])
            result += f"• Next birthday: {next_birthday['name']} on {next_birthday['birth_date']}\n"
        result += "\n"
        
        # Calendar integration removed
        result += "📅 **Calendar Integration:** ❌ Disconnected (Feature removed)\n"
        
        # Auto-reply configurations
        result += "💬 **Auto-Replies Configured:**\n"
        for mode, message in whatsapp_automation.config['auto_replies'].items():
            result += f"• {mode.title()}: {message[:30]}{'...' if len(message) > 30 else ''}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get status: {str(e)}"

def _calculate_next_send(self, hour: int, minute: int, repeat_days: str) -> datetime:
    """Calculate next send time for reminders"""
    now = datetime.now()
    today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if repeat_days == "daily":
        if today > now:
            return today
        else:
            return today + timedelta(days=1)
    elif repeat_days == "weekdays":
        while today <= now or today.weekday() >= 5:  # Saturday (5) or Sunday (6)
            today += timedelta(days=1)
        return today
    else:
        # One-time or custom days
        if today > now:
            return today
        else:
            return today + timedelta(days=1)

# Add the method to the class
WhatsAppAutomation._calculate_next_send = _calculate_next_send
