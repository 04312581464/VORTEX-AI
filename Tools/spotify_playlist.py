import subprocess
import time
from livekit.agents import function_tool

@function_tool()
async def play_study_work_playlist() -> str:
    """
    Open Spotify and play the 'Study & Work Songs' playlist
    
    Returns:
        str: Status message
    """
    try:
        # Open Spotify first
        try:
            subprocess.Popen(["spotify"], shell=True)
            time.sleep(7)  # Wait for Spotify to open
            print("🎵 Spotify opened successfully")
        except Exception as e:
            return f"❌ Failed to open Spotify: {str(e)}"
        
        # Try to play the playlist using Spotify URI
        try:
            # Spotify URI for playlist (you may need to update this with your actual playlist URI)
            playlist_uri = "spotify:playlist:Study%20Work%20Songs"
            
            # Try multiple methods to play the playlist
            methods = [
                # Method 1: Direct URI
                ["spotify", "--uri", playlist_uri],
                # Method 2: Search and play
                ["spotify", "/search", "Study & Work Songs"],
                # Method 3: Command line with playlist name
                ["cmd", "/c", f"start spotify:search:Study & Work Songs"]
            ]
            
            for i, method in enumerate(methods, 1):
                try:
                    if i == 1:
                        subprocess.run(method, check=True, timeout=10)
                    else:
                        subprocess.run(method, check=True, timeout=10, shell=True)
                    
                    result = f"🎵 STUDY & WORK SONGS PLAYLIST STARTED! 🎵\n\n"
                    result += f"✅ Spotify opened successfully\n"
                    result += f"🎶 Now playing: Study & Work Songs\n"
                    result += f"📚 Perfect for studying and working!\n"
                    result += f"🎯 Method {i} worked!\n"
                    result += f"⏱️ Give it a moment to load...\n\n"
                    result += f"💡 If playlist doesn't play, try:\n"
                    result += f"   • 'spotify_play_liked' for liked songs\n"
                    result += f"   • 'spotify_search_play_quick Study & Work Songs'\n"
                    
                    return result
                    
                except subprocess.CalledProcessError:
                    continue
                except Exception:
                    continue
            
            # If all methods fail, provide manual instructions
            return f"🎵 SPOTIFY OPENED - MANUAL PLAY NEEDED 🎵\n\n"
            result += f"✅ Spotify opened successfully\n"
            result += f"🔍 Please manually search for 'Study & Work Songs'\n"
            result += f"📝 Steps:\n"
            result += f"   1. Click search bar in Spotify\n"
            result += f"   2. Type 'Study & Work Songs'\n"
            result += f"   3. Click on your playlist\n"
            result += f"   4. Press play\n\n"
            result += f"💡 Alternative commands:\n"
            result += f"   • 'spotify_play_liked' for liked songs\n"
            result += f"   • 'spotify_search_play_quick Study & Work Songs'\n"
            
        except Exception as e:
            return f"❌ Failed to play playlist: {str(e)}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

@function_tool()
async def spotify_play_playlist(playlist_name: str) -> str:
    """
    Open Spotify and play a specific playlist by name
    
    Args:
        playlist_name: Name of the playlist to play
        
    Returns:
        str: Status message
    """
    try:
        # Open Spotify first
        try:
            subprocess.Popen(["spotify"], shell=True)
            time.sleep(10)  # Wait for Spotify to open
            print(f"🎵 Spotify opened successfully")
        except Exception as e:
            return f"❌ Failed to open Spotify: {str(e)}"
        
        # Try to search and play the playlist
        try:
            # Search for the playlist
            subprocess.run(["spotify", "/search", playlist_name], check=True, timeout=10)
            
            result = f"🎵 PLAYLIST '{playlist_name}' STARTED! 🎵\n\n"
            result += f"✅ Spotify opened successfully\n"
            result += f"🔍 Searched for: {playlist_name}\n"
            result += f"🎶 Please click on your playlist in the results\n"
            result += f"⏱️ Give it a moment to load...\n\n"
            result += f"💡 If not found, try:\n"
            result += f"   • Check exact playlist name\n"
            result += f"   • Use 'play_study_work_playlist' for your main playlist\n"
            
            return result
            
        except Exception as e:
            return f"🎵 SPOTIFY OPENED - MANUAL SEARCH NEEDED 🎵\n\n"
            result += f"✅ Spotify opened successfully\n"
            result += f"🔍 Please manually search for '{playlist_name}'\n"
            result += f"📝 Steps:\n"
            result += f"   1. Click search bar in Spotify\n"
            result += f"   2. Type '{playlist_name}'\n"
            result += f"   3. Click on your playlist\n"
            result += f"   4. Press play\n"
            
            return result
            
    except Exception as e:
        return f"❌ Error: {str(e)}"
