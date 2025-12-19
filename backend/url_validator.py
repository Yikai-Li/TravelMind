"""
URL Validator
Validates URLs before displaying them to users
"""
import requests
from urllib.parse import urlparse
import re


def is_valid_url_format(url: str) -> bool:
    """Check if URL has valid format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False


def validate_url(url: str, timeout: int = 3) -> bool:
    """
    Validate if a URL is accessible
    
    Args:
        url: URL to validate
        timeout: Request timeout in seconds
    
    Returns:
        True if URL is valid and accessible, False otherwise
    """
    # First check format
    if not is_valid_url_format(url):
        return False
    
    try:
        # Make HEAD request to check if URL exists
        response = requests.head(url, timeout=timeout, allow_redirects=True, 
                                headers={'User-Agent': 'Mozilla/5.0'})
        
        # Accept 200-399 status codes (success and redirects)
        return response.status_code < 400
    except:
        # If HEAD fails, try GET with very short timeout
        try:
            response = requests.get(url, timeout=2, allow_redirects=True,
                                  headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
            return response.status_code < 400
        except:
            return False


def validate_urls(urls: list, max_concurrent: int = 5) -> list:
    """
    Validate a list of URLs
    
    Args:
        urls: List of URL strings or dicts with 'url' key
        max_concurrent: Max number of URLs to validate concurrently
    
    Returns:
        List of valid URLs only
    """
    valid_urls = []
    
    for url_item in urls[:max_concurrent]:  # Limit to prevent hanging
        # Handle both string URLs and dict objects
        if isinstance(url_item, str):
            url = url_item
            if validate_url(url):
                valid_urls.append(url)
        elif isinstance(url_item, dict):
            url = url_item.get('url') or url_item.get('link') or ''
            if url and validate_url(url):
                valid_urls.append(url_item)
    
    return valid_urls


def filter_valid_sources(data: dict) -> dict:
    """
    Filter AI-generated data to only include valid, accessible URLs
    
    Args:
        data: Response data from AI with potential sources/links
    
    Returns:
        Data with only validated URLs
    """
    # Validate official_links
    if 'official_links' in data and data['official_links']:
        data['official_links'] = validate_urls(data['official_links'])
    
    # Validate sources
    if 'sources' in data and data['sources']:
        data['sources'] = validate_urls(data['sources'])
    
    # Recursively validate in itinerary activities
    if 'itinerary' in data:
        for day in data.get('itinerary', []):
            for activity in day.get('activities', []):
                if 'official_links' in activity:
                    activity['official_links'] = validate_urls(activity.get('official_links', []))
                if 'sources' in activity:
                    activity['sources'] = validate_urls(activity.get('sources', []))
    
    return data
