"""
Task Completion Monitor with Shutdown/Lock Capabilities
Monitors tasks every 5 seconds and executes shutdown/lock commands upon completion
"""

import asyncio
import os
import time
import json
import logging
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from dataclasses import dataclass, field
from livekit.agents import function_tool
from livekit.agents import RunContext

@dataclass
class MonitoredTask:
    """Represents a task being monitored"""
    task_id: str
    description: str
    check_function: Callable[[], bool]  # Returns True when task is complete
    after_command: str  # 'shutdown' or 'lock'
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    completion_message: Optional[str] = None

class TaskCompletionMonitor:
    """Monitors tasks and executes system commands upon completion"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or Path("json/task_monitor.json")
        self.tasks: Dict[str, MonitoredTask] = {}
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
        # Ensure storage directory exists
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing tasks
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        # Convert datetime strings back to datetime objects
                        task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
                        # Note: check_function cannot be serialized, so we'll skip active tasks
                        task_data['check_function'] = None
                        task_data['is_active'] = False  # Mark as inactive since check_function is missing
                        task = MonitoredTask(**task_data)
                        self.tasks[task.task_id] = task
        except Exception as e:
            self.logger.warning(f"Failed to load tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to storage"""
        try:
            data = {
                'tasks': []
            }
            for task in self.tasks.values():
                task_dict = {
                    'task_id': task.task_id,
                    'description': task.description,
                    'after_command': task.after_command,
                    'created_at': task.created_at.isoformat(),
                    'is_active': task.is_active,
                    'completion_message': task.completion_message
                }
                data['tasks'].append(task_dict)
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
    
    def add_task(self, 
                 task_id: str, 
                 description: str, 
                 check_function: Callable[[], bool], 
                 after_command: str,
                 completion_message: Optional[str] = None) -> bool:
        """Add a new task to monitor"""
        if after_command not in ['shutdown', 'lock']:
            raise ValueError("after_command must be 'shutdown' or 'lock'")
        
        task = MonitoredTask(
            task_id=task_id,
            description=description,
            check_function=check_function,
            after_command=after_command,
            completion_message=completion_message
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        # Start monitor if not running
        if not self.is_running:
            asyncio.create_task(self.start_monitoring())
        
        self.logger.info(f"Added task: {task_id} - {description}")
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from monitoring"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            self.logger.info(f"Removed task: {task_id}")
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                'task_id': task.task_id,
                'description': task.description,
                'after_command': task.after_command,
                'created_at': task.created_at.isoformat(),
                'is_active': task.is_active,
                'completion_message': task.completion_message
            }
        return None
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active tasks"""
        return [self.get_task_status(task_id) for task_id in self.tasks if self.tasks[task_id].is_active]
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("Task completion monitor started")
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Task completion monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop - checks tasks every 5 seconds"""
        while self.is_running:
            try:
                completed_tasks = []
                
                for task_id, task in self.tasks.items():
                    if not task.is_active or not task.check_function:
                        continue
                    
                    try:
                        # Check if task is complete
                        if task.check_function():
                            completed_tasks.append(task)
                            self.logger.info(f"Task completed: {task_id} - {task.description}")
                    except Exception as e:
                        self.logger.error(f"Error checking task {task_id}: {e}")
                        # Deactivate problematic task
                        task.is_active = False
                
                # Execute after commands for completed tasks
                for task in completed_tasks:
                    await self._execute_after_command(task)
                    task.is_active = False
                
                # Save updated status
                if completed_tasks:
                    self._save_tasks()
                
                # Wait 5 seconds before next check
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    async def _execute_after_command(self, task: MonitoredTask):
        """Execute the after command (shutdown/lock)"""
        try:
            # Announce completion if message provided
            if task.completion_message:
                print(f"🎯 Task Monitor: {task.completion_message}")
            
            if task.after_command == 'shutdown':
                await self._shutdown_pc()
            elif task.after_command == 'lock':
                await self._lock_pc()
                
        except Exception as e:
            self.logger.error(f"Error executing after command for task {task.task_id}: {e}")
    
    async def _shutdown_pc(self):
        """Shutdown the PC"""
        print("🔴 Task Monitor: Shutting down PC in 30 seconds...")
        print("💡 To cancel: run 'shutdown /a' in Command Prompt")
        
        # Windows shutdown command with 30 second delay
        subprocess.run(['shutdown', '/s', '/t', '30'], check=False)
    
    async def _lock_pc(self):
        """Lock the PC"""
        print("🔒 Task Monitor: Locking PC now...")
        
        # Windows lock command
        subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)

# Global monitor instance
_task_monitor: Optional[TaskCompletionMonitor] = None

def get_task_monitor() -> TaskCompletionMonitor:
    """Get the global task monitor instance"""
    global _task_monitor
    if _task_monitor is None:
        _task_monitor = TaskCompletionMonitor()
    return _task_monitor

# =========================
# BUILT-IN TASK CHECKERS
# =========================

def create_file_exists_checker(file_path: str) -> Callable[[], bool]:
    """Create a checker that waits for a file to exist"""
    def check_file_exists() -> bool:
        return os.path.exists(file_path)
    return check_file_exists

