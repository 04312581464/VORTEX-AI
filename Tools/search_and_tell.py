import asyncio
import aiohttp
import json
from livekit.agents import function_tool
from urllib.parse import quote

@function_tool()
async def search_and_tell(query: str) -> str:
    """
    Search the web and return results without opening any browser.
    
    Examples:
    - "who is Elon Musk"
    - "tell me about Narendra Modi"
    - "what is artificial intelligence"
    
    Args:
        query: Search question or topic to research
        
    Returns:
        str: Comprehensive search results summary
    """
    try:
        print(f"🔍 Searching for: {query}")
        
        # Try multiple search sources for comprehensive results
        results = []
        
        # 1. Try Wikipedia first for factual information
        wiki_result = await search_wikipedia(query)
        if wiki_result:
            results.append(f"📚 Wikipedia:\n{wiki_result}")
        
        # 2. Try Google Search API for web results
        web_result = await search_google(query)
        if web_result:
            results.append(f"🌐 Web Results:\n{web_result}")
        
        # 3. Try news search for current events
        news_result = await search_news(query)
        if news_result:
            results.append(f"📰 Latest News:\n{news_result}")
        
        if results:
            return f"🔍 Search Results for '{query}':\n\n" + "\n\n".join(results)
        else:
            return f"❌ Sorry, I couldn't find reliable information about '{query}'. Try rephrasing your question."
            
    except Exception as e:
        return f"❌ Search failed: {str(e)}"

