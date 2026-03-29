import asyncio
import re
from datetime import datetime, timedelta
from livekit.agents import function_tool
from typing import Dict, Any, List, Optional, Callable
import json

class AdvancedScheduler:
    """Advanced cron-like scheduler with emotional intelligence"""
    
    def __init__(self):
        self.cron_jobs = {}  # Recurring tasks
        self.emotional_triggers = {}  # Emotion-based tasks
        self.conditional_tasks = {}  # Condition-based tasks
        self.one_time_tasks = {}  # Single execution tasks
        self.task_counter = 0
        self.running = False
        
    def parse_cron_expression(self, cron_expr: str) -> Dict[str, Any]:
        """Parse cron expression: * * * * * (minute hour day month weekday)"""
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression. Use format: * * * * *")
        
        return {
            'minute': parts[0],
            'hour': parts[1], 
            'day': parts[2],
            'month': parts[3],
            'weekday': parts[4]
        }
    
    def matches_cron_time(self, cron_config: Dict[str, Any], test_time: datetime) -> bool:
        """Check if current time matches cron expression"""
        # Minute
        if cron_config['minute'] != '*' and str(test_time.minute) != cron_config['minute']:
            return False
        # Hour
        if cron_config['hour'] != '*' and str(test_time.hour) != cron_config['hour']:
            return False
        # Day
        if cron_config['day'] != '*' and str(test_time.day) != cron_config['day']:
            return False
        # Month
        if cron_config['month'] != '*' and str(test_time.month) != cron_config['month']:
            return False
        # Weekday (0=Monday, 6=Sunday)
        if cron_config['weekday'] != '*' and str(test_time.weekday()) != cron_config['weekday']:
            return False
        
        return True
    
    def parse_natural_schedule(self, schedule_str: str) -> Dict[str, Any]:
        """Parse natural language schedule to cron or datetime"""
        schedule_str = schedule_str.lower().strip()
        now = datetime.now()
        
        # Daily at specific time
        if 'daily' in schedule_str:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)', schedule_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                am_pm = time_match.group(3)
                
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                return {
                    'type': 'cron',
                    'cron_expr': f'{minute} {hour} * * *',
                    'description': f'Daily at {time_match.group(0)}'
                }
        
        # Weekdays at specific time
        if 'weekday' in schedule_str or 'weekdays' in schedule_str:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)', schedule_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                am_pm = time_match.group(3)
                
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                return {
                    'type': 'cron',
                    'cron_expr': f'{minute} {hour} * * 1-5',
                    'description': f'Weekdays at {time_match.group(0)}'
                }
        
        # Weekends at specific time
        if 'weekend' in schedule_str or 'weekends' in schedule_str:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)', schedule_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                am_pm = time_match.group(3)
                
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                return {
                    'type': 'cron',
                    'cron_expr': f'{minute} {hour} * * 0,6',
                    'description': f'Weekends at {time_match.group(0)}'
                }
        
        # Every X hours/minutes
        every_match = re.search(r'every\s*(\d+)\s*(minutes?|hours?)', schedule_str)
        if every_match:
            interval = int(every_match.group(1))
            unit = every_match.group(2)
            
            if 'hour' in unit:
                return {
                    'type': 'interval',
                    'interval_seconds': interval * 3600,
                    'description': f'Every {interval} hours'
                }
            else:
                return {
                    'type': 'interval',
                    'interval_seconds': interval * 60,
                    'description': f'Every {interval} minutes'
                }
        
        # Specific days
        days_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        for day_name, day_num in days_map.items():
            if day_name in schedule_str:
                time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)', schedule_str)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    am_pm = time_match.group(3)
                    
                    if am_pm == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                    
                    return {
                        'type': 'cron',
                        'cron_expr': f'{minute} {hour} * * {day_num}',
                        'description': f'Every {day_name.title()} at {time_match.group(0)}'
                    }
        
        # Fallback to basic time parsing
        basic_time = parse_schedule_time(schedule_str)
        if basic_time:
            return {
                'type': 'datetime',
                'datetime': basic_time,
                'description': f'At {basic_time.strftime("%Y-%m-%d %H:%M:%S")}'
            }
        
        return None

