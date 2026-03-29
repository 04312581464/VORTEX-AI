"""
Vortex Perception System
Monitors user behavior patterns for emotional intelligence
"""

from __future__ import annotations
import json
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum
import psutil
import subprocess
import re


class ActivityType(Enum):
    """Types of user activities"""
    STUDY = "study"
    ENTERTAINMENT = "entertainment"
    SOCIAL = "social"
    WORK = "work"
    IDLE = "idle"
    DISTRACTION = "distraction"


class FocusLevel(Enum):
    """Levels of user focus"""
    DEEP_FOCUS = "deep_focus"
    MODERATE_FOCUS = "moderate_focus"
    LIGHT_FOCUS = "light_focus"
    DISTRACTED = "distracted"
    IDLE = "idle"


@dataclass
class WindowInfo:
    """Information about active window"""
    title: str
    process_name: str
    activity_type: ActivityType
    focus_level: FocusLevel
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class UserActivity:
    """User activity session"""
    start_time: str
    end_time: Optional[str]
    activity_type: ActivityType
    focus_level: FocusLevel
    window_title: str
    duration_minutes: float = 0.0
    interruption_count: int = 0


@dataclass
class BehaviorPattern:
    """User behavior patterns"""
    # Focus patterns
    avg_focus_duration: float = 0.0  # Average focus session length
    distraction_frequency: float = 0.0  # Distractions per hour
    procrastination_score: float = 0.0  # 0-1 scale
    
    # Time patterns
    productive_hours: Set[int] = field(default_factory=set)  # Hours when user is productive
    distraction_triggers: Set[str] = field(default_factory=set)  # Common distraction apps
    
    # Study patterns
    study_streak: int = 0  # Consecutive study sessions
    last_study_time: Optional[str] = None
    total_study_today: float = 0.0  # Minutes of study today
    
    # Recent activities
    recent_windows: List[WindowInfo] = field(default_factory=list)
    current_session: Optional[UserActivity] = None


