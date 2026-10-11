from langchain.tools import tool
from tavily import TavilyClient
from rich import print
import os

from bs4 import BeautifulSoup
import requests
@tool
def web_search(query: str):
    """ Search the web for recent and reliable information on a topic. and Returns the  Title, URL and snippets. """

    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    result = tavily.search(
        query=query,
        max_results=3
        )

    out = []

    for r in result['results']:
        out.append(
            f" Title : {r['title']} \n URL : {r['url']} \n Snippet : {r['content'][:200]} "
        )

    return "\n---------\n".join(out)

# print(web_search.invoke("What are the recent news of war?"))


@tool
def scarape_url(url: str):
    """ Scrap and return the clean text content from a given URL for deeper reading.  """

    try:
        response = requests.get(
            url=url,
            timeout=8,
            headers={"User-Agent" : "Mozilla/5.0"}
        )

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(['style', 'script', 'nav', 'footer']):
            tag.decompose()

        return soup.get_text(separator=" ", strip=True)[:2000]

    except Exception as e:
        return f"Something went wrong, Could not scrap the URL: {str(e)}"

