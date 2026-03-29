"""
Focus Mode Tools - App and Website Blocking
Blocks distracting applications and websites during focus sessions
"""

import asyncio
import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Set
from livekit.agents import function_tool

# Default distracting apps and websites
DISTRACTING_APPS = {
    "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe",
    "discord.exe", "slack.exe", "teams.exe", "zoom.exe",
    "steam.exe", "epicgameslauncher.exe", "origin.exe", "uplay.exe",
    "spotify.exe", "itunes.exe", "vlc.exe", "wmplayer.exe",
    "solitaire.exe", "minecraft.exe", "roblox.exe", "fortnite.exe",
    "tiktok.exe", "instagram.exe", "facebook.exe", "twitter.exe",
    "youtube.exe", "netflix.exe", "primevideo.exe", "disneyplus.exe"
}

DISTRACTING_WEBSITES = {
    "facebook.com", "twitter.com", "x.com", "instagram.com", "tiktok.com",
    "youtube.com", "youtu.be", "reddit.com", "9gag.com", "buzzfeed.com",
    "netflix.com", "hulu.com", "disneyplus.com", "primevideo.com",
    "twitch.tv", "discord.com", "steam.com", "epicgames.com",
    "spotify.com", "soundcloud.com", "pandora.com", "youtube.com/music"
}

BLOCKED_HOSTS_FILE = Path("C:/Windows/System32/drivers/etc/hosts")
FOCUS_CONFIG_FILE = Path("json/focus_mode_config.json")

