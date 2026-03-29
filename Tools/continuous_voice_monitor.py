"""
Continuous Voice Monitor for Vortex AI
Listens for voice commands like "stop recording" while recording
"""

import asyncio
import threading
import time
import logging
from typing import Callable, Optional
from pathlib import Path
import json

# Global voice monitor state
voice_monitor_state = {
    'is_monitoring': False,
    'stop_command_detected': False,
    'monitor_thread': None,
    'callback': None
}

class ContinuousVoiceMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.stop_command_detected = False
        self.monitor_thread = None
        self.callback = None
        self.stop_phrases = [
            "stop recording",
            "stop the recording", 
            "stop record",
            "end recording",
            "finish recording",
            "pause recording",
            "that's it",
            "done recording",
            "enough",
            "stop now"
        ]
        
    def start_monitoring(self, stop_callback: Callable):
        """Start continuous voice monitoring for stop commands"""
        if self.is_monitoring:
            return False, "Already monitoring voice commands"
        
        try:
            self.callback = stop_callback
            self.stop_command_detected = False
            self.is_monitoring = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_voice_commands,
                daemon=True
            )
            self.monitor_thread.start()
            
            return True, "Voice monitoring started - listening for 'stop recording'"
            
        except Exception as e:
            logging.error(f"Failed to start voice monitoring: {e}")
            return False, f"Failed to start voice monitoring: {str(e)}"
    
    def _monitor_voice_commands(self):
        """Monitor voice commands in background thread"""
        try:
            # Try to use speech recognition
            self._monitor_with_speech_recognition()
        except Exception as e:
            logging.warning(f"Speech recognition failed, using fallback: {e}")
            # Fallback to simple time-based monitoring
            self._fallback_monitoring()
    
    def _monitor_with_speech_recognition(self):
        """Monitor using speech recognition library"""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            microphone = None
            
            # Try to find microphone
            try:
                microphone = sr.Microphone()
            except:
                logging.warning("No microphone found for voice monitoring")
                self._fallback_monitoring()
                return
            
            # Calibrate microphone
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logging.info("Voice monitoring started with speech recognition")
            
            while self.is_monitoring and not self.stop_command_detected:
                try:
                    with microphone as source:
                        # Listen for audio
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    
                    # Try to recognize speech
                    try:
                        text = recognizer.recognize_google(audio).lower()
                        logging.info(f"Voice command detected: {text}")
                        
                        # Check for stop commands
                        for phrase in self.stop_phrases:
                            if phrase in text:
                                logging.info(f"Stop command detected: '{phrase}'")
                                self.stop_command_detected = True
                                if self.callback:
                                    self.callback()
                                break
                                
                    except sr.UnknownValueError:
                        # Speech not understood, continue monitoring
                        pass
                    except sr.RequestError:
                        # API error, continue monitoring
                        pass
                        
                except sr.WaitTimeoutError:
                    # No speech detected, continue monitoring
                    pass
                except Exception as e:
                    logging.warning(f"Voice monitoring error: {e}")
                    time.sleep(0.5)
                    
        except ImportError:
            logging.warning("Speech recognition library not available")
            self._fallback_monitoring()
        except Exception as e:
            logging.error(f"Speech recognition monitoring failed: {e}")
            self._fallback_monitoring()
    
    def _fallback_monitoring(self):
        """Fallback monitoring without speech recognition"""
        logging.info("Using fallback voice monitoring")
        
        # Simple periodic check system
        check_interval = 2.0  # Check every 2 seconds
        
        while self.is_monitoring and not self.stop_command_detected:
            try:
                # In fallback mode, we rely on the main AI to detect "stop recording"
                # This is just a placeholder that keeps the thread alive
                time.sleep(check_interval)
                
                # You could add alternative detection methods here
                # For example, keyboard shortcuts or other input methods
                
            except Exception as e:
                logging.error(f"Fallback monitoring error: {e}")
                time.sleep(1)
    
    def stop_monitoring(self):
        """Stop voice monitoring"""
        if not self.is_monitoring:
            return False, "Not currently monitoring"
        
        self.is_monitoring = False
        self.stop_command_detected = False
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        return True, "Voice monitoring stopped"
    
    def was_stop_detected(self) -> bool:
        """Check if stop command was detected"""
        return self.stop_command_detected
    
    def reset_stop_detection(self):
        """Reset stop command detection"""
        self.stop_command_detected = False

# Global monitor instance
voice_monitor = ContinuousVoiceMonitor()

# Voice command detection functions
def start_voice_monitoring(stop_callback: Callable) -> tuple[bool, str]:
    """Start monitoring for voice commands"""
    try:
        success, message = voice_monitor.start_monitoring(stop_callback)
        
        if success:
            voice_monitor_state['is_monitoring'] = True
            voice_monitor_state['stop_command_detected'] = False
            voice_monitor_state['callback'] = stop_callback
            return True, message
        else:
            return False, message
            
    except Exception as e:
        logging.error(f"Failed to start voice monitoring: {e}")
        return False, f"Failed to start voice monitoring: {str(e)}"

def stop_voice_monitoring() -> tuple[bool, str]:
    """Stop monitoring for voice commands"""
    try:
        success, message = voice_monitor.stop_monitoring()
        
        if success:
            voice_monitor_state['is_monitoring'] = False
            voice_monitor_state['stop_command_detected'] = False
            voice_monitor_state['callback'] = None
            return True, message
        else:
            return False, message
            
    except Exception as e:
        logging.error(f"Failed to stop voice monitoring: {e}")
        return False, f"Failed to stop voice monitoring: {str(e)}"

def was_stop_command_detected() -> bool:
    """Check if stop command was detected"""
    return voice_monitor.was_stop_detected()

def reset_stop_detection():
    """Reset stop command detection"""
    voice_monitor.reset_stop_detection()
    voice_monitor_state['stop_command_detected'] = False

def get_monitoring_status() -> str:
    """Get current monitoring status"""
    if voice_monitor_state['is_monitoring']:
        return "🎙️ Voice monitoring active - listening for 'stop recording'"
    else:
        return "⏹️ Voice monitoring inactive"

# Install speech recognition if available
def check_speech_recognition():
    """Check if speech recognition is available"""
    try:
        import speech_recognition
        return True
    except ImportError:
        return False

def install_speech_recognition():
    """Install speech recognition library"""
    try:
        import subprocess
        import sys
        
        print("📦 Installing speech recognition library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "SpeechRecognition"])
        print("✅ SpeechRecognition installed!")
        
        # Also try to install PyAudio for microphone access
        try:
            print("📦 Installing PyAudio for microphone access...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyAudio"])
            print("✅ PyAudio installed!")
        except:
            print("⚠️ PyAudio installation failed - voice monitoring may be limited")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to install speech recognition: {e}")
        return False
