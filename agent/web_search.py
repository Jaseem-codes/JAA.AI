import os

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()


def web_search(query: str, max_results: int = 5):
    """
    Search the web using Tavily and return
    clean results for JAA.AI.
    """

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return {
            "success": False,
            "results": [],
            "error": "TAVILY_API_KEY is not configured."
        }

    try:
        client = TavilyClient(
            api_key=api_key
        )

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )

        results = []

        for item in response.get("results", []):

            results.append({
                "title": item.get(
                    "title",
                    "Untitled"
                ),

                "url": item.get(
                    "url",
                    ""
                ),

                "content": item.get(
                    "content",
                    ""
                )
            })

        return {
            "success": True,
            "results": results,
            "error": None
        }

    except Exception as e:

        print(
            "WEB SEARCH ERROR:",
            repr(e)
        )

        return {
            "success": False,
            "results": [],
            "error": "Web search failed."
        }


if __name__ == "__main__":

    result = web_search(
        "latest technology news"
    )

    print(result)