# Global scheduler instance
advanced_scheduler = AdvancedScheduler()

def parse_schedule_time(time_str: str) -> datetime:
    """Parse schedule time string to datetime (legacy support)"""
    time_str = time_str.lower().strip()
    now = datetime.now()
    
    # Today at specific time
    time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        am_pm = time_match.group(3)
        
        # Convert to 24-hour format
        if am_pm == 'pm' and hour < 12:
            hour += 12
        elif am_pm == 'am' and hour == 12:
            hour = 0
            
        schedule_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time already passed today, schedule for tomorrow
        if schedule_time < now:
            schedule_time += timedelta(days=1)
            
        return schedule_time
    
    # After X minutes/hours
    time_patterns = [
        (r'after\s*(\d+)\s*minutes?', 60),
        (r'after\s*(\d+)\s*hours?', 3600),
        (r'in\s*(\d+)\s*minutes?', 60),
        (r'in\s*(\d+)\s*hours?', 3600),
    ]
    
    for pattern, multiplier in time_patterns:
        match = re.search(pattern, time_str)
        if match:
            seconds = int(match.group(1)) * multiplier
            return now + timedelta(seconds=seconds)
    
    # Tomorrow at specific time
    if 'tomorrow' in time_str:
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            am_pm = time_match.group(3)
            
            if am_pm == 'pm' and hour < 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
                
            schedule_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            schedule_time += timedelta(days=1)
            return schedule_time
    
    return None

@function_tool()
async def schedule_task(
    task_description: str,
    schedule_time: str,
    tool_name: str,
    tool_parameters: str = ""
) -> str:
    """
    Schedule a task to be executed automatically at specific time.
    
    Examples:
    - "Schedule to open browser at 3:00 PM"
    - "Set task to check weather tomorrow at 9:00 AM" 
    - "After 30 minutes, search for AI news"
    - "At 6:00 PM, send WhatsApp message to mom"
    
    Args:
        task_description: What task to perform
        schedule_time: When to execute (e.g., "3:00 PM", "after 30 minutes", "tomorrow at 9:00 AM")
        tool_name: Which tool to execute (e.g., "open_app", "search_web", "send_whatsapp_message")
        tool_parameters: Parameters for the tool (e.g., "browser", "AI news", "message to mom")
    """
    try:
        # Parse schedule time
        scheduled_datetime = parse_schedule_time(schedule_time)
        if not scheduled_datetime:
            return "❌ Could not understand the schedule time. Please specify like '3:00 PM' or 'after 30 minutes'"
        
        # Store task in agent's scheduler system
        from tools import assistant_instance
        if hasattr(assistant_instance, 'add_scheduled_task'):
            task_id = assistant_instance.add_scheduled_task(
                task_description=task_description,
                schedule_time=scheduled_datetime,
                tool_name=tool_name,
                tool_parameters=tool_parameters
            )
            
            return (f"✅ Task scheduled successfully!\n"
                   f"📝 Task: {task_description}\n"
                   f"🛠️ Tool: {tool_name}\n" 
                   f"⏰ Time: {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n"
                   f"🆔 ID: {task_id}")
        else:
            return "❌ Task scheduler not available"
            
    except Exception as e:
        return f"❌ Failed to schedule task: {str(e)}"

@function_tool()
async def view_scheduled_tasks() -> str:
    """View all scheduled tasks"""
    try:
        from tools import assistant_instance
        if hasattr(assistant_instance, 'get_scheduled_tasks'):
            tasks = assistant_instance.get_scheduled_tasks()
            if not tasks:
                return "📋 No scheduled tasks"
            
            task_list = []
            for task_id, task in tasks.items():
                time_left = task['schedule_time'] - datetime.now()
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                task_list.append(
                    f"🆔 {task_id}\n"
                    f"📝 {task['task_description']}\n"
                    f"🛠️ Tool: {task['tool_name']}\n"
                    f"⏰ Time: {task['schedule_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"⏳ Time left: {hours}h {minutes}m {seconds}s\n"
                )
            
            return "📋 Scheduled Tasks:\n\n" + "\n".join(task_list)
        else:
            return "❌ Task scheduler not available"
            
    except Exception as e:
        return f"❌ Failed to view scheduled tasks: {str(e)}"

