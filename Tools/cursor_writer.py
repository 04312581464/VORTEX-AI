import asyncio
import pyautogui
import time
from typing import Dict, Optional, Tuple, Any
from livekit.agents import function_tool

class CursorWriter:
    """Intelligent cursor-aware text writing system"""
    
    def __init__(self):
        self.cursor_position = None
        self.last_cursor_check = 0
        self.cursor_check_interval = 2  # Check every 2 seconds
        self.active_window = None
        self.typing_speed = 0.05  # 50ms between keystrokes
        
    def get_cursor_position(self) -> Tuple[int, int]:
        """Get current cursor position on screen"""
        try:
            return pyautogui.position()
        except Exception as e:
            print(f"Cursor position error: {e}")
            return (0, 0)
    
    def get_active_window_info(self) -> Dict[str, Any]:
        """Get information about the active window"""
        try:
            import psutil
            import win32gui
            
            # Get active window handle
            hwnd = win32gui.GetForegroundWindow()
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get window class
            window_class = win32gui.GetClassName(hwnd)
            
            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)
            window_rect = {
                'left': rect[0],
                'top': rect[1], 
                'right': rect[2],
                'bottom': rect[3]
            }
            
            # Get process info
            _, pid = win32gui.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except:
                process_name = "Unknown"
            
            return {
                'title': window_title,
                'class': window_class,
                'process': process_name,
                'rect': window_rect,
                'pid': pid,
                'hwnd': hwnd
            }
            
        except Exception as e:
            print(f"Window info error: {e}")
            return {
                'title': 'Unknown',
                'class': 'Unknown',
                'process': 'Unknown',
                'rect': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                'pid': 0,
                'hwnd': 0
            }
    
    def detect_text_field(self) -> Dict[str, Any]:
        """Detect if cursor is in a text field"""
        try:
            window_info = self.get_active_window_info()
            window_title = window_info.get('title', '').lower()
            window_class = window_info.get('class', '').lower()
            process_name = window_info.get('process', '').lower()
            
            # Common text editing applications
            text_editors = [
                'notepad', 'word', 'excel', 'powerpoint', 'outlook',
                'notepad++', 'sublime', 'vs code', 'visual studio',
                'chrome', 'firefox', 'edge', 'brave', 'opera'
            ]
            
            # Common text field indicators
            text_indicators = [
                'edit', 'text', 'input', 'textarea', 'contenteditable',
                'richedit', 'textbox', 'document', 'sheet'
            ]
            
            # Check if it's a text editing application
            is_text_app = any(editor in process_name for editor in text_editors)
            
            # Check window class for text indicators
            is_text_class = any(indicator in window_class for indicator in text_indicators)
            
            # Check window title for text indicators
            is_text_title = any(indicator in window_title for indicator in text_indicators)
            
            return {
                'is_text_field': is_text_app or is_text_class or is_text_title,
                'window_info': window_info,
                'confidence': self._calculate_text_field_confidence(
                    is_text_app, is_text_class, is_text_title, window_info
                )
            }
            
        except Exception as e:
            print(f"Text field detection error: {e}")
            return {
                'is_text_field': False,
                'window_info': {},
                'confidence': 0.0
            }
    
    def _calculate_text_field_confidence(self, is_app: bool, is_class: bool, is_title: bool, window_info: Dict) -> float:
        """Calculate confidence score for text field detection"""
        confidence = 0.0
        
        if is_app:
            confidence += 0.4
        if is_class:
            confidence += 0.3
        if is_title:
            confidence += 0.2
        
        # Additional checks
        window_title = window_info.get('title', '').lower()
        if any(word in window_title for word in ['notepad', 'word', 'excel', 'document']):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def write_at_cursor(self, text: str, click_first: bool = True) -> bool:
        """Write text at current cursor position"""
        try:
            if click_first:
                # Click at current position to ensure focus
                current_pos = self.get_cursor_position()
                pyautogui.click(current_pos[0], current_pos[1])
                await asyncio.sleep(0.1)
            
            # Type the text
            pyautogui.typewrite(text, interval=self.typing_speed)
            
            return True
            
        except Exception as e:
            print(f"Write at cursor error: {e}")
            return False
    
    async def smart_write(self, text: str) -> Dict[str, Any]:
        """Smart write with cursor detection and validation"""
        try:
            result = {
                'success': False,
                'message': '',
                'cursor_position': None,
                'window_info': None,
                'text_field_detected': False,
                'confidence': 0.0
            }
            
            # Get cursor position
            cursor_pos = self.get_cursor_position()
            result['cursor_position'] = cursor_pos
            
            # Detect text field
            text_field_info = self.detect_text_field()
            result['text_field_detected'] = text_field_info['is_text_field']
            result['confidence'] = text_field_info['confidence']
            result['window_info'] = text_field_info['window_info']
            
            # Write text
            if text_field_info['is_text_field']:
                success = await self.write_at_cursor(text)
                result['success'] = success
                
                if success:
                    result['message'] = f"✅ Text written successfully at cursor position"
                else:
                    result['message'] = f"❌ Failed to write text"
            else:
                # Try anyway but warn user
                success = await self.write_at_cursor(text)
                result['success'] = success
                
                if success:
                    result['message'] = f"⚠️ Text written (low confidence - may not be text field)"
                else:
                    result['message'] = f"❌ Failed to write text"
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Smart write failed: {str(e)}",
                'cursor_position': None,
                'window_info': None,
                'text_field_detected': False,
                'confidence': 0.0
            }
    
    async def click_and_write(self, x: int, y: int, text: str) -> bool:
        """Click at specific position and write text"""
        try:
            # Click at position
            pyautogui.click(x, y)
            await asyncio.sleep(0.2)
            
            # Write text
            pyautogui.typewrite(text, interval=self.typing_speed)
            
            return True
            
        except Exception as e:
            print(f"Click and write error: {e}")
            return False
    
    def get_cursor_info(self) -> str:
        """Get detailed cursor and window information"""
        try:
            cursor_pos = self.get_cursor_position()
            window_info = self.get_active_window_info()
            text_field_info = self.detect_text_field()
            
            result = f"🖱️ Cursor Information:\n\n"
            result += f"📍 Cursor Position: ({cursor_pos[0]}, {cursor_pos[1]})\n"
            result += f"🪟 Active Window: {window_info.get('title', 'Unknown')}\n"
            result += f"💻 Process: {window_info.get('process', 'Unknown')}\n"
            result += f"📝 Text Field: {'Yes' if text_field_info['is_text_field'] else 'No'}\n"
            result += f"🎯 Confidence: {text_field_info['confidence']:.1%}\n"
            
            if text_field_info['is_text_field']:
                result += f"\n✅ Ready to write at cursor position!\n"
                result += f"💡 Use 'write_at_cursor' to type text here\n"
            else:
                result += f"\n⚠️ Not in a recognized text field\n"
                result += f"💡 Move cursor to text editor or browser input field\n"
            
            return result
            
        except Exception as e:
            return f"❌ Cursor info failed: {str(e)}"

