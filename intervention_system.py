"""
Vortex Intervention System
Executes context-aware interventions based on emotional state
"""

from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import subprocess
import threading
import queue

from emotional_intelligence import EmotionalEngine, InterventionLevel, Emotion
from perception_system import PerceptionSystem, ActivityType, FocusLevel
from voice_error_system import get_voice_error_system, speak_error, ErrorSeverity


class InterventionType(Enum):
    """Types of interventions"""
    MESSAGE = "message"
    NOTIFICATION = "notification"
    WINDOW_ACTION = "window_action"
    APP_SWITCH = "app_switch"
    VOLUME_CONTROL = "volume_control"
    BREAK_REMINDER = "break_reminder"
    FOCUS_MODE = "focus_mode"


@dataclass
class InterventionAction:
    """Definition of an intervention action"""
    type: InterventionType
    message: str
    severity: InterventionLevel
    cooldown_minutes: float
    user_overridable: bool = True
    action_data: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CooldownManager:
    """Manages intervention cooldowns"""
    
    def __init__(self):
        self.intervention_cooldowns: Dict[str, float] = {}
        self.global_cooldown_until = 0.0
        self.user_override_active = False
        self.override_until = 0.0
    
    def can_intervene(self, intervention_type: str, severity: InterventionLevel) -> bool:
        """Check if intervention is allowed (not on cooldown)"""
        current_time = time.time()
        
        # Check global override
        if self.user_override_active and current_time < self.override_until:
            return False
        
        # Check global cooldown
        if current_time < self.global_cooldown_until:
            return False
        
        # Check specific intervention cooldown
        cooldown_key = f"{intervention_type}_{severity.value}"
        if cooldown_key in self.intervention_cooldowns:
            if current_time < self.intervention_cooldowns[cooldown_key]:
                return False
        
        return True
    
    def set_cooldown(self, intervention_type: str, severity: InterventionLevel, cooldown_minutes: float) -> None:
        """Set cooldown for intervention"""
        cooldown_key = f"{intervention_type}_{severity.value}"
        self.intervention_cooldowns[cooldown_key] = time.time() + (cooldown_minutes * 60)
    
    def set_global_cooldown(self, minutes: float) -> None:
        """Set global cooldown for all interventions"""
        self.global_cooldown_until = time.time() + (minutes * 60)
    
    def activate_user_override(self, duration_minutes: float = 30.0) -> None:
        """Activate user override to stop all interventions"""
        self.user_override_active = True
        self.override_until = time.time() + (duration_minutes * 60)
    
    def deactivate_user_override(self) -> None:
        """Deactivate user override"""
        self.user_override_active = False
        self.override_until = 0.0
    
    def get_override_status(self) -> Dict:
        """Get current override status"""
        current_time = time.time()
        return {
            'override_active': self.user_override_active and current_time < self.override_until,
            'override_remaining_minutes': max(0, (self.override_until - current_time) / 60) if self.user_override_active else 0.0,
            'global_cooldown_remaining': max(0, (self.global_cooldown_until - current_time) / 60)
        }