@function_tool()
async def cancel_scheduled_task(task_id: str) -> str:
    """Cancel a specific scheduled task by ID"""
    try:
        from tools import assistant_instance
        if hasattr(assistant_instance, 'cancel_scheduled_task'):
            success = assistant_instance.cancel_scheduled_task(task_id)
            if success:
                return f"✅ Task {task_id} cancelled successfully"
            else:
                return f"❌ Task {task_id} not found"
        else:
            return "❌ Task scheduler not available"
            
    except Exception as e:
        return f"❌ Failed to cancel task: {str(e)}"

@function_tool()
async def schedule_advanced_task(
    task_description: str,
    schedule_pattern: str,
    tool_name: str,
    tool_parameters: str = ""
) -> str:
    """
    Schedule advanced recurring tasks using cron expressions or natural language.
    
    Examples:
    - "Daily motivation at 8 AM", "send_whatsapp_message", "Good morning! Time to conquer the day!"
    - "Weekdays at 3 PM", "play_media", "study music"
    - "Every 2 hours", "get_emotional_status", ""
    - "Every Monday at 9 AM", "send_whatsapp_message", "Weekly progress update"
    - "Weekends at 10 AM", "generate_ai_image", "motivational quote"
    
    Args:
        task_description: Description of the task
        schedule_pattern: When to execute (cron format like "0 8 * * *" or natural language)
        tool_name: Which tool to execute
        tool_parameters: Parameters for the tool
    """
    try:
        # Parse schedule pattern
        schedule_config = advanced_scheduler.parse_natural_schedule(schedule_pattern)
        if not schedule_config:
            return "❌ Could not understand schedule pattern. Use cron format (0 8 * * *) or natural language like 'daily at 8 AM'"
        
        # Generate task ID
        task_id = f"adv_task_{advanced_scheduler.task_counter}"
        advanced_scheduler.task_counter += 1
        
        # Store task
        task_data = {
            'id': task_id,
            'description': task_description,
            'tool_name': tool_name,
            'tool_parameters': tool_parameters,
            'schedule_config': schedule_config,
            'created_at': datetime.now(),
            'enabled': True
        }
        
        if schedule_config['type'] == 'cron':
            advanced_scheduler.cron_jobs[task_id] = task_data
        elif schedule_config['type'] == 'interval':
            advanced_scheduler.cron_jobs[task_id] = task_data  # Store intervals in cron_jobs for simplicity
        else:
            advanced_scheduler.one_time_tasks[task_id] = task_data
        
        return (f"✅ Advanced task scheduled successfully!\n"
               f"📝 Task: {task_description}\n"
               f"🛠️ Tool: {tool_name}\n"
               f"⏰ Schedule: {schedule_config['description']}\n"
               f"🆔 ID: {task_id}\n"
               f"📊 Type: {schedule_config['type'].title()}")
               
    except Exception as e:
        return f"❌ Failed to schedule advanced task: {str(e)}"