class FocusModeBlocker:
    """Advanced focus mode with app and website blocking"""
    
    def __init__(self):
        self.is_blocking = False
        self.blocked_pids: Set[int] = set()
        self.original_hosts = ""
        self.focus_start_time = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load focus mode configuration"""
        try:
            if FOCUS_CONFIG_FILE.exists():
                with open(FOCUS_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            "blocked_apps": list(DISTRACTING_APPS),
            "blocked_websites": list(DISTRACTING_WEBSITES),
            "custom_apps": [],
            "custom_websites": [],
            "strict_mode": False,
            "allow_breaks": True,
            "break_duration": 5  # minutes
        }
    
    def _save_config(self) -> None:
        """Save focus mode configuration"""
        try:
            FOCUS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(FOCUS_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save focus config: {e}")
    
    def _backup_hosts_file(self) -> bool:
        """Backup original hosts file"""
        try:
            if BLOCKED_HOSTS_FILE.exists():
                with open(BLOCKED_HOSTS_FILE, 'r') as f:
                    self.original_hosts = f.read()
                return True
        except Exception as e:
            print(f"⚠️ Failed to backup hosts file: {e}")
        return False
    
    def _restore_hosts_file(self) -> None:
        """Restore original hosts file"""
        try:
            if self.original_hosts:
                with open(BLOCKED_HOSTS_FILE, 'w') as f:
                    f.write(self.original_hosts)
                print("✅ Restored original hosts file")
        except Exception as e:
            print(f"⚠️ Failed to restore hosts file: {e}")
    
    def _block_websites(self) -> None:
        """Block distracting websites via hosts file"""
        try:
            if not self.original_hosts:
                self._backup_hosts_file()
            
            # Read current hosts
            current_hosts = ""
            if BLOCKED_HOSTS_FILE.exists():
                with open(BLOCKED_HOSTS_FILE, 'r') as f:
                    current_hosts = f.read()
            
            # Add website blocks
            blocked_sites = (self.config["blocked_websites"] + 
                          self.config["custom_websites"])
            
            hosts_entries = []
            for site in blocked_sites:
                hosts_entries.append(f"127.0.0.1 {site}")
                hosts_entries.append(f"127.0.0.1 www.{site}")
            
            # Combine original hosts with blocks
            if current_hosts:
                # Remove previous blocks
                lines = current_hosts.split('\n')
                filtered_lines = []
                for line in lines:
                    if not any(blocked in line.lower() for blocked in blocked_sites):
                        filtered_lines.append(line)
                current_hosts = '\n'.join(filtered_lines)
            
            # Add new blocks
            updated_hosts = current_hosts + "\n\n# Vortex Focus Mode Blocks\n"
            updated_hosts += "\n".join(hosts_entries)
            
            # Write updated hosts file
            with open(BLOCKED_HOSTS_FILE, 'w') as f:
                f.write(updated_hosts)
                
            # Flush DNS cache
            try:
                subprocess.run(["ipconfig", "/flushdns"], capture_output=True, shell=True)
            except:
                pass
                
            print(f"🚫 Blocked {len(blocked_sites)} distracting websites")
            
        except Exception as e:
            print(f"⚠️ Failed to block websites: {e}")
    
    def _is_distracting_app(self, process_name: str) -> bool:
        """Check if an app is distracting"""
        all_blocked = set(self.config["blocked_apps"] + self.config["custom_apps"])
        return any(blocked.lower() in process_name.lower() for blocked in all_blocked)
    
    def _block_apps(self) -> None:
        """Block distracting applications"""
        try:
            # Get running processes
            result = subprocess.run(["tasklist", "/fo", "csv"], capture_output=True, text=True)
            if result.returncode != 0:
                return
            
            processes = result.stdout.split('\n')[1:]  # Skip header
            blocked_count = 0
            
            for process_line in processes:
                if not process_line.strip():
                    continue
                    
                parts = process_line.split(',')
                if len(parts) < 2:
                    continue
                    
                process_name = parts[0].strip('"')
                pid_str = parts[1].strip('"')
                
                if not pid_str.isdigit():
                    continue
                    
                pid = int(pid_str)
                
                if self._is_distracting_app(process_name):
                    if pid not in self.blocked_pids:
                        try:
                            # Terminate the distracting app
                            subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                        capture_output=True, shell=True)
                            self.blocked_pids.add(pid)
                            blocked_count += 1
                            print(f"🚫 Blocked distracting app: {process_name}")
                        except Exception as e:
                            print(f"⚠️ Failed to block {process_name}: {e}")
            
            if blocked_count > 0:
                print(f"🎯 Focus Mode: Blocked {blocked_count} distracting apps")
                
        except Exception as e:
            print(f"⚠️ Error in app blocking: {e}")
    
    async def _monitor_and_block(self) -> None:
        """Continuous monitoring and blocking"""
        while self.is_blocking:
            try:
                self._block_apps()
                await asyncio.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                await asyncio.sleep(5)
    
    def start_focus_mode(self, duration_minutes: int = 60) -> str:
        """Start focus mode with app and website blocking"""
        if self.is_blocking:
            return "🎯 Focus mode is already active!"
        
        try:
            self.is_blocking = True
            self.focus_start_time = time.time()
            self.blocked_pids.clear()
            
            # Block websites
            self._block_websites()
            
            # Initial app blocking
            self._block_apps()
            
            # Start continuous monitoring
            asyncio.create_task(self._monitor_and_block())
            
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            
            return f"""🎯 **Focus Mode Activated**
            
⏰ **Duration**: {hours}h {minutes}min
🚫 **Blocking**: 
  • {len(self.config['blocked_apps'])} distracting apps
  • {len(self.config['blocked_websites'])} websites
🔒 **Status**: Active and monitoring

💡 *Apps and websites will be automatically blocked if opened*
"""
        
        except Exception as e:
            return f"❌ Failed to start focus mode: {e}"
    
    def stop_focus_mode(self) -> str:
        """Stop focus mode and restore access"""
        if not self.is_blocking:
            return "🎯 Focus mode is not currently active."
        
        try:
            self.is_blocking = False
            
            # Restore hosts file
            self._restore_hosts_file()
            
            # Clear blocked PIDs (they're already terminated)
            self.blocked_pids.clear()
            
            if self.focus_start_time:
                duration = int((time.time() - self.focus_start_time) / 60)
                hours = duration // 60
                minutes = duration % 60
                
                return f"""✅ **Focus Mode Deactivated**
                
