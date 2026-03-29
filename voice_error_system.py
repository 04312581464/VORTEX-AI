"""
Vortex Voice Error System
Speaks errors and important information instead of console logging
"""

from __future__ import annotations
import warnings
import time
from typing import Optional, Dict, Any
from enum import Enum
import threading
import queue
import asyncio
from dataclasses import dataclass, field

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

try:
    import pyttsx3
    TTS_AVAILABLE = True
    # Initialize COM for Windows with error handling
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print(f"⚠️ COM initialization failed: {e}")
        TTS_AVAILABLE = False
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: pyttsx3 not available. Voice errors will be silent.")

try:
    import pygame
    PYGAME_AVAILABLE = True
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"⚠️ Pygame initialization failed: {e}")
        PYGAME_AVAILABLE = False
except ImportError:
    PYGAME_AVAILABLE = False


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class VoiceMessage:
    """Voice message configuration"""
    text: str
    severity: ErrorSeverity
    priority: int = 1  # Higher priority = spoken sooner
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """Comparison for PriorityQueue - compare by priority, then timestamp"""
        if self.priority != other.priority:
            return self.priority > other.priority  # Higher priority = "less than" for min-heap
        return self.timestamp < other.timestamp  # Earlier timestamp = "less than"


class VoiceErrorSystem:
    """Voice-based error and information reporting system"""
    
    def __init__(self):
        self.message_queue = queue.PriorityQueue()
        self.is_speaking = False
        self.enabled = True
        self.tts_engine = None
        self.voice_thread = None
        
        # Voice settings
        self.voice_rate = 150  # Words per minute
        self.voice_volume = 0.8
        
        # Initialize TTS
        self._initialize_tts()
        
        # Start voice thread
        self._start_voice_thread()
    
    def _initialize_tts(self) -> None:
        """Initialize text-to-speech engine"""
        if not TTS_AVAILABLE:
            return
        
        try:
            # Don't initialize TTS here - defer to voice worker thread
            # to avoid COM initialization issues
            self.tts_engine = None
            self._tts_ready = False
            
        except Exception as e:
            print(f"Warning: Could not initialize TTS: {e}")
            self.tts_engine = None
            self._tts_ready = False
    
    def _start_voice_thread(self) -> None:
        """Start background voice thread"""
        self.voice_thread = threading.Thread(target=self._voice_worker, daemon=True)
        self.voice_thread.start()
    
    def _voice_worker(self) -> None:
        """Background thread for speaking messages"""
        # Initialize COM and TTS in this thread for Windows
        if TTS_AVAILABLE and not self.tts_engine:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                
                # Initialize TTS engine in this thread
                self.tts_engine = pyttsx3.init()
                
                # Set voice properties
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Prefer female voice for Vortex
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                    else:
                        # Use first available voice
                        self.tts_engine.setProperty('voice', voices[0].id)
                
                self.tts_engine.setProperty('rate', self.voice_rate)
                self.tts_engine.setProperty('volume', self.voice_volume)
                self._tts_ready = True
                
            except Exception as e:
                print(f"Warning: Could not initialize TTS in voice thread: {e}")
                self.tts_engine = None
                self._tts_ready = False
        
        while True:
            try:
                # Get message from queue (blocks until message available)
                message = self.message_queue.get()
                
                if self.enabled and message and self.tts_engine:
                    self._speak_message(message)
                
                self.message_queue.task_done()
                
                # Small delay between messages
                time.sleep(0.5)
                
            except Exception as e:
                # Don't use voice system to report its own errors
                time.sleep(1)
    
    def _speak_message(self, message: VoiceMessage) -> None:
        """Speak a message using TTS"""
        if not self.tts_engine:
            return
        
        try:
            self.is_speaking = True
            
            # Format message based on severity
            formatted_text = self._format_message(message)
            
            # Speak the message
            self.tts_engine.say(formatted_text)
            self.tts_engine.runAndWait()
            
        except Exception as e:
            # Silent fallback
            pass
        finally:
            self.is_speaking = False
    
    def _format_message(self, message: VoiceMessage) -> str:
        """Format message based on severity"""
        text = message.text
        
        # Add severity prefixes
        if message.severity == ErrorSeverity.CRITICAL:
            text = f"Critical error: {text}"
        elif message.severity == ErrorSeverity.ERROR:
            text = f"Error: {text}"
        elif message.severity == ErrorSeverity.WARNING:
            text = f"Warning: {text}"
        # Info messages don't need prefix
        
        # Clean up technical jargon for speech
        text = self._clean_text_for_speech(text)
        
        return text
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech readability"""
        # Replace technical terms with spoken equivalents
        replacements = {
            'API': 'A P I',
            'HTTP': 'H T T P',
            'HTTPS': 'H T T P S',
            'URL': 'U R L',
            'JSON': 'J son',
            'XML': 'X M L',
            'SQL': 'S Q L',
            'GUI': 'G U I',
            'CPU': 'C P U',
            'GPU': 'G P U',
            'RAM': 'ram',
            'OS': 'operating system',
            'Vortex': 'Vortex',
            'AI': 'A I',
            'TTS': 'text to speech',
            'Exception': 'exception',
            'Error': 'error',
            'Warning': 'warning',
            'Info': 'info',
            'null': 'null',
            'None': 'none',
            'True': 'true',
            'False': 'false',
            'async': 'async',
            'await': 'await',
            'def': 'function',
            'class': 'class',
            'import': 'import',
            'from': 'from',
            '__init__': 'init',
            '__main__': 'main',
            'self': 'self',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Clean up special characters
        text = text.replace('_', ' ')
        text = text.replace('-', ' ')
        text = text.replace('_', ' ')
        
        # Replace file paths with readable format
        if '.py' in text:
            text = text.replace('.py', ' python file')
        if '.txt' in text:
            text = text.replace('.txt', 'text file')
        if '.json' in text:
            text = text.replace('.json', 'j son file')
        
        return text
    
    def speak_error(self, error_message: str, severity: ErrorSeverity = ErrorSeverity.ERROR) -> None:
        """Queue an error message to be spoken"""
        if not self.enabled:
            return
        
        message = VoiceMessage(
            text=error_message,
            severity=severity,
            priority=self._get_priority(severity)
        )
        
        # Put VoiceMessage directly (now has __lt__ method)
        self.message_queue.put(message)
    
    def speak_info(self, info_message: str) -> None:
        """Queue an informational message to be spoken"""
        self.speak_error(info_message, ErrorSeverity.INFO)
    
    def speak_warning(self, warning_message: str) -> None:
        """Queue a warning message to be spoken"""
        self.speak_error(warning_message, ErrorSeverity.WARNING)
    
    def speak_critical(self, critical_message: str) -> None:
        """Queue a critical error message to be spoken"""
        self.speak_error(critical_message, ErrorSeverity.CRITICAL)
    
    def _get_priority(self, severity: ErrorSeverity) -> int:
        """Get priority level for severity"""
        priorities = {
            ErrorSeverity.CRITICAL: 4,
            ErrorSeverity.ERROR: 3,
            ErrorSeverity.WARNING: 2,
            ErrorSeverity.INFO: 1
        }
        return priorities.get(severity, 1)
    
    def enable(self) -> None:
        """Enable voice error reporting"""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable voice error reporting"""
        self.enabled = False
    
    def set_voice_rate(self, rate: int) -> None:
        """Set voice speaking rate"""
        self.voice_rate = max(50, min(300, rate))  # Reasonable range
        if self.tts_engine:
            self.tts_engine.setProperty('rate', self.voice_rate)
    
    def set_voice_volume(self, volume: float) -> None:
        """Set voice volume (0.0 to 1.0)"""
        self.voice_volume = max(0.0, min(1.0, volume))
        if self.tts_engine:
            self.tts_engine.setProperty('volume', self.voice_volume)
    
    def is_available(self) -> bool:
        """Check if voice system is available"""
        return TTS_AVAILABLE and self.tts_engine is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current voice system status"""
        return {
            'enabled': self.enabled,
            'available': self.is_available(),
            'speaking': self.is_speaking,
            'queue_size': self.message_queue.qsize(),
            'voice_rate': self.voice_rate,
            'voice_volume': self.voice_volume
        }
    
    def clear_queue(self) -> None:
        """Clear all pending messages"""
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except queue.Empty:
                break
    
    def speak_immediately(self, message: str, severity: ErrorSeverity = ErrorSeverity.INFO) -> None:
        """Speak a message immediately, bypassing queue"""
        if not self.enabled or not self.tts_engine:
            return
        
        voice_message = VoiceMessage(
            text=message,
            severity=severity,
            priority=999  # Highest priority
        )
        
        # Speak directly without queue
        self._speak_message(voice_message)
    
    def shutdown(self) -> None:
        """Shutdown voice system gracefully"""
        self.enabled = False
        self.clear_queue()
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass


# Global voice error system instance
_voice_error_system = None

def get_voice_error_system() -> VoiceErrorSystem:
    """Get global voice error system instance"""
    global _voice_error_system
    if _voice_error_system is None:
        _voice_error_system = VoiceErrorSystem()
    return _voice_error_system


# Convenience functions
def speak_error(error_message: str, severity: ErrorSeverity = ErrorSeverity.ERROR) -> None:
    """Speak an error message"""
    system = get_voice_error_system()
    system.speak_error(error_message, severity)


def speak_info(info_message: str) -> None:
    """Speak an informational message"""
    system = get_voice_error_system()
    system.speak_info(info_message)


def speak_warning(warning_message: str) -> None:
    """Speak a warning message"""
    system = get_voice_error_system()
    system.speak_warning(warning_message)


def speak_critical(critical_message: str) -> None:
    """Speak a critical error message"""
    system = get_voice_error_system()
    system.speak_critical(critical_message)


def speak_immediately(message: str, severity: ErrorSeverity = ErrorSeverity.INFO) -> None:
    """Speak a message immediately"""
    system = get_voice_error_system()
    system.speak_immediately(message, severity)


def enable_voice_errors() -> None:
    """Enable voice error reporting"""
    system = get_voice_error_system()
    system.enable()


def disable_voice_errors() -> None:
    """Disable voice error reporting"""
    system = get_voice_error_system()
    system.disable()


def get_voice_status() -> Dict[str, Any]:
    """Get voice system status"""
    system = get_voice_error_system()
    return system.get_status()
