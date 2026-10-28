from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()

tavily = TavilyClient(api_key = os.getenv('TAVILY_API_KEY'))

def search_web(query: str, max_results: int = 5) -> str:
    results = tavily.search(query=query, max_results=max_results)['results']
    return "\n\n".join(f"{r['title']}\n{r['url']}\n{r['content']}" for r in results)

@tool
def web_search(query: str) -> str:
    """Search the web for recent information. Returns titles, URLs and snippets."""
    return search_web(query)

@tool
def scrap_url(url : str)->str:
    '''scrape and return clean text content from a given url for deeper reading.'''
    try:
        resp = requests.get(url, timeout=30, headers={'user-agent':'mozilla/5.0'})
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text,'html.parser')
        for tag in soup(['script','style','nav','footer']):
            tag.decompose()
        return soup.get_text(separator=' ',strip=True)[:3000]
    except Exception as e:
        return f'could not scrap url : {str(e)}'
    