# Global instance
cursor_writer = CursorWriter()

@function_tool()
async def write_at_cursor(text: str) -> str:
    """
    Write text at current cursor position
    
    Args:
        text: Text to write at cursor position
        
    Returns:
        str: Writing result
    """
    try:
        result = f"✍️ Cursor Writer:\n\n"
        result += f"📝 Text: '{text}'\n"
        result += f"🔍 Analyzing cursor position...\n"
        
        # Smart write with detection
        write_result = await cursor_writer.smart_write(text)
        
        cursor_pos = write_result.get('cursor_position', (0, 0))
        window_info = write_result.get('window_info', {})
        is_text_field = write_result.get('text_field_detected', False)
        confidence = write_result.get('confidence', 0.0)
        success = write_result.get('success', False)
        
        result += f"📍 Cursor Position: ({cursor_pos[0]}, {cursor_pos[1]})\n"
        result += f"🪟 Active Window: {window_info.get('title', 'Unknown')}\n"
        result += f"📝 Text Field: {'Yes' if is_text_field else 'No'}\n"
        result += f"🎯 Confidence: {confidence:.1%}\n\n"
        
        result += f"{write_result.get('message', 'No message')}\n"
        
        if success:
            result += f"\n🎉 Text written successfully!\n"
            result += f"💡 Check the cursor position for your text\n"
        else:
            result += f"\n❌ Failed to write text\n"
            result += f"💡 Ensure cursor is in a text field\n"
        
        return result
        
    except Exception as e:
        return f"❌ Write at cursor failed: {str(e)}"

