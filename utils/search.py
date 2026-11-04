import os

import arxiv
from dotenv import load_dotenv
from tavily import TavilyClient
from tinyfish import TinyFish

load_dotenv()
__all__ = ["create_arxiv", "create_tavily", "create_tiny_fish"]


# ---------------------------------------------------------------------------
# INFO Helpers
# ---------------------------------------------------------------------------
def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"{name} is not set. Add it to your .env file "
            f"or export it before creating that model/client."
        )
    return value


# ---------------------------------------------------------------------------
# INFO Create Tavily Client
# ---------------------------------------------------------------------------
def create_tavily():
    # api_key = os.environ["TAVILY_API_KEY"] = cast(str, os.getenv("TAVILY_API_KEY"))
    _require_env("TAVILY_API_KEY")
    tavily_client = TavilyClient()
    return tavily_client


# ---------------------------------------------------------------------------
# INFO Create TinyFish Client
# ---------------------------------------------------------------------------
def create_tiny_fish():
    # api_key = os.environ["TINYFISH_API_KEY"] = cast(str, os.getenv("TINYFISH_API_KEY"))
    _require_env("TINYFISH_API_KEY")
    client = TinyFish()
    return client


def create_arxiv(search_query: str, max_results: int = 3):
    client = arxiv.Client()
    search = arxiv.Search(query=search_query, max_results=max_results)
    return client.results(search)
