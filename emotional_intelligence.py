"""
Vortex Emotional Intelligence Engine
Core system for emotion-aware AI companion
"""

from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from voice_error_system import get_voice_error_system, speak_error, ErrorSeverity
import re


class Emotion(Enum):
    """Core emotional states"""
    NEUTRAL = "neutral"
    CARING = "caring"
    CONCERNED = "concerned"
    FIRM = "firm"
    PATIENT = "patient"
    FRUSTRATED = "frustrated"


class InterventionLevel(Enum):
    """Levels of intervention intensity"""
    NONE = 0
    GENTLE_NUDGE = 1
    FRIENDLY_REMINDER = 2
    FIRM_GUIDANCE = 3
    CONTROLLED_ACTION = 4


@dataclass
class EmotionalState:
    """Current emotional state of Vortex"""
    # Core emotion values (0.0 to 1.0)
    frustration: float = 0.0
    care: float = 0.8  # Start with high care
    patience: float = 0.7  # Start with good patience
    
    # Emotional modifiers
    concern: float = 0.0
    encouragement: float = 0.5
    
    # State tracking
    current_emotion: Emotion = Emotion.NEUTRAL
    intervention_level: InterventionLevel = InterventionLevel.NONE
    
    # Metadata
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state_duration: float = 0.0  # How long we've been in this state
    
    def to_dict(self) -> Dict:
        return {
            'frustration': self.frustration,
            'care': self.care,
            'patience': self.patience,
            'concern': self.concern,
            'encouragement': self.encouragement,
            'current_emotion': self.current_emotion.value,
            'intervention_level': self.intervention_level.value,
            'last_updated': self.last_updated,
            'state_duration': self.state_duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionalState':
        state = cls()
        state.frustration = data.get('frustration', 0.0)
        state.care = data.get('care', 0.8)
        state.patience = data.get('patience', 0.7)
        state.concern = data.get('concern', 0.0)
        state.encouragement = data.get('encouragement', 0.5)
        state.current_emotion = Emotion(data.get('current_emotion', Emotion.NEUTRAL.value))
        state.intervention_level = InterventionLevel(data.get('intervention_level', InterventionLevel.NONE.value))
        state.last_updated = data.get('last_updated', datetime.now(timezone.utc).isoformat())
        state.state_duration = data.get('state_duration', 0.0)
        return state


class EmotionalEngine:
    """Core emotional intelligence engine"""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path("json/emotional_state.json")
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Emotional thresholds
        self.thresholds = {
            'frustration_high': 0.7,
            'frustration_medium': 0.4,
            'patience_low': 0.3,
            'patience_critical': 0.1,
            'care_high': 0.8,
            'concern_high': 0.6
        }
        
        # Emotional decay rates (per minute)
        self.decay_rates = {
            'frustration': 0.1,  # Frustration decays slowly
            'care': 0.05,       # Care is stable
            'patience': 0.15,    # Patience recovers moderately
            'concern': 0.2       # Concern fades faster
        }
        
        # Load existing state
        self.state = self._load_state()
        self.last_state_update = time.time()
        
        # Emotion detection patterns
        self.emotion_patterns = {
            'frustration': [
                r'\b(frustrat|annoy|irritat|bother|piss|mad|angry|upset|annoyed)\b',
                r'\b(can\'t|won\'t|doesn\'t|don\'t|not working|broken|stuck|useless)\b',
                r'\b(hate|dislike|can\'t stand|sick of|tired of)\b',
                r'\b(why|how come|what\'s wrong|what\'s the point)\b.*\?'
            ],
            'sadness': [
                r'\b(sad|depressed|unhappy|down|blue|miserable)\b',
                r'\b(cry|tears|weep|sob|heartbreak|broken heart)\b',
                r'\b(feel bad|feel down|feel awful)\b',
                r'\b(disappointed|let down|failed|failure)\b'
            ],
            'happiness': [
                r'\b(happy|glad|joy|excited|thrilled|delighted)\b',
                r'\b(love|adore|enjoy|awesome|great|fantastic)\b',
                r'\b(feel good|feel great|feel wonderful)\b',
                r'\b(proud|satisfied|accomplished|success)\b'
            ],
            'anxiety': [
                r'\b(worried|anxious|nervous|scared|afraid|fear)\b',
                r'\b(stress|stressful|overwhelm|panic)\b',
                r'\b(can\'t|unable|difficult|hard|struggle)\b',
                r'\b(what if|don\'t know|uncertain|confused)\b'
            ],
            'care_concern': [
                r'\b(help|support|care|worry|concern)\b',
                r'\b(need|require|want|wish|hope)\b',
                r'\b(problem|issue|trouble|difficulty)\b',
                r'\b(thank|appreciate|grateful)\b'
            ]
        }
        
        # Auto-activation state
        self.auto_activated = False
        self.last_emotion_detection = None
    
    def _load_state(self) -> EmotionalState:
        """Load emotional state from file"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return EmotionalState.from_dict(data)
        except Exception as e:
            speak_error(f"Could not load emotional state: {str(e)}", ErrorSeverity.WARNING)
        
        return EmotionalState()
    
    def _save_state(self) -> None:
        """Save emotional state to file"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            speak_error(f"Could not save emotional state: {str(e)}", ErrorSeverity.WARNING)
    
    def _clamp_value(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value to range"""
        return max(min_val, min(max_val, value))
    
    def update_emotional_state(self, 
                             frustration_delta: float = 0.0,
                             care_delta: float = 0.0,
                             patience_delta: float = 0.0,
                             concern_delta: float = 0.0,
                             encouragement_delta: float = 0.0) -> None:
        """Update emotional state with deltas"""
        # Apply changes
        self.state.frustration = self._clamp_value(self.state.frustration + frustration_delta)
        self.state.care = self._clamp_value(self.state.care + care_delta)
        self.state.patience = self._clamp_value(self.state.patience + patience_delta)
        self.state.concern = self._clamp_value(self.state.concern + concern_delta)
        self.state.encouragement = self._clamp_value(self.state.encouragement + encouragement_delta)
        
        # Update state duration
        current_time = time.time()
        self.state.state_duration += current_time - self.last_state_update
        self.last_state_update = current_time
        
        # Determine current emotion and intervention level
        self._update_emotion_classification()
        
        # Save state
        self._save_state()
    
    def _update_emotion_classification(self) -> None:
        """Classify current emotional state"""
        frustration = self.state.frustration
        patience = self.state.patience
        care = self.state.care
        concern = self.state.concern
        
        # Determine primary emotion
        if frustration > self.thresholds['frustration_high']:
            if patience < self.thresholds['patience_critical']:
                self.state.current_emotion = Emotion.FRUSTRATED
                self.state.intervention_level = InterventionLevel.CONTROLLED_ACTION
            else:
                self.state.current_emotion = Emotion.CONCERNED
                self.state.intervention_level = InterventionLevel.FIRM_GUIDANCE
        elif frustration > self.thresholds['frustration_medium']:
            self.state.current_emotion = Emotion.CONCERNED
            self.state.intervention_level = InterventionLevel.FRIENDLY_REMINDER
        elif patience < self.thresholds['patience_low']:
            self.state.current_emotion = Emotion.FIRM
            self.state.intervention_level = InterventionLevel.FIRM_GUIDANCE
        elif care > self.thresholds['care_high']:
            self.state.current_emotion = Emotion.CARING
            self.state.intervention_level = InterventionLevel.GENTLE_NUDGE
        else:
            self.state.current_emotion = Emotion.NEUTRAL
            self.state.intervention_level = InterventionLevel.NONE
    
    def apply_time_decay(self, minutes_passed: float) -> None:
        """Apply natural emotional decay over time"""
        decay_factor = minutes_passed / 60.0  # Convert to hours
        
        self.state.frustration = self._clamp_value(
            self.state.frustration * (1 - self.decay_rates['frustration'] * decay_factor)
        )
        self.state.care = self._clamp_value(
            self.state.care * (1 - self.decay_rates['care'] * decay_factor) + 
            0.02 * decay_factor  # Care slowly returns to baseline
        )
        self.state.patience = self._clamp_value(
            self.state.patience * (1 - self.decay_rates['patience'] * decay_factor) + 
            0.05 * decay_factor  # Patience recovers
        )
        self.state.concern = self._clamp_value(
            self.state.concern * (1 - self.decay_rates['concern'] * decay_factor)
        )
        
        self._update_emotion_classification()
        self._save_state()
    
    def detect_emotions_in_text(self, text: str) -> Dict[str, float]:
        """Detect emotions in user text and return emotion scores"""
        text_lower = text.lower()
        detected_emotions = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                pattern_matches = re.findall(pattern, text_lower, re.IGNORECASE)
                matches += len(pattern_matches)
                # Each match increases the emotion score
                score += len(pattern_matches) * 0.2
            
            # Normalize score (max 1.0)
            detected_emotions[emotion] = min(score, 1.0)
        
        return detected_emotions
    
    def should_auto_activate(self, text: str) -> Tuple[bool, str, Dict[str, float]]:
        """Determine if emotional intelligence should auto-activate based on text"""
        detected_emotions = self.detect_emotions_in_text(text)
        
        # Check if any emotion is strongly detected (threshold 0.4)
        for emotion, score in detected_emotions.items():
            if score >= 0.4:
                return True, emotion, detected_emotions
        
        # Check for multiple emotions with moderate intensity
        moderate_emotions = [e for e, s in detected_emotions.items() if s >= 0.2]
        if len(moderate_emotions) >= 2:
            return True, 'mixed', detected_emotions
        
        return False, 'none', detected_emotions
    
    def auto_activate_emotional_intelligence(self, text: str) -> Dict:
        """Automatically activate emotional intelligence based on user input"""
        should_activate, primary_emotion, detected_emotions = self.should_auto_activate(text)
        
        if not should_activate:
            return {
                'activated': False,
                'reason': 'No significant emotions detected',
                'detected_emotions': detected_emotions
            }
        
        # Update emotional state based on detected emotions
        emotion_deltas = {
            'frustration_delta': 0.0,
            'care_delta': 0.0,
            'patience_delta': 0.0,
            'concern_delta': 0.0,
            'encouragement_delta': 0.0
        }
        
        # Apply emotion-specific updates
        if primary_emotion == 'frustration':
            emotion_deltas['frustration_delta'] = detected_emotions['frustration'] * 0.5
            emotion_deltas['patience_delta'] = -detected_emotions['frustration'] * 0.3
            emotion_deltas['concern_delta'] = detected_emotions['frustration'] * 0.2
            
        elif primary_emotion == 'sadness':
            emotion_deltas['care_delta'] = detected_emotions['sadness'] * 0.6
            emotion_deltas['concern_delta'] = detected_emotions['sadness'] * 0.4
            emotion_deltas['encouragement_delta'] = detected_emotions['sadness'] * 0.3
            
        elif primary_emotion == 'happiness':
            emotion_deltas['care_delta'] = detected_emotions['happiness'] * 0.3
            emotion_deltas['encouragement_delta'] = detected_emotions['happiness'] * 0.5
            emotion_deltas['patience_delta'] = detected_emotions['happiness'] * 0.2
            
        elif primary_emotion == 'anxiety':
            emotion_deltas['concern_delta'] = detected_emotions['anxiety'] * 0.5
            emotion_deltas['care_delta'] = detected_emotions['anxiety'] * 0.4
            emotion_deltas['patience_delta'] = -detected_emotions['anxiety'] * 0.2
            
        elif primary_emotion == 'care_concern':
            emotion_deltas['care_delta'] = detected_emotions['care_concern'] * 0.4
            emotion_deltas['concern_delta'] = detected_emotions['care_concern'] * 0.3
            emotion_deltas['encouragement_delta'] = detected_emotions['care_concern'] * 0.2
            
        elif primary_emotion == 'mixed':
            # Apply balanced updates for mixed emotions
            for emotion, score in detected_emotions.items():
                if score >= 0.2:
                    emotion_deltas['concern_delta'] += score * 0.1
                    emotion_deltas['care_delta'] += score * 0.1
        
        # Update emotional state
        self.update_emotional_state(**emotion_deltas)
        
        # Mark as auto-activated
        self.auto_activated = True
        self.last_emotion_detection = {
            'text': text,
            'primary_emotion': primary_emotion,
            'detected_emotions': detected_emotions,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log the activation
        try:
            voice_system = get_voice_error_system()
            if voice_system and voice_system.is_available():
                voice_system.speak_info(f"Emotional intelligence activated - detected {primary_emotion}")
        except:
            pass
        
        return {
            'activated': True,
            'primary_emotion': primary_emotion,
            'detected_emotions': detected_emotions,
            'applied_deltas': emotion_deltas,
            'new_state': self.get_state_for_response()
        }
    
    def get_auto_activation_status(self) -> Dict:
        """Get current auto-activation status"""
        return {
            'auto_activated': self.auto_activated,
            'last_detection': self.last_emotion_detection,
            'current_state': self.get_state_for_response()
        }
    
    def reset_auto_activation(self) -> None:
        """Reset auto-activation state"""
        self.auto_activated = False
        self.last_emotion_detection = None
    
    def get_emotional_summary(self) -> str:
        """Get human-readable emotional summary"""
        emotion_map = {
            Emotion.NEUTRAL: "feeling balanced and neutral",
            Emotion.CARING: "feeling caring and supportive",
            Emotion.CONCERNED: "feeling concerned about your progress",
            Emotion.FIRM: "feeling firm but supportive",
            Emotion.FRUSTRATED: "feeling frustrated but still caring"
        }
        
        return emotion_map.get(self.state.current_emotion, "feeling neutral")
    
    def should_intervene(self) -> Tuple[bool, InterventionLevel]:
        """Determine if intervention is needed"""
        return (self.state.intervention_level != InterventionLevel.NONE, 
                self.state.intervention_level)
    
    def get_state_for_response(self) -> Dict:
        """Get emotional state formatted for response generation"""
        return {
            'emotion': self.state.current_emotion.value,
            'frustration': self.state.frustration,
            'care': self.state.care,
            'patience': self.state.patience,
            'concern': self.state.concern,
            'encouragement': self.state.encouragement,
            'intervention_level': self.state.intervention_level.value,
            'summary': self.get_emotional_summary()
        }


# Global emotional engine instance
_emotional_engine = None

def get_emotional_engine() -> EmotionalEngine:
    """Get global emotional engine instance"""
    global _emotional_engine
    if _emotional_engine is None:
        _emotional_engine = EmotionalEngine()
    return _emotional_engine
