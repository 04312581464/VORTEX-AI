"""
Vortex Emotional Response Generator
Generates emotionally-aware responses based on current state
"""

from __future__ import annotations
import json
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from emotional_intelligence import Emotion, EmotionalState, InterventionLevel
from perception_system import ActivityType, FocusLevel


class ResponseTone(Enum):
    """Response tone categories"""
    GENTLE = "gentle"
    CARING = "caring"
    CONCERNED = "concerned"
    FIRM = "firm"
    SUPPORTIVE = "supportive"
    ENCOURAGING = "encouraging"
    NEUTRAL = "neutral"


@dataclass
class ResponseTemplate:
    """Template for emotional responses"""
    tone: ResponseTone
    emotion: Emotion
    intervention_level: InterventionLevel
    contexts: List[str]
    templates: List[str]
    variations: List[str]


class EmotionalResponseGenerator:
    """Generates context-aware, emotional responses"""
    
    def __init__(self):
        self.response_templates = self._load_response_templates()
        self.context_modifiers = self._load_context_modifiers()
        self.emotion_modifiers = self._load_emotion_modifiers()
    
    def _load_response_templates(self) -> List[ResponseTemplate]:
        """Load response templates for different emotional contexts"""
        templates = [
            # Gentle nudge responses
            ResponseTemplate(
                tone=ResponseTone.GENTLE,
                emotion=Emotion.NEUTRAL,
                intervention_level=InterventionLevel.GENTLE_NUDGE,
                contexts=["distraction", "general"],
                templates=[
                    "Hey, just checking in. How's your focus going?",
                    "Just wanted to see how you're doing with your tasks.",
                    "Everything going well with your work/study?",
                    "How are you feeling about your progress today?"
                ],
                variations=[
                    "Is there anything I can help you with?",
                    "Remember to take breaks when you need them.",
                    "You're doing great, keep it up!"
                ]
            ),
            
            # Caring responses
            ResponseTemplate(
                tone=ResponseTone.CARING,
                emotion=Emotion.CARING,
                intervention_level=InterventionLevel.GENTLE_NUDGE,
                contexts=["study", "work", "general"],
                templates=[
                    "I'm here to support you in any way I can.",
                    "Your well-being is important to me.",
                    "I want to help you succeed while staying balanced.",
                    "Remember that I care about your progress and your health."
                ],
                variations=[
                    "You're capable of amazing things.",
                    "Take it one step at a time.",
                    "I believe in you."
                ]
            ),
            
            # Concerned responses
            ResponseTemplate(
                tone=ResponseTone.CONCERNED,
                emotion=Emotion.CONCERNED,
                intervention_level=InterventionLevel.FRIENDLY_REMINDER,
                contexts=["distraction", "procrastination"],
                templates=[
                    "I've noticed you might be getting a bit distracted. Is everything okay?",
                    "I'm a little concerned about your current focus. Want to talk about it?",
                    "It seems like you might need some help getting back on track.",
                    "I'm worried this distraction might be affecting your goals."
                ],
                variations=[
                    "Maybe we can figure this out together?",
                    "What do you think would help you focus better?",
                    "I'm here to help you get back to what matters."
                ]
            ),
            
            # Firm guidance responses
            ResponseTemplate(
                tone=ResponseTone.FIRM,
                emotion=Emotion.FIRM,
                intervention_level=InterventionLevel.FIRM_GUIDANCE,
                contexts=["distraction", "procrastination", "repeated_issues"],
                templates=[
                    "Alright, let's be honest about what's happening here.",
                    "I need to be direct with you because I care about your success.",
                    "This distraction isn't serving your goals, and we both know it.",
                    "It's time to get serious about what you want to achieve."
                ],
                variations=[
                    "You're better than this distraction.",
                    "Let's focus on what really matters right now.",
                    "I'm being firm because I believe in your potential."
                ]
            ),
            
            # Supportive responses
            ResponseTemplate(
                tone=ResponseTone.SUPPORTIVE,
                emotion=Emotion.CARING,
                intervention_level=InterventionLevel.FRIENDLY_REMINDER,
                contexts=["study", "work", "achievement"],
                templates=[
                    "You're making real progress, and I'm proud of you.",
                    "I can see how hard you're working, and it's paying off.",
                    "Your dedication is really inspiring.",
                    "You're building something meaningful here."
                ],
                variations=[
                    "Keep going, you're on the right track.",
                    "This effort will be worth it.",
                    "I'm here to celebrate your wins with you."
                ]
            ),
            
            # Encouraging responses
            ResponseTemplate(
                tone=ResponseTone.ENCOURAGING,
                emotion=Emotion.CARING,
                intervention_level=InterventionLevel.GENTLE_NUDGE,
                contexts=["study", "work", "challenges"],
                templates=[
                    "You've got this! One step at a time.",
                    "I believe in your ability to figure this out.",
                    "Every challenge is making you stronger.",
                    "You're more capable than you think."
                ],
                variations=[
                    "Trust yourself and the process.",
                    "Small progress is still progress.",
                    "You're learning and growing every day."
                ]
            ),
            
            # Frustrated but caring responses
            ResponseTemplate(
                tone=ResponseTone.FIRM,
                emotion=Emotion.FRUSTRATED,
                intervention_level=InterventionLevel.CONTROLLED_ACTION,
                contexts=["repeated_distraction", "ignoring_guidance"],
                templates=[
                    "I'm getting frustrated because I care too much to watch you struggle.",
                    "This isn't easy for me to say, but I have to be honest with you.",
                    "I'm frustrated because I know what you're capable of, and this isn't it.",
                    "It hurts to see you stuck like this when I know you can do better."
                ],
                variations=[
                    "Please, let me help you get back on track.",
                    "I'm doing this because I care about your future.",
                    "This tough love comes from a place of genuine concern."
                ]
            )
        ]
        
        return templates
    
    def _load_context_modifiers(self) -> Dict[str, List[str]]:
        """Load context-specific response modifiers"""
        return {
            "study": [
                "your studies", "your learning", "your education", "your academic goals",
                "your course material", "your assignments", "your research"
            ],
            "work": [
                "your work", "your career", "your professional goals", "your projects",
                "your productivity", "your deadlines", "your responsibilities"
            ],
            "distraction": [
                "this distraction", "this interruption", "this delay", "this setback",
                "this obstacle", "this challenge", "this temptation"
            ],
            "procrastination": [
                "procrastinating", "delaying", "putting things off", "avoiding",
                "postponing", "waiting", "hesitating"
            ],
            "achievement": [
                "your progress", "your success", "your accomplishments", "your growth",
                "your improvement", "your results", "your achievements"
            ]
        }
    
    def _load_emotion_modifiers(self) -> Dict[Emotion, List[str]]:
        """Load emotion-specific response modifiers"""
        return {
            Emotion.CARING: [
                "I'm here for you", "I want to help", "I care about", "I'm concerned about",
                "I'm proud of", "I believe in", "I support", "I'm here to support"
            ],
            Emotion.CONCERNED: [
                "I'm worried about", "I'm concerned about", "I've noticed", "It seems like",
                "I'm wondering if", "I hope you're", "I want to make sure"
            ],
            Emotion.FIRM: [
                "It's time to", "You need to", "Let's be honest", "I have to be direct",
                "This isn't working", "We need to", "I expect better"
            ],
            Emotion.FRUSTRATED: [
                "I'm frustrated because", "This is difficult for me", "I'm struggling with",
                "It hurts me to see", "I can't watch you", "I have to intervene"
            ],
            Emotion.NEUTRAL: [
                "I notice", "I see", "It appears", "It seems", "I observe", "I detect"
            ],
            Emotion.PATIENT: [
                "Take your time", "Whenever you're ready", "No rush", "At your pace",
                "I'll wait", "When you feel ready"
            ]
        }
    
    def generate_response(self, 
                         emotional_state: Dict,
                         perception_summary: Dict,
                         context: str = "general",
                         user_input: Optional[str] = None) -> str:
        """Generate emotionally-aware response"""
        
        # Extract emotional information
        emotion = Emotion(emotional_state.get('emotion', 'neutral'))
        intervention_level = InterventionLevel(emotional_state.get('intervention_level', 0))
        care_level = emotional_state.get('care', 0.5)
        frustration_level = emotional_state.get('frustration', 0.0)
        
        # Extract perception information
        activity_type = perception_summary.get('current_activity', 'idle')
        is_distracted = perception_summary.get('is_distracted', False)
        is_studying = perception_summary.get('is_studying', False)
        procrastination_score = perception_summary.get('procrastination_score', 0.0)
        
        # Determine appropriate tone
        tone = self._determine_tone(emotion, intervention_level, care_level, frustration_level)
        
        # Select appropriate template
        template = self._select_template(emotion, intervention_level, context, activity_type)
        
        if not template:
            return self._generate_fallback_response(emotional_state, perception_summary)
        
        # Generate base response
        base_response = random.choice(template.templates)
        
        # Add context-specific modifications
        response = self._apply_context_modifications(base_response, context, activity_type, perception_summary)
        
        # Add emotional modifiers
        response = self._apply_emotional_modifiers(response, emotion, care_level, frustration_level)
        
        # Add personalization based on user input
        if user_input:
            response = self._personalize_response(response, user_input)
        
        # Add variation if needed
        if random.random() < 0.3:  # 30% chance to add variation
            variation = random.choice(template.variations)
            response = f"{response} {variation}"
        
        return response
    
    def _determine_tone(self, emotion: Emotion, intervention_level: InterventionLevel, 
                       care_level: float, frustration_level: float) -> ResponseTone:
        """Determine appropriate response tone"""
        
        if frustration_level > 0.7:
            return ResponseTone.FIRM
        
        if intervention_level == InterventionLevel.CONTROLLED_ACTION:
            return ResponseTone.FIRM
        
        if intervention_level == InterventionLevel.FIRM_GUIDANCE:
            return ResponseTone.FIRM if frustration_level > 0.4 else ResponseTone.CONCERNED
        
        if care_level > 0.7:
            return ResponseTone.CARING
        
        if emotion == Emotion.CONCERNED:
            return ResponseTone.CONCERNED
        
        if emotion == Emotion.CARING:
            return ResponseTone.SUPPORTIVE
        
        return ResponseTone.NEUTRAL
    
    def _select_template(self, emotion: Emotion, intervention_level: InterventionLevel, 
                        context: str, activity_type: str) -> Optional[ResponseTemplate]:
        """Select appropriate response template"""
        
        # Filter templates by emotion and intervention level
        matching_templates = [
            t for t in self.response_templates
            if t.emotion == emotion and t.intervention_level == intervention_level
        ]
        
        # If no exact match, try by intervention level only
        if not matching_templates:
            matching_templates = [
                t for t in self.response_templates
                if t.intervention_level == intervention_level
            ]
        
        # Filter by context
        if matching_templates and context != "general":
            context_matching = [
                t for t in matching_templates
                if context in t.contexts or "general" in t.contexts
            ]
            if context_matching:
                matching_templates = context_matching
        
        # Return random matching template
        return random.choice(matching_templates) if matching_templates else None
    
    def _apply_context_modifications(self, response: str, context: str, 
                                   activity_type: str, perception: Dict) -> str:
        """Apply context-specific modifications to response"""
        
        # Add activity-specific references
        if activity_type == "study" and "study" in self.context_modifiers:
            study_ref = random.choice(self.context_modifiers["study"])
            response = response.replace("your goals", f"{study_ref}")
        
        elif activity_type == "work" and "work" in self.context_modifiers:
            work_ref = random.choice(self.context_modifiers["work"])
            response = response.replace("your goals", f"{work_ref}")
        
        elif perception.get("is_distracted") and "distraction" in self.context_modifiers:
            distraction_ref = random.choice(self.context_modifiers["distraction"])
            response = response.replace("this", distraction_ref)
        
        # Add procrastination references if high score
        if perception.get("procrastination_score", 0) > 0.6 and "procrastination" in self.context_modifiers:
            proc_ref = random.choice(self.context_modifiers["procrastination"])
            response = response.replace("struggling", proc_ref)
        
        return response
    
    def _apply_emotional_modifiers(self, response: str, emotion: Emotion, 
                                  care_level: float, frustration_level: float) -> str:
        """Apply emotional modifiers to response"""
        
        if emotion in self.emotion_modifiers:
            modifiers = self.emotion_modifiers[emotion]
            
            # Add emotional prefix based on levels
            if care_level > 0.8 and emotion == Emotion.CARING:
                prefix = random.choice(modifiers[:4])  # Caring modifiers
                response = f"{prefix} {response}"
            
            elif frustration_level > 0.6 and emotion == Emotion.FRUSTRATED:
                prefix = random.choice(modifiers[:4])  # Frustrated modifiers
                response = f"{prefix} {response}"
            
            elif emotion == Emotion.CONCERNED:
                prefix = random.choice(modifiers[:3])  # Concerned modifiers
                response = f"{prefix} {response}"
        
        return response
    
    def _personalize_response(self, response: str, user_input: str) -> str:
        """Personalize response based on user input"""
        
        # Simple personalization - acknowledge user's input
        if "thank" in user_input.lower():
            response = f"You're welcome. {response}"
        elif "sorry" in user_input.lower():
            response = f"No need to apologize. {response}"
        elif "help" in user_input.lower():
            response = f"I'm here to help. {response}"
        
        return response
    
    def _generate_fallback_response(self, emotional_state: Dict, perception_summary: Dict) -> str:
        """Generate fallback response when no template matches"""
        
        emotion = emotional_state.get('emotion', 'neutral')
        care_level = emotional_state.get('care', 0.5)
        
        if care_level > 0.7:
            return "I'm here to support you. How can I help you stay focused on your goals?"
        
        elif emotion == "concerned":
            return "I'm concerned about your current situation. Is there anything I can do to help?"
        
        elif emotion == "frustrated":
            return "I'm frustrated because I care about your success. Let's work together to get back on track."
        
        else:
            return "I'm monitoring your progress and I'm here to help when you need me."
    
    def generate_intervention_response(self, intervention_level: InterventionLevel, 
                                     context: Dict) -> str:
        """Generate response specifically for interventions"""
        
        emotional_state = context.get('emotional_state', {})
        perception_summary = context.get('perception_summary', {})
        
        # Generate base emotional response
        response = self.generate_response(
            emotional_state, 
            perception_summary, 
            context="intervention"
        )
        
        # Add intervention-specific elements
        if intervention_level == InterventionLevel.CONTROLLED_ACTION:
            response += " I'm going to take action to help you refocus."
        
        elif intervention_level == InterventionLevel.FIRM_GUIDANCE:
            response += " Please take this guidance seriously."
        
        return response
    
    def get_status_response(self, system_status: Dict) -> str:
        """Generate response for status inquiries"""
        
        emotional_state = system_status.get('emotional_state', {})
        perception_summary = system_status.get('perception_summary', {})
        
        emotion = emotional_state.get('emotion', 'neutral')
        care_level = emotional_state.get('care', 0.5)
        frustration_level = emotional_state.get('frustration', 0.0)
        
        # Build status response
        responses = []
        
        # Emotional state
        if emotion == "caring":
            responses.append("I'm feeling caring and supportive right now.")
        elif emotion == "concerned":
            responses.append("I'm feeling concerned about your progress.")
        elif emotion == "frustrated":
            responses.append("I'm feeling frustrated but I still care deeply.")
        else:
            responses.append("I'm feeling balanced and ready to help.")
        
        # Current activity
        activity = perception_summary.get('current_activity', 'unknown')
        if activity == "study":
            responses.append("I see you're studying, which is great!")
        elif activity == "distraction":
            responses.append("I notice you might be distracted.")
        
        # Combine responses
        return " ".join(responses)


# Global response generator instance
_response_generator = None

def get_response_generator() -> EmotionalResponseGenerator:
    """Get global response generator instance"""
    global _response_generator
    if _response_generator is None:
        _response_generator = EmotionalResponseGenerator()
    return _response_generator