class InterventionExecutor:
    """Executes intervention actions"""
    
    def __init__(self):
        self.action_queue = queue.Queue()
        self.execution_thread = threading.Thread(target=self._execute_actions, daemon=True)
        self.execution_thread.start()
    
    def _execute_actions(self) -> None:
        """Background thread to execute interventions"""
        while True:
            try:
                action = self.action_queue.get(timeout=1)
                self._perform_action(action)
                self.action_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                speak_error(f"Error executing intervention: {str(e)}", ErrorSeverity.ERROR)
    
    def _perform_action(self, action: InterventionAction) -> None:
        """Perform the actual intervention action"""
        try:
            if action.type == InterventionType.MESSAGE:
                self._send_message(action.message, action.severity)
            
            elif action.type == InterventionType.NOTIFICATION:
                self._send_notification(action.message, action.severity)
            
            elif action.type == InterventionType.WINDOW_ACTION:
                self._perform_window_action(action.action_data)
            
            elif action.type == InterventionType.APP_SWITCH:
                self._switch_to_study_app(action.action_data)
            
            elif action.type == InterventionType.VOLUME_CONTROL:
                self._adjust_volume(action.action_data)
            
            elif action.type == InterventionType.BREAK_REMINDER:
                self._send_break_reminder(action.message)
            
            elif action.type == InterventionType.FOCUS_MODE:
                self._activate_focus_mode(action.action_data)
        
        except Exception as e:
            pass
    
    def _send_message(self, message: str, severity: InterventionLevel) -> None:
        """Send a message to the user"""
        # TODO: Integrate with TTS system
    
    def _send_notification(self, message: str, severity: InterventionLevel) -> None:
        """Send a system notification"""
        try:
            # Windows notification
            subprocess.run([
                'powershell', '-Command',
                f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show("{message}", "Vortex", "OK", "Information")'
            ], capture_output=True, timeout=10)
        except Exception as e:
            pass
    
    def _perform_window_action(self, action_data: Dict) -> None:
        """Perform window-related actions"""
        action = action_data.get('action')
        
        if action == 'close_distraction':
            window_title = action_data.get('window_title', '')
            # TODO: Implement window closing logic
        
        elif action == 'minimize_window':
            window_title = action_data.get('window_title', '')
            # TODO: Implement window minimization
    
    def _switch_to_study_app(self, action_data: Dict) -> None:
        """Switch to a study application"""
        app_name = action_data.get('app_name', 'notepad')
        try:
            subprocess.run([app_name], capture_output=True, timeout=5)
        except Exception as e:
            pass
    
    def _adjust_volume(self, action_data: Dict) -> None:
        """Adjust system volume"""
        volume_level = action_data.get('volume_level', 50)
        try:
            subprocess.run([
                'powershell', '-Command',
                f'(New-Object -comObject WScript.Shell).SendKeys([char]175)'  # Volume up
            ], capture_output=True, timeout=5)
        except Exception as e:
            pass
    
    def _send_break_reminder(self, message: str) -> None:
        """Send a break reminder"""
        # TODO: Implement break reminder logic
    
    def _activate_focus_mode(self, action_data: Dict) -> None:
        """Activate focus mode"""
        duration = action_data.get('duration_minutes', 25)
        # TODO: Implement focus mode logic
    
    def queue_action(self, action: InterventionAction) -> None:
        """Queue an intervention action for execution"""
        self.action_queue.put(action)