def create_file_size_checker(file_path: str, target_size: int) -> Callable[[], bool]:
    """Create a checker that waits for a file to reach target size"""
    def check_file_size() -> bool:
        if not os.path.exists(file_path):
            return False
        return os.path.getsize(file_path) >= target_size
    return check_file_size

def create_process_not_running_checker(process_name: str) -> Callable[[], bool]:
    """Create a checker that waits for a process to stop running"""
    def check_process_not_running() -> bool:
        try:
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], 
                                  capture_output=True, text=True)
            return process_name not in result.stdout
        except:
            return True  # Assume not running if error occurs
    return check_process_not_running

def create_download_complete_checker(download_folder: str, file_pattern: str) -> Callable[[], bool]:
    """Create a checker that waits for downloads to complete (no .crdownload/.tmp files)"""
    def check_download_complete() -> bool:
        try:
            download_path = Path(download_folder)
            if not download_path.exists():
                return False
            
            # Check for temporary download files
            temp_extensions = ['.crdownload', '.tmp', '.part', '.download']
            for file_path in download_path.glob(file_pattern):
                if any(file_path.suffix.lower() == ext for ext in temp_extensions):
                    return False
            
            # Check if at least one matching file exists
            return any(download_path.glob(file_pattern))
        except:
            return False
    return check_download_complete

def create_cpu_usage_checker(threshold: float = 10.0, duration_seconds: int = 60) -> Callable[[], bool]:
    """Create a checker that waits for CPU usage to drop below threshold for specified duration"""
    start_time = None
    
    def check_cpu_usage() -> bool:
        nonlocal start_time
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent < threshold:
                if start_time is None:
                    start_time = time.time()
                elif time.time() - start_time >= duration_seconds:
                    return True
            else:
                start_time = None
            
            return False
        except ImportError:
            # Fallback: just return True after a delay
            return True
        except:
            return False
    
    return check_cpu_usage

# =========================
# TOOL FUNCTIONS
# =========================

@function_tool()
async def monitor_task_completion(context: RunContext, task_id: str, description: str, check_type: str, after_command: str, 
                          check_params: Dict[str, Any], completion_message: Optional[str] = None) -> str:
    """
    Monitor a task and execute shutdown/lock upon completion
    
    Args:
        task_id: Unique identifier for the task
        description: Human-readable description of the task
        check_type: Type of check ('file_exists', 'file_size', 'process_not_running', 'download_complete', 'cpu_usage')
        after_command: 'shutdown' or 'lock'
        check_params: Parameters for the check function
        completion_message: Message to display when task completes
    
    Returns:
        Success message
    """
    monitor = get_task_monitor()
    
    # Create appropriate check function
    if check_type == 'file_exists':
        check_function = create_file_exists_checker(check_params['file_path'])
    elif check_type == 'file_size':
        check_function = create_file_size_checker(check_params['file_path'], check_params['target_size'])
    elif check_type == 'process_not_running':
        check_function = create_process_not_running_checker(check_params['process_name'])
    elif check_type == 'download_complete':
        check_function = create_download_complete_checker(check_params['download_folder'], check_params['file_pattern'])
    elif check_type == 'cpu_usage':
        check_function = create_cpu_usage_checker(
            check_params.get('threshold', 10.0), 
            check_params.get('duration_seconds', 60)
        )
    else:
        return f"❌ Unknown check type: {check_type}"
    
    try:
        monitor.add_task(task_id, description, check_function, after_command, completion_message)
        return f"✅ Task monitoring started: {description}\n📍 Task ID: {task_id}\n🎯 After completion: {after_command}"
    except Exception as e:
        return f"❌ Failed to start task monitoring: {str(e)}"

@function_tool()
async def stop_task_monitoring(context: RunContext, task_id: str) -> str:
    """Stop monitoring a specific task"""
    monitor = get_task_monitor()
    if monitor.remove_task(task_id):
        return f"✅ Stopped monitoring task: {task_id}"
    else:
        return f"❌ Task not found: {task_id}"

@function_tool()
async def get_monitoring_status(context: RunContext, task_id: Optional[str] = None) -> str:
    """Get status of task monitoring"""
    monitor = get_task_monitor()
    
    if task_id:
        status = monitor.get_task_status(task_id)
        if status:
            return f"📊 Task Status:\n📍 ID: {status['task_id']}\n📝 Description: {status['description']}\n🎯 After: {status['after_command']}\n✅ Active: {status['is_active']}\n🕐 Created: {status['created_at']}"
        else:
            return f"❌ Task not found: {task_id}"
    else:
        active_tasks = monitor.list_active_tasks()
        if active_tasks:
            lines = ["📊 Active Tasks:"]
            for task in active_tasks:
                lines.append(f"📍 {task['task_id']}: {task['description']} → {task['after_command']}")
            return "\n".join(lines)
        else:
            return "📊 No active tasks being monitored"

@function_tool()
async def cancel_all_monitoring(context: RunContext) -> str:
    """Cancel all active task monitoring"""
    monitor = get_task_monitor()
    count = len([t for t in monitor.tasks.values() if t.is_active])
    
    # Deactivate all tasks
    for task in monitor.tasks.values():
        task.is_active = False
    
    monitor._save_tasks()
    return f"✅ Cancelled monitoring for {count} tasks"
