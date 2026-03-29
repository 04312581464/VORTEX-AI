import pyautogui
import os
from datetime import datetime
from livekit.agents import function_tool

# Verify pyautogui is available
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

@function_tool()
async def screen_short() -> str:
    """
    Takes a screenshot of entire screen and saves it in OneDrive Pictures/vortex_screenshots folder.
    
    Returns:
        str: Confirmation message that screenshot was taken and saved.
    """
    if not PYAUTOGUI_AVAILABLE:
        return "❌ PyAutoGUI module not found. Please install with: pip install pyautogui"
    
    try:
        # OneDrive Pictures folder path (using your actual OneDrive path)
        onedrive_path = r"C:\Users\manju\OneDrive"
        pictures_folder = os.path.join(onedrive_path, "Pictures", "vortex_screenshots")
        
        # Create Pictures folder if it doesn't exist
        pictures_base = os.path.join(onedrive_path, "Pictures")
        if not os.path.exists(pictures_base):
            os.makedirs(pictures_base)
        
        # Create vortex_screenshots folder if it doesn't exist
        if not os.path.exists(pictures_folder):
            os.makedirs(pictures_folder)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Screenshot_{timestamp}.png"
        filepath = os.path.join(pictures_folder, filename)
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        return f"📸 Screenshot le liya gaya hai! OneDrive Pictures/vortex_screenshots me save ho gaya. File: {filename}"
        
    except Exception as e:
        return f"❌ Screenshot lene mein error: {str(e)}"