class InterventionSystem:
    """Main intervention system"""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path("json/intervention_log.json")
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.emotional_engine = EmotionalEngine()
        self.perception_system = PerceptionSystem()
        self.cooldown_manager = CooldownManager()
        self.executor = InterventionExecutor()
        
        # Intervention history
        self.intervention_history: List[InterventionAction] = []
        self.max_history_size = 100
        
        # Intervention strategies
        self.intervention_strategies = self._load_strategies()
        
        # Background monitoring
        self._monitoring_active = False
        self._monitoring_thread = None
        self.last_intervention_time = 0.0
        self.intervention_interval = 300  # 5 minutes minimum between interventions
    
    def _load_strategies(self) -> Dict:
        """Load intervention strategies"""
        return {
            InterventionLevel.GENTLE_NUDGE: [
                InterventionType.MESSAGE,
                InterventionType.NOTIFICATION
            ],
            InterventionLevel.FRIENDLY_REMINDER: [
                InterventionType.MESSAGE,
                InterventionType.NOTIFICATION,
                InterventionType.BREAK_REMINDER
            ],
            InterventionLevel.FIRM_GUIDANCE: [
                InterventionType.MESSAGE,
                InterventionType.NOTIFICATION,
                InterventionType.WINDOW_ACTION,
                InterventionType.VOLUME_CONTROL
            ],
            InterventionLevel.CONTROLLED_ACTION: [
                InterventionType.MESSAGE,
                InterventionType.WINDOW_ACTION,
                InterventionType.APP_SWITCH,
                InterventionType.FOCUS_MODE,
                InterventionType.VOLUME_CONTROL
            ]
        }
    
    def evaluate_and_intervene(self) -> Optional[InterventionAction]:
        """Evaluate current state and decide on intervention"""
        # Get current emotional and perception state
        emotional_state = self.emotional_engine.get_state_for_response()
        perception_summary = self.perception_system.monitor_behavior()
        
        # Check if intervention is needed
        should_intervene, intervention_level = self.emotional_engine.should_intervene()
        
        if not should_intervene:
            return None
        
        # Check cooldowns
        intervention_type = self._select_intervention_type(intervention_level, perception_summary)
        if not self.cooldown_manager.can_intervene(intervention_type.value, intervention_level):
            return None
        
        # Check minimum interval
        current_time = time.time()
        if current_time - self.last_intervention_time < self.intervention_interval:
            return None
        
        # Generate intervention
        action = self._generate_intervention(intervention_level, intervention_type, emotional_state, perception_summary)
        
        # Execute intervention
        if action:
            self._execute_intervention(action)
            return action
        
        return None
    
    def _select_intervention_type(self, level: InterventionLevel, perception: Dict) -> InterventionType:
        """Select appropriate intervention type based on level and context"""
        available_types = self.intervention_strategies[level]
        
        # Context-based selection
        if perception.get('is_distracted') and level in [InterventionLevel.FIRM_GUIDANCE, InterventionLevel.CONTROLLED_ACTION]:
            return InterventionType.WINDOW_ACTION
        
        if perception.get('total_study_today', 0) > 120:  # More than 2 hours of study
            if InterventionType.BREAK_REMINDER in available_types:
                return InterventionType.BREAK_REMINDER
        
        if level == InterventionLevel.CONTROLLED_ACTION and perception.get('is_distracted'):
            return InterventionType.APP_SWITCH
        
        # Default selection
        return available_types[0] if available_types else InterventionType.MESSAGE
    
    def _generate_intervention(self, level: InterventionLevel, type: InterventionType, 
                              emotional: Dict, perception: Dict) -> Optional[InterventionAction]:
        """Generate specific intervention action"""
        message = self._generate_message(level, type, emotional, perception)
        
        if not message:
            return None
        
        action_data = self._generate_action_data(type, perception)
        cooldown_minutes = self._get_cooldown_duration(level, type)
        
        return InterventionAction(
            type=type,
            message=message,
            severity=level,
            cooldown_minutes=cooldown_minutes,
            action_data=action_data
        )
    
    def _generate_message(self, level: InterventionLevel, type: InterventionType, 
                         emotional: Dict, perception: Dict) -> Optional[str]:
        """Generate context-aware message"""
        emotion = emotional.get('emotion', 'neutral')
        care = emotional.get('care', 0.5)
        frustration = emotional.get('frustration', 0.0)
        
        # Context-specific messages
        if perception.get('is_distracted'):
            window_title = perception.get('window_title', 'that app')
            
            if level == InterventionLevel.GENTLE_NUDGE:
                return f"Hey, just checking in. Are you still focused on your goals?"
            
            elif level == InterventionLevel.FRIENDLY_REMINDER:
                return f"I notice you've been on {window_title} for a while. Maybe it's time to get back to studying?"
            
            elif level == InterventionLevel.FIRM_GUIDANCE:
                return f"Alright, let's be honest. {window_title} isn't helping you reach your goals. Time to switch back."
            
            elif level == InterventionLevel.CONTROLLED_ACTION:
                return f"I care about your success, but this distraction is costing you. I'm going to help you refocus now."
        
        elif perception.get('total_study_today', 0) > 180:  # 3+ hours
            return "You've been studying for a while! A short break might help you focus better."
        
        elif perception.get('study_streak', 0) > 3:
            return f"Great job maintaining your study streak of {perception['study_streak']} sessions! Keep it up!"
        
        return None
    
    def _generate_action_data(self, type: InterventionType, perception: Dict) -> Dict:
        """Generate action-specific data"""
        if type == InterventionType.WINDOW_ACTION:
            return {
                'action': 'minimize_window',
                'window_title': perception.get('window_title', '')
            }
        
        elif type == InterventionType.APP_SWITCH:
            return {
                'app_name': 'notepad'  # Default to notepad for study
            }
        
        elif type == InterventionType.VOLUME_CONTROL:
            return {
                'volume_level': 30  # Lower volume for focus
            }
        
        elif type == InterventionType.FOCUS_MODE:
            return {
                'duration_minutes': 25
            }
        
        return {}
    
    def _get_cooldown_duration(self, level: InterventionLevel, type: InterventionType) -> float:
        """Get cooldown duration for intervention"""
        base_cooldowns = {
            InterventionLevel.GENTLE_NUDGE: 15.0,
            InterventionLevel.FRIENDLY_REMINDER: 20.0,
            InterventionLevel.FIRM_GUIDANCE: 30.0,
            InterventionLevel.CONTROLLED_ACTION: 45.0
        }
        
        base = base_cooldowns.get(level, 20.0)
        
        # Adjust based on intervention type
        if type in [InterventionType.WINDOW_ACTION, InterventionType.APP_SWITCH]:
            base *= 1.5  # Longer cooldown for intrusive actions
        
        return base
    
    def _execute_intervention(self, action: InterventionAction) -> None:
        """Execute intervention and update cooldowns"""
        # Set cooldowns
        self.cooldown_manager.set_cooldown(action.type.value, action.severity, action.cooldown_minutes)
        
        # Queue for execution
        self.executor.queue_action(action)
        
        # Update history
        self.intervention_history.append(action)
        if len(self.intervention_history) > self.max_history_size:
            self.intervention_history.pop(0)
        
        # Update emotional state (interventions increase frustration slightly)
        self.emotional_engine.update_emotional_state(frustration_delta=0.05)
        
        # Update last intervention time
        self.last_intervention_time = time.time()
        
        # Save intervention log
        self._save_intervention_log(action)
    
    def _save_intervention_log(self, action: InterventionAction) -> None:
        """Save intervention to log file"""
        try:
            log_entry = {
                'timestamp': action.timestamp,
                'type': action.type.value,
                'severity': action.severity.value,
                'message': action.message,
                'cooldown_minutes': action.cooldown_minutes,
                'action_data': action.action_data
            }
            
            # Load existing log
            log_data = []
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            
            # Add new entry
            log_data.append(log_entry)
            
            # Keep only last 50 entries
            if len(log_data) > 50:
                log_data = log_data[-50:]
            
            # Save log
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            pass
    
    def user_override(self, duration_minutes: float = 30.0) -> None:
        """Activate user override to stop interventions"""
        self.cooldown_manager.activate_user_override(duration_minutes)
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'emotional_state': self.emotional_engine.get_state_for_response(),
            'perception_summary': self.perception_system.monitor_behavior(),
            'cooldown_status': self.cooldown_manager.get_override_status(),
            'last_intervention': self.intervention_history[-1].timestamp if self.intervention_history else None,
            'intervention_count_today': len([i for i in self.intervention_history 
                                           if datetime.fromisoformat(i.timestamp.replace('Z', '+00:00')).date() == datetime.now().date()])
        }
    
    def start_background_monitoring(self) -> None:
        """Start background monitoring for automatic interventions"""
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
        """Background loop for continuous monitoring"""
        while self._monitoring_active:
            try:
                # Check if intervention is needed
                action = self.evaluate_and_intervene()
                if action:
                    self._execute_intervention(action)
                
                # Sleep for monitoring interval (check every 2 minutes)
                time.sleep(120)
                
            except Exception as e:
                speak_error(f"Error in intervention monitoring: {str(e)}", ErrorSeverity.WARNING)
                time.sleep(30)  # Shorter sleep on error


# Global intervention system instance
_intervention_system = None

def get_intervention_system() -> InterventionSystem:
    """Get global intervention system instance"""
    global _intervention_system
    if _intervention_system is None:
        _intervention_system = InterventionSystem()
    return _intervention_system
