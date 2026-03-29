import asyncio
import time
import threading
from livekit.agents import function_tool
from typing import Optional

class WakeWordDetector:
    """Manages wake word detection and keeps AI session active"""
    
    def __init__(self):
        self.last_activity = time.time()
        self.session_active = True
        self.wake_words = ["vortex", "hey vortex", "ok vortex", "vortex ai"]
        self.heartbeat_thread = None
        self.inactivity_timeout = 120  # 2 minutes
        
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = time.time()
        # Silent update - no message output
    
    def start_heartbeat(self):
        """Start background heartbeat to keep session alive"""
        if self.heartbeat_thread is None or not self.heartbeat_thread.is_alive():
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
            self.heartbeat_thread.start()
            print("💓 Heartbeat started - Session will stay active")
    
    def _heartbeat_worker(self):
        """Background worker to maintain session activity"""
        while self.session_active:
            current_time = time.time()
            time_since_activity = current_time - self.last_activity
            
            # Send heartbeat every 30 seconds to prevent timeout (silent)
            if time_since_activity > 30:
                # Silent heartbeat - no message output
                self.last_activity = current_time
            
            # Check for inactivity timeout
            if time_since_activity > self.inactivity_timeout:
                print(f"⚠️ Inactivity detected: {time_since_activity:.0f}s")
                print("🎤 Say 'Vortex' to reactivate the session!")
            
            time.sleep(10)  # Check every 10 seconds
    
    def detect_wake_word(self, text: str) -> bool:
        """Check if text contains a wake word"""
        text_lower = text.lower().strip()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                print(f"🎯 Wake word detected: '{wake_word}'")
                self.update_activity()
                return True
        
        return False
    
    def stop(self):
        """Stop the heartbeat system"""
        self.session_active = False
        print("💓 Heartbeat stopped")

# Global instance
wake_detector = WakeWordDetector()

@function_tool()
def keep_session_alive() -> str:
    """
    Keep the AI session active and prevent timeouts.
    
    Returns:
        str: Confirmation that session is being kept alive
    """
    wake_detector.start_heartbeat()
    wake_detector.update_activity()
    return "💓 Session heartbeat started - I'll stay active and listen for your commands!"

@function_tool()
def reactivate_session() -> str:
    """
    Reactivate the AI session when it becomes inactive.
    
    Returns:
        str: Confirmation that session has been reactivated
    """
    wake_detector.update_activity()
    wake_detector.start_heartbeat()
    return "🔥 Session reactivated! I'm listening and ready to help!"

@function_tool()
def check_session_status() -> str:
    """
    Check the current session activity status.
    
    Returns:
        str: Current session status information
    """
    current_time = time.time()
    time_since_activity = current_time - wake_detector.last_activity
    
    if time_since_activity < 30:
        status = "🟢 Active"
    elif time_since_activity < wake_detector.inactivity_timeout:
        status = "🟡 Idle"
    else:
        status = "🔴 Inactive"
    
    return f"Session Status: {status} - Last activity: {time_since_activity:.0f}s ago"

@function_tool()
def set_inactivity_timeout(seconds: int) -> str:
    """
    Set the inactivity timeout for the session.
    
    Args:
        seconds (int): Timeout in seconds before session becomes inactive
        
    Returns:
        str: Confirmation of timeout setting
    """
    wake_detector.inactivity_timeout = seconds
    return f"⏱️ Inactivity timeout set to {seconds} seconds"
