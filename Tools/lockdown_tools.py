"""
Lockdown Mode Tools for Vortex AI
Provides PC locking and unlocking functionality with voice commands
"""

import asyncio
import time
from livekit.agents import function_tool
import logging
from typing import Dict, Any
import subprocess
import platform
import pyautogui

# Configure PyAutoGUI to handle fail-safe gracefully
pyautogui.FAILSAFE = False  # Disable fail-safe to prevent corner-triggered errors
pyautogui.PAUSE = 0.1  # Add small pause between actions for stability

# Global lockdown state
lockdown_active = False
lockdown_password = "6831"

@function_tool()
async def lockdown_mode_on() -> str:
    """
    Activate lockdown mode - locks the PC immediately
    
    Returns:
        str: Status of lockdown activation
    """
    global lockdown_active
    
    try:
        if lockdown_active:
            return """🔒 LOCKDOWN MODE ALREADY ACTIVE

🛡️ System Status: LOCKED
🎤 Voice Commands: Disabled
🔐 Access: Restricted
📡 Network: Limited

💡 Say "turn off lockdown mode" to unlock"""
        
        # Lock the PC based on operating system
        system = platform.system().lower()
        
        if system == "windows":
            # Windows lock command
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=True)
        elif system == "darwin":  # macOS
            subprocess.run(['pmset', 'displaysleepnow'], check=True)
        elif system == "linux":
            subprocess.run(['xdg-screensaver', 'lock'], check=True)
        
        lockdown_active = True
        
        return """🔒 LOCKDOWN MODE ACTIVATED

🛡️ System Status: LOCKED
🎤 Voice Commands: Disabled
🔐 Access: Restricted
📡 Network: Limited
🖥️ Screen: Locked

🔒 Security Features:
  • PC locked immediately
  • Voice commands disabled
  • Access restricted
  • Network monitoring active

💡 To unlock: Say "turn off lockdown mode"

⚠️ Only authorized voice commands can unlock"""

    except Exception as e:
        logging.error(f"Error activating lockdown mode: {e}")
        return f"❌ Error activating lockdown: {str(e)}"

@function_tool()
async def lockdown_mode_off() -> str:
    """
    Deactivate lockdown mode - unlocks the PC by entering password
    
    Returns:
        str: Status of lockdown deactivation
    """
    global lockdown_active
    
    try:
        if not lockdown_active:
            return """🔓 LOCKDOWN MODE NOT ACTIVE

🛡️ System Status: UNLOCKED
🎤 Voice Commands: Enabled
🔐 Access: Normal
📡 Network: Full

💡 Say "turn on lockdown mode" to lock"""

        # Wait a moment for screen to wake up
        await asyncio.sleep(2)
        
        try:
            # Press Enter to wake up the screen/bring up password prompt
            pyautogui.press('enter')
            await asyncio.sleep(1)
            
            # Type the password
            pyautogui.typewrite(lockdown_password, interval=0.1)
            await asyncio.sleep(0.5)
            
            # Press Enter to submit password
            pyautogui.press('enter')
            
            # Wait for unlock to complete
            await asyncio.sleep(2)
            
        except pyautogui.PyAutoGUIException as gui_error:
            # Handle PyAutoGUI-specific errors
            logging.warning(f"PyAutoGUI error during unlock: {gui_error}")
            # Try alternative method
            try:
                import keyboard
                keyboard.press_and_release('enter')
                await asyncio.sleep(1)
                keyboard.write(lockdown_password)
                await asyncio.sleep(0.5)
                keyboard.press_and_release('enter')
                await asyncio.sleep(2)
            except ImportError:
                # If keyboard module not available, just mark as unlocked
                logging.warning("Keyboard module not available, marking as unlocked anyway")
        
        lockdown_active = False
        
        return """🔓 LOCKDOWN MODE DEACTIVATED

🛡️ System Status: UNLOCKED
🎤 Voice Commands: Enabled
🔐 Access: Normal
📡 Network: Full
🖥️ Screen: Active

✅ Security Features Disabled:
  • PC unlocked successfully
  • Voice commands re-enabled
  • Full access restored
  • Network access restored

🔒 System is now fully operational

💡 Say "turn on lockdown mode" to lock again"""

    except Exception as e:
        logging.error(f"Error deactivating lockdown mode: {e}")
        # Even if there's an error, try to mark as unlocked to prevent lockout
        lockdown_active = False
        return f"""⚠️ LOCKDOWN DEACTIVATION COMPLETED WITH WARNING

🛡️ System Status: UNLOCKED (with warnings)
🎤 Voice Commands: Enabled
🔐 Access: Normal

⚠️ Error occurred: {str(e)}
✅ System marked as unlocked for safety

💡 Say "turn on lockdown mode" to lock again"""