@function_tool()
async def schedule_emotional_trigger(
    emotion_type: str,
    threshold: float,
    action_tool: str,
    action_parameters: str = "",
    trigger_description: str = ""
) -> str:
    """
    Schedule tasks that trigger based on emotional states.
    
    Examples:
    - "frustration", 0.7, "play_media", "calming music", "When I'm frustrated"
    - "low focus", 0.4, "manual_emotional_intervention", "gentle", "When focus is low"
    - "high care", 0.8, "send_whatsapp_message", "I'm doing great!", "Share achievements"
    
    Args:
        emotion_type: Type of emotion (frustration, care, patience, focus)
        threshold: Trigger threshold (0.0 - 1.0)
        action_tool: Tool to execute when triggered
        action_parameters: Parameters for the action tool
        trigger_description: Description of when this triggers
    """
    try:
        # Generate task ID
        task_id = f"emot_trigger_{advanced_scheduler.task_counter}"
        advanced_scheduler.task_counter += 1
        
        # Store emotional trigger
        trigger_data = {
            'id': task_id,
            'emotion_type': emotion_type.lower(),
            'threshold': max(0.0, min(1.0, threshold)),  # Clamp between 0 and 1
            'action_tool': action_tool,
            'action_parameters': action_parameters,
            'description': trigger_description or f"When {emotion_type} > {threshold}",
            'created_at': datetime.now(),
            'enabled': True,
            'last_triggered': None,
            'trigger_count': 0
        }
        
        advanced_scheduler.emotional_triggers[task_id] = trigger_data
        
        return (f"✅ Emotional trigger scheduled!\n"
               f"🧠 Emotion: {emotion_type}\n"
               f"📊 Threshold: {threshold}\n"
               f"🛠️ Action: {action_tool}\n"
               f"📝 Parameters: {action_parameters}\n"
               f"🆔 ID: {task_id}\n"
               f"📋 Description: {trigger_data['description']}")
               
    except Exception as e:
        return f"❌ Failed to schedule emotional trigger: {str(e)}"

@function_tool()
async def schedule_conditional_task(
    condition: str,
    action_tool: str,
    action_parameters: str = "",
    time_window: str = "always",
    task_description: str = ""
) -> str:
    """
    Schedule tasks that execute when specific conditions are met.
    
    Examples:
    - "focus_level < 0.3", "manual_emotional_intervention", "gentle", "9 AM - 5 PM", "Low focus intervention"
    - "screen_time > 120", "desktop_control", "show", "", "After 2 hours of screen time"
    - "battery < 20", "system_power_action", "lock", "", "Low battery protection"
    
    Args:
        condition: Python-like condition (e.g., "focus_level < 0.3")
        action_tool: Tool to execute when condition is met
        action_parameters: Parameters for the action tool
        time_window: When this condition is checked (e.g., "9 AM - 5 PM", "always")
        task_description: Description of the conditional task
    """
    try:
        # Generate task ID
        task_id = f"cond_task_{advanced_scheduler.task_counter}"
        advanced_scheduler.task_counter += 1
        
        # Store conditional task
        task_data = {
            'id': task_id,
            'condition': condition,
            'action_tool': action_tool,
            'action_parameters': action_parameters,
            'time_window': time_window,
            'description': task_description or f"When {condition}",
            'created_at': datetime.now(),
            'enabled': True,
            'last_triggered': None,
            'trigger_count': 0
        }
        
        advanced_scheduler.conditional_tasks[task_id] = task_data
        
        return (f"✅ Conditional task scheduled!\n"
               f"🔍 Condition: {condition}\n"
               f"⏰ Time Window: {time_window}\n"
               f"🛠️ Action: {action_tool}\n"
               f"📝 Parameters: {action_parameters}\n"
               f"🆔 ID: {task_id}\n"
               f"📋 Description: {task_data['description']}")
               
    except Exception as e:
        return f"❌ Failed to schedule conditional task: {str(e)}"