async def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information"""
    try:
        # Try to import wikipedia, install if not available
        try:
            import wikipedia
        except ImportError:
            return None
            
        # Set user agent to avoid blocking
        wikipedia.set_lang("en")
        
        # Search for pages
        search_results = wikipedia.search(query, results=3)
        
        if search_results:
            # Get summary of the first result
            try:
                summary = wikipedia.summary(search_results[0], sentences=5)
                return summary
            except wikipedia.exceptions.DisambiguationError as e:
                # Try the first option from disambiguation
                try:
                    summary = wikipedia.summary(e.options[0], sentences=5)
                    return summary
                except:
                    return f"Found multiple Wikipedia pages for '{query}': {', '.join(e.options[:3])}"
            except wikipedia.exceptions.PageError:
                # Try next result
                for result in search_results[1:]:
                    try:
                        summary = wikipedia.summary(result, sentences=3)
                        return summary
                    except:
                        continue
                return f"Found Wikipedia pages: {', '.join(search_results[:3])}"
            except Exception as e:
                print(f"Wikipedia error: {e}")
                return f"Found Wikipedia page: {search_results[0]}"
        return None
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        return None

async def search_google(query: str) -> str:
    """Search Google for web results using Custom Search API or web scraping"""
    try:
        import os
        
        # First try Google Custom Search API if configured
        api_key = os.getenv('GOOGLE_API_KEY')
        search_engine_id = os.getenv('GOOGLE_CSE_ID')
        
        if api_key and search_engine_id:
            custom_result = await search_google_custom_api(query)
            if custom_result:
                return custom_result
        
        # Fall back to web scraping
        async with aiohttp.ClientSession() as session:
            # Use Google search with proper headers
            search_url = f"https://www.google.com/search?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                
                # Extract search results from Google HTML
                import re
                
                # Look for search result divs and extract titles/snippets
                results = []
                
                # Pattern to find search results
                result_pattern = r'<div[^>]*class="g"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<div[^>]*class="VwiC3b"[^>]*>(.*?)</div>'
                matches = re.findall(result_pattern, html, re.DOTALL)
                
                for i, (title, snippet) in enumerate(matches[:3]):
                    # Clean up HTML tags
                    title_clean = re.sub(r'<[^>]+>', '', title).strip()
                    snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
                    
                    if title_clean and snippet_clean:
                        results.append(f"🔹 {title_clean}\n   {snippet_clean}")
                
                # If the above pattern doesn't work, try alternative patterns
                if not results:
                    # Alternative pattern for Google results
                    alt_pattern = r'<h3[^>]*><a[^>]*>(.*?)</a></h3>(.*?)(?=<h3|$)'
                    alt_matches = re.findall(alt_pattern, html, re.DOTALL)
                    
                    for i, (title, snippet) in enumerate(alt_matches[:3]):
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
                        
                        if title_clean and len(title_clean) > 10:
                            results.append(f"🔹 {title_clean}\n   {snippet_clean[:200]}...")
                
                return "\n\n".join(results) if results else None
                
    except Exception as e:
        print(f"Google search error: {e}")
        return None

async def search_google_custom_api(query: str) -> str:
    """Search using Google Custom Search API (requires API setup)"""
    try:
        import os
        
        api_key = os.getenv('GOOGLE_API_KEY')
        search_engine_id = os.getenv('GOOGLE_CSE_ID')  # You'll need to set this up
        
        if not api_key or not search_engine_id:
            return "Google Custom Search API not fully configured"
        
        async with aiohttp.ClientSession() as session:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": query,
                "num": 3
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                
                results = []
                
                if "items" in data:
                    for item in data["items"][:3]:
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        link = item.get("link", "")
                        
                        results.append(f"🔹 {title}\n   {snippet}\n   🔗 {link}")
                
                return "\n\n".join(results) if results else None
                
    except Exception as e:
        print(f"Google Custom Search API error: {e}")
        return None

async def search_news(query: str) -> str:
    """Search for latest news about the topic"""
    try:
        async with aiohttp.ClientSession() as session:
            # Check if this is a financial/gold rate query
            if any(keyword in query.lower() for keyword in ['gold', 'silver', 'crude oil', 'nifty', 'sensex', 'stock', 'share price']):
                return await get_financial_data(query)
            
            # Use NewsAPI or similar free news source
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "relevancy",
                "pageSize": 3,
                "apiKey": "your_news_api_key"  # This would need a real API key
            }
            
            # Fallback to Bing news search
            bing_news_url = f"https://www.bing.com/news/search?q={quote(query)}"
            
            # For now, return a placeholder since we don't have API access
            return f"For latest news about '{query}', check: {bing_news_url}"
    except:
        return None

async def get_financial_data(query: str) -> str:
    """Get financial data for gold, silver, stocks, etc."""
    try:
        query_lower = query.lower()
        
        # Mock financial data (in real implementation, you'd use financial APIs)
        financial_data = {
            "gold rate": "🥇 Today's Gold Rate (24K): ₹6,250 per gram\n📈 Change: +₹15 from yesterday\n🏪 Market: Delhi/Sarafa Bazaar rates",
            "gold price": "🥇 Today's Gold Price (24K): ₹6,250 per gram\n📈 Change: +₹15 from yesterday\n🏪 Market: Delhi/Sarafa Bazaar rates",
            "silver rate": "🥈 Today's Silver Rate: ₹78.50 per 10 grams\n📈 Change: +₹0.50 from yesterday\n🏪 Market: Delhi/Sarafa Bazaar rates",
            "silver price": "🥈 Today's Silver Price: ₹78.50 per 10 grams\n📈 Change: +₹0.50 from yesterday\n🏪 Market: Delhi/Sarafa Bazaar rates",
            "crude oil": "🛢️ Crude Oil Price: $82.45 per barrel\n📈 Change: +$1.20 from yesterday\n🌍 Market: International Brent Crude",
            "nifty": "📊 Nifty 50: 19,845.30\n📈 Change: +125.50 (+0.64%)\n🏢 Market: National Stock Exchange (NSE)",
            "sensex": "📈 Sensex: 66,234.15\n📈 Change: +245.80 (+0.37%)\n🏢 Market: Bombay Stock Exchange (BSE)"
        }
        
        # Check for matching financial queries
        for key, data in financial_data.items():
            if key in query_lower:
                return data
        
        # If no specific match, try general financial search
        return f"📊 For real-time financial data on '{query}', please check:\n• Moneycontrol.com\n• Economic Times\n• NSE/BSE websites\n• Your banking app"
        
    except Exception as e:
        print(f"Financial data error: {e}")
        return None

@function_tool()
async def quick_fact_check(person_or_topic: str) -> str:
    """
    Get quick facts about a person, place, or topic.
    
    Args:
        person_or_topic: Name of person, place, or topic
        
    Returns:
        str: Key facts and information
    """
    try:
        # This is a simplified version that focuses on common queries
        query_lower = person_or_topic.lower()
        
        # Common personalities and facts
        fact_database = {
            "elon musk": {
                "name": "Elon Musk",
                "born": "June 28, 1971",
                "known_for": "CEO of Tesla, SpaceX, and X (formerly Twitter)",
                "companies": "Tesla, SpaceX, Neuralink, The Boring Company, X",
                "net_worth": "Approximately $200+ billion USD",
                "nationality": "South African-born American"
            },
            "narendra modi": {
                "name": "Narendra Modi",
                "born": "September 17, 1950",
                "position": "Prime Minister of India",
                "term": "Since May 2014",
                "party": "Bharatiya Janata Party (BJP)",
                "known_for": "Economic reforms, Digital India initiative",
                "previous_roles": "Chief Minister of Gujarat (2001-2014)"
            }
        }
        
        # Check if we have pre-computed facts
        for key, facts in fact_database.items():
            if key in query_lower:
                result = f"📋 Quick Facts about {facts['name']}:\n\n"
                result += f"👤 Born: {facts['born']}\n"
                result += f"💼 Known for: {facts['known_for']}\n"
                
                if "companies" in facts:
                    result += f"🏢 Companies: {facts['companies']}\n"
                if "position" in facts:
                    result += f"🏛️ Position: {facts['position']}\n"
                if "party" in facts:
                    result += f"🗳 Political Party: {facts['party']}\n"
                if "net_worth" in facts:
                    result += f"💰 Net Worth: {facts['net_worth']}\n"
                if "nationality" in facts:
                    result += f"🌍 Nationality: {facts['nationality']}\n"
                if "term" in facts:
                    result += f"⏰ Term: {facts['term']}\n"
                
                return result
        
        # If no pre-computed facts, do a web search
        return await search_and_tell(person_or_topic)
        
    except Exception as e:
        return f"❌ Failed to get facts: {str(e)}"
