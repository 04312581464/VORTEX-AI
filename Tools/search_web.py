"""
Simple Web Search with Default Browser
Opens user's default browser and searches the user's query
"""

import webbrowser
import urllib.parse
from livekit.agents import function_tool

@function_tool()
async def search_web(query: str) -> str:
    """
    Opens user's default browser and searches the user's query directly.
    
    Args:
        query: User's search question or terms
        
    Returns:
        str: Confirmation message that search has been opened
    """
    try:
        # Encode the query for URL
        encoded_query = urllib.parse.quote_plus(query)
        
        # Create search URL
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        # Open user's default browser with the search
        webbrowser.open_new_tab(search_url)
        
        return f"✅ Opened your default browser with search results for '{query}'. Check your browser for the results!"
        
    except Exception as e:
        return f"❌ Failed to open browser for search: {str(e)}"
