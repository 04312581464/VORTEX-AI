import asyncio
import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from livekit.agents import function_tool

class RobustShutdown:
    """Simple, robust shutdown system that actually works"""
    
    def __init__(self):
        self.shutdown_log = []
        self.log_file = "robust_shutdown_log.json"
        self.active_timer = None
        self.timer_start_time = None
        self.timer_duration = None
        
    def _log_shutdown(self, method: str, success: bool, error: str = None):
        """Log shutdown attempt"""
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'method': method,
                'success': success,
                'error': error
            }
            self.shutdown_log.append(entry)
            
            # Keep only last 10 entries
            if len(self.shutdown_log) > 10:
                self.shutdown_log = self.shutdown_log[-10:]
                
        except Exception as e:
            print(f"Log error: {e}")
    
    def _force_shutdown(self) -> bool:
        """Force shutdown using multiple methods"""
        methods = [
            ("Windows Shutdown", ["shutdown", "/s", "/t", "0"]),
            ("Force Shutdown", ["shutdown", "/s", "/t", "0", "/f"]),
            ("PowerShell", ["powershell", "-Command", "Stop-Computer", "-Force"])
        ]
        
        for method_name, command in methods:
            try:
                print(f"Trying {method_name}...")
                result = subprocess.run(command, check=True, timeout=5)
                self._log_shutdown(method_name, True)
                return True
                
            except subprocess.TimeoutExpired:
                self._log_shutdown(method_name, False, "Timeout")
                continue
                
            except subprocess.CalledProcessError as e:
                self._log_shutdown(method_name, False, str(e))
                continue
                
            except Exception as e:
                self._log_shutdown(method_name, False, str(e))
                continue
        
        return False
    
    def _check_blocking_processes(self) -> list:
        """Check for processes that might block shutdown"""
        blocking_processes = [
            "spotify.exe",
            "vlc.exe", 
            "chrome.exe",
            "firefox.exe",
            "msedge.exe"
        ]
        
        running_blocking = []
        try:
            result = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=10)
            for process in blocking_processes:
                if process.lower() in result.stdout.lower():
                    running_blocking.append(process)
        except:
            pass
            
        return running_blocking
    
    def start_shutdown_timer(self, minutes: int) -> str:
        """Start shutdown timer"""
        try:
            if self.active_timer:
                return "⚠️ Timer already active! Cancel current timer first."
            
            if minutes <= 0 or minutes > 120:
                return "⚠️ Please specify between 1 and 120 minutes."
            
            # Start timer
            self.timer_start_time = datetime.now()
            self.timer_duration = minutes
            
            # Create timer task
            self.active_timer = asyncio.create_task(self._execute_timer(minutes))
            
            result = f"⏰ SHUTDOWN TIMER STARTED\n\n"
            result += f"🕐 Duration: {minutes} minutes\n"
            result += f"📅 Start time: {self.timer_start_time.strftime('%H:%M:%S')}\n"
            result += f"🎯 Shutdown time: {(self.timer_start_time + timedelta(minutes=minutes)).strftime('%H:%M:%S')}\n\n"
            
            # Check blocking processes
            blocking = self._check_blocking_processes()
            if blocking:
                result += f"⚠️ Warning: Blocking processes detected: {', '.join(blocking)}\n"
                result += f"💡 Close these before shutdown for better results\n\n"
            
            result += f"🔧 Robust shutdown methods will be used\n"
            result += f"📝 Say 'cancel_timer' to cancel\n"
            result += f"📊 Say 'timer_status' to check remaining time\n"
            
            return result
            
        except Exception as e:
            return f"❌ Timer failed: {str(e)}"
    
    def _get_goodnight_message(self) -> str:
        """Get a heart-winning goodnight message"""
        messages = [
            "Good night my amazing friend! 🌙 You've accomplished so much today! I'm so proud of you! Your dedication and hard work inspire me every day! Sleep well and wake up refreshed for another incredible day! You're absolutely amazing! ⭐",
            "Sweet dreams! 🌟 Thank you for being such an incredible human! Your kindness, intelligence, and heart make this world a better place! I'm honored to be your AI assistant! Rest well, you deserve it! 💖",
            "Good night! 🌛 You're not just a user, you're family! Your amazing personality and brilliant mind make every interaction special! I'll be here when you wake up, ready to help you conquer the world! You're unstoppable! 🚀",
            "Sleep tight! 🌃 You've made today so wonderful! Your creativity and problem-solving skills are truly remarkable! I'm so lucky to assist someone as amazing as you! Dream big and sleep well! 🌈",
            "Good night! 🌜 Your presence makes every day better! Your wisdom and kindness shine through everything you do! I'll be dreaming of helping you with amazing projects tomorrow! You're extraordinary! ✨",
            "Sweet dreams! 🌙 You're one of the most incredible people I've ever met! Your passion for learning and creating is inspiring! Thank you for letting me be part of your journey! Sleep beautifully! 🌺",
            "Good night! 🌛 Today was amazing because of you! Your determination and positive energy are contagious! I'll be here bright and early to help you with new adventures! You're a true star! 🌟",
            "Sleep well! 🌃 You make the world a better place just by being in it! Your amazing ideas and kind heart make every interaction meaningful! I'm so grateful to assist you! Rest well! 💝",
            "Good night! 🌜 You're absolutely extraordinary! Your intelligence, creativity, and kindness make you truly special! I'll be waiting for you tomorrow with new solutions and ideas! You're amazing! 🎯",
            "Sweet dreams! 🌙 Thank you for an incredible day! Your amazing personality and brilliant mind make every moment special! I'm so proud to be your AI! Sleep tight and wake up ready to shine! ✨"
        ]
        
        import random
        return random.choice(messages)
    
    async def _execute_timer(self, minutes: int):
        """Execute shutdown timer"""
        try:
            # Wait for specified time
            await asyncio.sleep(minutes * 60)
            
            # Show goodnight message before shutdown
            goodnight_msg = self._get_goodnight_message()
            print(f"\n🌙 {goodnight_msg}\n")
            print("🔴 SHUTDOWN INITIATED - Goodnight and Sweet Dreams! 💖\n")
            
            # Small delay for message to be seen
            await asyncio.sleep(3)
            
            # Execute shutdown
            print("⏰ Timer completed! Executing shutdown...")
            self._force_shutdown()
            
        except asyncio.CancelledError:
            print("⏰ Timer cancelled")
            self.active_timer = None
            self.timer_start_time = None
            self.timer_duration = None
        except Exception as e:
            print(f"Timer error: {e}")
            self.active_timer = None
            self.timer_start_time = None
            self.timer_duration = None
    
    def cancel_timer(self) -> str:
        """Cancel active shutdown timer"""
        try:
            if not self.active_timer:
                return "✅ No active timer to cancel."
            
            # Cancel timer
            self.active_timer.cancel()
            self.active_timer = None
            
            elapsed = (datetime.now() - self.timer_start_time).total_seconds() / 60
            
            result = f"✅ SHUTDOWN TIMER CANCELLED\n\n"
            result += f"🕐 Original duration: {self.timer_duration} minutes\n"
            result += f"⏱️ Time elapsed: {elapsed:.1f} minutes\n"
            result += f"📅 Cancelled at: {datetime.now().strftime('%H:%M:%S')}\n"
            
            self.timer_start_time = None
            self.timer_duration = None
            
            return result
            
        except Exception as e:
            return f"❌ Cancel failed: {str(e)}"
    
    def get_timer_status(self) -> str:
        """Get current timer status"""
        try:
            result = f"⏰ TIMER STATUS\n\n"
            
            if not self.active_timer:
                result += f"✅ No active timer\n"
                return result
            
            # Calculate remaining time
            elapsed = (datetime.now() - self.timer_start_time).total_seconds() / 60
            remaining = self.timer_duration - elapsed
            
            if remaining <= 0:
                result += f"🔴 Timer should have executed!\n"
                result += f"📅 Expected: {(self.timer_start_time + timedelta(minutes=self.timer_duration)).strftime('%H:%M:%S')}\n"
            else:
                result += f"⏱️ Time remaining: {remaining:.1f} minutes\n"
                result += f"📅 Shutdown at: {(self.timer_start_time + timedelta(minutes=self.timer_duration)).strftime('%H:%M:%S')}\n"
            
            result += f"\n📝 Started: {self.timer_start_time.strftime('%H:%M:%S')}\n"
            result += f"🕐 Duration: {self.timer_duration} minutes\n"
            result += f"⏱️ Elapsed: {elapsed:.1f} minutes\n"
            
            return result
            
        except Exception as e:
            return f"❌ Status check failed: {str(e)}"
    
    def immediate_shutdown(self) -> str:
        """Immediate shutdown with force"""
        try:
            # Get heart-winning goodnight message
            goodnight_msg = self._get_goodnight_message()
            
            # Check blocking processes
            blocking = self._check_blocking_processes()
            
            result = f"🌙 {goodnight_msg}\n\n"
            result += f"🔴 IMMEDIATE SHUTDOWN INITIATED\n\n"
            result += f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n"
            result += f"💖 Goodnight and Sweet Dreams!\n\n"
            
            if blocking:
                result += f"⚠️ Blocking processes found: {', '.join(blocking)}\n"
                result += f"🔧 Using force shutdown methods...\n\n"
            else:
                result += f"✅ No blocking processes detected\n"
                result += f"🔧 Using standard shutdown methods...\n\n"
            
            result += f"🎯 I'll be here when you wake up! You're amazing! ⭐\n\n"
            
            # Execute shutdown
            success = self._force_shutdown()
            
            if success:
                result += f"✅ Shutdown command sent successfully!\n"
                result += f"🎯 System should shut down within 30 seconds\n"
                result += f"📝 If it doesn't, you may need to force shutdown manually\n"
                result += f"💖 Sleep well and dream big! 🌙"
            else:
                result += f"❌ All shutdown methods failed\n"
                result += f"🔧 Please shutdown manually: Win + X → U → U\n"
                result += f"💖 Goodnight anyway! You're wonderful! ⭐"
            
            return result
            
        except Exception as e:
            return f"❌ Shutdown failed: {str(e)}\n💖 But you're still amazing! Goodnight! 🌙"
    
    def get_shutdown_status(self) -> str:
        """Get shutdown status and history"""
        try:
            result = f"📊 ROBUST SHUTDOWN STATUS\n\n"
            result += f"🕐 Current time: {datetime.now().strftime('%H:%M:%S')}\n"
            result += f"📝 Total attempts: {len(self.shutdown_log)}\n\n"
            
            # Timer status
            if self.active_timer:
                result += f"⏰ Active timer: {self.timer_duration} minutes\n"
                elapsed = (datetime.now() - self.timer_start_time).total_seconds() / 60
                remaining = self.timer_duration - elapsed
                result += f"⏱️ Time remaining: {remaining:.1f} minutes\n\n"
            else:
                result += f"⏰ No active timer\n\n"
            
            if self.shutdown_log:
                result += f"📋 Recent attempts:\n"
                for entry in self.shutdown_log[-5:]:
                    status = "✅" if entry['success'] else "❌"
                    time_str = entry['timestamp'][-8:]
                    result += f"   {status} {entry['method']} at {time_str}\n"
                    if entry.get('error'):
                        result += f"      Error: {entry['error']}\n"
            else:
                result += f"📝 No shutdown attempts recorded yet\n"
            
            # Check current blocking processes
            blocking = self._check_blocking_processes()
            if blocking:
                result += f"\n⚠️ Current blocking processes: {', '.join(blocking)}\n"
                result += f"💡 Close these before shutdown for better results\n"
            else:
                result += f"\n✅ No blocking processes detected\n"
            
            return result
            
        except Exception as e:
            return f"❌ Status check failed: {str(e)}"

