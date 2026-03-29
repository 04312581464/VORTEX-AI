import asyncio
import random
import time
import threading
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from livekit.agents import function_tool

class DynamicExecutor:
    """Handles dynamic task execution beyond static tools"""
    
    def __init__(self):
        self.active_tasks = {}
        self.task_history = []
        self.running = True
        
    def execute_dynamic_command(self, command: str) -> str:
        """Execute dynamic commands based on natural language"""
        try:
            command = command.strip().lower()
            
            # Random number generation
            if "random number" in command and "every" in command:
                return self._handle_random_number_sequence(command)
            
            # Countdown timer
            elif "countdown" in command or "timer" in command:
                return self._handle_countdown(command)
            
            # Repeated actions
            elif "repeat" in command or "every" in command:
                return self._handle_repeated_action(command)
            
            # Math operations
            elif any(op in command for op in ["calculate", "compute", "solve"]):
                return self._handle_math_operation(command)
            
            # Time-based operations
            elif "wait" in command or "delay" in command:
                return self._handle_delay(command)
            
            # File operations
            elif any(op in command for op in ["create file", "write file", "save"]):
                return self._handle_file_operation(command)
            
            # System monitoring
            elif "monitor" in command or "track" in command:
                return self._handle_monitoring(command)
            
            else:
                return f"🤔 I'm not sure how to execute: '{command}'. Try: 'Give me a random number from 0 to 6 every 3 seconds'"
                
        except Exception as e:
            return f"❌ Error executing dynamic command: {str(e)}"
    
    def _handle_random_number_sequence(self, command: str) -> str:
        """Handle random number generation with intervals"""
        try:
            # Extract range: "random number from 0 to 6"
            range_match = re.search(r'random number from (\d+) to (\d+)', command)
            if not range_match:
                return "❌ Please specify range like: 'random number from 0 to 6'"
            
            min_val, max_val = int(range_match.group(1)), int(range_match.group(2))
            
            # Extract interval: "every 3 seconds" or "every 5 minutes"
            interval_match = re.search(r'every (\d+) (\w+)', command)
            if not interval_match:
                return "❌ Please specify interval like: 'every 3 seconds'"
            
            interval_val, interval_unit = int(interval_match.group(1)), interval_match.group(2)
            
            # Convert to seconds
            unit_multipliers = {'second': 1, 'seconds': 1, 'minute': 60, 'minutes': 60, 'hour': 3600, 'hours': 3600}
            interval_seconds = interval_val * unit_multipliers.get(interval_unit[:-1] if interval_unit.endswith('s') else interval_unit, 1)
            
            # Start background task
            task_id = f"random_{min_val}_{max_val}_{int(time.time())}"
            self.active_tasks[task_id] = {
                'type': 'random_numbers',
                'min': min_val,
                'max': max_val,
                'interval': interval_seconds,
                'start_time': datetime.now(),
                'count': 0
            }
            
            # Start background thread
            threading.Thread(target=self._random_number_worker, args=(task_id,), daemon=True).start()
            
            return f"🎲 Started generating random numbers from {min_val} to {max_val} every {interval_val} {interval_unit}. Task ID: {task_id}"
            
        except Exception as e:
            return f"❌ Error setting up random number generation: {str(e)}"
    
    def _random_number_worker(self, task_id: str):
        """Background worker for random number generation"""
        task = self.active_tasks.get(task_id)
        if not task:
            return
        
        while task_id in self.active_tasks and self.running:
            try:
                # Generate random number
                num = random.randint(task['min'], task['max'])
                task['count'] += 1
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"🎲 [{timestamp}] Random #{task['count']}: {num}")
                
                # Store in history
                self.task_history.append({
                    'task_id': task_id,
                    'timestamp': timestamp,
                    'type': 'random_number',
                    'value': num,
                    'count': task['count']
                })
                
                # Wait for next iteration
                time.sleep(task['interval'])
                
            except Exception as e:
                print(f"❌ Error in random number worker: {e}")
                break
    
    def _handle_countdown(self, command: str) -> str:
        """Handle countdown timers"""
        try:
            # Extract time: "countdown 30 seconds" or "timer 5 minutes"
            time_match = re.search(r'(?:countdown|timer) (\d+) (\w+)', command)
            if not time_match:
                return "❌ Please specify time like: 'countdown 30 seconds'"
            
            time_val, time_unit = int(time_match.group(1)), time_match.group(2)
            
            # Convert to seconds
            unit_multipliers = {'second': 1, 'seconds': 1, 'minute': 60, 'minutes': 60, 'hour': 3600, 'hours': 3600}
            total_seconds = time_val * unit_multipliers.get(time_unit[:-1] if time_unit.endswith('s') else time_unit, 1)
            
            # Start countdown
            task_id = f"countdown_{int(time.time())}"
            threading.Thread(target=self._countdown_worker, args=(task_id, total_seconds, time_val, time_unit), daemon=True).start()
            
            return f"⏰ Started {time_val} {time_unit} countdown. Task ID: {task_id}"
            
        except Exception as e:
            return f"❌ Error starting countdown: {str(e)}"
    
    def _handle_repeated_action(self, command: str) -> str:
        """Handle repeated actions (fallback to random number handler)"""
        # For now, redirect to random number handler if it contains "every"
        if "every" in command:
            return self._handle_random_number_sequence(command)
        return "❌ Unsupported repeated action format"
    
    def _countdown_worker(self, task_id: str, total_seconds: int, original_val: int, original_unit: str):
        """Background worker for countdown"""
        remaining = total_seconds
        
        while remaining > 0 and self.running:
            mins, secs = divmod(remaining, 60)
            hours, mins = divmod(mins, 60)
            
            if hours > 0:
                time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            else:
                time_str = f"{mins:02d}:{secs:02d}"
            
            print(f"⏰ Countdown: {time_str} remaining")
            
            time.sleep(1)
            remaining -= 1
        
        if remaining <= 0:
            print(f"🎯 Countdown completed! {original_val} {original_unit} finished!")
            self.task_history.append({
                'task_id': task_id,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'type': 'countdown_complete',
                'duration': f"{original_val} {original_unit}"
            })
    
    def _handle_math_operation(self, command: str) -> str:
        """Handle mathematical calculations"""
        try:
            # Extract math expression
            math_match = re.search(r'(?:calculate|compute|solve) (.+)', command)
            if not math_match:
                return "❌ Please provide an expression like: 'calculate 2 + 3 * 4'"
            
            expression = math_match.group(1).strip()
            
            # Safe math evaluation
            allowed_chars = set('0123456789+-*/().^ ')
            if not all(c in allowed_chars for c in expression):
                return "❌ Invalid characters in math expression"
            
            # Replace ^ with ** for exponentiation
            expression = expression.replace('^', '**')
            
            result = eval(expression)
            return f"🧮 {expression} = {result}"
            
        except Exception as e:
            return f"❌ Error calculating: {str(e)}"
    
    def _handle_delay(self, command: str) -> str:
        """Handle wait/delay operations"""
        try:
            # Extract delay time
            delay_match = re.search(r'(?:wait|delay) (\d+) (\w+)', command)
            if not delay_match:
                return "❌ Please specify time like: 'wait 5 seconds'"
            
            delay_val, delay_unit = int(delay_match.group(1)), delay_match.group(2)
            
            # Convert to seconds
            unit_multipliers = {'second': 1, 'seconds': 1, 'minute': 60, 'minutes': 60}
            delay_seconds = delay_val * unit_multipliers.get(delay_unit[:-1] if delay_unit.endswith('s') else delay_unit, 1)
            
            print(f"⏳ Waiting {delay_val} {delay_unit}...")
            time.sleep(delay_seconds)
            print(f"✅ Finished waiting {delay_val} {delay_unit}")
            
            return f"✅ Waited {delay_val} {delay_unit} successfully"
            
        except Exception as e:
            return f"❌ Error during delay: {str(e)}"
    
    def _handle_file_operation(self, command: str) -> str:
        """Handle basic file operations"""
        try:
            # Extract filename and content
            if "create file" in command:
                filename_match = re.search(r'create file ["\']?([^"\']+)["\']?', command)
                if not filename_match:
                    return "❌ Please specify filename like: 'create file test.txt'"
                
                filename = filename_match.group(1)
                content_match = re.search(r'with content ["\']([^"\']*)["\']', command)
                content = content_match.group(1) if content_match else f"Created at {datetime.now()}"
                
                with open(filename, 'w') as f:
                    f.write(content)
                
                return f"📝 Created file '{filename}' with content: {content}"
            
            return "❌ Unsupported file operation"
            
        except Exception as e:
            return f"❌ Error with file operation: {str(e)}"
    
    def _handle_monitoring(self, command: str) -> str:
        """Handle system monitoring tasks"""
        try:
            if "monitor cpu" in command:
                import psutil
                task_id = f"cpu_monitor_{int(time.time())}"
                threading.Thread(target=self._cpu_monitor_worker, args=(task_id,), daemon=True).start()
                return f"📊 Started CPU monitoring. Task ID: {task_id}"
            
            elif "monitor memory" in command:
                import psutil
                task_id = f"memory_monitor_{int(time.time())}"
                threading.Thread(target=self._memory_monitor_worker, args=(task_id,), daemon=True).start()
                return f"💾 Started memory monitoring. Task ID: {task_id}"
            
            return "❌ Please specify what to monitor: 'monitor cpu' or 'monitor memory'"
            
        except Exception as e:
            return f"❌ Error starting monitoring: {str(e)}"
    
    def _cpu_monitor_worker(self, task_id: str):
        """Background CPU monitoring"""
        import psutil
        
        while task_id in self.active_tasks and self.running:
            cpu_percent = psutil.cpu_percent(interval=1)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"📊 [{timestamp}] CPU Usage: {cpu_percent:.1f}%")
            
            self.task_history.append({
                'task_id': task_id,
                'timestamp': timestamp,
                'type': 'cpu_monitor',
                'value': cpu_percent
            })
            
            time.sleep(5)  # Update every 5 seconds
    
    def _memory_monitor_worker(self, task_id: str):
        """Background memory monitoring"""
        import psutil
        
        while task_id in self.active_tasks and self.running:
            memory = psutil.virtual_memory()
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"💾 [{timestamp}] Memory Usage: {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f}GB used)")
            
            self.task_history.append({
                'task_id': task_id,
                'timestamp': timestamp,
                'type': 'memory_monitor',
                'value': memory.percent
            })
            
            time.sleep(5)  # Update every 5 seconds
    
    def stop_task(self, task_id: str) -> str:
        """Stop a running task"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            return f"🛑 Stopped task: {task_id}"
        return f"❌ Task not found: {task_id}"
    
    def list_active_tasks(self) -> str:
        """List all active tasks"""
        if not self.active_tasks:
            return "📋 No active tasks running"
        
        result = "📋 Active Tasks:\n"
        for task_id, task in self.active_tasks.items():
            task_type = task.get('type', 'unknown')
            start_time = task.get('start_time', datetime.now())
            elapsed = (datetime.now() - start_time).total_seconds()
            
            result += f"  • {task_id} ({task_type}) - Running for {elapsed:.1f}s\n"
        
        return result
    
    def get_task_history(self, limit: int = 10) -> str:
        """Get recent task history"""
        if not self.task_history:
            return "📜 No task history"
        
        recent = self.task_history[-limit:]
        result = f"📜 Recent Task History (last {len(recent)}):\n"
        
        for entry in recent:
            timestamp = entry.get('timestamp', 'Unknown')
            task_type = entry.get('type', 'unknown')
            value = entry.get('value', 'N/A')
            result += f"  • [{timestamp}] {task_type}: {value}\n"
        
        return result

# Global instance
dynamic_executor = DynamicExecutor()

# LiveKit-compatible tool functions with proper decorators
@function_tool()
def dynamic_executor_tool(command: str) -> str:
    """
    Execute dynamic commands beyond static tools.
    
    Args:
        command (str): The natural language command to execute
        
    Returns:
        str: Result of the dynamic command execution
    """
    return dynamic_executor.execute_dynamic_command(command)

@function_tool()
def stop_dynamic_task(task_id: str) -> str:
    """
    Stop a running dynamic task by ID.
    
    Args:
        task_id (str): The ID of the task to stop
        
    Returns:
        str: Result of stopping the task
    """
    return dynamic_executor.stop_task(task_id)

@function_tool()
def list_dynamic_tasks() -> str:
    """
    List all currently running dynamic tasks.
    
    Returns:
        str: List of active tasks with their details
    """
    return dynamic_executor.list_active_tasks()

@function_tool()
def get_dynamic_history() -> str:
    """
    Get history of dynamic task executions.
    
    Returns:
        str: Recent task execution history
    """
    return dynamic_executor.get_task_history()