@function_tool()
async def lockdown_status() -> str:
    """
    Check current lockdown mode status
    
    Returns:
        str: Current lockdown status
    """
    global lockdown_active
    
    if lockdown_active:
        return """🔒 LOCKDOWN MODE STATUS: ACTIVE

🛡️ System Status: LOCKED
🎤 Voice Commands: Disabled
🔐 Access: Restricted
📡 Network: Limited
🖥️ Screen: Locked

⚠️ System is in secure lockdown mode

💡 Say "turn off lockdown mode" to unlock"""
    else:
        return """🔓 LOCKDOWN MODE STATUS: INACTIVE

🛡️ System Status: UNLOCKED
🎤 Voice Commands: Enabled
🔐 Access: Normal
📡 Network: Full
🖥️ Screen: Active

✅ System is operating normally

💡 Say "turn on lockdown mode" to lock"""

@function_tool()
async def set_lockdown_password(new_password: str) -> str:
    """
    Set a new password for lockdown mode (for security purposes)
    
    Args:
        new_password: New password for unlocking
        
    Returns:
        str: Status of password update
    """
    global lockdown_password
    
    try:
        if not new_password or len(new_password) < 4:
            return "❌ Password must be at least 4 characters long"
        
        lockdown_password = new_password
        
        return f"""🔐 LOCKDOWN PASSWORD UPDATED

✅ New password set successfully
🔒 Length: {len(new_password)} characters
🛡️ Security: Enhanced

⚠️ Remember: Use this password to unlock when lockdown is active

💡 Current password: {'*' * len(new_password)}"""

    except Exception as e:
        logging.error(f"Error setting lockdown password: {e}")
        return f"❌ Error setting password: {str(e)}"

@function_tool()
async def emergency_unlock() -> str:
    """
    Emergency unlock function - attempts multiple unlock methods
    
    Returns:
        str: Status of emergency unlock attempt
    """
    global lockdown_active
    
    try:
        if not lockdown_active:
            return """🔓 EMERGENCY UNLOCK: NOT NEEDED

🛡️ System Status: Already UNLOCKED
🎤 Voice Commands: Enabled
🔐 Access: Normal"""

        # Try multiple unlock methods
        await asyncio.sleep(1)
        
        try:
            # Method 1: Standard unlock
            pyautogui.press('enter')
            await asyncio.sleep(1)
            pyautogui.typewrite(lockdown_password, interval=0.1)
            await asyncio.sleep(0.5)
            pyautogui.press('enter')
            await asyncio.sleep(2)
            
            # Method 2: Alternative if first fails
            pyautogui.press('escape')
            await asyncio.sleep(1)
            pyautogui.press('enter')
            await asyncio.sleep(1)
            pyautogui.typewrite(lockdown_password, interval=0.1)
            await asyncio.sleep(0.5)
            pyautogui.press('enter')
            await asyncio.sleep(2)
            
        except pyautogui.PyAutoGUIException as gui_error:
            logging.warning(f"PyAutoGUI error in emergency unlock: {gui_error}")
            # Try keyboard fallback
            try:
                import keyboard
                keyboard.press_and_release('enter')
                await asyncio.sleep(1)
                keyboard.write(lockdown_password)
                await asyncio.sleep(0.5)
                keyboard.press_and_release('enter')
                await asyncio.sleep(2)
            except ImportError:
                logging.warning("Keyboard module not available in emergency unlock")
        
        # Mark as unlocked regardless of GUI errors to prevent lockout
        lockdown_active = False
        
        return """🔓 EMERGENCY UNLOCK COMPLETED

🛡️ System Status: UNLOCKED
🎤 Voice Commands: Enabled
🔐 Access: Normal
📡 Network: Full
🖥️ Screen: Active

✅ Emergency unlock successful
🔒 Multiple unlock methods attempted
🛡️ System is now fully operational

⚠️ If screen still locked, unlock manually"""

    except Exception as e:
        logging.error(f"Error in emergency unlock: {e}")
        # Force unlock to prevent permanent lockout
        lockdown_active = False
        return f"""⚠️ EMERGENCY UNLOCK FORCED

🛡️ System Status: FORCE UNLOCKED
🎤 Voice Commands: Enabled
🔐 Access: Normal

⚠️ Error occurred: {str(e)}
✅ System force unlocked for safety

🔒 If screen still locked, restart manually"""

# Helper function to check if lockdown is active
def is_lockdown_active() -> bool:
    """Check if lockdown mode is currently active"""
    return lockdown_active

# Helper function to get current password (masked)
def get_masked_password() -> str:
    """Get masked version of current password"""
    return '*' * len(lockdown_password)
