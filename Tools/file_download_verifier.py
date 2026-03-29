"""
MJ Remote AI - File Download Verifier Core Module
Handles file download verification and tracking functionality
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import glob

class FileDownloadVerifier:
    def __init__(self):
        self.tasks = {}
        self.data_file = os.path.join(os.path.dirname(__file__), 'download_tasks.json')
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.tasks = json.load(f)
        except Exception as e:
            logging.error(f"Error loading tasks: {e}")
            self.tasks = {}
    
    def save_tasks(self):
        """Save tasks to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving tasks: {e}")
    
    def register_download_task(self, task_id: str, file_list: List[str], source: str) -> str:
        """Register a new download task"""
        try:
            self.tasks[task_id] = {
                'task_id': task_id,
                'files': file_list,
                'source': source,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'completed_files': 0,
                'total_files': len(file_list),
                'file_status': {file: 'pending' for file in file_list}
            }
            self.save_tasks()
            return f"✅ Download task registered successfully with {len(file_list)} files"
        except Exception as e:
            return f"❌ Error registering task: {str(e)}"
    
    async def verify_downloads(self, task_id: str) -> Dict[str, Any]:
        """Verify if all files in a download task are completed"""
        try:
            if task_id not in self.tasks:
                return {'success': False, 'error': 'Task not found'}
            
            task = self.tasks[task_id]
            search_paths = self._get_search_paths()
            
            completed_files = 0
            missing_files = []
            failed_files = []
            
            for file_name in task['files']:
                file_found = False
                file_path = None
                
                # Search in all common download locations
                for path in search_paths:
                    search_pattern = os.path.join(path, '**', file_name)
                    matches = glob.glob(search_pattern, recursive=True)
                    
                    if matches:
                        # Use the first match
                        file_path = matches[0]
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            file_found = True
                            task['file_status'][file_name] = 'completed'
                            completed_files += 1
                            break
                
                if not file_found:
                    missing_files.append({'name': file_name, 'error': 'File not found'})
                    task['file_status'][file_name] = 'missing'
            
            # Update task status
            task['completed_files'] = completed_files
            task['status'] = 'completed' if completed_files == task['total_files'] else 'incomplete'
            task['verified_at'] = datetime.now().isoformat()
            self.save_tasks()
            
            success_rate = (completed_files / task['total_files']) * 100 if task['total_files'] > 0 else 0
            
            return {
                'success': True,
                'task_id': task_id,
                'total_files': task['total_files'],
                'completed_files': completed_files,
                'missing_files': missing_files,
                'failed_files': failed_files,
                'success_rate': success_rate,
                'is_complete': completed_files == task['total_files']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_download_status(self, task_id: str) -> Dict[str, Any]:
        """Get current status of a download task"""
        try:
            if task_id not in self.tasks:
                return {'success': False, 'error': 'Task not found'}
            
            task = self.tasks[task_id]
            return {
                'success': True,
                'task_id': task['task_id'],
                'status': task['status'],
                'source': task['source'],
                'total_files': task['total_files'],
                'completed_files': task.get('completed_files', 0),
                'files': task['files'],
                'created_at': task.get('created_at'),
                'verified_at': task.get('verified_at')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active download tasks"""
        try:
            active_tasks = []
            for task_id, task in self.tasks.items():
                if task['status'] in ['pending', 'incomplete']:
                    active_tasks.append({
                        'task_id': task_id,
                        'status': task['status'],
                        'total_files': task['total_files'],
                        'source': task['source']
                    })
            return active_tasks
        except Exception as e:
            logging.error(f"Error listing tasks: {e}")
            return []
    
    def _get_search_paths(self) -> List[str]:
        """Get common download and file locations"""
        paths = []
        
        # User-specific paths
        home = os.path.expanduser("~")
        paths.extend([
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Videos"),
            os.path.join(home, "Music"),
        ])
        
        # Windows-specific paths
        if os.name == 'nt':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    downloads = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
                    paths.append(downloads)
            except:
                pass
            
            # Add common Windows paths
            paths.extend([
                r"C:\Users\Public\Downloads",
                r"C:\Temp",
                r"C:\tmp"
            ])
        
        # Current directory and project directories
        paths.extend([
            os.getcwd(),
            os.path.dirname(__file__),
        ])
        
        # Filter only existing paths
        return [path for path in paths if os.path.exists(path)]

# Create global instance
file_verifier = FileDownloadVerifier()
