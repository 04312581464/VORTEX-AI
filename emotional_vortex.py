"""
Vortex Emotional Intelligence Integration
Main integration point for emotional AI companion
"""

from __future__ import annotations
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any

from emotional_intelligence import get_emotional_engine, EmotionalEngine
from perception_system import get_perception_system, PerceptionSystem
from intervention_system import get_intervention_system, InterventionSystem
from emotional_response_generator import get_response_generator, EmotionalResponseGenerator


class EmotionalVortex:
    """Main emotional intelligence integration for Vortex"""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path("json/emotional_vortex.json")
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize all components
        self.emotional_engine = get_emotional_engine()
        self.perception_system = get_perception_system()
        self.intervention_system = get_intervention_system()
        self.response_generator = get_response_generator()
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 30  # seconds
        
        # Configuration
        self.config = self._load_config()
        
        # State tracking
        self.last_update = time.time()
        self.session_start = time.time()
        self.intervention_count = 0
        
    def _load_config(self) -> Dict:
        """Load emotional Vortex configuration"""
        config_path = self.data_path.parent / "emotional_config.json"
        
        default_config = {
            "monitoring_enabled": True,
            "monitoring_interval": 30,
            "intervention_enabled": True,
            "auto_intervene": True,
            "user_override_duration": 30,
            "emotional_decay_enabled": True,
            "decay_interval": 300,  # 5 minutes
            "response_style": "emotional",
            "care_baseline": 0.8,
            "patience_baseline": 0.7,
            "frustration_threshold": 0.7,
            "study_recognition": True,
            "distraction_detection": True,
            "break_reminders": True,
            "max_study_sessions": 5,
            "study_session_duration": 45  # minutes
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            return default_config
        except Exception as e:
            pass
            return default_config
    
    def start_monitoring(self) -> None:
        """Start background emotional monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop background emotional monitoring"""
        self.monitoring_active = False
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Update emotional state based on perception
                self._update_emotional_state()
                
                # Check for interventions
                if self.config.get("auto_intervene", True):
                    self._check_interventions()
                
                # Apply emotional decay
                if self.config.get("emotional_decay_enabled", True):
                    self._apply_emotional_decay()
                
                # Sleep until next update
                time.sleep(self.config.get("monitoring_interval", 30))
                
            except Exception as e:
                time.sleep(60)  # Wait longer on error
    
    def _update_emotional_state(self) -> None:
        """Update emotional state based on current perception"""
        # Get perception summary
        perception_summary = self.perception_system.monitor_behavior()
        
        # Calculate emotional deltas based on perception
        frustration_delta = 0.0
        care_delta = 0.0
        patience_delta = 0.0
        concern_delta = 0.0
        encouragement_delta = 0.0
        
        # Distraction handling
        if perception_summary.get("is_distracted"):
            frustration_delta += 0.1
            patience_delta -= 0.05
            concern_delta += 0.1
        
        # Study recognition
        if perception_summary.get("is_studying"):
            care_delta += 0.05
            patience_delta += 0.1
            encouragement_delta += 0.1
            frustration_delta -= 0.05
        
        # Procrastination handling
        proc_score = perception_summary.get("procrastination_score", 0.0)
        if proc_score > 0.6:
            frustration_delta += 0.15 * proc_score
            concern_delta += 0.1 * proc_score
            patience_delta -= 0.1 * proc_score
        
        # Study streak encouragement
        study_streak = perception_summary.get("study_streak", 0)
        if study_streak > 3:
            encouragement_delta += 0.1
            care_delta += 0.05
        
        # Total study time recognition
        total_study = perception_summary.get("total_study_today", 0.0)
        if total_study > 120:  # 2+ hours
            care_delta += 0.1
            encouragement_delta += 0.05
        
        # Apply emotional changes
        self.emotional_engine.update_emotional_state(
            frustration_delta=frustration_delta,
            care_delta=care_delta,
            patience_delta=patience_delta,
            concern_delta=concern_delta,
            encouragement_delta=encouragement_delta
        )
        
        self.last_update = time.time()
    
    def _check_interventions(self) -> None:
        """Check if intervention is needed and execute"""
        if not self.config.get("intervention_enabled", True):
            return
        
        intervention = self.intervention_system.evaluate_and_intervene()
        if intervention:
            self.intervention_count += 1
    
    def _apply_emotional_decay(self) -> None:
        """Apply natural emotional decay over time"""
        current_time = time.time()
        time_since_last = current_time - self.last_update
        
        if time_since_last > self.config.get("decay_interval", 300):  # 5 minutes
            minutes_passed = time_since_last / 60.0
            self.emotional_engine.apply_time_decay(minutes_passed)
            self.last_update = current_time
    
    def process_user_input(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Process user input with emotional awareness"""
        # Get current emotional and perception state
        emotional_state = self.emotional_engine.get_state_for_response()
        perception_summary = self.perception_system.monitor_behavior()
        
        # Determine context
        if context is None:
            context = {}
        
        context.update({
            "emotional_state": emotional_state,
            "perception_summary": perception_summary
        })
        
        # Generate emotional response
        response = self.response_generator.generate_response(
            emotional_state,
            perception_summary,
            context="user_interaction",
            user_input=user_input
        )
        
        # Update emotional state based on user interaction
        self._update_emotion_from_user_input(user_input)
        
        return response
    
    def _update_emotion_from_user_input(self, user_input: str) -> None:
        """Update emotional state based on user input"""
        input_lower = user_input.lower()
        
        # Positive interactions
        if any(word in input_lower for word in ["thank", "thanks", "good", "great", "helpful"]):
            self.emotional_engine.update_emotional_state(
                care_delta=0.05,
                frustration_delta=-0.1,
                encouragement_delta=0.1
            )
        
        # Negative interactions
        elif any(word in input_lower for word in ["annoying", "stop", "leave", "quit"]):
            self.emotional_engine.update_emotional_state(
                frustration_delta=0.1,
                patience_delta=-0.05
            )
        
        # Override commands
        elif any(word in input_lower for word in ["override", "stop intervening", "no more"]):
            self.intervention_system.user_override(
                duration_minutes=self.config.get("user_override_duration", 30)
            )
        
        # Status requests
        elif any(word in input_lower for word in ["status", "how are you", "feeling"]):
            # No emotional change, just information request
            pass
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "monitoring_active": self.monitoring_active,
            "session_duration_minutes": (time.time() - self.session_start) / 60,
            "intervention_count": self.intervention_count,
            "last_update": datetime.fromtimestamp(self.last_update, timezone.utc).isoformat(),
            "emotional_state": self.emotional_engine.get_state_for_response(),
            "perception_summary": self.perception_system.monitor_behavior(),
            "intervention_status": self.intervention_system.get_system_status(),
            "config": self.config
        }
    
    def user_override(self, duration_minutes: Optional[float] = None) -> None:
        """Activate user override to stop interventions"""
        if duration_minutes is None:
            duration_minutes = self.config.get("user_override_duration", 30)
        
        self.intervention_system.user_override(duration_minutes)
    
    def manual_intervention(self, message: str, severity: str = "gentle") -> str:
        """Trigger manual intervention"""
        severity_map = {
            "gentle": 1,
            "reminder": 2,
            "firm": 3,
            "action": 4
        }
        
        level = severity_map.get(severity.lower(), 1)
        
        # Generate response
        emotional_state = self.emotional_engine.get_state_for_response()
        perception_summary = self.perception_system.monitor_behavior()
        
        response = self.response_generator.generate_response(
            emotional_state,
            perception_summary,
            context="manual_intervention"
        )
        
        print(f"🎯 Manual intervention: {response}")
        
        return response
    
    def update_config(self, new_config: Dict) -> None:
        """Update configuration"""
        self.config.update(new_config)
        
        # Save configuration
        config_path = self.data_path.parent / "emotional_config.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
        
        # Apply configuration changes
        if "monitoring_interval" in new_config:
            self.monitoring_interval = new_config["monitoring_interval"]
    
    def get_emotional_summary(self) -> str:
        """Get human-readable emotional summary"""
        emotional_state = self.emotional_engine.get_state_for_response()
        perception_summary = self.perception_system.monitor_behavior()
        
        summary_parts = []
        
        # Emotional state
        emotion = emotional_state.get("emotion", "neutral")
        summary_parts.append(f"I'm feeling {emotion}")
        
        # Current activity
        activity = perception_summary.get("current_activity", "unknown")
        if activity != "unknown":
            summary_parts.append(f"I see you're {activity}")
        
        # Concerns or encouragement
        if perception_summary.get("is_distracted"):
            summary_parts.append("and I'm a bit concerned about your focus")
        elif perception_summary.get("is_studying"):
            summary_parts.append("and I'm proud of your dedication")
        
        # Care level
        care = emotional_state.get("care", 0.5)
        if care > 0.8:
            summary_parts.append("I really care about your progress")
        
        return " ".join(summary_parts) + "."
    
    def shutdown(self) -> None:
        """Clean shutdown of emotional Vortex"""
        self.stop_monitoring()
        
        # Save final state
        try:
            final_status = self.get_system_status()
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(final_status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
        
        pass


# Global emotional Vortex instance
_emotional_vortex = None

def get_emotional_vortex() -> EmotionalVortex:
    """Get global emotional Vortex instance"""
    global _emotional_vortex
    if _emotional_vortex is None:
        _emotional_vortex = EmotionalVortex()
    return _emotional_vortex


# Convenience functions for integration
def start_emotional_monitoring() -> None:
    """Start emotional monitoring"""
    vortex = get_emotional_vortex()
    vortex.start_monitoring()


def process_emotional_input(user_input: str, context: Optional[Dict] = None) -> str:
    """Process user input with emotional intelligence"""
    vortex = get_emotional_vortex()
    return vortex.process_user_input(user_input, context)


def get_emotional_status() -> Dict:
    """Get emotional system status"""
    vortex = get_emotional_vortex()
    return vortex.get_system_status()


def activate_user_override(duration_minutes: float = 30.0) -> None:
    """Activate user override"""
    vortex = get_emotional_vortex()
    vortex.user_override(duration_minutes)


def manual_emotional_intervention(message: str, severity: str = "gentle") -> str:
    """Trigger manual emotional intervention"""
    vortex = get_emotional_vortex()
    return vortex.manual_intervention(message, severity)
