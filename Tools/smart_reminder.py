import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from livekit.agents import function_tool

class SmartReminder:
    """Smart reminder system with notifications"""
    
    def __init__(self):
        self.reminders = {}
        self.reminder_counter = 0
        self.monitor_task = None
        self.session = None
        self.reminder_file = "json/smart_reminders.json"
        
        # Load existing reminders
        self._load_reminders()
        
    def _load_reminders(self):
        """Load reminders from file"""
        try:
            import os
            if os.path.exists(self.reminder_file):
                with open(self.reminder_file, 'r') as f:
                    self.reminders = json.load(f)
                    self.reminder_counter = max([int(k.split('_')[1]) for k in self.reminders.keys()] + [0]) + 1
        except Exception as e:
            print(f"Failed to load reminders: {e}")
            self.reminders = {}
            self.reminder_counter = 0
    
    def _save_reminders(self):
        """Save reminders to file"""
        try:
            with open(self.reminder_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"Failed to save reminders: {e}")
    
    def set_session(self, session):
        """Set session for notifications"""
        self.session = session
    
    def add_reminder(self, text: str, minutes: int = None, hours: int = None, time_str: str = None) -> str:
        """Add a new reminder"""
        try:
            rid = f"rem_{self.reminder_counter}"
            self.reminder_counter += 1
            
            # Calculate reminder time
            if time_str:
                # Parse time string (e.g., "2:30 PM", "14:30")
                try:
                    if "PM" in time_str.upper():
                        time_parts = time_str.replace("PM", "").strip().split(":")
                        hour = int(time_parts[0]) + 12
                        minute = int(time_parts[1])
                    elif "AM" in time_str.upper():
                        time_parts = time_str.replace("AM", "").strip().split(":")
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                    else:
                        time_parts = time_str.split(":")
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                    
                    now = datetime.now()
                    reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # If time is in the past, set for tomorrow
                    if reminder_time <= now:
                        reminder_time += timedelta(days=1)
                        
                except:
                    return "❌ Invalid time format. Use '2:30 PM' or '14:30'"
                    
            elif minutes or hours:
                # Add minutes/hours from now
                now = datetime.now()
                reminder_time = now + timedelta(minutes=minutes or 0, hours=hours or 0)
            else:
                return "❌ Please specify time: minutes, hours, or time_str"
            
            self.reminders[rid] = {
                "text": text,
                "time": reminder_time.isoformat(),
                "created": datetime.now().isoformat(),
                "triggered": False
            }
            
            # Start monitor if not running
            if not self.monitor_task or self.monitor_task.done():
                self.monitor_task = asyncio.create_task(self._monitor_reminders())
            
            # Save to file
            self._save_reminders()
            
            result = f"✅ REMINDER ADDED\n\n"
            result += f"📝 Reminder: {text}\n"
            result += f"🕐 Time: {reminder_time.strftime('%H:%M:%S')}\n"
            result += f"📅 Date: {reminder_time.strftime('%Y-%m-%d')}\n"
            result += f"🆔 ID: {rid}\n"
            result += f"🔔 I'll notify you when it's time!\n"
            
            return result
            
        except Exception as e:
            return f"❌ Failed to add reminder: {str(e)}"
    
    def cancel_reminder(self, rid: str = None) -> str:
        """Cancel a reminder"""
        try:
            if rid and rid in self.reminders:
                # Cancel specific reminder
                reminder = self.reminders.pop(rid)
                self._save_reminders()
                
                result = f"✅ REMINDER CANCELLED\n\n"
                result += f"🆔 ID: {rid}\n"
                result += f"📝 Text: {reminder['text']}\n"
                result += f"🕐 Was set for: {datetime.fromisoformat(reminder['time']).strftime('%H:%M:%S')}\n"
                
            elif not rid:
                # Cancel all reminders
                cancelled_count = len(self.reminders)
                self.reminders.clear()
                self._save_reminders()
                
                result = f"✅ ALL REMINDERS CANCELLED\n\n"
                result += f"🗑️ Cancelled: {cancelled_count} reminders\n"
                
            else:
                return f"❌ Reminder ID '{rid}' not found"
            
            return result
            
        except Exception as e:
            return f"❌ Failed to cancel reminder: {str(e)}"
    
    def list_reminders(self) -> str:
        """List all active reminders"""
        try:
            if not self.reminders:
                return "✅ No active reminders\n\n💡 Use 'add_reminder' to create one!"
            
            result = f"📋 ACTIVE REMINDERS\n\n"
            
            for rid, reminder in self.reminders.items():
                reminder_time = datetime.fromisoformat(reminder['time'])
                now = datetime.now()
                
                if reminder_time > now:
                    time_left = reminder_time - now
                    hours_left = int(time_left.total_seconds() // 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) // 60)
                    
                    result += f"🆔 {rid}: {reminder['text']}\n"
                    result += f"   🕐 Time: {reminder_time.strftime('%H:%M:%S')}\n"
                    result += f"   📅 Date: {reminder_time.strftime('%Y-%m-%d')}\n"
                    result += f"   ⏱️ In: {hours_left}h {minutes_left}m\n\n"
                else:
                    result += f"⏰ {rid}: {reminder['text']} (PAST)\n"
                    result += f"   🕐 Was: {reminder_time.strftime('%H:%M:%S')}\n\n"
            
            return result
            
        except Exception as e:
            return f"❌ Failed to list reminders: {str(e)}"
    
    async def _monitor_reminders(self):
        """Monitor and trigger reminders"""
        print("🔔 Smart reminder monitor started")
        
        while self.reminders:
            now = datetime.now()
            triggered = []
            
            for rid, reminder in self.reminders.items():
                if not reminder.get('triggered', False):
                    reminder_time = datetime.fromisoformat(reminder['time'])
                    
                    if now >= reminder_time:
                        # Trigger reminder
                        await self._trigger_reminder(reminder['text'], rid)
                        reminder['triggered'] = True
                        triggered.append(rid)
            
            # Remove triggered reminders
            for rid in triggered:
                self.reminders.pop(rid, None)
            
            # Save updated reminders
            self._save_reminders()
            
            # Check every 30 seconds
            await asyncio.sleep(30)
    
    async def _trigger_reminder(self, text: str, rid: str):
        """Trigger a reminder notification"""
        try:
            if self.session:
                message = f"🔔 Your reminder for {text} is here boss. Please start with your {text}. 🕐 {datetime.now().strftime('%H:%M:%S')}\n\n🆔 ID: {rid}"
                
                try:
                    await self.session.generate_reply(
                        instructions=message
                    )
                    print(f"🔔 Reminder triggered: {text}")
                    print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
                    print(f"🆔 ID: {rid}")
                except Exception as session_error:
                    print(f"⚠️ Session not ready for reminder: {session_error}")
                
        except Exception as e:
            print(f"Failed to trigger reminder: {e}")

# Global instance
smart_reminder = SmartReminder()

@function_tool()
async def add_reminder(text: str, minutes: int = None, hours: int = None, time_str: str = None) -> str:
    """
    Add a new reminder with flexible time options
    
    Args:
        text: Reminder text/message
        minutes: Minutes from now (optional)
        hours: Hours from now (optional)  
        time_str: Specific time like "2:30 PM" or "14:30" (optional)
        
    Returns:
        str: Reminder confirmation
    """
    try:
        return smart_reminder.add_reminder(text, minutes, hours, time_str)
        
    except Exception as e:
        return f"❌ Add reminder failed: {str(e)}"

@function_tool()
async def cancel_reminder(rid: str = None) -> str:
    """
    Cancel a specific reminder or all reminders
    
    Args:
        rid: Reminder ID (optional, if not provided cancels all)
        
    Returns:
        str: Cancellation confirmation
    """
    try:
        return smart_reminder.cancel_reminder(rid)
        
    except Exception as e:
        return f"❌ Cancel reminder failed: {str(e)}"

@function_tool()
async def list_reminders() -> str:
    """
    List all active reminders with time remaining
    
    Returns:
        str: List of reminders
    """
    try:
        return smart_reminder.list_reminders()
        
    except Exception as e:
        return f"❌ List reminders failed: {str(e)}"

@function_tool()
async def reminder_status() -> str:
    """
    Get reminder system status
    
    Returns:
        str: System status
    """
    try:
        result = f"📊 SMART REMINDER STATUS\n\n"
        result += f"🕐 Current time: {datetime.now().strftime('%H:%M:%S')}\n"
        result += f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        result += f"📝 Active reminders: {len(smart_reminder.reminders)}\n"
        result += f"🔔 Monitor: {'Running' if smart_reminder.monitor_task and not smart_reminder.monitor_task.done() else 'Stopped'}\n\n"
        
        if smart_reminder.reminders:
            result += f"💡 Next check in 30 seconds\n"
            result += f"📁 Reminders saved to: {smart_reminder.reminder_file}\n"
        else:
            result += f"💡 Use 'add_reminder' to create reminders!\n"
        
        return result
        
    except Exception as e:
        return f"❌ Status check failed: {str(e)}"
