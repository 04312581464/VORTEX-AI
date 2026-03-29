import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os
from livekit.agents import function_tool

@function_tool()
async def web_scraper(query: str) -> str:
    """
    Analyzes webpage content based on user query. 
    When executed, it will prompt for a URL, scrape the webpage content, 
    and use Groq AI to analyze the content in relation to the user's query.
    
    Args:
        query (str): The question or topic to analyze from the webpage content
    
    Returns:
        str: AI-analyzed summary answering the user's query based on scraped content
    """
    
    try:
        # Simple input for URL
        print(f"\n🔍 Your Query: {query}")
        print("Please enter the website URL to scrape:")
        url = input("URL: ").strip()
        
        if not url:
            return "❌ No URL provided. Operation cancelled."
        
        # Step 1: Web Scraping
        print("🌐 Scraping website...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return f"❌ Failed to access website: HTTP {response.status}"
                    
                    html = await response.text()
                    
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = '\n'.join(chunk for chunk in chunks if chunk)
            
            if not content:
                return "❌ No content found. Please check the URL."
            
            # Limit content to 1000 characters
            if len(content) > 1000:
                content = content[:1000]
                
            print(f"✅ Scraped {len(content)} characters")
                
        except Exception as e:
            return f"❌ Failed to scrape website: {str(e)}"
        
        # Step 2: Send to Groq AI
        print("🤖 Analyzing with AI...")
        
        GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        
        # Simple prompt - fast processing
        prompt = f"Query: {query}\n\nContent: {content}\n\nAnswer the query based ONLY on above content. Keep answer under 150 words."
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama2-70b-4096",  # Fast and reliable
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 300,  # Short response
            "top_p": 0.9
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_API_URL, headers=headers, json=payload, timeout=30) as res:
                if res.status != 200:
                    error_text = await res.text()
                    return f"❌ API Error {res.status}: {error_text}"
                
                data = await res.json()
                
                result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                if not result:
                    # If AI fails, return scraped content
                    return f"""
                    📊 **Direct Content (AI analysis failed)**
                    
                    **URL:** {url}
                    **Query:** {query}
                    
                    **First 500 chars:**
                    {content[:500]}
                    """
                
                return f"""
                🔍 **Query:** {query}
                🌐 **URL:** {url}
                
                **Analysis:**
                {result}
                
                ✅ Analysis complete.
                """
            
    except Exception as e:
        return f"❌ Error in web scraper: {str(e)}"