@function_tool()
async def click_and_write(x: int, y: int, text: str) -> str:
    """
    Click at specific coordinates and write text
    
    Args:
        x: X coordinate to click
        y: Y coordinate to click
        text: Text to write after clicking
        
    Returns:
        str: Click and write result
    """
    try:
        result = f"🖱️ Click and Write:\n\n"
        result += f"📍 Click Position: ({x}, {y})\n"
        result += f"📝 Text: '{text}'\n"
        result += f"🚀 Executing...\n"
        
        success = await cursor_writer.click_and_write(x, y, text)
        
        if success:
            result += f"✅ Clicked at ({x}, {y}) and wrote text successfully!\n"
            result += f"🎉 Text should appear at clicked position\n"
        else:
            result += f"❌ Failed to click and write\n"
            result += f"💡 Check if position is valid and accessible\n"
        
        return result
        
    except Exception as e:
        return f"❌ Click and write failed: {str(e)}"

@function_tool()
async def get_cursor_status() -> str:
    """
    Get current cursor position and window information
    
    Returns:
        str: Cursor status information
    """
    try:
        return cursor_writer.get_cursor_info()
        
    except Exception as e:
        return f"❌ Cursor status failed: {str(e)}"

@function_tool()
async def type_text_fast(text: str) -> str:
    """
    Type text quickly at current position (no cursor detection)
    
    Args:
        text: Text to type
        
    Returns:
        str: Typing result
    """
    try:
        result = f"⚡ Fast Type:\n\n"
        result += f"📝 Text: '{text}'\n"
        result += f"🚀 Typing at current position...\n"
        
        success = await cursor_writer.write_at_cursor(text, click_first=False)
        
        if success:
            result += f"✅ Text typed successfully!\n"
            result += f"⚡ Fast typing completed\n"
        else:
            result += f"❌ Failed to type text\n"
            result += f"💡 Ensure cursor is in active text field\n"
        
        return result
        
    except Exception as e:
        return f"❌ Fast type failed: {str(e)}"

@function_tool()
async def write_in_window(window_title: str, text: str) -> str:
    """
    Write text in specific window by title
    
    Args:
        window_title: Title of window to write in
        text: Text to write
        
    Returns:
        str: Window writing result
    """
    try:
        result = f"🪟 Window Writer:\n\n"
        result += f"🪟 Window: '{window_title}'\n"
        result += f"📝 Text: '{text}'\n"
        result += f"🔍 Searching for window...\n"
        
        import win32gui
        
        # Find window by title
        hwnd = win32gui.FindWindow(None, window_title)
        
        if hwnd == 0:
            result += f"❌ Window not found: '{window_title}'\n"
            result += f"💡 Check if window is open and title is exact\n"
            return result
        
        # Bring window to front
        win32gui.SetForegroundWindow(hwnd)
        await asyncio.sleep(0.5)
        
        # Write text
        success = await cursor_writer.write_at_cursor(text)
        
        if success:
            result += f"✅ Text written in '{window_title}' successfully!\n"
            result += f"🎉 Check the window for your text\n"
        else:
            result += f"❌ Failed to write in window\n"
            result += f"💡 Ensure window has active text field\n"
        
        return result
        
    except Exception as e:
        return f"❌ Window write failed: {str(e)}"
