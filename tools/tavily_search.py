import os

from tavily import TavilyClient

import config  # loads .env from project root
from config import COLLEGE_DOMAIN, get_tavily_api_key

client = TavilyClient(api_key=get_tavily_api_key())


def web_search(query: str, include_domains: list[str] | None = None, site_domain: str = COLLEGE_DOMAIN) -> str:
    """
    Search web results, prioritizing the specified college website domain (e.g. vignan.ac.in).
    """
    domains = include_domains or ([site_domain] if site_domain else None)

    try:
        if domains:
            response = client.search(
                query=query,
                include_domains=domains,
                search_depth="advanced",
                max_results=5,
            )
        else:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
            )

        results_list = response.get("results", [])

        # Fallback if domain-restricted search yielded fewer than 2 results
        if len(results_list) < 2 and site_domain:
            fallback_response = client.search(
                query=f"{query} site:{site_domain} OR {site_domain}",
                search_depth="advanced",
                max_results=5,
            )
            existing_urls = {r.get("url") for r in results_list}
            for item in fallback_response.get("results", []):
                if item.get("url") not in existing_urls:
                    results_list.append(item)

        if not results_list:
            # Final fallback to general web search if still no results found
            general_response = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
            )
            results_list = general_response.get("results", [])

    except Exception as e:
        return f"Web search error: {str(e)}"

    formatted_results = ""
    for item in results_list:
        formatted_results += f"""
Title: {item.get('title', 'N/A')}
Content: {item.get('content', 'N/A')}
URL: {item.get('url', 'N/A')}

"""

    return formatted_results