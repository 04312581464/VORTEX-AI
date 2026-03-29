"""
Smart Task Monitor - Natural Language Interface for Task Completion Monitoring
Provides intelligent parsing of natural language requests for task monitoring
"""

import re
import json
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from livekit.agents import function_tool
from livekit.agents import RunContext

from .task_completion_monitor import monitor_task_completion, get_monitoring_status, stop_task_monitoring

class SmartTaskMonitor:
    """Natural language interface for task monitoring"""
    
    def __init__(self):
        self.patterns = {
            # Shutdown patterns
            'shutdown_after': [
                r'(?i)(?:after|when|once)\s+(.+?)\s+(?:completes?|finishes?|done?)(?:\s*,? then?)?\s+shutdown',
                r'(?i)(?:monitor|watch)\s+(.+?)\s+and\s+shutdown',
                r'(?i)(.+?)\s+(?:completes?|finishes?|done?)\s+(?:then\s+)?shutdown',
                r'(?i)shutdown\s+(?:after|when|once)\s+(.+?)(?:\s+completes?|\s+finishes?|\s+done?)',
            ],
            
            # Lock patterns
            'lock_after': [
                r'(?i)(?:after|when|once)\s+(.+?)\s+(?:completes?|finishes?|done?)(?:\s*,? then?)?\s+lock',
                r'(?i)(?:monitor|watch)\s+(.+?)\s+and\s+lock',
                r'(?i)(.+?)\s+(?:completes?|finishes?|done?)\s+(?:then\s+)?lock',
                r'(?i)lock\s+(?:after|when|once)\s+(.+?)(?:\s+completes?|\s+finishes?|\s+done?)',
                r'(?i)lock\s+(?:the\s+)?computer\s+(?:when|after)\s+(.+?)(?:\s+completes?|\s+finishes?|\s+done?)',
            ],
            
            # Status check patterns
            'check_status': [
                r'(?i)(?:check|show|get)\s+(?:monitoring|task)\s+status',
                r'(?i)what\s+(?:tasks?|monitoring)\s+(?:is|are)\s+(?:active|running)',
                r'(?i)monitoring\s+status',
            ],
            
            # Cancel patterns
            'cancel_monitoring': [
                r'(?i)(?:stop|cancel)\s+(?:monitoring|task)',
                r'(?i)(?:stop|cancel)\s+(?:all|everything)',
            ]
        }
        
        # Task type detection patterns
        self.task_patterns = {
            'download': [
                r'(?i)(?:download|downloading)',
                r'(?i)(?:file|files?)\s+(?:downloading|being downloaded)',
            ],
            'conversion': [
                r'(?i)(?:convert|converting|conversion)',
                r'(?i)(?:video|audio|image)\s+(?:convert|converting)',
                r'(?i)(?:ffmpeg|handbrake|convert)',
            ],
            'backup': [
                r'(?i)(?:backup|backing up)',
                r'(?i)(?:copy|copying)\s+(?:files?|data)',
            ],
            'processing': [
                r'(?i)(?:process|processing)',
                r'(?i)(?:render|rendering)',
                r'(?i)(?:compile|compiling)',
            ],
            'installation': [
                r'(?i)(?:install|installing|installation)',
                r'(?i)(?:setup|setting up)',
            ],
        }
    
    def parse_request(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse natural language request and return action and parameters
        
        Returns:
            Tuple of (action_type, parameters)
        """
        text = text.strip()
        
        # Check for shutdown patterns
        for pattern in self.patterns['shutdown_after']:
            match = re.search(pattern, text)
            if match:
                task_desc = match.group(1).strip()
                action_type, params = self._parse_task_description(task_desc, 'shutdown')
                return action_type, params
        
        # Check for lock patterns (more specific patterns first)
        for pattern in self.patterns['lock_after']:
            match = re.search(pattern, text)
            if match:
                task_desc = match.group(1).strip()
                action_type, params = self._parse_task_description(task_desc, 'lock')
                return action_type, params
        
        # Check for "when/after" patterns with lock/shutdown at end
        when_pattern = r'(?i)(?:when|after|once)\s+(.+?)\s+(?:completes?|finishes?|done?)(?:\s*,? then?)?\s+(shutdown|lock|the\s+system|the\s+pc)'
        match = re.search(when_pattern, text)
        if match:
            task_desc = match.group(1).strip()
            after_command_raw = match.group(2).strip()
            # Normalize after command
            if after_command_raw in ['shutdown', 'lock']:
                after_command = after_command_raw
            elif after_command_raw in ['the system', 'the pc']:
                after_command = 'lock'
            else:
                after_command = 'lock'
            
            action_type, params = self._parse_task_description(task_desc, after_command)
            return action_type, params
        
        # Check for "after this" pattern
        after_this_pattern = r'(?i)after\s+this\s+(.+?)\s+(?:completes?|finishes?|done?),?\s*(?:then\s+)?(shutdown|lock)'
        match = re.search(after_this_pattern, text)
        if match:
            task_desc = match.group(1).strip()
            after_command = match.group(2).strip()
            action_type, params = self._parse_task_description(task_desc, after_command)
            return action_type, params
        
        # Check for status patterns
        for pattern in self.patterns['check_status']:
            if re.search(pattern, text):
                return 'status', {}
        
        # Check for cancel patterns
        for pattern in self.patterns['cancel_monitoring']:
            if re.search(pattern, text):
                return 'cancel', {}
        
        return 'unknown', {}
    
    def _parse_task_description(self, task_desc: str, after_command: str) -> Tuple[str, Dict[str, Any]]:
        """Parse task description and determine monitoring type and parameters"""
        
        # Detect task type
        task_type = self._detect_task_type(task_desc)
        
        # Generate task ID
        task_id = f"{task_type}_{hash(task_desc) % 10000}"
        
        # Determine check type and parameters based on task description
        check_type, check_params = self._determine_check_type(task_desc, task_type)
        
        # Create completion message
        completion_message = f"✅ Task completed: {task_desc}"
        
        params = {
            'task_id': task_id,
            'description': task_desc,
            'check_type': check_type,
            'after_command': after_command,
            'check_params': check_params,
            'completion_message': completion_message
        }
        
        return 'monitor', params
    
    def _detect_task_type(self, task_desc: str) -> str:
        """Detect the type of task from description"""
        for task_type, patterns in self.task_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_desc):
                    return task_type
        return 'general'
    
    def _determine_check_type(self, task_desc: str, task_type: str) -> Tuple[str, Dict[str, Any]]:
        """Determine the best check type and parameters for the task"""
        
        # Look for file paths in the description
        file_path_match = re.search(r'([A-Za-z]:\\[^\\s]+|/[^\\s]+)', task_desc)
        if file_path_match:
            file_path = file_path_match.group(1)
            
            # Check for size requirements
            size_match = re.search(r'(\d+)\s*(?:GB|MB|KB)', task_desc, re.IGNORECASE)
            if size_match:
                size_value = int(size_match.group(1))
                size_unit = size_match.group(2).upper()
                
                # Convert to bytes
                if size_unit == 'GB':
                    target_size = size_value * 1024 * 1024 * 1024
                elif size_unit == 'MB':
                    target_size = size_value * 1024 * 1024
                else:  # KB
                    target_size = size_value * 1024
                
                return 'file_size', {'file_path': file_path, 'target_size': target_size}
            else:
                return 'file_exists', {'file_path': file_path}
        
        # Look for process names
        process_match = re.search(r'([a-zA-Z0-9_\-]+\.exe|[a-zA-Z0-9_\-]+)', task_desc)
        if process_match and task_type in ['conversion', 'processing', 'installation']:
            process_name = process_match.group(1)
            if not process_name.endswith('.exe'):
                process_name += '.exe'
            return 'process_not_running', {'process_name': process_name}
        
        # Task-specific defaults
        if task_type == 'download':
            # Try to detect download folder
            download_folder = self._detect_download_folder(task_desc)
            return 'download_complete', {
                'download_folder': download_folder,
                'file_pattern': '*'
            }
        
        if task_type in ['conversion', 'processing']:
            return 'cpu_usage', {'threshold': 10.0, 'duration_seconds': 60}
        
        # Default to CPU usage check
        return 'cpu_usage', {'threshold': 15.0, 'duration_seconds': 30}
    
    def _detect_download_folder(self, task_desc: str) -> str:
        """Try to detect download folder from description or use default"""
        # Common download folders
        download_folders = [
            str(Path.home() / "Downloads"),
            "C:/Downloads",
            "C:/Users/*/Downloads",
            "D:/Downloads"
        ]
        
        # Look for folder patterns in description
        folder_match = re.search(r'([A-Za-z]:\\[^\\s]*|/[^\\s]*)', task_desc)
        if folder_match:
            potential_folder = folder_match.group(1)
            if 'download' in potential_folder.lower():
                return potential_folder
        
        # Return default
        return download_folders[0]
    
    async def execute_request(self, text: str, context: RunContext) -> str:
        """Execute the parsed request and return response"""
        action, params = self.parse_request(text)
        
        if action == 'monitor':
            try:
                result = await monitor_task_completion(
                    context,
                    params['task_id'],
                    params['description'],
                    params['check_type'],
                    params['after_command'],
                    params['check_params'],
                    params['completion_message']
                )
                return result
            except Exception as e:
                return f"❌ Failed to start monitoring: {str(e)}"
        
        elif action == 'status':
            return await get_monitoring_status(context)
        
        elif action == 'cancel':
            from .task_completion_monitor import cancel_all_monitoring
            return await cancel_all_monitoring(context)
        
        else:
            return "❌ I couldn't understand your request. Try saying something like:\n• 'Monitor my download and shutdown after completion'\n• 'Lock PC when video conversion finishes'\n• 'Check monitoring status'"

# Global smart monitor instance
_smart_monitor: Optional[SmartTaskMonitor] = None

def get_smart_monitor() -> SmartTaskMonitor:
    """Get the global smart monitor instance"""
    global _smart_monitor
    if _smart_monitor is None:
        _smart_monitor = SmartTaskMonitor()
    return _smart_monitor

# =========================
# TOOL FUNCTION
# =========================

@function_tool()
async def smart_task_monitor(context: RunContext, request: str) -> str:
    """
    Smart task monitoring with natural language interface
    
    Examples:
    - "Monitor my download and shutdown after completion"
    - "Lock PC when video conversion finishes"
    - "After the backup completes, shutdown the PC"
    - "Check monitoring status"
    - "Cancel all monitoring"
    
    Args:
        request: Natural language request for task monitoring
    
    Returns:
        Response message
    """
    monitor = get_smart_monitor()
    return await monitor.execute_request(request, context)