class PerceptionSystem:
    """Monitors user behavior and patterns"""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path("json/perception_data.json")
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Window classification patterns
        self.study_keywords = [
            'vs code', 'visual studio', 'python', 'code', 'programming',
            'study', 'learn', 'course', 'tutorial', 'documentation',
            'stack overflow', 'github', 'git', 'terminal', 'command',
            'notepad', 'word', 'excel', 'powerpoint', 'slides'
        ]
        
        self.entertainment_keywords = [
            'youtube', 'netflix', 'prime video', 'disney+', 'hbo',
            'spotify', 'music', 'game', 'steam', 'epic games',
            'tiktok', 'instagram', 'facebook', 'twitter', 'reddit',
            'movie', 'video', 'stream', 'watch'
        ]
        
        self.social_keywords = [
            'whatsapp', 'telegram', 'discord', 'slack', 'teams',
            'messenger', 'chat', 'video call', 'zoom', 'meet'
        ]
        
        self.work_keywords = [
            'email', 'outlook', 'calendar', 'meeting', 'presentation',
            'report', 'document', 'spreadsheet', 'project', 'task'
        ]
        
        # Load behavior patterns
        self.patterns = self._load_patterns()
        self.last_check_time = time.time()
        self.current_window = None
        
        # Background monitoring
        self._monitoring_active = False
        self._monitoring_thread = None
        
    def _load_patterns(self) -> BehaviorPattern:
        """Load behavior patterns from file"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    patterns = BehaviorPattern()
                    patterns.avg_focus_duration = data.get('avg_focus_duration', 0.0)
                    patterns.distraction_frequency = data.get('distraction_frequency', 0.0)
                    patterns.procrastination_score = data.get('procrastination_score', 0.0)
                    patterns.productive_hours = set(data.get('productive_hours', []))
                    patterns.distraction_triggers = set(data.get('distraction_triggers', []))
                    patterns.study_streak = data.get('study_streak', 0)
                    patterns.last_study_time = data.get('last_study_time', None)
                    patterns.total_study_today = data.get('total_study_today', 0.0)
                    return patterns
        except Exception as e:
            pass
        
        return BehaviorPattern()
    
    def _save_patterns(self) -> None:
        """Save behavior patterns to file"""
        try:
            data = {
                'avg_focus_duration': self.patterns.avg_focus_duration,
                'distraction_frequency': self.patterns.distraction_frequency,
                'procrastination_score': self.patterns.procrastination_score,
                'productive_hours': list(self.patterns.productive_hours),
                'distraction_triggers': list(self.patterns.distraction_triggers),
                'study_streak': self.patterns.study_streak,
                'last_study_time': self.patterns.last_study_time,
                'total_study_today': self.patterns.total_study_today
            }
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
    
    def _get_active_window(self) -> Optional[WindowInfo]:
        """Get information about currently active window"""
        try:
            # Get active window title (Windows-specific)
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Add-Type -Name User32 -Namespace Win32API -PassThru -MemberDefinition \"[DllImport(\\"user32.dll\\")] public static extern bool GetForegroundWindow();\"; [DllImport(\\"user32.dll\\")] public static extern bool GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count); $hwnd = [Win32API.User32]::GetForegroundWindow(); $text = New-Object System.Text.StringBuilder(256); [Win32API.User32]::GetWindowText($hwnd, $text, 256); $text.ToString()'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_title = result.stdout.strip().lower()
                
                # Get process name
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name']:
                            process_name = proc.info['name'].lower()
                            if any(keyword in window_title for keyword in process_name.split()):
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                else:
                    process_name = "unknown"
                
                # Classify activity
                activity_type = self._classify_activity(window_title, process_name)
                focus_level = self._assess_focus_level(window_title, process_name, activity_type)
                
                return WindowInfo(
                    title=window_title,
                    process_name=process_name,
                    activity_type=activity_type,
                    focus_level=focus_level
                )
                
        except Exception as e:
            pass
        
        return None
    
    def _classify_activity(self, window_title: str, process_name: str) -> ActivityType:
        """Classify the type of activity based on window title"""
        title = window_title.lower()
        name = process_name.lower()
        combined = f"{title} {name}"
        
        # Check study keywords
        if any(keyword in combined for keyword in self.study_keywords):
            return ActivityType.STUDY
        
        # Check work keywords
        if any(keyword in combined for keyword in self.work_keywords):
            return ActivityType.WORK
        
        # Check social keywords
        if any(keyword in combined for keyword in self.social_keywords):
            return ActivityType.SOCIAL
        
        # Check entertainment keywords
        if any(keyword in combined for keyword in self.entertainment_keywords):
            return ActivityType.ENTERTAINMENT
        
        # Default to distraction if it seems non-productive
        if any(keyword in combined for keyword in ['game', 'video', 'music', 'chat']):
            return ActivityType.DISTRACTION
        
        return ActivityType.IDLE
    
    def _assess_focus_level(self, window_title: str, process_name: str, activity_type: ActivityType) -> FocusLevel:
        """Assess the user's focus level based on activity"""
        if activity_type == ActivityType.STUDY:
            # Deep focus indicators
            if any(keyword in window_title for keyword in ['code', 'terminal', 'documentation']):
                return FocusLevel.DEEP_FOCUS
            return FocusLevel.MODERATE_FOCUS
        
        elif activity_type == ActivityType.WORK:
            return FocusLevel.MODERATE_FOCUS
        
        elif activity_type in [ActivityType.ENTERTAINMENT, ActivityType.DISTRACTION]:
            return FocusLevel.DISTRACTED
        
        elif activity_type == ActivityType.SOCIAL:
            return FocusLevel.LIGHT_FOCUS
        
        return FocusLevel.IDLE
    
    def monitor_behavior(self) -> Dict:
        """Main monitoring function - called periodically"""
        current_time = time.time()
        
        # Get current window
        window_info = self._get_active_window()
        
        if window_info:
            # Update recent windows (keep last 10)
            self.patterns.recent_windows.append(window_info)
            if len(self.patterns.recent_windows) > 10:
                self.patterns.recent_windows.pop(0)
            
            # Check for activity changes
            if self.current_window:
                if self.current_window.title != window_info.title:
                    # Window changed - end previous session
                    self._end_current_session()
                    # Start new session
                    self._start_new_session(window_info)
            else:
                # Start new session
                self._start_new_session(window_info)
            
            self.current_window = window_info
        
        # Update patterns
        self._update_behavior_patterns(current_time)
        
        # Save patterns
        self._save_patterns()
        
        # Return current state for emotional engine
        return self._get_perception_summary()
    
    def _start_new_session(self, window_info: WindowInfo) -> None:
        """Start tracking a new activity session"""
        self.patterns.current_session = UserActivity(
            start_time=window_info.timestamp,
            end_time=None,
            activity_type=window_info.activity_type,
            focus_level=window_info.focus_level,
            window_title=window_info.title
        )
        
        # Update study streak
        if window_info.activity_type == ActivityType.STUDY:
            self.patterns.study_streak += 1
            self.patterns.last_study_time = window_info.timestamp
    
    def _end_current_session(self) -> None:
        """End current activity session"""
        if self.patterns.current_session:
            # Calculate duration
            start_time = datetime.fromisoformat(self.patterns.current_session.start_time.replace('Z', '+00:00'))
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds() / 60.0  # Convert to minutes
            
            self.patterns.current_session.duration_minutes = duration
            self.patterns.current_session.end_time = end_time.isoformat()
            
            # Update study time
            if self.patterns.current_session.activity_type == ActivityType.STUDY:
                self.patterns.total_study_today += duration
            
            # Update patterns based on session
            self._update_patterns_from_session(self.patterns.current_session)
            
            self.patterns.current_session = None
    
    def _update_patterns_from_session(self, session: UserActivity) -> None:
        """Update behavior patterns based on completed session"""
        # Update average focus duration
        if session.focus_level in [FocusLevel.DEEP_FOCUS, FocusLevel.MODERATE_FOCUS]:
            if self.patterns.avg_focus_duration == 0:
                self.patterns.avg_focus_duration = session.duration_minutes
            else:
                # Weighted average
                self.patterns.avg_focus_duration = (
                    self.patterns.avg_focus_duration * 0.8 + session.duration_minutes * 0.2
                )
        
        # Update distraction frequency
        if session.activity_type in [ActivityType.DISTRACTION, ActivityType.ENTERTAINMENT]:
            # Calculate distractions per hour
            if session.duration_minutes > 0:
                distractions_per_hour = 60.0 / session.duration_minutes
                self.patterns.distraction_frequency = (
                    self.patterns.distraction_frequency * 0.9 + distractions_per_hour * 0.1
                )
        
        # Update procrastination score
        current_hour = datetime.now().hour
        if session.activity_type in [ActivityType.DISTRACTION, ActivityType.ENTERTAINMENT]:
            if current_hour in self.patterns.productive_hours:
                self.patterns.procrastination_score = min(1.0, 
                    self.patterns.procrastination_score + 0.1)
        elif session.activity_type == ActivityType.STUDY:
            self.patterns.procrastination_score = max(0.0, 
                self.patterns.procrastination_score - 0.05)
    
    def _update_behavior_patterns(self, current_time: float) -> None:
        """Update overall behavior patterns"""
        # Update productive hours
        if self.current_window and self.current_window.activity_type == ActivityType.STUDY:
            current_hour = datetime.now().hour
            self.patterns.productive_hours.add(current_hour)
        
        # Update distraction triggers
        if self.current_window and self.current_window.activity_type in [ActivityType.DISTRACTION, ActivityType.ENTERTAINMENT]:
            self.patterns.distraction_triggers.add(self.current_window.process_name)
        
        # Apply time-based decay to procrastination score
        time_since_last_check = current_time - self.last_check_time
        if time_since_last_check > 300:  # 5 minutes
            self.patterns.procrastination_score = max(0.0, 
                self.patterns.procrastination_score - 0.01)
            self.last_check_time = current_time
    
    def _get_perception_summary(self) -> Dict:
        """Get summary of current perception for emotional engine"""
        current_activity = self.current_window.activity_type if self.current_window else ActivityType.IDLE
        current_focus = self.current_window.focus_level if self.current_window else FocusLevel.IDLE
        
        return {
            'current_activity': current_activity.value,
            'current_focus': current_focus.value,
            'window_title': self.current_window.title if self.current_window else "Unknown",
            'procrastination_score': self.patterns.procrastination_score,
            'distraction_frequency': self.patterns.distraction_frequency,
            'study_streak': self.patterns.study_streak,
            'total_study_today': self.patterns.total_study_today,
            'avg_focus_duration': self.patterns.avg_focus_duration,
            'is_distracted': current_activity in [ActivityType.DISTRACTION, ActivityType.ENTERTAINMENT],
            'is_studying': current_activity == ActivityType.STUDY,
            'session_duration': self.patterns.current_session.duration_minutes if self.patterns.current_session else 0.0
        }
    
    def start_background_monitoring(self) -> None:
        """Start background monitoring for user behavior"""
        if hasattr(self, '_monitoring_thread') and self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._background_monitoring_loop, daemon=True)
        self._monitoring_thread.start()
    
    def stop_background_monitoring(self) -> None:
        """Stop background monitoring"""
        self._monitoring_active = False
        if hasattr(self, '_monitoring_thread'):
            self._monitoring_thread.join(timeout=5)
    
    def _background_monitoring_loop(self) -> None:
        """Background loop for continuous behavior monitoring"""
        while self._monitoring_active:
            try:
                # Monitor user behavior
                self.monitor_behavior()
                
                # Sleep for monitoring interval (check every 30 seconds)
                time.sleep(30)
                
            except Exception as e:
                # Log error but continue monitoring
                time.sleep(10)  # Shorter sleep on error


# Global perception system instance
_perception_system = None

def get_perception_system() -> PerceptionSystem:
    """Get global perception system instance"""
    global _perception_system
    if _perception_system is None:
        _perception_system = PerceptionSystem()
    return _perception_system