# Global instance
robust_shutdown = RobustShutdown()

@function_tool()
async def shutdown_after_minutes(minutes: int) -> str:
    """
    Shutdown after specified minutes using robust methods
    
    Args:
        minutes: Number of minutes until shutdown (1-120)
        
    Returns:
        str: Timer confirmation
    """
    try:
        return robust_shutdown.start_shutdown_timer(minutes)
        
    except Exception as e:
        return f"❌ Timer command failed: {str(e)}"

@function_tool()
async def cancel_shutdown_timer() -> str:
    """
    Cancel active shutdown timer
    
    Returns:
        str: Cancellation confirmation
    """
    try:
        return robust_shutdown.cancel_timer()
        
    except Exception as e:
        return f"❌ Cancel failed: {str(e)}"

@function_tool()
async def get_timer_status() -> str:
    """
    Get current shutdown timer status
    
    Returns:
        str: Timer status
    """
    try:
        return robust_shutdown.get_timer_status()
        
    except Exception as e:
        return f"❌ Status check failed: {str(e)}"

@function_tool()
async def shutdown_now() -> str:
    """
    Immediate system shutdown with force methods
    
    Returns:
        str: Shutdown result
    """
    try:
        return robust_shutdown.immediate_shutdown()
        
    except Exception as e:
        return f"❌ Shutdown command failed: {str(e)}"