⏰ **Session Duration**: {hours}h {minutes}min
🔓 **Status**: All restrictions lifted
🎉 **Good work on staying focused!**

💡 *All apps and websites are now accessible*
"""
            else:
                return "✅ Focus mode deactivated. All restrictions lifted."
                
        except Exception as e:
            return f"❌ Error stopping focus mode: {e}"
    
    def get_status(self) -> str:
        """Get current focus mode status"""
        if not self.is_blocking:
            return """🎯 **Focus Mode Status**: INACTIVE

🔓 *All apps and websites are currently accessible*
"""
        
        if self.focus_start_time:
            duration = int((time.time() - self.focus_start_time) / 60)
            hours = duration // 60
            minutes = duration % 60
        else:
            duration = 0
            hours = 0
            minutes = 0
        
        return f"""🎯 **Focus Mode Status**: ACTIVE

⏰ **Session Duration**: {hours}h {minutes}min
🚫 **Currently Blocking**: 
  • {len(self.config['blocked_apps'])} distracting apps
  • {len(self.config['blocked_websites'])} websites
🔒 **Status**: Active and monitoring

💡 *Distracting content is being automatically blocked*
"""
    
    def add_custom_app(self, app_name: str) -> str:
        """Add custom app to block list"""
        app_name = app_name.strip().lower()
        if app_name not in self.config["custom_apps"]:
            self.config["custom_apps"].append(app_name)
            self._save_config()
            return f"✅ Added '{app_name}' to custom app block list."
        else:
            return f"⚠️ '{app_name}' is already in the block list."
    
    def add_custom_website(self, website: str) -> str:
        """Add custom website to block list"""
        website = website.strip().lower()
        if not website.startswith('www.'):
            website = 'www.' + website
        
        if website not in self.config["custom_websites"]:
            self.config["custom_websites"].append(website)
            self._save_config()
            return f"✅ Added '{website}' to custom website block list."
        else:
            return f"⚠️ '{website}' is already in the block list."

# Global focus mode instance
_focus_blocker = None

def get_focus_blocker():
    """Get global focus blocker instance"""
    global _focus_blocker
    if _focus_blocker is None:
        _focus_blocker = FocusModeBlocker()
    return _focus_blocker

# Tool functions
@function_tool()
async def enable_focus_mode(duration_minutes: int = 60) -> str:
    """
    Enable focus mode to block distracting apps and websites
    
    Args:
        duration_minutes: How long to maintain focus mode (default: 60 minutes)
        
    Returns:
        str: Status message
    """
    blocker = get_focus_blocker()
    return blocker.start_focus_mode(duration_minutes)

@function_tool()
async def disable_focus_mode() -> str:
    """
    Disable focus mode and restore access to all apps and websites
    
    Returns:
        str: Status message
    """
    blocker = get_focus_blocker()
    return blocker.stop_focus_mode()

@function_tool()
async def get_focus_status() -> str:
    """
    Get current focus mode status and session information
    
    Returns:
        str: Current status and statistics
    """
    blocker = get_focus_blocker()
    return blocker.get_status()

@function_tool()
async def block_distracting_app(app_name: str) -> str:
    """
    Add a specific app to the distraction block list
    
    Args:
        app_name: Name of the application to block (e.g., "chrome.exe")
        
    Returns:
        str: Confirmation message
    """
    blocker = get_focus_blocker()
    return blocker.add_custom_app(app_name)

@function_tool()
async def block_distracting_website(website: str) -> str:
    """
    Add a specific website to the distraction block list
    
    Args:
        website: Website domain to block (e.g., "facebook.com")
        
    Returns:
        str: Confirmation message
    """
    blocker = get_focus_blocker()
    return blocker.add_custom_website(website)

if __name__ == "__main__":
    # Test focus mode
    blocker = FocusModeBlocker()
    print(blocker.start_focus_mode(30))
    input("Press Enter to stop focus mode...")
    print(blocker.stop_focus_mode())