@function_tool()
async def list_advanced_schedules() -> str:
    """List all advanced scheduled tasks including cron jobs, emotional triggers, and conditional tasks"""
    try:
        output_parts = []
        
        # Cron jobs and recurring tasks
        if advanced_scheduler.cron_jobs:
            output_parts.append("🔄 **Recurring Tasks (Cron Jobs):**")
            for task_id, task in advanced_scheduler.cron_jobs.items():
                status = "✅ Active" if task['enabled'] else "❌ Disabled"
                output_parts.append(
                    f"🆔 {task_id} - {status}\n"
                    f"📝 {task['description']}\n"
                    f"⏰ {task['schedule_config']['description']}\n"
                    f"🛠️ {task['tool_name']}\n"
                )
        else:
            output_parts.append("🔄 **No recurring tasks scheduled**")
        
        # Emotional triggers
        if advanced_scheduler.emotional_triggers:
            output_parts.append("\n🧠 **Emotional Triggers:**")
            for task_id, trigger in advanced_scheduler.emotional_triggers.items():
                status = "✅ Active" if trigger['enabled'] else "❌ Disabled"
                trigger_count = trigger.get('trigger_count', 0)
                output_parts.append(
                    f"🆔 {task_id} - {status}\n"
                    f"🧠 Emotion: {trigger['emotion_type']} > {trigger['threshold']}\n"
                    f"📋 Description: {trigger['description']}\n"
                    f"🛠️ Action: {trigger['action_tool']}\n"
                    f"📊 Triggered: {trigger_count} times\n"
                )
        else:
            output_parts.append("\n🧠 **No emotional triggers scheduled**")
        
        # Conditional tasks
        if advanced_scheduler.conditional_tasks:
            output_parts.append("\n🔍 **Conditional Tasks:**")
            for task_id, task in advanced_scheduler.conditional_tasks.items():
                status = "✅ Active" if task['enabled'] else "❌ Disabled"
                trigger_count = task.get('trigger_count', 0)
                output_parts.append(
                    f"🆔 {task_id} - {status}\n"
                    f"🔍 Condition: {task['condition']}\n"
                    f"⏰ Window: {task['time_window']}\n"
                    f"📋 Description: {task['description']}\n"
                    f"🛠️ Action: {task['action_tool']}\n"
                    f"📊 Triggered: {trigger_count} times\n"
                )
        else:
            output_parts.append("\n🔍 **No conditional tasks scheduled**")
        
        return "\n".join(output_parts)
        
    except Exception as e:
        return f"❌ Failed to list advanced schedules: {str(e)}"

@function_tool()
async def cancel_advanced_task(task_id: str) -> str:
    """Cancel an advanced scheduled task by ID"""
    try:
        # Check cron jobs
        if task_id in advanced_scheduler.cron_jobs:
            del advanced_scheduler.cron_jobs[task_id]
            return f"✅ Recurring task {task_id} cancelled"
        
        # Check emotional triggers
        if task_id in advanced_scheduler.emotional_triggers:
            del advanced_scheduler.emotional_triggers[task_id]
            return f"✅ Emotional trigger {task_id} cancelled"
        
        # Check conditional tasks
        if task_id in advanced_scheduler.conditional_tasks:
            del advanced_scheduler.conditional_tasks[task_id]
            return f"✅ Conditional task {task_id} cancelled"
        
        # Check one-time tasks
        if task_id in advanced_scheduler.one_time_tasks:
            del advanced_scheduler.one_time_tasks[task_id]
            return f"✅ One-time task {task_id} cancelled"
        
        return f"❌ Task {task_id} not found"
        
    except Exception as e:
        return f"❌ Failed to cancel task: {str(e)}"

@function_tool()
async def enable_disable_task(task_id: str, enabled: bool = True) -> str:
    """Enable or disable an advanced scheduled task"""
    try:
        action = "enabled" if enabled else "disabled"
        
        # Check and update cron jobs
        if task_id in advanced_scheduler.cron_jobs:
            advanced_scheduler.cron_jobs[task_id]['enabled'] = enabled
            return f"✅ Recurring task {task_id} {action}"
        
        # Check and update emotional triggers
        if task_id in advanced_scheduler.emotional_triggers:
            advanced_scheduler.emotional_triggers[task_id]['enabled'] = enabled
            return f"✅ Emotional trigger {task_id} {action}"
        
        # Check and update conditional tasks
        if task_id in advanced_scheduler.conditional_tasks:
            advanced_scheduler.conditional_tasks[task_id]['enabled'] = enabled
            return f"✅ Conditional task {task_id} {action}"
        
        return f"❌ Task {task_id} not found"
        
    except Exception as e:
        return f"❌ Failed to {action} task: {str(e)}"