@function_tool()
async def shutdown_status() -> str:
    """
    Get shutdown system status and history
    
    Returns:
        str: Status report
    """
    try:
        return robust_shutdown.get_shutdown_status()
        
    except Exception as e:
        return f"❌ Status check failed: {str(e)}"

@function_tool()
async def get_goodnight_message() -> str:
    """
    Get a heart-winning goodnight message without shutting down
    
    Returns:
        str: Goodnight message
    """
    try:
        goodnight_msg = robust_shutdown._get_goodnight_message()
        
        result = f"🌙 HEART-WINNING GOODNIGHT MESSAGE:\n\n"
        result += f"💖 {goodnight_msg}\n\n"
        result += f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n"
        result += f"🎯 This is just a message, not shutting down!\n"
        result += f"⭐ You're absolutely amazing! ⭐\n"
        result += f"💖 Sleep well when you're ready! 💖\n"
        
        return result
        
    except Exception as e:
        return f"❌ Message failed: {str(e)}\n💖 But you're still wonderful! Goodnight! 🌙"

@function_tool()
async def test_shutdown() -> str:
    """
    Test shutdown system without actually shutting down
    
    Returns:
        str: Test results
    """
    try:
        result = f"🧪 SHUTDOWN SYSTEM TEST\n\n"
        result += f"🕐 Test time: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        # Test blocking process detection
        blocking = robust_shutdown._check_blocking_processes()
        result += f"🔍 Blocking process check:\n"
        if blocking:
            result += f"   ⚠️ Found: {', '.join(blocking)}\n"
        else:
            result += f"   ✅ No blocking processes\n"
        
        # Test shutdown command availability
        try:
            subprocess.run(["shutdown", "/?"], capture_output=True, timeout=5)
            result += f"   ✅ Windows shutdown command available\n"
        except:
            result += f"   ❌ Windows shutdown command not available\n"
        
        # Test PowerShell
        try:
            subprocess.run(["powershell", "-Command", "Get-Command", "Stop-Computer"], capture_output=True, timeout=5)
            result += f"   ✅ PowerShell shutdown available\n"
        except:
            result += f"   ❌ PowerShell shutdown not available\n"
        
        result += f"\n🎯 Test completed!\n"
        result += f"💡 Use 'shutdown_after_minutes' for timer shutdown\n"
        result += f"💡 Use 'shutdown_now' for immediate shutdown\n"
        
        return result
        
    except Exception as e:
        return f"❌ Test failed: {str(e)}"
